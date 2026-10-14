import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo


IGNORED = {"LDUSDC", "EFI", "PARA", "BTTC"}
READ_ONLY = {
    ("spot", "get-account"),
    ("spot", "get-open-orders"),
    ("spot", "ticker-trading-day"),
    ("wallet", "funding-wallet"),
    ("wallet", "query-user-wallet-balance"),
    ("simple-earn", "get-flexible-product-position"),
    ("simple-earn", "get-locked-product-position"),
    ("futures-usds", "account-information-v3"),
    ("futures-usds", "position-information-v3"),
    ("futures-usds", "get-income-history"),
    ("futures-usds", "mark-price-kline-candlestick-data"),
    ("futures-coin", "account-information"),
    ("futures-coin", "position-information"),
    ("futures-coin", "exchange-information"),
    ("futures-coin", "mark-price-kline-candlestick-data"),
    ("request", "https://dapi.binance.com/dapi/v1/income"),
}
ZERO = Decimal(0)


def number(value):
    if value is None:
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except InvalidOperation:
        return None


def product(*values):
    if any(value is None for value in values):
        return None
    result = Decimal(1)
    for value in values:
        result *= value
    return result


def total(values):
    values = list(values)
    return None if any(value is None for value in values) else sum(values, ZERO)


def difference(current, previous):
    return None if current is None or previous is None else current - previous


def percent(numerator, denominator):
    return (
        None
        if numerator is None or not denominator or denominator < 0
        else numerator / denominator * 100
    )


def fmt(value, signed=False, precise=False):
    if value is None:
        return "未取得"
    if precise:
        return f"{value:,.12f}".rstrip("0").rstrip(".")
    if signed and value != 0 and abs(value) < Decimal("0.005"):
        return f"{value:+.8f}"
    return f"{value:+,.2f}" if signed else f"{value:,.2f}"


def pct(value):
    return "不可计算" if value is None else f"{value:+.2f}%"


def table(headers, rows):
    def width(text):
        return sum(
            0
            if unicodedata.combining(char)
            else 2
            if unicodedata.east_asian_width(char) in {"W", "F"}
            else 1
            for char in text
        )

    cells = [[str(cell).replace("|", "/") for cell in row] for row in [headers, *rows]]
    widths = [max(3, *(width(cell) for cell in column)) for column in zip(*cells)]
    numeric_columns = (
        [
            any(
                number(cell.replace(",", "").removesuffix("%")) is not None
                for cell in column
            )
            for column in zip(*cells[1:])
        ]
        if len(cells) > 1
        else [False] * len(headers)
    )

    def line(cells):
        padded = []
        for cell, size, numeric in zip(cells, widths, numeric_columns):
            padding = " " * (size - width(cell))
            padded.append(f"{padding}{cell}" if numeric else f"{cell}{padding}")
        return f"| {' | '.join(padded)} |"

    return "\n".join(
        [
            line(cells[0]),
            line(["-" * size for size in widths]),
            *(line(row) for row in cells[1:]),
        ]
    )


def utc_start(now):
    return now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


class Binance:
    def __init__(self, executable, timeout=20):
        self.executable = executable
        self.timeout = timeout

    def call(self, group, command, **params):
        if (group, command) not in READ_ONLY:
            raise ValueError("拒绝非白名单命令")
        if group == "request":
            # 原始请求只读 GET，参数沿用接口的驼峰命名
            args = [self.executable, "request", "--signed", "GET", command]
            for key, value in params.items():
                first, *rest = key.split("_")
                args.extend(
                    [f"--{first}{''.join(w.title() for w in rest)}", str(value)]
                )
        else:
            args = [self.executable, group, command]
            for key, value in params.items():
                args.extend([f"--{key.replace('_', '-')}", str(value)])
        for attempt in range(2):
            try:
                process = subprocess.run(
                    args,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False,
                )
                if process.returncode:
                    transient = any(
                        word in process.stderr.lower()
                        for word in (
                            "timeout",
                            "timed out",
                            "recvwindow",
                            "502",
                            "503",
                            "connection",
                            "fetch",
                        )
                    )
                    if transient and attempt == 0:
                        time.sleep(0.3)
                        continue
                    # CLI errors can contain signed URLs; never echo raw stderr.
                    raise ValueError(f"CLI 查询失败（退出码 {process.returncode}）")
                data = json.loads(process.stdout)
                if (
                    isinstance(data, dict)
                    and "code" in data
                    and str(data["code"]) not in {"0", "200"}
                ):
                    raise ValueError(f"接口错误码 {data['code']}")
                return data
            except subprocess.TimeoutExpired:
                if attempt:
                    raise ValueError(
                        f"请求超时（每次 {self.timeout} 秒，已重试一次）"
                    ) from None
            except json.JSONDecodeError:
                raise ValueError("接口未返回有效 JSON") from None

    def paged(self, group, command, **params):
        rows = []
        for page in range(1, 101):
            if group == "simple-earn":
                data = self.call(group, command, current=page, size=100, **params)
                batch = data["rows"]
                done = len(rows) + len(batch) >= int(data["total"])
            else:
                batch = self.call(group, command, page=page, limit=1000, **params)
                done = len(batch) < 1000
            if not isinstance(batch, list):
                raise ValueError("分页响应结构异常")
            rows.extend(batch)
            if done:
                return rows
            if not batch:
                break
        raise ValueError("分页未完成，不使用不完整余额或流水")


def parallel(jobs, warnings):
    def run(job):
        key, function = job
        try:
            return key, function(), None
        except (ValueError, KeyError, TypeError, OSError) as error:
            detail = (
                str(error) if isinstance(error, ValueError) else type(error).__name__
            )
            return key, None, f"{key}：{detail}"

    result = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for key, value, error in pool.map(run, jobs.items()):
            result[key] = value
            if error:
                warnings.append(error)
    return result


def collect(client, now, warnings):
    day = int(utc_start(now).timestamp() * 1000)
    end = int(now.timestamp() * 1000)
    commands = {
        "spot": ("spot", "get-account", {"omit_zero_balances": "true"}),
        "orders": ("spot", "get-open-orders", {}),
        "usds": ("futures-usds", "account-information-v3", {}),
        "positions": ("futures-usds", "position-information-v3", {}),
        "coin": ("futures-coin", "account-information", {}),
        "coin_positions": ("futures-coin", "position-information", {}),
        "funding": ("wallet", "funding-wallet", {}),
        "wallets": ("wallet", "query-user-wallet-balance", {"quote_asset": "USDT"}),
    }
    jobs = {
        key: lambda args=args: client.call(args[0], args[1], **args[2])
        for key, args in commands.items()
    }
    for key, command in (
        ("earn", "get-flexible-product-position"),
        ("locked", "get-locked-product-position"),
    ):
        jobs[key] = lambda command=command: client.paged("simple-earn", command)
    # CLI 的币本位流水模型把 tranId 定义为字符串，接口实际返回数字导致解析失败，改走原始请求
    for key, group, command in (
        ("u_fees", "futures-usds", "get-income-history"),
        ("c_fees", "request", "https://dapi.binance.com/dapi/v1/income"),
    ):
        jobs[key] = lambda group=group, command=command: client.paged(
            group,
            command,
            income_type="FUNDING_FEE",
            start_time=day,
            end_time=end,
        )
    data = parallel(jobs, warnings)

    assets = {"USDT"}
    for rows in (
        (data.get("spot") or {}).get("balances", []),
        [
            row
            for row in (data.get("usds") or {}).get("assets", [])
            if number(row.get("marginBalance")) != ZERO
        ],
        [
            row
            for row in (data.get("coin") or {}).get("assets", [])
            if number(row.get("walletBalance")) != ZERO
            or number(row.get("marginBalance")) != ZERO
        ],
        data.get("earn") or [],
        data.get("locked") or [],
        data.get("funding") or [],
        data.get("u_fees") or [],
        data.get("c_fees") or [],
    ):
        assets.update(row["asset"] for row in rows)
    jobs = {}
    for key, group in (
        ("positions", "futures-usds"),
        ("coin_positions", "futures-coin"),
    ):
        if data[key] is not None:
            data[key] = [
                row for row in data[key] if number(row.get("positionAmt")) != ZERO
            ]
        for row in data[key] or []:
            assets.add(row.get("marginAsset", "USDT"))
            symbol = row["symbol"]
            jobs[f"{group}:{symbol}"] = lambda symbol=symbol, group=group: client.call(
                group,
                "mark-price-kline-candlestick-data",
                symbol=symbol,
                interval="1m",
                start_time=day,
                end_time=day + 59999,
                limit=1,
            )
    if data["coin_positions"]:
        jobs["coin_info"] = lambda: client.call("futures-coin", "exchange-information")
    for asset in assets - IGNORED - {"USDT"}:
        jobs[asset] = lambda asset=asset: client.call(
            "spot", "ticker-trading-day", symbol=f"{asset}USDT", time_zone="0:00"
        )
    market = parallel(jobs, warnings)
    market["USDT"] = {"lastPrice": "1", "openPrice": "1", "openTime": day}
    for key, value in list(market.items()):
        if value is None or key == "coin_info":
            continue
        valid = (
            value[0][0] == day
            if ":" in key and isinstance(value, list) and value
            else isinstance(value, dict) and value.get("openTime") == day
        )
        if not valid:
            market[key] = None
            warnings.append(f"{key}：UTC 零点时间戳不匹配或缺失")
    return data, market


def spot_row(asset, quantity, market):
    ticker = market.get(asset) or {}
    price, opening = number(ticker.get("lastPrice")), number(ticker.get("openPrice"))
    return dict(
        asset=asset,
        quantity=quantity,
        price=price,
        value=product(quantity, price),
        change=percent(difference(price, opening), opening),
        day=product(quantity, difference(price, opening)),
    )


def position_row(position, market, coin=False, metadata=None):
    symbol = position["symbol"]
    qty = number(position.get("positionAmt"))
    entry, mark = number(position.get("entryPrice")), number(position.get("markPrice"))
    margin = number(position.get("positionInitialMargin"))
    pnl = number(position.get("unRealizedProfit", position.get("unrealizedProfit")))
    group = "futures-coin" if coin else "futures-usds"
    candles = market.get(f"{group}:{symbol}")
    opening = number(candles[0][1]) if candles else None
    asset = (metadata or {}).get("marginAsset") if coin else position.get("marginAsset")
    conversion = number((market.get(asset) or {}).get("lastPrice"))
    direction = position.get("positionSide")
    if qty is not None:
        qty = (
            -abs(qty)
            if direction == "SHORT"
            else abs(qty)
            if direction == "LONG"
            else qty
        )

    if coin:
        face = number((metadata or {}).get("contractSize"))
        notional = product(abs(qty) if qty is not None else None, face)
        inverse_move = (
            Decimal(1) / opening - Decimal(1) / mark if opening and mark else None
        )
        day = product(qty, face, inverse_move, conversion)
    else:
        raw_notional = number(position.get("notional"))
        notional = product(
            abs(raw_notional)
            if raw_notional is not None
            else product(abs(qty) if qty is not None else None, mark),
            conversion,
        )
        day = product(qty, difference(mark, opening), conversion)
        entry, mark = product(entry, conversion), product(mark, conversion)
    return dict(
        symbol=symbol,
        side="空" if qty is not None and qty < 0 else "多",
        quantity=abs(qty) if qty is not None else None,
        entry=entry if entry and entry > 0 else None,
        mark=mark,
        notional=notional,
        pnl=product(pnl, conversion),
        native_pnl=pnl,
        asset=asset,
        margin=product(margin, conversion),
        roi=percent(pnl, margin),
        change=percent(difference(number(position.get("markPrice")), opening), opening),
        day=day,
    )


def position_table(rows, coin=False):
    rows = sorted(rows, key=lambda row: row["notional"] or ZERO, reverse=True)
    output = [
        [
            row["symbol"],
            row["side"],
            fmt(row["quantity"], precise=True),
            fmt(row["entry"], precise=True),
            fmt(row["mark"], precise=True),
            fmt(row["notional"]),
            fmt(row["pnl"], signed=True),
            pct(row["roi"]),
            pct(row["change"]),
            fmt(row["day"], signed=True),
        ]
        for row in rows
    ]
    output.append(
        [
            "合计",
            "—",
            "—",
            "—",
            "—",
            fmt(total(r["notional"] for r in rows)),
            fmt(total(r["pnl"] for r in rows), signed=True),
            pct(
                percent(total(r["pnl"] for r in rows), total(r["margin"] for r in rows))
            ),
            "—",
            fmt(total(r["day"] for r in rows), signed=True),
        ]
    )
    price_unit = "（USD）" if coin else ""
    return table(
        [
            "币种",
            "方向",
            "数量（张）" if coin else "数量",
            f"开仓均价{price_unit}",
            f"标记价格{price_unit}",
            "名义价值",
            "当前未实现盈亏",
            "保证金收益率",
            "今日涨幅",
            "今日估算盈亏",
        ],
        output,
    )


ACCOUNT_SOURCES = (
    ("earn", "Simple Earn 活期", ("totalAmount",)),
    ("locked", "Simple Earn 定期", ("amount",)),
    ("funding", "资金账户", ("free", "locked", "freeze", "withdrawing")),
    ("usds", "U 本位账户权益", ("marginBalance",)),
    ("coin", "币本位账户权益", ("marginBalance",)),
)


def source_balances(data, key, fields):
    rows = data[key]
    if key in {"usds", "coin"}:
        rows = (rows or {}).get("assets")
    if rows is None:
        return None
    return [
        (row["asset"], total(number(row.get(field)) for field in fields))
        for row in rows
        if row["asset"] not in IGNORED
    ]


def wallet_values(data):
    # 交易机器人等账户没有分币种数据，只能按整体估值计入
    wallets = data["wallets"]
    bots = next(
        (
            wallet
            for wallet in wallets or []
            if wallet.get("walletName") == "Trading Bots"
        ),
        None,
    )
    values = [("交易机器人", number(bots.get("balance")) if bots else None)]
    covered = {
        "Spot",
        "Funding",
        "Earn",
        "USDⓈ-M Futures",
        "COIN-M Futures",
        "Trading Bots",
    }
    for wallet in wallets or []:
        if (
            wallet.get("walletName") not in covered
            and number(wallet.get("balance")) != ZERO
        ):
            values.append((f"其他账户待核实：{wallet.get('walletName', '未知')}", None))
    return values


def account_values(data, market, spot_value):
    values = [("现货（含挂单锁定）", spot_value)]
    for key, label, fields in ACCOUNT_SOURCES:
        balances = source_balances(data, key, fields)
        values.append(
            (
                label,
                None
                if balances is None
                else total(
                    ZERO
                    if quantity == ZERO
                    else spot_row(asset, quantity, market)["value"]
                    for asset, quantity in balances
                ),
            )
        )
    return [*values, *wallet_values(data)]


def spot_rows(data, market):
    if data["spot"] is None:
        return None
    rows = [
        spot_row(
            row["asset"],
            total(number(row.get(key)) for key in ("free", "locked")),
            market,
        )
        for row in data["spot"]["balances"]
        if row["asset"] not in IGNORED
    ]
    rows.sort(key=lambda row: row["value"] or ZERO, reverse=True)
    return rows


def futures_rows(data, market):
    if data["positions"] is None:
        return None
    return [position_row(p, market) for p in data["positions"]]


def coin_asset_rows(data, market):
    if data["coin"] is None:
        return None
    return [
        spot_row(a["asset"], number(a.get("walletBalance")), market)
        for a in data["coin"]["assets"]
        if a["asset"] not in IGNORED and number(a.get("walletBalance")) != ZERO
    ]


def coin_trade_rows(data, market):
    positions = data["coin_positions"]
    if not positions:
        return positions
    metadata = {
        s["symbol"]: s for s in (market.get("coin_info") or {}).get("symbols", [])
    }
    account_positions = {
        (p["symbol"], p.get("positionSide", "BOTH")): p
        for p in (data["coin"] or {}).get("positions", [])
    }
    return [
        position_row(
            {
                **account_positions.get(
                    (p["symbol"], p.get("positionSide", "BOTH")), {}
                ),
                **p,
            },
            market,
            coin=True,
            metadata=metadata.get(p["symbol"]),
        )
        for p in positions
    ]


def funding_fee(data, market, key):
    if data[key] is None:
        return None
    return total(
        product(
            number(r.get("income")),
            number((market.get(r["asset"]) or {}).get("lastPrice")),
        )
        for r in data[key]
    )


def daily_breakdown(data, market):
    def named(rows, name, failed):
        # 查询失败用一行 None 占位，让合计自动变为未取得，而不是被当成 0
        if rows is None:
            return [dict(name=failed, day=None, failed=True)]
        return [dict(row, name=name(row)) for row in rows]

    def position_name(row):
        # 菜单宽度有限：U 本位去掉 USDT 后缀，币本位保留 USD 以示区分
        symbol = row["symbol"].removesuffix("USDT").removesuffix("_PERP")
        return f"{symbol} {row['side']}"

    spot = named(spot_rows(data, market), lambda r: r["asset"], "现货未取得")
    contract = [
        *named(futures_rows(data, market), position_name, "U 本位持仓未取得"),
        *(
            dict(row, quantity_unit="张")
            for row in named(
                coin_trade_rows(data, market), position_name, "币本位持仓未取得"
            )
        ),
        *named(
            coin_asset_rows(data, market),
            lambda r: f"{r['asset']} 抵押",
            "币本位钱包未取得",
        ),
    ]
    funding = total(funding_fee(data, market, key) for key in ("u_fees", "c_fees"))
    return spot, contract, funding


def overview(data, market):
    """按币种汇总所有账户的数量与市值；无法拆分币种的账户和取数失败的账户单列一行。"""
    spot = spot_rows(data, market)
    sources = [
        ("现货", None if spot is None else [(r["asset"], r["quantity"]) for r in spot]),
        *(
            (label, source_balances(data, key, fields))
            for key, label, fields in ACCOUNT_SOURCES
        ),
    ]
    quantities, rows = {}, []
    for label, balances in sources:
        if balances is None:
            rows.append(dict(name=f"{label}未取得", value=None))
            continue
        for asset, quantity in balances:
            quantities[asset] = total([quantities.get(asset, ZERO), quantity])
    rows += [
        dict(spot_row(asset, quantity, market), name=asset)
        for asset, quantity in quantities.items()
        if quantity != ZERO
    ]
    rows += [
        dict(name=label, value=value)
        for label, value in wallet_values(data)
        if value != ZERO
    ]
    whole = total(row["value"] for row in rows)
    rows = [dict(row, share=percent(row["value"], whole)) for row in rows]
    return rows, dict(name="总资产", value=whole, share=percent(whole, whole))


def column_totals(rows, keys):
    failed = any(row.get("failed") for row in rows)
    return {
        key: None if failed else total(row[key] for row in rows if key in row)
        for key in keys
    }


def spot_summary(rows):
    summary = column_totals(rows, ("value", "day"))
    opening = difference(summary["value"], summary["day"])
    return dict(summary, name="合计", change=percent(summary["day"], opening))


def contract_summary(rows, funding=ZERO):
    summary = column_totals(rows, ("notional", "margin", "pnl", "day"))
    return dict(
        summary,
        name="合计",
        roi=percent(summary["pnl"], summary["margin"]),
        day=total([summary["day"], funding]),
    )


def render(data, market, started, finished, warnings):
    spot = spot_rows(data, market)
    spot_value = total(row["value"] for row in spot) if spot is not None else None
    spot_day = total(row["day"] for row in spot) if spot is not None else None
    balances = account_values(data, market, spot_value)
    account_total = total(value for _, value in balances)
    known_values = [value for _, value in balances if value is not None]
    subtotal = total(known_values) if known_values else None
    missing = [label for label, value in balances if value is None]
    if missing:
        warnings.append(
            f"账户总价值未完整取得：{'、'.join(missing)}；仅显示可核实账户小计"
        )

    beijing = ZoneInfo("Asia/Shanghai")
    lines = [
        "# 币安持仓报告",
        f"创建于 {finished.astimezone(beijing):%Y-%m-%d}",
        "",
        f"**账户总价值：{fmt(account_total)} USDT**",
        *(
            [f"**可核实账户小计（不完整）：{fmt(subtotal)} USDT**"]
            if account_total is None
            else []
        ),
        f"**现货总市值：{fmt(spot_value)} USDT｜今日估算浮盈：{fmt(spot_day, signed=True)} USDT**",
        "",
        f"查询时间：北京时间 {started.astimezone(beijing):%Y-%m-%d %H:%M:%S}—{finished.astimezone(beijing):%H:%M:%S}；"
        f"UTC {started:%Y-%m-%d %H:%M:%S}—{finished:%H:%M:%S}。",
        f"收益起点：{utc_start(started):%Y-%m-%d %H:%M} UTC（北京时间 08:00）。价格及金额默认以 USDT 表示。",
        "",
        "## 账户总价值",
        "",
        table(
            ["账户", "价值（USDT）"],
            [[label, fmt(value)] for label, value in balances]
            + [
                [
                    "合计" if account_total is not None else "可核实账户小计（不完整）",
                    fmt(account_total if account_total is not None else subtotal),
                ]
            ],
        ),
        "",
        "总价值按现货、Simple Earn 活期与定期、资金账户、U 本位及币本位账户权益、交易机器人余额相加。合约权益已含未实现盈亏，不再加名义价值、保证金或今日盈亏。",
        "沿用忽略 LDUSDC、EFI、PARA、BTTC 的口径；LDUSDC 凭证不与实际理财 USDC 重复计入。机器人使用钱包总览估值，未取得币种明细；其他未覆盖账户如有余额则标记总价值不完整。",
        "",
        "## 1. 现货持仓",
        "",
    ]
    if spot is None:
        lines.append("现货查询失败，不能认定为零余额。")
    else:
        rows = [
            [
                r["asset"],
                fmt(r["quantity"], precise=True),
                fmt(r["price"], precise=True),
                fmt(r["value"]),
                pct(r["change"]),
                fmt(r["day"], signed=True),
            ]
            for r in spot
        ]
        rows.append(
            ["合计", "—", "—", fmt(spot_value), "—", fmt(spot_day, signed=True)]
        )
        lines.append(
            table(
                [
                    "币种",
                    "持有数量",
                    "当前价格",
                    "持仓市值",
                    "今日涨幅",
                    "今日估算浮盈",
                ],
                rows,
            )
        )
        usdt = next(
            (r for r in data["spot"]["balances"] if r["asset"] == "USDT"),
            {"free": "0", "locked": "0"},
        )
        lines.extend(
            [
                "",
                f"USDT 可用 {fmt(number(usdt['free']))}，锁定 {fmt(number(usdt['locked']))}。数量包含 free + locked。",
            ]
        )
        if data["orders"] is not None:
            locked = total(
                product(
                    difference(number(o.get("origQty")), number(o.get("executedQty"))),
                    number(o.get("price")),
                )
                for o in data["orders"]
                if o.get("side") == "BUY" and o["symbol"].endswith("USDT")
            )
            lines.append(
                f"现货挂单 {len(data['orders'])} 张，USDT 买单剩余预算 {fmt(locked)}。"
            )
            if locked is None or abs(locked - number(usdt["locked"])) > Decimal("0.01"):
                warnings.append(
                    "USDT 锁定余额与买单预算未完全核对一致；其他冻结或采样时差尚未排除"
                )
    lines.extend(
        [
            "",
            "已忽略 LDUSDC、EFI、PARA、BTTC；理财实际 USDC 单列，不重复计入凭证。",
            "",
            "## 2. U 本位合约",
            "",
        ]
    )

    futures = futures_rows(data, market)
    futures_day = total(r["day"] for r in futures) if futures is not None else None
    lines.append(
        position_table(futures)
        if futures
        else "普通 U 本位无持仓。"
        if futures == []
        else "持仓接口失败，数据未取得。"
    )
    account = data["usds"]
    if account is not None:
        lines.extend(
            [
                "",
                table(
                    ["合约账户指标", "USDT"],
                    [
                        [label, fmt(number(account.get(key)))]
                        for label, key in (
                            ("账户权益（已含未实现盈亏）", "totalMarginBalance"),
                            ("钱包余额", "totalWalletBalance"),
                            ("持仓初始保证金", "totalPositionInitialMargin"),
                            ("挂单初始保证金", "totalOpenOrderInitialMargin"),
                        )
                    ],
                ),
            ]
        )
        observed = total(r["pnl"] for r in futures) if futures is not None else None
        expected = number(account.get("totalUnrealizedProfit"))
        if (
            observed is None
            or expected is None
            or abs(observed - expected) > Decimal("0.01")
        ):
            warnings.append(
                f"合约浮盈核对未一致：逐仓 {fmt(observed)}，账户 {fmt(expected)}；可能存在采样时差或缺失"
            )
        else:
            lines.extend(
                [
                    "",
                    f"逐仓未实现盈亏与账户 totalUnrealizedProfit 核对一致（误差小于 0.01 USDT），账户值 {fmt(expected, signed=True)}。",
                ]
            )

    lines.extend(["", "## 3. 其他账户", ""])
    other_rows, coin_assets = [], coin_asset_rows(data, market)
    if coin_assets is not None:
        other_rows.extend(
            [
                "币本位钱包余额（不含合约浮盈）",
                r["asset"],
                fmt(r["quantity"], precise=True),
                fmt(r["price"], precise=True),
                fmt(r["value"]),
            ]
            for r in coin_assets
        )
        if not coin_assets:
            other_rows.append(["币本位钱包", "无余额", "—", "—", "0.00"])
    else:
        other_rows.append(["币本位钱包", "未取得", "—", "—", "未取得"])
    for key, label, quantity_fields in (
        ("earn", "Simple Earn 活期", ("totalAmount",)),
        ("locked", "Simple Earn 定期", ("amount",)),
        ("funding", "资金账户", ("free", "locked", "freeze", "withdrawing")),
    ):
        if data[key] is None:
            other_rows.append([label, "未取得", "—", "—", "未取得"])
        elif not data[key]:
            other_rows.append([label, "无余额", "—", "—", "0.00"])
        for item in data[key] or []:
            if item["asset"] in IGNORED:
                continue
            r = spot_row(
                item["asset"],
                total(number(item.get(field)) for field in quantity_fields),
                market,
            )
            other_rows.append(
                [
                    label,
                    r["asset"],
                    fmt(r["quantity"], precise=True),
                    fmt(r["price"], precise=True),
                    fmt(r["value"]),
                ]
            )
    bots = next(
        (w for w in data["wallets"] or [] if w.get("walletName") == "Trading Bots"),
        None,
    )
    other_rows.append(
        [
            "交易机器人",
            "币种明细未取得",
            "—",
            "—",
            fmt(number(bots.get("balance")) if bots else None),
        ]
    )
    lines.append(table(["账户", "币种", "数量", "当前价格", "市值"], other_rows))
    coin_positions = data["coin_positions"]
    coin_trades = coin_trade_rows(data, market)
    if coin_trades:
        lines.extend(
            [
                "",
                "### 币本位合约",
                "",
                position_table(coin_trades, coin=True),
                "",
                "币本位数量为合约张数；开仓均价、标记价格原始报价为 USD，名义价值按 1 USD≈1 USDT 估值。逆向合约今日盈亏先按结算币计算，再按现货价格折算 USDT。",
            ]
        )
        for r in coin_trades:
            lines.append(
                f"- {r['symbol']} {r['side']}：接口未实现盈亏 {fmt(r['native_pnl'], signed=True)} {r['asset']}，折合 {fmt(r['pnl'], signed=True)} USDT。"
            )
        for asset in {r["asset"] for r in coin_trades}:
            actual = total(r["native_pnl"] for r in coin_trades if r["asset"] == asset)
            expected = next(
                (
                    number(x.get("unrealizedProfit"))
                    for x in (data["coin"] or {}).get("assets", [])
                    if x["asset"] == asset
                ),
                None,
            )
            if (
                actual is None
                or expected is None
                or abs(actual - expected) > Decimal("0.00000001")
            ):
                warnings.append(f"币本位 {asset} 未实现盈亏与账户未核对一致")
    else:
        lines.extend(
            [
                "",
                "普通币本位账户无未平仓合约。"
                if coin_positions == []
                else "币本位持仓查询失败，不能认定无仓位。",
            ]
        )
    lines.extend(
        [
            "",
            "普通账户接口不覆盖网格内部仓位，不能据此认定网格无仓位。机器人仅列本次接口总余额，内部仓位、开仓价及收益未核实，不纳入今日收益。理财收益同样不计入。",
        ]
    )

    summaries = [
        ("现货价格变动估算", spot_day),
        ("U 本位合约价格变动估算", futures_day),
        (
            "币本位抵押币价格变动估算",
            total(r["day"] for r in coin_assets) if coin_assets is not None else None,
        ),
        (
            "普通币本位合约价格变动估算",
            total(r["day"] for r in coin_trades) if coin_trades is not None else None,
        ),
    ]
    for key, label in (
        ("u_fees", "U 本位资金费净收入"),
        ("c_fees", "普通币本位资金费净收入"),
    ):
        summaries.append((label, funding_fee(data, market, key)))
    combined = total(value for _, value in summaries)
    verified = [value for _, value in summaries if value is not None]
    summaries.append(
        (
            "已覆盖部分合计" if combined is not None else "可核实部分小计（不完整）",
            combined if combined is not None else total(verified) if verified else None,
        )
    )
    lines.extend(
        [
            "",
            "## 4. 今日收益汇总",
            "",
            table(
                ["项目", "USDT"],
                [[label, fmt(value, signed=True)] for label, value in summaries],
            ),
            "",
            "估算按当前持仓和 UTC 零点至查询时价差计算，未调整日内交易、转账、仓位变化及交易手续费；资金费按接口流水单列。不是实际今日盈亏，不含网格及理财收益。资金账户仅列余额，其价格变动不计入该合计。",
            "开仓均价直接读取 entryPrice，当前浮盈直接读取 unrealizedProfit/unRealizedProfit；二者不使用零点价格推算。名义价值按绝对值求和，不计入账户资产。当前浮盈与今日估算盈亏不能相加，也不重复加到账户权益。",
            "持仓收益率＝未实现盈亏÷positionInitialMargin；合计按统一估值后的分子、分母分别求和再相除，排除挂单保证金。缺失或分母为零时不可计算。受杠杆和保证金变化影响，未扣费用，不保证与币安界面 ROI 一致。",
        ]
    )
    all_positions = (futures or []) + (coin_trades or [])
    if any(
        r[key] is None
        for r in all_positions
        for key in ("entry", "mark", "margin", "pnl", "day", "roi", "notional")
    ):
        warnings.append("部分合约价格、初始保证金或盈亏字段缺失/无效，对应字段未计算")
    if started.date() != finished.date():
        warnings.append(
            "查询跨 UTC 日期，报告仍以查询开始日零点为起点，请重新运行取得新交易日报告"
        )
    if warnings:
        lines.extend(["", "## 数据缺口", "", *(f"- {warning}" for warning in warnings)])
    lines.extend(
        ["", "使用技能：binance（脚本通过只读 CLI 调用，不读取或输出密钥）。", ""]
    )
    return "\n".join(lines)


def terminal_report(report):
    if not sys.stdout.isatty():
        return report

    labels = {
        "合计",
        "账户权益（已含未实现盈亏）",
        "钱包余额",
        "持仓初始保证金",
        "挂单初始保证金",
    }
    lines = []
    in_summary = False
    for line in report.splitlines(keepends=True):
        if line.startswith("## "):
            in_summary = line.strip() in {"## 4. 今日收益汇总", "## 账户总价值"}
        if line.startswith(
            ("**现货总市值：", "**账户总价值：", "**可核实账户小计（不完整）：")
        ) or (
            line.startswith("| ")
            and (in_summary or line.split("|")[1].strip() in labels)
        ):
            line = re.sub(
                r"[+-]?\d[\d,]*(?:\.\d+)?%?",
                lambda match: f"\033[38;5;108m{match[0]}\033[0m",
                line,
            )
        lines.append(line)
    return "\033[r\033[0m\033[H\033[2J\033[3J\033[H" + "".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="实时只读 Binance 持仓报告；无第三方 Python 依赖。"
    )
    parser.add_argument(
        "--output", type=Path, help="同时保存 Markdown 报告（覆盖指定文件）"
    )
    parser.add_argument(
        "--timeout", type=int, default=20, help="单请求超时秒数，默认 20"
    )
    args = parser.parse_args()
    if args.timeout < 1 or args.timeout > 60:
        parser.error("timeout 必须介于 1 到 60 秒")
    executable = shutil.which("binance-cli")
    if not executable:
        parser.exit(2, "未找到 binance-cli，请先安装并激活只读 profile。\n")
    warnings = []
    started = datetime.now(UTC)
    data, market = collect(Binance(executable, args.timeout), started, warnings)
    report = render(data, market, started, datetime.now(UTC), warnings)
    print(terminal_report(report))
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())

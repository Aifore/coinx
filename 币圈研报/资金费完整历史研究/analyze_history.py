import json
import math
from bisect import bisect_right
from collections import Counter, defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
HOUR = 3_600_000
DAY = 24 * HOUR
HORIZONS = (7, 30, 90)
TURN_SEARCHES = (
    ("2017_peak", "peak", 2017),
    ("2018_bottom", "bottom", 2018),
    ("2021_peak", "peak", 2021),
    ("2022_bottom", "bottom", 2022),
    ("2025_peak", "peak", 2025),
)


def iso(timestamp):
    return datetime.fromtimestamp(timestamp / 1000, UTC).isoformat()


def ms(date):
    return int(datetime.fromisoformat(date).replace(tzinfo=UTC).timestamp() * 1000)


def load(path):
    return json.loads(path.read_text())


def ratio(numerator, denominator):
    return 100 * numerator / denominator if denominator else None


def quantile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    offset = fraction * (len(ordered) - 1)
    lower = int(offset)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (offset - lower)


def price_summary(values):
    values = [value for value in values if value is not None]
    return {
        "count": len(values),
        "min": min(values) if values else None,
        "p25": quantile(values, 0.25),
        "median": median(values) if values else None,
        "p75": quantile(values, 0.75),
        "max": max(values) if values else None,
    }


def summarize(rows):
    hours = sum(row["h"] for row in rows)
    counts = Counter((row["r"] > 0) - (row["r"] < 0) for row in rows)
    result = {"settlements": len(rows), "observed_cycle_hours": hours}
    for name, sign in (("positive", 1), ("negative", -1), ("zero", 0)):
        sign_hours = sum(
            row["h"] for row in rows if (row["r"] > 0) - (row["r"] < 0) == sign
        )
        result[name] = counts[sign]
        result[f"{name}_percent"] = ratio(counts[sign], len(rows))
        result[f"{name}_duration_percent"] = ratio(sign_hours, hours)
        result[f"{name}_cycle_days"] = sign_hours / 24

    result["mean_rate_percent"] = mean(row["r"] for row in rows) * 100 if rows else None
    result["mean_rate_8h_percent"] = (
        sum(row["r"] for row in rows) / hours * 800 if hours else None
    )
    result["sum_rate_percent"] = sum(row["r"] for row in rows) * 100
    return result


def with_prices(rows, daily, reference_daily=None):
    days = sorted(row["t"] for row in daily)
    closes = {row["t"]: row["close"] for row in daily}
    references = {row["t"]: row["close"] for row in (reference_daily or [])}
    result = []
    for row in rows:
        row = dict(row)
        if row.get("p") is not None and row["p"] > 0:
            row["price_source"] = "settlement_mark_price"
        else:
            index = bisect_right(days, row["t"] // DAY * DAY - DAY) - 1
            # 历史结算缺标记价时，只使用当时已经收盘的日线，避免偷看当日收盘。
            day = days[index] if index >= 0 else None
            if day is not None and row["t"] // DAY * DAY - day > DAY:
                day = None
            row["p"] = closes[day] if day is not None else None
            row["price_source"] = (
                "previous_completed_daily_close" if day is not None else None
            )
            if day is None:
                previous_day = row["t"] // DAY * DAY - DAY
                row["p"] = references.get(previous_day)
                row["price_source"] = (
                    "previous_day_coinmetrics_reference"
                    if row["p"] is not None
                    else None
                )
        result.append(row)
    return result


def contiguous(previous, current):
    return current["t"] - previous["t"] <= current["h"] * HOUR + 60_000


def longest_run(rows, positive):
    best = []
    current = []
    best_hours = current_hours = 0
    for index, row in enumerate(rows):
        matches = row["r"] > 0 if positive else row["r"] < 0
        if not matches or (index and not contiguous(rows[index - 1], row)):
            current = []
            current_hours = 0
        if matches:
            current.append(row)
            current_hours += row["h"]
            if current_hours > best_hours:
                best = current.copy()
                best_hours = current_hours

    prices = [row["p"] for row in best if row["p"] is not None]
    return {
        "first_utc": iso(best[0]["t"]) if best else None,
        "last_utc": iso(best[-1]["t"]) if best else None,
        "count": len(best),
        "cycle_days": best_hours / 24,
        "elapsed_days": (best[-1]["t"] - best[0]["t"]) / DAY if best else 0,
        "price_min": min(prices) if prices else None,
        "price_max": max(prices) if prices else None,
    }


def monthly_summary(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[iso(row["t"])[:7]].append(row)
    return [
        {
            "month": month,
            "summary": summarize(group),
            "positive_price": price_summary(
                [row["p"] for row in group if row["r"] > 0]
            ),
            "negative_price": price_summary(
                [row["p"] for row in group if row["r"] < 0]
            ),
        }
        for month, group in sorted(groups.items())
    ]


def price_bins(rows):
    prices = [row["p"] for row in rows if row["p"] is not None]
    if not prices:
        return None, []
    target = median(prices) / 8
    magnitude = 10 ** math.floor(math.log10(target))
    width = min((1, 2, 2.5, 5, 10), key=lambda value: abs(value * magnitude - target))
    width *= magnitude
    groups = defaultdict(list)
    for row in rows:
        if row["p"] is not None:
            groups[math.floor(row["p"] / width) * width].append(row)
    total_positive = sum(row["r"] > 0 for row in rows)
    total_negative = sum(row["r"] < 0 for row in rows)
    result = []
    for low, group in sorted(groups.items()):
        positive = sum(row["r"] > 0 for row in group)
        negative = sum(row["r"] < 0 for row in group)
        result.append(
            {
                "low": low,
                "high": low + width,
                "total": len(group),
                "positive": positive,
                "negative": negative,
                "positive_share_of_sign_percent": ratio(positive, total_positive),
                "negative_share_of_sign_percent": ratio(negative, total_negative),
                "positive_rate_percent": ratio(positive, len(group)),
                "negative_rate_percent": ratio(negative, len(group)),
            }
        )
    return width, result


def turning_points(daily, source):
    points = []
    for point_id, kind, year in TURN_SEARCHES:
        start, end = ms(f"{year}-01-01"), ms(f"{year + 1}-01-01")
        candles = [row for row in daily if start <= row["t"] < end]
        if not candles:
            continue
        field = "high" if kind == "peak" else "low"
        choose = max if kind == "peak" else min
        candle = choose(candles, key=lambda row: row[field])
        points.append(
            {
                "id": point_id,
                "date": iso(candle["t"])[:10],
                "t": candle["t"],
                "kind": kind,
                "price": candle[field],
                "price_field": field,
                "source": source,
                "search_start": iso(start),
                "search_end": iso(end),
                "search_days_available": len(candles),
            }
        )
    return points


def make_phases(points, start, end):
    result = []
    cursor = start
    for point in points:
        if point["t"] < start:
            continue
        boundary = point["t"] + DAY
        if boundary >= end:
            break
        prefix = "牛市" if point["kind"] == "peak" else "熊市"
        result.append(
            {
                "id": f"to_{point['id']}",
                "label": f"{iso(cursor)[:10]}—{point['date']} {prefix}",
                "start": cursor,
                "end": boundary,
                "start_utc": iso(cursor),
                "end_utc": iso(boundary),
                "retrospective": True,
                "partial_cycle": not result,
            }
        )
        cursor = boundary
    result.append(
        {
            "id": "after_last_peak_unconfirmed",
            "label": f"{iso(cursor)[:10]}—{iso(end - DAY)[:10]} 高点后观察期（底部未确认）",
            "start": cursor,
            "end": end,
            "start_utc": iso(cursor),
            "end_utc": iso(end),
            "retrospective": True,
            "partial_cycle": True,
        }
    )
    return result


def phase_for(timestamp, phases):
    return next(
        (phase["id"] for phase in phases if phase["start"] <= timestamp < phase["end"]),
        None,
    )


def outcomes(entry, candles):
    if entry not in candles:
        return {}
    price = candles[entry]["open"]
    result = {}
    for horizon in HORIZONS:
        days = [entry + index * DAY for index in range(horizon)]
        if any(day not in candles for day in days):
            continue
        result[str(horizon)] = {
            "return_percent": (candles[days[-1]]["close"] / price - 1) * 100,
            "mae_percent": min(
                0, (min(candles[day]["low"] for day in days) / price - 1) * 100
            ),
        }
    return result


def performance(records, horizon):
    selected = [
        row["outcomes"][str(horizon)]
        for row in records
        if str(horizon) in row["outcomes"]
    ]
    if not selected:
        return {"n": 0}
    returns = [row["return_percent"] for row in selected]
    drawdowns = [row["mae_percent"] for row in selected]
    return {
        "n": len(selected),
        "win_percent": ratio(sum(value > 0 for value in returns), len(returns)),
        "mean_return_percent": mean(returns),
        "median_return_percent": median(returns),
        "return_p10_percent": quantile(returns, 0.1),
        "median_mae_percent": median(drawdowns),
        "worst_mae_percent": min(drawdowns),
    }


def comparison(signals, baseline):
    return {
        str(horizon): {
            "signal": performance(signals, horizon),
            "baseline": performance(baseline, horizon),
        }
        for horizon in HORIZONS
    }


def phase_matched_baseline(signals, baseline):
    result = {}
    for horizon in HORIZONS:
        eligible = [row for row in signals if str(horizon) in row["outcomes"]]
        control = {
            phase: performance(
                [row for row in baseline if row["phase"] == phase], horizon
            )
            for phase in {row["phase"] for row in eligible}
        }
        valid = [row for row in eligible if control[row["phase"]]["n"]]
        result[str(horizon)] = {
            "matched_signal_count": len(valid),
            "weighted_baseline_mean_return_percent": mean(
                control[row["phase"]]["mean_return_percent"] for row in valid
            )
            if valid
            else None,
            "weighted_baseline_win_percent": mean(
                control[row["phase"]]["win_percent"] for row in valid
            )
            if valid
            else None,
        }
    return result


def backtest(rows, daily, phases):
    candles = {row["t"]: row for row in daily}
    lookback = deque()
    negatives = 0
    uninterrupted_start = rows[0]["t"]
    eligible_days = set()
    candidates = []
    for index, row in enumerate(rows):
        if index and not contiguous(rows[index - 1], row):
            uninterrupted_start = row["t"]
        while lookback and lookback[0]["t"] <= row["t"] - 7 * DAY:
            negatives -= lookback.popleft()["r"] < 0
        lookback.append(row)
        negatives += row["r"] < 0
        if row["t"] - uninterrupted_start < 7 * DAY:
            continue
        entry = row["t"] // DAY * DAY + DAY
        if entry not in candles:
            continue
        eligible_days.add(entry)
        if row["r"] < 0 and negatives / len(lookback) >= 0.7:
            candidates.append(
                (row, entry, negatives / len(lookback) * 100, len(lookback))
            )

    signals = []
    last_entry = -90 * DAY
    for row, entry, negative_share, count in candidates:
        if entry - last_entry < 90 * DAY:
            continue
        last_entry = entry
        signals.append(
            {
                "signal_utc": iso(row["t"]),
                "entry_utc": iso(entry),
                "entry_t": entry,
                "phase": phase_for(entry, phases),
                "year": iso(entry)[:4],
                "entry_price": candles[entry]["open"],
                "negative_share_percent": negative_share,
                "lookback_settlements": count,
                "outcomes": outcomes(entry, candles),
            }
        )
    baseline = [
        {
            "phase": phase_for(entry, phases),
            "year": iso(entry)[:4],
            "outcomes": outcomes(entry, candles),
        }
        for entry in sorted(eligible_days)
    ]
    complete = [row for row in signals if "90" in row["outcomes"]]
    full_baseline = [row for row in baseline if "90" in row["outcomes"]]
    groups = {}
    for field in ("phase", "year"):
        groups[f"by_{field}"] = {
            name: comparison(
                [row for row in complete if row[field] == name],
                [row for row in full_baseline if row[field] == name],
            )
            for name in sorted({row[field] for row in baseline} - {None})
        }
    return {
        "rule": "预设过去7天结算次数中负费率>=70%，当前结算为负；下一UTC日现货开盘买入；信号入场间隔至少90天。",
        "candidate_settlements": len(candidates),
        "signals": signals,
        "complete_90d_signal_count": len(complete),
        "tail_incomplete_90d_signal_count": len(signals) - len(complete),
        "overall": comparison(complete, full_baseline),
        "phase_matched_baseline": phase_matched_baseline(complete, full_baseline),
        "per_horizon_available": comparison(signals, baseline),
        **groups,
    }


def analyze_dataset(path, phases):
    dataset_id = path.name.removesuffix("-funding.json")
    source, symbol = dataset_id.split("-", 1)
    price_path = RAW / f"{dataset_id}-spot-daily.json"
    if source == "bitmex":
        price_symbol = "ETHUSDT" if symbol == "ETHUSD" else "BTCUSDT"
        price_path = RAW / f"binance-{price_symbol}-spot-daily.json"
    daily = sorted(load(price_path), key=lambda row: row["t"])
    rows = sorted(
        ({**row, "t": row["t"] // 60_000 * 60_000} for row in load(path)),
        key=lambda row: row["t"],
    )
    assert len({row["t"] for row in rows}) == len(rows), f"Duplicate funding: {path}"
    assert all(row["h"] > 0 for row in rows), f"Invalid intervals: {path}"
    assert len({row["t"] for row in daily}) == len(daily), (
        f"Duplicate candles: {price_path}"
    )
    reference_path = RAW / "coinmetrics-BTCUSD-reference-daily.json"
    references = (
        load(reference_path)
        if source == "bitmex" and symbol == "XBTUSD" and reference_path.exists()
        else []
    )
    rows = with_prices(rows, daily, references)
    phase_results = []
    for phase in phases:
        selected = [row for row in rows if phase["start"] <= row["t"] < phase["end"]]
        if not selected:
            continue
        width, bins = price_bins(selected)
        monthly = monthly_summary(selected)
        phase_results.append(
            {
                **phase,
                "coverage_start_utc": iso(selected[0]["t"]),
                "coverage_end_utc": iso(selected[-1]["t"]),
                "summary": summarize(selected),
                "longest_positive": longest_run(selected, True),
                "longest_negative": longest_run(selected, False),
                "monthly": monthly,
                "most_negative_months": sorted(
                    monthly, key=lambda row: row["summary"]["negative"], reverse=True
                )[:3],
                "most_positive_months": sorted(
                    monthly, key=lambda row: row["summary"]["positive"], reverse=True
                )[:3],
                "price_bin_width": width,
                "price_bins": bins,
            }
        )
    return {
        "id": dataset_id,
        "symbol": symbol,
        "source": source,
        "price_source": price_path.name,
        "early_price_reference": reference_path.name if references else None,
        "start_utc": iso(rows[0]["t"]),
        "end_utc": iso(rows[-1]["t"]),
        "total": summarize(rows),
        "data_quality": {
            "backtest_ohlc_start_utc": iso(daily[0]["t"]),
            "backtest_ohlc_end_utc": iso(daily[-1]["t"]),
            "funding_observations_before_backtest_ohlc": sum(
                row["t"] < daily[0]["t"] for row in rows
            ),
            "funding_interval_hour_counts": dict(Counter(row["h"] for row in rows)),
            "price_assignment_counts": dict(
                Counter(row["price_source"] for row in rows)
            ),
            "funding_gaps": [
                {
                    "previous": iso(a["t"]),
                    "next": iso(b["t"]),
                    "gap_hours": (b["t"] - a["t"]) / HOUR,
                }
                for a, b in zip(rows, rows[1:])
                if not contiguous(a, b)
            ],
        },
        "phases": phase_results,
        "backtest": backtest(rows, daily, phases),
    }


def self_check():
    rows = [
        {"t": index * 8 * HOUR + 2, "r": -0.001, "h": 8, "p": None}
        for index in range(400)
    ]
    daily = [
        {"t": index * DAY, "open": 100, "high": 102, "low": 90, "close": 101}
        for index in range(150)
    ]
    phases = [
        {"id": "first", "start": 0, "end": 10 * DAY},
        {"id": "second", "start": 10 * DAY, "end": 160 * DAY},
    ]
    assert phase_for(10 * DAY - 1, phases) == "first"
    assert phase_for(10 * DAY, phases) == "second"
    assigned = with_prices(rows[:4], daily)
    assert assigned[0]["p"] is None and assigned[3]["p"] == 101
    test = backtest(rows, daily, phases)
    assert test["signals"][0]["entry_t"] == 8 * DAY
    assert test["signals"][1]["entry_t"] == 98 * DAY
    assert math.isclose(test["signals"][0]["outcomes"]["7"]["return_percent"], 1)
    assert math.isclose(test["signals"][0]["outcomes"]["90"]["mae_percent"], -10)
    changed = [dict(row) for row in daily]
    changed[9]["close"] = 1000
    assert backtest(rows, changed, phases)["signals"][0]["entry_t"] == 8 * DAY
    assert outcomes(149 * DAY, {row["t"]: row for row in daily}) == {}
    mixed = [{"r": 0.001, "h": 24}, {"r": -0.001, "h": 8}]
    assert summarize(mixed)["positive_percent"] == 50
    assert summarize(mixed)["positive_duration_percent"] == 75


def main():
    self_check()
    funding_paths = sorted(RAW.glob("*-funding.json"))
    funding_paths = [
        path for path in funding_paths if path.name.startswith(("binance-", "bitmex-"))
    ]
    reference = RAW / "binance-BTCUSDT-spot-daily.json"
    points = turning_points(load(reference), reference.name)
    start = min(row["t"] for path in funding_paths for row in load(path)) // DAY * DAY
    end = (
        max(row["t"] for path in funding_paths for row in load(path)) // DAY * DAY + DAY
    )
    phases = make_phases(points, start, end)
    result = {
        "created_date": "2026-10-02",
        "turning_points": points,
        "phase_definitions": phases,
        "methodology": {
            "phase_boundary": "BTC指定年度日线最高high/最低low事后选点；拐点日整体归前一段，下一UTC日开始后一段；ETH按BTC周期对齐，并非ETH独立顶底。",
            "phase_caveat": "事后周期标签仅用于研究分组，不参与买入信号；2018低点至2021高点内含2020年3月及2021年中大回撤。最终观察期的熊市底部尚未确认。",
            "funding_units": "r为原始结算小数费率；展示百分比乘100；跨周期比较以r*8/h归一到8小时。",
            "timestamp_normalization": "分析将结算时间归一到整分钟，消除币安几毫秒抖动使7日滚动窗错误计入20/22条的影响；raw保留原始时间。",
            "duration": "时长占比=sum(符合符号结算的h)/sum(全部结算h)，属于结算周期时长加权，非逐秒预测费率占比；按结算时间归段，边界周期不拆分。",
            "price_bins": "各阶段以中位价格/8取邻近1、2、2.5、5、10倍十进制箱宽；左闭右开。占全部同号次数与箱内同号比例分列。",
            "price_alignment": "优先同次结算标记价；缺失则用上一已完成UTC日现货close；BitMEX BTC在币安日线开始前使用CoinMetrics上一UTC日PriceUSD（官方定义为当日收盘，次日才可用）。均仅作为粗略价格区域，非精确结算价。",
            "backtest": "只用当时及之前7天资金费，负费率次数>=70%且当前为负；次UTC日开盘买入现货；无杠杆、不计资金费收入；持有7/30/90日，以第N日收盘退出；MAE为持有期间最低low/entry-1，最多0。",
            "backtest_dedup": "按时间顺序首个触发入选，后续90日不重复入场，跨阶段不重置；主表仅含未来90日完整样本，使7/30/90日使用相同信号。",
            "baseline": "同一数据源、同期、历史资金费满足7日连续观测的所有可入场日期；主表同样要求90日价格完整。按阶段/年度分组，基线日期彼此重叠，不能按样本数当作独立试验。",
            "limitations": "门槛为本研究事先固定的描述性规则，但作者已见过部分2025-2026数据，不构成严格样本外检验；未优化阈值、未计手续费和滑点；BitMEX与币安为不同合约人群，仅分别统计；两平台信号均用对应币种的币安USDT现货日线测后续收益。2017-08-17前无该OHLC，不伪造收益/MAE。所有信号与基线均可能存在市场状态混杂。",
        },
        "datasets": [analyze_dataset(path, phases) for path in funding_paths],
    }
    output = ROOT / "analysis.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    for dataset in result["datasets"]:
        print(
            json.dumps(
                {
                    "id": dataset["id"],
                    "start": dataset["start_utc"],
                    "end": dataset["end_utc"],
                    "settlements": dataset["total"]["settlements"],
                    "signals_90d": dataset["backtest"]["complete_90d_signal_count"],
                    "performance": dataset["backtest"]["overall"],
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()

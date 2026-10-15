import unittest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

from binance_report import (
    Binance,
    account_values,
    collect,
    contract_summary,
    core_data_missing,
    daily_breakdown,
    overview,
    number,
    percent,
    position_row,
    render,
    spot_summary,
    table,
    terminal_report,
    total,
    utc_start,
)


class ReportTest(unittest.TestCase):
    def test_account_total_uses_equity_without_double_counting(self):
        data = dict(
            earn=[{"asset": "USDC", "totalAmount": "50"}],
            locked=[{"asset": "USDT", "amount": "25"}],
            funding=[
                dict(asset="USDT", free="1", locked="2", freeze="3", withdrawing="4")
            ],
            usds={
                "totalMarginBalance": "999",
                "assets": [
                    {"asset": "USDT", "marginBalance": "20"},
                    {"asset": "USDC", "marginBalance": "5"},
                    {"asset": "BNB", "marginBalance": "0"},
                ],
            },
            coin={
                "assets": [
                    {"asset": "BTC", "walletBalance": "0.003", "marginBalance": "0.002"}
                ]
            },
            wallets=[
                {"walletName": "Trading Bots", "balance": "30"},
                {"walletName": "Spot", "balance": "100"},
                {"walletName": "Earn", "balance": "75"},
                {"walletName": "Cross Margin", "balance": "0"},
            ],
        )
        market = {
            asset: {"lastPrice": price}
            for asset, price in (("USDT", "1"), ("USDC", "1"), ("BTC", "30000"))
        }
        values = account_values(data, market, Decimal(100))
        self.assertEqual(total(value for _, value in values), Decimal(300))
        data["earn"].append({"asset": "LDUSDC", "totalAmount": "50"})
        self.assertEqual(
            total(value for _, value in account_values(data, market, Decimal(100))),
            Decimal(300),
        )

        for key, replacement in (
            ("coin", None),
            ("usds", {}),
            ("earn", None),
            ("wallets", []),
            (
                "wallets",
                [
                    {"walletName": "Trading Bots", "balance": "30"},
                    {"walletName": "Cross Margin", "balance": "5"},
                ],
            ),
        ):
            with self.subTest(key=key, replacement=replacement):
                incomplete = account_values(
                    {**data, key: replacement}, market, Decimal(100)
                )
                self.assertIsNone(total(value for _, value in incomplete))
        self.assertIsNone(
            total(
                value
                for _, value in account_values(
                    data, {"USDT": market["USDT"]}, Decimal(100)
                )
            )
        )

        now = datetime(2026, 9, 21, tzinfo=UTC)
        data.update(
            spot={"balances": [{"asset": "USDT", "free": "80", "locked": "20"}]},
            orders=None,
            positions=[],
            coin_positions=[],
            u_fees=[],
            c_fees=[],
        )
        report = render(data, market, now, now, [])
        self.assertIn("**账户总价值：300.00 USDT**", report)
        self.assertNotIn("可核实账户小计（不完整）", report)
        report = render({**data, "earn": None}, market, now, now, [])
        self.assertIn("**账户总价值：未取得 USDT**", report)
        self.assertIn("**可核实账户小计（不完整）：250.00 USDT**", report)
        self.assertIn("账户总价值未完整取得：Simple Earn 活期", report)

    def test_summary_color_only_in_terminal(self):
        details = table(["币种", "市值"], [["BTC", "123.00"], ["合计", "123.00"]])
        report = (
            "**账户总价值：3,456.78 USDT**\n"
            "**现货总市值：1,234.56 USDT｜今日估算浮盈：-2.00 USDT**\n"
            f"{details}\n"
            "## 4. 今日收益汇总\n"
            "| 项目 | USDT |\n| 现货价格变动估算 | +2.50 |\n"
            "| 可核实部分小计（不完整） | 未取得 |\n"
            "## 数据缺口\n- 连接失败 2 次\n"
        )
        with patch("sys.stdout.isatty", return_value=True):
            colored = terminal_report(report)
        clear_screen = "\033[r\033[0m\033[H\033[2J\033[3J\033[H"
        self.assertTrue(colored.startswith(clear_screen))
        for value in ("3,456.78", "1,234.56", "-2.00", "123.00", "+2.50"):
            self.assertIn(f"\033[38;5;108m{value}\033[0m", colored)
        self.assertIn(details.splitlines()[2], colored)
        self.assertIn("| 可核实部分小计（不完整） | 未取得 |", colored)
        self.assertIn("- 连接失败 2 次", colored)
        self.assertEqual(
            colored.removeprefix(clear_screen)
            .replace("\033[38;5;108m", "")
            .replace("\033[0m", ""),
            report,
        )
        with patch("sys.stdout.isatty", return_value=False):
            self.assertEqual(terminal_report(report), report)

    def test_table_terminal_alignment(self):
        self.assertEqual(
            table(
                ["币种", "市值", "涨幅"],
                [["BTC", "1,234.56", "+2.00%"], ["合计", "未取得", "—"]],
            ),
            "| 币种 |     市值 |   涨幅 |\n"
            "| ---- | -------- | ------ |\n"
            "| BTC  | 1,234.56 | +2.00% |\n"
            "| 合计 |   未取得 |      — |",
        )
        self.assertEqual(table(["币种"], []), "| 币种 |\n| ---- |")
        self.assertEqual(
            table(["名称"], [["e\u0301"], ["A|B"]]),
            "| 名称 |\n| ---- |\n| e\u0301    |\n| A/B  |",
        )

    def test_utc_and_missing_values(self):
        self.assertEqual(
            utc_start(datetime.fromisoformat("2026-09-21T02:00:00+08:00")),
            datetime(2026, 9, 20, tzinfo=UTC),
        )
        self.assertIsNone(total([number("2"), None]))
        self.assertIsNone(number("NaN"))
        self.assertIsNone(percent(number("1"), number("0")))
        self.assertEqual(total([]), Decimal(0))

    def test_long_short_and_margin_roi(self):
        market = {"USDT": {"lastPrice": "1"}, "futures-usds:BTCUSDT": [[0, "100"]]}
        position = dict(
            symbol="BTCUSDT",
            positionAmt="2",
            positionSide="LONG",
            entryPrice="90",
            markPrice="110",
            unRealizedProfit="40",
            marginAsset="USDT",
            positionInitialMargin="10",
            initialMargin="100",
            notional="220",
        )
        row = position_row(position, market)
        self.assertEqual(row["day"], Decimal(20))
        self.assertEqual(row["roi"], Decimal(400))
        self.assertEqual(row["entry"], Decimal(90))
        position.update(positionSide="SHORT", unRealizedProfit="-40", notional="-220")
        row = position_row(position, market)
        self.assertEqual(row["day"], Decimal(-20))
        self.assertEqual(row["notional"], Decimal(220))
        self.assertEqual(row["roi"], Decimal(-400))
        position.pop("positionInitialMargin")
        self.assertIsNone(position_row(position, market)["roi"])

    def test_inverse_contract(self):
        market = {
            "DOGE": {"lastPrice": "0.1"},
            "futures-coin:DOGEUSD_PERP": [[0, "0.08"]],
        }
        position = dict(
            symbol="DOGEUSD_PERP",
            positionAmt="2",
            positionSide="LONG",
            entryPrice="0.08",
            markPrice="0.1",
            unRealizedProfit="50",
            positionInitialMargin="20",
        )
        row = position_row(
            position,
            market,
            coin=True,
            metadata={"marginAsset": "DOGE", "contractSize": "10"},
        )
        self.assertEqual(row["day"], Decimal(5))
        self.assertEqual(row["pnl"], Decimal(5))
        self.assertEqual(row["notional"], Decimal(20))
        self.assertEqual(row["roi"], Decimal(250))

    def test_write_commands_denied(self):
        with self.assertRaises(ValueError):
            Binance("unused").call("spot", "new-order")
        with self.assertRaises(ValueError):
            Binance("unused").call("request", "https://dapi.binance.com/dapi/v1/order")

    def test_raw_request_uses_signed_get_with_camel_case_params(self):
        url = "https://dapi.binance.com/dapi/v1/income"
        with patch("binance_report.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = '[{"tranId": 1600035591563102480}]'
            rows = Binance("cli").call("request", url, income_type="FUNDING_FEE")
        self.assertEqual(
            run.call_args.args[0],
            ["cli", "request", "--signed", "GET", url, "--incomeType", "FUNDING_FEE"],
        )
        self.assertEqual(rows[0]["tranId"], 1600035591563102480)

    def test_pagination(self):
        client = Binance("unused")
        with patch.object(
            client,
            "call",
            side_effect=[{"rows": [1], "total": 2}, {"rows": [2], "total": 2}],
        ):
            self.assertEqual(
                client.paged("simple-earn", "get-flexible-product-position"), [1, 2]
            )
        with patch.object(client, "call", return_value={"rows": [], "total": 2}):
            with self.assertRaises(ValueError):
                client.paged("simple-earn", "get-flexible-product-position")

    def test_failures_are_not_zero_balances(self):
        data = dict.fromkeys(
            (
                "spot",
                "orders",
                "positions",
                "usds",
                "coin",
                "coin_positions",
                "earn",
                "locked",
                "funding",
                "wallets",
                "u_fees",
                "c_fees",
            )
        )
        now = datetime(2026, 9, 21, tzinfo=UTC)
        report = render(data, {}, now, now, ["连接失败"])
        self.assertIn("现货总市值：未取得", report)
        self.assertIn("| 可核实部分小计（不完整） | 未取得 |", " ".join(report.split()))
        self.assertNotIn("普通币本位账户无未平仓合约", report)

    def test_daily_breakdown_marks_failed_groups(self):
        data = dict(
            spot={"balances": [{"asset": "BTC", "free": "2", "locked": "0"}]},
            positions=None,
            coin={"assets": []},
            coin_positions=[],
            u_fees=[{"asset": "USDT", "income": "0.5"}],
            c_fees=[],
        )
        market = {
            "USDT": {"lastPrice": "1"},
            "BTC": {"lastPrice": "110", "openPrice": "100"},
        }
        spot, contract, funding = daily_breakdown(data, market)
        self.assertEqual((spot[0]["name"], spot[0]["day"]), ("BTC", Decimal(20)))
        summary = spot_summary(spot)
        self.assertEqual(summary["value"], Decimal(220))
        self.assertEqual(summary["change"], Decimal(10))
        self.assertEqual(
            contract, [dict(name="U 本位持仓未取得", day=None, failed=True)]
        )
        self.assertEqual(funding, Decimal("0.5"))
        data.update(
            positions=[],
            coin_positions=[dict(symbol="LTCUSD_PERP", positionAmt="98")],
        )
        _, contract, _ = daily_breakdown(data, market)
        self.assertEqual(contract[0]["quantity_unit"], "张")
        summary = contract_summary(contract, funding)
        self.assertIsNone(summary["day"])
        self.assertIsNone(summary["notional"])

    def test_coin_margin_collateral_stays_out_of_spot(self):
        data = dict(
            spot={"balances": [{"asset": "DOGE", "free": "100", "locked": "0"}]},
            positions=[],
            coin={"assets": [{"asset": "DOGE", "walletBalance": "50"}]},
            coin_positions=[],
            u_fees=[],
            c_fees=[],
        )
        market = {"DOGE": {"lastPrice": "2", "openPrice": "1"}}
        spot, contract, _ = daily_breakdown(data, market)
        self.assertEqual([row["quantity"] for row in spot], [Decimal(100)])
        self.assertEqual([row["name"] for row in contract], ["DOGE 抵押"])

    def test_overview_sums_each_coin_across_accounts(self):
        data = dict(
            spot={"balances": [{"asset": "DOGE", "free": "100", "locked": "0"}]},
            earn=[],
            locked=[],
            funding=[
                {
                    "asset": "DOGE",
                    "free": "10",
                    "locked": "0",
                    "freeze": "0",
                    "withdrawing": "0",
                }
            ],
            usds={"assets": [{"asset": "USDT", "marginBalance": "100"}]},
            coin={"assets": [{"asset": "DOGE", "marginBalance": "40"}]},
            wallets=[{"walletName": "Trading Bots", "balance": "50"}],
        )
        market = {"DOGE": {"lastPrice": "2"}, "USDT": {"lastPrice": "1"}}
        rows, summary = overview(data, market)
        doge = next(row for row in rows if row["name"] == "DOGE")
        self.assertEqual(
            (doge["quantity"], doge["price"], doge["value"]),
            (Decimal(150), Decimal(2), Decimal(300)),
        )
        self.assertEqual(summary["value"], Decimal(450))
        self.assertEqual(doge["share"] * 3, Decimal(200))

        data["usds"] = None
        rows, summary = overview(data, market)
        self.assertIsNone(summary["value"])
        self.assertIn("U 本位账户权益未取得", [row["name"] for row in rows])

    def test_collect_fetches_btc_ticker_without_holding(self):
        now = datetime(2026, 1, 2, 3, tzinfo=UTC)
        day = int(utc_start(now).timestamp() * 1000)
        client = Binance("binance-cli")
        ticker = {"lastPrice": "100000", "openPrice": "98000", "openTime": day}

        def fake_call(group, command, **_):
            return ticker if command == "ticker-trading-day" else {}

        with (
            patch.object(client, "call", side_effect=fake_call) as call,
            patch.object(client, "paged", return_value=[]),
        ):
            _, market = collect(client, now, [])
        self.assertEqual(market["BTC"], ticker)
        call.assert_any_call(
            "spot", "ticker-trading-day", symbol="BTCUSDT", time_zone="0:00"
        )

    def test_core_data_missing_only_when_all_core_endpoints_failed(self):
        self.assertTrue(
            core_data_missing(dict(spot=None, positions=None, usds=None, coin=1))
        )
        self.assertFalse(
            core_data_missing(dict(spot=None, positions=[], usds=None, coin=None))
        )

    def test_contract_summary_roi_uses_total_margin(self):
        rows = [
            dict(
                name="A",
                notional=Decimal(100),
                margin=Decimal(10),
                pnl=Decimal(5),
                day=Decimal(1),
            ),
            dict(
                name="B",
                notional=Decimal(300),
                margin=Decimal(30),
                pnl=Decimal(-1),
                day=Decimal(2),
            ),
        ]
        summary = contract_summary(rows, Decimal("0.5"))
        self.assertEqual(summary["notional"], Decimal(400))
        self.assertEqual(summary["roi"], Decimal(10))
        self.assertEqual(summary["day"], Decimal("3.5"))


if __name__ == "__main__":
    unittest.main()

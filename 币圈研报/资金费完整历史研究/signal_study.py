import json
from bisect import bisect_left
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median

from analyze_history import DAY, quantile, with_prices

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
HORIZONS = (30, 90)
DENSE_WINDOW_DAYS = 30
EPISODE_GAP_DAYS = 30
EVENT_COOLDOWN_DAYS = 30
DATASETS = (
    ("binance-BTCUSDT", "binance-BTCUSDT-spot-daily"),
    ("binance-ETHUSDT", "binance-ETHUSDT-spot-daily"),
    ("bitmex-XBTUSD", "binance-BTCUSDT-spot-daily"),
)
APR_BUCKETS = (
    ("< 0%", None, 0),
    ("0—5%", 0, 5),
    ("5—10%", 5, 10),
    ("10—20%", 10, 20),
    ("20—40%", 20, 40),
    ("≥ 40%", 40, None),
)
NEGATIVE_SHARE_BUCKETS = (
    ("0%", None, 0.001),
    ("0—30%", 0.001, 30),
    ("30—50%", 30, 50),
    ("50—70%", 50, 70),
    ("≥ 70%", 70, None),
)
TREND_COMBOS = (
    ("低费率 <5% · 200日线上方", lambda row: row["apr_7d"] < 5 and row["above_ma200"]),
    (
        "低费率 <5% · 200日线下方",
        lambda row: row["apr_7d"] < 5 and not row["above_ma200"],
    ),
    (
        "中费率 5—20% · 200日线上方",
        lambda row: 5 <= row["apr_7d"] < 20 and row["above_ma200"],
    ),
    (
        "高费率 ≥20% · 200日线上方",
        lambda row: row["apr_7d"] >= 20 and row["above_ma200"],
    ),
    ("全部 · 200日线上方", lambda row: row["above_ma200"]),
    ("全部 · 200日线下方", lambda row: not row["above_ma200"]),
)
PERCENTILE_BUCKETS = (
    ("最低 10%", None, 10),
    ("10—30%", 10, 30),
    ("30—70%", 30, 70),
    ("70—90%", 70, 90),
    ("最高 10%", 90, None),
)


def day_label(timestamp):
    return datetime.fromtimestamp(timestamp / 1000, UTC).date().isoformat()


def load(name):
    return json.loads((RAW / f"{name}.json").read_text())


def rate_8h(row):
    return row["r"] * 8 / row["h"]


def daily_features(funding, candles):
    times = [row["t"] for row in funding]
    rates = [rate_8h(row) for row in funding]
    closes = {day: candle["close"] for day, candle in candles.items()}
    history_7d = []
    features = []
    first_day = funding[0]["t"] // DAY * DAY + 7 * DAY
    last_day = funding[-1]["t"] // DAY * DAY
    for day in range(first_day, last_day + DAY, DAY):
        # 只用 D 日 24:00 之前已结算的记录，D+1 开盘入场，不偷看入场时点的结算。
        end = bisect_left(times, day + DAY)
        start_7d = bisect_left(times, day + DAY - 7 * DAY)
        start_30d = bisect_left(times, day + DAY - 30 * DAY)
        window_7d = rates[start_7d:end]
        if len(window_7d) < 18 or day not in closes:
            continue

        mean_7d = mean(window_7d)
        prior = history_7d[-365:]
        percentile = (
            100 * sum(value < mean_7d for value in prior) / len(prior)
            if len(prior) >= 180
            else None
        )
        history_7d.append(mean_7d)
        recent_closes = [
            closes[d] for d in range(day - 89 * DAY, day + DAY, DAY) if d in closes
        ]
        closes_200d = [
            closes[d] for d in range(day - 199 * DAY, day + DAY, DAY) if d in closes
        ]
        features.append(
            {
                "day": day,
                "apr_7d": mean_7d * 3 * 365 * 100,
                "apr_30d": mean(rates[start_30d:end]) * 3 * 365 * 100,
                "negative_share_7d": 100
                * sum(rate < 0 for rate in window_7d)
                / len(window_7d),
                "percentile_7d": percentile,
                "drawdown_90d": (closes[day] / max(recent_closes) - 1) * 100,
                "above_ma200": len(closes_200d) == 200
                and closes[day] > mean(closes_200d),
            }
        )
    return features


def forward(entry, candles, horizon):
    days = [entry + index * DAY for index in range(horizon)]
    if any(day not in candles for day in days):
        return None
    price = candles[entry]["open"]
    return {
        "return": (candles[days[-1]]["close"] / price - 1) * 100,
        "mae": min(0, (min(candles[d]["low"] for d in days) / price - 1) * 100),
    }


def attach_outcomes(features, candles):
    for row in features:
        row["outcomes"] = {
            horizon: forward(row["day"] + DAY, candles, horizon) for horizon in HORIZONS
        }


def episodes(days):
    count = 0
    previous = None
    for day in sorted(days):
        if previous is None or day - previous > EPISODE_GAP_DAYS * DAY:
            count += 1
        previous = day
    return count


def stats(rows, horizon):
    selected = [row for row in rows if row["outcomes"][horizon]]
    if not selected:
        return {"n": 0}
    returns = [row["outcomes"][horizon]["return"] for row in selected]
    maes = [row["outcomes"][horizon]["mae"] for row in selected]
    return {
        "n": len(selected),
        "episodes": episodes(row["day"] for row in selected),
        "mean": mean(returns),
        "median": median(returns),
        "win": 100 * sum(value > 0 for value in returns) / len(returns),
        "p10": quantile(returns, 0.1),
        "median_mae": median(maes),
        "worst_mae": min(maes),
    }


def in_bucket(value, low, high):
    return (
        value is not None
        and (low is None or value >= low)
        and (high is None or value < high)
    )


def bucket_table(features, field, buckets):
    return [
        {
            "bucket": label,
            **{
                str(horizon): stats(
                    [row for row in features if in_bucket(row[field], low, high)],
                    horizon,
                )
                for horizon in HORIZONS
            },
        }
        for label, low, high in buckets
    ]


def trend_table(features):
    return [
        {
            "bucket": label,
            **{
                str(horizon): stats([row for row in features if match(row)], horizon)
                for horizon in HORIZONS
            },
        }
        for label, match in TREND_COMBOS
    ]


def first_triggers(features, condition):
    events = []
    next_allowed = None
    for index, row in enumerate(features):
        if next_allowed is not None and row["day"] < next_allowed:
            continue
        if condition(features, index):
            events.append(row)
            next_allowed = row["day"] + EVENT_COOLDOWN_DAYS * DAY
    return events


def deep_fear(features, index):
    row = features[index]
    return row["negative_share_7d"] >= 50 and row["drawdown_90d"] <= -20


def fear_repaired(features, index):
    row = features[index]
    recent = features[max(0, index - 14) : index]
    return (
        row["negative_share_7d"] <= 20
        and row["apr_7d"] > 0
        and any(previous["negative_share_7d"] >= 50 for previous in recent)
    )


def overheated(features, index):
    return features[index]["apr_7d"] >= 30


def event_table(events):
    return {
        "events": [
            {
                "day": day_label(row["day"] + DAY),
                "apr_7d": row["apr_7d"],
                "negative_share_7d": row["negative_share_7d"],
                "drawdown_90d": row["drawdown_90d"],
                **{str(h): row["outcomes"][h] for h in HORIZONS},
            }
            for row in events
        ],
        **{f"stats_{h}": stats(events, h) for h in HORIZONS},
    }


def analyze(dataset, spot):
    funding = sorted(load(f"{dataset}-funding"), key=lambda row: row["t"])
    candles = {row["t"]: row for row in load(spot)}
    features = daily_features(funding, candles)
    attach_outcomes(features, candles)
    latest = features[-1]
    return {
        "dataset": dataset,
        "first_day": day_label(features[0]["day"]),
        "last_day": day_label(latest["day"]),
        "baseline": {str(h): stats(features, h) for h in HORIZONS},
        "by_apr_7d": bucket_table(features, "apr_7d", APR_BUCKETS),
        "by_negative_share_7d": bucket_table(
            features, "negative_share_7d", NEGATIVE_SHARE_BUCKETS
        ),
        "by_percentile_7d": bucket_table(features, "percentile_7d", PERCENTILE_BUCKETS),
        "by_trend": trend_table(features),
        "deep_fear": event_table(first_triggers(features, deep_fear)),
        "fear_repaired": event_table(first_triggers(features, fear_repaired)),
        "overheated": event_table(first_triggers(features, overheated)),
        "latest": {key: value for key, value in latest.items() if key != "outcomes"}
        | {"day": day_label(latest["day"])},
    }


def btc_phases(end):
    points = {
        point["id"]: point
        for point in json.loads((ROOT / "analysis.json").read_text())["turning_points"]
    }
    # 牛市段对照启动它的上一轮熊市低点，熊市段对照自身低点；高点后段用至今最低价，底部未确认。
    return (
        ("2019-09—2021-11 牛市", None, points["2021_peak"], points["2018_bottom"]),
        (
            "2021-11—2022-11 熊市",
            points["2021_peak"],
            points["2022_bottom"],
            points["2022_bottom"],
        ),
        (
            "2022-11—2025-10 牛市",
            points["2022_bottom"],
            points["2025_peak"],
            points["2022_bottom"],
        ),
        ("2025-10 至今 高点后", points["2025_peak"], None, None),
    )


def dense_negative_zones():
    funding = sorted(load("binance-BTCUSDT-funding"), key=lambda row: row["t"])
    daily = load("binance-BTCUSDT-spot-daily")
    funding = with_prices(funding, daily)
    end = funding[-1]["t"] + 1
    zones = []
    for label, start_point, end_point, low_point in btc_phases(end):
        start = start_point["t"] + DAY if start_point else funding[0]["t"]
        stop = end_point["t"] + DAY if end_point else end
        if low_point is None:
            lowest = min(
                (row for row in daily if start <= row["t"] < stop),
                key=lambda row: row["low"],
            )
            low_point = {"date": day_label(lowest["t"]), "price": lowest["low"]}
        negatives = [
            row for row in funding if start <= row["t"] < stop and row["r"] < 0
        ]
        times = [row["t"] for row in negatives]

        def window_end(index):
            return bisect_left(times, times[index] + DENSE_WINDOW_DAYS * DAY)

        best = max(range(len(negatives)), key=lambda i: window_end(i) - i)
        window = negatives[best : window_end(best)]
        prices = [row["p"] for row in window]
        zones.append(
            {
                "phase": label,
                "from": day_label(window[0]["t"]),
                "to": day_label(window[-1]["t"]),
                "negatives": len(window),
                "price_low": min(prices),
                "price_high": max(prices),
                "bear_low_date": low_point["date"],
                "bear_low": low_point["price"],
                "distance_low_pct": (min(prices) / low_point["price"] - 1) * 100,
                "distance_high_pct": (max(prices) / low_point["price"] - 1) * 100,
            }
        )
    return zones


def fmt(value, suffix="%"):
    return "—" if value is None else f"{value:+.1f}{suffix}"


def print_bucket(title, table):
    print(f"\n{title}\n")
    print(
        "| 区间 | 天数 | 独立段 | 30日均值 | 30日上涨率 | 90日均值 | 90日中位 | 90日上涨率 | 90日P10 | 90日MAE中位 |"
    )
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in table:
        a, b = row["30"], row["90"]
        if not b["n"]:
            print(f"| {row['bucket']} | {a['n']} | — | 无样本 |||||||")
            continue
        print(
            f"| {row['bucket']} | {b['n']} | {b['episodes']} | {fmt(a['mean'])} | {a['win']:.0f}% "
            f"| {fmt(b['mean'])} | {fmt(b['median'])} | {b['win']:.0f}% | {fmt(b['p10'])} | {fmt(b['median_mae'])} |"
        )


def print_events(title, table):
    print(f"\n{title}\n")
    print("| 入场日 | 7日APR | 7日负占比 | 距90日高点 | 30日 | 90日 | 90日MAE |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in table["events"]:
        r30, r90 = row["30"], row["90"]
        print(
            f"| {row['day']} | {row['apr_7d']:.1f}% | {row['negative_share_7d']:.0f}% | {row['drawdown_90d']:.1f}% "
            f"| {fmt(r30 and r30['return'])} | {fmt(r90 and r90['return'])} | {fmt(r90 and r90['mae'])} |"
        )
    s = table["stats_90"]
    if s["n"]:
        print(
            f"\n汇总：90日满窗 {s['n']} 次，均值 {fmt(s['mean'])}，中位 {fmt(s['median'])}，"
            f"上涨率 {s['win']:.0f}%，最差 MAE {fmt(s['worst_mae'])}"
        )


def self_check():
    candles = {
        i * DAY: {"open": 100, "close": 100 + i, "low": 90, "high": 120}
        for i in range(10)
    }
    result = forward(0, candles, 3)
    assert round(result["return"], 9) == 2 and round(result["mae"], 9) == -10
    assert forward(8 * DAY, candles, 3) is None
    assert episodes([0, DAY, 40 * DAY]) == 2
    assert in_bucket(0, 0, 5) and not in_bucket(5, 0, 5) and in_bucket(-1, None, 0)
    assert round(rate_8h({"r": 0.0003, "h": 24}), 12) == 0.0001


def main():
    self_check()
    results = [analyze(dataset, spot) for dataset, spot in DATASETS]
    zones = dense_negative_zones()
    (ROOT / "signal-study.json").write_text(
        json.dumps(
            {"datasets": results, "btc_dense_negative_zones": zones},
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"\n## 币安 BTC 各阶段负费率最密集的 {DENSE_WINDOW_DAYS} 天\n")
    for zone in zones:
        print(
            f"| {zone['phase']} | {zone['from']}—{zone['to']}（{zone['negatives']} 次） "
            f"| {zone['price_low']:,.0f}—{zone['price_high']:,.0f} "
            f"| {fmt(zone['distance_low_pct'])}—{fmt(zone['distance_high_pct'])}"
            f"（{zone['bear_low_date']} 低点 {zone['bear_low']:,.0f}） |"
        )
    for result in results:
        print(f"\n## {result['dataset']}  {result['first_day']}—{result['last_day']}")
        base = result["baseline"]
        print(
            f"基线：90日均值 {fmt(base['90']['mean'])}，上涨率 {base['90']['win']:.0f}%，"
            f"30日均值 {fmt(base['30']['mean'])}，上涨率 {base['30']['win']:.0f}%"
        )
        print_bucket("### 7日平均费率（年化）", result["by_apr_7d"])
        print_bucket("### 7日负费率占比", result["by_negative_share_7d"])
        print_bucket("### 7日费率在过去365天中的分位", result["by_percentile_7d"])
        print_bucket("### 费率 × 200日均线趋势", result["by_trend"])
        print_events(
            "### 深度恐慌：7日负占比≥50% 且距90日高点≤-20%", result["deep_fear"]
        )
        print_events(
            "### 恐慌修复：14日内曾负占比≥50%，现≤20%且均值转正",
            result["fear_repaired"],
        )
        print_events("### 过热：7日年化≥30%", result["overheated"])
        print("\n最新：", json.dumps(result["latest"], ensure_ascii=False))


if __name__ == "__main__":
    main()

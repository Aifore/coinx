import json
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
START = 1672531200000
END = 1767225600000
INTERVAL = 8 * 60 * 60 * 1000


def fetch_pages(base, params, timestamp):
    rows = []
    cursor = START
    while cursor < END:
        query = urlencode(
            {**params, "startTime": cursor, "endTime": END - 1, "limit": 1000}
        )
        with urlopen(f"{base}?{query}", timeout=45) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError(f"Unexpected response: {batch}")
        if not batch:
            break
        rows.extend(batch)
        cursor = timestamp(batch[-1]) + 1
    return rows


def summarize(rows):
    rates = [Decimal(row["fundingRate"]) for row in rows]
    positive = sum(rate > 0 for rate in rates)
    days = defaultdict(list)
    for row, rate in zip(rows, rates, strict=True):
        day = datetime.fromtimestamp(row["fundingTime"] / 1000, UTC).date().isoformat()
        days[day].append(rate)

    return {
        "settlements": len(rates),
        "positive": positive,
        "negative": sum(rate < 0 for rate in rates),
        "zero": sum(rate == 0 for rate in rates),
        "positive_percent": positive / len(rates) * 100,
        "positive_equivalent_days": positive / 3,
        "all_positive_days": sum(
            all(rate > 0 for rate in daily) for daily in days.values()
        ),
        "net_positive_days": sum(sum(daily) > 0 for daily in days.values()),
        "above_001_percent": sum(rate > Decimal("0.0001") for rate in rates)
        / len(rates)
        * 100,
        "sum_rate_percent": float(sum(rates) * 100),
        "mean_rate_percent": float(sum(rates) / len(rates) * 100),
    }


def longest_positive_run(rows):
    best = []
    current = []
    for row in rows:
        if Decimal(row["fundingRate"]) > 0:
            current.append(row)
            if len(current) > len(best):
                best = current.copy()
        else:
            current = []
    return {
        "settlements": len(best),
        "equivalent_days": len(best) / 3,
        "first_settlement_utc": datetime.fromtimestamp(
            best[0]["fundingTime"] / 1000, UTC
        ).isoformat(),
        "last_settlement_utc": datetime.fromtimestamp(
            best[-1]["fundingTime"] / 1000, UTC
        ).isoformat(),
    }


def analyze_symbol(symbol):
    funding_path = ROOT / f"{symbol}-funding-2023-2025.json"
    prices_path = ROOT / f"{symbol}-spot-daily-2023-2025.json"
    if not funding_path.exists():
        funding = fetch_pages(
            "https://fapi.binance.com/fapi/v1/fundingRate",
            {"symbol": symbol},
            lambda row: row["fundingTime"],
        )
        funding_path.write_text(json.dumps(funding, ensure_ascii=False, indent=2))
    funding = json.loads(funding_path.read_text())

    if not prices_path.exists():
        prices = fetch_pages(
            "https://data-api.binance.vision/api/v3/klines",
            {"symbol": symbol, "interval": "1d"},
            lambda row: row[0],
        )
        prices_path.write_text(json.dumps(prices, indent=2))
    prices = json.loads(prices_path.read_text())

    slots = [row["fundingTime"] // INTERVAL for row in funding]
    assert slots == list(range(START // INTERVAL, END // INTERVAL)), (
        f"Missing or duplicate funding slots: {symbol}"
    )
    assert [row[0] for row in prices] == list(range(START, END, 86400000)), (
        f"Missing price days: {symbol}"
    )
    groups = defaultdict(list)
    price_groups = defaultdict(list)
    for row in funding:
        date = datetime.fromtimestamp(row["fundingTime"] / 1000, UTC)
        for key in (
            f"{date.year}",
            f"{date.year}-Q{(date.month - 1) // 3 + 1}",
            f"{date.year}-{date.month:02d}",
        ):
            groups[key].append(row)
    for row in prices:
        date = datetime.fromtimestamp(row[0] / 1000, UTC)
        for key in (
            f"{date.year}",
            f"{date.year}-Q{(date.month - 1) // 3 + 1}",
            f"{date.year}-{date.month:02d}",
        ):
            price_groups[key].append(row)

    periods = {}
    for key, group in sorted(groups.items()):
        candles = price_groups[key]
        periods[key] = {
            **summarize(group),
            "spot_return_percent": (float(candles[-1][4]) / float(candles[0][1]) - 1)
            * 100,
        }
    return {
        "symbol": symbol,
        "total": summarize(funding),
        "longest_positive_run": longest_positive_run(funding),
        "daily_settlement_counts": dict(
            Counter(Counter(row["fundingTime"] // 86400000 for row in funding).values())
        ),
        "spot_start": prices[0][1],
        "spot_end": prices[-1][4],
        "periods": periods,
    }


def self_check():
    rates = ("0.0001", "-0.0002", "0", "0.0003", "0.0001", "0.0001")
    rows = [
        {"fundingTime": START + index * INTERVAL, "fundingRate": rate}
        for index, rate in enumerate(rates)
    ]
    result = summarize(rows)
    assert result["positive"] == 4 and result["negative"] == 1 and result["zero"] == 1
    assert result["all_positive_days"] == 1 and result["net_positive_days"] == 1
    assert longest_positive_run(rows)["settlements"] == 3


if __name__ == "__main__":
    self_check()
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(analyze_symbol, ("BTCUSDT", "ETHUSDT")))
    output = {
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "start_utc": "2023-01-01",
        "end_exclusive_utc": "2026-01-01",
        "results": results,
    }
    (ROOT / "summary.json").write_text(json.dumps(output, ensure_ascii=False, indent=2))
    for result in results:
        print(
            json.dumps(
                {key: value for key, value in result.items() if key != "periods"},
                ensure_ascii=False,
            )
        )
        for key, value in result["periods"].items():
            if len(key) == 4 or "Q" in key:
                print(key, json.dumps(value, ensure_ascii=False))

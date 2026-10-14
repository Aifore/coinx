import json
import math
import os
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
DAY = 86_400_000
HOUR = 3_600_000
START = int(datetime(2012, 1, 1, tzinfo=UTC).timestamp() * 1000)
# 默认固定为首份报告的截止日以便复现；刷新时用 FUNDING_END=YYYY-MM-DD 覆盖。
END = int(
    datetime.fromisoformat(os.environ.get("FUNDING_END", "2026-10-02"))
    .replace(tzinfo=UTC)
    .timestamp()
    * 1000
)


def iso(timestamp):
    return datetime.fromtimestamp(timestamp / 1000, UTC).isoformat()


def millis(value):
    return round(
        datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000
    )


def request_json(url, params=None):
    target = f"{url}?{urlencode(params)}" if params else url
    for attempt in range(5):
        try:
            request = Request(
                target, headers={"User-Agent": "funding-history-research/1.0"}
            )
            with urlopen(request, timeout=60) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            if isinstance(error, HTTPError) and error.code not in (
                429,
                500,
                502,
                503,
                504,
            ):
                raise
            if attempt == 4:
                raise
            time.sleep(min(2 ** (attempt + 1), 20))
    raise RuntimeError(f"Could not fetch {target}")


def binance_rows(symbol, funding):
    url = (
        "https://fapi.binance.com/fapi/v1/fundingRate"
        if funding
        else "https://data-api.binance.vision/api/v3/klines"
    )
    cursor = START
    rows = []
    params = {"symbol": symbol}
    if not funding:
        params["interval"] = "1d"

    while cursor < END:
        batch = request_json(
            url, {**params, "startTime": cursor, "endTime": END - 1, "limit": 1000}
        )
        if not isinstance(batch, list):
            raise ValueError(f"Unexpected Binance response: {batch}")
        if not batch:
            break
        rows.extend(batch)
        next_cursor = (batch[-1]["fundingTime"] if funding else batch[-1][0]) + 1
        if next_cursor <= cursor:
            raise ValueError(f"Non-advancing Binance page for {symbol}")
        cursor = next_cursor

    return rows, url


def interval_diagnostics(rows, step):
    slots = [row["t"] // step for row in rows]
    observed = set(slots)
    missing = [
        slot * step for slot in range(slots[0], slots[-1] + 1) if slot not in observed
    ]
    return {
        "expected_interval_hours": step / HOUR,
        "duplicate_slots": len(slots) - len(observed),
        "missing_slots": len(missing),
        "missing_slot_times_utc": [iso(value) for value in missing],
    }


def save_dataset(name, kind, records, original, url, extra=None):
    by_time = {row["t"]: row for row in records if START <= row["t"] < END}
    rows = sorted(by_time.values(), key=lambda row: row["t"])
    if not rows:
        raise ValueError(f"Empty dataset: {name}")
    validate_rows(rows, kind)
    filename = f"{name}.json"
    (RAW / filename).write_text(json.dumps(rows, separators=(",", ":")))
    (RAW / f"{name}-source.json").write_text(
        json.dumps(original, separators=(",", ":"))
    )

    intervals = Counter(
        round((b["t"] - a["t"]) / HOUR, 3) for a, b in zip(rows, rows[1:])
    )
    result = {
        "file": f"raw/{filename}",
        "kind": kind,
        "first_utc": iso(rows[0]["t"]),
        "last_utc": iso(rows[-1]["t"]),
        "count": len(rows),
        "duplicate_timestamps_removed": len(records) - len(by_time),
        "observed_interval_hours_counts": dict(sorted(intervals.items())),
        "source_url": url,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        **(extra or {}),
    }
    print(
        f"Saved {name}: {len(rows)} rows, {result['first_utc']} — {result['last_utc']}",
        flush=True,
    )
    return name, result


def collect_binance(symbol, funding):
    original, url = binance_rows(symbol, funding)
    if funding:
        records = [
            {
                "t": row["fundingTime"],
                "r": float(row["fundingRate"]),
                "p": float(row["markPrice"]) if row.get("markPrice") else None,
                "h": 8,
            }
            for row in original
        ]
        diagnostics = interval_diagnostics(records, 8 * HOUR)
        diagnostics["interval_basis"] = (
            "8-hour grid verified against all observed timestamps; millisecond jitter retained"
        )
        diagnostics["null_settlement_mark_prices"] = sum(
            row["p"] is None for row in records
        )
        kind = "funding"
    else:
        records = [
            {
                "t": row[0],
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
            }
            for row in original
        ]
        diagnostics = interval_diagnostics(records, DAY)
        kind = "spot-daily"
    return save_dataset(
        f"binance-{symbol}-{kind}", kind, records, original, url, diagnostics
    )


def collect_bitmex(symbol="XBTUSD"):
    url = "https://www.bitmex.com/api/v1/funding"
    original = []
    cursor = START
    while cursor < END:
        batch = request_json(
            url,
            {
                "symbol": symbol,
                "count": 500,
                "reverse": "false",
                "startTime": iso(cursor),
                "endTime": iso(END - 1),
            },
        )
        if not isinstance(batch, list):
            raise ValueError(f"Unexpected BitMEX response: {batch}")
        if not batch:
            break
        original.extend(batch)
        next_cursor = millis(batch[-1]["timestamp"]) + 1
        if next_cursor <= cursor:
            raise ValueError("Non-advancing BitMEX funding page")
        cursor = next_cursor
        time.sleep(0.3)

    interval_base = millis("2000-01-01T00:00:00Z")
    records = [
        {
            "t": millis(row["timestamp"]),
            "r": float(row["fundingRate"]),
            "p": None,
            "h": (millis(row["fundingInterval"]) - interval_base) / HOUR,
        }
        for row in original
    ]
    gaps = [
        {
            "after_utc": iso(previous["t"]),
            "before_utc": iso(current["t"]),
            "elapsed_hours": (current["t"] - previous["t"]) / HOUR,
            "current_funding_interval_hours": current["h"],
        }
        for previous, current in zip(records, records[1:])
        if abs(current["t"] - previous["t"] - current["h"] * HOUR) > 1000
    ]
    return save_dataset(
        f"bitmex-{symbol}-funding",
        "funding",
        records,
        original,
        url,
        {
            "reported_interval_hours_counts": dict(
                Counter(row["h"] for row in records)
            ),
            "interval_basis": "Each settlement's source fundingInterval, measured from 2000-01-01T00:00:00Z",
            "interval_transition_or_gap_count": len(gaps),
            "interval_transitions_or_gaps": gaps,
            "null_settlement_mark_prices": len(records),
            "unavailable_tail_slots_to_requested_end": int(
                (END - 1 - records[-1]["t"]) // (records[-1]["h"] * HOUR)
            ),
            "tail_note": "No records beyond last_utc were returned; do not interpret the unavailable tail as zero funding",
        },
    )


def collect_coinmetrics():
    url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
    payload = request_json(
        url,
        {
            "assets": "btc",
            "metrics": "PriceUSD",
            "frequency": "1d",
            "start_time": iso(START)[:10],
            "end_time": iso(END)[:10],
            "page_size": 10000,
        },
    )
    original = payload["data"]
    while payload.get("next_page_url"):
        payload = request_json(payload["next_page_url"])
        original.extend(payload["data"])
    records = [
        {"t": millis(row["time"]), "close": float(row["PriceUSD"])}
        for row in original
        if row.get("PriceUSD") is not None and millis(row["time"]) < END
    ]
    return save_dataset(
        "coinmetrics-BTCUSD-reference-daily",
        "reference-daily",
        records,
        original,
        url,
        {
            **interval_diagnostics(records, DAY),
            "metric": "PriceUSD",
            "price_basis": "CoinMetrics daily USD reference price; close is a schema alias, not an exchange candle close",
            "available_after_ms_from_t": DAY,
            "timestamp_definition": "t labels the UTC day; PriceUSD is the price as of that day's end",
            "methodology_url": "https://github.com/coinmetrics/docs-website/blob/master/asset-metrics/market/priceusd.md",
            "missing_price_values": sum(
                row.get("PriceUSD") is None for row in original
            ),
        },
    )


def validate_rows(rows, kind):
    assert all(a["t"] < b["t"] for a, b in zip(rows, rows[1:]))
    for row in rows:
        if kind == "funding":
            assert math.isfinite(row["r"]) and row["h"] > 0
            assert row["p"] is None or row["p"] > 0
        elif kind == "reference-daily":
            assert math.isfinite(row["close"]) and row["close"] > 0
        else:
            assert row["low"] <= min(row["open"], row["close"]) <= row["high"]
            assert row["low"] <= max(row["open"], row["close"]) <= row["high"]


def self_check():
    assert millis("2026-10-02T00:00:00Z") == END
    records = [{"t": 8 * HOUR}, {"t": 16 * HOUR + 5}, {"t": 32 * HOUR}]
    assert interval_diagnostics(records, 8 * HOUR)["missing_slots"] == 1
    assert interval_diagnostics(records, 8 * HOUR)["duplicate_slots"] == 0
    assert (
        millis("2000-01-02T00:00:00Z") - millis("2000-01-01T00:00:00Z")
    ) / HOUR == 24


def main():
    self_check()
    RAW.mkdir(parents=True, exist_ok=True)
    output = {
        "requested_start_utc": iso(START),
        "end_exclusive_utc": iso(END),
        "datasets": {},
        "errors": {},
    }
    jobs = [
        (
            f"binance-{symbol}-{'funding' if funding else 'spot-daily'}",
            collect_binance,
            (symbol, funding),
        )
        for symbol in ("BTCUSDT", "ETHUSDT")
        for funding in (True, False)
    ]
    jobs.extend(
        (f"bitmex-{symbol}-funding", collect_bitmex, (symbol,))
        for symbol in ("XBTUSD", "ETHUSD")
    )
    jobs.append(("coinmetrics-BTCUSD-reference-daily", collect_coinmetrics, ()))
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(function, *arguments): name
            for name, function, arguments in jobs
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                key, result = future.result()
                output["datasets"][key] = result
            except Exception as error:
                output["errors"][name] = f"{type(error).__name__}: {error}"
                print(f"Failed {name}: {error}", flush=True)
            (ROOT / "manifest.json").write_text(
                json.dumps(output, ensure_ascii=False, indent=2)
            )


if __name__ == "__main__":
    main()

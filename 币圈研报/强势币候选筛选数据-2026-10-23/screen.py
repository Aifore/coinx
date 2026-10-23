import concurrent.futures
import csv
import datetime as dt
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
API = "https://data-api.binance.vision/api/v3"
DAY = 86_400_000
EXCLUDED = {
    "USDC",
    "FDUSD",
    "TUSD",
    "USDP",
    "DAI",
    "EUR",
    "TRY",
    "BRL",
    "USD1",
    "XUSD",
    "RLUSD",
    "USDE",
    "BFUSD",
    "EURI",
    "AEUR",
    "PAXG",
    "WBTC",
    "WBETH",
    "BNSOL",
    "PYUSD",
    "U",
    "USDS",
    "XAUT",
    "RWUSD",
}
FOLLOW = {"BTC", "PENGU", "TIA", "JUP", "JST", "PLUME", "ONDO", "INJ", "TAO", "VIRTUAL"}
SECURITIES = set(
    "MUB CRCLB NVDAB SNDKB TSLAB SPCXB AMDB EWYB INTCB MSTRB LITEB METAB MSFTB PLTRB QQQB CBRSB COINB DRAMB GLWB GOOGLB NBISB QCOMB SOXLB SPYB WDCB SKHYB AAOIB ARMB AVGOB BABAB HOODB IBMB MRVLB NOKB TSMB RKLBB AXTIB CRWVB INTWB KORUB MUUB MVLLB ORCLB QNTB SNXXB TQQQB AAPLB AMATB AMZNB BEB DELLB FLNCB GSB PYPLB SMHB SOXSB ASMLB ASTSB BMNRB COHRB CRDOB IRENB NFLXB SMCIB USARB ALABB GMEB DJTB CRWDB MRNAB SQQQB STXB CRMB HIMSB BNCB GPROB RDDTB AGPUB AMCB CYPHB ADBEB FWDIB HPEB PDDB SHAZB WENB ZMB USDEB SECZB LLYB JPMB BBB MDBB PENGB UVXYB BOTB KSTRB TMFB VSTB BRKBB".split()
)


def get(endpoint, **params):
    url = f"{API}/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=40) as response:
        return json.load(response)


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2))


def date(timestamp):
    return dt.datetime.fromtimestamp(timestamp / 1000, dt.UTC).date().isoformat()


def change(current, previous):
    return (current / previous - 1) * 100


def analyze(symbol, raw, btc, tickers, eligible):
    rows = {date(r[0]): [float(x) for x in r[1:6]] for r in raw}
    days = sorted(rows)
    if len(days) < 61:
        return {"symbol": symbol, "history_days": len(days), "eligible": eligible}
    last = days[-1]
    close = rows[last][3]
    ratio = {d: rows[d][3] / btc[d][3] for d in days}
    result = {
        "symbol": symbol,
        "eligible": eligible,
        "history_days": len(days),
        "close": close,
        "live_price": float(tickers[symbol]["lastPrice"]),
        "quote_volume_24h_m": float(tickers[symbol]["quoteVolume"]) / 1e6,
        "volume_ratio": rows[last][4] / (sum(rows[d][4] for d in days[-21:-1]) / 20),
        "ma20": sum(rows[d][3] for d in days[-20:]) / 20,
        "ma60": sum(rows[d][3] for d in days[-60:]) / 60,
        "prior_high_close60": max(rows[d][3] for d in days[-61:-1]),
        "high20": max(rows[d][1] for d in days[-20:]),
        "low7": min(rows[d][2] for d in days[-7:]),
        "low14": min(rows[d][2] for d in days[-14:]),
        "low30": min(rows[d][2] for d in days[-30:]),
        "low60": min(rows[d][2] for d in days[-60:]),
        "ratio_vs_high60_pct": change(ratio[last], max(ratio[d] for d in days[-61:-1])),
    }
    for period in [7, 14, 30, 60, 90, 180]:
        if len(days) <= period:
            continue
        result[f"return{period}_pct"] = change(close, rows[days[-period - 1]][3])
        result[f"rs{period}_pct"] = change(ratio[last], ratio[days[-period - 1]])
    for period in [120, 200]:
        if len(days) >= period:
            result[f"ma{period}"] = sum(rows[d][3] for d in days[-period:]) / period
    result["distance_low7_pct"] = (1 - result["low7"] / close) * 100
    result["distance_high20_pct"] = change(close, result["high20"])
    if "2026-01-01" in rows:
        lows = []
        for start, end in [
            ("2026-01-01", "2026-02-28"),
            ("2026-06-05", "2026-07-05"),
            ("2026-08-01", "2026-08-31"),
            ("2026-09-21", last),
        ]:
            lows.append(min(rows[d][2] for d in days if start <= d <= end))
        result["historical_lows"] = lows
        result["hold_feb_pct"] = change(lows[1], lows[0])
        result["rising_lows"] = all(b > a for a, b in zip(lows, lows[1:]))
        result["year_low_date"] = min(
            (d for d in days if d >= "2026-01-01"), key=lambda d: rows[d][2]
        )
        result["original_structure"] = (
            result["rising_lows"]
            and result["year_low_date"] < "2026-03-01"
            and result["rs60_pct"] > 0
        )
        result["return_since0630_pct"] = change(close, rows["2026-06-30"][3])
    return result


def main():
    assert math.isclose(change(110, 100), 10)
    assert date(1792627200000) == "2026-10-22"
    (ROOT / "data").mkdir(exist_ok=True)
    server = get("time")["serverTime"]
    end = server // DAY * DAY - 1
    start = int(dt.datetime(2025, 12, 1, tzinfo=dt.UTC).timestamp() * 1000)
    info = get("exchangeInfo", permissions="SPOT", showPermissionSets="false")
    tickers_raw = get("ticker/24hr")
    tickers = {t["symbol"]: t for t in tickers_raw}
    pairs = {
        s["symbol"]: s["baseAsset"]
        for s in info["symbols"]
        if s["status"] == "TRADING"
        and s["quoteAsset"] == "USDT"
        and s["baseAsset"] not in EXCLUDED
        and s["baseAsset"] not in SECURITIES
    }
    eligible = {s for s in pairs if float(tickers[s]["quoteVolume"]) >= 5_000_000}
    symbols = sorted(eligible | {s for s, base in pairs.items() if base in FOLLOW})
    save("exchange-info.json", info)
    save("ticker24h.json", tickers_raw)
    save(
        "snapshot.json",
        {
            "serverTimeUtc": dt.datetime.fromtimestamp(
                server / 1000, dt.UTC
            ).isoformat(),
            "dailyThrough": date(end),
            "api": API,
            "minQuoteVolume": 5_000_000,
            "eligibleSymbols": sorted(eligible),
            "collectedSymbols": symbols,
            "excludedBases": sorted(EXCLUDED),
            "excludedSecurities": sorted(SECURITIES),
        },
    )

    def fetch(symbol):
        rows = get(
            "klines",
            symbol=symbol,
            interval="1d",
            startTime=start,
            endTime=end,
            limit=1000,
        )
        assert rows and rows[-1][6] == end, f"{symbol}: stale last candle"
        assert all(b[0] - a[0] == DAY for a, b in zip(rows, rows[1:])), (
            f"{symbol}: missing candle"
        )
        assert all(
            float(r[3])
            <= min(float(r[1]), float(r[4]))
            <= max(float(r[1]), float(r[4]))
            <= float(r[2])
            for r in rows
        )
        save(f"data/{symbol}-1d.json", rows)
        return symbol, rows

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        data = dict(executor.map(fetch, symbols))
    btc = {date(r[0]): [float(x) for x in r[1:6]] for r in data["BTCUSDT"]}
    results = [analyze(s, data[s], btc, tickers, s in eligible) for s in symbols]
    save("screen.json", results)
    fields = list(dict.fromkeys(k for r in results for k in r))
    with (ROOT / "screen.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(
        f"Validated {len(results)} series through {date(end)}; eligible {len(eligible)}"
    )


if __name__ == "__main__":
    main()

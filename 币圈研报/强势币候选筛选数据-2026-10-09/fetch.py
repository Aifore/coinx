import json, urllib.request, concurrent.futures as cf, pathlib, sys
API = "https://api.binance.com/api/v3"
START, END = 1764547200000, 1791503999999  # 2025-12-01 ~ 2026-10-08 UTC 收盘
MIN_QUOTE_VOL = 5_000_000
STABLE = {"USDC","FDUSD","TUSD","USDP","DAI","EUR","TRY","BRL","USD1","XUSD","RLUSD","USDE","BFUSD","EURI","AEUR","PAXG","WBTC","WBETH","BNSOL","PYUSD","U","USDS"}
data = pathlib.Path("data")

def get(path):
    with urllib.request.urlopen(f"{API}/{path}", timeout=30) as r:
        return json.load(r)

info = get("exchangeInfo?permissions=SPOT")
spot = {s["symbol"]: s["baseAsset"] for s in info["symbols"]
        if s["symbol"].isascii() and s["status"] == "TRADING" and s["quoteAsset"] == "USDT" and s["baseAsset"] not in STABLE}
tickers = {t["symbol"]: float(t["quoteVolume"]) for t in get("ticker/24hr")}
symbols = sorted(s for s in spot if tickers.get(s, 0) >= MIN_QUOTE_VOL)
if "BTCUSDT" not in symbols: symbols.append("BTCUSDT")

def fetch(sym):
    rows = get(f"klines?symbol={sym}&interval=1d&startTime={START}&endTime={END}&limit=1000")
    (data / f"{sym}-1d.json").write_text(json.dumps(rows))
    return sym, len(rows)

with cf.ThreadPoolExecutor(8) as ex:
    res = list(ex.map(fetch, symbols))
json.dump({"symbols": symbols, "quoteVolume24h": {s: tickers[s] for s in symbols}, "minQuoteVolume": MIN_QUOTE_VOL,
           "start": "2025-12-01", "endInclusive": "2026-10-08"}, open("universe.json", "w"), indent=1)
print(len(symbols), "symbols;", sum(1 for _, n in res if n >= 312), "with full history")

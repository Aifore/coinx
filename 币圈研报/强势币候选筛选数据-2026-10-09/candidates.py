import json, urllib.request, datetime as dt
from analyze import load, window

API = "https://api.binance.com/api/v3"
LAST = "2026-10-08"
CANDIDATES = ["TIA", "JUP", "JST", "PLUME"]

def get(path):
    with urllib.request.urlopen(f"{API}/{path}", timeout=30) as r:
        return json.load(r)

def today_open(sym):
    return float(get(f"klines?symbol={sym}&interval=1d&limit=1")[0][1])

def depth_usdt(sym, mid, pct):
    book = get(f"depth?symbol={sym}&limit=1000")
    bid = sum(float(p) * float(q) for p, q in book["bids"] if float(p) >= mid * (1 - pct))
    ask = sum(float(p) * float(q) for p, q in book["asks"] if float(p) <= mid * (1 + pct))
    return round(bid), round(ask)

B = load("BTCUSDT")
btc_pairs = {s["symbol"] for s in get("exchangeInfo?permissions=SPOT")["symbols"] if s["status"] == "TRADING" and s["quoteAsset"] == "BTC"}
sampled_at = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
out = {"sampledAt": sampled_at, "btcOpen1009": today_open("BTCUSDT"), "coins": {}}
for base in CANDIDATES:
    sym = base + "USDT"
    X = load(sym); days = sorted(X); i = days.index(LAST)
    ratio = {d: X[d]["c"] / B[d]["c"] for d in days if d in B}
    last60, last20 = days[i - 59:i + 1], days[i - 19:i + 1]
    upper_day = max(last60, key=lambda d: X[d]["c"])
    lower_day = min(last20, key=lambda d: X[d]["l"])
    ratio_day = max(last60, key=lambda d: ratio[d])
    vol20 = sum(X[d]["v"] for d in days[i - 20:i]) / 20
    raw = {r[0]: r for r in json.load(open(f"data/{sym}-1d.json"))}
    qvol = [float(r[7]) for r in json.load(open(f"data/{sym}-1d.json"))][i - 19:i + 1]
    bt = get(f"ticker/bookTicker?symbol={sym}")
    bid, ask = float(bt["bidPrice"]), float(bt["askPrice"]); mid = (bid + ask) / 2
    out["coins"][base] = dict(
        directBtcPair=base + "BTC" in btc_pairs,
        close1008=X[LAST]["c"], high1008=X[LAST]["h"], low1008=X[LAST]["l"],
        upper=X[upper_day]["c"], upperDay=upper_day,
        lower=X[lower_day]["l"], lowerDay=lower_day,
        ratio1008=ratio[LAST], ratioMax60=ratio[ratio_day], ratioMaxDay=ratio_day,
        vol1008=X[LAST]["v"], vol20avgExcl1008=vol20, volRatio1008=X[LAST]["v"] / vol20,
        quoteVol20avg=sum(qvol) / 20,
        distToUpperPct=(X[upper_day]["c"] / X[LAST]["c"] - 1) * 100,
        distToLowerPct=(X[lower_day]["l"] / X[LAST]["c"] - 1) * 100,
        open1009=today_open(sym),
        spreadBps=(ask - bid) / mid * 1e4,
        depth1pct=depth_usdt(sym, mid, 0.01), depth2pct=depth_usdt(sym, mid, 0.02),
    )
json.dump(out, open("candidates.json", "w"), indent=1)
print(json.dumps(out, indent=1))

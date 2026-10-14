import json, datetime as dt, csv

def load(sym):
    rows = json.load(open(f"data/{sym}-1d.json"))
    return {dt.datetime.fromtimestamp(r[0] / 1000, dt.UTC).date().isoformat():
            dict(o=float(r[1]), h=float(r[2]), l=float(r[3]), c=float(r[4]), v=float(r[5])) for r in rows}

def window(X, a, b):
    return [d for d in sorted(X) if a <= d <= b]

LAST = "2026-10-08"
B = load("BTCUSDT")
BTC_PEAK_DAY = max(window(B, "2026-09-20", LAST), key=lambda d: B[d]["h"])
universe = json.load(open("universe.json"))
out = []
for sym in universe["symbols"]:
    if sym == "BTCUSDT":
        continue
    X = load(sym)
    days = sorted(X)
    if days[0] > "2025-12-31" or LAST not in X:
        continue
    jan_feb = window(X, "2026-01-01", "2026-02-28")
    feb_low = min(X[d]["l"] for d in jan_feb)
    break_low = min(X[d]["l"] for d in window(X, "2026-06-05", "2026-07-05"))
    ytd = window(X, "2026-01-01", LAST)
    ytd_low_day = min(ytd, key=lambda d: X[d]["l"])

    ratio = {d: X[d]["c"] / B[d]["c"] for d in ytd}
    i = days.index(LAST)
    prev60 = days[i - 60:i]
    r_prev60_max = max(ratio[d] for d in prev60 if d in ratio)
    r_60ago = ratio[days[i - 60]]

    peak_day = max(window(X, "2026-09-20", LAST), key=lambda d: X[d]["h"])
    after_peak_low = min(X[d]["l"] for d in window(X, peak_day, LAST))
    btc_after_peak_low = min(B[d]["l"] for d in window(B, BTC_PEAK_DAY, LAST))

    last_breakout = None
    for j in range(i - 19, i + 1):
        d = days[j]
        if X[d]["c"] > max(X[x]["c"] for x in days[j - 60:j]):
            vol_ratio = X[d]["v"] / (sum(X[x]["v"] for x in days[j - 20:j]) / 20)
            last_breakout = (d, round(vol_ratio, 2))

    out.append(dict(
        sym=sym[:-4],
        qvol_m=round(universe["quoteVolume24h"][sym] / 1e6, 1),
        hold_vs_feb_pct=round((break_low / feb_low - 1) * 100, 1),
        ytd_low_day=ytd_low_day,
        ret_since_0630_pct=round((X[LAST]["c"] / X["2026-06-30"]["c"] - 1) * 100, 1),
        ret_30d_pct=round((X[LAST]["c"] / X[days[i - 30]]["c"] - 1) * 100, 1),
        ratio_chg_60d_pct=round((ratio[LAST] / r_60ago - 1) * 100, 1),
        ratio_vs_60d_max_pct=round((ratio[LAST] / r_prev60_max - 1) * 100, 1),
        close_vs_60d_max_close_pct=round((X[LAST]["c"] / max(X[d]["c"] for d in prev60) - 1) * 100, 1),
        pullback_from_late_sep_peak_pct=round((after_peak_low / X[peak_day]["h"] - 1) * 100, 1),
        btc_pullback_pct=round((btc_after_peak_low / B[BTC_PEAK_DAY]["h"] - 1) * 100, 1),
        last_breakout=last_breakout,
    ))

with open("screen.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
json.dump(out, open("screen.json", "w"), indent=1)
print(len(out), "coins analysed; BTC late-Sep peak", BTC_PEAK_DAY)

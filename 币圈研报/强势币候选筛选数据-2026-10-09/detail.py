import json, datetime as dt, sys
from analyze import load, window
LAST = "2026-10-08"
B = load("BTCUSDT")
WINDOWS = [("Feb", "2026-01-01", "2026-02-28"), ("BTC破底6/5-7/5", "2026-06-05", "2026-07-05"),
           ("8月", "2026-08-01", "2026-08-31"), ("9/21后回调", "2026-09-21", LAST)]
for base in sys.argv[1:]:
    X = load(base + "USDT"); days = sorted(X); i = days.index(LAST)
    ratio = {d: X[d]["c"] / B[d]["c"] for d in days if d in B}
    lows = " | ".join(f"{n} {min(window(X,a,b), key=lambda d: X[d]['l'])[5:]} {min(X[d]['l'] for d in window(X,a,b)):.4g}" for n, a, b in WINDOWS)
    prev60 = days[i-60:i]
    hc = max(prev60, key=lambda d: X[d]["c"]); hr = max(prev60, key=lambda d: ratio[d])
    rmin90 = min(days[i-90:i], key=lambda d: ratio[d])
    vavg = sum(X[d]["v"] for d in days[i-20:i]) / 20
    print(f"== {base}")
    print("  低点:", lows)
    print(f"  60日最高收盘 {X[hc]['c']:.4g}@{hc[5:]}  现收 {X[LAST]['c']:.4g}  距离 {X[LAST]['c']/X[hc]['c']-1:+.1%}")
    print(f"  币/BTC: 现 {ratio[LAST]:.4g}  60日最高 {ratio[hr]:.4g}@{hr[5:]} ({ratio[LAST]/ratio[hr]-1:+.1%})  90日最低 {ratio[rmin90]:.4g}@{rmin90[5:]} ({ratio[LAST]/ratio[rmin90]-1:+.1%})")
    tail = days[i-7:i+1]
    print("  近8日 c/h/l/量比:", "  ".join(f"{d[5:]} {X[d]['c']:.4g}/{X[d]['h']:.4g}/{X[d]['l']:.4g}/{X[d]['v']/vavg:.2f}" for d in tail))
    print(f"  10/8 收盘>10/7 最高? {X[LAST]['c'] > X[days[i-1]]['h']}")

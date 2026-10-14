import json
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from matplotlib import font_manager
from matplotlib.collections import LineCollection
from plotly.subplots import make_subplots

from analyze_history import with_prices

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "charts"
RED = "#ba2439"
BLUE = "#205ea6"
DAY = 86400000


def concentration(rows):
    history = deque()
    counts = {1: 0, -1: 0, 0: 0}
    result = []
    for row in rows:
        timestamp = row["t"] // 60000 * 60000
        sign = 1 if row["r"] > 0 else -1 if row["r"] < 0 else 0
        while history and history[0][0] <= timestamp - 7 * DAY:
            _, expired = history.popleft()
            counts[expired] -= 1
        history.append((timestamp, sign))
        counts[sign] += 1
        result.append(counts[sign] / len(history))
    return result


def load_price(dataset):
    daily = json.loads((ROOT / "raw" / dataset["price_source"]).read_text())
    if dataset["id"] == "bitmex-XBTUSD":
        reference = json.loads(
            (ROOT / "raw/coinmetrics-BTCUSD-reference-daily.json").read_text()
        )
        daily = [row for row in reference if row["t"] < daily[0]["t"]] + daily
    return daily


def stamp(t):
    return datetime.fromtimestamp(t / 1000, UTC)


def plot_static(dataset, rows, prices, phases):
    fig, axes = plt.subplots(
        3,
        1,
        figsize=(16, 9),
        sharex=True,
        gridspec_kw={"height_ratios": [1.1, 1.8, 0.65]},
    )
    colors = concentration(rows)
    times = np.array([mdates.date2num(stamp(row["t"])) for row in rows])
    rates = np.array([row["r"] * 800 / row["h"] for row in rows])
    if prices:
        axes[0].plot(
            [stamp(row["t"] + DAY) for row in prices],
            [row["close"] for row in prices],
            color="#454d5d",
            linewidth=1.1,
        )
        axes[0].set_yscale("log")
    axes[0].set_ylabel("现货价格（USD / USDT，对数）")
    axes[1].axhline(0, color="#888888", linewidth=0.6)
    for positive, color in [(True, RED), (False, BLUE)]:
        indices = [
            i for i, value in enumerate(rates) if (value > 0) == positive and value != 0
        ]
        segments = [[(times[i], 0), (times[i], rates[i])] for i in indices]
        rgba = [
            matplotlib.colors.to_rgba(color, 0.12 + 0.88 * colors[i] ** 2)
            for i in indices
        ]
        axes[1].add_collection(LineCollection(segments, colors=rgba, linewidths=0.75))
        axes[1].scatter(times[indices], rates[indices], c=rgba, s=2)
    bound = max(abs(rates.min()), abs(rates.max())) * 1.08
    axes[1].set_ylim(-bound, bound)
    axes[1].set_ylabel("资金费率（% / 8 小时等值）")
    negatives = []
    history = deque()
    for row in rows:
        timestamp = row["t"] // 60000 * 60000
        while history and history[0]["t"] // 60000 * 60000 <= timestamp - 7 * DAY:
            history.popleft()
        history.append(row)
        negatives.append(sum(item["r"] < 0 for item in history) / len(history) * 100)
    axes[2].plot(times, negatives, color=BLUE, linewidth=0.9)
    axes[2].axhline(70, color="#777777", linewidth=0.6, linestyle="--")
    axes[2].set_ylim(0, 100)
    axes[2].set_ylabel("过去 7 天\n负费率占比（%）")
    axes[2].set_xlabel("结算时间（UTC）")
    for ax in axes:
        ax.grid(axis="y", color="#dddddd", linewidth=0.5)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlim(times[0], times[-1])
        for phase in phases:
            if rows[0]["t"] < phase["start"] < rows[-1]["t"]:
                ax.axvline(stamp(phase["start"]), color="#b2b2b2", linewidth=0.6)
    axes[2].xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=12))
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.suptitle(f"{dataset['id']} · 全历史资金费与价格", fontsize=16)
    fig.text(
        0.5,
        0.935,
        "红色：正费率；蓝色：负费率。过去 7 天同方向结算越集中，颜色越深。竖线为事后牛熊分段边界。",
        ha="center",
        fontsize=10,
    )
    fig.text(
        0.02,
        0.012,
        "每根线为一次真实结算；纵轴统一为 8h 等值，未截去极端值。价格点绘于日收盘已知时刻。",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.925))
    path = OUT / f"{dataset['id']}-overview.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_interactive(dataset, rows, prices, phases):
    shares = concentration(rows)
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.32, 0.68],
        vertical_spacing=0.08,
    )
    fig.add_trace(
        go.Scatter(
            x=[stamp(row["t"] + DAY) for row in prices],
            y=[row["close"] for row in prices],
            name="现货收盘价",
            mode="lines",
            line={"color": "#555d6d", "width": 1.2},
            hovertemplate="%{x|%Y-%m-%d %H:%M} UTC<br>截至此刻已完成的日收盘：%{y:,.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    for sign, rgb, name in [
        (1, "186,36,57", "正资金费"),
        (-1, "32,94,166", "负资金费"),
    ]:
        selected = [
            (row, share)
            for row, share in zip(rows, shares, strict=True)
            if row["r"] * sign > 0
        ]
        fig.add_trace(
            go.Bar(
                x=[stamp(row["t"]) for row, _ in selected],
                y=[row["r"] * 800 / row["h"] for row, _ in selected],
                width=[row["h"] * 3600000 * 0.7 for row, _ in selected],
                marker={
                    "color": [
                        f"rgba({rgb},{0.12 + 0.88 * share**2:.3f})"
                        for _, share in selected
                    ],
                    "line": {"width": 0},
                },
                customdata=[
                    [
                        share * 100,
                        row["r"] * 100,
                        row["h"],
                        row.get("p"),
                        row.get("price_source"),
                    ]
                    for row, share in selected
                ],
                name=name,
                hovertemplate="%{x|%Y-%m-%d %H:%M} UTC<br>8h 等值费率：%{y:.5f}%<br>原始费率：%{customdata[1]:.5f}% / %{customdata[2]}h<br>过去 7 天同号：%{customdata[0]:.1f}%<br>参考价格：%{customdata[3]}<br>价格来源：%{customdata[4]}<extra></extra>",
            ),
            row=2,
            col=1,
        )
    buttons = [
        {
            "label": "完整历史",
            "method": "relayout",
            "args": [
                {
                    "xaxis.range": [stamp(rows[0]["t"]), stamp(rows[-1]["t"])],
                    "xaxis2.range": [stamp(rows[0]["t"]), stamp(rows[-1]["t"])],
                    "yaxis2.autorange": True,
                }
            ],
        }
    ]
    for phase in phases:
        selected = [r for r in rows if phase["start"] <= r["t"] < phase["end"]]
        if not selected:
            continue
        times = [stamp(selected[0]["t"]), stamp(selected[-1]["t"])]
        values = [r["r"] * 800 / r["h"] for r in selected]
        bound = max(abs(min(values)), abs(max(values))) * 1.1
        buttons.append(
            {
                "label": phase["label"],
                "method": "relayout",
                "args": [
                    {
                        "xaxis.range": times,
                        "xaxis2.range": times,
                        "yaxis2.range": [-bound, bound],
                    }
                ],
            }
        )
        if rows[0]["t"] < phase["start"] < rows[-1]["t"]:
            for panel in [1, 2]:
                fig.add_vline(
                    x=phase["start"],
                    row=panel,
                    col=1,
                    line_width=0.6,
                    line_color="#aaaaaa",
                )
    fig.update_yaxes(
        type="linear",
        title_text="现货价格（USD / USDT）",
        tickformat=",.0f",
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="资金费率（% / 8h 等值）",
        zeroline=True,
        zerolinecolor="#888888",
        row=2,
        col=1,
    )
    fig.update_xaxes(
        title_text="结算时间（UTC）",
        rangeslider={"visible": True, "thickness": 0.10},
        row=2,
        col=1,
    )
    fig.update_layout(
        title=f"{dataset['id']} · 红正蓝负，过去 7 天同号越集中颜色越深",
        template="plotly_white",
        height=760,
        margin={"l": 75, "r": 35, "t": 100, "b": 65},
        barmode="overlay",
        hovermode="closest",
        dragmode="zoom",
        legend={"orientation": "h", "y": 1.06, "x": 0.45},
        updatemenus=[
            {
                "buttons": buttons,
                "direction": "down",
                "x": 0,
                "y": 1.12,
                "xanchor": "left",
                "showactive": True,
            }
        ],
        font={"family": "PingFang SC, Arial, sans-serif"},
    )
    path = OUT / f"{dataset['id']}-interactive.html"
    fig.write_html(
        path,
        include_plotlyjs="directory",
        config={"responsive": True, "displaylogo": False, "scrollZoom": False},
        post_script=(ROOT / "price_axis.js").read_text(),
    )
    return path


def main():
    OUT.mkdir(exist_ok=True)
    font_manager.fontManager.addfont(
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
    )
    plt.rcParams["font.family"] = "Arial Unicode MS"
    plt.rcParams["axes.unicode_minus"] = False
    analysis = json.loads((ROOT / "analysis.json").read_text())
    pages = []
    for dataset in analysis["datasets"]:
        rows = json.loads((ROOT / "raw" / f"{dataset['id']}-funding.json").read_text())
        prices = load_price(dataset)
        daily = json.loads((ROOT / "raw" / dataset["price_source"]).read_text())
        reference_path = ROOT / "raw/coinmetrics-BTCUSD-reference-daily.json"
        reference = (
            json.loads(reference_path.read_text())
            if dataset["id"] == "bitmex-XBTUSD"
            else None
        )
        rows = with_prices(rows, daily, reference)
        prices = [
            row
            for row in prices
            if rows[0]["t"] - DAY <= row["t"] + DAY <= rows[-1]["t"]
        ]
        plot_static(dataset, rows, prices, analysis["phase_definitions"])
        pages.append(
            plot_interactive(dataset, rows, prices, analysis["phase_definitions"])
        )
    links = "\n".join(
        f'<li><a href="charts/{path.name}">{path.stem.replace("-interactive", "")}</a></li>'
        for path in pages
    )
    (ROOT / "图表入口.html").write_text(
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>资金费完整历史图表</title><style>body{font:16px/1.7 system-ui;max-width:880px;margin:40px auto;padding:0 20px}li{margin:16px 0}a{color:#205ea6}</style>"
        f"<h1>资金费完整历史图表</h1><p>红色为正、蓝色为负；过去 7 天同方向结算占比越高，颜色越深。选择牛熊分段，或拖选时间区间放大；悬停查看费率和价格。</p><ul>{links}</ul>"
        "<p>竖线与牛熊分段为事后统计标注，不能作为实时买卖信号。2016 年初期 24 小时费率换算成 8 小时等值，不同交易所分开展示。没有资金费的年份没有补零。</p></html>"
    )
    print(f"已生成 {len(pages)} 组完整历史图表")


if __name__ == "__main__":
    assert concentration([{"t": 0, "r": 1}, {"t": 1, "r": -1}, {"t": 2, "r": -1}]) == [
        1,
        0.5,
        2 / 3,
    ]
    main()

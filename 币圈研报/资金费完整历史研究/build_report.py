import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def number(value, digits=2):
    return f"{value:,.{digits}f}" if value is not None else "未获取"


def percent(value):
    return f"{value:+.2f}%" if value is not None else "无可评估样本"


def table(headers, rows):
    return [
        f"| {' | '.join(headers)} |",
        f"| {' | '.join('---' for _ in headers)} |",
        *[f"| {' | '.join(str(item) for item in row)} |" for row in rows],
        "",
    ]


def main():
    analysis = json.loads((ROOT / "analysis.json").read_text())
    datasets = analysis["datasets"]
    lines = [
        "# BTC、ETH 全历史资金费：牛熊分段、集中价格与买入验证",
        "",
        "创建于 2026-10-02",
        "",
        "## 核心结论",
        "",
        "持续负资金费可以提供逆向观察线索，但本次完整历史验证不能把它升级为跨币种、跨交易所都稳健的高胜率买点。BTC 部分样本后续表现较强，ETH 短期结果较弱；信号出现后仍可能经历很深的下跌。",
        "",
        "2012 年有 BTC 价格记录，但没有本次研究对应的永续资金费记录。BTC 资金费最早实际取得 BitMEX 2016-05-14，ETH 最早取得 BitMEX 2018-08-02；币安 BTC/ETH 从 2019 年开始。不同交易所不拼接成一条伪连续费率，也不把缺失填成零。",
        "",
        "[打开交互图表入口](./图表入口.html) · [TradingView 指标源码](./funding_concentration.pine) · [指标使用说明](./TradingView指标使用说明.md)",
        "",
        "## 图表如何阅读",
        "",
        "横轴是 UTC 时间，主纵轴是资金费率（百分数，统一为每 8 小时等值）。红色表示正费率、蓝色表示负费率。每个结算点的颜色深浅由截至当时过去 7 天内同号结算次数占比决定，占比越高越深；它不表示费率金额更高。早期不足 7 天的区域属于不完整窗口。",
        "",
        "价格面板使用日收盘价：交互图采用线性纵轴，并按当前可见时间段的价格自动缩放、上下留 8% 余量；静态全历史图保留对数坐标。早期 BTC 使用 CoinMetrics 日参考价，之后用币安现货收盘。选择阶段、拖动时间滑块或框选放大时，交互价格纵轴同步调整；悬停可查看费率、同号占比和参考价格。灰色竖线是事后牛熊边界，不能实时预知。",
        "",
        "## 数据范围与缺口",
        "",
    ]
    lines += table(
        ["数据集", "第一条 UTC", "最后一条 UTC", "结算数", "周期小时:次数"],
        [
            [
                d["id"],
                d["start_utc"],
                d["end_utc"],
                d["total"]["settlements"],
                json.dumps(d["data_quality"]["funding_interval_hour_counts"]),
            ]
            for d in datasets
        ],
    )
    lines += [
        "本次分析截止 2026-10-02 00:00 UTC，保留最后完整交易日。币安资金费内部网格完整。BitMEX 两合约接口最新只返回到 2026-09-16 12:00，各自尾部 46 个 8 小时时槽未获取；对应阶段占比的分母仅包含已获取记录，不声称覆盖完整尾部。",
        "",
        "早期币安资金费记录缺少结算标记价（BTC 4536 条、ETH 4302 条），使用当时已经完成的上一 UTC 日现货收盘作价格代理。BitMEX 资金费接口不附带价格，同样匹配上一日收盘；BTC 在币安日线开始前使用上一 UTC 日 CoinMetrics 参考价。价格区间因此是粗略区域，不能当作每次结算的精确交易价格。",
        "",
        "完整原始响应、规范记录和缺口检查见 [manifest.json](./manifest.json) 与 `raw/`。",
        "",
        "BitMEX ETHUSD 另以四个日期独立查询各 3 条记录，12 条 `fundingRate` 与保存的小数费率全部一致，没有误用 `fundingRateDaily`。此为同一官方 API 不同参数交叉检查，不冒充独立归档源验证；证据见 `raw/bitmex-ETHUSD-sample-validation.json`。",
        "",
        "BitMEX ETHUSD 必须单独解释：它是 USD 报价、BTC 保证金及盈亏结算的 quanto 合约，与币安 USDT 本位 ETHUSDT 不同。本次统计中其正费率占 98.53%，没有触发 7 天负费率 ≥70% 的规则。BitMEX 2018 年官方研究就讨论过 ETH 下跌但费率仍长期为正，以及 quanto 风险溢价与 ETH/BTC 相关性对定价的影响。这提供了结构性解释，但不能证明本次全历史的全部差异都由单一机制造成。[官方合约说明](https://www.bitmex.com/app/perpetualContractsGuide)；[官方 quanto 定价分析](https://www.bitmex.com/blog/is-the-ethusd-swap-fairly-priced)。",
        "",
        "## 牛熊分段方式",
        "",
        "在预先选定的主要周期年份中，使用币安 BTC 日线最高 high / 最低 low 查找大周期顶底。2017 年币安日线从 8 月 17 日开始，已覆盖 12 月峰值；2018、2021、2022、2025 年覆盖完整。ETH 沿用 BTC 周期以便比较，不等于 ETH 自己的最高点和最低点。",
        "",
    ]
    lines += table(
        ["拐点", "UTC 日期", "BTC 价格（USDT）"],
        [[p["id"], p["date"], number(p["price"])] for p in analysis["turning_points"]],
    )
    lines += [
        "拐点当日整体归入前一阶段，下一 UTC 日开始后一阶段，避免重复计数。首次覆盖是周期中途截入；最后阶段从 2025-10-07 至研究截止日，仅称高点后观察期，尚未确认完整熊市终点。长牛市阶段仍包含 2020 年 3 月、2021 年中等大幅回撤。",
        "",
        "这一分段用于事后描述。买入信号的计算完全不引用顶底日期；阶段只用于事后分组及基线比较。",
        "",
        "## 每个阶段的正负费率占比",
        "",
        "次数占比是同号结算次数 / 全部结算次数；时长占比按每次实际结算周期小时数加权。两者都不是期内每秒预测费率的正负占比。阶段按结算时点归属，不拆分跨边界周期。",
        "",
    ]
    summary_csv = []
    for d in datasets:
        lines += [f"### {d['id']}", ""]
        rows = []
        for phase in d["phases"]:
            s = phase["summary"]
            rows.append(
                [
                    phase["coverage_start_utc"][:10]
                    + "—"
                    + phase["coverage_end_utc"][:10],
                    "高点后 / 未完"
                    if "unconfirmed" in phase["id"]
                    else "熊市"
                    if "bottom" in phase["id"]
                    else "牛市",
                    s["settlements"],
                    f"{s['positive_percent']:.2f}%",
                    f"{s['negative_percent']:.2f}%",
                    f"{s['zero_percent']:.2f}%",
                    f"{s['positive_duration_percent']:.2f}%",
                    f"{s['negative_duration_percent']:.2f}%",
                ]
            )
            summary_csv.append(
                {
                    "dataset": d["id"],
                    "phase": phase["id"],
                    "start": phase["coverage_start_utc"],
                    "end": phase["coverage_end_utc"],
                    **s,
                }
            )
        lines += table(
            [
                "实际覆盖日期",
                "阶段",
                "次数",
                "正次数占比",
                "负次数占比",
                "零占比",
                "正时长占比",
                "负时长占比",
            ],
            rows,
        )
        lines += [
            f"![{d['id']} 全历史图](./charts/{d['id']}-overview.png)",
            "",
            f"[查看可缩放分段图](./charts/{d['id']}-interactive.html)",
            "",
        ]

    lines += [
        "## 集中月份、价格区域和连续段",
        "",
        "以下逐阶段列出正负各自出现次数最多的月份和价格箱。月份括号是该月同号次数，价格箱括号是占本阶段全部同号次数的比例；这些是事后分布，停留时间长也会增加次数。价格箱宽按该阶段价格中位数自动分档，左闭右开，不是人工挑选支撑位。",
        "",
    ]
    for d in datasets:
        lines += [f"### {d['id']}", ""]
        for phase in d["phases"]:
            lines += [f"**{phase['label']}**", ""]
            rows = []
            for sign, label in [("positive", "正费率"), ("negative", "负费率")]:
                months = phase[f"most_{sign}_months"]
                month_text = "；".join(
                    f"{m['month']}（{m['summary'][sign]} 次）"
                    for m in months
                    if m["summary"][sign] > 0
                )
                bins = sorted(phase["price_bins"], key=lambda b: b[sign], reverse=True)[
                    :2
                ]
                price_text = "；".join(
                    f"{number(b['low'], 0)}—{number(b['high'], 0)}（{b[f'{sign}_share_of_sign_percent']:.1f}%）"
                    for b in bins
                    if b[sign]
                )
                run = phase[f"longest_{sign}"]
                run_text = (
                    f"{run['first_utc'][:16]}—{run['last_utc'][:16]}；{run['count']} 次 / 折算 {run['cycle_days']:.2f} 天"
                    if run["count"]
                    else "无"
                )
                rows.append([label, month_text or "无", price_text or "无", run_text])
            lines += table(
                ["方向", "最集中月份", "集中价格箱（USD / USDT）", "最长连续段（UTC）"],
                rows,
            )
        lines += [
            "完整价格箱还同时提供箱内正负发生比例，见 `analysis.json` 的 `price_bins`。不能把“全部负费率有多少发生在这个价格”误解为“到这个价格有多大概率负费率”。",
            "",
        ]

    lines += [
        "## 负费率集中之后，买入结果怎样",
        "",
        "规则在批量分析前固定：过去 7 天已结算记录中，负费率次数占比 ≥70%，且当前费率为负；下一 UTC 日现货开盘买入。信号按时间顺序取首次触发，之后 90 天不再入场。每个事件分别持有 7、30、90 天，在第 N 天收盘退出。主表只使用未来 90 天价格完整的事件，三个期限使用同一批样本。",
        "",
        "这是无杠杆现货事件研究，未计手续费和滑点，也没有把资金费收入算进收益。最大不利波动 MAE = 持有期内最低价 / 入场价 - 1（最多为 0），是相对买入价的最深下跌，不是收益曲线回撤。",
        "",
        "对照包含两个口径：同数据源同期所有可入场日期的基线；再按信号所处牛熊阶段的权重重算基线。后者减少牛熊样本构成差异，但依然是事后描述，不是因果证明。基线日期的持有窗口重叠，不能把数千个日期视作数千次独立试验。不同交易所 BTC 信号共享同一市场，也不是独立实验。",
        "",
    ]
    lines += table(
        [
            "数据源",
            "完整事件数",
            "30日均收益",
            "30日上涨率",
            "90日均收益",
            "90日上涨率",
            "同阶段基线90日",
            "最差90日MAE",
        ],
        [
            [
                d["id"],
                d["backtest"]["complete_90d_signal_count"],
                percent(
                    d["backtest"]["overall"]["30"]["signal"].get("mean_return_percent")
                ),
                percent(d["backtest"]["overall"]["30"]["signal"].get("win_percent")),
                percent(
                    d["backtest"]["overall"]["90"]["signal"].get("mean_return_percent")
                ),
                percent(d["backtest"]["overall"]["90"]["signal"].get("win_percent")),
                percent(
                    d["backtest"]["phase_matched_baseline"]["90"][
                        "weighted_baseline_mean_return_percent"
                    ]
                ),
                percent(
                    d["backtest"]["overall"]["90"]["signal"].get("worst_mae_percent")
                ),
            ]
            for d in datasets
        ],
    )
    lines += [
        "结果支持把集中负费率作为候选观察条件，尚不支持只靠它机械买入。尤其币安 ETH 的 30 日平均收益为负，且弱于同阶段基线。BTC 均值较强，也不能消除深度套牢风险。样本数很少，门槛未做独立样本外测试；本研究开始前已看过部分 2025—2026 数据，因此不能称为严格盲测。",
        "",
        "### 各阶段的验证结果",
        "",
    ]
    for d in datasets:
        rows = []
        for phase in d["phases"]:
            stats = d["backtest"]["by_phase"].get(phase["id"])
            if not stats or not stats["90"]["signal"]["n"]:
                rows.append([phase["label"], 0, "无样本", "无样本", "无样本"])
            else:
                s = stats["90"]["signal"]
                rows.append(
                    [
                        phase["label"],
                        s["n"],
                        f"{s['mean_return_percent']:+.2f}%",
                        f"{s['win_percent']:.2f}%",
                        f"{s['worst_mae_percent']:.2f}%",
                    ]
                )
        lines += [f"**{d['id']}**", ""]
        lines += table(["阶段", "事件数", "90日均收益", "90日上涨率", "最差MAE"], rows)

    lines += [
        "### 全部信号明细",
        "",
        "缺少未来足够价格的尾部事件明确列为未满窗口，不填零。入场价格和结果均来自币安对应现货；BitMEX 2017-08-17 以前没有相同 OHLC，未伪造早期回测。",
        "",
    ]
    signal_csv = []
    for d in datasets:
        lines += [f"**{d['id']}**", ""]
        rows = []
        for event in d["backtest"]["signals"]:
            outcomes = event["outcomes"]
            returns = [
                f"{outcomes[str(h)]['return_percent']:+.2f}%"
                if str(h) in outcomes
                else "未满窗口"
                for h in [7, 30, 90]
            ]
            mae = (
                f"{outcomes['90']['mae_percent']:.2f}%"
                if "90" in outcomes
                else "未满窗口"
            )
            rows.append(
                [event["entry_utc"][:10], number(event["entry_price"]), *returns, mae]
            )
            signal_csv.append(
                {
                    "dataset": d["id"],
                    "entry": event["entry_utc"],
                    "entry_price": event["entry_price"],
                    "phase": event["phase"],
                    **{
                        f"return_{h}d_pct": outcomes.get(str(h), {}).get(
                            "return_percent"
                        )
                        for h in [7, 30, 90]
                    },
                    "mae_90d_pct": outcomes.get("90", {}).get("mae_percent"),
                }
            )
        lines += table(
            ["入场日期UTC", "价格", "7日收益", "30日收益", "90日收益", "90日MAE"], rows
        )

    lines += [
        "## TradingView 自定义指标",
        "",
        "[funding_concentration.pine](./funding_concentration.pine) 为 Pine Script v6，默认读取 TradingView 官方支持的永续资金费数据流，7 天 =21 个已确认的 8 小时样本。红正蓝负，同号越集中颜色越深。它不把历史顶底当作实时信号，也没有依据本次回测在图上画买卖箭头。",
        "",
        "建议先在 `BINANCE:BTCUSDT.P` 的 8 小时普通 K 线图中测试：Pine Editor → 新建指标 → 粘贴源码 → 添加到图表。ETH 在设置里切换合约即可。日线会漏掉日内采样，因此脚本明确要求日内周期。读取上一根已确认数据，柱子相应延后一个采样周期，不回填。",
        "",
        "已核验官方 Request 库的 `_FR` 数据命名与百分数单位，并完成静态检查；尚未在 TradingView 在线编译和核对实际账户的数据权限。数据流的已确认采样未必逐条等于交易所最终结算率，因此其显示与本报告可能不完全一致。细节与兼容模式见使用说明。",
        "",
        "图表验证：静态 PNG 已生成并目视检查，分段计数、7 天滚动窗口、日期对齐已复核。浏览器安全策略拒绝自动访问本机预览页，因此 HTML 的交互操作尚未在浏览器中实机验证；图表文件采用本地 Plotly 依赖，不依赖在线 CDN。",
        "",
        "## 复现与一手来源",
        "",
        "1. `python3 collect_data.py`：读取公开 API，保留原始响应与规范数据；不会读取私有账户。",
        "2. `python3 analyze_history.py`：阶段分布、7天集中度规则和后续收益验证。",
        "3. 安装标准绘图库 `matplotlib plotly` 后运行 `python3 plot_history.py`；运行 `python3 build_report.py` 更新本报告。macOS 字体路径在绘图脚本中。",
        "4. [分段汇总 CSV](./phase-summary.csv)、[全部信号 CSV](./signal-events.csv)、[完整分析 JSON](./analysis.json)。",
        "",
        "- [币安历史资金费与市场数据文档](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)",
        "- [币安现货日线文档](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints)",
        "- [BitMEX 资金费历史 API](https://docs.bitmex.com/api-explorer/get-funding.html)",
        "- [BitMEX 永续产品发布公告](https://www.bitmex.com/blog/announcing-the-launch-of-the-perpetual-xbtusd-leveraged-swap)",
        "- [CoinMetrics 日度参考价时间定义](https://github.com/coinmetrics/docs-website/blob/master/asset-metrics/market/priceusd.md)",
        "- [TradingView 官方 Request 库](https://www.tradingview.com/script/Rpmobpw5-Request/)",
        "",
        "使用的 skill：research。",
        "",
    ]
    for filename, records in [
        ("phase-summary.csv", summary_csv),
        ("signal-events.csv", signal_csv),
    ]:
        with (ROOT / filename).open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    path = ROOT / "资金费完整历史研究报告-2026-10-02.md"
    path.write_text("\n".join(lines))
    print(f"报告已生成：{len(lines)} 行")


if __name__ == "__main__":
    main()

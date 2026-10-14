# TradingView 资金费方向集中度指标

创建于 2026-10-02

对应文件：`funding_concentration.pine`，Pine Script v6，支持日内和 1D 日线。横轴为图表时间，纵轴为资金费率百分数。正值红色、负值蓝色；当前方向在最近有效采样中占比越高，颜色越深。默认 21 个 8 小时样本，数据连续时对应 7 天。日线分别显示当天正、负采样费率的合计，日内显示单次采样值。

## 直接试用

1. 在 TradingView 打开普通 K 线图，建议 `BINANCE:BTCUSDT.P`，图表周期可设为 8 小时或 **1D**。
2. 打开 Pine Editor，新建指标，粘贴 `.pine` 文件全部内容，保存并添加到图表。
3. 默认「TradingView 资金费」模式请求 BTCUSDT 永续的真实资金费数据流；ETH 可将设置中的永续合约改为 `BINANCE:ETHUSDT.P`。
4. 默认采样周期为 480 分钟，窗口 21。**切到 1D 时仍保留采样周期 480，不改成 1D。** 纵轴 `0.01` 代表 `0.01%`，不是 `1%`；日内显示单期值，日线显示日内合计，都不自动年化。
5. 数据不足 21 个样本时柱子更淡，并显示「窗口未满」。无数据时明确显示暂无资金费数据，不用价格或溢价代替。

## 数据来源确已查到，未猜 ticker

[TradingView 官方 Request 库](https://www.tradingview.com/script/Rpmobpw5-Request/)于 2025-09-19 的 v2 加入 `cryptoDerivativeMetric()`，提供 Funding Rate。此次实际读取 v3 官方公开源代码，核验其实现用 `ticker.standard(symbol) + "_FR"` 请求 `close`，再乘以 100 转成百分数。因此本指标使用同一命名与单位：日内调用 `request.security()`，1D 调用 `request.security_lower_tf()`，数据不存在时保持缺失。

这是真正的资金费数据流，不是 premium index，也不是永续与现货价差代理。不过，核验到的官方文档没有保证每根 8 小时 K 线的收盘值都与币安该次最终结算费率逐条一致。因此本指标叫「已确认采样」：它适合观察方向集中度；离线报告采用交易所历史结算记录，口径更严格。TradingView 能显示多长历史还取决于其数据源和账户权限，不能据此承诺完整复现交易所档案。

## 1D 的显示和计算

日线通过 `request.security_lower_tf()` 读取当天全部可用采样。默认每天最多 3 个 8 小时样本，逐个加入原来的 21 样本窗口，因此不会把 7 天窗口误改成 21 天，也不会只取一天的最后一个样本。

- 红柱：当天所有正费率之和；蓝柱：当天所有负费率之和。同一天可以同时出现红、蓝柱。例如三次为 `+0.01%、-0.02%、+0.03%`，红柱是 `+0.04%`，蓝柱是 `-0.02%`。
- 红柱深浅看最近 21 个有效样本中的正费率占比，蓝柱看负费率占比；两者都使用该日全部样本处理完后的窗口。
- 当天日线收盘后才提交样本、显示柱子；未收盘日显示「等待日线收盘」。历史柱画在所属日，但数据只有该日收盘后才可知，不能用于当天开盘决策。
- 数据窗口显示当天正负合计、净合计、有效样本数和窗口正负占比。缺失采样不补零；若只拿到 2 个，就按 2 个计算。没有可用采样的日子不画柱。

这里的日合计是采样值相加，不是年化利率，也不是按实际仓位计算的资金费收益。1D 与 8 小时图柱高的统计周期不同；日内旧路径延后一根采样周期显示确认值，不能直接按同一显示日期把两种图的柱子对加。日线只支持原生资金费模式，周线、多日线仍不支持。[官方低周期数组请求说明](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/#requestsecurity_lower_tf)、[官方收盘确认说明](https://www.tradingview.com/pine-script-docs/concepts/bar-states/#barstateisconfirmed)

## 时间、去重与颜色

原生日内模式以资金费数据流的上一根已收盘采样 K 线为输入，只有该数据源时间戳前进时才记录一次。同一笔 8 小时采样在 1 小时图上不会被重复记 8 次；连续两期费率相同仍是两个独立样本，不会被误删。日内图表周期必须能整除采样周期且不高于采样周期；1D 使用上面的日内数组汇总，采样周期须小于一天并能整除一天。

日内柱子画在已确认数据可用的新周期，不回填到上一周期。当前柱颜色使用最近 21 个有效样本（包含该已确认样本），正柱看正样本占比，负柱看负样本占比。零值占分母、不计正负，缺失值不计数；存在缺失时 21 个有效样本可能横跨超过 7 天。若合约改为 4 小时结算，采样设 240、窗口设 42；此固定设置不能自动重建历史结算周期变更。

脚本没有未来数据引用，不用未完成周期的费率重写历史。日内模式的 `close[1]` 配合 `lookahead_on` 是读取已确认高周期数据的官方方式；外部模式同样只读上一根。1D 直接读取日内采样，不做一根偏移，并在主图的 `barstate.isconfirmed` 为真时才计数和绘图。源数据事后修订、外部指标自身重绘或加载历史起点改变仍可能改变结果，不属于脚本能消除的因素。[官方跨周期数据说明](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/)

图表时区只改变时间标签，不改变脚本使用的时间戳或数据源 K 线划分；若想与研究图逐点对照，请把图表显示时区设为 UTC。建议直接挂在对应的全天候加密合约图表上，避免其他市场休市导致缺少可接收采样的图表 K 线。[官方时间与时区说明](https://www.tradingview.com/pine-script-docs/concepts/time/)

## 外部指标兼容模式

若原生数据不支持你的合约，可先添加一个可靠资金费指标，再切换为「外部指标输出」，在「外部资金费输出」选择该指标的费率 plot，并核对百分数/小数单位，最后勾选确认。默认不勾选，避免把图表价格误画成资金费。

外部模式只支持日内图，要求图表周期与采样周期一致，不把 `input.source` 再放进跨周期请求；无法从一个日线外部输出恢复当天三次独立费率。来源必须是非重绘资金费指标；若选择预测费率或代理估算，本脚本不会使它变成真实结算费率。外部指标需按图表时间正确对齐数据，本指标无法仅凭数值判断一个输出是不是重复或过期。[官方 source input 文档](https://www.tradingview.com/pine-script-docs/concepts/inputs/)

## 验证情况

已核验官方库源码中的 ticker 格式、百分数换算与确认值请求方式，以及 1D 所用的低周期数组请求与收盘确认规则；已做离线静态检查，脚本包含运行时计数一致性检查。尚未在 TradingView 编辑器中编译、加载或核对账户实际数据权限，不宣称已经通过在线编译。

在线验证限制：本次浏览器连接一度返回 `unsupported Codex auth method: apikey`；随后原生 Chrome 读取虽可用，但单次调用耗时约 8 分钟，未继续操作 Pine 编辑器。没有调用未经核实的匿名编译接口。

二次静态审查已核验：`chart.is_standard` 有官方 v6 示例，`timeframe.in_seconds()` 可赋给 `int`；布尔条件显式处理 `na`，没有依赖 v6 已移除的布尔缺失值。窗口数组、计数与去重时间戳都使用普通 `var`、未使用 `varip`，实时 K 线重复执行会回滚到上一根已确认状态，再重算同一采样，不把每个 tick 重复提交为新样本。此结论属于代码与官方执行模型审查，不代替线上编译。[官方调试示例](https://www.tradingview.com/pine-script-docs/writing/debugging/)、[官方时间周期输入示例](https://www.tradingview.com/pine-script-docs/concepts/inputs/)、[官方执行模型](https://www.tradingview.com/pine-script-docs/language/execution-model/)

可在文件目录重跑最小静态检查（不代替 Pine 编译）：

```sh
python3 - <<'PY'
from pathlib import Path

source = Path('funding_concentration.pine').read_text()
assert source.startswith('//@version=6')
assert '[close[1], time[1]]' in source
assert 'sampleTimestamp > lastTimestamp' in source
assert 'input.int(21,' in source
assert 'ignore_invalid_symbol = true' in source
assert 'sampleSigns.shift()' in source
assert 'externalSource[1]' in source
assert 'timeframe.isdaily and timeframe.multiplier == 1' in source
assert 'request.security_lower_tf(fundingSymbol, sampleTimeframe, [close * 100, time]' in source
assert 'if barstate.isconfirmed and not na(dailyRates) and not na(dailyTimes)' in source
assert 'for [sampleIndex, rate] in incomingRates' in source
assert '1D 正费率合计（%）' in source and '1D 负费率合计（%）' in source
print('静态检查通过；尚未执行 Pine 编译。')
PY
```

使用的 skill：初版研究使用 research；本次 1D 支持未使用额外 skill。

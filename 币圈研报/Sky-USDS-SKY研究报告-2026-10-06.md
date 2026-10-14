# Sky / USDS / SKY 深度研究报告

创建于 2026-10-06

> **研究对象**：Sky Protocol，原 MakerDAO；重点区分 USDS、DAI、sUSDS、stUSDS 与 SKY。
>
> **核验时间**：2026-10-06，主要快照采集于 15:48—16:15，Asia/Singapore（UTC+8）。价格、资产、质押数据来自不同分钟，未保证同一区块。
>
> **统计窗口**：近 30 日为 2026-09-06—2026-10-05；上周为 2026-09-28—2026-10-04，均按完整 UTC 日。本文 DefiLlama TTM 为 2025-10—2026-09 的 12 个完整自然月；BA Labs 看板自身的滚动 TTM 另标截止日。进行中的 10 月 6 日不计入收入年化。
>
> **分析结构**：参考《Ethena-USDe-ENA研究报告-2026-09-17.md》，依次讨论业务、代币价值、历史压力与投资判断。本文重新核验 Sky 的事实，不沿用参考报告中的历史市场数字。
>
> **金额口径**：除代币枚数另有标注外，金额均为美元；“收入”不自动等于净利润，“回购”不自动等于销毁，“流通量”不自动等于可自由出售的筹码。

## 核心摘要

**Sky 的核心业务，是以 USDS/DAI 获得资金，通过加密抵押借贷、机构贷款和现实资产配置赚取收益，再支付储蓄成本、运营费用与风险成本。SKY 已有实际执行的收入分配机制，但它既不是稳定币，也不是稳定币储备的法定股权。**

截至本次核验，最值得关注的不是“Sky 有没有收入”，而是：**可持续净盈余有多少、多少需要留下补资本、多少真正分给 SKY 持有人，以及这种分配能持续多久。**

| 核心指标 | 本次读数 | 应如何理解 |
|---|---:|---|
| SKY 价格 | **$0.08835** | CoinGecko 10 月 6 日即时快照 |
| SKY 流通市值 / FDV | **20.72 亿 / 20.74 亿** | 取 CoinGecko market_cap/FDV 字段；按价格×供应约为 20.70/20.73 亿，约 0.1% 差异来自字段刷新时点。两者接近不代表市场上没有潜在卖盘 |
| SKY 总供应 / 数据商流通供应 | **234.60 亿 / 234.29 亿枚** | 预铸转换库存、国库、质押与自由流通仍需分开 |
| USDS+DAI 总发行 | **118.01 亿** | 含预铸缓冲、内部持有和闲置余额 |
| USDS+DAI 对外流通口径 | **100.42 亿** | BA Labs 看板剔除非流通后的口径 |
| sUSDS 底层 USDS 余额 / 当前 SSR | **48.33 亿 / 3.60%** | 治理可调；余额不是 sUSDS 份额枚数 |
| Sky TVL | **61.93 亿** | DefiLlama 特定产品范围，不是完整资产负债表 |
| 穿透 Loan Coverage | **101.45 亿** | 支持借款的覆盖价值，不是额外资本 |
| Sky Reserves | **8,156 万** | 看板定义的储备；远小于毛抵押资产市值 |
| 近 30 日毛费用 / 协议收入 | **2,712.80 万 / 1,347.40 万** | DefiLlama Fees / Revenue，不是审计净利润 |
| 近 30 日协议收入年化 | **1.639 亿** | 过去 30 日运行速度 ×365/30，不是未来预测 |
| 市值 / 近 30 日年化协议收入 | **12.64 倍** | 不能标为 P/E |
| 近 30 日 HoldersRevenue | **541.81 万** | 回购计值＋USDS 质押奖励，非全部现金股息 |
| 上述回流年化 / 市值 | **3.18%** | 全市值尺度的历史指标，不是质押 APY |
| SKY 奖励池 / USDS 奖励池当前年化读数 | **6.58% / 4.53%** | 两类池各自计算，不能相加 |

数据来源：[CoinGecko 市场快照](https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=sky,aave,ethena,hyperliquid,morpho,spark)、[Sky 收入 API](https://api.llama.fi/summary/fees/sky?dataType=dailyRevenue)、[Sky 持有者回流 API](https://api.llama.fi/summary/fees/sky?dataType=dailyHoldersRevenue)、[供给](https://sky.data.blockanalitica.com/internal/supply/)、[储蓄](https://sky.data.blockanalitica.com/internal/savings/)、[风险资本](https://sky.data.blockanalitica.com/internal/risk/info/)、[质押池](https://sky.data.blockanalitica.com/internal/staking/farms/)。API 会继续更新，以上为本次保存并计算的快照。

### 先给出四项判断

1. **业务已经成熟，资产配置也比早期 Maker 复杂得多。** 当前不仅有 ETH 抵押借稳定币，还有大量外部稳定币、链上贷款、机构加密抵押贷款和 RWA。把 Sky 简化为“去中心化美元国债基金”会漏掉信用、清算与交易对手风险。
2. **SKY 的价值承接已经落地，但主要回购用于奖励再分发。** 月度净收入先拨 20% 用于安全与维护；余下的 Protocol Surplus 在 Sky Reserves 低于 1.5 亿美元 Turbo-Fill Floor 时留存 50%，其余按 22.5% 买 SKY 发奖励、22.5% 发 USDS 奖励、5% 买回销毁分配。折回月度净收入，持有人侧合计约 40%，永久销毁仅约 4%。
3. **近期的分配改善不能被误读成业务同步加速，也不是历史最高分配水平。** 2026 年 3 月治理曾把程序化回购从净盈余的 75% 降至 7.5% 以加速补储备，HoldersRevenue 随即从 2 月的 771.90 万降至 4 月的 112.64 万；8 月起的 Stage 2 将分配恢复到 Protocol Surplus 的 50%，仍低于 3 月前的 75%。9 月协议收入较 8 月下降约 4.79%，HoldersRevenue 却增加约 105.18%；按日均校正后，分别为约 -1.61% 和 +112.02%。治理分配变化是主要解释。
4. **当前估值有现金流依据，但“低收入倍数”不是充分买入理由。** 近 30 日收入年化低于过去完整 12 个月的收入；USDC 集中度仍高；Sky Reserves 约 8,156 万，仅为 1.5 亿 Turbo-Fill Floor 的约 54%，在补足前 50% 留存不会自动下调。需要同时验证收益质量、资本充足程度和未来分配约束。

上述分配框架见 [Sky Ecosystem 官方说明](https://www.linkedin.com/posts/skyecosystem_sky-protocols-buyback-framework-starts-with-activity-7507799775547883522-lHTv) 与 [BA Labs TMF 配置帖（Atlas A.2.3.1.2 分配瀑布的逐月执行）](https://forum.skyeco.com/t/treasury-management-function-tmf-configurations/28153)，执行及历史数据详见第 5、8、9 节。

---

## A. 这是什么：项目、产品与赚钱方式

### 1. 从 MakerDAO 到 Sky：项目与稳定币分别何时上线

| 时间 | 事件 | 对今天的意义 |
|---|---|---|
| 2014—2015 年 | Rune Christensen 推动 Maker 构想，随后进入早期开发 | 项目起源早于稳定币正式上线，不能把起源年当产品上线年 |
| **2017-12-18** | 单抵押 Dai 上线，主要以 ETH 抵押生成 | 稳定币业务正式开始；后来通常称这版为 Sai |
| **2019-11-18** | Multi-Collateral Dai 上线 | 支持多抵押品，建立后续 Dai 与 DSR 体系 |
| 2021 年 | Maker Foundation 逐步退出，治理职责转向 DAO | 不是一家持续由原基金会经营、为持币人兜底的公司 |
| **2024-08-27** | 宣布 Maker 向 Sky 品牌升级 | 名称改变不等于协议从零创立 |
| **2024-09-18** | USDS、SKY 及相关升级产品推出 | DAI、MKR 迁移与新产品开始；旧币不会因改名自动全部消失 |
| 2025—2026 年 | Agents、Staking Engine、stUSDS 与新分配框架持续演进 | 今天的资本配置、代币分配和风险结构已不同于早期 Maker |

来源：[早期项目与 2018 年投资说明](https://a16z.com/maker/)、[Dai 上线公告](https://medium.com/@MakerDAO/dai-is-now-live-ad87e34fc826)、[Dai 技术沿革](https://github.com/sky-ecosystem/developerguides/blob/master/dai/dai-token/dai-token.md)、[治理组织 MIP39](https://mips.makerdao.com/mips/details/MIP39)、[Sky 品牌公告](https://forum.skyeco.com/t/sky-has-arrived/24959)、[上线参数提案](https://forum.skyeco.com/t/sky-protocol-launch-season-token-and-product-launch-parameter-proposal/25031)。

#### 1.1 团队与实体：不能用一个“公司”概括

Rune Christensen 是早期创始人和长期参与者，但不能因此把今天的协议治理表述为由一个传统公司 CEO 独立决定。Sky 的治理、前端、基金会、风险服务商和 Agents 分属不同层次。

| 主体 | 主要角色 | 不应推导出的结论 |
|---|---|---|
| Sky Protocol / 治理体系 | 智能合约、参数、资本配置与执行提案 | 不等于统一持牌银行 |
| Skybase International | 经营 sky.money / app.sky.money 等产品入口的独立 Agent | 使用前端不等于取得发行人的存款保险 |
| Sky Frontier Foundation | 开曼基金会公司，运营部分生态信息入口 | 不代表其对全部协议负债承担公司担保 |
| BA Labs / Block Analitica | 风险研究与财务数据看板 | 官方链接的看板不等于独立审计财报 |
| Spark、Grove、Obex 等 | 各自承接资本并运营业务 | 不能统一当作 Sky 的法律全资子公司 |

本报告使用的 financial.skyeco.com 由 BA Labs 提供，其说明明确与正式协议文档独立；相关财务是管理分析口径，未经审计，也不按 GAAP/IFRS 编制。[Skybase 条款](https://docs.sky.money/legal/skybase-international/terms-of-use.md)、[Sky Frontier Foundation 条款](https://insights.skyeco.com/legal/terms-of-use)、[看板来源说明](https://financial.skyeco.com/llms.txt)、[财务方法论](https://financial.skyeco.com/docs/methodology/profit-and-loss)。

#### 1.2 早期资金支持与当前筹码不能混为一谈

- 2018 年，a16z 公告购买约 **1,500 万美元 MKR**。
- 2019 年，Maker Foundation 公告 Dragonfly 与 Paradigm 购买约 **2,750 万美元 MKR**，当时对应约 5.5% 的代币供应。

这些是历史代币交易，不是今天的 Sky 公司股权结构，也不能证明投资者目前仍持有原始数量。本次未取得完整、可验证的当前机构持仓和实际控制人表，不编造最新“团队/机构占比”。[a16z 原始公告](https://a16z.com/maker/)、[Maker Foundation 2019 年公告](https://www.prnewswire.com/news-releases/maker-foundation-announces-27-5-million-mkr-sale-to-dragonfly-capital-partners-and-paradigm-300977381.html)。

### 2. USDS 怎么产生，sUSDS 的利息从哪里来

#### 2.1 用户获得 USDS 的三条常见路径

1. **DAI 升级**：DAI 与 USDS 按 1:1 转换。技术上通过 join/exit 销毁旧币并生成对应新币，不是把 DAI 永久锁住再额外复制一份经济负债。迁移本身不会让合并业务增长。
2. **稳定币兑换**：通过 LitePSM 等路径以 USDC 换 USDS，反向兑换亦依赖相应流动性。主网路由使用共享的 DAI/USDC PSM，再经过 DAI/USDS 转换。
3. **借贷或市场购买**：通过合格抵押/授信安排生成 USDS，或者直接在交易市场购买。持有 USDS 不表示该持有人本人一定开了 ETH 抵押仓。

DAI/USDS 的转换与 MKR/SKY 的迁移是两套不同机制，不能把后者的 5% 迟迁移罚金套到前者。[USDS 技术文档](https://developers.skyeco.com/protocol/tokens/usds/)、[LitePSM 指南](https://developers.skyeco.com/guides/psm/litepsm/)、[DaiUsds 源码](https://github.com/sky-ecosystem/usds/blob/master/src/DaiUsds.sol)。

#### 2.2 五种代币分别代表什么

| 代币 | 持有人实际获得什么 | 收益来源与主要风险 |
|---|---|---|
| **USDS** | 目标为 1 美元的稳定币 | 裸持币通常不自动获得 SSR；有脱锚、资产与合约风险 |
| **DAI** | 同一体系中的既有稳定币 | 可迁移为 USDS；DSR 与 SSR 当前利率不同 |
| **sUSDS** | USDS 储蓄模块的份额 | SSR 累积到份额兑换率；承担协议与稳定币风险 |
| **stUSDS** | 为 SKY 抵押借款提供 USDS 资金的高风险产品份额 | 贷款利息；增加 SKY 清算、利用率和退出流动性风险 |
| **SKY** | 治理及满足条件后的质押奖励参与权 | 代币价格风险、分配政策风险；不是固定面值美元债权 |

**sUSDS 和 stUSDS 只差一个字母，却不是同风险产品。** sUSDS 对应普通储蓄模块；stUSDS 则直接涉及以 SKY 为抵押物的借贷风险。[sUSDS 技术文档](https://developers.skyeco.com/protocol/tokens/susds/)、[stUSDS 技术文档](https://developers.skyeco.com/protocol/tokens/stusds/)。

#### 2.3 sUSDS 的收益：来自协议支付能力，利率由治理决定

存入 USDS 后获得 sUSDS 份额。收益主要体现在每份 sUSDS 可兑换的 USDS 增加，而非每天向钱包额外发送同数量份额。因此 **1 sUSDS 价值高于 1 美元可以是正常累积收益，不能直接判为稳定币溢价**。

本次实时看板：sUSDS 底层余额约 **48.33 亿 USDS**，SSR **3.60%**；DSR 余额约 **2.01 亿 DAI**，利率 **1.25%**；stUSDS 底层余额约 **1.88 亿 USDS**，利率读数 **5.07%**。利率可变，且不是把某笔国债收益无损透传给特定储户。[储蓄 API](https://sky.data.blockanalitica.com/internal/savings/)、[Sky：sUSDS 收益来源](https://sky.money/blog/where-does-susds-yield-come-from)。

如果利率全年不变，以 10,000 USDS 存入、按 3.6% 年收益读数粗算，一年增加约 360 USDS。这个例子只解释量级；实际由份额兑换率和持有期间的利率路径决定，还不包含 USDS 美元价格变化及交易费用。

#### 2.4 “能随时赎回”要分两层理解

- **sUSDS→USDS**：标准储蓄模块没有固定到期日或常规冷却期。
- **USDS→USDC/法币**：取决于 PSM 中可用的 USDC、参数、链运行及二级市场深度；转换成银行美元还涉及外部发行人和出入金安排。

LitePSM 可以补充预铸 DAI 缓冲，但这不等于可以无限创造用于赎回的 USDC。底层国债、机构贷款、结构化信用也不会在所有压力情景下瞬间变成链上美元。正常时小额交易顺畅，不能证明所有人同时退出时也无滑点。[LitePSM 流动性文档](https://developers.skyeco.com/protocol/liquidity/litepsm/)。

### 3. Sky 怎样赚钱：资金成本、资产收益与信用风险

#### 3.1 收入来源不是单一的“国债利息”

| 业务来源 | 谁支付收益 | Sky 需要承担的成本与风险 |
|---|---|---|
| 传统加密抵押 Vault | 抵押借款人支付稳定费 | 抵押物波动、清算、坏账 |
| 链上借贷配置 | 借款市场的用户 | 利率变化、协议合约、抵押质量与市场容量 |
| 机构加密抵押贷款 | 机构借款人，经 Agent/服务商安排 | 托管、合同、期限、交易对手与抵押处置 |
| RWA：国债、结构化信用等 | 发行人或底层借款人 | 利率、信用、流动性、法律执行和费用 |
| PSM/外部稳定币安排 | 兑换费或相关资产收益、激励和结算 | 发行人、银行、储备与兑付风险；不能全部称为兑换手续费 |
| 清算等其他收入 | 被清算仓位或其他业务 | 波动较大，不能当作稳定经常性利息 |

本次读取的 PSM 参数中 tin/tout 为零，但专用账务快照截至 9 月 30 日；本文不据此断言所有未来兑换永远免费。PSM 收入即使存在，也不意味着都是当前用户支付的换币费。[财务收入方法论](https://financial.skyeco.com/docs/methodology/profit-and-loss)、[PSM API](https://sky.data.blockanalitica.com/internal/psm/LITE-PSM-USDC-A/)。

一个有用的分析式是：

```text
可持续净盈余 ≈ 外部资产收入
             − SSR、DSR 等资金成本
             − Agent、治理及运营支出
             − 预期信用损失与必要调整

持有人当期回流 = 可分配净盈余 × 实际执行的分配比例
```

这不是把不同数据商字段直接相减的会计恒等式。特别是 DefiLlama Revenue 已扣部分储蓄成本，再计算时不能重复扣。

**非生息余额是一项真实的资金成本优势。** 并非全部 USDS/DAI 都支付 3.6% SSR；但也不能将全部资产毛收益率减 3.6%，就说那是全系统净利差。应使用实际生息资产、各类储蓄余额和其对应成本。

#### 3.2 总发行 118 亿，为什么对外流通只有 100 亿

| 2026-10-06 供给快照 | USDS | DAI | 合计 |
|---|---:|---:|---:|
| 总发行，亿美元 | 70.19 | 47.82 | **118.01** |
| 对外流通口径，亿美元 | 61.16 | 39.26 | **100.42** |
| 两者差额，亿美元 | 9.03 | 8.56 | **17.59** |

主要差额包括 LitePSM 预铸 DAI 缓冲约 **7.86 亿**、Spark 持有且未借出的 USDS 约 **4.33 亿**、Agents 资本缓冲 **1.41 亿**，以及其他内部闲置与流动性头寸。不同接口不是同一区块，非流通明细加总与总表差约 35.76 万美元，本文没有用虚构“其他”强行配平。

这个差额不能解释成“DAI 全锁在转换器里，所以重复计算了 17.59 亿”。代码显示 DAI→USDS 是销毁与发行的对应转换；差额来自看板对内部/非流通余额的分类。[供给总表](https://sky.data.blockanalitica.com/internal/supply/)、[非流通明细](https://sky.data.blockanalitica.com/internal/supply/non-circulating/)。

#### 3.3 当前资产穿透：USDC 依赖仍然明显

下表使用同一份、共 135 项的 **Loan Coverage** 穿透记录，表示匹配借款的支持价值。它既不是净资产审计表，也不是把所有底层抵押市值相加。

| 资产分类 | Loan Coverage，亿美元 | 占比 |
|---|---:|---:|
| 外部稳定币等 Stablecoins | **53.46** | **52.69%** |
| 链上加密抵押借贷 | **27.26** | **26.87%** |
| OTC 加密抵押借贷 | **10.23** | **10.09%** |
| AAA 公司债/结构化信用类 | 4.97 | 4.90% |
| 短久期国债 | 4.29 | 4.23% |
| Other | 0.83 | 0.81% |
| Private Credit | 0.21 | 0.20% |
| Basis Trade | 0.20 | 0.20% |
| **合计** | **101.45** | **100%（舍入）** |

稳定币分类中，USDC 约 **44.52 亿美元**，占该分类约 **83.28%**，占全部 Loan Coverage **43.88%**。最大单条记录是 LitePSM USDC，约 **43.53 亿美元**、占全表 **42.91%**。其次还有 PYUSD、RLUSD 等；表中亦有约 0.72 亿内部 USDS，因此本表不是完全抵销内部头寸后的外部净资产证明。

这说明：**资产形式更丰富，并不代表已经消除 Circle、其储备银行和兑付渠道的集中风险。** “稳定币”不等于无风险现金，“AAA”也不等于绝无违约或流动性风险。本次稳定币分类未出现 USDe/USDtb，不能进一步断言所有多层配置完全没有 Ethena 间接敞口。[资产穿透看板](https://financial.skyeco.com/usds/collateral-backing)、[原始资产明细](https://sky.data.blockanalitica.com/internal/backing/items/)。

#### 3.4 Spark、Grove、Obex：为什么 Sky 不只是一个借贷市场

本次 Prime API 中，Spark、Grove、Obex 对 Sky 的债务/资金义务分别约 **37.47 亿、18.25 亿、4.04 亿美元**。这是 Agent 层面的口径，不能加到 USDS 总供给、Sky TVL 或穿透资产上制造更大的“生态总资产”。[Primes API](https://sky.data.blockanalitica.com/internal/primes/)。

- **Spark**：包含 SparkLend、储蓄产品和 Spark Liquidity Layer。SparkLend 直接经营借贷市场；SLL 则在多个市场和策略间配置流动性。USDS 是 Sky 发行，不能因 Spark 使用 USDS 就说是 Spark 自己发行的稳定币。
- **Grove**：机构信用与 RWA 配置。2026 年 7 月公布的 Galaxy 贷款安排上限为 **5 亿美元**；本次配置表可见约 **3.75 亿美元**，额度不等于已经全部投放。业务引入机构客户，也引入服务商、托管、合同执行与期限风险。
- **Obex**：在本次看板中已有独立配置和资本记录，不能只凭总规模推断其全部底层借款人的质量。

Spark 新版 Savings 产品与 Sky 的 sUSDS 也需区分：前者可能由 SLL 及其治理决定收益，后者使用 Sky 治理设定的 SSR。[SparkLend 文档](https://docs.spark.finance/products/sparklend)、[Spark Savings 文档](https://docs.spark.finance/products/spark-savings)、[Grove–Galaxy 原始公告](https://grove.finance/blog/grove-and-galaxy-digital-announce-usd500-million-warehouse-lending-facility)、[当前配置明细 API](https://sky.data.blockanalitica.com/internal/allocations/?limit=1000)。

### 4. 合规与法律权利：链上可见不等于资产可无条件索取

Sky 同时跨越代码、治理、法币稳定币发行人、RWA 法律结构和机构借贷。评估安全性需要逐层识别责任主体。

| 层次 | 可以核实什么 | 仍需关心什么 |
|---|---|---|
| 链上合约 | 余额、转换、参数、执行与权限 | 漏洞、权限变更、治理控制和升级风险 |
| USDC 等外部稳定币 | 链上余额、发行人储备披露 | 银行渠道、冻结、兑付和法律限制 |
| 国债/信用配置 | 持仓凭证、基金或 SPV 结构、合同安排 | 底层所有权、受益权、赎回条件与破产执行 |
| 产品前端 | 当期服务条款与可用地区 | 前端开放不等于所有地区具有同样法律权利 |
| USDS / SKY 持有人 | 各产品合约定义的功能 | 不自动获得对每项储备资产的直接按份索取权 |

早期 Maker RWA 法律评估就涉及 SPV、信托、服务商与控制协议；部分底层合同并非全部公开。历史案例可以说明法律执行链条的重要性，不能替代对今天每个 Agent 的独立审查。[New Silver 风险与法律评估](https://forum.skyeco.com/t/rwa-002-new-silver-restructuring-risk-and-legal-assessment/21417)。

对投资判断而言，关键不是简单贴“中心化/去中心化”标签，而是识别：**谁欠谁钱、谁能停止兑付、谁有资产处置权、发生违约后谁有资格追索，以及恢复现金流需要多久。**

---

## B. 代币值多少：SKY 权利、分配、估值与供给

### 5. SKY 已有哪些实际权利，回购和销毁如何执行

#### 5.1 持有、质押与抵押借贷是三个动作

裸持有 SKY 获得的是代币价格敞口和相应治理功能；参与 Staking Engine 后，可以获得所选奖励池的奖励并委托治理权。还可以选择抵押 SKY 借 USDS，但借款不是领取奖励的必要前提。

“没有固定锁期”的表述不能用于忽略借款约束：如果仓位有债务，能否提出 SKY 取决于抵押率等条件；价格下跌可能触发清算。[SKY 概览](https://sky.money/blog/understanding-the-sky-token)、[质押机制说明](https://sky.money/blog/what-staking-sky-unlocks)。

#### 5.2 现行 Stage 2：四个去向必须拆开

按 Atlas A.2.3.1.2 的分配瀑布，起点是月度结算（MSC）确定的**净收入**，不是总手续费，也不是直接照搬 DefiLlama Revenue：

1. **Step 1**：净收入的 20% 用于安全与维护，Core Council、Fortification Conserver 各 10%；
2. **Step 2**：余下 80%（官方帖称 Protocol Surplus）按 Sky Reserves 相对 **1.5 亿美元 Turbo-Fill Floor** 及目标储备的位置决定留存比例；当前储备低于 Floor，留存 **50%**；
3. **Step 3**：剩余部分按 45% / 45% / 10% 分为 SKY 奖励回购、USDS 奖励和回购销毁。

| 去向 | 占 Protocol Surplus | 折合月度净收入 | 对持有人的经济作用 |
|---|---:|---:|---|
| 安全与维护（Step 1） | — | **20%** | 先于留存和分配扣除，不进入持有人回流 |
| 买 SKY，发给 SKY 奖励池 | **22.5%** | 18% | 产生买盘；分发后接收者仍可以出售 |
| 发 USDS 给 USDS 奖励池 | **22.5%** | 18% | 更直接的稳定币分配，但需满足质押等条件 |
| 买 SKY 并永久销毁 | **5%** | 4% | 实际销毁后减少总供应 |
| 留存储备（Step 2） | **当前 50%** | 40% | 增强协议承受损失的能力，不是当期可领取奖励 |

官方表述为“至多 50%”留存：留存比例随储备水平而定，储备达到 Turbo-Fill Floor 后可能下调，届时同样的盈余对应更高回流。本文未取得 Step 2 的逐档参数，不推算下调后的具体比例。以 8 月结算为例，MSC 净收入 1,574.53 万 USDS，Step 1 拨出 314.91 万，留存 629.81 万，USDS 奖励与 SKY 奖励回购各 283.42 万，销毁回购 62.98 万。

“买回后发给质押者”有真实价值：奖励由收入购买，而非必然新增发行。但它与永久销毁的供给效果不同。**回购再分发是资金流向持币人的渠道，销毁才是减少代币总量的动作。** 同一批买回的币之后销毁，不能再将其市值重复加入持有人回报。

来源：[官方分配框架](https://www.linkedin.com/posts/skyecosystem_sky-protocols-buyback-framework-starts-with-activity-7507799775547883522-lHTv)、[TMF 分配瀑布与逐月参数](https://forum.skyeco.com/t/treasury-management-function-tmf-configurations/28153)、[2026 年 8 月执行提案](https://vote.sky.money/executive/template-executive-vote-initialize-sbe-beam-monthly-settlement-cycle-for-july-2026-lssky-sky-rewards-normalization-increase-buybacks-and-reactivate-lssky-usds-farm-adjust-grove-and-osero-dc-iam-parameters-rename-osero-chainlog-keys-update-safe-harbor-agreement-prime-agent-proxy-spells-august-13-2026)。

#### 5.3 不只看提案标题：本次核对了实际执行状态

| 治理事项 | 提案日期 | 官方 API 的实际执行时间，UTC | 已确认内容 |
|---|---|---|---|
| Stage 2 相关 SBE、奖励与分流调整 | 2026-08-13 | **2026-08-17 14:02:23** | 买回路径与 USDS 奖励分流调整，奖励流更新 |
| 8 月结算对应销毁等事项 | 2026-09-10 | **2026-09-13 12:42:11** | 销毁 **2,860,943.76 SKY**，迟迁移罚金升至 5% |

9 月这笔是新 Stage 2 净回购销毁安排下的首次执行，**不是 SKY 历史上第一次销毁**。2025 年 6 月的历史执行提案已包含清理转换器多余预铸币，以及销毁约 4.26 亿 SKY 抵消早期排放等事项；两类销毁的目的和分母不同。

销毁量并非事先固定：Flapper 买回的 SKY 全部先进入 Pause Proxy，再按 10/55 归属销毁。9 月这笔对应 8 月 17—31 日的实际回购，共支出 1,026,300 USDS、购入 15,735,190.69 SKY，均价约 0.065223；其中 10/55 即 2,860,943.76 SKY 销毁。10 月 8 日执行起改按上一完整自然月计算。

此外，合约参数 `splitter.burn=55%` 表示该分流器中走买回路径的比例（45%+10%），不能翻译为“协议把 55% 总收入全部销毁”。[治理执行 API](https://vote.sky.money/api/executive)、[9 月执行代码](https://github.com/sky-ecosystem/spells-mainnet/blob/master/archive/2026-09-10-DssSpell/DssSpell.sol)、[2025 年 6 月历史执行提案](https://vote.sky.money/executive/template-executive-vote-spk-farming-initialization-partial-phase-3-mkr-to-sky-migration-smart-burn-engine-parameter-updates-allocator-bloom-a-maximum-debt-ceiling-increase-spark-usds-transfer-launch-project-funding-delegate-compensation-for-may-2025-atlas-core-development-payments-for-june-2025-spark-proxy-spell-june-26-2025)。

#### 5.4 本次取得的回购与奖励实数

| 期间 | 实际购入 SKY 数量 | USDS 奖励累计增加 | DefiLlama HoldersRevenue |
|---|---:|---:|---:|
| 上周，9 月 28 日—10 月 4 日 | **892.63 万枚** | **61.91 万 USDS** | **137.78 万美元** |
| 近 30 日，9 月 6 日—10 月 5 日 | **4,148.04 万枚** | **243.58 万 USDS** | **541.81 万美元** |

截至 10 月 6 日接口当前快照，历史累计回购实际支出约 **1.273846 亿 USDS**，购入约 **20.1649 亿 SKY**，平均成本约 **$0.06317/SKY**。该累计以接口覆盖历史为准，不全部归属于刚推出的 Stage 2。

限制有两点：其一，奖励累计增加包括已产生但未必已领取的奖励，不能全部称为已进入用户钱包；其二，本次历史接口完整提供每日购入数量，但未完整取得周度/30 日实际 USDS 成交支出。**用当天币价乘历史购入枚数，是计值，不是历史买入现金成本。**

来源：[回购历史 API](https://info-sky.blockanalitica.com/buyback/historic/?days_ago=9999&format=json)、[当前累计回购 API](https://info-sky.blockanalitica.com/buyback/)、[USDS 奖励池历史 API](https://info-sky.blockanalitica.com/farms/0x38e4254bd82ed5ee97cd1c4278faae748d998865/historic/?days_ago=9999)。

#### 5.5 质押收益率：为什么不能与 3.18% 直接比较

当前质押总量约 **174.21 亿 SKY**。其中 SKY 奖励池约 **88.29 亿枚**，年化读数 **6.58%**；USDS 奖励池约 **85.92 亿枚**，年化读数 **4.53%**。前者用 SKY 发放，后者用 USDS 发放，不应相加为 11.10%。

质押池收益率以该池参与资本为分母；3.18% 则以全部 SKY 流通市值为分母，并使用过去 30 日回流年化。币价、池内质押量、奖励速率和计价时点都会影响两者，因此它们不矛盾，也都不是固定保证。[质押总览](https://sky.data.blockanalitica.com/internal/staking/overview/)、[各池参数](https://sky.data.blockanalitica.com/internal/staking/farms/)。

### 6. 估值：收入倍数便宜到什么程度

#### 6.1 先区分三个收入层次

| 指标 | 近 30 日 | ×365/30 年化 | 不能误称为 |
|---|---:|---:|---|
| Fees | 2,712.80 万 | **3.301 亿** | SKY 持有人的全部收入 |
| Revenue | 1,347.40 万 | **1.639 亿** | 已扣完所有支出和信用损失的审计净利润 |
| HoldersRevenue | 541.81 万 | **6,591.97 万** | 人人可领、全部现金、永久不变的股息 |

DefiLlama 的 Maker/Sky 适配器以稳定费、清算与 PSM 相关年化收入等估算日值，并在 Revenue 中扣除储蓄利率成本；HoldersRevenue 使用购入 SKY 的计值，加上 USDS 奖励池累计奖励增量。源码没有再把同批 SKY 发奖重复加一次，但也没有将它转换成经过审计的自由现金流。[DefiLlama 适配器源码](https://github.com/DefiLlama/dimension-adapters/blob/master/fees/makerdao.ts)。

以本次市值 **20.72 亿美元**计算：

- 市值 / 近 30 日年化 Revenue：**12.64 倍**。
- 市值 / 完整 TTM Revenue：**10.11 倍**，TTM Revenue 约 **2.050 亿美元**。
- 近 30 日 HoldersRevenue 年化 / 市值：**3.18%**。
- 完整 TTM HoldersRevenue / 市值：**2.98%**，TTM 约 **6,181.58 万美元**。

TTM 收入高于近 30 日运行速度，说明使用较低的 TTM 倍数时，必须同时考虑近期收入下降。不能挑最有利分母而不交代趋势。

#### 6.2 与其他协议相比：是筛选工具，不是直接买卖结论

统一用本次市值、相同 30 个完整 UTC 日和 DefiLlama Revenue。

| 协议 | 流通市值，亿美元 | 30 日 Revenue，万美元 | 年化 Revenue，亿美元 | 市值 / 年化 Revenue |
|---|---:|---:|---:|---:|
| **Sky** | **20.72** | **1,347.40** | **1.639** | **12.64 倍** |
| Aave | 27.98 | 488.62 | 0.594 | 47.07 倍 |
| Hyperliquid | 207.10 | 7,241.91 | 8.811 | 23.50 倍 |
| Ethena | 32.85 | 1.79 | 0.00217 | 分母过小，不作为有效比较倍数 |

**流通市值口径会放大 Hyperliquid 与 Sky 的可比性。** SKY 的 FDV 与流通市值几乎相同；HYPE 的流通量约 2.22 亿枚、总供应约 9.55 亿枚，CoinGecko FDV 约 891.6 亿美元，约为流通市值的 4.3 倍。按 FDV 计，Hyperliquid 的倍数约为 101 倍，Aave 约 48.6 倍，Sky 仍约 12.6 倍。两种分母回答的问题不同：流通市值反映当前可交易筹码的定价，FDV 还计入未来解锁的稀释。

这张表只能说明：**在数据商的协议留存收入口径下，Sky 的价格相对现有收入较低。** 不同业务的成本扣除、风险承担与持有人分配方式不同，不能直接当作股票同行 P/E。

尤其 Ethena 的 30 日 Fees 约 **1,833.83 万美元**，不能因为 Revenue 留存口径很小，就说其全部业务收入几乎为零；大量收益可能归于储蓄持有人等。这里不根据单个数据字段推断 ENA 或 AAVE 当前全部代币分配政策。

来源：[Aave 收入](https://api.llama.fi/summary/fees/aave?dataType=dailyRevenue)、[Ethena 收入](https://api.llama.fi/summary/fees/ethena?dataType=dailyRevenue)、[Ethena 毛费用](https://api.llama.fi/summary/fees/ethena?dataType=dailyFees)、[Hyperliquid 收入](https://api.llama.fi/summary/fees/hyperliquid?dataType=dailyRevenue)、[CoinGecko 市场数据](https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=sky,aave,ethena,hyperliquid)。

#### 6.3 反推：怎样的净盈余才能支撑现在的市值

下面不是利润预测。设未来全年的 **Protocol Surplus N**（即月度净收入已扣 Step 1 的 20% 后的部分）分别为不同数值，现行 50% 留存全年不变，并暂不加入增长估值。以当前 20.72 亿市值为固定分母：

| 假设年度 N | 50% 总回流配置 | 总回流 / 市值 | 其中 27.5% 买 SKY | 其中 5% 买回销毁 | 销毁预算 / 市值 |
|---|---:|---:|---:|---:|---:|
| 8,000 万 | 4,000 万 | 1.93% | 2,200 万 | 400 万 | 0.19% |
| 1.2 亿 | 6,000 万 | 2.90% | 3,300 万 | 600 万 | 0.29% |
| 1.6 亿 | 8,000 万 | 3.86% | 4,400 万 | 800 万 | 0.39% |
| 2.0 亿 | 1.0 亿 | 4.83% | 5,500 万 | 1,000 万 | 0.48% |
| 2.5 亿 | 1.25 亿 | 6.03% | 6,875 万 | 1,250 万 | 0.60% |

总回流配置包括 USDS 奖励、SKY 奖励买回与销毁预算；不代表所有金额都以现金支付给每个持币人。买 SKY 的 27.5%=22.5% 奖励＋5% 销毁。储备留存也有经济价值，不能视为毫无价值，但其变成持有人可领取收益的时间和条件并不确定。

如果仅靠当前 50% 分配来实现相当于市值 **5%** 的年度回流，要求 N 约 **2.072 亿美元**；若要求 **8%**，则要求 N 约 **3.315 亿美元**。换算回月度净收入（N=0.8×净收入），分别约需 **2.59 亿**和 **4.14 亿**。前者已经高于当前 30 日 Revenue 的年化值，而后者更高；考虑 Revenue 尚不等于扣完所有成本的 N，市场若接受当前价格，通常还隐含增长、资本积累或未来分配改善的预期。

反过来，储备补足到 Turbo-Fill Floor 后若留存比例下调，同样的 N 会对应更高回流。这是现行规则内的上行选项，但需要先补约 6,844 万储备，且以收入不下滑为前提。

因此，更合理的判断是：**Sky 有可估值的现金流基础，但当前价格不是单凭极高当期分红率就能解释的“收息资产”。**

#### 6.4 利率下降一定是利空吗

不一定，要同时看资产收益和资金成本。

举一个明确的假设：若有 60 亿美元资产收益率下降 1 个百分点，年收入约少 6,000 万；若同期约 48.33 亿 sUSDS 的支付利率也下降 1 个百分点，粗略减少年成本约 4,833 万，两者净影响约 -1,167 万。这里的 60 亿是情景假设，不是本次已确认的全体利率敏感资产余额；计算也未处理复利、内部余额和规模变化。

真正的问题在于：资产利率与 SSR 是否同步调整、低收益资产占比多少、削减 SSR 会不会导致储蓄外流，以及收回资金是否需要折价。**降息既可能压缩毛收入，也可能降低负债成本；净效应需要逐项测算。**

### 7. 供应、迁移与潜在卖压

#### 7.1 当前 MKR→SKY 迁移规则

基础比例为 **1 MKR→24,000 SKY**。当前新转换器为单向；9 月执行后迟迁移罚金为 **5%**，因此基础计算为 **1 MKR 到手 22,800 SKY**。旧介绍页中的“双向”“无费用”或“4%”不应覆盖后续已执行规则。[升级总览](https://developers.skyeco.com/guides/sky/token-governance-upgrade/overview/)、[9 月执行代码](https://github.com/sky-ecosystem/spells-mainnet/blob/master/archive/2026-09-10-DssSpell/DssSpell.sol)。

转换器使用事先预铸的 SKY 库存，未迁移 MKR 对应的那部分 SKY 已包含在总供应内，不能再加一遍计算“潜在总量”。但库存进入用户手中后仍可能提高有效可交易供给。

**迟迁移罚金不自动销毁。** 代码记录该部分库存，治理可以通过 `collect` 等授权操作提取。只有后续明确执行 burn 才能计作销毁；“用户少拿了币”不是永久减少总供应的充分证据。[升级代码分析](https://developers.skyeco.com/guides/sky/token-governance-upgrade/codebase-change-analysis/)、[转换器源码](https://github.com/sky-ecosystem/sky/blob/one-direction/src/MkrSky.sol)。

#### 7.2 “停止排放”与“不可修改硬上限”不同

按现行官方政策，奖励使用回购与存量安排，官方称新增排放已停止。但公开 Sky.sol 仍定义授权 `mint` 与授权管理函数；源码存在函数不代表当前一定有可用增发权限，营销措辞也不能独立证明所有权限已永久消失。

本次未完成最新区块全部 `wards` 及授权事件审计，因此本文只确认**现行政策和已执行分配**，不把“永远不能再增发”当作已独立证明的不可修改代码事实。[官方 SKY 说明](https://sky.money/blog/understanding-the-sky-token)、[Sky.sol](https://github.com/sky-ecosystem/sky/blob/dev/src/Sky.sol)。

#### 7.3 哪些卖压比“FDV 接近市值”更值得看

| 来源 | 是否必然新增总供应 | 为什么仍会影响价格 |
|---|---|---|
| SKY 奖励领取后出售 | 否，当前主要由回购/库存支持 | 买回产生需求，奖励兑现可能反向形成卖盘 |
| MKR 迁移库存进入市场 | 不因兑换本身新增 | 老持有人可处置转换后代币 |
| 国库与历史大户出售 | 不一定 | 从低流动性持仓转为实际市场供给 |
| 质押退出 | 否 | 可出售筹码增加；有借款时还涉及抵押约束 |
| SKY 抵押仓清算 | 否 | 下跌时产生被动卖盘，可能放大波动 |
| 新治理改变排放或权限 | 需具体核验 | 属于未来治理与合约权限风险，不能当作已发生 |

本次数据商流通/总供应约 **99.87%**，质押量很高，但这些指标不能替代实际自由流通、持仓集中度和解锁/国库支出的逐项核查。本文未获取完整受益所有人筹码图，也不把“未发现传统 VC 解锁表”写成“未来没有供给压力”。

---

## C. 历史、压力事件与竞争

### 8. 业务是在增长，还是主要靠分配规则重估

#### 8.1 USDS 历史：不能只看迁移后的新币数量

以下为 DefiLlama 每日 USDS/DAI 原始供给序列，单位亿美元。最新日线是 10 月 6 日 UTC 00:00（UTC+8 的 08:00），早于本文即时供给快照；它也未采用前文 BA Labs 的非流通剔除法。

| 日期 | USDS 原始供给 | DAI 原始供给 | 观察 |
|---|---:|---:|---|
| 2024-09-18 | 0.99 | 52.89 | USDS 上线初期，业务不能从零算起 |
| 2024-12-31 | 12.65 | 44.21 | 存在 DAI 向 USDS 的迁移 |
| 2025-06-30 | 42.48 | 42.94 | USDS 规模扩大，但不能全部归因于新增外部需求 |
| 2025-12-31 | 60.11 | 44.98 | 新旧币继续并存 |
| 2026-03-31 | 84.93 | 46.09 | USDS 接近阶段高位 |
| 2026-06-30 | 79.12 | 48.49 | USDS 从高位回落 |
| 2026-08-31 | 66.68 | 47.93 | 原始 USDS 供给继续下降 |
| 2026-10-06 日线 | 67.79 | 48.00 | 较 8 月底回升，但未回到春季高位 |

该序列 USDS 高点为 **2026-04-01 的约 89.50 亿**；至最新日线约下降 **24.26%**。所以“USDS 上线后一直快速扩张”并不符合这一完整路径。

不过，原始供给会受迁移、预铸和内部余额影响，不能直接据此算过去每一时点的对外净需求。本次未取得按同一剔除方法回溯的完整外部流通序列，故不把两条原始序列简单相加后宣布为精确业务增长率。[USDS 历史](https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=209)、[DAI 历史](https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=5)。

#### 8.2 十二个月收入与回流：能看出业务和政策的区别

单位：万美元。按完整自然月汇总同一 DefiLlama 日序列。

| 月份 | Fees | Revenue | HoldersRevenue |
|---|---:|---:|---:|
| 2025-10 | 3,583.26 | 2,515.72 | 1,210.54 |
| 2025-11 | 3,600.11 | 2,253.35 | 850.24 |
| 2025-12 | 3,635.11 | 2,063.04 | 848.61 |
| 2026-01 | 3,493.09 | 1,978.41 | 849.64 |
| 2026-02 | 3,212.94 | 1,702.81 | 771.90 |
| 2026-03 | 3,595.62 | 1,547.83 | 439.15 |
| 2026-04 | 3,393.84 | 1,481.39 | 112.64 |
| 2026-05 | 3,369.91 | 1,508.08 | 115.46 |
| 2026-06 | 3,079.48 | 1,267.55 | 111.11 |
| 2026-07 | 2,967.90 | 1,424.25 | 116.41 |
| 2026-08 | 2,835.67 | 1,411.94 | 247.69 |
| 2026-09 | 2,705.39 | 1,344.37 | 508.19 |
| **合计** | **39,472.30** | **20,498.75** | **6,181.58** |

可以确认两件事：第一，近期 Revenue 较去年秋季明显降低；第二，HoldersRevenue 的起落主要由治理分配比例驱动。

- **3 月下调**：治理把程序化回购从净盈余的 75% 降至 7.5%，以加速补充 Sky Reserves。HoldersRevenue 从 2 月的 771.90 万降至 3 月的 439.15 万，4—7 月稳定在每月 111—117 万，同期 Revenue 只从约 1,548 万降至 1,267—1,508 万。
- **8 月起部分恢复**：8 月 17 日执行 Stage 2 后，分配比例回到 Protocol Surplus 的 50%。8 月只有半个月按新比例运行，9 月是首个完整月，HoldersRevenue 达 508.19 万。
- **仍未回到 3 月前**：50% 低于此前的 75%，且分配前还先扣 Step 1 的 20%。9 月 508.19 万也只有去年 10 月 1,210.54 万的约 42%。

价格计值等因素也会影响该指标，但按幅度和时间点看，两次治理调整是主要解释。[官方分配框架说明](https://www.linkedin.com/posts/skyecosystem_sky-protocols-buyback-framework-starts-with-activity-7507799775547883522-lHTv)。

对价格的因果解释应拆成两条：

```text
业务改善：外部需求增加 → 收益资产与净利差改善 → 可持续净盈余增加

分配重估：既有净盈余 → 更多买回/奖励 → 持有人价值承接增强
```

两条链都可能支持价格，但第二条不要求业务收入同步大增。把它们混在一起，容易在分配率完成上调后继续高估后续增长。[Fees 日序列](https://api.llama.fi/summary/fees/sky?dataType=dailyFees)、[Revenue 日序列](https://api.llama.fi/summary/fees/sky?dataType=dailyRevenue)、[HoldersRevenue 日序列](https://api.llama.fi/summary/fees/sky?dataType=dailyHoldersRevenue)。

#### 8.3 上周只是一个短窗口

9 月 28 日—10 月 4 日：Fees **637.69 万**，Revenue **311.61 万**，HoldersRevenue **137.78 万**。Revenue 比前一周 **318.49 万**下降约 **2.16%**。

财务看板另一套当周 P&L 却只有约 89.30 万毛收入，且 Primes/PSM 项为零。其方法论包括应计、月度结算及事件日记账，本次没有完成与 DefiLlama 运行速度估算的逐项调节。**某周尚未结算入账，不能等同于那些业务完全没赚到钱；也不能拿日估算值冒充已经结算的净利润。**[当周 P&L API](https://sky.data.blockanalitica.com/v1/accounting/profit-and-loss/?date_from=2026-09-28&date_to=2026-10-04)、[财务方法论](https://financial.skyeco.com/docs/methodology/profit-and-loss)。

### 9. 压力测试：经历过什么，今天的缓冲有多厚

#### 9.1 2020 年：抵押足额，不代表清算流程一定有效

黑色星期四期间，ETH 急跌与网络拥堵叠加，拍卖竞价机制失灵，出现零价成交，造成抵押用户损失和协议坏账。后续通过增发并拍卖 MKR 募集资金修复系统缺口；当时资料显示约 20,980 MKR 筹得约 530 万 DAI，对应约 540 万美元量级缺口。

这些数字分别指融资额、系统缺口和用户损失中的不同层次，不能互换。其投资含义是：**抵押品的正常市值、压力下的成交能力与协议可动用资本是三回事。** 历史 MKR 能增发补资本，不证明当前 SKY 完全沿用同一套权限。[当时治理响应](https://forum.skyeco.com/t/black-thursday-response-thread/1433)、[同期 MKR 治理周报](https://forum.skyeco.com/t/mkr-holder-dai-gest-week-14-for-real-2020-today-is-the-first-day-of-the-rest-of-the-dao/1892)、[QUNIE 原始研究摘要](https://www.fsa.go.jp/policy/bgin/ResearchPaper_Summary_qunie_en.pdf)。

#### 9.2 2023 年：外部稳定币风险能够传导给 Dai

Circle 披露约 33 亿美元储备涉及 Silicon Valley Bank，USDC 出现脱锚。Dai 因 PSM 与 USDC 的联系受到影响；Maker 当时通过紧急参数调整限制相关风险流入，并调整兑换条件。后续事件缓解不代表风险链条不存在。[Circle 原始说明](https://www.circle.com/pressroom/3-3-billion-of-usdc-reserve-risk-removed-dollar-de-peg-closes)、[2023-03-11 紧急治理提案](https://forum.skyeco.com/t/emergency-proposal-risk-and-governance-parameter-changes-11-march-2023/20125)。

今天 USDC 在稳定币分类内仍占很高比重，所以不能用“经历过 2023 年”推导“同类风险已经被彻底去除”。本文未核验各交易所当日 Dai 最低价，不引用一个伪精确低点。

#### 9.3 当前资本：172 亿抵押市值不是 172 亿现金

| 本次看板指标 | 金额 | 解释 |
|---|---:|---|
| Total Collateral | **172.19 亿** | 包含借款人的超额抵押市值 |
| Loan Coverage | **101.45 亿** | 匹配借款的覆盖价值 |
| Sky Capital Buffer | **1.41 亿** | 看板资本缓冲字段 |
| Operating Cash Balance | **-5,943.83 万** | 管理会计口径；已经抵减下项 |
| **Sky Reserves** | **8,156.17 万** | 1.41 亿减上述负现金余额 |
| Agent first-loss capital | **2,885.89 万** | 各相关 Agent/配置的第一损失资本，不一定能跨业务自由调拨 |

借款人多抵押的 BTC/ETH，其剩余权益仍与借款人相连，不能把 Total Collateral 减稳定币供给后的差额当作协议可回购资金。负 Operating Cash Balance 也不能直接翻译为银行透支或即将破产；它是特定管理会计字段，应与资本、结算和内部缓冲一起核对，且不能在 Sky Reserves 中再重复扣一次。

Sky Reserves 相当于前文对外流通口径约 **0.81%**。这不是监管资本充足率；不同贷款另有抵押与分层保障。不过，它提示了一项重要限制：**能跨系统直接承担损失的储备，与看起来庞大的毛抵押资产相差很远。**

储备水平还直接决定分配：按 Atlas 分配瀑布，Sky Reserves 低于 **1.5 亿美元 Turbo-Fill Floor** 时，Protocol Surplus 留存 50%。当前 8,156 万约为 Floor 的 54%。多个时点的读数如下：

| 时点 | Sky Reserves | 来源 |
|---|---:|---|
| 2026-08-07 前后 | 8,048 万 | BA Labs TMF 配置帖（8 月 13 日执行输入） |
| 2026-09-04 前后 | 7,573 万 | BA Labs TMF 配置帖（9 月 10 日执行输入） |
| 2026-09-21 | 8,944 万 | Sky 官方分配框架说明 |
| 2026-10-06 | 8,156 万 | 本次风险资本 API |

9 月 21 日至今回落约 790 万，本次未完成逐项归因，可能涉及结算时点、支出或口径差异。储备在月度结算周期内波动明显，不宜用单一读数线性外推“何时补足 Floor”。[TMF 配置帖](https://forum.skyeco.com/t/treasury-management-function-tmf-configurations/28153)。[资本 API](https://sky.data.blockanalitica.com/internal/risk/info/)、[资产穿透明细](https://sky.data.blockanalitica.com/internal/backing/items/)、[资产负债表方法论](https://financial.skyeco.com/docs/methodology/balance-sheet)。

#### 9.4 三个情景，说明风险怎样传导

| 假设冲击，非预测 | 第一层影响 | 后续可能影响 |
|---|---|---|
| 部分储蓄资金集中要求退出 | PSM/二级市场现金需求上升 | 需要收回资产、卖出流动资产或调整利率；折价风险取决于可用流动性 |
| 外部稳定币或机构贷款发生损失 | 先看抵押、合同、第一损失资本与回收率 | 超出保护层后消耗协议储备，可能压低或暂停代币分配 |
| SKY 快速下跌 | SKY 抵押贷款健康度下降 | 清算增加卖压，stUSDS 出资者风险上升，可能形成顺周期反馈 |

仅作规模比较，若有相当于对外流通 **1%**、即约 **1.004 亿美元**的最终净损失真正由 Sky 层面承担，已高于本次约 8,156 万储备。实际损失落在哪一层、能回收多少、是否有其他保障，必须逐笔判断；不能把这个例子当作全体资产同时损失 1% 的预测。

#### 9.5 新模块的上线与自动化不能提前认定

9 月风险月报和 10 月 5 日的 stUSDS keeper 说明显示，部分参数自动化仍在推进，10 月 8 日相关事项截至本报告日属于未来安排。不能把拟上线 keeper 当成已经运行，更不能认为加入 keeper 后就消除了利率、清算或权限风险。[2026 年 9 月风险月报](https://forum.skyeco.com/t/risk-month-in-review-september-2026/28266)、[stUSDS keeper 公告](https://forum.skyeco.com/t/stusds-keeper-launch/28282)。

### 10. 竞争格局：Sky 与 Aave 到底是不是同一类业务

**有交集，但核心商业模式不相同。** Sky 更偏稳定币资金来源、储蓄利率和资产配置；Aave 的核心是多资产借贷市场。Sky 生态中与 Aave 更直接相似的是 SparkLend，而不是把整个 Sky 与一个借贷市场逐项对应。

| 维度 | Sky | Aave / Morpho 等借贷市场 | Ethena |
|---|---|---|---|
| 用户核心需求 | 稳定币、美元储蓄、融资与资本配置 | 存入资产赚息、抵押资产借款 | 合成美元与收益产品 |
| 主要收入驱动 | 资产配置规模、利差、信用与费用 | 借款需求、利用率和协议抽成 | 对冲仓位收益及储备配置等 |
| 核心资金成本 | SSR/DSR、合作与运营支出 | 大量借款利息付给出资人 | 大量收益分给储蓄持有人等 |
| 重要风险 | 外部稳定币、信用、RWA 法律、清算与资本 | 抵押清算、市场结构、合约 | 对冲执行、交易场所、资金费率与抵押资产 |
| 主要规模指标 | 对外流通、收益资产、净盈余与资本 | 同口径存款/TVL、未偿借款、利息与坏账 | USDe 规模、收益结构与对冲覆盖 |

这里是业务分析分类，并不意味着协议之间互斥：Sky 的资金可以配置进借贷市场，借贷市场也可以接纳 USDS/sUSDS，彼此既竞争又合作。

#### 10.1 当前借贷板块龙头：Aave 的规模仍居首

本次同日 DefiLlama 快照，单位亿美元；TVL 与借款余额分别展示，不将 borrowed 再混入 TVL。

| 平台 | TVL | 未偿借款 | 解读 |
|---|---:|---:|---|
| **Aave** | **193.66** | **131.34** | 在这两项借贷规模指标上居首 |
| Morpho | 114.11 | 56.10 | TVL 约为 Aave 的 59%，借款约 43% |
| SparkLend | 56.37 | 29.06 | 直接借贷业务可与前两者对比 |
| Sky 父协议 | 61.93 | 不按同一市场余额横比 | 包含 Sky Lending、Sky Money、Sky RWA 等边界 |

Aave TVL 约为 Sky 父协议的 **3.13 倍**，差约 **131.73 亿美元**；但这并不表示 Sky 的全部资产、稳定币业务或收入只有 Aave 的三分之一。贷款龙头的结论应来自同类借贷余额和市场规模，而非混用不同业务的 TVL。[借贷板块排行](https://defillama.com/protocols/lending)、[Aave](https://defillama.com/protocol/aave)、[Morpho](https://defillama.com/protocol/morpho)、[SparkLend](https://defillama.com/protocol/sparklend)、[Sky](https://defillama.com/protocol/sky)。

#### 10.2 为什么 Sky TVL 61.93 亿小于其稳定币流通 100.42 亿

DefiLlama 的 Sky 父协议产品列表和适配器有明确统计边界，未将所有 Agent 在外部市场、机构贷款和终端借款人处的全部抵押资产统一合并。其 TVL 不是发行稳定币的完整经济资产负债表。

因此，“TVL÷USDS/DAI 流通量”不能直接充当偿付覆盖率，Sky、Spark、Grove 的指标也不能不经抵销就相加。需要分别看发行规模、穿透资产、现金流、抵押保护和风险资本。[TVL 适配器](https://github.com/DefiLlama/DefiLlama-Adapters/blob/main/projects/maker/index.js)。

#### 10.3 稳定币竞争的真正约束

USDT/USDC 的优势包括交易和结算使用网络；USDS 要扩大非生息、稳定使用的余额，不能只靠给出更高储蓄利率。若新增资金完全由高收益吸引，资产端赚到的收入可能大部分又作为吸储成本付出去。

与 USDe 或代币化国债产品竞争时，也应比较收益来源、退出条件和风险，而非只比当前 APY。对 Sky 最有价值的增长，是能保持净利差与资产质量的外部需求增长，而非只把内部库存、补贴和迁移推高。

### 11. SKY 与 BTC：历史上是不是高弹性牛市币

#### 11.1 实际检验，而非只凭机制猜测

使用 Binance SKYUSDT、BTCUSDT 的完整 UTC 日收盘，最后一个收盘日为 2026-10-05。按简单日收益率计算 OLS beta（带截距），不把旧 MKR 价格按名义数字直接拼接到 SKY。

| 窗口 | 日收益样本数 | SKY 涨跌幅 | BTC 涨跌幅 | SKY 对 BTC beta | 相关系数 |
|---|---:|---:|---:|---:|---:|
| 2025-10-05—2026-10-05 | 365 | **+30.50%** | **-30.54%** | **0.95** | **0.58** |
| 2026-07-07—2026-10-05 | 90 | **+63.03%** | **+35.36%** | **1.00** | **0.50** |
| 2026-09-05—2026-10-05 | 30 | **+24.25%** | **+7.43%** | **1.37** | **0.51** |

全年 SKY 日收益年化波动率约 **73.60%**，收盘最大回撤约 **-44.94%**；BTC 对应约 **44.77%**、**-52.97%**。最近 30 日 SKY 年化波动率约 **102.70%**，足以说明带质押收益并不等于价格稳定。

上述涨跌幅使用窗口首尾收盘，因此 30 个收益观测需要 31 个价格观测。它与本文即时 CoinGecko 价格不是同一时点；不能把两套数据的差异解释成计算错误。[Binance SKY 日线](https://data-api.binance.vision/api/v3/klines?symbol=SKYUSDT&interval=1d&startTime=1759622400000&endTime=1791244799999&limit=1000)、[BTC 日线](https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=1759622400000&endTime=1791244799999&limit=1000)。

#### 11.2 数据支持什么，不支持什么

- 全年 beta 接近 1，最近 30 日升至约 1.37；**不支持把 SKY 永久定义为固定倍数的 BTC 杠杆替代品**。
- 全年累计收益与 BTC 相反，同时日收益仍正相关，两者并不矛盾：回归描述日波动关联，全年累计表现还受独立收益与路径影响。
- 全年回归的 R² 约 0.34，意味着该样本中单一 BTC 日收益只能解释一部分波动，不能据此认定其余部分全由回购造成。
- 不同窗口表现差异较大，不证明未来会延续独立上涨，也不证明用 BTC 管理市场风险一定无效。

#### 11.3 更合理的周期链条

```text
加密市场活跃 → 抵押融资与交易流动性需求增加 → 可能改善贷款利用率和收益

美元利率变化 → RWA/稳定币相关资产收益与 SSR 成本共同变化 → 净利差方向待核验

治理分配调整 → 奖励和回购买盘变化 → SKY 相对表现可能重估

风险事件 → 抵押清算或资产损失 → 储备需求上升 → 分配可能减少
```

这四条链可以同时存在。判断 SKY 时，既要看加密融资需求，也要看利率与信用，不能只用“牛市资金费为正”套用全部业务逻辑。

---

## D. 投资判断与跟踪方法

### 12. 风险清单：优先盯哪些会破坏投资逻辑

| 风险 | 传导到 USDS / SKY 的方式 | 本次证据与优先观察项 |
|---|---|---|
| **外部稳定币集中** | 脱锚、兑付或冻结冲击 PSM 和可用资产 | 稳定币分类中 USDC 占全系统 Loan Coverage 43.88%；关注发行人和赎回渠道 |
| **信用与期限错配** | 贷款/RWA 回收慢，储户退出快 | 分开看合同到期、赎回窗口、折价和损失层级 |
| **资本缓冲受损** | 为补储备而削减代币分配（2026 年 3 月已发生过一次：回购从 75% 降至 7.5%） | 当前 Sky Reserves 约 8,156 万，低于 1.5 亿 Turbo-Fill Floor；看金额、变化来源及留存比例 |
| **分配政策改变** | 同样业务收入对应较少奖励/回购 | 以已执行 spell、奖励速率与资本规则核验 |
| **净利差下降** | 资产收入先降，SSR 成本较难同步下降 | 看日均 Revenue、储蓄余额、利率与收益资产结构 |
| **治理/权限风险** | 参数或授权改变，执行延迟或集中 | 审核最新权限、代表控制与执行状态；本次未完成持有人控制权审计 |
| **SKY 抵押清算反馈** | 币价下降引发被动卖出，影响 stUSDS | 看借款余额、抵押率、利用率和可退出流动性 |
| **技术与运营风险** | 合约、oracle、keeper、跨链或托管出错 | 区分已经上线与尚未执行的新模块 |
| **数据口径误判** | 把毛费用、库存、TVL 当利润或净资产 | 固定数据源与期间，保留结算和非流通调整 |

其中，资产配置扩张同时可能提高收入和尾部风险。新 Agent、新机构额度或更高收益率不能自动被记作纯利好；至少还要知道抵押、第一损失资本、期限和法律回收安排。

### 13. 多空论点，以及什么证据会改变判断

| 看多论点 | 对应的反证/限制 | 应等待的证据 |
|---|---|---|
| 已有真实经营收入，价值承接已执行 | 收入不是全部归持币人，分配还受储备约束 | 净盈余与奖励/回购连续匹配，且资本未被持续抽薄 |
| 收入倍数低于一些头部协议 | 可能是信用、增长、治理复杂度的合理折价 | 用一致口径看到净利差与收益质量改善 |
| USDS 可利用长期品牌和合作网络 | DAI 迁移和内部闲置不等于新增外部需求 | 剔除非流通后的净发行增长，且不完全靠提高利率 |
| 回购支持价格，销毁减少供应 | 大部分买回用于再发奖励，销毁仅占 Protocol Surplus 的 5%（约月度净收入的 4%） | 实际净销毁与现金分配持续，而非只公告额度 |
| 储备留存提升长期安全性 | 当前可动用资本仍小于毛抵押数字给人的印象 | 储备随风险资产同步增长，坏账与逾期可核验 |
| 不完全依赖加密资金费率 | 仍受加密贷款、USDC 与利率环境影响 | 收入来源分散能在不同压力期转化成稳定净盈余 |

#### 当前倾向

**业务层面偏正面，价格层面保留条件。** Sky 已具备稳定币负债来源、持续收入和实际执行的持币者分配，在“项目赚钱能否传到代币”这一步上，有明确证据。但当前数据尚不足以支持“低风险、高分红、低估值三者同时成立”。

近 30 日的价格表现强于收入表现，更合理的待验证解释是：市场同时交易分配机制改善、未来增长预期及加密行情，而不只是已经兑现的经营增长。若后续收入没有跟上，单靠一次分配率提升难以无限重复。

**有利于提高长期估值的组合证据**：对外流通稳定增长；净利差不靠提高风险来维持；完整结算净盈余改善；回购和稳定币奖励持续；风险资本相对风险资产没有恶化。

**会削弱当前逻辑的组合证据**：收入下行而奖励靠消耗存量维持；储蓄外流要求快速变现低流动性资产；Agent 发生信用损失；USDC 渠道受损；或治理显著降低持有人分配。

这不是一个单一目标价结论。当前约 20.72 亿市值应与未来可持续净盈余和风险资本需求一起判断，而不是仅凭 12.64 倍收入倍数排序。

### 14. 每周跟踪：怎样判断结论正在被验证

| 每周指标 | 固定口径 | 重点变化及解释 |
|---|---|---|
| Fees、Revenue、HoldersRevenue | 上周完整 UTC 周与前周，同源 | 先拆经营变化和分配变化；标记非经常项 |
| 回购数量与实际开支 | SKY 枚数、USDS 支出分别列 | 实际开支未取得就注明，不能用现价冒充 |
| 永久销毁 | 已执行交易/治理记录 | 提案、通过、执行三种状态分开 |
| USDS 奖励与 SKY 奖励 | 实际奖励增量、速率与池规模 | APY 上升可能源于参与者减少或币价变化 |
| 对外流通量 | USDS+DAI，剔除同口径内部余额 | 拆迁移、库存变动与外部净需求 |
| sUSDS/DSR/stUSDS | 余额、利率、退出与利用率 | 不将三个产品混作一个储蓄池 |
| 资产集中与期限 | 稳定币发行人、Agent、最大借款人等 | 收入增长是否伴随更集中或更难退出的资产 |
| Sky Reserves 与第一损失资本 | 同一看板、同一指标定义 | 变动来自利润、损失、内部转移还是结算调整 |
| 机构/RWA 异常 | 逾期、赎回、托管和法律事件 | 链上余额正常不代表底层现金流正常 |
| 治理和合约权限 | 已执行参数及授权 | 特别关注分配率、资本门槛、mint 和迁移罚金 |
| 估值 | 市值、30 日与 TTM 收入、实际回流 | 一起观察分母是否衰退，不只看币价跌了多少 |

周报适合监测趋势；月度结算后应再复核经营净盈余与资本变动。单周异常先核实结算和数据延迟，不机械外推一年。

---

## 附录一：本报告使用的口径与计算

### 1. 七个容易混淆的数字

| 名称 | 回答的问题 | 不等于什么 |
|---|---|---|
| 稳定币总发行 | token 总账面发行多少 | 对外有效流通 |
| 对外流通 | 剔除规定内部/非流通后剩多少 | 持有人随时可拿到的 USDC 现金 |
| TVL | 数据商指定产品锁定多少资产 | 全生态合并资产或资本 |
| Loan Coverage | 借款由多少支持价值覆盖 | 协议可任意分配的盈余 |
| Total Collateral | 全部抵押物标记市值多少 | 协议净资产 |
| Revenue | 数据商定义的协议留存收入 | 审计净利润/净协议盈余 |
| HoldersRevenue | 指定回购与奖励价值多少 | 全现金分红或永久销毁金额 |

### 2. 算式

```text
30 日年化收入 = 完整 30 日收入合计 ×365/30
收入倍数 = 当次流通市值 ÷ 上述年化收入
历史回流率 = 完整 30 日 HoldersRevenue ×365/30 ÷ 当次流通市值

日收益 r(t) = 收盘价(t) / 收盘价(t-1) - 1
beta = Cov(SKY 日收益, BTC 日收益) / Var(BTC 日收益)
相关系数 = Cov(SKY, BTC) / [Std(SKY) × Std(BTC)]
年化波动率 = 日收益样本标准差 × sqrt(365)
收盘最大回撤 = min[收盘价(t) / 截至 t 的历史最高收盘价 - 1]
```

收益率计算不是总收益指数，没有把 SKY 质押奖励再投入；BTC 也未加入任何借贷收益。最大回撤只基于日收盘，不代表盘中最坏价格。

### 3. 财务看板与 DefiLlama 为什么会不一致

BA Labs 看板截至 2026-10-06 的滚动 TTM 指标，本次约为收入 **4.099 亿**、费用 **2.391 亿**、净收入 **1.708 亿**。本文 DefiLlama 截至 2026-09-30 的完整 12 个自然月 Fees 则约 **3.947 亿**、Revenue 约 **2.050 亿**。

两者的截止日、应计估计、月度结算、成本归类和内部处理不完全相同；本次没有完成逐项桥接。因此不能用其中一个数字给另一个直接贴“错误”标签，也不能把 BA Labs 的净收入与 DefiLlama 收入随意拼接成一套精确现金流表。[财务指标 API](https://sky.data.blockanalitica.com/internal/accounting/financials/)、[利润表方法论](https://financial.skyeco.com/docs/methodology/profit-and-loss)。

## 附录二：本次已确认与仍有缺口的事项

| 事项 | 状态 | 本报告处理 |
|---|---|---|
| 当前 SSR、质押池规模与收益读数 | 已取得当次 API | 使用实时看板，不使用旧营销页利率 |
| Stage 2 调整和 9 月销毁 | 已核对官方执行状态与代码 | 写实际执行日，非提案日期 |
| 周/30 日回购枚数与 USDS 奖励 | 完整日期覆盖 | 可列数量与奖励增量 |
| 周/30 日实际 USDS 回购成交开支 | **未完整取得** | 不以现价计值冒充现金支出 |
| MKR 迁移罚金与兑换方向 | 已核对新文档、代码及执行 | 5%、单向；罚金不自动算销毁 |
| SKY 全部最新 mint/wards 权限 | **未完成独立链上审计** | 不宣称已证明永久不可增发 |
| 当前机构最终持仓与受益所有人集中度 | **未完整取得** | 不编造当前团队/VC 持仓表 |
| 统一口径历史对外流通 | **未取得完整回溯序列** | 原始供给历史与当次调整后流通分开 |
| Agent 全部合同、资产追索与最终回收率 | **未完成逐项法律/信用核查** | 不把看板当审计或无风险担保 |
| 多套财务数字逐项调节 | **未完成** | 保留边界，不强行拼成净利润 |
| 10 月 8 日 keeper/后续事项 | **报告日尚未发生** | 仅列计划，不提前记为执行 |
| Sky Reserves 9 月 21 日后回落约 790 万 | **未完成归因** | 列出多时点读数，不外推补足 Floor 的时间 |
| Turbo-Fill Floor 以上的留存逐档比例 | **未取得** | 只说明“至多 50%”及可能下调的方向，不推算具体比例 |

## 附录三：主要来源索引

优先级为：**已执行治理与合约记录 → 当前技术文档 → 官方原始公告 → 方法公开的数据商 → 本文计算和推断**。不同版本冲突时，不用旧营销页覆盖后续实际执行。

- 产品与合约：[Sky 开发文档](https://developers.skyeco.com/)、[USDS](https://developers.skyeco.com/protocol/tokens/usds/)、[sUSDS](https://developers.skyeco.com/protocol/tokens/susds/)、[stUSDS](https://developers.skyeco.com/protocol/tokens/stusds/)、[MKR/SKY 升级](https://developers.skyeco.com/guides/sky/token-governance-upgrade/overview/)。
- 治理与执行：[执行记录 API](https://vote.sky.money/api/executive)、[TMF 分配瀑布配置帖](https://forum.skyeco.com/t/treasury-management-function-tmf-configurations/28153)、[2026-09-10 执行代码](https://github.com/sky-ecosystem/spells-mainnet/blob/master/archive/2026-09-10-DssSpell/DssSpell.sol)、[2026 年 9 月风险月报](https://forum.skyeco.com/t/risk-month-in-review-september-2026/28266)。
- 资产与资本：[BA Labs 财务看板](https://financial.skyeco.com/)、[资产穿透](https://financial.skyeco.com/usds/collateral-backing)、[方法论](https://financial.skyeco.com/docs/methodology/profit-and-loss)、[API 文档](https://financial.skyeco.com/docs/api)。
- 收入与市场规模：[Sky DefiLlama](https://defillama.com/protocol/sky)、[费用适配器源码](https://github.com/DefiLlama/dimension-adapters/blob/master/fees/makerdao.ts)、[稳定币数据](https://stablecoins.llama.fi/stablecoins?includePrices=true)、[借贷板块](https://defillama.com/protocols/lending)。
- 价格与供给：[CoinGecko SKY](https://www.coingecko.com/en/coins/sky)、[Binance 公开市场数据说明](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md)。

**使用的 skill：research。**

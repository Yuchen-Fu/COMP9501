# 完成实验后的 presentation 逐页修改方案

**依据：** [详细结果与分析](../../DETAILED_FOLLOWUP_REPORT.md)、完整精度 [summary.json](../../results/representation_8h/summary.json)。版本：2026 年 11 月 17 日。

**交付范围：** 本文是可以直接实施的改稿和讲稿方案，配套七张 Python 生成的学术图件；本次没有重建历史 PPT/PDF。旧 deck 继续作为五轮实验的历史版本，不应直接当成本次结论使用。

## 一、整场报告只回答一个主要问题

> **当 counts 与 ports 已经能够确定一笔交易是否是首次观测到的交易对时，再显式加入这个事实，能否改善 AML 预测？**

回答必须和实际证据相符：**这次受控添加实验没有建立正向收益。** 旧替换结果、早期 checkpoint 或 probe 都不能代替主要比较。报告的研究价值在于把这个假设检验清楚，并说明它对 AML 告警意味着什么。

推荐封面标题：

> **Explicit Relationship Novelty in AML Graph Learning**
>
> A controlled study of counts, port ranks and alert trade-offs

不要继续使用暗示已成功的标题，例如 “Making relationship facts explicit improves AML detection”。可以保留用户改过的封面姓名、课程、日期及视觉风格。

## 二、20 分钟的完整结构

正文 14 页、备份 4 页。下列时间合计约 20 分钟，已将主结果和错误分解留出较多讲解空间。标题用完整句子表达论点，正文每页最多三条支撑证据。幻灯片可以用英文，下面同时给出中文讲解重点。

| 页 | 主要任务 | 时间 | 图件 |
|---:|---|---:|---|
| 1 | 提出研究问题 | 0:30 | 无统计图 |
| 2 | 建立 AML 决策背景 | 1:30 | 小型业务指标表即可 |
| 3 | 说明数据与时间难点 | 1:30 | Figure 1 |
| 4 | 既有工作与本项目的缺口 | 1:15 | 旧/新比较文字表 |
| 5 | 解释 counts、ports、novelty | 1:30 | Figure 2 |
| 6 | A/B/C 设计 | 1:30 | 输入槽矩阵 |
| 7 | 预定评价协议 | 1:30 | 简洁顺序文字 |
| 8 | 主要结果 | 2:10 | Figure 3 |
| 9 | AML 告警后果 | 1:50 | Figure 4 |
| 10 | 时间与 checkpoint 敏感性 | 1:30 | Figure 5 |
| 11 | 停止与学习轨迹 | 1:15 | Figure 6 |
| 12 | Probe 的证据边界 | 1:30 | Figure 7 |
| 13 | 结果允许我们说到哪里 | 1:20 | 三层证据表 |
| 14 | 回答问题并结束 | 1:00 | 无新图或新数字 |

## 三、每页具体改法

### Slide 1 — We test whether explicit pair novelty adds value to an AML graph model.

**页面内容：** 封面标题、作者、课程；一行问题：“Does an explicit relationship flag help when counts and ports already determine it?”

**讲述：** 先告诉观众研究什么，不从 Egressy 的分数开场，也不在封面堆模型名和所有限制。口头说：“我们研究的是同一个可推导事实怎样提供给模型，是否会改变反洗钱筛查效果。”

**删除：** “novelty is our successful improvement”、巨大 +9.42 数字框，以及含糊的 “identity effect” 成功宣称。

### Slide 2 — Useful AML screening must control false alerts as well as recover laundering transactions.

**三个完整句子：**

- Most transfers are legitimate, so even a small false-positive tendency can create many alerts.
- We evaluate transaction-level detection and alert counts; we do not measure investigation outcomes.
- Relationship history is useful only if it improves this screening trade-off under a clear evaluation rule.

**视觉：** 使用两行普通文字/小表解释 TP 为被标出的洗钱交易、FP 为被标出的正常交易。不要画一堆人物、金钱或银行图标。此页先让不熟悉 AML 的观众理解“多抓一些”并不等于“系统更有用”。

**讲述：** F1 描述一个阈值下的精度与召回，AP 描述排序。业务人员还关心同样报警预算下能发现多少，但这次主实验没有固定预算比较。

### Slide 3 — The benchmark has rare positives and a highly unusual late test tail.

**证据：**

- HI-Small contains 5.08 million transfers and 5,177 laundering labels; accounts are nodes and transfers are directed edges.
- Whole-day boundaries at days 6 and 8 separate training, validation and testing.
- Day 10 onward contains only 1,108 test transfers but 655 laundering labels, so we also report days 8–9.

**图：** [Figure 1](../../results/representation_8h/detailed_figures/fig01_data_context.png)，占页面宽度约 85%。下方加一行图注：“Figure 1. Test base rates and daily pair novelty. Left axis is logarithmic; novelty and time partitions overlap.”

**讲述：** 用第一张实证图解释数据，而不是先展示模型胜负。明确这是合成数据；first-contact 指观测窗口内的有向交易对，不一定是真实银行的新关系。数据总量可写在正文，不用巨大数字卡片。

### Slide 4 — A replacement gain does not establish an additive benefit.

**证据：**

- Egressy et al. study directed multigraph GNNs and motivate port ranks; Altman et al. provide the synthetic AML benchmark.
- Our five-epoch pilot found +9.42 F1 points when novelty replaced ports under the original protocol.
- That comparison changed two inputs at once, motivating a new comparison that retains ports.

**视觉：** 两行普通表：旧比较 `Counts + Novelty` 对 `Counts + Ports`；新主比较 `Counts + Ports + Novelty` 对 `Counts + Ports`。旧结果明确标记 “pilot; different protocol”。

**讲述：** 论文的 28.7→54.9 只需一句动机和页脚引用。不要声称论文没考虑 counting，不讨论未经核实的章节编号，不把我们旧 +9.42 与论文 +26.2 当成同一种增益。

### Slide 5 — Counts and zero-based port ranks already determine pair novelty.

**证据：**

- A new counterparty receives the next port rank, equal to the previous distinct-counterparty count.
- A repeated counterparty retains a smaller rank.
- Explicit novelty therefore changes the input representation without adding an external relationship fact.

**图：** [Figure 2](../../results/representation_8h/detailed_figures/fig02_relationship.png)。在图下写 `N = 1[d − p < 0.5]`，再用一句话说明 d、p 是非负整数语义下的计数和局部序号。

**讲述：** 逐行走过第一笔、第二笔和第三笔即可，剩下两行让观众自行核对。它不是在任意实数上学习复杂的“相等”，而是一个可线性分离的谓词。不要声称确定性特征绝不改变固定网络的有效函数类或优化难度。

### Slide 6 — The primary contrast adds novelty while retaining counts and ports.

**输入矩阵：**

| Arm | Base attributes | Counts | Ports | Novelty slot |
|---|---|---|---|---|
| A | ✓ | ✓ | ✓ | 0 |
| B | ✓ | ✓ | ✓ | N |
| C | ✓ | ✓ | 0, 0 | N |

**三条支撑：**

- All arms use 11 input slots, 38,997 parameters and matched initialization within each seed block.
- B − A is primary; C − A bridges the earlier replacement question under the new protocol.
- Five new paired seeds, 15–19, are used in every arm.

**讲述：** C 是必做的次比较，不能因它均值最高就改成主要结果。本设计缺少新协议的 Counts-only 组，因此没有完整识别 ports × novelty 交互。

### Slide 7 — Validation rules are fixed before the new training runs.

**证据：**

- A shared training-only scale preserves each count–port relation across periods; scoring uses evaluation mode.
- Each run trains for 20–30 epochs, and the exact highest validation-AP checkpoint is selected.
- The threshold maximizes validation F1; strong support requires positive paired intervals for both test F1 and AP.

**视觉：** 三段简短文字按“训练 → 验证选择 → 测试报告”的阅读顺序排布；不要增加复杂流程箭头。页脚补一句：“Five paired seed blocks; intervals reflect training variation on one previously inspected graph.”

**讲述：** 五种子的规划检测尺度约 5 个 F1 点，来自旧替换对比的方差，不是保证。所有新运行前方案固定，但旧研究已看过该测试图，不能称全新盲测。完整超参数放备份。

### Slide 8 — The controlled addition experiment does not establish a positive benefit.

**图：** [Figure 3](../../results/representation_8h/detailed_figures/fig03_paired_effects.png)，约占页面 70% 高度。图题、灰点、区间都保留，避免只画三组均值柱图。

**支撑证据：**

- The primary paired F1 difference is −7.21 points, with a 95% interval of [−15.46,+1.03].
- All five F1 differences are negative; the AP interval also crosses zero.
- C has the highest mean, but its replacement contrast is uncertain and cannot replace the primary comparison.

**讲述：** 先指向第一行，再讲灰点让观众看到每个种子。结论是“没有建立正向收益”，而不是“什么也不知道”“已证明有害”或“确认等效”。不要临时报告单侧显著性。

### Slide 9 — Most additional false alerts occur on repeated transaction pairs.

**图：** [Figure 4](../../results/representation_8h/detailed_figures/fig04_error_decomposition.png)。图注必须带 “Post-hoc descriptive decomposition at validation-selected thresholds”。

**支撑证据：**

- Adding novelty changes mean true alerts by +101 and false alerts by +1,794.
- First contacts account for 94.5% of the net true-alert increase, while repeated pairs account for 81.6% of the net false-alert increase.
- These are net count changes, not confirmed additional cases or a comparison at equal investigator workload.

**讲述：** 这是对业务最有解释力的一页。明确左右轴尺度不同，图中灰点显示大幅种子波动。输入 flag 在重复交易中为零，不代表重新训练后这些交易的预测不会变；但我们没有识别内部原因。

### Slide 10 — The early F1 advantage does not survive the primary selection rule.

**图：** [Figure 5](../../results/representation_8h/detailed_figures/fig05_sensitivity.png)。完整展示所有预定行，不删去不利 checkpoint。

**支撑证据：**

- Fixed epoch 5 gives a positive F1 interval, but its AP interval still crosses zero.
- The selected-model effect remains negative on days 8–9, so the sparse tail is not a sufficient explanation.
- These views reuse the same dataset and models; they do not provide independent replications.

**讲述：** 不把此页命名为 “Novelty accelerates learning” 或 “The benefit depends on budget”。没有专门确认预算交互，也不能把 AP 与 F1 混为一个指标。它是对主结论的敏感性描述。

### Slide 11 — The stopping rules limit the claim without overturning the observed result.

**图：** [Figure 6](../../results/representation_8h/detailed_figures/fig06_validation_trajectories.png)。图足够大；若投影字号不足，可单独呈现 A/B 两面板，把完整三面板图放备份，但不要重算或挑选轨迹。

**证据：**

- Nine of fifteen runs reached the 30-epoch cap, including every A run.
- Six selected checkpoints occur before epoch 20; the minimum duration does not restrict model selection to late checkpoints.
- Neither the cap nor validation patience proves convergence, and more epochs are not guaranteed to reverse the result.

**讲述：** 黑色均值线只延续至所有五种子都存在的第 20 轮，避免提前停止造成平均样本组成变化。不要说全部 A 最后仍在改善；部分最好 checkpoint 在第 21 或 23 轮。

### Slide 12 — Novelty is decodable, but decodability does not establish AML utility.

**图：** [Figure 7](../../results/representation_8h/detailed_figures/fig07_probe.png)。AP 面板保留约 0.043 的 prevalence 参照。

**证据：**

- Linear probes recover novelty almost perfectly from the raw count–port inputs.
- Frozen 25-dimensional representations retain variable linear signal: AP ranges from 0.12 to 0.44.
- A probe predicts novelty, not laundering, and does not show whether the AML classifier causally uses that signal.

**讲述：** 不能把 0.12–0.44 简化为“模型没学会”；该范围比无信息基准高。也不能说高 AUROC 就表示 AML 已充分利用它。精确 ReLU 推导可留备份，正文只保留可线性分离的概念。

### Slide 13 — The evidence separates feature availability, predictive gain and operational value.

**视觉：** 三行简表，不用六个密集状态框。

| Question | Evidence-based answer |
|---|---|
| Is the relationship fact available? | Yes: the input definition and raw-input probe support recoverability. |
| Does explicitly adding it improve prediction? | Not established under the primary comparison. |
| Does it improve AML operations? | Not established: workload is not fixed, and case outcomes are not observed. |

**讲述：** 自己的贡献是让这三个问题不再混在一起。告警分解是重要的描述性证据；优化不稳定、漂移或输入交互是解释线索，不能作为已经确定的机制。C 也使用 novelty，因此单靠 novelty 漂移不足以解释全部模式。

**简短限制：** One inspected synthetic graph; five seeds; fixed hyperparameters; offline transductive evaluation. 逐条限制不要在最后突然堆一页小字，之前相应页面已解释。

### Slide 14 — A plausible relationship feature still requires a controlled benefit test.

**结论突出，三条证据支撑：**

- Explicit novelty did not meet the prespecified improvement criterion when counts and ports were retained.
- The observed alert increase was dominated by false alerts, with most of the net false-alert increase on repeated pairs.
- Replacement gains and representation probes cannot substitute for an additive task-performance test.

**最后一句讲稿：** “我们的数据没有支持原先期待的 novelty 改进；它支持的是一个更严格的结论：一个关系事实既重要又可推导，并不足以保证显式提供它会改善反洗钱筛查。”

不要在最后临时加入“未来多训练肯定有效”“已超过 AAAI 基准”或“我们仍然成功验证了原假设”。如果被问有没有研究意义，说明这是对明确假设的受控评价与可复核的反例性观察，范围限定在本协议，不能宣称普适反定理。

## 四、备份页

### Appendix A — Exact seed results and the interval definition

放详细报告第 8 节的五种子 F1/AP 表。说明配对差值、df=4、均值±SD与均值区间的区别。解释为何测试交易数不是独立训练重复数；说明五个负差值没有让我们事后更换检验。

### Appendix B — Stopping, scaling and the complete model specification

放 15 次运行的完成/选中轮次表，以及 min 20、max 30、patience 10、delta 0.001。强调同一均值与标准差处理每个 count–port pair。留出空间说明固定预算与不声称收敛。

### Appendix C — What the earlier five-epoch study did and did not identify

保留原 counts × ports 主问题和原始解释比例区间作为历史证据。明确旧 +9.42 是 replacement、原五轮有推理模式及分区归一化差异；新 A/B/C 不能重估原 factorial，也没有新协议 Counts-only D 来识别交互。

### Appendix D — Definitions, provenance and deployment scope

解释 current first-contact edge 不等于 account-never-repeated stratum；有限窗口 novelty 不等于 first-ever relationship。列出原始 ZIP、协议 hash、运行记录路径和逐笔预测未随审阅包导入的事实。说明图评价仍是 transductive，不能据此声称在线因果预测或真实银行效果。

## 五、排版与图件使用规范

- 16:9 页面；延续用户 refined deck 的封面与配色，正文以浅底、深色字为主。标题建议 28–32 pt，正文 22–24 pt，图注 14–16 pt。需要缩到更小才能塞入的内容应移到备份。
- 每页以一个完整论点标题开头。结果页最多三个完整支撑句；不要用 “Better novelty / Identity learnt / Significant!” 之类含糊短语。
- 图占页面约 60%–75%，数值图直接嵌入 Python 输出的 SVG 或高分辨率 PNG；PDF 适合文章。不要在 PowerPoint 里重画柱、置信区间或箭头解释数据。
- 不用巨大数字方框。将关键差值写成一句完整结论，随后放区间、灰色种子点与清楚的轴标签。不能只展示均值。
- 表格可用普通表格对象，但不把全量数据表放入正文。需要用颜色区分模型组时采用 A 蓝、B 赭红、C 绿；种子轨迹和 probe 使用各自明确的图例，不把 probe 的两条线误读成 A/B 模型。
- 每张图下有 `Figure x.`、测量对象、样本单位和必要的限制。Figure 4 注明事后描述；Figure 5 注明同一模型的敏感性视角；Figure 7 标明 probe 目标是 novelty。
- 引用置于相关页页脚，前人介绍一页足够。不要因为负结果就加长文献综述来掩盖自己的实验；也不要把自己所有数字写进正文页。

## 六、图件清单与来源

所有文件位于 [detailed_figures/](../../results/representation_8h/detailed_figures/)，每个图有 `.png`、`.pdf`、`.svg`。

| 图 | 文件 stem | 实际来源 |
|---|---|---|
| Figure 1 | `fig01_data_context` | `diagnostics.json` 与 `summary.json` 的基准率 |
| Figure 2 | `fig02_relationship` | 明确标记的定义示例，不是实测结果 |
| Figure 3 | `fig03_paired_effects` | 主模型的三种配对效应，沿用已保存区间 |
| Figure 4 | `fig04_error_decomposition` | 保存的 confusion counts，新增描述性分解 |
| Figure 5 | `fig05_sensitivity` | 已预定 checkpoint 与 days 8–9 敏感性结果 |
| Figure 6 | `fig06_validation_trajectories` | 15 个运行 JSON 的全部 validation AP 记录 |
| Figure 7 | `fig07_probe` | 五个已完成 probe 的原始输入与隐层评价 |

生成命令：`python src/report_followup.py`。不会训练模型、拟合新 probe、读取测试预测选模或新增显著性检验。完整精度的新增描述数据保存在 [analysis_notes.json](../../results/representation_8h/analysis_notes.json)。

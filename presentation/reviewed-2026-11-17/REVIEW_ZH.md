# 上传版 presentation 审阅：贡献、显著性与定稿修改

审阅日期：2026 年 11 月 17 日（香港时间）。

对象：用户上传的 `What Do Port Numbers Add Counterparty Counts vs. Counterparty Identity in Multigraph GNNs for AML (1).pptx`。实际有 **14 页**；结论和参考文献的可见页码仍为 14、15。本次逐页读取了正文及 speaker notes，渲染了全部页面，并对照仓库结果、训练代码及 Egressy et al. 的论文。

## 总体判断

**作为博士课程的 research presentation，已经有明确的研究问题、实质性实验和统计上清楚的正向结果。主线可以保留。正式汇报前需要补充少量方法披露和范围标注，不需要为这次 presentation 推倒重做或追加训练。**

研究贡献定位为：检验“端口收益能否由四个历史计数替代”的解释，并评价一个简单、可解释的交易对历史特征。第 9 页回答原问题，第 11 页给出强的补充特征结果，第 12 页如实交代保留 ports 后的加法比较。这样能形成完整的研究推进，不必在结论最后加一长串未完成目标。

这些显著性来自一个固定图、五个训练种子的 nominal 配对 t 分析。它们足以支撑本设置内的比较；不应被讲成跨银行总体的统计保证。补充比较未做多重比较校正，讲述时继续保留 supplementary 标签。

## 1. 数字核对

下列区间和 p 值均来自保存的分析，不是本次另选检验重新计算：

| 页面及比较 | F1 差值及 95% 配对区间 | 已保存 p 值 | 判断 |
|---|---:|---:|---|
| 第 9 页：Ports − Base | +7.48 [2.96,12.00] | 约 0.010 | 引用正确。 |
| 第 9 页：Counts+Ports − Counts | +14.91 [10.11,19.71] | 0.000997 | 有明确正向证据，直接支持计数未消除端口收益。 |
| 第 11 页：Counts+Novelty − Counts | +24.33 [21.47,27.19] | 0.0000191 | 原协议中很强的补充结果，五个种子均正。 |
| 第 11 页：Counts+Novelty − Counts+Ports | +9.42 [5.73,13.11] | 0.00210 | 数字正确，页面已正确注明是替换比较。 |
| 第 12 页：CPN − CP，新协议 | −7.21 [−15.46,+1.03] | 页面不需要新增 p 值 | 页面正确报告未建立收益，也未证明损害。 |

第 11 页另列的 days 8–9 F1 +18.19 [17.31,19.06] 与 AP +28.89 [21.05,36.74] 也与保存结果一致。它们使“收益完全由高正例尾部或一个 F1 阈值造成”这一解释不充分，但仍使用相同模型与数据，不是独立重复。

原论文的 [Table 2](https://arxiv.org/html/2306.11586v3#S7.T2) 中 GIN+Ports 的 HI-Small F1 为 54.85，支持第 4 页的四舍五入 54.9；基准约为 28.7。论文 Corollary 4.4.1 也确实讨论了三种适配组合的理论子图检测能力。讲稿最好加上 suitably expressive / under the paper's assumptions，避免让听众将其理解为本项目两层模型能实际检测任意长度模式的保证。

## 2. 这版做得好的地方

1. 第 4 页已经画成“三笔交易来自同一发送方”对“三笔交易来自不同发送方”。边数相同，正文也限定消息特征相同，避免了把“一条消息与三条消息”说成求和无法区分的错误。
2. 第 5 页的端口示例和第 10 页的计数反例正确。第 10 页只说这是 counts 缺少的一个属性，讲稿明确不声称它是 ports 的全部价值。
3. 第 6 页的三个问题分别有实验落点；第 9、11、12 页按顺序回答，逻辑不依赖把不显著结果删除。
4. 第 9 页保留了原计划的 Fieller 区间，措辞是“不支持计数解释大部分收益”，没有把 +8.4% 写成普适确定上限。
5. 第 11 页明确 supplementary，并区分替换与添加；第 12 页说明新协议、同输入维度、新种子、缺少 Counts-only 和不合并两项研究。这些都值得保留。
6. 结论以已建立的贡献收尾，可以继续使用；只需加入一行实验范围，避免把原协议结果变成无条件宣称。

## 3. 正式汇报前优先修正的三处

### A. 第 7 页：“strictly earlier transfers” 应改为固定顺序上的历史

代码对相同 timestamp 使用固定、与标签无关的 tie order。因此 earlier in the order 不完全等于 strictly earlier wall-clock time。

建议替换为：

> Built from preceding transfers in a fixed timestamp-and-tie order.

讲稿补一句：

> Transactions with the same timestamp follow a fixed label-independent order.

并在第 5 页统一定义：

> New pair = first observed directed pair within the dataset window.

这能避免“first ever / never before”被误读成现实银行的完整历史。

### B. 第 7–8 页：原实验的评价设置应明确披露

目前第 12 页介绍新协议更严格，但正文及 notes 没有明确交代产生正向主结果的原协议设置。代码 `src/train.py` 显示：

- 原实验对 train、train+validation、完整测试图分别计算归一化统计量。
- 评分时模型未切换到 eval mode；dropout 和 BatchNorm 的批统计量仍起作用。
- 使用累积 transductive 图，某笔目标交易可接触该时期内更晚的图边，因而不是严格在线回测。
- 五轮刻画固定预算，而不是已验证的收敛表现。

无需另加限制页。可以在第 8 页下方用两行脚注，并在讲稿中解释：

> Experiment 1 uses the original five-epoch transductive protocol, with split-specific normalization and stochastic scoring. Experiment 2 changes preprocessing and scoring and is analyzed separately.

再将 “The network is held fixed” 收紧为：

> The GIN architecture and optimization settings are shared within each experiment.

原实验的输入维度随特征组变化；新实验才将三组统一为 11 个槽位和相同参数数目。不能把后者的控制追溯到原五组。

### C. 结论页：添加范围脚注，不必弱化正面标题

建议保留现有三条贡献，在页底加入：

> Positive findings: HI-Small, original five-epoch protocol, five paired seeds.

方法页或图注再说明：

> Nominal 95% paired-seed intervals, conditional on this dataset; supplementary contrasts are unadjusted.

不需要将结论改成“尚未证明……”的清单。范围限定与正面贡献可以同时清楚表达。

## 4. 逐页简评

| 实际页 | 评价 | 建议 |
|---:|---|---|
| 1 | 原标题过于宽泛，副标题没有体现本项目自己的比较。 | 已改封面主副标题，见下节。 |
| 2 | 能让非图学习观众理解 AML 网络模式。 | 讲述为可疑结构示例；正常资金活动也可能形成这些结构，形状不是洗钱证明。 |
| 3 | 模型输入、两轮消息、边分类流程清楚。 | “accounts start blank” 可口头解释为相同常量初始特征。层内还包含学习变换和非线性，不是纯求和模型。 |
| 4 | 对等边数的例子正确，文献数值有来源。 | 理论能力附带论文条件；不将其视作本项目两层模型的实践保证。 |
| 5 | 端口与历史 distinct count 的例子正确。 | 补上 first observed / finite window 定义，避免 “first ever” 歧义。 |
| 6 | 三问结构是目前最有力的组织方式。 | 可以保留。 |
| 7 | 数据规模、切分与两批运行数正确。 | 修正 strictly earlier；模型来源建议写 “two-layer edge-feature GIN with reference hyperparameters”，避免暗示代码与发表实现逐字一致。 |
| 8 | 2×2 加补充组的设计清楚。 | 增加原评价协议说明，以及 nominal seed-variation interval 的范围。 |
| 9 | 正向对照、单种子点和 Fieller 措辞基本准确。 | 页眉改为 RESULTS。讲稿 “counts alone add almost nothing” 改为“Counts−Base 点估计为 +0.98，但区间较宽，未建立一致收益”；原区间为 [−7.18,+9.14]。 |
| 10 | 反例正确，避免了把 novelty 当作全部 port 信息。 | 保留。页眉可写 INTERPRETATION。 |
| 11 | 最强的补充结果，含时间/AP 支撑，解释克制。 | 页眉改为 RESULTS；五个种子点或区间图比只展示均值条形图更便于评价波动。 |
| 12 | 对新旧协议、加法比较、缺少 Counts-only 的说明正确。 | 保留并正常讲述。可删减重复正文，把详细规则移至 notes，提高投影可读性。 |
| 13（页脚 14） | 贡献清楚，不以未完成目标结束。 | 加一行范围脚注；页脚改为 13。 |
| 14（页脚 15） | 三篇文献齐全。 | 页脚改为 14；新增 IBM/Multi-GNN 与项目 GitHub 链接，使 notes 中提及的 code/materials 有真实入口。 |

## 5. 学术图与版式

我检查了实际 PPTX 结构：第 9 页有 51 个普通形状、零张图片、零个 chart；第 11 页有 26 个普通形状、零张图片、零个 chart。这些统计展示是 PowerPoint 形状组成的，并非嵌入的 Python 输出图。它们的制作方式本身不决定统计结论真假，但没有满足你此前“统计图由 Python 直接输出”的要求。

正式出图时，建议仅替换第 9、11 页的数值图：直接读保存的 JSON，用 Python 生成配对点或差值区间图，并附 Figure 编号。现有配色、版式和讲述顺序可以保留。第 11 页的大 +24.33 数字可以缩小，将视觉重心放在数据图和一句完整结论上。

这版没有明显的整体溢出；部分方法细节和图注投影时可能偏小，尤其第 12 页。渲染检查由 LibreOffice 完成，不保证 Microsoft PowerPoint 与嵌入字体呈现完全相同。

## 6. 已完成的标题修改

**Beyond Counterparty Counts**

*Ports and Pair Novelty in AML Graph Learning*

中文含义：**超越交易对手计数：反洗钱图学习中的端口与交易对新颖性**。

该标题覆盖两个主要正面结果：计数未替代 ports，以及 novelty 在 counts 之外有效。它不预先暗示已将收益分解为 counterparty identity 机制，也不让标题只围绕未建立收益的添加实验。

文件：[Beyond_Counterparty_Counts_AML.pptx](Beyond_Counterparty_Counts_AML.pptx)。另附 [PDF 预览](Beyond_Counterparty_Counts_AML.pdf) 与 [封面](cover.png)。

**修改边界：只修改了封面的主标题与副标题。** PPTX 内仅 `ppt/slides/slide1.xml` 的内容发生变化；其余页面、讲稿、表格、图片、字体及关系文件的解压内容均与上传版一致。上面的正文修改是审阅建议，尚未写入此 PPT。详见 [TITLE_CHANGE.json](TITLE_CHANGE.json)。没有新增训练或统计检验。

## 7. 答辩时可以这样概括贡献

> We tested whether four historical account-level counts could substitute for ports, and found a clear residual port benefit. We then showed that explicitly providing pair novelty substantially improved prediction beyond those counts in the original protocol. These results give an empirical basis for evaluating pair-specific history alongside account-level activity summaries in AML graph learning.

如果被问新协议是否确认了 +24.33，应直接说明：新协议没有 Counts-only，因此不直接重测该比较；它检验的是保留 ports 后再加 novelty 的额外价值，结果未建立正向收益。这两个问题在第 6、11、12 页已经分开，继续保持即可。

## 来源

- [原实验报告与完整结果](https://github.com/Yuchen-Fu/COMP9501/blob/main/RESEARCH_REPORT.md)
- [原实验机器结果](https://github.com/Yuchen-Fu/COMP9501/blob/main/results/summary.json)
- [后续实验机器结果](https://github.com/Yuchen-Fu/COMP9501/blob/main/results/representation_8h/summary.json)
- [原实验训练与评分代码](https://github.com/Yuchen-Fu/COMP9501/blob/main/src/train.py)
- [Egressy et al.，全文](https://arxiv.org/html/2306.11586v3)

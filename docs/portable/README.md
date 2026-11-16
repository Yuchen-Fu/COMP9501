# AML：显式关系新旧标记的受控实验

这个包可单独上传到大学 Linux GPU 服务器运行。包含完整代码、已准备的 HI-Small 图、冻结实验方案及自动分析程序；不需要从 GitHub 克隆旧项目，也不需要重新下载数据。这里没有新实验的结果，不能把预检或旧实验当成新证据。

研究问题是：**当 counts 和 ports 已足以推导一个交易对是否首次出现时，直接提供这个标记，是否仍能改善 AML 预测？**

| 组别 | 输入 | 新种子 | 作用 |
|---|---|---|---|
| A / `cp` | counts + ports + 空标记槽 | 5–14，共 10 个 | 主对照 |
| B / `cpn` | counts + ports + novelty | 5–14，共 10 个 | 检验显式添加的作用 |
| C / `cn` | counts + 空 port 槽 + novelty | 5–9，共 5 个 | 必跑，核对旧的替换优势 |

共 25 次训练，顺序执行，三组输入槽和参数数量相同。主要比较 B−A；C 的比较只使用共同的五个种子。novelty 指数据观察窗口内第一次出现的**有向交易对**，不等于银行客户之间历史上第一次建立关系。

## 最短运行步骤

1. 解压，进入 `AML_EXPLICIT_PAIR_STUDY`。建议使用 Linux x86_64、Python 3.11 或 3.12、1 张 NVIDIA GPU（建议至少 24 GB 显存）、32 GB 主内存及 20 GB 可用磁盘。实际显存需求由预检报告；单个预检批次不能保证所有邻域都能容纳。
2. 安装独立环境。HKU 登录信息显示已有 Conda，可先创建指定 Python：

```bash
conda create -n aml-port-study python=3.12 -y
conda activate aml-port-study
```

然后在解压目录安装：

```bash
PYTHON=python3.12 bash scripts/representation/install.sh cuda
```

也可指定 `PYTHON=python3.11`。CUDA 12.6 的 PyTorch wheel 自带运行库，但需要兼容的 NVIDIA 驱动（建议 560 或更新）。只在授权的计算节点或 GPU 调度任务中开始训练。

3. HKU 已确认使用 Slurm。模板按登录信息申请一张 RTX 4090、4 CPU、32 GB 内存和 24 小时，使用默认分区。按需补充学校要求的 partition/account，然后在解压目录提交：

```bash
sbatch scripts/representation/submit.slurm
squeue -u "$USER"
```

如果是可以直接使用的 GPU 计算机，可在 `tmux` 会话中运行：

```bash
tmux new -s aml-study
.venv/bin/python -I scripts/representation/run_batch.py --device cuda
```

按 `Ctrl-b`，再按 `d` 脱离会话；恢复查看用 `tmux attach -t aml-study`。**Slurm 或 tmux 可以让任务不依赖 SSH 窗口持续打开，但不能防止服务器重启、调度时限或作业被终止。** 程序每个完整 epoch 保存断点；同一命令重跑会恢复，最多重做中断时的那个 epoch。不要同时启动第二份任务，程序也会拒绝重复启动。

不知道学校的调度方式时，把 `RUN_PROMPT.txt` 交给执行助手或管理员；它只需适配机器和调度器，不应更改实验方案。模板不会自行申请资源或提交任务。

## 程序自动完成什么

1. 独立重算全图历史计数和 ports，核验数据 SHA-256、时间切分，并绘制逐日 novelty 比例和特征范围漂移。
2. 在选定设备运行三组小样本预检，再测试真实图上的一个训练批次和一个验证批次。CUDA 不可用、确定性算子不受支持或显存不足时明确停止，不会悄悄改用 CPU、缩小批次或减少种子。
3. 完成 25 次训练，至少 20、至多 50 epochs。验证 AP 连续 10 epochs 未较平台参考值累计提高 0.001，则在达到最低轮数后停止。按最高验证 AP 选 checkpoint；测试集不选择轮数或阈值。最优 checkpoint 可能早于第 20 轮，另行报告固定第 20 轮和最终轮结果。
4. 核对全部预测与标签，生成配对区间、学习曲线和报告。随后对 A 的冻结表示运行预先规定的线性 probe，并与原始输入 probe 和精确等式规则比较。
5. 生成 `AML_EXPLICIT_PAIR_RESULTS.zip`，把它传回来即可继续科研解释和更新展示材料。模型 checkpoint 留在服务器，不放入较小的回传包；请暂时保留它们。

详细方案见 `PROTOCOL.md`，机器读取的冻结配置在 `results/representation_followup/protocol.json`。`src/train.py` 仅保留供新程序导入固定模型定义和超参数；不要执行它的旧训练入口，本实验统一使用上面的 `run_batch.py`。

## 查看状态和恢复

每十分钟记录状态；每个任务开始和完成时也会记录。查看状态不改变训练：

```bash
cat results/representation_followup/batch_status.json
tail -n 15 results/representation_followup/logs/cp_s5.log
```

失败后查看状态文件给出的具体日志。解决资源或连接问题后，使用同一设备类型、软件版本、代码和配置重复原命令。结果会校验来源，拒绝混入改变了方案的运行。若确实需要修改实验代码或统计设计，应在新目录建立明确记录的修订批次，不能覆盖已有批次。

运行时间取决于 GPU、CPU 邻居采样和验证停止时间。先看服务器上的预检和首个完整 epoch 耗时，再估算；本包不承诺未经测量的 ETA。Slurm 模板的 24 小时只是请求上限，并非预计用时。你提供的 HKU 登录信息显示剩余 2,806 GPU 分钟（约 46.8 GPU 小时）。若达到时限，先检查剩余配额，再提交同一脚本恢复；不要同时提交两份。为了避免混合硬件，恢复时继续用同一型号 GPU。

只打印全部任务命令，不训练：

```bash
.venv/bin/python -I scripts/representation/run_batch.py --device cuda --dry-run
```

## 如何读结果

- `FOLLOWUP_REPORT.md`：B−A 的主要估计、五种 checkpoint 的敏感性分析、days 8–9 检查、停止情况、TP/FP 和统计功效假设。
- `probes/PROBE_REPORT.md`：新旧关系是否可从冻结的 25 维表示中线性解码。它不能证明 AML 决策实际使用了该信息。
- `DRIFT_REPORT.md`：时间和历史累积带来的分布变化。
- `figures/` 与 `probes/`：Python 直接输出的学术图表。

如果新比较的配对标准差与旧实验相近，10 个种子的 80% 功效对应约 **2.96 个 F1 百分点**；5 个种子约 **5.00 个点**。旧实验估计的是不同的替换比较，不能保证 B−A 也有这一功效。这个数不是业务最低收益标准。

正面结论必须来自新数据。B−A 不明确时，不能用 C 的正面结果代替，也不能宣称“二者相同”。即使结果支持显式标记，也只支持本协议、这个合成数据集上的作用；50 epochs 和验证平台都不等于证明收敛。该评估使用累计的离线图，不能直接解释为实时 AML 部署效果。

## 可追溯性

`PACKAGE_SHA256SUMS` 覆盖包内代码、配置和图数据，可在首次运行前用 `sha256sum -c PACKAGE_SHA256SUMS` 检查。准备好的图共有 5,078,345 笔交易、515,088 个账户。原始数据地址、版本和校验值在 `DATA_PROVENANCE.md`；`src/prepare.py` 保留原始数据处理代码。旧实验和新实验不可合并计算区间。

`VALIDATION.md` 说明打包前实际通过的检查。云环境没有 GPU，真正的 CUDA 训练预检将在学校机器执行。

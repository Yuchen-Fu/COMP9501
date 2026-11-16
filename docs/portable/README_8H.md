# 8 小时预算版：保留研究问题，减少种子并行运行

这是独立的新批次，不修改或合并原来的 25 组结果。原始数据、模型、特征、共享缩放、评价方法和主要比较均不变。

| 项目 | 本版设定 |
|---|---|
| 研究问题 | 保留 counts 和 ports 后，显式 novelty 是否改善 AML 预测？ |
| A / B / C | Counts+Ports / Counts+Ports+Novelty / Counts+Novelty |
| 种子 | 每组固定 15–19，共 15 次训练；C 必跑 |
| 训练 | 至少 20、最多 30 epochs，原验证 AP 平台停止规则不变 |
| 主要终点 | 验证 AP 最优 checkpoint 上的测试 F1，B−A 配对差异 |
| 交叉检查 | AP、固定第 20 轮、最终轮、days 8–9，以及冻结表示 probe |
| GPU | 同一节点 4 张相同型号 RTX 3090，每卡一个训练进程 |
| 资源 | 8 CPU、64 GB RAM；Slurm 时限 8 小时 |
| 时间保护 | 程序在 7 小时 45 分停止未完成工作，保留 checkpoint |
| 输出 | `results/representation_8h/`，不混入旧批次 |

**统计代价：** 主要比较由十对种子降为五对。按照旧替换比较的配对 SD，80% 功效对应约 5.00 个 F1 百分点；原十对设计约 2.96。新比较的真实 SD 未知，不能把无显著差异解释为等效。30 轮和验证平台也不构成收敛证明。

**时间估计：** 最多 15×30=450 个训练 epochs，四卡并行通常分四批。若每轮训练＋验证约 1/2/3 分钟，训练阶段约 2/4/6 小时；各次训练后的测试、预检和 probe 还需时间。这是吞吐量情景估算，不保证所有硬件都能完成。排队不计入八小时作业预算；若未完成全部 15 次，则不会给出完整实验结论。不要删掉失败种子、临时改轮数或只挑完成的运行分析。

## 已有原始数据包时

把 `AML_EXPLICIT_PAIR_8H_UPDATE.zip` 放到原包解压后的 `AML_EXPLICIT_PAIR_STUDY` 目录，执行：

```bash
unzip -o AML_EXPLICIT_PAIR_8H_UPDATE.zip
sha256sum -c UPDATE_8H_SHA256SUMS
scontrol show partition debug
sbatch scripts/representation/submit_8h.slurm
squeue -u "$USER"
```

如果 `.venv` 尚未安装，先按原 README 安装 CUDA 环境。**只提交 `submit_8h.slurm`，不要再同时提交原 25 组作业。** 若原作业已经启动，先记录其状态并独立保存，不把其运行混入本方案。协议已固定在 `results/representation_8h/protocol.json`。

模板依据你提供的 HKU 登录信息申请 `--gpus=rtx_3090:4`。确认 `debug` 的 `MaxTime` 至少 8 小时；若学校不允许此资源组合，请报告调度器错误，不自动退成一张卡并声称仍能按时完成。当前 2,806 GPU 分钟配额约等于 46.8 GPU 小时；四卡满八小时最多用 32 GPU 小时。实际配额以提交前的学校记录为准。

## 运行中与完成后

程序每十分钟写 `results/representation_8h/batch_status.json`，每个任务有自己的日志。前几个完整 epoch 的耗时会记录在日志中，应据此更新剩余时间估计。GPU 预检将在四张卡上分别运行；当前云环境只验证 CPU 与调度逻辑，没有实测四卡 CUDA。

交付前，独立 Python 3.12 环境中的小图测试已完成本版全部 15 次训练、统计审计、5 个 probe 和结果打包；另行测试了四进程调度、失败传播及时间保护。这些是程序验证，不是 HI-Small 新实验结果。

完整结束后回传 `AML_EXPLICIT_PAIR_8H_RESULTS.zip`。超时会保留每个完整 epoch 的 checkpoint，标为 incomplete；如果另行恢复，须披露累计计算已超过一次八小时预算，保持原种子、模型和停止规则，不能将它描述成八小时内完成。

原协议的科学边界继续适用：共享缩放保留 count–port 等式；novelty 本来就是输入中的线性可分事实；probe 只检验可解码性；数据是已检查过的合成 HI-Small；离线累计图不等于实时因果 AML 评估。不能预先承诺正面结论。

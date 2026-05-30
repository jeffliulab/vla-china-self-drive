# 第七课笔记 ⑦ QLoRA 微调 + 接回闭环：造出"你自己训练的 VLA"

> 对应 [课程大纲.md](../课程大纲.md) **第七课（净新 · Stage 之后）**：用第六课数据 QLoRA 微调 Qwen2.5-VL-3B，导出 adapter 上传 HF，接回 `vla_agent`——得到三方 ablation 的第三个 agent。
> 承接 [第五课](5-VLA闭环与评测.md)（闭环接口）、[第六课](6-规模化数据与发布.md)（数据）。理论复用第一课 [§5.4](1-自动驾驶模型.md)（VLA 架构）、[§5.5(6)(7)](1-自动驾驶模型.md)（显存/路线）、[§5.7](1-自动驾驶模型.md)（BC/CIL）。
> 环境实测以 [CLAUDE.md](../../CLAUDE.md) 为准（5070 Ti 16GB；torch 现只在 `isaaclab`，`carla9` 无 torch）。

---

## 目录

- [0. 本课定位与产物](#0-本课定位与产物)
- [1. 心智模型①：为什么是 QLoRA，不是全量微调](#1-心智模型为什么是-qlora不是全量微调)
- [2. 心智模型②：训练在哪做（离线/服务器，CARLA 关掉）](#2-心智模型训练在哪做离线服务器carla-关掉)
- [3. 必须知道的原理](#3-必须知道的原理)
- [4. 实践：训练与接回](#4-实践训练与接回)
- [5. 验收 & 自测题](#5-验收--自测题)
- [6. 参考资料](#6-参考资料)

---

## 0. 本课定位与产物

| 项 | 内容 |
|---|---|
| **学完能干什么** | 用 QLoRA 在单张 16GB 卡上微调 Qwen2.5-VL-3B；约束输出到动作集；监控收敛与过拟合；导出 adapter 上传 HF；把权重接回闭环（第三个 agent） |
| **可运行产物** | **HF Model**（QLoRA adapter）+ 接回闭环的微调 agent |
| **一句话主线** | 把"租来的大脑"（zero-shot）换成"你自己训练的大脑"——这是让你能理直气壮说"训练过 VLA"的分水岭（第一课 [§5.5(8)](1-自动驾驶模型.md)） |
| **本质** | 高层离散动作上的**行为克隆 / 条件模仿 CIL**（第一课 [§5.7](1-自动驾驶模型.md)），不是端到端 |

---

## 1. 心智模型①：为什么是 QLoRA，不是全量微调

第一课 [§5.5(6)(7)](1-自动驾驶模型.md)：本机单张 16GB，CARLA 和推理/训练抢同一张卡。全量微调一个 3B 模型（权重+梯度+优化器状态 ≈ 数倍参数量的显存）在 16GB 上**放不下**。QLoRA 让它变可行：

```
全量微调：训练所有参数 → 显存 = 权重 + 梯度 + 优化器状态（Adam 再 ×2） → 3B 也吃十几~几十 GB
   ↓ QLoRA
QLoRA：①主干 4-bit 量化冻结(只读) ②只训练插入的低秩 adapter(LoRA) ③优化器状态只为 adapter
   → 3B 微调可压到 ~7–9GB，单张 16GB 可行
```

> 第一课 [§5.5(7)](1-自动驾驶模型.md) 的硬约束：**3B + 4bit + QLoRA 可行；OpenVLA-7B 全量微调（官方需 ~27GB 起）本机硬刚不可行**——要更大走服务器（PROJECT_PLAN §7）。

---

## 2. 心智模型②：训练在哪做（离线/服务器，CARLA 关掉）

第一课 [§5.5(6)](1-自动驾驶模型.md) 的三档：CARLA 渲染 + 本地训练**抢同一张卡**，同时跑基本不行。所以：

- **微调离线做**：训练时**关掉 CARLA**，把 16GB 全留给训练。
- 或**上服务器**（PROJECT_PLAN §7）跑更大/更快。
- **环境**：`carla9` 没 torch，torch 现只在 `isaaclab`（CLAUDE.md §3）。要么给一个独立训练环境装 `torch + transformers + peft + bitsandbytes + trl`，要么用 `isaaclab` 的 torch，要么服务器。**这是本课第一步要定的决策**（先验证后断言：实测剩余显存与依赖）。

---

## 3. 必须知道的原理

### 3.1 LoRA：冻结主干，只学低秩增量

直觉：微调其实只需要在原权重 $W$ 上加一个"小修正" $\Delta W$。LoRA 假设这个修正是**低秩**的：

$$
W' = W + \Delta W = W + B A,\qquad B\in\mathbb R^{d\times r},\ A\in\mathbb R^{r\times k},\ r\ll \min(d,k)
$$

- **冻结 $W$**（不训练），只训练 $A,B$（参数量从 $d\times k$ 降到 $(d+k)\times r$，通常少 1–2 个数量级）。
- $r$=秩（如 8/16/32），$\alpha$=缩放。推理时把 $BA$ 合并回 $W$ 或并行加。
- **好处**：可训练参数极少 → 优化器状态小 → 省显存；adapter 只有几十 MB，便于发布/切换。

### 3.2 量化 + QLoRA（Dettmers 2023）

QLoRA = **把冻结的主干量化到 4-bit** + 在其上挂 LoRA。三个关键技术：

- **NF4（NormalFloat4）**：为正态分布权重设计的 4-bit 数据类型，比普通 int4 更准。
- **双量化（double quantization）**：连量化用的常数也再量化一遍，进一步省显存。
- **paged optimizer**：用统一内存分页扛住显存尖峰（避免 OOM 崩溃）。

主干 4-bit 只读、前向时反量化计算；梯度只流到 bf16 的 LoRA adapter。**这就是 3B 能塞进 16GB 的原因。**

### 3.3 训练目标：SFT，对动作 token 算 loss

第一课 [§5.7](1-自动驾驶模型.md)：这是**高层动作上的行为克隆/CIL**。具体：

- 输入：图像 + 状态文本 + 中文指令 + 允许动作集（第六课 [§3.4](6-规模化数据与发布.md) 的对话格式）。
- 标签：assistant 那段的高层动作 JSON。
- **loss = 只对 assistant（动作）token 的交叉熵**，**mask 掉 prompt/图像 token**（不让模型去"预测输入"）。
- 图像经 ViT→connector 编码（第一课 [§5.4](1-自动驾驶模型.md)）；LoRA 通常挂在 LLM 主干（必要时也挂 connector）。

### 3.4 结构化/受限输出（本地模型的优势）

第五课 [§3.3](5-VLA闭环与评测.md) 靠 API 的结构化输出。本地微调模型可以更狠：

- **训练阶段**：标签统一成 `{"action": <enum>}`，模型学会稳定吐合法格式。
- **推理阶段**：可用**受限解码 / grammar**强制只生成允许动作集里的 token；仍保留校验+回退兜底。

### 3.5 监控：收敛、过拟合、动作准确率

- **train/val loss**：下降并在 val 上不反弹。
- **val 动作准确率**：预测动作 == 标签 的比例（比 loss 更直观）；注意类不平衡时看**各类别**准确率（别被 `KEEP_LANE` 占比骗了，第六课 [§3.2](6-规模化数据与发布.md)）。
- **过拟合**：数据集小（本项目自采，规模有限）→ 用 early stop、适度 LoRA 秩、val 监控；过拟合的模型闭环会很脆。

### 3.6 接回闭环（第三个 agent）

第一课 [§5.5(8)](1-自动驾驶模型.md) 强调三方要**公平对比**：

- 微调 agent **复用第五课的同一闭环接口**（`run_step(obs)→高层动作→控制器`），只把"调 API"换成"调本地微调模型"。
- 这样 rule / zero-shot / 微调 三方**在同一场景、同一控制器、同一指标**下比，差异才归因于"决策大脑"本身。

---

## 4. 实践：训练与接回

### 4.1 训练流程骨架（写代码前征得同意；先关 CARLA）

```
0. 定环境: 独立 torch 环境(transformers+peft+bitsandbytes+trl) 或 isaaclab 或服务器；关掉 CARLA
1. load:   4-bit 量化加载 Qwen2.5-VL-3B (bitsandbytes NF4 + double quant)
2. lora:   peft 给 LLM(必要时 connector) 挂 LoRA(r, alpha, dropout)
3. data:   第六课 HF Dataset → 对话样本；mask 掉非 assistant token
4. train:  trl SFTTrainer / 自写循环；paged optimizer；监控 train/val loss + val 动作准确率
5. eval:   离线 val 动作准确率 + 各类别准确率
6. export: 保存 adapter；push_to_hub(写 model card + 版本 + 基座/数据版本)
```

### 4.2 接回闭环骨架

```
class FinetunedVLAAgent(同第五课接口):
    def __init__(self): 4-bit 加载基座 + 合并/加载 LoRA adapter
    def run_step(self, obs):
        每 QUERY_EVERY tick: prompt=build_prompt(obs)(与第五课/第六课同格式)
                             action = 本地模型.generate(prompt, 受限解码到动作集)
        return controller.map(action, obs)   # 与 rule/zero-shot 同一控制器
```

### 4.3 常见坑

- **CARLA 没关就训练** → 抢显存 OOM（第一课 [§5.5(6)](1-自动驾驶模型.md)）。
- **在 `carla9` 里训练** → 没 torch；要换训练环境（CLAUDE.md §3）。
- **硬刚 7B 全量/微调** → 16GB 放不下（第一课 [§5.5(7)](1-自动驾驶模型.md)）。
- **没 mask prompt token** → 模型去学"复述输入"，浪费且学歪。
- **训练输入格式 ≠ 部署 prompt** → 协变量偏移（第六课 [§3.4](6-规模化数据与发布.md)、第一课 [§4.4](1-自动驾驶模型.md)）。
- **只看总准确率** → 被多数类 `KEEP_LANE` 骗；看各类别 + 闭环表现。
- **微调 agent 换了控制器/场景** → 三方对比不公平（第一课 [§5.5(8)](1-自动驾驶模型.md)）。
- **过拟合小数据** → 离线准确率高、闭环很脆；early stop + 多 seed 闭环验。

---

## 5. 验收 & 自测题

**操作验收**
- [ ] 训练在 16GB 上跑起来（CARLA 关闭），train/val loss 收敛、无明显过拟合。
- [ ] val 动作准确率合理，且各类别（尤其 STOP/SLOW_DOWN）不塌方。
- [ ] adapter 导出并上传 HF（含 model card：基座、数据版本、动作集）。
- [ ] 微调 agent 用**第五课同一闭环接口**在鬼探头场景跑通；权重可从 HF 加载复现。

**概念自测（能用自己话答上即过关）**
1. QLoRA 为什么能在 16GB 上微调 3B？NF4 / 双量化 / paged optimizer 各解决什么？
2. LoRA 的低秩假设是什么？为什么省显存、adapter 还小？
3. 训练 loss 为什么只对 assistant（动作）token 算、要 mask 掉 prompt？
4. 为什么微调 agent 必须复用第五课的同一闭环接口和控制器？
5. 数据集小，怎么防过拟合？为什么"离线准确率高"不等于"闭环好"？

---

## 6. 参考资料

- QLoRA：Dettmers et al. 2023《QLoRA: Efficient Finetuning of Quantized LLMs》；LoRA：Hu et al. 2021。
- 工具：HuggingFace `peft` / `bitsandbytes` / `trl(SFTTrainer)`；LLaMA-Factory / unsloth（更省事的微调框架）。
- 模型：Qwen2.5-VL 技术报告与官方微调脚本/数据格式。
- 显存/路线、VLA 架构、BC/CIL 分别见第一课 [§5.5(6)(7)](1-自动驾驶模型.md)、[§5.4](1-自动驾驶模型.md)、[§5.7](1-自动驾驶模型.md)。

> 第三个 agent 造出来了。下一课把 **rule / zero-shot / 微调 三方**统一评测、写成论文交付，见 [第八课](8-三方评测与论文.md)。

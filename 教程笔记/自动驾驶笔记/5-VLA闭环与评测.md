# 第五课笔记 ⑤ VLA 闭环 + 评测交付：把大脑接进鬼探头

> 对应 [课程大纲.md](../课程大纲.md) **第五课（原 Stage 9+10）**：把「看图像+读中文指令→输出高层动作」的 VLA 接进闭环（先 zero-shot VLM，不训练也能跑）；统一指标评测、对比基线、产出结果表+演示视频。
> 承接 [第一课](1-自动驾驶模型.md)（理论总论，VLA 概念在 [§5.3](1-自动驾驶模型.md)/[§5.4](1-自动驾驶模型.md)/[§5.5](1-自动驾驶模型.md)）、[第四课](4-场景与数据.md)（场景+数据）。本课把 VLA 从概念**接进真实闭环**并量出结果。
> 环境实测以 [CLAUDE.md](../../CLAUDE.md) 为准（`carla9` / CARLA 0.9.16 / Low 画质）。

---

## 目录

- [0. 本课定位与产物](#0-本课定位与产物)
- [1. 心智模型①：VLA 在闭环里的位置（双系统）](#1-心智模型vla-在闭环里的位置双系统)
- [2. 心智模型②：zero-shot 先行——租一个 System 2](#2-心智模型zero-shot-先行租一个-system-2)
- [3. 必须知道的原理](#3-必须知道的原理)
- [4. 实践：CARLA Python client](#4-实践carla-python-client)
- [5. 验收 & 自测题](#5-验收--自测题)
- [6. 参考资料](#6-参考资料)

---

## 0. 本课定位与产物

| 项 | 内容 |
|---|---|
| **学完能干什么** | 设计 prompt（图+状态+中文指令+允许动作集）、用结构化输出逼模型选一个动作；把 1–2Hz 的 VLA 决策接到 20Hz 控制器；统一指标评测、做 rule vs zero-shot 对比表 + 演示视频 |
| **可运行产物** | `vla_agent.py`（闭环）+ `eval.py`（指标表）+ 演示视频（可在 0.10.0 高画质复现） |
| **一句话主线** | 给项目接上「会推理的大脑」——先 zero-shot 跑通全链路，量出它比规则 baseline 好/差在哪 |
| **交付边界** | 本课交付**三方 ablation 的前两方**（rule + zero-shot）；第三方"微调 VLA"在 [第七课](7-QLoRA微调.md)，完整论文在 [第八课](8-三方评测与论文.md)（第一课 [§5.5(8)](1-自动驾驶模型.md)） |

---

## 1. 心智模型①：VLA 在闭环里的位置（双系统）

第一课 [§5.3](1-自动驾驶模型.md) 立了分层架构，[§5.5](1-自动驾驶模型.md) 讲了双系统。本课把它接成真闭环：

```
 ┌──── System 2（慢，1–2Hz）────┐         ┌──── System 1（快，20Hz）────┐
 前视图+状态文本+中文指令+允许动作集 ─►VLA─► 高层动作 ─►第三课控制器─► VehicleControl ─► 车
 └──────────────────────────────┘         └─────────────────────────────┘
        ▲ 中间帧不查模型，控制器顶住（options，第一课 §5.3.1）
```

- VLA 只负责**慢的语义决策**（出一个高层离散动作），控制器负责**快的稳定执行**。
- 关键：**异步两层 + 同步时间红利**——同步模式下 server 会停下来等 VLA 算完（第一课 [§5.5(5)](1-自动驾驶模型.md)），所以 API 慢也不会撞车，只是墙上时钟变慢。

> 这就是为什么本项目能"先用 API 当大脑跑通闭环"，而不是权宜之计（第一课 [§5.5(3)(5)](1-自动驾驶模型.md)）。

## 2. 心智模型②：zero-shot 先行——租一个 System 2

第一课 [§5.5(3)](1-自动驾驶模型.md)：真·VLA 控制服务没有公开 API，但**通用多模态 VLM（GPT-4o / Claude / Qwen-VL）有成熟 API，正好胜任高层语义决策**。所以本课**先 zero-shot**：

- 不训练、直接 prompt 一个通用 VLM，把它当 System 2。
- 它是三方 ablation 的 **expert baseline / zero-shot agent**（第二个 agent）。
- **注意**：zero-shot agent 输出**不严格可复现**（服务端版本/采样/限流不由你控），评测要锁版本+`temperature=0`+落盘（第一课 [§5.5(8)](1-自动驾驶模型.md)）。

> zero-shot ≠ 微调。本课只 prompt，不训练；"你自己训练的 VLA"在第七课（第一课 [§5.5(8)](1-自动驾驶模型.md)、[§5.7](1-自动驾驶模型.md) 的 BC/CIL）。

---

## 3. 必须知道的原理

### 3.1 VLA / VLM 架构（深化第一课 §5.4）

典型结构：**视觉编码器（ViT）→ 投影层（connector）→ LLM 主干**。图像被切成 patch、编码成**图像 token**，与文本 token 拼接，LLM 自回归解码。动作可作为：**纯文本** / **结构化字段(JSON)** / **专用 action token**。本项目走"结构化字段"——让模型吐一个 JSON，里面是从允许动作集里选的一个动作。

### 3.2 prompt 设计 = 四件套 + 强约束

```
[System] 你是驾驶决策器，只能从「允许动作集」里选恰好一个动作，按 JSON 输出。
[Image]  前视 RGB（必要时多视角/depth 概览）
[Text]   自车状态：速度 8.3 m/s，所在车道…，目标：前方路口直行
[Text]   中文指令：注意公交车后可能有行人，确认安全再通过
[Text]   允许动作集：{KEEP_LANE, SLOW_DOWN, STOP, YIELD, FOLLOW, CHANGE_LEFT/RIGHT, ...}
→ 期望输出：{"action": "SLOW_DOWN", "reason": "..."}
```

要点：
- **守红线**（第一课 [§3.2](1-自动驾驶模型.md)）：被遮挡行人的真值**不进 prompt**；中文指令注入的是 belief 先验（"可能有人"），不是"看见了人"。
- **中文指令要真正影响决策**：在 prompt 里把指令与动作选择强绑定（否则模型无视指令，instruction_compliance 上不去）。

### 3.3 结构化/约束输出（逼模型守规矩）

第一课 [§5.4](1-自动驾驶模型.md) 提过。手段：
- **JSON schema / function calling**：声明输出必须是 `{"action": <enum>}`，`enum` 就是允许动作集。
- **受限解码（constrained decoding）**：本地模型可强制只生成合法 token。
- **校验 + 重试**：解析失败或动作不在集合内 → 重试/回退到安全动作（如 `KEEP_LANE`/`SLOW_DOWN`）。

### 3.4 推理频率与延迟（第一课 §5.5 的落地）

- 带图 VLM API 单次往返 **0.5–2s = 0.5–2Hz**（第一课 [§5.5(4)](1-自动驾驶模型.md)），物理上做不到 20Hz——所以**高层 1–2Hz 查、控制器 20Hz 顶**。
- 查询别太频繁：**又慢又烧钱**；用 options（一个高层动作管几十帧，第一课 [§5.3.1](1-自动驾驶模型.md)）天然降低查询频率。
- 应急刹车**不交给 VLA**（来不及），交给高频反射层（第一课 [§5.3.1](1-自动驾驶模型.md)）。

### 3.5 评测方法学（量化才算交付）

指标（PROJECT_PLAN §9，重点几个）：

| 指标 | 测什么 |
|---|---|
| `scenario_success` | 是否在鬼探头场景安全完成（最重要） |
| `collision_count` | 是否撞到行人/车 |
| `min_ttc` | 最危险时刻的接近程度（第四课 [§3.2](4-场景与数据.md)） |
| `hard_brake_count` | 急刹次数（平顺性/是否靠急刹兜底） |
| `instruction_compliance` | 是否遵守中文指令 |

- **多 seed 统计**：单 seed 没说服力，必须在固定 seed 集上跑、报均值/方差。
- **复现性边界**（第一课 [§5.5(8)](1-自动驾驶模型.md)）：rule/expert 完全可复现 ↔ API VLA 仅版本锁定下近似可复现；锁模型版本号、`temperature=0`、prompt+原始响应落盘（可进 `labels.jsonl`）。

---

## 4. 实践：CARLA Python client

### 4.1 vla_agent 骨架（写代码前征得同意）

```
class VLAAgent:
    def __init__(self): self.last_action = "KEEP_LANE"; self.t = 0
    def run_step(self, obs):                  # obs: 前视图+状态+指令
        self.t += 1
        if self.t % QUERY_EVERY == 0:         # 1–2Hz：每 ~10–20 个 tick 查一次
            prompt = build_prompt(obs)        # 四件套 + 允许动作集
            resp = call_vlm(prompt, temperature=0)   # 锁版本、落盘 prompt+resp
            self.last_action = parse_and_validate(resp)  # 不合法→重试/回退
        return controller.map(self.last_action, obs)     # 第三课的高层→VehicleControl
```

### 4.2 eval 骨架

```
for agent in [rule_baseline, zero_shot_vla]:        # 第七课再加 finetuned_vla
    for seed in SEED_SET:
        scenario.reset(seed); 跑到结束
        收集 success/collision/min_ttc/hard_brake/instruction_compliance
聚合成表（均值±方差）→ 输出 results.csv / markdown 表
```

### 4.3 常见坑

- **模型自由发挥、动作不在集合内** → 必须结构化输出 + 校验重试（§3.3）。
- **查询太频繁** → 延迟拖垮闭环、API 烧钱；用 options 降频。
- **中文指令没真正影响决策** → prompt 里没强绑定；要在 system/格式上逼模型用指令。
- **只看一个 seed** → 不可信；多 seed（第八课会强调）。
- **API 不锁版本/不落盘** → 结果不可复现、无法写进论文（第一课 [§5.5(8)](1-自动驾驶模型.md)）。
- **拿被遮挡行人真值喂 prompt** → 越红线，鬼探头评测作废（第一课 [§3.2](1-自动驾驶模型.md)）。

---

## 5. 验收 & 自测题

**操作验收**
- [ ] VLM 驱动的 ego 能跑完鬼探头场景并对窜出做出反应。
- [ ] 跑通「图像+中文指令 → 动作（结构化）→ 控制器 → VehicleControl」全链路。
- [ ] 一张「rule vs zero-shot VLA」多 seed 指标对比表 + 一段演示视频。
- [ ] prompt+原始响应有落盘、模型版本+`temperature=0` 已记录。

**概念自测（能用自己话答上即过关）**
1. 为什么 zero-shot VLM API 能当大脑、却不能做控制环？同步模式怎么化解它的延迟？
2. prompt 四件套是什么？怎么逼模型只从允许动作集里选？
3. zero-shot agent 为什么"不严格可复现"？评测时怎么把它逼到"近似可复现"？
4. 为什么应急刹车不交给 VLA？它交给谁？
5. 为什么评测必须多 seed？`instruction_compliance` 衡量什么、为何对本项目重要？

---

## 6. 参考资料

- 官方/范式：*On the Road with GPT-4V*；*DriveVLM*；LMDrive（CARLA 闭环+语言）；VLM-for-AD survey。
- 双系统/推理频率：Reasoning-VLA、Fast-in-Slow（第一课 [§5.5](1-自动驾驶模型.md)/[§8](1-自动驾驶模型.md) 参考）。
- 结构化输出：JSON schema / function calling / 受限解码（各家 SDK 文档）。
- 指标范式：Bench2Drive（闭环评测）；PROJECT_PLAN §9。
- VLA 架构、推理频率、复现性边界分别见第一课 [§5.4](1-自动驾驶模型.md)、[§5.5](1-自动驾驶模型.md)、[§5.5(8)](1-自动驾驶模型.md)。

> 至此原 5 节课闭环：能连→能看→会动→搭舞台采数据→接 zero-shot 大脑评测。**但三方 ablation 还差"微调 VLA"那一方**——从 [第六课](6-规模化数据与发布.md) 起进入"规模化数据→微调→三方评测+论文"。

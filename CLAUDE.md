# CLAUDE.md

本文件供 Claude / AI agent 在本仓库工作时参考，记录**已实测验证的本机环境**、项目约定和版本追踪规则。
区别于 [PROJECT_PLAN.md](教程笔记/PROJECT_PLAN.md)（规划/目标）——本文件只写**当前真实状态**与**协作规则**。

- **项目版本**：见文末「版本追踪」。当前 **v0.1（规划期）**。
- **仓库**：https://github.com/jeffliulab/vla-china-self-drive
- **本机工作目录**：`/home/jeff/Projects/vla-china-self-drive`

---

## 1. Agent 工作规则

> **【硬规则 · 最高优先级】未经用户明确许可，任何时候都不得编写或修改任何代码（`.py`/`.sh`/源码/配置脚本）。**
> 用户点头之前，只做讲解、给方案、写文档与学习笔记（`.md`）；需要写/改代码时，先说明要写什么并征得同意，再动手。运行只读检查命令（查状态、看文件）不受此限，但**生成代码文件必须先获许可**。

1. **先验证，后断言**。静态资产/文件存在 ≠ 功能可用（例：blueprint 能否 spawn 必须运行时确认）。涉及环境的结论以实测为准，不照抄文档。
2. **本文件与现实同步**。当环境、依赖、可用资产发生变化时，更新本文件对应小节，并在文末版本追踪登记。
3. **PROJECT_PLAN.md 是「想做什么」，CLAUDE.md 是「现在是什么」**。讨论计划改 PLAN；环境/状态变更改本文件。
4. **大文件不入 git**：CARLA 包、地图、数据集、视频、模型权重一律走 [.gitignore](.gitignore)，不提交。
5. **不要同时启动两个 CARLA server**：0.9.16 与 0.10.0 默认都占 `localhost:2000`。
6. **提交/推送需用户明确许可**；改动先在分支上做。
7. 文档默认用中文，与现有 PLAN / 会议纪要保持一致。

---

## 2. 本机环境（实测于 2026-05-29）

| 项 | 值 |
|---|---|
| OS | Ubuntu 24.04.4 LTS (noble) |
| Kernel / Arch | 6.17.0-29-generic / x86_64 |
| Hostname | jeff-workstation |
| GPU | NVIDIA GeForce RTX 5070 Ti，16 GB 显存 |
| 驱动 / CUDA | Driver 580.159.03 / CUDA 13.0（驱动层） |
| 磁盘 | `/` (nvme0n1p2) 共 1.8T，可用 ~1.5T |
| conda | miniforge3 @ `/home/jeff/miniforge3` |

> 显存仅 16 GB：跑大 VLA/VLM 推理需注意，必要时用量化或走 API。

---

## 3. Conda 环境（实测）

| 环境 | Python | 用途 | 关键包（实测） |
|---|---|---|---|
| `carla9` | 3.10.20 | **主线**：CARLA 0.9.16 实验/数据采集 | carla 0.9.16 ✓import OK, numpy 2.2.6, opencv-python 4.13, pygame 2.6.1, matplotlib 3.10.9, tqdm 4.67.3 |
| `carla10` | 3.10.20 | CARLA 0.10.0 高画质展示 demo | carla 0.10.0 ✓import OK（编译 .so） |
| `isaaclab` | — | Isaac Sim 5.1 / 训练备用 | **torch 2.7.0+cu128（CUDA 可用 ✓）**, Isaac Sim 5.1.0, isaaclab 0.54.3 |
| `base` | — | 默认，勿用于实验 | — |

实测注意：
- `carla9` **未装 pyyaml / torch**——若脚本需读 YAML 配置或做本地推理，需先 `pip install`。
- 需要 GPU 训练/推理时，torch 环境目前只有 `isaaclab`（不在 carla9 内）。后续 VLA 阶段要决定：是给 carla9 装 torch，还是分离推理进程。

验证命令：
```bash
conda run -n carla9  python -c "import carla; print(carla.__file__)"
conda run -n carla10 python -c "import carla; print(carla.__file__)"
```

---

## 4. CARLA 安装（实测）

| 版本 | 路径 | 大小 | 引擎 | 启动脚本 |
|---|---|---|---|---|
| 0.9.16 | `/home/jeff/CARLA/carla-0.9.16` | 44 G | UE4 | `CarlaUE4.sh` |
| 0.10.0 | `/home/jeff/CARLA/carla-0.10.0` | 20 G | UE5 | `CarlaUnreal.sh` |

启动（低画质，用于采集）：
```bash
# 主线
conda activate carla9  && cd /home/jeff/CARLA/carla-0.9.16  && ./CarlaUE4.sh   -quality-level=Low -nosound
# 展示
conda activate carla10 && cd /home/jeff/CARLA/carla-0.10.0 && ./CarlaUnreal.sh -quality-level=Low -nosound
```

**0.9.16 可用地图（实测，AdditionalMaps 已导入）**：
`Town01 Town02 Town03 Town04 Town05 Town06 Town07 Town10HD Town11 Town12 Town13 Town15`
（比 PLAN 文档列的更多——Town12/13/15 为大尺寸地图）。第一阶段建议 `Town05`，展示用 `Town10HD`。

**现有零散脚本**（CARLA 目录内，非本仓库）：
- `carla-0.9.16/my_scripts/list_bikes.py`
- `carla-0.10.0/my_scripts/{list_bikes.py, list_all_vehicles.py}`

---

## 5. 待验证 / 已知风险

- [ ] **二轮车 blueprint 能否实际 spawn**（项目成立的前提）— 需 server 运行时跑 inventory 确认。
- [ ] carla9 + numpy 2.x 在数据采集/序列化时是否有兼容问题（import 已通过，深用待测）。
- [ ] 服务器 headless 运行（`-RenderOffScreen` + Vulkan + NVIDIA runtime）尚未验证。
- [ ] VLA 推理的 GPU 路径未定（carla9 无 torch / 16GB 显存约束）。

---

## 6. 版本追踪

版本号语义（项目阶段，非软件 semver）：
- **0.x**：框架搭建期。`0.1` 规划，`0.2` 工程骨架+健康检查，`0.3` 场景，`0.4` baseline，`0.5` VLA 接入…
- **1.0**：首个可复现、能闭环、有评测结果的完整实验平台。

更新规则：每次实质性进展（环境变更、阶段完成、关键决策）→ 在下表追加一行，并同步更新上文受影响小节。

| 版本 | 日期 | 状态 | 说明 |
|---|---|---|---|
| 0.1 | 2026-05-29 | 规划期 | 初始化 CLAUDE.md，实测记录本机环境（OS/GPU/conda/CARLA/地图）。仓库仅含 PROJECT_PLAN 与会议纪要，无代码。本次对话主题：讨论计划。 |

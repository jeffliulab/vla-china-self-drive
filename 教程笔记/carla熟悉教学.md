# CARLA 熟悉教学：从零到「鬼探头」具身智能自动驾驶项目

> 面向**已懂深度学习 / DNN、但没碰过具身智能、自动驾驶、CARLA**的学习者。
> **最终目标**：独立完成一个**完整的「鬼探头」VLA 自动驾驶项目**——场景里行人从遮挡物后突然窜出，智能体看图像 + 中文指令做出高层决策，闭环控制车辆安全应对，并有评测与演示。
>
> 本文是**教学大纲（规划性质）**，与 [PROJECT_PLAN.md](PROJECT_PLAN.md) / [中国路况.md](中国路况.md) 同级；环境实测以 [CLAUDE.md](../CLAUDE.md) 为准（用 `carla9` 环境、CARLA 0.9.16、Low 画质）。

---

## 0. 这份大纲怎么用（教学法说明）

调研了官方教程、社区博客、sentdex 视频系列、ScenarioRunner、模仿学习与 VLA 论文后，本大纲采用四条原则：

1. **倒推设计（backward design）**：终点是「鬼探头」项目，每个 stage 都是通往它的一块拼图，不教用不上的东西。
2. **项目式 + 每阶段一个可运行产物**：每个 stage 结束你都有一个**能跑、能看到结果**的脚本，而不是只读文档。
3. **先跑后写**：每个新主题，**先跑通官方 `PythonAPI/examples/` 里的现成脚本**，再自己改写。这是所有入门教程的共识，能极大降低挫败感。
4. **统一验收**：每个 stage 给出「**验收标准**」（做到什么算过关）和「**常见坑**」，避免似懂非懂往下走。

> 你已有的 DNN/DL 基础**直接复用**，本大纲**不讲深度学习原理**；重点补的是：① 自动驾驶的软件栈心智模型，② CARLA 这个「服务器-客户端 + 游戏引擎」的运行机制和它特有的坑，③ 把 VLA 接进闭环。

**建议节奏**：Stage 0–5 是「熟悉 CARLA」（约 1–2 周），Stage 6–10 是「搭出鬼探头项目」（约 2–4 周）。所有自己写的脚本统一放进仓库 `scripts/` 和 `src/`，纳入 git。

**与 PROJECT_PLAN 的对应**：Stage 1–5 ≈ PLAN 阶段 1（仿真与资产验证）；Stage 6–7 ≈ PLAN 阶段 2（场景）；Stage 8 ≈ PLAN 阶段 3（baseline/数据）；Stage 9 ≈ PLAN 阶段 4（VLA）；Stage 10 ≈ PLAN 阶段 5（评测展示）。

---

## Stage 0 — 心智模型：自动驾驶栈 + CARLA 是什么（少量代码）

**教学目标**：在写任何代码前，建立两张「地图」——自动驾驶软件栈，和 CARLA 的运行机制。

**核心概念**
- **自动驾驶软件栈**：`感知(Perception) → 预测(Prediction) → 规划(Planning) → 控制(Control)`。本项目里 VLA 承担「感知+预测+高层规划」，传统控制器承担「低层控制」。
- **具身智能 vs 你熟悉的 DNN**：不再是「数据集→预测→算 loss」一次性前向，而是**智能体在环境里闭环**：观测→决策→动作→环境改变→新观测……（你要习惯「闭环 / closed-loop」这个词）。
- **CARLA = 服务器-客户端 + UE4 游戏引擎**：
  - **server**（仿真器本体）装着虚拟世界（路、车、人、物理、光照）；
  - **client**（你的 Python 脚本）连 `localhost:2000`，spawn 物体、挂传感器、推进时间。
  - **传感器拍的是引擎渲染出来的虚拟世界**，没有真实相机。
- **「鬼探头」问题**：行人/电动车被遮挡物（公交、停车、货车）挡住，**在极短 TTC 内突然出现**。难点是「**看不见也要会提前减速**」——遮挡感知 + 预防性决策。

**动手任务**：画出（手画即可）①AD 软件栈框图 ②CARLA server-client + 传感器数据流 ③鬼探头场景俯视示意（自车、遮挡物、藏在后面的行人、触发点）。

**验收标准**：能用自己的话讲清「为什么鬼探头难」「VLA 在栈里负责哪一段」「传感器数据从哪来」。

**参考**：CARLA「First steps」「Foundations」官方文档；UofT《Self-Driving Cars》Course 1（软件栈概览）。

---

## Stage 1 — 把 CARLA 跑起来 + Python 连上去

**教学目标**：启动 server，用 client 连上，跑通官方示例，建立「我能控制这个世界」的体感。

**核心概念**：`carla.Client` / `client.set_timeout` / `client.get_world()` / `world.get_map()` / **spectator**（观察相机）/ `client.load_world('Town05')`。

**动手任务**
1. 按 CLAUDE.md 启动：`conda activate carla9 && cd ~/CARLA/carla-0.9.16 && ./CarlaUE4.sh -quality-level=Low -nosound`。
2. 新终端连接，打印当前地图名、可用地图列表、切到 `Town05`。
3. **先跑官方示例**：`PythonAPI/examples/` 下的 `manual_control.py`（键盘开车）、`generate_traffic.py`（生成车流）。
4. 用 spectator 把视角移到地图某处。

**验收标准**：能手动开车在城里转一圈；能在脚本里切换地图并打印信息。

**常见坑**：client/server 版本必须一致（都 0.9.16）；`set_timeout` 太短会连不上；第一次加载大地图慢。

**参考**：官方 *Python API tutorial* / *First steps*；sentdex《Programming Self-Driving Cars with Carla》；WuhanStudio CARLA Basic 博客。

---

## Stage 2 — Actor 与 Blueprint：spawn 自车与 NPC（含二轮车验证）

**教学目标**：理解 CARLA 一切皆 **actor**，掌握 blueprint→spawn→destroy 全流程。

**核心概念**：`world.get_blueprint_library()` / `bp.filter('vehicle.*')` / `world.get_map().get_spawn_points()` / `world.try_spawn_actor()` / `actor.set_autopilot(True)` / **`actor.destroy()`（不销毁会残留！）**。

**动手任务**
1. 列出全部 vehicle blueprint；spawn 一辆 ego 到某 spawn point。
2. spawn 几辆 NPC 车，开 autopilot。
3. **验证项目前提**：跑 `my_scripts/list_bikes.py`，确认**自行车/摩托车/电动车 proxy 能否真正 spawn**（对应 CLAUDE.md 第 5 节风险）。
4. 写一个统一的 `cleanup()`，结束时销毁所有自己 spawn 的 actor。

**验收标准**：能稳定 spawn ego + N 辆 NPC 并干净销毁；产出一份「可 spawn actor 清单」（对接 PLAN 的 `asset_inventory.py`）。

**常见坑**：spawn point 被占→`try_spawn_actor` 返回 None；脚本崩了 actor 残留导致下次 spawn 失败（重启 server 或先清场）。

**参考**：官方 *Actors and blueprints (core_actors)*；*tutorial.py* 示例。

---

## Stage 3 — 同步模式与世界时钟（可复现的关键）

**教学目标**：理解异步/同步模式，学会用固定时间步驱动仿真——**这是数据可复现和传感器对齐的命门**。

**核心概念**：异步（server 不等 client）vs **同步**（server 等 `world.tick()`）；`settings.synchronous_mode=True` + `settings.fixed_delta_seconds=0.05`（=20FPS）；TrafficManager 也要设同步；主循环 `while: world.tick()`。

**动手任务**：把 Stage 2 脚本改成同步模式，写一个「tick N 步、每步打印帧号和 ego 位置」的确定性循环；对比异步模式下的行为差异。

**验收标准**：能解释「为什么采集数据必须同步 + 固定步长」；同一 seed 下两次运行轨迹一致。

**常见坑**：开了同步却忘了调 `world.tick()`→整个卡死；传感器回调与 tick 不同步导致图像帧错位。

**参考**：官方 *Synchrony and time-step*；`examples/synchronous_mode.py`；arijitray headless 教程。

---

## Stage 4 — 传感器：相机数据进 numpy 并可视化

**教学目标**：给车挂 RGB（+depth+semantic）相机，把数据取成 numpy，实时显示并存盘。这是 VLA 的「眼睛」。

**核心概念**：`sensor.camera.rgb/depth/semantic_segmentation` blueprint；用 `carla.Transform` 设挂载位置；`camera.listen(callback)`；图像是 **BGRA** 字节流→reshape→numpy；**depth/semantic 的编码**（depth 三通道→线性深度公式；semantic 只取标签通道）；用 pygame/opencv 显示。

**动手任务**
1. 在 ego 车头挂一个前视 RGB 相机，回调里转 numpy，用 pygame 开窗实时显示。
2. 同时挂 depth、semantic，理解三者差异（语义/深度与画质无关）。
3. 同步模式下，每个 tick 把前视图存成 `frames/rgb_front/000123.png`。

**验收标准**：一个实时前视窗口 + 能按帧把图像存盘，且与 tick 对齐。

**常见坑**：BGRA vs RGB 通道顺序搞反（图发蓝）；回调里做重活拖慢仿真；相机分辨率开太大吃显存（VLA 输入边长建议 ≤896）。

**参考**：官方 *Retrieve sensor data (tuto_G_retrieve_data)* / *Sensors reference* / *Pygame for vehicle control*；wambitz「Capturing Images」；enginBozkurt 数据采集 repo。

---

## Stage 5 — 行人与 AI 控制器（鬼探头的「人」）

**教学目标**：spawn 行人，既会用 AI 控制器让其自然行走，也会**用脚本精确控制行人突然横穿**——后者是鬼探头的核心。

**核心概念**：`walker.pedestrian.*` blueprint；`controller.ai.walker`（无实体、无物理）→ `start()` / `go_to_location()` / `set_max_speed()`；以及**手动控制** `carla.WalkerControl(direction, speed)`（脚本化「窜出」用这个最可控）。

**动手任务**
1. 用 AI 控制器 spawn 一个行人，让他走到随机点。
2. 写一个函数：**在被调用的瞬间，让指定行人以固定速度朝马路对面直线冲出**（为 Stage 7 触发做准备）。

**验收标准**：行人能自然行走；也能在你「下令」的那一刻精确横穿。

**常见坑**：忘了同时 spawn controller→行人站着不动；AI 行人会避让，做「鬼探头」要用手动 WalkerControl 才够突然。

**参考**：官方 *core_actors（pedestrians 部分）* / *Python API tutorial*；行人 bones 教程。

---

## Stage 6 — 控制桥接 + 规则 baseline（先有个会刹车的车）

**教学目标**：把「高层动作」翻译成 `carla.VehicleControl`，并做出一个**会沿路行驶、遇障急刹**的规则策略——它既是对照基线，也是后面采数据的 expert。

**核心概念**：`carla.VehicleControl(throttle, steer, brake)`；**纵向控制**（PID 控速）+**横向控制**（PID/纯追踪沿 waypoint）；可直接复用官方 `agents/navigation` 里的 `BasicAgent` / `VehiclePIDController` / `LocalPlanner`；高层动作集 → 控制映射（`KEEP_LANE / SLOW_DOWN / STOP / BRAKE`）。

**动手任务**
1. 用 `BasicAgent` 让 ego 从 A 点开到 B 点（沿 waypoint）。
2. 写一个最简规则策略：正常巡航，**当前方一定距离内出现行人/障碍→紧急制动**（用 actor 距离或语义/深度判断）。

**验收标准**：ego 能自动跑完一条路线；在前方有人时能刹停。

**常见坑**：PID 参数不当→画龙/震荡；steer 范围 [-1,1]、throttle/brake 不要同时给满。

**参考**：LearnOpenCV *PID Controller*；官方 `controller.py` / *CARLA Agents (adv_agents)*；Medium「Longitudinal & Lateral Control」。

---

## Stage 7 — 搭「鬼探头」场景（项目主场景）

**教学目标**：组装出**可复现、可配置、可判定成败**的鬼探头场景——这是整个项目的舞台。

**核心概念**：场景三要素 = **遮挡物**（路边停的公交/货车）+ **藏在后面的行人** + **触发条件**（ego 进入触发距离时令行人窜出）；固定 `seed` 可复现；`reset()` 复位；成败判据（碰撞 / 安全停住 / `min_TTC` 阈值）。可手写触发逻辑，进阶用 **ScenarioRunner**（`BasicScenario` + py_trees 行为树 + 评测 criteria）或 **Scenic** 描述。

**动手任务**
1. 选一段直路（Town05），在路边停一辆公交当遮挡，行人藏其后。
2. 触发：ego 距遮挡物 < D 米时，调用 Stage 5 的「窜出」函数。
3. 实现 `reset(seed)` 和 `is_success()/is_collision()`，把场景参数（D、行人速度、遮挡车型）做成可配置（YAML）。

**验收标准**：同一 seed 下场景**完全复现**；规则 baseline 在此场景有时成功(刹停)、有时失败(撞上)，说明难度真实存在。

**常见坑**：触发距离/行人速度没调好→要么必撞要么没威胁；遮挡没挡住相机视线→失去「鬼探头」意义（先用 spectator/语义图确认确实被遮挡）。

**参考**：CARLA *ScenarioRunner: creating_new_scenario*；Rocketloop *Scenic* 教程；遮挡行人研究（occlusion-aware risk，理解为何危险/如何设计指标）。

---

## Stage 8 — Episode 录制 + 小数据集

**教学目标**：把一次场景运行**完整录下来**（图像+状态+动作标签+元信息），用规则 baseline 批量产出小数据集——这就是后续微调的 SFT 数据。

**核心概念**：PLAN 第 8 节的数据结构（`frames/`、`states.parquet`、`actors.parquet`、`labels.jsonl`、`meta.json`）；同步模式下逐帧对齐落盘；把连续控制反推成高层动作标签（行为克隆思路）。

**动手任务**
1. 写 `record_episode.py`：跑一遍鬼探头，按帧存「前视图 + ego 状态 + 周围 actor + 当前高层动作标签 + meta」。
2. 用规则 baseline 在多个 seed 上批量跑，攒下 N 条 episode。

**验收标准**：磁盘上有结构规整、可复看的 N 条 episode；能加载任意一条检查图文是否对齐。

**常见坑**：异步下图像与状态错帧（务必 Stage 3 同步）；数据落 git（应走 .gitignore，存 `data/`）。

**参考**：官方 *data-collector* repo；COiLTRAiNE；行为克隆论文（Codevilla《Limitations of BC》了解陷阱）。

---

## Stage 9 — VLA Agent（zero-shot 先跑通闭环）

**教学目标**：把「看图像 + 读中文指令 → 输出高层动作」的 VLA 接进闭环，先用 **zero-shot VLM（API）**，不训练也能跑。

**核心概念**：prompt 设计 = 前视图 + 自车状态(文本) + 中文指令 + **允许动作集**，让模型**从给定选项里选一个动作**（结构化输出）；高层动作 → Stage 6 控制器 → `VehicleControl`；**延迟处理**：高层 1–2Hz 查模型，中间帧由控制器顶住（VLM 闭环延迟约 1–1.5s，这是已知特性）。

**动手任务**
1. 写 `vla_agent.py`：每隔若干 tick 把前视图+状态+中文指令(如「注意公交车后可能有行人，确认安全再通过」)发给 VLM，解析出动作。
2. 在鬼探头场景闭环运行，和规则 baseline 对比表现。

**验收标准**：VLM 驱动的 ego 能跑完场景并对鬼探头做出反应；能跑通「图像+中文指令→动作→控制」全链路。

**常见坑**：模型自由发挥不在动作集里→必须强约束输出格式/重试；查询太频繁→延迟拖垮闭环且烧钱；中文指令没真正影响决策→要在 prompt 里强绑定。

**参考**：*On the Road with GPT-4V*；*DriveVLM*；VLM-for-AD survey；LMDrive（CARLA 闭环 + 语言指令，作为进阶对标）。

---

## Stage 10 — 评测、对比与展示（毕业项目 = 完整鬼探头项目）

**教学目标**：用统一指标评测，对比基线，产出结果表 + 演示视频——交付一个**完整的鬼探头具身智能项目**。

**核心概念**：指标（`scenario_success`、`collision_count`、`min_ttc`、`hard_brake_count`、`instruction_compliance`）；多 seed 统计；rule baseline vs zero-shot VLA 对比；（进阶）用 Stage 8 数据 **QLoRA 微调一个小 VLM(如 Qwen2.5-VL-3B)**，再加一列对比。

**动手任务**
1. 写 `eval.py`：在固定 seed 集上跑各 agent，汇总指标成表。
2. 录一段成功避让鬼探头的 episode 视频（可在 0.10.0 高画质复现展示）。
3. （可选）QLoRA 微调小模型，对比 zero-shot。

**验收标准**：一张「rule vs zero-shot VLA (vs 微调 VLA)」的指标对比表 + 一段演示视频。**做到这步，鬼探头项目即闭环完成。**

**常见坑**：只看一个 seed（必须多 seed 才有说服力）；只报成功率不报安全指标（min_ttc/碰撞同样重要）。

**参考**：Bench2Drive（闭环评测指标范式）；PLAN 第 9 节指标。

---

## 参考资料汇总（调研来源，按用途分组）

**官方文档 / 教程**
- [First steps](https://carla.readthedocs.io/en/latest/tuto_first_steps/) ｜ [Python API tutorial](https://carla.readthedocs.io/en/0.9.7/python_api_tutorial/) ｜ [Actors & blueprints](https://carla.readthedocs.io/en/latest/core_actors/)
- [Synchrony and time-step](https://carla.readthedocs.io/en/latest/adv_synchrony_timestep/) ｜ [Retrieve sensor data](https://github.com/carla-simulator/carla/blob/master/Docs/tuto_G_retrieve_data.md) ｜ [Sensors reference](https://carla.readthedocs.io/en/latest/ref_sensors/)
- [Traffic Manager](https://carla.readthedocs.io/en/latest/tuto_G_traffic_manager/) ｜ [Pygame for vehicle control](https://carla.readthedocs.io/en/latest/tuto_G_pygame/) ｜ [CARLA Agents](https://carla.readthedocs.io/en/0.9.14/adv_agents/)
- [中文 CARLA 社区文档](https://bbs.carla.org.cn/)

**入门博客 / 视频系列**
- [sentdex: Programming Self-Driving Cars with Carla](https://www.classcentral.com/course/youtube-programming-autonomous-self-driving-cars-with-carla-and-python-153671) ｜ [Sentdex/Carla-RL](https://github.com/Sentdex/Carla-RL)
- [WuhanStudio: CARLA Basic](https://blog.wuhanstudio.uk/blog/carla-tutorial-basic/) / [Intermediate](https://blog.wuhanstudio.uk/blog/carla-tutorial-intermediate/) ｜ [sagnibak: How to use CARLA](https://sagnibak.github.io/blog/how-to-use-carla/)
- [wambitz: Capturing Images with CARLA](https://wambitz.github.io/tech-blog/carla/python/c++/simulation/autonomous-vehicles/2024/11/03/carla-capture-camera-images.html) ｜ [Towards AI: Build a Self-Driving Car in CARLA](https://towardsai.net/p/machine-learning/build-a-self-driving-car-in-carla-simulator-with-python-step-by-step)
- [arijitray: headless CARLA for data collection](https://arijitray.com/CARLA_tutorial/)

**控制 / 数据 / 模仿学习**
- [LearnOpenCV: PID Controller + CARLA](https://learnopencv.com/pid-controller-ros-2-carla/) ｜ [Medium: Longitudinal & Lateral Control](https://medium.com/@jaimin-k/longitudinal-lateral-control-for-autonomous-vehicles-carla-simulator-c045918816bd)
- [carla-simulator/data-collector](https://github.com/carla-simulator/data-collector) ｜ [COiLTRAiNE 条件模仿学习](https://github.com/felipecode/coiltraine) ｜ [Codevilla: Limitations of Behavior Cloning](https://openaccess.thecvf.com/content_ICCV_2019/papers/Codevilla_Exploring_the_Limitations_of_Behavior_Cloning_for_Autonomous_Driving_ICCV_2019_paper.pdf)

**场景设计**
- [ScenarioRunner: 创建新场景](https://scenario-runner.readthedocs.io/en/latest/creating_new_scenario/) ｜ [GitHub: scenario_runner](https://github.com/carla-simulator/scenario_runner) ｜ [Rocketloop: 用 Scenic 创建场景](https://rocketloop.de/en/blog/creating-scenarios-carla-scenic/)

**鬼探头 / 遮挡领域背景**
- [Occlusion-Aware Risk Assessment (CMU)](https://ppms.cit.cmu.edu/media/project_files/Pedestrian_Emergence_Estimation_and_Occlusion-Aware_Risk_Assessment_for_Urban_Autonomous_Driving.pdf) ｜ [Overcoming Blind Spots](https://arxiv.org/html/2402.01507v1) ｜ [Risk assessment under occluded vision](https://pmc.ncbi.nlm.nih.gov/articles/PMC8943059/)

**VLA / VLM 驾驶**
- [LMDrive (CVPR'24, CARLA 闭环+语言)](https://github.com/opendilab/LMDrive) ｜ [On the Road with GPT-4V](https://arxiv.org/pdf/2311.05332) ｜ [DriveVLM](https://arxiv.org/html/2402.12289v4) ｜ [VLM in AD: Survey](https://arxiv.org/html/2310.14414v2)

**系统课程（打底，选学）**
- [UofT: Self-Driving Cars Specialization (Coursera)](https://www.coursera.org/specializations/self-driving-cars) ｜ [Motion Planning for Self-Driving Cars](https://www.coursera.org/learn/motion-planning-self-driving-cars) ｜ [Self-Driving Cars with Duckietown (edX)](https://www.edx.org/learn/technology/eth-zurich-self-driving-cars-with-duckietown)

---

## 阶段-产物-能力 速查表

| Stage | 产物（可运行） | 你将掌握 |
|---|---|---|
| 0 | 三张框图 | AD 栈 / CARLA 机制 / 鬼探头难点 |
| 1 | 连接+手动开车脚本 | client-server、跑官方示例 |
| 2 | spawn/cleanup 脚本 + 资产清单 | actor/blueprint、二轮车验证 |
| 3 | 确定性同步循环 | 同步模式、可复现 |
| 4 | 实时相机窗口 + 存帧 | 传感器、numpy、可视化 |
| 5 | 行人窜出函数 | 行人 AI + 手动控制 |
| 6 | 会刹车的规则 baseline | VehicleControl、PID、高层→低层 |
| 7 | 可复现鬼探头场景 | 场景设计、触发、成败判据 |
| 8 | episode 录制 + 小数据集 | 数据格式、行为克隆数据 |
| 9 | zero-shot VLA 闭环 | prompt、图像+中文指令→动作 |
| 10 | 评测表 + 演示视频 | 指标、对比、（进阶）QLoRA 微调 |

# vla-china-self-drive 项目计划

本文档记录当前本机环境、CARLA 仿真资产、项目目标、云端服务器开发迁移方式和阶段计划。项目 GitHub 仓库已经建立：

https://github.com/jeffliulab/vla-china-self-drive

## 1. 项目定位

本项目目标是构建一个面向中国式混合交通场景的 CARLA 具身智能 / VLA 自动驾驶实验平台。

核心问题不是先训练一个完整端到端自动驾驶大模型，而是先做出一个可复现、可扩展、能闭环运行的仿真研究框架：

- 在 CARLA 中构建中国式混合交通场景。
- 使用汽车、自行车、摩托车、行人等 actor 生成高风险交互任务。
- 采集视觉、语义、深度、车辆状态、控制量、场景描述和动作标签。
- 让 VLA / VLM 模型根据图像、状态和中文指令输出高层驾驶动作。
- 使用传统控制器把高层动作转成 CARLA `VehicleControl`，完成闭环驾驶。
- 用统一指标评估 rule baseline、expert baseline 和 VLA agent。

## 2. 当前本机情况

### 2.1 工作目录

当前项目目录：

```bash
/home/jeff/Projects/vla-china-self-drive
```

当前目录内容很少，主要有：

```text
会议纪要
PROJECT_PLAN.md
```

注意：当前本机目录在 Codex 沙箱内能看到 `.git` 目录名，但 `git status` 返回：

```text
fatal: not a git repository (or any of the parent directories): .git
```

因此应把 GitHub 仓库视为远端权威仓库。后续建议在本机或服务器上重新执行：

```bash
git clone git@github.com:jeffliulab/vla-china-self-drive.git
```

或者：

```bash
git clone https://github.com/jeffliulab/vla-china-self-drive.git
```

然后把本地文档和代码提交进去。

### 2.2 操作系统

本机系统：

```text
Ubuntu 24.04.4 LTS
Kernel: 6.17.0-29-generic
Hostname: jeff-workstation
Architecture: x86_64
```

`nvidia-smi` ：

(carla9) jeff@jeff-workstation:~/CARLA/carla-0.9.16$ nvidia-smi
Thu May 28 22:35:16 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.159.03             Driver Version: 580.159.03     CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 5070 Ti     Off |   00000000:01:00.0  On |                  N/A |
|  0%   45C    P3             51W /  300W |    2602MiB /  16303MiB |     11%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A            2362      G   /usr/lib/xorg/Xorg                     1383MiB |
|    0   N/A  N/A            2562      G   /usr/bin/gnome-shell                    130MiB |
|    0   N/A  N/A            3604      G   ...rack-uuid=3190708988185955192        306MiB |
|    0   N/A  N/A            6057      G   /usr/share/code/code                    320MiB |
|    0   N/A  N/A            7681      G   .../7766/usr/lib/firefox/firefox         21MiB |
|    0   N/A  N/A           13845      G   ...f/Documents/Telegram/Telegram        303MiB |
|    0   N/A  N/A           24627      G   /usr/bin/nautilus                        16MiB |
+-----------------------------------------------------------------------------------------+
(carla9) jeff@jeff-workstation:~/CARLA/carla-0.9.16$ 


### 2.3 Conda 环境

当前 Conda 环境：

```text
base
carla10
carla9
isaaclab
```

重点环境：

```text
carla9  -> CARLA 0.9.16，Python 3.10.20
carla10 -> CARLA 0.10.0，Python 3.10.20
```

`carla9` 已确认可导入 CARLA Python API：

```bash
conda run -n carla9 python -c "import carla; print(carla.__file__)"
```

输出位置：

```text
/home/jeff/miniforge3/envs/carla9/lib/python3.10/site-packages/carla/__init__.py
```

## 3. CARLA 仿真情况

### 3.1 CARLA 根目录

CARLA 安装目录：

```bash
/home/jeff/CARLA
```

当前内容：

```text
/home/jeff/CARLA/carla-0.9.16
/home/jeff/CARLA/carla-0.10.0
/home/jeff/CARLA/Carla-0.10.0-Linux-Shipping.tar.gz
```

空间占用：

```text
carla-0.9.16                         44G
carla-0.10.0                         20G
Carla-0.10.0-Linux-Shipping.tar.gz   9.8G
```

CARLA 安装包和解压后的仿真器体积很大，不应该直接提交到 GitHub。GitHub 仓库只保存项目代码、配置、文档、场景定义和小型 metadata。大文件应放在本机、服务器磁盘、对象存储或 release artifact 中。

### 3.2 CARLA 0.9.16

路径：

```bash
/home/jeff/CARLA/carla-0.9.16
```

版本：

```text
0.9.16
```

关键文件：

```text
CarlaUE4.sh
VERSION
PythonAPI/
ImportAssets.sh
Import/AdditionalMaps_0.9.16.tar.gz
HDMaps/
Co-Simulation/
CarlaUE4/Content/Carla/Maps/
```

Python wheel 已存在：

```text
PythonAPI/carla/dist/carla-0.9.16-cp310-cp310-manylinux_2_31_x86_64.whl
PythonAPI/carla/dist/carla-0.9.16-cp311-cp311-manylinux_2_31_x86_64.whl
PythonAPI/carla/dist/carla-0.9.16-cp312-cp312-manylinux_2_31_x86_64.whl
```

`carla9` 使用 Python 3.10，因此对应 wheel 是：

```text
carla-0.9.16-cp310-cp310-manylinux_2_31_x86_64.whl
```

启动命令：

```bash
conda activate carla9
cd /home/jeff/CARLA/carla-0.9.16
./CarlaUE4.sh -quality-level=Low -nosound
```

低画质优先用于数据采集和长时间实验。需要展示视频时再提高画质。

### 3.3 CARLA 0.9.16 附加地图

已确认 `AdditionalMaps_0.9.16.tar.gz` 位于：

```text
/home/jeff/CARLA/carla-0.9.16/Import/AdditionalMaps_0.9.16.tar.gz
```

地图内容已经出现在：

```text
/home/jeff/CARLA/carla-0.9.16/CarlaUE4/Content/Carla/Maps
```

已看到的主地图包括：

```text
Town01
Town02
Town03
Town04
Town05
Town06
Town07
Town10HD
Town11
```

其中还包括对应的 `_Opt` 版本和 `Town11_Tile_*` 大地图瓦片。

推荐第一阶段地图：

- `Town05`：城市路口、交通流、变道、跟车、行人交互，适合初始实验。
- `Town10HD`：高精地图和更复杂道路结构，适合后续展示和复杂路线。
- `Town11`：附加地图，可作为扩展场景探索，但初期不建议作为唯一主地图。

### 3.4 二轮车和混合交通资产

已在 CARLA 0.9.16 静态资源目录中看到：

```text
CarlaUE4/Content/Carla/Static/Bicycle/
CarlaUE4/Content/Carla/Static/Bicycle/CrossBike
CarlaUE4/Content/Carla/Static/Bicycle/LeisureBike
CarlaUE4/Content/Carla/Static/Bicycle/Roadbike
CarlaUE4/Content/Carla/Static/Motorcycle/
CarlaUE4/Content/Carla/Static/Motorcycle/Yamaha
CarlaUE4/Content/Carla/Static/Motorcycle/kawasakiNinja
CarlaUE4/Content/Carla/Static/Motorcycle/Harley
```

已有脚本：

```text
/home/jeff/CARLA/carla-0.9.16/my_scripts/list_bikes.py
```

该脚本连接 `localhost:2000`，查询 blueprint library，并过滤：

```text
bike
bicycle
yamaha
harley
vespa
kawasaki
crossbike
diamondback
gazelle
```

注意：静态资源文件存在不等于 Python blueprint 一定可 spawn。下一步必须在 CARLA server 运行时执行 blueprint inventory，确认可 spawn 的 actor id。

### 3.5 CARLA 0.10.0

路径：

```bash
/home/jeff/CARLA/carla-0.10.0
```

关键文件：

```text
CarlaUnreal.sh
VERSION
PythonAPI/
```

已有脚本：

```text
/home/jeff/CARLA/carla-0.10.0/my_scripts/list_bikes.py
/home/jeff/CARLA/carla-0.10.0/my_scripts/list_all_vehicles.py
```

启动命令：

```bash
conda activate carla10
cd /home/jeff/CARLA/carla-0.10.0
./CarlaUnreal.sh -quality-level=Low -nosound
```

0.10.0 基于 UE5，适合高质量展示视频和视觉效果验证。但主实验建议优先使用 0.9.16，因为 0.9.x 生态成熟、资产稳定、资料和案例更多。

## 4. 为什么主线选择 CARLA 0.9.16

主线实验建议使用 CARLA 0.9.16：

- 已安装完整，`carla9` 已可导入 Python API。
- 已导入 AdditionalMaps。
- 已确认存在自行车、摩托车等混合交通相关资产。
- UE4 版生态成熟，Python 示例、社区代码、历史项目更多。
- 适合做数据采集、闭环控制、场景脚本和评测。

CARLA 0.10.0 的定位：

- 用于后期可视化、视频展示、UE5 画质 demo。
- 暂不作为第一阶段数据生成和闭环评测主线。

## 5. 目标系统设计

### 5.1 输入

第一阶段建议使用以下输入：

- 前视 RGB camera
- 可选：左右/后视 RGB camera
- depth camera
- semantic segmentation camera
- ego vehicle 状态：速度、加速度、yaw、当前位置、目标 waypoint
- 周围 actor metadata：车辆、行人、自行车、摩托车位置和速度
- 中文驾驶指令，例如：
  - “前方路口右转，注意右侧电动车。”
  - “保持车道，遇到行人先让行。”
  - “前方慢车，确认安全后左侧绕行。”

### 5.2 输出

VLA agent 第一阶段不要直接输出连续控制量，而是输出高层动作：

```text
KEEP_LANE
SLOW_DOWN
STOP
YIELD
FOLLOW
CHANGE_LEFT
CHANGE_RIGHT
TURN_LEFT
TURN_RIGHT
NUDGE_AROUND
```

再由低层控制器生成：

```python
carla.VehicleControl(throttle=..., brake=..., steer=...)
```

这种结构更容易调试，也更适合把 VLA 模型和传统控制器解耦。

### 5.3 第一批中国式混合交通场景

建议第一批实现 5 个场景：

1. 右转遇到电动车/摩托车直行
2. 非保护左转遇到对向车和行人
3. 自行车或摩托车突然横穿
4. 前车急刹或加塞
5. 公交站、路边停车或障碍物导致绕行

这些场景都适合体现“中国式混合交通”的核心难点：二轮车密集、交互意图不稳定、路口让行复杂、弱势交通参与者多。

## 6. 建议仓库结构

建议 GitHub 仓库逐步组织为：

```text
vla-china-self-drive/
  PROJECT_PLAN.md
  README.md
  .gitignore
  pyproject.toml
  configs/
    carla_0916.yaml
    carla_0100.yaml
    sensors.yaml
    scenarios.yaml
  docs/
    env_setup.md
    server_setup.md
    scenario_design.md
    data_format.md
  scripts/
    launch_carla09.sh
    launch_carla10.sh
    health_check.py
    asset_inventory.py
    record_episode.py
  src/
    vla_china_self_drive/
      __init__.py
      sim/
      scenarios/
      agents/
      control/
      data/
      eval/
      utils/
  tests/
  outputs/
    .gitkeep
```

`outputs/`、大型数据集、视频、模型权重、CARLA package、地图包都不提交到 git。

## 7. 服务器开发迁移方案

### 7.1 服务器需要准备的内容

服务器至少需要：

- Ubuntu 22.04 或 24.04
- NVIDIA GPU 和可用驱动
- 能运行 `nvidia-smi`
- Vulkan / OpenGL 相关依赖
- Miniforge 或 Miniconda
- Git
- 足够磁盘空间，建议至少 200GB 起步
- 如果要训练模型，额外准备 CUDA、PyTorch 和模型缓存目录

建议服务器目录：

```bash
~/Projects/vla-china-self-drive
~/CARLA/carla-0.9.16
~/CARLA/carla-0.10.0
~/data/vla-china-self-drive
~/checkpoints/vla-china-self-drive
```

### 7.2 服务器 clone 项目

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone git@github.com:jeffliulab/vla-china-self-drive.git
cd vla-china-self-drive
```

如果服务器未配置 SSH key：

```bash
git clone https://github.com/jeffliulab/vla-china-self-drive.git
```

### 7.3 服务器安装 CARLA 0.9.16

不要从 git 仓库同步 CARLA 大目录。应在服务器单独下载或从本机传输：

```text
CARLA_0.9.16.tar.gz
AdditionalMaps_0.9.16.tar.gz
```

服务器安装步骤：

```bash
mkdir -p ~/CARLA/carla-0.9.16
tar -xzf CARLA_0.9.16.tar.gz -C ~/CARLA/carla-0.9.16
cd ~/CARLA/carla-0.9.16
mkdir -p Import
cp /path/to/AdditionalMaps_0.9.16.tar.gz Import/
chmod +x ImportAssets.sh
./ImportAssets.sh
```

创建环境：

```bash
conda create -n carla9 python=3.10 -y
conda activate carla9
python -m pip install --upgrade pip
pip install numpy pygame opencv-python matplotlib tqdm pyyaml
pip install ~/CARLA/carla-0.9.16/PythonAPI/carla/dist/carla-0.9.16-cp310-cp310-manylinux_2_31_x86_64.whl
python -c "import carla; print(carla.__file__)"
```

启动：

```bash
cd ~/CARLA/carla-0.9.16
./CarlaUE4.sh -quality-level=Low -nosound
```

新终端测试：

```bash
conda activate carla9
python scripts/health_check.py
python scripts/asset_inventory.py
```

### 7.4 服务器无显示器运行

如果服务器没有桌面显示，需要处理 headless CARLA。常见方案：

- 使用 `-RenderOffScreen`，前提是服务器驱动和 Vulkan 支持正常。
- 使用 Docker + NVIDIA runtime。
- 使用虚拟显示或远程桌面方案。

第一阶段建议先在本机完成脚本和场景逻辑，再迁移到服务器跑长时间采集。

## 8. 数据和文件管理

建议数据根目录不放在 git 仓库内：

```bash
~/data/vla-china-self-drive
```

建议 episode 数据结构：

```text
episode_000001/
  meta.json
  config.yaml
  frames/
    rgb_front/
    depth_front/
    semantic_front/
  states.parquet
  controls.parquet
  actors.parquet
  labels.jsonl
```

`meta.json` 至少包含：

```json
{
  "carla_version": "0.9.16",
  "map": "Town05",
  "scenario": "right_turn_with_motorbike",
  "weather": "...",
  "seed": 0,
  "fps": 20,
  "sensors": ["rgb_front", "depth_front", "semantic_front"]
}
```

## 9. 评测指标

第一阶段评测指标：

```text
route_completion
scenario_success
collision_count
red_light_violation
lane_invasion
offroad_count
min_ttc
hard_brake_count
average_jerk
instruction_compliance
```

本项目最重要的指标：

- `scenario_success`：是否在指定中国式交互场景中完成任务。
- `instruction_compliance`：是否遵守中文驾驶指令。
- `collision_count`：是否碰撞二轮车、行人、车辆。
- `min_ttc`：是否出现危险接近。

## 10. 开发阶段计划

### 阶段 0：工程初始化

目标：把项目从会议纪要变成可开发仓库。

任务：

- 新增 README、`.gitignore`、项目配置文件。
- 新增 `configs/`、`scripts/`、`src/`、`docs/`。
- 写 `health_check.py`，检查 CARLA server、map、blueprint。
- 写 `asset_inventory.py`，导出所有可 spawn actor。
- 明确本机和服务器环境配置。

### 阶段 1：仿真与资产验证

目标：确认 0.9.16 的地图、车辆、二轮车、行人、传感器可用。

任务：

- 在 `Town05` 启动 ego vehicle。
- spawn 汽车、行人、自行车、摩托车。
- 挂载 RGB、depth、semantic camera。
- 记录一段基础 episode。
- 输出资产清单 JSON。

### 阶段 2：场景生成

目标：实现第一批中国式混合交通场景。

任务：

- `right_turn_with_motorbike`
- `unprotected_left_turn`
- `bike_crossing`
- `cut_in_and_hard_brake`
- `bus_stop_or_parked_car_overtake`

每个场景需要：

- 固定 seed 可复现。
- 可配置 actor 数量和速度。
- 可保存场景描述。
- 可输出成功/失败结果。

### 阶段 3：Expert / Rule Baseline

目标：生成可用训练数据和评测基线。

任务：

- 使用 BehaviorAgent / TrafficManager / 自定义 rule policy。
- 将连续控制转成高层动作标签。
- 保存图像、状态、actor metadata、控制量和动作标签。
- 初步生成小规模数据集。

### 阶段 4：VLA Agent

目标：接入 VLA / VLM 高层决策。

第一版结构：

```text
image + ego state + route instruction + Chinese driving instruction
  -> VLA/VLM policy
  -> high-level action
  -> low-level controller
  -> carla.VehicleControl
```

第一阶段可以先用 prompt/API 或本地 VLM 做推理，不急于训练。

### 阶段 5：评测与展示

目标：形成可展示结果。

任务：

- 统一跑 rule baseline 和 VLA agent。
- 输出 episode 视频。
- 输出评测表格。
- 在 0.10.0 中复现一个高质量展示场景。
- 撰写 README 和实验报告。

## 11. 近期最优先任务

下一步建议按这个顺序执行：

1. 初始化 GitHub 仓库本地 checkout。
2. 补 `.gitignore`，避免提交 CARLA、大数据、视频、权重。
3. 新增工程骨架。
4. 写 `scripts/health_check.py`。
5. 写 `scripts/asset_inventory.py`。
6. 在 CARLA 0.9.16 server 运行时导出地图和 blueprint 清单。
7. 实现第一个场景：`right_turn_with_motorbike`。
8. 实现 episode recorder。

## 12. 当前风险和注意事项

- 当前本机 Codex 沙箱中 git 状态不可用，需要重新 clone 或初始化后再提交。
- 静态资产存在不代表 blueprint 一定可 spawn，需要运行 `asset_inventory.py` 验证。
- CARLA 0.9.16 和 0.10.0 默认都使用 `localhost:2000`，不要同时启动。
- CARLA package、地图、episode 数据、模型权重不要进入 git。
- 服务器 headless 运行 CARLA 可能需要额外处理 Vulkan、NVIDIA runtime 或 offscreen rendering。


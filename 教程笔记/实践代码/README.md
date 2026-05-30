# 实践代码 · 官方示例学习副本

> 本目录是从 CARLA 官方示例 `~/CARLA/carla-0.9.16/PythonAPI/examples/` **拷贝**来的学习副本（CARLA 0.9.16，MIT 许可，文件头保留原版权）。
> **用途**：在这些副本上改写成我们自己的脚本。**最终成品脚本建议放到项目 `scripts/`**（保持本目录是"学习/起步"、`scripts/` 是"产品"）。
> 文件夹按 `N-主题/` 命名，与 [../自动驾驶笔记/](../自动驾驶笔记/) 的 `N-主题.md` **一一对应**。

---

## 运行前提

1. **先起 server**（第一课任务 1，单独一个终端、常开）：
   ```bash
   conda activate carla9 && cd ~/CARLA/carla-0.9.16 && ./CarlaUE4.sh -quality-level=Low -nosound
   ```
2. **再跑示例**（另一个终端）：
   ```bash
   conda activate carla9 && python 实践代码/1-自动驾驶模型/manual_control.py
   ```
3. ⚠️ **导入注意**：`import carla` 走 carla9 已装的 wheel，开箱即用；但用到 `agents.navigation` 的（如 `automatic_control.py`）需把 `PythonAPI/carla` 加进 `PYTHONPATH`：
   ```bash
   export PYTHONPATH=$PYTHONPATH:~/CARLA/carla-0.9.16/PythonAPI/carla
   ```

**角色图例**：🏃 直接跑 ｜ 📖 读源码学 ｜ ✏️ 以它为范本写我们的脚本

---

## 1-自动驾驶模型（连接 / spawn / 资产）

| 示例 | 角色 | 我们怎么用 |
|---|---|---|
| `manual_control.py` | 🏃 | 任务 2：手动开车转一圈 |
| `generate_traffic.py` | 🏃 | 任务 2：生成 NPC 车流 |
| `tutorial.py` | 📖✏️ | 最小"spawn 车 + 挂相机"范本 → 改写成我们的 `scripts/health_check.py` / spawn 逻辑 |
| `vehicle_gallery.py` | 📖 | 遍历展示车型 → 任务 5/6（二轮车验证 / 资产清单）参考 |

## 2-可复现与传感器（同步 + 传感器）

| 示例 | 角色 | 我们怎么用 |
|---|---|---|
| `synchronous_mode.py` | 📖✏️ | **同步主循环 + 队列对齐范式** → 我们的确定性同步循环以它起步 |
| `sensor_synchronization.py` | 📖 | 多传感器按帧对齐 |
| `visualize_multiple_sensors.py` | 📖 | 多相机窗口可视化 |
| `dynamic_weather.py` | 📖 | 天气控制（第二/四课用） |

### 选读（在 `2-可复现与传感器/选读/`，激光雷达等；本项目以相机为主，可跳过）

| 示例 | 角色 | 我们怎么用 |
|---|---|---|
| `lidar_to_camera.py` | 📖 | 激光点投影到图像 |
| `open3d_lidar.py` | 📖 | Open3D 可视化激光点云 |
| `bounding_boxes.py` | 📖 | 3D 包围盒投影到图像（用内参 §4.6；对第四/五课的标注也有用） |

## 3-控制与行人

| 示例 | 角色 | 我们怎么用 |
|---|---|---|
| `automatic_control.py` | 📖✏️ | BehaviorAgent 自动驾驶 → 我们的规则 baseline / 控制桥接以它起步 |
| （手动开车见 1-自动驾驶模型 `manual_control.py`） | 🏃 | 行人控制无官方专门示例，第三课笔记里有 `WalkerControl` 用法 |

## 4-场景与数据

| 示例 | 角色 | 我们怎么用 |
|---|---|---|
| `start_recording.py` / `start_replaying.py` | 📖 | CARLA 自带录制/回放，做我们 `record_episode` 的对照 |
| `show_recorder_actors_blocked.py` / `show_recorder_collisions.py` / `show_recorder_file_info.py` | 📖 | 解析 recorder 日志（卡死/碰撞/文件信息），评测可借鉴 |
| `no_rendering_mode.py` | 📖 | 省渲染 / headless 采集参考（对接服务器路线） |

---

## git 处理（你决定）

这些是上游副本：
- 想**保留学习痕迹/改动** → 提交进 git。
- 想**保持仓库干净** → 把 `实践代码/` 加进 `.gitignore`，只把改写后的成品放 `scripts/`。

> 暂不用的示例（外设/第三方/niche，没拷进来）：`manual_control_carsim/chrono/steeringwheel`、`invertedai_traffic`、`carla_cosmos_gen`、`V2XDemo`、`vehicle_physics`、`draw_skeleton`、`get_component_test`、`test_addsecondvx`、`tutorial_gbuffer`、`client_bounding_boxes`。需要随时从 `~/CARLA/carla-0.9.16/PythonAPI/examples/` 取。

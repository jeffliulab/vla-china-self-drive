# CARLA 0.9.16 可用 Actor 清单（实测）

> 来源：运行中 server 的 blueprint library 查询。**41 车 + 52 行人 + 1 行人控制器 + 19 传感器**。
> ⚠️ **蓝图存在 ≠ 一定能 spawn**：spawn 点被占时 `spawn_actor` 会抛错、`try_spawn_actor` 返回 `None`（`vehicle_gallery.py` 崩溃就是用了 `spawn_actor` 撞了占位，不是车不可用）。二轮车能否稳定 spawn 仍需运行时逐个验（任务 5）。

---

## 一、车辆 `vehicle.*`（41，按轮数分）

### 🛵 二轮车（7）★ 项目核心
| id | 类型 |
|---|---|
| `vehicle.bh.crossbike` | 自行车 |
| `vehicle.diamondback.century` | 自行车 |
| `vehicle.gazelle.omafiets` | 自行车 |
| `vehicle.harley-davidson.low_rider` | 摩托 |
| `vehicle.kawasaki.ninja` | 摩托 |
| `vehicle.vespa.zx125` | 踏板/类电动车 |
| `vehicle.yamaha.yzf` | 摩托 |

### 🚌 大型车（适合做鬼探头"遮挡物"）
| id | 类型 |
|---|---|
| `vehicle.mitsubishi.fusorosa` | 巴士 |
| `vehicle.carlamotors.european_hgv` | 重卡（6 轮） |
| `vehicle.carlamotors.firetruck` | 消防车 |
| `vehicle.ford.ambulance` | 救护车 |
| `vehicle.carlamotors.carlacola` | 货车 |
| `vehicle.mercedes.sprinter` | 厢式货车 |
| `vehicle.volkswagen.t2` / `t2_2021` | 面包车 |

### 🚓 警车
`vehicle.dodge.charger_police` ｜ `vehicle.dodge.charger_police_2020`

### 🚗 普通轿车 / SUV（其余四轮，24）

| id | 车 | 说明 |
|---|---|---|
| `vehicle.audi.a2` | 奥迪 A2 | 小型两厢 |
| `vehicle.audi.etron` | 奥迪 e-tron | 电动 SUV |
| `vehicle.audi.tt` | 奥迪 TT | 双门轿跑 |
| `vehicle.bmw.grandtourer` | 宝马 Gran Tourer | 旅行/小车 |
| `vehicle.chevrolet.impala` | 雪佛兰 Impala | 美式大轿车 |
| `vehicle.citroen.c3` | 雪铁龙 C3 | 小型两厢 |
| `vehicle.dodge.charger_2020` | 道奇 Charger | 美式肌肉轿车 |
| `vehicle.ford.crown` | 福特 皇冠维多利亚 | 美式大轿车（常见警车/出租原型） |
| `vehicle.ford.mustang` | 福特 野马 | 肌肉跑车 |
| `vehicle.jeep.wrangler_rubicon` | Jeep 牧马人 | 越野 SUV |
| `vehicle.lincoln.mkz_2017` | 林肯 MKZ (2017) | 中型轿车 |
| `vehicle.lincoln.mkz_2020` | 林肯 MKZ (2020) | 中型轿车（CARLA 示例常用作 ego 默认车） |
| `vehicle.mercedes.coupe` | 奔驰 双门轿跑 | 轿跑 |
| `vehicle.mercedes.coupe_2020` | 奔驰 双门轿跑 (2020) | 轿跑 |
| `vehicle.micro.microlino` | Microlino | 微型电动泡泡车（极小） |
| `vehicle.mini.cooper_s` | Mini Cooper S | 小型车 |
| `vehicle.mini.cooper_s_2021` | Mini Cooper S (2021) | 小型车 |
| `vehicle.nissan.micra` | 日产 Micra（玛驰） | 小型两厢 |
| `vehicle.nissan.patrol` | 日产 途乐 | 大型 SUV |
| `vehicle.nissan.patrol_2021` | 日产 途乐 (2021) | 大型 SUV |
| `vehicle.seat.leon` | 西雅特 Leon | 紧凑两厢 |
| `vehicle.tesla.cybertruck` | 特斯拉 Cybertruck | 电动皮卡 |
| `vehicle.tesla.model3` | 特斯拉 Model 3 | 电动轿车 |
| `vehicle.toyota.prius` | 丰田 普锐斯 | 混动轿车 |

---

## 二、行人 `walker.pedestrian.*`（52）

- 编号连续：`walker.pedestrian.0001` … `walker.pedestrian.0052`。
- **行人控制器**：`controller.ai.walker`（1 个）——给行人加 AI 自动行走；**鬼探头"窜出"用手动 `WalkerControl`，不用它**（见第三课）。

---

## 三、传感器 `sensor.*`（19）

**本项目要用**：`sensor.camera.rgb`（VLA 的眼睛）、`sensor.camera.depth`、`sensor.camera.semantic_segmentation`；安全层算 TTC 可用 `sensor.other.obstacle` / `radar` / `lidar.ray_cast`。

全部：
- 相机：`rgb` `depth` `semantic_segmentation` `instance_segmentation` `normals` `optical_flow` `dvs` `cosmos_visualization`
- 激光：`lidar.ray_cast` `lidar.ray_cast_semantic`
- 其他：`radar` `gnss` `imu` `collision` `lane_invasion` `obstacle` `rss` `v2x` `v2x_custom`

---

## 项目相关结论

- **二轮车 7 种蓝图齐全** → 中国式混合交通的前提成立（自行车 3 + 摩托/踏板 4）。
- **遮挡物候选充足**：巴士 `fusorosa`、重卡 `european_hgv` 最适合鬼探头。
- **行人 52 种 + 控制器齐全** → 鬼探头的"人"没问题。
- 待办（任务 5）：运行时逐个 `try_spawn_actor` 验证 7 种二轮车在目标 spawn 点能否真 spawn，把成功/失败记进资产清单 JSON。

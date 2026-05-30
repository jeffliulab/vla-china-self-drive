#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import carla

import random
import time


def main():
    actor_list = []

    # 在本教程脚本中，我们将向仿真中添加一辆 vehicle，
    # 并让它以 autopilot 自动驾驶。我们还会创建一个挂载到该
    # vehicle 上的 camera，并把 camera 生成的所有图像保存到磁盘。

    try:
        # 首先，我们需要创建向模拟器发送请求的 client。
        # 这里我们假设模拟器在 localhost 的 2000 端口
        # 接收请求。
        client = carla.Client('localhost', 2000)
        client.set_timeout(2.0)

        # 有了 client 之后，我们就可以获取当前正在
        # 运行的 world。
        world = client.get_world()

        # world 中包含一系列 blueprint，我们可以用它们向仿真中
        # 添加新的 actor。
        blueprint_library = world.get_blueprint_library()

        # 现在我们过滤出所有类型为 'vehicle' 的 blueprint，并随机
        # 选择一个。
        bp = random.choice(blueprint_library.filter('vehicle'))

        # 一个 blueprint 包含定义某个 vehicle 实例的一系列属性，
        # 我们可以读取它们并修改其中一些。比如，
        # 我们来随机化它的颜色。
        if bp.has_attribute('color'):
            color = random.choice(bp.get_attribute('color').recommended_values)
            bp.set_attribute('color', color)

        # 现在我们需要给这辆 vehicle 一个初始 transform。我们从地图
        # 推荐的 spawn point 列表中随机选择一个 transform。
        transform = random.choice(world.get_map().get_spawn_points())

        # 那么，让我们告诉 world 去 spawn 这辆 vehicle。
        vehicle = world.spawn_actor(bp, transform)

        # 需要特别注意的是，我们创建的 actor 不会被销毁，
        # 除非我们调用它们的 "destroy" 函数。如果不调用 "destroy"，
        # 即使我们退出 Python 脚本，它们仍会留在仿真中。
        # 因此，我们把创建的所有 actor 都保存起来，以便
        # 之后销毁它们。
        actor_list.append(vehicle)
        print('created %s' % vehicle.type_id)

        # 让这辆 vehicle 四处行驶起来。
        vehicle.set_autopilot(True)

        # 现在我们再添加一个挂载到 vehicle 上的 "depth" camera。注意这里
        # 给出的 transform 现在是相对于 vehicle 的。
        camera_bp = blueprint_library.find('sensor.camera.depth')
        camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
        camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
        actor_list.append(camera)
        print('created %s' % camera.type_id)

        # 现在我们注册一个函数，每当该 sensor 收到一张图像时
        # 都会调用它。在本例中，我们把图像的像素转换为灰度图
        # 后保存到磁盘。
        cc = carla.ColorConverter.LogarithmicDepth
        camera.listen(lambda image: image.save_to_disk('_out/%06d.png' % image.frame, cc))

        # 等等，我不太喜欢之前给这辆 vehicle 设的位置，我打算
        # 把它往前移动一点。
        location = vehicle.get_location()
        location.x += 40
        vehicle.set_location(location)
        print('moved vehicle to %s' % location)

        # 不过现在这座城市大概相当空旷，让我们再添加几辆
        # vehicle。
        transform.location += carla.Location(x=40, y=-3.2)
        transform.rotation.yaw = -180.0
        for _ in range(0, 10):
            transform.location.x += 8.0

            bp = random.choice(blueprint_library.filter('vehicle'))

            # 这次我们使用 try_spawn_actor。如果该位置已经
            # 被其他物体占据，该函数会返回 None。
            npc = world.try_spawn_actor(bp, transform)
            if npc is not None:
                actor_list.append(npc)
                npc.set_autopilot(True)
                print('created %s' % npc.type_id)

        time.sleep(5)

    finally:

        print('destroying actors')
        camera.destroy()
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        print('done.')


if __name__ == '__main__':

    main()

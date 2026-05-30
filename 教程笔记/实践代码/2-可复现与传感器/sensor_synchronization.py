#!/usr/bin/env python

# Copyright (c) 2020 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
CARLA 的 sensor 同步示例

CARLA 同步模式（synchronous mode）的通信模型会并行地发送 world 的 snapshot
和各个 sensor 的数据流。
我们以此脚本为例，演示如何在 client 端同步 sensor 数据的采集。
为此，我们创建一个队列，每个 sensor 在 client 收到其数据时都会向该队列填充内容，
主循环会被阻塞，直到所有 sensor 都收到各自的数据。
这里假设所有 sensor 在每一个 tick 都会采集信息。如果并非如此，
client 需要在每一帧考虑该帧将有多少个 sensor 触发（tick）。
"""

from queue import Queue
from queue import Empty

import carla


# sensor 回调函数。
# 你在这里接收 sensor 数据并按需对其进行处理，
# 重要的一点是：在最后，它应当向 sensor 队列中加入一个元素。
def sensor_callback(sensor_data, sensor_queue, sensor_name):
    # 对 sensor_data 数据做处理，比如把它保存到磁盘
    # 然后你只需要把它加入队列即可
    sensor_queue.put((sensor_data.frame, sensor_name))


def main():
    # 我们先创建 client
    client = carla.Client('localhost', 2000)
    client.set_timeout(2.0)
    world = client.get_world()

    try:
        # 我们需要保存这些设置（settings），以便在脚本结束时恢复它们，
        # 让 server 回到我们最初找到它时的状态。
        original_settings = world.get_settings()
        settings = world.get_settings()

        # 我们启用 CARLA 同步模式（synchronous mode）
        settings.fixed_delta_seconds = 0.2
        settings.synchronous_mode = True
        world.apply_settings(settings)

        # 我们创建 sensor 队列，用来跟踪已经收到的信息。
        # 该结构是线程安全的，可以被所有 sensor 回调并发访问而不会出问题。
        sensor_queue = Queue()

        # 各个 sensor 的 blueprint
        blueprint_library = world.get_blueprint_library()
        cam_bp = blueprint_library.find('sensor.camera.rgb')
        lidar_bp = blueprint_library.find('sensor.lidar.ray_cast')
        radar_bp = blueprint_library.find('sensor.other.radar')

        # 我们创建所有 sensor，并把它们保存在一个列表里以方便使用。
        sensor_list = []

        cam01 = world.spawn_actor(cam_bp, carla.Transform())
        cam01.listen(lambda data: sensor_callback(data, sensor_queue, "camera01"))
        sensor_list.append(cam01)

        cam02 = world.spawn_actor(cam_bp, carla.Transform())
        cam02.listen(lambda data: sensor_callback(data, sensor_queue, "camera02"))
        sensor_list.append(cam02)

        cam03 = world.spawn_actor(cam_bp, carla.Transform())
        cam03.listen(lambda data: sensor_callback(data, sensor_queue, "camera03"))
        sensor_list.append(cam03)

        lidar_bp.set_attribute('points_per_second', '100000')
        lidar01 = world.spawn_actor(lidar_bp, carla.Transform())
        lidar01.listen(lambda data: sensor_callback(data, sensor_queue, "lidar01"))
        sensor_list.append(lidar01)

        lidar_bp.set_attribute('points_per_second', '1000000')
        lidar02 = world.spawn_actor(lidar_bp, carla.Transform())
        lidar02.listen(lambda data: sensor_callback(data, sensor_queue, "lidar02"))
        sensor_list.append(lidar02)

        radar01 = world.spawn_actor(radar_bp, carla.Transform())
        radar01.listen(lambda data: sensor_callback(data, sensor_queue, "radar01"))
        sensor_list.append(radar01)

        radar02 = world.spawn_actor(radar_bp, carla.Transform())
        radar02.listen(lambda data: sensor_callback(data, sensor_queue, "radar02"))
        sensor_list.append(radar02)

        # 主循环
        while True:
            # 触发 server（tick）
            world.tick()
            w_frame = world.get_snapshot().frame
            print("\nWorld's frame: %d" % w_frame)

            # 现在，我们等待 sensor 数据被接收。
            # 由于队列是阻塞的，我们会在 queue.get() 方法处等待，
            # 直到所有信息都被处理完，然后继续下一帧。
            # 我们在 get 方法中设置了 1.0 秒的超时时间，如果在这段时间内
            # 某些信息未收到，我们就继续。
            try:
                for _ in range(len(sensor_list)):
                    s_frame = sensor_queue.get(True, 1.0)
                    print("    Frame: %d   Sensor: %s" % (s_frame[0], s_frame[1]))

            except Empty:
                print("    Some of the sensor information is missed")

    finally:
        world.apply_settings(original_settings)
        for sensor in sensor_list:
            sensor.destroy()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(' - Exited by user.')

#!/usr/bin/env python

# Copyright (c) 2020 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
将 lidar 投影到 RGB camera 上的示例
"""

import os
import sys

import carla

import argparse
from queue import Queue
from queue import Empty
from matplotlib import cm

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

try:
    from PIL import Image
except ImportError:
    raise RuntimeError('cannot import PIL, make sure "Pillow" package is installed')

VIRIDIS = np.array(cm._colormaps.get_cmap('viridis').colors)
VID_RANGE = np.linspace(0.0, 1.0, VIRIDIS.shape[0])

def sensor_callback(data, queue):
    """
    这个简单的 callback 只是把数据存入一个线程安全的 Python Queue，
    以便从「主线程」中取出。
    """
    queue.put(data)


def tutorial(args):
    """
    本函数旨在作为一个教程，演示如何以同步方式获取数据，
    并把 lidar 的 3D 点投影到 2D camera 上。
    """
    # 连接到 server
    client = carla.Client(args.host, args.port)
    client.set_timeout(2.0)
    world = client.get_world()
    bp_lib = world.get_blueprint_library()

    traffic_manager = client.get_trafficmanager(8000)
    traffic_manager.set_synchronous_mode(True)

    original_settings = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 3.0
    world.apply_settings(settings)

    vehicle = None
    camera = None
    lidar = None

    try:
        if not os.path.isdir('_out'):
            os.mkdir('_out')
        # 查找所需的 blueprint
        vehicle_bp = bp_lib.filter("vehicle.lincoln.mkz_2017")[0]
        camera_bp = bp_lib.filter("sensor.camera.rgb")[0]
        lidar_bp = bp_lib.filter("sensor.lidar.ray_cast")[0]

        # 配置 blueprint
        camera_bp.set_attribute("image_size_x", str(args.width))
        camera_bp.set_attribute("image_size_y", str(args.height))

        if args.no_noise:
            lidar_bp.set_attribute('dropoff_general_rate', '0.0')
            lidar_bp.set_attribute('dropoff_intensity_limit', '1.0')
            lidar_bp.set_attribute('dropoff_zero_intensity', '0.0')
        lidar_bp.set_attribute('upper_fov', str(args.upper_fov))
        lidar_bp.set_attribute('lower_fov', str(args.lower_fov))
        lidar_bp.set_attribute('channels', str(args.channels))
        lidar_bp.set_attribute('range', str(args.range))
        lidar_bp.set_attribute('points_per_second', str(args.points_per_second))

        # spawn 这些 blueprint
        vehicle = world.spawn_actor(
            blueprint=vehicle_bp,
            transform=world.get_map().get_spawn_points()[0])
        vehicle.set_autopilot(True)
        camera = world.spawn_actor(
            blueprint=camera_bp,
            transform=carla.Transform(carla.Location(x=1.6, z=1.6)),
            attach_to=vehicle)
        lidar = world.spawn_actor(
            blueprint=lidar_bp,
            transform=carla.Transform(carla.Location(x=1.0, z=1.8)),
            attach_to=vehicle)

        # 构建 K 投影矩阵：
        # K = [[Fx,  0, image_w/2],
        #      [ 0, Fy, image_h/2],
        #      [ 0,  0,         1]]
        image_w = camera_bp.get_attribute("image_size_x").as_int()
        image_h = camera_bp.get_attribute("image_size_y").as_int()
        fov = camera_bp.get_attribute("fov").as_float()
        focal = image_w / (2.0 * np.tan(fov * np.pi / 360.0))

        # 这里 Fx 和 Fy 相同，因为像素纵横比为 1
        K = np.identity(3)
        K[0, 0] = K[1, 1] = focal
        K[0, 2] = image_w / 2.0
        K[1, 2] = image_h / 2.0

        # sensor 数据将被保存到线程安全的 Queue 中
        image_queue = Queue()
        lidar_queue = Queue()

        camera.listen(lambda data: sensor_callback(data, image_queue))
        lidar.listen(lambda data: sensor_callback(data, lidar_queue))

        for frame in range(args.frames):
            world.tick()
            world_frame = world.get_snapshot().frame

            try:
                # 数据一旦收到就取出。
                image_data = image_queue.get(True, 1.0)
                lidar_data = lidar_queue.get(True, 1.0)
            except Empty:
                print("[Warning] Some sensor data has been missed")
                continue

            assert image_data.frame == lidar_data.frame == world_frame
            # 此时，我们已经拿到了两个 sensor 同步后的信息。
            sys.stdout.write("\r(%d/%d) Simulation: %d Camera: %d Lidar: %d" %
                (frame, args.frames, world_frame, image_data.frame, lidar_data.frame) + ' ')
            sys.stdout.flush()

            # 获取原始的 BGRA 缓冲区，并将其转换为形状为
            # (image_data.height, image_data.width, 3) 的 RGB 数组。
            im_array = np.copy(np.frombuffer(image_data.raw_data, dtype=np.dtype("uint8")))
            im_array = np.reshape(im_array, (image_data.height, image_data.width, 4))
            im_array = im_array[:, :, :3][:, :, ::-1]

            # 获取 lidar 数据并将其转换为 numpy 数组。
            p_cloud_size = len(lidar_data)
            p_cloud = np.copy(np.frombuffer(lidar_data.raw_data, dtype=np.dtype('f4')))
            p_cloud = np.reshape(p_cloud, (p_cloud_size, 4))

            # 形状为 (p_cloud_size,) 的 lidar 强度（intensity）数组，不过现在
            # 我们先关注 3D 点。
            intensity = np.array(p_cloud[:, 3])

            # lidar sensor 坐标系下的 point cloud，形状为 (3, p_cloud_size)。
            local_lidar_points = np.array(p_cloud[:, :3]).T

            # 在每个 3d 点末尾追加一个 1.0，使其形状变为
            # (4, p_cloud_size)，从而可以与 (4, 4) 矩阵相乘。
            local_lidar_points = np.r_[
                local_lidar_points, [np.ones(local_lidar_points.shape[1])]]

            # 这个 (4, 4) 矩阵把点从 lidar 坐标系变换到 world 坐标系。
            lidar_2_world = lidar.get_transform().get_matrix()

            # 把点从 lidar 坐标系变换到 world 坐标系。
            world_points = np.dot(lidar_2_world, local_lidar_points)

            # 这个 (4, 4) 矩阵把点从 world 坐标系变换到 sensor 坐标系。
            world_2_camera = np.array(camera.get_transform().get_inverse_matrix())

            # 把点从 world 坐标系变换到 camera 坐标系。
            sensor_points = np.dot(world_2_camera, world_points)

            # 现在我们必须从 UE4 的坐标系转换到「标准」的
            # camera 坐标系（与 OpenCV 所用的相同）：

            # ^ z                       . z
            # |                        /
            # |              转换为：    +-------> x
            # | . x                   |
            # |/                      |
            # +-------> y             v y

            # 这可以通过乘以下面这个矩阵来实现：
            # [[ 0,  1,  0 ],
            #  [ 0,  0, -1 ],
            #  [ 1,  0,  0 ]]

            # 或者，在本例中，等价于做如下交换：
            # (x, y ,z) -> (y, -z, x)
            point_in_camera_coords = np.array([
                sensor_points[1],
                sensor_points[2] * -1,
                sensor_points[0]])

            # 最后我们就可以用 K 矩阵来执行真正的 3D -> 2D 投影。
            points_2d = np.dot(K, point_in_camera_coords)

            # 记得用第 3 个分量对 x、y 值做归一化。
            points_2d = np.array([
                points_2d[0, :] / points_2d[2, :],
                points_2d[1, :] / points_2d[2, :],
                points_2d[2, :]])

            # 此时，points_2d[0, :] 包含了所有点的 x 值，points_2d[1, :]
            # 包含了所有点的 y 值。为了能在屏幕上正确地可视化这些内容，
            # 必须丢弃位于屏幕之外的点，位于 camera 投影平面之后的点
            # 同样也要丢弃。
            points_2d = points_2d.T
            intensity = intensity.T
            points_in_canvas_mask = \
                (points_2d[:, 0] > 0.0) & (points_2d[:, 0] < image_w) & \
                (points_2d[:, 1] > 0.0) & (points_2d[:, 1] < image_h) & \
                (points_2d[:, 2] > 0.0)
            points_2d = points_2d[points_in_canvas_mask]
            intensity = intensity[points_in_canvas_mask]

            # 提取屏幕坐标 (uv) 并转换为整数。
            u_coord = points_2d[:, 0].astype(int)
            v_coord = points_2d[:, 1].astype(int)

            # 由于在编写本脚本时，intensity 函数返回的值偏大，
            # 这里对其做调整以便更好地可视化。
            intensity = 4 * intensity - 3
            color_map = np.array([
                np.interp(intensity, VID_RANGE, VIRIDIS[:, 0]) * 255.0,
                np.interp(intensity, VID_RANGE, VIRIDIS[:, 1]) * 255.0,
                np.interp(intensity, VID_RANGE, VIRIDIS[:, 2]) * 255.0]).astype(int).T

            if args.dot_extent <= 0:
                # 用 numpy 把这些 2d 点以单个像素的形式绘制到图像上。
                im_array[v_coord, u_coord] = color_map
            else:
                # 把这些 2d 点以边长为 args.dot_extent 的方块形式绘制到图像上。
                for i in range(len(points_2d)):
                    # 我不是 NumPy 专家，不知道在不使用这个循环的情况下如何绘制更大的点，
                    # 所以如果有人有更好的方案，请务必更新本脚本。
                    # 在此之前，它已经足够快了 :)
                    im_array[
                        v_coord[i]-args.dot_extent : v_coord[i]+args.dot_extent,
                        u_coord[i]-args.dot_extent : u_coord[i]+args.dot_extent] = color_map[i]

            # 使用 Pillow 模块保存图像。
            image = Image.fromarray(im_array)
            image.save("_out/%08d.png" % image_data.frame)

    finally:
        # 退出时恢复原始 settings。
        world.apply_settings(original_settings)

        # 销毁场景中的 actor。
        if camera:
            camera.destroy()
        if lidar:
            lidar.destroy()
        if vehicle:
            vehicle.destroy()


def main():
    """启动函数"""
    argparser = argparse.ArgumentParser(
        description='CARLA Sensor sync and projection tutorial')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='680x420',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '-f', '--frames',
        metavar='N',
        default=500,
        type=int,
        help='number of frames to record (default: 500)')
    argparser.add_argument(
        '-d', '--dot-extent',
        metavar='SIZE',
        default=2,
        type=int,
        help='visualization dot extent in pixels (Recomended [1-4]) (default: 2)')
    argparser.add_argument(
        '--no-noise',
        action='store_true',
        help='remove the drop off and noise from the normal (non-semantic) lidar')
    argparser.add_argument(
        '--upper-fov',
        metavar='F',
        default=30.0,
        type=float,
        help='lidar\'s upper field of view in degrees (default: 15.0)')
    argparser.add_argument(
        '--lower-fov',
        metavar='F',
        default=-25.0,
        type=float,
        help='lidar\'s lower field of view in degrees (default: -25.0)')
    argparser.add_argument(
        '-c', '--channels',
        metavar='C',
        default=64.0,
        type=float,
        help='lidar\'s channel count (default: 64)')
    argparser.add_argument(
        '-r', '--range',
        metavar='R',
        default=100.0,
        type=float,
        help='lidar\'s maximum range in meters (default: 100.0)')
    argparser.add_argument(
        '--points-per-second',
        metavar='N',
        default='100000',
        type=int,
        help='lidar points per second (default: 100000)')
    args = argparser.parse_args()
    args.width, args.height = [int(x) for x in args.res.split('x')]
    args.dot_extent -= 1

    try:
        tutorial(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':

    main()

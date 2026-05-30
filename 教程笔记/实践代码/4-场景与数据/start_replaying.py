#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import carla

import argparse


def main():

    argparser = argparse.ArgumentParser(
        description=__doc__)
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
        '-s', '--start',
        metavar='S',
        default=0.0,
        type=float,
        help='starting time (default: 0.0)')
    argparser.add_argument(
        '-d', '--duration',
        metavar='D',
        default=0.0,
        type=float,
        help='duration (default: 0.0)')
    argparser.add_argument(
        '-f', '--recorder-filename',
        metavar='F',
        default="test1.log",
        help='recorder filename (test1.log)')
    argparser.add_argument(
        '-c', '--camera',
        metavar='C',
        default=0,
        type=int,
        help='camera follows an actor (ex: 82)')
    argparser.add_argument(
        '-x', '--time-factor',
        metavar='X',
        default=1.0,
        type=float,
        help='time factor (default 1.0)')
    argparser.add_argument(
        '-i', '--ignore-hero',
        action='store_true',
        help='ignore hero vehicles')
    argparser.add_argument(
        '--move-spectator',
        action='store_true',
        help='move spectator camera')
    argparser.add_argument(
        '--top-view',
        action='store_true',
        help='enable top-down camera view when following an actor')
    argparser.add_argument(
        '--spawn-sensors',
        action='store_true',
        help='spawn sensors in the replayed world')
    args = argparser.parse_args()

    try:

        client = carla.Client(args.host, args.port)
        client.set_timeout(60.0)

        # 设置 replayer 的时间倍率
        client.set_replayer_time_factor(args.time_factor)

        # 设置是否忽略 hero 车辆
        client.set_replayer_ignore_hero(args.ignore_hero)

        # 设置是否忽略 spectator 摄像机
        client.set_replayer_ignore_spectator(not args.move_spectator)

        # 设置期望的偏移量
        offset = carla.Transform(carla.Location(-10, 0, 5),  carla.Rotation(-25, 0, 0))
        if args.top_view:
            offset = carla.Transform(carla.Location(0, 0, 40), carla.Rotation(-90, 0, 0))

        # 回放本次录制会话
        print(client.replay_file(args.recorder_filename, args.start, args.duration, args.camera, args.spawn_sensors, offset))

    finally:
        pass


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')

#!/usr/bin/env python
from __future__ import division, print_function


# cloudberryCam v0 copyright (c) 2013-2015 Lars Rosengreen

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import io
import os
import sys
import time

import numpy
import picamera

from PIL import Image


_current_directory = os.path.dirname(os.path.abspath(__file__))
_preview_directory =  "/mnt/ramdisk/previews"
_movie_directory = _current_directory + "/movies"
_resolution = (1920, 1080)
_preview_resolution = (960, 540)
_framerate = 4 #frames per second
_start_time = datetime.time(6)
_end_time = datetime.time(18)
_minimum_free_space = 0.5 #free space in GB


def free_space():
    "Free disk space in gigabytes."
    s = os.statvfs('/')
    return (s.f_bavail * s.f_frsize) / 1.0e9


def run():
    if not os.path.exists(_preview_directory):
        os.makedirs(_preview_directory)
    if not os.path.exists(_movie_directory):
        os.makedirs(_movie_directory)

    now = datetime.datetime.now().time()
    while free_space() > _minimum_free_space:
        now = datetime.datetime.now().time()
        if now > _start_time and now < _end_time:
            counter = 1
            with picamera.PiCamera() as camera:
                camera.resolution = _resolution
                camera.vflip = True
                camera.hflip = True
                camera.framerate = _framerate
                camera.annotate_background = True
                try:
                    start_time = datetime.datetime.now()
                    camera.start_recording(os.path.join(_movie_directory,
                        "{}.h264".format(start_time.strftime("%Y%b%d_%H-%M-%S").lower())))
                    while free_space() > _minimum_free_space and now > _start_time and now < _end_time:
                        timestamp = datetime.datetime.now()
                        now = timestamp.time()
                        camera.annotate_text = timestamp.strftime("%Y%b%d %H:%M").lower()
                        camera.capture(os.path.join(_preview_directory,"preview.jpg"),
                                resize=_preview_resolution,
                                quality=30,
                                use_video_port=True)
                        print("\r{:78}".format(""), end="\r")
                        print("\rrunning:{} previews:{}".format(str(timestamp - start_time).split(".")[0], counter), end="")
                        sys.stdout.flush()
                        counter += 1
                        camera.wait_recording(60)
                finally:
                    camera.stop_recording()
        else:
            print("\r{:78}".format(""), end="\r")
            print("\rwaiting until: {} ({})".format(str(_start_time), str(now).split(".")[0]), end="")
            sys.stdout.flush()
            time.sleep(20)


if __name__ == "__main__":
    run()

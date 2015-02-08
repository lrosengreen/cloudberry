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
import shutil
import sys
import time

import picamera


_current_directory = os.path.dirname(os.path.abspath(__file__))
_preview_directory =  "/mnt/ramdisk/previews"
_picture_directory = _current_directory + "/pictures"
_start_time = datetime.datetime.now()
_timelapse_interval = 2 # how long to wait between taking pictures (in seconds)


def free_space():
    "Free disk space in gigabytes."
    s = os.statvfs('/')
    return (s.f_bavail * s.f_frsize) / 1.0e9


def run():
    if not os.path.exists(_preview_directory):
        os.makedirs(_preview_directory)
    if not os.path.exists(_picture_directory):
        os.makedirs(_picture_directory)
    counter = 0
    with picamera.PiCamera() as camera:
        camera.resolution = (2592, 1944) #2592, 1944
        camera.vflip = True
        camera.hflip = True
        camera.annotate_background = True
        camera.start_preview()
        time.sleep(5)
        start_time = datetime.datetime.now()
        next_time = start_time
        try:
            timestamp = datetime.datetime.now()
            while free_space() > 0.5:
                timestamp = datetime.datetime.now()
                next_time = next_time + datetime.timedelta(seconds=_timelapse_interval)
                fname = os.path.join(_picture_directory, "{:06d} {}.jpg".format(counter, timestamp.strftime("%Y%b%d %Hh%Mm%Ss")))
                camera.annotate_text = timestamp.strftime("%Y%b%d %H:%M:%S").lower()
                camera.capture(fname)
                #if counter % 20 == 0:
                shutil.copy(fname, os.path.join(_preview_directory, "preview.jpg"))
                # figure out how long to wait before taking next picture
                if datetime.datetime.now() <= next_time:
                    wait_time = next_time - datetime.datetime.now()
                    wait_time = wait_time.seconds + wait_time.microseconds * 1e-6
                else:
                    # It could be that the time to take next picture has already passed.
                    # In that case, wait time should be negative and value passed to
                    # time.sleep() should be 0.
                    wait_time = datetime.datetime.now() - next_time
                    wait_time = -1 * (wait_time.seconds + wait_time.microseconds * 1e-6)
                print("time:{} images:{} wait:{}s".format(str(timestamp - start_time).split(".")[0], counter, wait_time))
                time.sleep(0 if wait_time < 0 else wait_time)
                counter += 1
        finally:
                camera.stop_preview()
                camera.close()




if __name__ == "__main__":
    run()

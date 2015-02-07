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
import math
import os
import shutil
import sys
import time

import numpy
import picamera
from PIL import Image



_current_directory = os.path.dirname(os.path.abspath(__file__))
_preview_directory =  "/mnt/ramdisk/previews"
_picture_directory = _current_directory + "/pictures"
_start_time = datetime.datetime.now()
_image_width = 2592
_image_height = 1944
_preview_width = _image_width // 3
_preview_heigh = _image_height // 3
_timelapse_interval = 10 # how long to wait between taking pictures (in seconds)
_darkness_cutoff = 18
_darkness_sleeptime = 300 - _timelapse_interval # how long to wait when image is too dark (in seconds)


def brightness(image):
    m = numpy.asarray(image)
    b = math.log(numpy.sum(m))
    return b

def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def free_space():
    "Free disk space in gigabytes."
    s = os.statvfs('/')
    return (s.f_bavail * s.f_frsize) / 1.0e9

def save_preview(image):
    preview = image.resize((_preview_width,_preview_heigh))
    preview.save(os.path.join(_preview_directory, "preview.jpg"), quality=30)


def save_image(image, filepath):
    image.save(filepath, quality=90)


def update_status(status):
    print(status)


def run():
    ensure_directory(_preview_directory)
    ensure_directory(_picture_directory)
    counter = 0
    with picamera.PiCamera() as camera:
        camera.resolution = (2592, 1944) #2592, 1944
        camera.vflip = True
        camera.hflip = True
        camera.annotate_background = True
        time.sleep(5)
        start_time = datetime.datetime.now()
        next_time = start_time
        try:
            timestamp = datetime.datetime.now()
            while free_space() > 0.5:
                timestamp = datetime.datetime.now()
                next_time = next_time + datetime.timedelta(seconds=_timelapse_interval)
                camera.annotate_text = timestamp.strftime("%Y-%m-%d %H:%M:%S").lower()
                # Create the in-memory stream
                stream = io.BytesIO()
                camera.capture(stream, format='jpeg')
                # "Rewind" the stream to the beginning so we can read its content
                stream.seek(0)
                image = Image.open(stream)
                light_level = brightness(image)
                save_preview(image)
                status = ""
                if light_level > _darkness_cutoff:
                    save_location = os.path.join(_picture_directory, timestamp.strftime("%Y-%m-%d"))
                    ensure_directory(save_location)
                    fpath = os.path.join(save_location, "{:06d}.jpg".format(counter))
                    save_image(image, fpath)
                    counter = counter + 1
                else:
                    status += " [sleeping]"
                    next_time = next_time + datetime.timedelta(seconds=_darkness_sleeptime)
                stream.close()
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
                status = "time:{} images:{} wait:{:.2f}s brightness:{:.2f}".format(str(timestamp - start_time).split(".")[0], counter, wait_time, light_level) + status
                update_status(status)
                time.sleep(0 if wait_time < 0 else wait_time)
        finally:
                camera.stop_preview()
                camera.close()




if __name__ == "__main__":
    run()

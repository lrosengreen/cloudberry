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


import copy
import datetime
import io
import multiprocessing
import os
import random
import subprocess
import sys
import time

import numpy

import picamera

from PIL import Image


_current_directory = os.path.dirname(os.path.abspath(__file__))
_event_directory =  _current_directory + "/events"
_preview_directory = _current_directory + "/previews"
_image_width = 2592
_image_height = 1944
_preview_width = _image_width // 3
_preview_heigh = _image_height // 3
_heartbeat = 10
_darkness_cutoff = 40000000
_darkness_sleeptime = 10 # time in minutes



class RPiCamera:
    def __init__(self, image_size=(_image_width, _image_height)):
        self.image_size = image_size
        self.image_counter = 0
        self.start_time = datetime.datetime.now()

    def take_picture(self):
        # Create the in-memory stream
        stream = io.BytesIO()
        with picamera.PiCamera() as camera:
            camera.resolution = self.image_size
            camera.meter_mode = 'average'
            camera.ISO = 200
            camera.start_preview()
            time.sleep(2)
            camera.capture(stream, format='jpeg')
        # "Rewind" the stream to the beginning so we can read its content
        stream.seek(0)
        image = Image.open(stream)
        timestamp = datetime.datetime.now()
        self.image_counter += 1
        return (image, timestamp)



class RPiCamera2:
    def __init__(self, image_size=(_image_width, _image_height)):
        self.image_size = image_size
        self.image_counter = 0
        self.start_time = datetime.datetime.now()
        # set up the camera (with initial values, run preview, etc.)
        self.camera = self.start()


    def start(self):
        camera = picamera.PiCamera()
        camera.resolution = self.image_size
        camera.meter_mode = 'average'
        camera.ISO = 200
        camera.vflip = True
        camera.hflip = True
        # Need to "warm up" the camera for a few seconds before starting to take any picutres
        # to ensure that it has an accurate exposure reading.
        camera.start_preview()
        time.sleep(10)
        self.running = True
        return camera


    def stop(self):
        # When the camera isn't going to be used for a while, turn it off to save power.
        # (for example when it's too dark outside)
        self.camera.stop_preview()
        self.camera.close()
        self.running = False


    def take_picture(self):
        if not self.running: self.start()
        # Create the in-memory stream
        stream = io.BytesIO()
        self.camera.capture(stream, format='jpeg')
        # "Rewind" the stream to the beginning so we can read its content
        stream.seek(0)
        image = Image.open(stream)
        timestamp = datetime.datetime.now()
        self.image_counter += 1
        return (image, timestamp)



class DummyCamera:
    def __init__(self, image_size=(_image_width, _image_height)):
        self.image_size = image_size
        self.image_counter = 0
        self.start_time = datetime.datetime.now()
        self.running = False

    def start(self):
        self.running = True
        time.sleep(10)

    def stop(self):
        self.running = False

    def take_picture(self):
        # start up the camera if it is not currently running
        if not self.running: self.start()
        color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        image = Image.new('RGB', self.image_size, color)
        timestamp = datetime.datetime.now()
        self.image_counter += 1
        time.sleep(2)
        return (image, timestamp)


def brightness(image):
    m = numpy.asarray(image)
    return numpy.sum(m)


def save_image(image, image_counter, timestamp):
    outfile = "{:05d}_{}.jpg".format(image_counter,
                timestamp.strftime("%Y%b%d_%H%M%S"))
    preview = image.resize((_preview_width,_preview_heigh))
    preview.save(os.path.join(_preview_directory, outfile))
    image.save(os.path.join(_event_directory, outfile), quality=90)


def free_space():
    "Free disk space in gigabytes."
    s = os.statvfs('/')
    return (s.f_bavail * s.f_frsize) / 1.0e9


def run(testing=False):
    if not os.path.exists(_event_directory):
        os.makedirs(_event_directory)
    if not os.path.exists(_preview_directory):
        os.makedirs(_preview_directory)

    Camera = RPiCamera2()
    #Camera = DummyCamera()

    too_dark = False

    image, timestamp = Camera.take_picture()

    while True:
        running_time = str(timestamp - Camera.start_time).split('.')[0]
        print("\rtime: {} images: {}".format(running_time, Camera.image_counter), end="")
        sys.stdout.flush()

        if Camera.image_counter % _heartbeat == 0 or too_dark:
            light_level = brightness(image)
            if light_level < _darkness_cutoff:
                too_dark = True
                Camera.stop()
                print(" * too dark ({}); sleeping for {} minutes".format(light_level, _darkness_sleeptime), end="")
                sys.stdout.flush()
                time.sleep(_darkness_sleeptime * 60)
            else:
                too_dark = False
                print(" *", end="")
                sys.stdout.flush()
            if free_space() < 0.5:
                print("\n\n**** quitting: no disk space ****\n\n")
                break

        save_process = multiprocessing.Process(target=save_image, args=(copy.copy(image), Camera.image_counter, timestamp))
        save_process.start()
        image, timestamp = Camera.take_picture()
        save_process.join()

        print("\r{:78}".format(""), end="\r")


if __name__ == "__main__":
    run(testing=True)

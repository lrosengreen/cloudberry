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


import collections
import datetime
import os
import shutil
import StringIO
import subprocess
import sys
import time

from PIL import Image
import numpy as np


_preview_directory = "previews"
_event_directory = "events"
BACKGROUND_QUEUE_SIZE = 60
_image_width = 2592
_image_height = 1944
_preview_width = _image_width // 3
_preview_heigh = _image_height // 3
IMAGE_QUEUE_SIZE = 3
SIGMA = 4
EVENT_THRESHOLD = 0.0025
SNAPSHOT_PIXELS = 160*120*3
DARKNESS_CUTOFF = 100
DARKNESS_SLEEPTIME = 600
HEARTBEAT = 2


class Picture:
    def __init__(self, image, timestamp):
        self.image = image
        self.timestamp = timestamp


class RPiCamera:
    def __init__(self, image_size=(_image_width, _image_height)):
        self.image_size = image_size
        self.image_counter = 0
        self.start_time = datetime.datetime.now()

    def take_picture(self):
        command = "raspistill -n -mm average -w {} -h {} -ISO 200 -q 100 -t 1000 -e bmp -o -".format(self.image_size[0], self.image_size[1])
        image_data = StringIO.StringIO()
        image_data.write(subprocess.check_output(command, shell=True))
        image_data.seek(0)
        image = Image.open(image_data)
        image.load()
        image_data.close()
        timestamp = datetime.datetime.now()
        self.image_counter += 1
        return Picture(image, timestamp)



def preprocess_image(i):
    im = i.image
    im = im.resize((160,120))
    # convert color RGB image to grayscale. This gives a greater range
    # of values than Image.convert('L')
    #r, g, b = (np.asarray(band, dtype="u4") for band in im.split())
    #matrix = sum((0.2126 * r, 0.7152 * g, 0.0722 * b))
    matrix = np.asarray(im)
    return matrix


def calc_stats(xs):
    n = len(xs)
    mean = sum(xs) / n
    stdev = np.sqrt(sum(np.square(x - mean) for x in xs) / n)
    return (mean, stdev)


def find_foreground(b, x, factor):
    m, s = calc_stats(b)
    diff = np.abs(x - m)
    foreground_pixels = (diff > (s * factor)).sum()
    return foreground_pixels


def warm_up(background_queue_size, image_queue_size):
    background_queue = collections.deque(maxlen=background_queue_size)
    image_queue = collections.deque(maxlen=image_queue_size)
    for x in range(background_queue_size, 0, -1):
        im = RPiCameraImage()
        m = preprocess_image(im)
        background_queue.append(m)
        if x <= image_queue_size:
            image_queue.append(im)
        print("\rwarming up... {:>3}".format(x), end="")
        sys.stdout.flush()
    print("\r{:60}".format(""), end="\r")
    return (background_queue, image_queue)


def do_event(background_queue, image_queue, event_counter):
    print("\r{:60}".format(""), end="\r")
    n = len(image_queue)
    midpoint = n // 2
    for x in range(0,n):
        im = image_queue.popleft()
        image = im.image
        ts = im.timestamp
        print("===> event: {} time: {}".format(event_counter,
                                                ts.strftime("%x %X")))
        outfile = "{:05d}_{}.jpg".format(event_counter, ts.strftime("%Y%b%d_%H%M%S"))
        preview = image.resize((_preview_width,_preview_heigh))
        preview.save(os.path.join(_preview_directory, outfile))
        image.save(os.path.join(_event_directory, outfile), quality=90)
        event_counter += 1
        # Images after the midpoint in the image queue have not been added yet to the back-
        # ground queue, so add them now.
        if x > midpoint:
            m = preprocess_image(im)
            background_queue.append(m)
    return (background_queue, image_queue, event_counter)






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



def run():
    camera = RPiCamera((_image_width, _image_height))

    event_counter = 0
    too_dark = False

    background_queue, image_queue = warm_up(BACKGROUND_QUEUE_SIZE, IMAGE_QUEUE_SIZE)

    # main run loop
    while True:
        im = camera.take_picture()
        image_queue.append(im)
        # sample from the mid point of the image queue. By doing this, we can save
        # to disk a few images before and after an event happens.
        i = image_queue[len(image_queue) // 2]
        m = preprocess_image(i)
        # estimate how many pixels are in the foreground
        fg = find_foreground(background_queue, m, SIGMA) / SNAPSHOT_PIXELS
        print("\r{:6} {:5.2f}%".format(camera.image_counter, fg * 100), end="")
        sys.stdout.flush()
        if fg > EVENT_THRESHOLD:
            # get a full-sized image and save it to a file
            background_queue, image_queue, event_counter = do_event(background_queue,
                                                                    image_queue,
                                                                    event_counter)
        # If the image is very dark, then switch to darkness mode, pause for a few
        # minutes between taking thumbnails to save power
        if (image_counter % HEARTBEAT == 0) or too_dark:
            light_level = brightness(m)
            if light_level < DARKNESS_CUTOFF:
                too_dark = True
                print("\r{:6} sleeping (too dark, light level {})".format(image_counter,
                        light_level), end="")
                sys.stdout.flush()
                time.sleep(DARKNESS_SLEEPTIME)
                print("\r{:70}".format(""), end="\r")
            else:
                too_dark = False
        background_queue.append(m)



if __name__ == "__main__":
    run()

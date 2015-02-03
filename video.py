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

import picamera


_current_directory = os.path.dirname(os.path.abspath(__file__))

# where to send previews (ideally to a ramdisk to avoid wear on the memory card)
_preview_directory =  "/mnt/ramdisk/previews"

# where to save movies
_movie_directory = os.path.joing(_current_directory,"movies")

# resolution of movie footage; (1920, 1080) is HD
_resolution = (1920, 1080)

# resolution of web previews
_preview_resolution = (960, 540)

# how often should the preview images be updated (in seconds wait time between
# updates)
_preview_update_interval = 15

# for video footage, home many frames per second
_framerate = 4

# start time and end time for when video should be recorded, in hours, using
# a 24-hour clock (for example datetime.time(7) would be 7AM, datetime.time(18)
# would be 5PM)
_start_time = datetime.time(7) # start time in hours (24 hr clock)
_end_time = datetime.time(18) # end time in hours (24hr clock)

# If free disk space drops below this ammount, stop recording.
_minimum_free_space = 0.5 #stop if free space gets lower than this in GB

# Should current time be added as an annotation in the video frame? (True = yes,
# False = no)
_annotate_video = True

def free_space():
    "Free disk space in gigabytes."
    s = os.statvfs('/')
    return (s.f_bavail * s.f_frsize) / 1.0e9


def record_footage():
    "Record video footage"
    counter = 1
    with picamera.PiCamera() as camera:
        camera.resolution = _resolution
        camera.vflip = True
        camera.hflip = True
        camera.framerate = _framerate
        if _annotate_video = True:
            camera.annotate_background = True
        else:
            camera.annotate_background = False
        try:
            start_time = datetime.datetime.now()
            now = now.time()
            fname = os.path.join(_movie_directory, "{}.h264".format(start_time.strftime("%Y%b%d_%H-%M-%S").lower()))
            print("recording to {}".format(fname))
            camera.start_recording(fname)
            while free_space() > _minimum_free_space and now > _start_time and now < _end_time:
                timestamp = datetime.datetime.now()
                now = timestamp.time()
                if _annotate_video = True:
                    camera.annotate_text = timestamp.strftime("%Y%b%d %H:%M").lower()
                camera.capture(os.path.join(_preview_directory,"preview.jpg"),
                        resize=_preview_resolution,
                        quality=30,
                        use_video_port=True)
                print("\r{:78}".format(""), end="\r")
                print("\rrunning:{} previews:{}".format(str(timestamp - start_time).split(".")[0], counter), end="")
                sys.stdout.flush()
                counter += 1
                camera.wait_recording(_preview_update_interval)
        finally:
            camera.stop_recording()
            print()



def run():
    if not os.path.exists(_preview_directory):
        os.makedirs(_preview_directory)
    if not os.path.exists(_movie_directory):
        os.makedirs(_movie_directory)

    while free_space() > _minimum_free_space:
        now = datetime.datetime.now().time()
        if now > _start_time and now < _end_time:
            record_footage()
        else:
            print("\r{:78}".format(""), end="\r")
            print("\rwaiting until: {} ({})".format(str(_start_time), str(now).split(".")[0]), end="")
            sys.stdout.flush()
            time.sleep(60)


if __name__ == "__main__":
    run()

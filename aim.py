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


import os
import os.path
import shutil
import StringIO
import subprocess
import sys
import time

import cherrypy
from cherrypy.lib import file_generator

from PIL import Image


current_dir = os.path.dirname(os.path.abspath(__file__))

IMAGE_WIDTH = 1600
IMAGE_HEIGHT = 1200
#IMAGE_WIDTH = 2592
#IMAGE_HEIGHT = 1944


def getRPiCameraImage():
    command = "raspistill -mm average -vf -hf -w {} -h {} -ISO 200 -q 100 -t 1000 -e bmp -o -".format(IMAGE_WIDTH, IMAGE_HEIGHT)
    im_data = StringIO.StringIO()
    im_data.write(subprocess.check_output(command, shell=True))
    im_data.seek(0)
    im = Image.open(im_data)
    im.load()
    im_data.close()
    return im


class Root:
    @cherrypy.expose
    def index(self):
        im = getRPiCameraImage()
        im_data = StringIO.StringIO()
        im.save(im_data, format="JPEG")
        im_data.seek(0)
        cherrypy.response.headers['Content-Type'] = "image/jpeg"
        return file_generator(im_data)


def run(testing=False):
    # Set up site-wide config first so we get a log if errors occur.
    cherrypy.config.update({'environment': 'production',
            'log.screen': testing})
    cherrypy.server.socket_host = '0.0.0.0'

    if testing == True:
        cherrypy.engine.autoreload.subscribe()

    cherrypy.quickstart(Root(), '/')


if __name__ == "__main__":
    run(testing=True)

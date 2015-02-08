# cloudberry timelapse camera copyright (c) 2013-2015 Lars Rosengreen

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


from multiprocessing import Process, Queue, Array

import timelapse_camera
import timelapse_server


__author__ = "Lars Rosengreen"
__email__ = "lars.rosengreen@sjsu.edu"
__license__ = "GPL"
__version__ = "1.0e-99"


if __name__ == "__main__":
    print("cloudberry timelapse camera v{}".format(__version__))
    current_status = Array('c', 80)
    camera = Process(target=timelapse_camera.run, args=(current_status,))
    server = Process(target=timelapse_server.run, args=(current_status,))
    camera.start()
    server.start()
    camera.join()

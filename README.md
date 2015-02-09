cloudberry
==========

Software for using the Raspberry Pi camera module to observe pollinators and
other small things.

preliminaries
-------------

First, create a small ramdisk so preview images can be temporarily stored
without writing them to disk.

edit /etc/fstab and add the line

    tmpfs /mnt/ramdisk tmpfs nodev,nosuid,size=6M 0 0

This adds a 6mb ramdisk which is small, but still large enough to hold a single
camera jpeg image.

add a mount point for the ramdisk and make sure you have necessary write
permissions

    mkdir /mnt/ramdisk
    chmod +rw /mnt/ramdisk

reboot when done

Next, disable the led light on the camera.

edit /boot/config.txt and add the line

disable_camera_led=1


motion.py
---------
Take pictures when motion is detected using an adaptive statistical filtering
method (slow!).

timelapse.py
------------
Take high resolution pictures of a subject with a time delay between captures
(currently 2 second minimum).

video.py
--------
Record (low framerate) video footage of a subject over several
days (depending on disk space, of course).

# Photobooth
Photobooth with a Raspberry Pi. Two configurations are available: 1) Use of the Raspberry Pi camera, or 2) Use of a DSLR camera.

## Installation
The photobooth software was tested with Raspbian Jessie.
git clone https://github.com/manjan4487/Photobooth/tree/dslrTest.git

### Pi camera
Just connect your Pi camera to the correct connector on the raspberry pi.

### DSLR
To use the DSLR configuration you need the gphoto2 lib for python, see https://github.com/jim-easterbrook/python-gphoto2 for installation details (you also need to install the dependencies!). Short instructions:
sudo apt-get install python3 libgphoto2-dev pkg-config
sudo pip3 install -v gphoto2

Connect your DSLR via USB to the raspberry pi. Check if your camera is supported by gphoto2, see http://gphoto.org/proj/libgphoto2/support.php

## Configuration
Check the configuration part of the main file.

### Pi camera
There are no special configurations neccesary for the Pi camera.

### DSLR
When you use a DSLR camera, you can modify it´s configuration to determine, if the picture is stored on the camera´s memory card or in the internal RAM. Notice, that it´s quicker to store the picture in the internal RAM and download it to the raspberry than via the memory card, there will be an additional delay when capturing pictures. You can modify the camera´s configuration via the corresponding python-gphoto2 example "camera-config-gui.py", see python-gphoto2 library.

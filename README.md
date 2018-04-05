# Photobooth
Photobooth with a Raspberry Pi. Two configurations are available: 1) Use of the Raspberry Pi camera, or 2) Use of a DSLR camera.

## Installation
The photobooth software was tested with Raspbian Jessie.

Install necessary dependencies for image handling:

`sudo apt-get install python3 python3-pil.imagetk`

Go to your path where you want to clone the git repository, e.g. `cd Desktop`

`git clone https://github.com/manjan4487/Photobooth.git --branch dslrTest Photobooth`

### Pi camera
Connect your Pi camera to the correct connector on the raspberry pi. Open `sudo raspi-config` and activate the Pi camera in "5 Interfacing Options" -> "P1 Camera"

### DSLR
To use the DSLR configuration you need the gphoto2 lib for python, see https://github.com/jim-easterbrook/python-gphoto2 for installation details (you also need to install the dependencies!).

Short instructions:

`sudo apt-get install libgphoto2-dev pkg-config`

`sudo pip3 install -v gphoto2`

Connect your DSLR via USB to the raspberry pi. Check if your camera is supported by gphoto2, see http://gphoto.org/proj/libgphoto2/support.php

## Configuration
Check the configuration part of the main file to configure the photobooth software for your needs. Note, that you need to set the camera type!

Also, check the comfort configuration part in this readme file.

### Pi camera
There are no special configurations neccesary for the Pi camera.

### DSLR
When you use a DSLR camera, you can modify it´s configuration to determine, if the picture is stored on the camera´s memory card or in the internal RAM. Notice, that it´s quicker to store the picture in the internal RAM and download it to the raspberry than via the memory card, there will be an additional delay when capturing pictures. You can modify the camera´s configuration via the corresponding python-gphoto2 example "camera-config-gui.py", see python-gphoto2 library.

## Comfort Configuration
This part describes a couple of comfort configurations of your raspberry pi to improve the photobooth functionality.

### Autostart the Photobooth Application
There are several ways to start the photobooth application after startup. One simple way ([described here](http://blog.startingelectronics.com/auto-start-a-desktop-application-on-the-rapberry-pi/)) is to use the graphical lxsession autostart.

Short instructions:

`sudo nano /home/pi/.config/lxsession/LXDE-pi/autostart`

Add the line:

`@ /PATH/TO/YOUR/STARTSCRIPT.sh`, e.g. `@ /home/pi/Desktop/Photobooth/start.sh`

If you have problems, a few tips: add permission to the start script `chmod +x start.sh` or `chmod 755 start.sh`

Depending on your Raspbian version you need to edit another autostart script, use google or the linked instruction site.

### Hide mouse cursor
TODO

### Raspberry Pi as Access Point
TODO

### Show captured images on webserver
TODO

### Domain name for Web Access
TODO

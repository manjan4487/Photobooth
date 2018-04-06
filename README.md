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
Install your preferred web gallery or something similar. You can use the [PiGallery](https://github.com/bpatrik/PiGallery), where you find the necessary installation details.

Short instructions:

`sudo apt-get install php5 apache2 php5-gd mysql-server mysql-client php5-mysql` (ignore the mysql packets if you don´t want to use a database)

Download the latest PiGallery Release, decompress it and move it to the `/var/www/` folder. Note, that you need to be root, so just use `sudo` on the command line to move the folder, e.g. `sudo mv /home/pi/Desktop/Gallery/* /var/www/html`. Maybe you need to remove the default index.html in the html folder.

If your setup is fine, you can browse on your pi to `localhost` and should see the configuration page of the PiGallery. Follow the configuration wizard. Some tips for the configuration wizard: you may need to create a link to the image folder of the photobooth application, like `sudo ln -s /home/pi/Desktop/photoboothImages /var/www/html/images`. Note, that you need to create a directory for the thumbnail generation and edit the write permissions of this directory. For me the "Document Root" box is complete empty because the gallery files are directly in the html folder.

If you want to use the database mode, you need to create the initial database, like:

`mysql -u root -p`

`CREATE DATABASE pigallery;`

`exit`

Note, that you need to change the permission, such that the webserver can modify all required files and folders. In worst case, that is absolutely not recommended, you could use `sudo chmod 777 /var/www/html -R` (**not** recommended!). When you have problems in the setup wizard, try to modify the config.php file directly and disable the wizard, this worked for me.

### Domain name for Web Access
TODO

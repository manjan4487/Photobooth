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

Disable auto-mount such that gphoto2 can access your camera, like:

```
sudo rm /usr/share/dbus-1/services/org.gtk.Private.GPhoto2VolumeMonitor.service
sudo rm /usr/share/gvfs/mounts/gphoto2.mount
sudo rm /usr/share/gvfs/remote-volume-monitors/gphoto2.monitor
sudo rm /usr/lib/gvfs/gvfs-gphoto2-volume-monitor
```

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

### Raspberry Pi as Access Point
I followed the instruction for this [Access Point Guide (german)](https://forum-raspberrypi.de/forum/thread/6902-raspberry-pi-accesspoint-mit-lokalem-webserver-betreiben/).

Short instructions:

Install the required packets: `sudo apt-get install hostapd udhcpd`

Now, edit the DHCP configuration in `sudo nano /etc/udhcpd.conf` like:

```
# Address area
start 192.168.0.2
end 192.168.0.254
# Interface
interface wlan0
remaining yes
# DNS and subnet
opt dns 8.8.8.8 4.2.2.2
opt subnet 255.255.255.0
# Adresse Router
opt router 192.168.0.1
# Leasetime in seconds (7 days)
opt lease 604800
```

Edit the folloing line in file `sudo nano /etc/default/udhcpd` to `#DHCPD_ENABLED="no"`

Change the static ip configuration of the pi via `sudo nano /etc/network/interfaces` to

```
auto lo
iface lo inet loopback
iface eth0 inet dhcp
iface wlan0 inet static
  address 192.168.0.1
  netmask 255.255.255.0
``` 

Now we need to configure the access point `sudo nano /etc/hostapd/hostapd.conf`:

```
interface=wlan0
driver=nl80211
ssid=RPI_AP
hw_mode=g
channel=6
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=secretphrase
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

Change the config file for the access point `sudo nano /etc/default/hostapd` to

`DAEMON_CONF="/etc/hostapd/hostapd.conf"`

After a reboot, you should be able to access the webserver via 192.168.0.1 from your pi and from other wifi devices.

### Show captured images on webserver
Install your preferred web gallery or something similar. You can use the [PiGallery](https://github.com/bpatrik/PiGallery), where you find the necessary installation details.

Short instructions:

`sudo apt-get install php5 apache2 php5-gd mysql-server mysql-client php5-mysql` (ignore the mysql packets if you don´t want to use a database)

Download the latest PiGallery Release, decompress it and move it to the `/var/www/` folder. Note, that you need to be root, so just use `sudo` on the command line to move the folder, e.g. `sudo mv /home/pi/Desktop/Gallery/* /var/www/html`. Maybe you need to remove the default index.html in the html folder.

If your setup is fine, you can browse on your pi to `localhost` and should see the configuration page of the PiGallery. Follow the configuration wizard. Some tips for the configuration wizard: you may need to create a link to the image folder of the photobooth application, like `sudo ln -s /home/pi/Desktop/photoboothImages /var/www/html/images`. Note, that you need to create a directory for the thumbnail generation and edit the write permissions of this directory. For me the "Document Root" box is complete empty because the gallery files are directly in the html folder.

Note, that you need to change the permission, such that the webserver can modify all required files and folders. In worst case, that is absolutely not recommended, you could use `sudo chmod 777 /var/www/html -R` (**not** recommended!). When you have problems in the setup wizard, try to modify the config.php file directly and disable the wizard, this worked for me.

If you get mysql errors, the file permission may be still be wrong! The setup wizard did all mysql initializations when the file permissions were correct (for the web user).

### Domain name for Web Access
Modify the hosts file on the pi `sudo nano /etc/hosts` and add the line `127.0.1.1 photobooth`. If you have problems accessing the webserver via this domain name, you need to google for further information. After adding this line I could access the webserver by visiting `http://photobooth`, note the http as prefix. For a domain like style you need to find out yourself.

### Include RTC for correct system time
If you use the raspberry pi as access point, you will need to set the system time every time after a reboot. As alternative you can add a GPS time module or a RTC module. To include a rtc module to the raspberry pi, you will need a hardware rtc module. Connect the rtc module, after that you can follow the [instructions](https://www.raspberrypi.org/forums/viewtopic.php?p=845588#p845588) to include the correct time measurement to the os.

### Disable energy saving mode
If you want to disable the screensaver and power saving mode, edit the file /etc/lightdm/lightdm.conf and uncomment the line `x-server-command` line **under** `SeatDefaults`. Edit the line to `xserver-command=X -s 0 -dpms` (or `xserver-command=X -nocursor -s 0 -dpms` when you want to hide the mouse cursor).

### Hide mouse cursor
If you want to hide the mouse cursor the whole time, you can simply edit the file /etc/lightdm/lightdm.conf and uncomment the line `x-server-command` line **under** `SeatDefaults`. Edit the line to `xserver-command=X -nocursor` (or `xserver-command=X -nocursor -s 0 -dpms` when you want to disable energy saving modes).

If you just want to hide the cursor when you do not move the mouse, try [uncutter](https://jackbarber.co.uk/blog/2017-02-16-hide-raspberry-pi-mouse-cursor-in-raspbian-kiosk). But check out if it´s ok, when you use the mouse button to capture a new image.

### Highly recommended
It is highly recommended to backup your complete configured photobooth raspbian distribution. You can use [Pi-Clone](https://github.com/billw2/rpi-clone) to backup your whole sd card to another one. You can even use another sd card size for the backup!

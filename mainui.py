'''
Created on 29.01.2018

@author: MJ
edited by KS
'''

CAMERA_PI = 0 # do not edit!
CAMERA_DSLR = 1 # do not edit!

# EDIT HERE
# CAMERA can be either CAMERA_PI or CAMERA_DSLR
CAMERA = CAMERA_DSLR

VERSION = 0.01


from tkinter import *
import PIL.Image
from PIL import ImageOps
import glob
import PIL.ImageTk
from random import randint
import _thread
import threading
import sys
import os
import logging
if CAMERA == CAMERA_PI:
    from picamera import PiCamera
elif CAMERA == CAMERA_DSLR:
    import gphoto2 as gp
from time import sleep
import time

if sys.version_info[0] == 2:  # Just checking your Python version to import Tkinter properly.
    from Tkinter import *
else:
    from tkinter import *


class Fullscreen_Window:

    image_list = []
    PHOTO_PATH = '/home/pi/Desktop/fotoboxImages/*.jpg' # change it to your own location!
    folder = '/home/pi/Desktop/fotoboxImages/'
    PHOTO_CHANGE_TIME = 4000 # Defines the timing of changing the ImageView in milliseconds
    SCREEN_RESOLUTION = (1920,1080) # (height,width)
    
    lockVar = False
    takePictureVar = False


    def __init__(self):
        self.tk = Tk()
        self.frame = Frame(self.tk)
        self.frame.pack()
        self.state = True
        self.tk.attributes("-fullscreen", self.state)
        self.tk.bind("<F11>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        self.tk.bind("<Button-1>", self.take_picture)
        self.panel = Label(self.tk)#
        self.panel.pack(side = "bottom", fill = "both", expand = "yes")
        self.update_ImageListForRandPreview()
        self.tk.mainloop()
        
    def take_picture(self, event=None):
        Fullscreen_Window.takePictureVar = True
        return "break"
    
    def toggle_fullscreen(self, event=None):
        self.state = not self.state
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"
        
    def update_ImageListForRandPreview(self):
        if not self.lockVar:
            # Get all Images in photoPath
            for filename in glob.glob(self.PHOTO_PATH):
                
                    self.im=PIL.Image.open(filename)
                    self.image_list.append(self.im.filename)
                
        if len(self.image_list) > 0:
            
            # Calc. random number for Image which has to be shown
            self.randomnumber = randint(0, len(self.image_list)-1)
            
            #Resize Image, so all Images have the same size
            self.resizedImg = ImageOps.fit(PIL.Image.open(self.image_list[self.randomnumber]), self.SCREEN_RESOLUTION)
            #Load the resized Image with PhotoImage
            self.resizedImg = PIL.ImageTk.PhotoImage(self.resizedImg)
            #Put the image into the Panel object
            self.panel.configure(image = self.resizedImg)
            #Maximize the Panel View
            self.panel.pack(side = "bottom", fill = "both", expand = "yes")

        #Update Timer
        self.tk.after(self.PHOTO_CHANGE_TIME, self.update_ImageListForRandPreview)

    def camTask(self):
        print("Photobooth v%s started" % VERSION)
        
        photoCount = 1
        
        if CAMERA == CAMERA_PI:
            mycam = PiCamera()

            #Setup camera parameters
            mycam.resolution = (3280,2464)
            #mycam.framerate = (30)
            mycam.sharpness = 0
            mycam.contrast = 0
            mycam.brightness = 50
            mycam.saturation = 0
            mycam.ISO = 0
            mycam.video_stabilization = False
            mycam.exposure_compensation = 0
            mycam.exposure_mode = 'auto'
            mycam.meter_mode = 'average'
            mycam.awb_mode = 'auto'
            mycam.image_effect = 'none'
            mycam.color_effects = None
            mycam.rotation = 0
            mycam.hflip = True
            mycam.vflip = True
            mycam.crop = (0.0, 0.0, 1.0, 1.0)
        elif CAMERA == CAMERA_DSLR:
            context = gp.Context()
            camera = gp.Camera()
            camera.init(context)
            text = camera.get_summary(context)
            if error:
                print("Failure while getting camera information")
            else:
                print('Summary')
                print('=======')
                print(text.text)
            error = gp.gp_camera_exit(camera, myDslr)
            

        while 1:
            
            #button_takePhoto.wait_for_press()
            while self.takePictureVar is not True:
                sleep(0.2)

            # setze globale Variable zurueck 
            self.takePictureVar = False
            
            now = time.strftime("%Y%m%d_%H-%M-%S")
            
            file = "%s_NUM_%s.jpg" % (now,photoCount)
            imgPath = "%s%s" % (self.folder,file)
            
            if CAMERA == CAMERA_PI:
                mycam.annotate_text_size=96

                mycam.start_preview(resolution=(self.SCREEN_RESOLUTION))
            elif CAMERA == CAMERA_DSLR:
                sleep(0.1) # TODO

            for i in range(6):
                if CAMERA == CAMERA_PI:
                    mycam.annotate_text = "%s" % (5-i)
                elif CAMERA == CAMERA_DSLR:
                    sleep(0.1) # TODO
                i = i-1
                sleep(1)
                
            if CAMERA == CAMERA_PI:
                mycam.annotate_text = ""
            elif CAMERA == CAMERA_DSLR:
                sleep(0.1) # TODO
                
            self.lockVar = True
            myfile = open(imgPath,'wb')
            
            if CAMERA == CAMERA_PI:
                mycam.capture(myfile,format='jpeg',quality=100,thumbnail=(64,48,35))
            elif CAMERA == CAMERA_DSLR:
                camera.Capture(context)
                camera.file_get(folder,file,'jpeg',context)
                
            sleep(0.1)
            myfile.close()
            self.lockVar=False
            
            if CAMERA == CAMERA_PI:
                mycam.stop_preview()
            elif CAMERA == CAMERA_DSLR:
                sleep(0.1) # TODO
            
            photoCount = photoCount +1

if __name__ == '__main__':

    try:
        
        #Starting Camera Thread
        _thread.start_new_thread(Fullscreen_Window.camTask,(Fullscreen_Window,))
        #Starting Gallery View
        _thread.start_new_thread(Fullscreen_Window(),(Fullscreen_Window,))
   

    except:
        print ("Error") 
    


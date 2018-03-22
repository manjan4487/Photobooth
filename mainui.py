'''
Created on 29.01.2018

@author: MJ
edited by KS
'''

# Script version
VERSION = 0.02

# do not edit the following lines
CAMERA_PI = 0
CAMERA_DSLR = 1


##### EDIT HERE ######
# CAMERA can be either CAMERA_PI or CAMERA_DSLR
CAMERA = CAMERA_DSLR

# Defines the timing of changing the ImageView in the slideshow in milliseconds
PHOTO_CHANGE_TIME = 4000

SCREEN_RESOLUTION = (1920,1080) # (height,width)

# folder path, where new pictures will be saved
PHOTO_PATH = '/home/pi/Desktop/fotoboxImages/'

# folder path, where corrupted pictures will be moved to such that never a picture could be erased in failure case
TEMP_TRASH_FOLDER = '/home/pi/Desktop/fotoboxImages/_temporaryTrash/'

# countdown that ticks down when button/event was pressed/occured
COUNTDOWN_S = 0

##### edit stop


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
            for filename in glob.glob("%s*.jpg" % PHOTO_PATH):
                
                    self.im=PIL.Image.open(filename)
                    self.image_list.append(self.im.filename)
                
        if len(self.image_list) > 0:
            
            # Calc. random number for Image which has to be shown
            self.randomnumber = randint(0, len(self.image_list)-1)
            
            #Resize Image, so all Images have the same size
            self.resizedImg = ImageOps.fit(PIL.Image.open(self.image_list[self.randomnumber]), SCREEN_RESOLUTION)
            #Load the resized Image with PhotoImage
            self.resizedImg = PIL.ImageTk.PhotoImage(self.resizedImg)
            #Put the image into the Panel object
            self.panel.configure(image = self.resizedImg)
            #Maximize the Panel View
            self.panel.pack(side = "bottom", fill = "both", expand = "yes")

        #Update Timer
        self.tk.after(PHOTO_CHANGE_TIME, self.update_ImageListForRandPreview)

    def camTask(self):
        print("Photobooth v%s started" % VERSION)
        
        # do some initialization stuff
        # check if the folders already exist
        if not os.path.exists(PHOTO_PATH):
            os.makedirs(PHOTO_PATH)
        if not os.path.exists(TEMP_TRASH_FOLDER):
            os.makedirs(TEMP_TRASH_FOLDER)
        
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
            # configure gphoto loggin
            logging.basicConfig(format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
            gp.check_result(gp.use_python_logging())
            camera = gp.check_result(gp.gp_camera_new())
            gp.check_result(gp.gp_camera_init(camera))
            text = gp.check_result(gp.gp_camera_get_summary(camera))
            
            print('Summary')
            print('=======')
            print(text.text)
            
            # TODO man könnte periodisch testen, ob eine Kamera
            # angeschlossen ist und diese dann ggf. initialisieren
            # dann lässt sich das System auch gestartet noch weiter verwenden
            # (vor allem falls der Akku zwischenzeitlich mal getauscht werden muss!)
            # und dann natürlich auch mit exception abfangen!

        while 1:
            
            #button_takePhoto.wait_for_press()
            while self.takePictureVar is not True:
                sleep(0.2)

            # setze globale Variable zurueck 
            self.takePictureVar = False
            
            now = time.strftime("%Y%m%d_%H-%M-%S")
            
            file = "%s_NUM_%s.jpg" % (now,photoCount)
            imgPath = "%s%s" % (PHOTO_PATH,file)
            
            if CAMERA == CAMERA_PI:
                mycam.annotate_text_size=96

                mycam.start_preview(resolution=(SCREEN_RESOLUTION))
            elif CAMERA == CAMERA_DSLR:
                sleep(0.1)
                
                # TODO bei DSLRs mit LivePreview diese Vorschau hier einbinden

            for i in range(COUNTDOWN_S):
                if CAMERA == CAMERA_PI:
                    mycam.annotate_text = "%s" % (COUNTDOWN_S-1-i)
                elif CAMERA == CAMERA_DSLR:
                    sleep(0.1)
                    
                    # TODO zeige hier auf einem zu definierenden Hintergrund den Countdown an
                    # (falls kein LivePreview verfügbar ist)
                    
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
                try:
                    cameraFilePath = gp.check_result(gp.gp_camera_capture(camera, gp.GP_CAPTURE_IMAGE))
                    cameraFile = gp.check_result(gp.gp_camera_file_get(camera, cameraFilePath.folder, cameraFilePath.name, gp.GP_FILE_TYPE_NORMAL))
                    gp.check_result(gp.gp_file_save(cameraFile, imgPath))
                except gp.GPhoto2Error:
                    print("Could not capture image!")
                    
                    # TODO show a notice on the screen (overlay)
                    
                    # be sure that there is no corrupted image file, so move the file to temporary trash
                    tempTrashPath = "%sTRASH_%s" % (TEMP_TRASH_FOLDER, file)
                    os.rename(imgPath, tempTrashPath)
                
            sleep(0.1)
            myfile.close()
            self.lockVar = False
            
            if CAMERA == CAMERA_PI:
                mycam.stop_preview()
            elif CAMERA == CAMERA_DSLR:
                sleep(0.1)
                # TODO ggf. die livePreview stoppen
            
            photoCount = photoCount +1

if __name__ == '__main__':

    try:
        
        #Starting Camera Thread
        _thread.start_new_thread(Fullscreen_Window.camTask,(Fullscreen_Window,))
        #Starting Gallery View
        _thread.start_new_thread(Fullscreen_Window(),(Fullscreen_Window,))
   

    except:
        print ("Error") 
    


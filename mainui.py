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

# Defines the timing of changing the ImageView in the slideshow in seconds
SLIDESHOW_CHANGE_TIME_S = 4

SCREEN_RESOLUTION = (1280,960) #(1920,1080) # (height,width)

# folder path, where new pictures will be saved
PHOTO_PATH = '/home/pi/Desktop/fotoboxImages/'

# folder path, where corrupted pictures will be moved to such that never a picture could be erased in failure case
TEMP_TRASH_FOLDER = '/home/pi/Desktop/fotoboxImages/_temporaryTrash/'

# countdown that ticks down when button/event was pressed/occured (in s)
COUNTDOWN_S = 5 # e.g. 5 means countdown goes in range [4,3,2,1,0]

# choose a countdown style. Style name is used in PNG files like "Countdown_%s_x.png" % COUNTDOWN_STYLE, see COUNTDOWN_FORMAT
# You can create your own style: name the new files with the style name you have chosen here
COUNTDOWN_STYLE = 'classic'

# the folder with the countdown images
COUNTDOWN_IMAGE_FOLDER = '/home/pi/Desktop/Photobooth/images/countdown/'

# the time that a captured image is displayed until the slideshow continues
TIME_TO_SHOW_CAPTURED_IMAGE = 8

# time between two digits of the countdown (in s)
DELAY_BETWEEN_COUNTDOWN = 1

# define if the live preview should be used if available (Pi Cam and a few DSLR cameras support live preview)
TRY_TO_USE_LIVE_PREVIEW = False

# background image to show if there is no live preview shown
BACKGROUND_PICTURE = '/home/pi/Desktop/Photobooth/images/background/Background_Coo.jpg'

# activates a grayscale effect on the background image
BACKGROUND_EFFECT_GRAYSCALE = True

##### edit stop

##### DEVELOPER EDIT START #####
# refresh time to check if we need to set a new picture to the front
PERIOD_PICTURE_REFRESH = 15 # in ms

# file format used to find the countdown pictures
# first argument has to be the COUNTDOWN_STYLE and the second the number of the countdown
COUNTDOWN_FORMAT = '%sCountdown_%s_%s.png' # % (COUNTDOWN_IMAGE_FOLDER,COUNTDOWN_STYLE,i)

# time difference to the delay between two countdown iterations to refresh the display
# value was found by testing
COUNTDOWN_REFRESH_DELTA = 0.4

##### developer edit stop

##### CONSTANTS #####
STATE_SLIDESHOW_IDLE         = 0
STATE_SLIDESHOW_BACKGROUND   = 1
STATE_SLIDESHOW_CAPTURED_IMG = 2

COUNTDOWN_WIDTH_FACTOR = 1.5
COUNTDOWN_HEIGHT_FACTOR = 1.5

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
import time

if sys.version_info[0] == 2:  # Just checking your Python version to import Tkinter properly.
    from Tkinter import *
else:
    from tkinter import *


class Fullscreen_Window:

    image_list = []    
    lockVar = False
    takePictureVar = False
    StateSlideshow = STATE_SLIDESHOW_IDLE
    Countdown = 0
    LastChangeTimeSlideshow = 0
    LastChangeTimeCountdown = 0
    CapturedImage = 0

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
        
        if CAMERA == CAMERA_DSLR:
            # configure gphoto logging
            logging.basicConfig(format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
            gp.check_result(gp.use_python_logging())
            self.checkForCameraDslr() # start periodical called function# TODO bei DSLRs mit LivePreview diese Vorschau hier einbinden

        print("Photobooth v%s started" % VERSION)
        
        # check if the folders already exist
        if not os.path.exists(PHOTO_PATH):
            os.makedirs(PHOTO_PATH)
        if not os.path.exists(TEMP_TRASH_FOLDER):
            os.makedirs(TEMP_TRASH_FOLDER)
        
        self.tk.mainloop()
        
    def take_picture(self, event=None): # gets called by button-1 (left mouse button)
        Fullscreen_Window.takePictureVar = True
        return "break" # TODO umschaltbar machen zwischen GPIO button und maus taste
    
    def toggle_fullscreen(self, event=None):
        self.state = not self.state
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"
        
    def update_ImageListForRandPreview(self):
        if self.StateSlideshow == STATE_SLIDESHOW_IDLE: # show slideshow
            now = time.time()
            if now - self.LastChangeTimeSlideshow > SLIDESHOW_CHANGE_TIME_S:
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
                    
                self.LastChangeTimeSlideshow = time.time() # store time for next iteration
                
        elif self.StateSlideshow == STATE_SLIDESHOW_BACKGROUND: # show background
            now = time.time()
            if now - self.LastChangeTimeCountdown > (DELAY_BETWEEN_COUNTDOWN - COUNTDOWN_REFRESH_DELTA):
                #Resize Image, so all Images have the same size
                self.resizedImg = ImageOps.fit(PIL.Image.open(BACKGROUND_PICTURE), SCREEN_RESOLUTION)
                
                if BACKGROUND_EFFECT_GRAYSCALE: # may use a grayscale effect
                    self.resizedImg = ImageOps.grayscale(self.resizedImg)
                
                # nun den Countdown einblenden
                numberPic = PIL.Image.open(COUNTDOWN_FORMAT % (COUNTDOWN_IMAGE_FOLDER,COUNTDOWN_STYLE,self.Countdown))
                numberPic = numberPic.resize((int(SCREEN_RESOLUTION[0]/COUNTDOWN_WIDTH_FACTOR),int(SCREEN_RESOLUTION[1]/COUNTDOWN_HEIGHT_FACTOR)))
                self.resizedImg.paste(numberPic, (int(SCREEN_RESOLUTION[0]/2-SCREEN_RESOLUTION[0]/COUNTDOWN_WIDTH_FACTOR/2),int(SCREEN_RESOLUTION[0]/2-SCREEN_RESOLUTION[0]/COUNTDOWN_HEIGHT_FACTOR/2)), numberPic)
                    
                #Load the resized Image with PhotoImage
                self.resizedImg = PIL.ImageTk.PhotoImage(self.resizedImg)
                #Put the image into the Panel object
                self.panel.configure(image = self.resizedImg)
                #Maximize the Panel View
                self.panel.pack(side = "bottom", fill = "both", expand = "yes")
                
                self.LastChangeTimeCountdown = time.time() # store time for next iteration
                
        elif self.StateSlideshow == STATE_SLIDESHOW_CAPTURED_IMG: # show the captured picture
            if self.CapturedImage != 0: # if a picture was captured
                #Resize Image, so all Images have the same size
                self.resizedImg = ImageOps.fit(PIL.Image.open(self.CapturedImage), SCREEN_RESOLUTION)
                #Load the resized Image with PhotoImage
                self.resizedImg = PIL.ImageTk.PhotoImage(self.resizedImg)
                #Put the image into the Panel object
                self.panel.configure(image = self.resizedImg)
                #Maximize the Panel View
                self.panel.pack(side = "bottom", fill = "both", expand = "yes")

        #Update Timer
        self.tk.after(PERIOD_PICTURE_REFRESH, self.update_ImageListForRandPreview)

    def camTask(self):
        livepreview = False
        
        if CAMERA == CAMERA_PI: # TODO in init function packen
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
            
            livepreview = True
            
        elif CAMERA == CAMERA_DSLR:
            livepreview = False # false by default. Only a few cameras support live preview

        while 1:
            
            #button_takePhoto.wait_for_press()
            while self.takePictureVar is not True:
                time.sleep(0.1)

            # setze globale Variable zurueck 
            self.takePictureVar = False
            
            now = time.strftime("%Y%m%d_%H-%M-%S")
            
            file = "%s.jpg" % now
            imgPath = "%s%s" % (PHOTO_PATH,file)
            
            ###### INITIALIZE CAMERAS WHILE RUN TIME
            if CAMERA == CAMERA_DSLR:
                try:
                    self.camera = gp.check_result(gp.gp_camera_new())
                    gp.check_result(gp.gp_camera_init(self.camera))
                    #text = gp.check_result(gp.gp_camera_get_summary(self.camera))
                    if False: # TODO: prüfen, ob livepreview available ist
                        self.livepreview = True # TODO start livepreview
                except:
                    print('Could not find any DSLR camera')
                    # TODO auch dem Nutzer anzeigen! Overlay?!
            
            ###### CHECK IF WE NEED TO SHOW LIVE PREVIEW OR BACKGROUND
            livepreviewavailable = False
            if TRY_TO_USE_LIVE_PREVIEW:
                if livepreview:
                    livepreviewavailable = True
                    
            # change the shown picture to the background
            self.StateSlideshow = STATE_SLIDESHOW_BACKGROUND
            
            ###### START LIVE PREVIEW OR SHOW BACKGROUND IMAGE
            # TODO über andren thread lösen
            if livepreviewavailable:
                if CAMERA == CAMERA_PI:
                    mycam.annotate_text_size=96
                    mycam.start_preview(resolution=(SCREEN_RESOLUTION))
                elif CAMERA == CAMERA_DSLR:
                    pass # TODO start live preview
            else:
                # picture = PIL.Image.open(BACKGROUND_PICTURE)
                pass # TODO über andren thread lösen

            ###### COUNTDOWN LOOP
            for i in range(COUNTDOWN_S):
                        
                if livepreviewavailable:
                    if CAMERA == CAMERA_PI:
                        mycam.annotate_text = "%s" % (COUNTDOWN_S - i - 1)
                    elif CAMERA == CAMERA_DSLR:
                        pass # TODO
                else: # background is displayed by other thread
                    self.Countdown = COUNTDOWN_S - i - 1 # just set the used countdown
                    
                # handle the delay per iteration
                if CAMERA == CAMERA_PI:
                    # Pi camera captures image immediately, so we can wait the complete countdown
                    sleep(DELAY_BETWEEN_COUNTDOWN)
                elif CAMERA == CAMERA_DSLR:
                    # dslr cameras need a little to capture image, so skip the last delay
                    if i != COUNTDOWN_S:
                        time.sleep(DELAY_BETWEEN_COUNTDOWN)
                        
            
            ###### POST LIVE PREVIEW
            if livepreviewavailable:
                if CAMERA == CAMERA_PI:
                    mycam.annotate_text = ""
                elif CAMERA == CAMERA_DSLR:
                    pass # TODO
                
            self.lockVar = True
            self.CapturedImage = 0
            myfile = open(imgPath,'wb')
            self.CapturedImage = imgPath
            
            if CAMERA == CAMERA_PI:
                mycam.capture(myfile,format='jpeg',quality=100,thumbnail=(64,48,35))
            elif CAMERA == CAMERA_DSLR:
                try:
                    cameraFilePath = gp.check_result(gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE))
                    cameraFile = gp.check_result(gp.gp_camera_file_get(self.camera, cameraFilePath.folder, cameraFilePath.name, gp.GP_FILE_TYPE_NORMAL))
                    gp.check_result(gp.gp_file_save(cameraFile, imgPath))
                except gp.GPhoto2Error:
                    print("Could not capture image!")
                    # TODO show a notice on the screen (overlay)
                    
                    # be sure that there is no corrupted image file, so move the file to temporary trash
                    tempTrashPath = "%sTRASH_%s" % (TEMP_TRASH_FOLDER, file)
                    os.rename(imgPath, tempTrashPath)
                    self.CapturedImage = 0 # we can not show a captured image on the screen
                
            myfile.close()
            self.lockVar = False
            
            if livepreviewavailable:
                if CAMERA == CAMERA_PI:
                    mycam.stop_preview()
                elif CAMERA == CAMERA_DSLR:
                    pass # TODO ggf. die livePreview stoppen
            
            ###### SHOW THE CAPUTRED IMAGE
            self.StateSlideshow = STATE_SLIDESHOW_CAPTURED_IMG
            time.sleep(TIME_TO_SHOW_CAPTURED_IMAGE)
            
            ###### CONTINUE WITH SLIDESHOW
            self.StateSlideshow = STATE_SLIDESHOW_IDLE
        
if __name__ == '__main__':

    try:
        
        #Starting Camera Thread
        _thread.start_new_thread(Fullscreen_Window.camTask,(Fullscreen_Window,))
        #Starting Gallery View
        _thread.start_new_thread(Fullscreen_Window(),(Fullscreen_Window,))
   

    except:
        print ("Error") 
    


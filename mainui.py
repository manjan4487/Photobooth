'''
Created on 29.01.2018

@author: MJ
edited by KS
'''

# Script version
VERSION = 0.04

# do not edit the following lines
CAMERA_PI = 0
CAMERA_DSLR = 1


##### EDIT HERE ######
# CAMERA can be either CAMERA_PI or CAMERA_DSLR
CAMERA = CAMERA_DSLR

# Defines the timing of changing the ImageView in the slideshow in seconds
SLIDESHOW_CHANGE_TIME_S = 4

SCREEN_RESOLUTION = (1680,1050)#(1280,960) #(1920,1080) # (height,width)

PHOTOBOOTH_PATH = '/home/pi/Desktop/Photobooth/'

# folder path, where new pictures will be saved
# info: if folder does not exist, the folder will be created
PHOTO_PATH = '/home/pi/Desktop/PhotoboothPictures/'

# if activated, the captured image is stored on the camera while displaying the image on the screen (so no delay will occur)
# Note, that this did not work with my Nikon D60!
DSLR_STORE_PICTURE_ON_CAMERA = False
CAMERA_FOLDER = '/Event0/'

# stores the captured picture also on the first usb device that is found
STORE_PICTURE_ALSO_ON_USB_DEVICE = True
USB_DEVICE_MOUNT_POINT = '/media/pi/'
BKP_DEVICE_FOLDER_ON_USB_DEVICE = '/Event0/'

# folder path, where corrupted pictures will be moved to such that never a picture could be erased in failure case
# info: if folder does not exist, the folder will be created
TEMP_TRASH_FOLDER = '/home/pi/Desktop/_temporaryTrash/'

# countdown that ticks down when button/event was pressed/occured (in s)
COUNTDOWN_S = 3 # e.g. 5 means countdown goes in range [4,3,2,1,0] + the first digit is shown while the camera is initialized

# choose a countdown style. Style name is used in PNG files like "Countdown_%s_x.png" % COUNTDOWN_STYLE, see COUNTDOWN_FORMAT
# You can create your own style: name the new files with the style name you have chosen here
COUNTDOWN_STYLE = 'classic'

# the folder with the countdown images
COUNTDOWN_IMAGE_FOLDER = PHOTOBOOTH_PATH + 'images/countdown/'

# the time that a captured image is displayed until the slideshow continues
TIME_TO_SHOW_CAPTURED_IMAGE = 8

# time between two digits of the countdown (in s)
DELAY_BETWEEN_COUNTDOWN = 0.9

# define if the live preview should be used if available (Pi Cam and a few DSLR cameras support live preview)
TRY_TO_USE_LIVE_PREVIEW = False

# background image to show if there is no live preview shown
BACKGROUND_PICTURE = PHOTOBOOTH_PATH + 'images/background/Background_Wine_un_trans40.jpg'

# activates a grayscale effect on the background image
# info: you should edit the background picture on a pc with all effects you want to
BACKGROUND_EFFECT_GRAYSCALE = False

# activates a blur effect on the background image
# info: you should edit the background picture on a pc with all effects you want to
BACKGROUND_EFFECT_BLUR = False

# with these factors you can determine the size of the overlayed countdown pictures
# factor = 1.0 means that the size is equivalent to the screen resolution (still depends
# on the original picture size)
# factors < 1.0 are possible as well
COUNTDOWN_WIDTH_FACTOR = 2.8
COUNTDOWN_HEIGHT_FACTOR = 1.5

# offset of the overlay of the countdown digits in x and y coordinates
# Info: position of the overlay picture is calculated by the desired resolution
#       but this is an additional offset to optimize the visible part of the picture
#       and not only the pictures resolution (can differ from the real visible part)
COUNTDOWN_OVERLAY_OFFSET_X = 0
COUNTDOWN_OVERLAY_OFFSET_Y = 0

# define if you want to use a button/switch to shutdown the raspberry pi properly
SHUTDOWN_GPIO_USE = True
SHUTDOWN_GPIO_PIN = 22 # in BCM Style (GPIO x)
SHUTDOWN_GPIO_POLARITY = True # False for GPIO.FALLING, True for GPIO.RISING
SHUTDOWN_GPIO_PULL = False # if True: pull_up if polarity is falling, pull_down if polarity is raising, else no pull

# information text that is shown during runtime
INFORMATION_TEXT = "Picture access in WIFI 'Photobooth':\nhttp://photobooth"
INFORMATION_TEXT_X = SCREEN_RESOLUTION[0] - 200
INFORMATION_TEXT_Y = SCREEN_RESOLUTION[1] - 28
INFORMATION_TEXT_FONT = ('Arial','16')
INFORMATION_TEXT_WIDTH = "300p"

FAILURE_TEXT_WIDTH = "360p"
FAILURE_TEXT_X = SCREEN_RESOLUTION[0] - 250
FAILURE_TEXT_Y = SCREEN_RESOLUTION[1] - 130
FAILURE_TEXT_FONT = ('Arial','22')
FAILURE_TEXT_COLOR = "red"

# configuration for logging
LOGGING_ACTIVE = True
LOGGING_FILE_PREFIX = "photobooth_log_" # the ctime at script start is added to the log file *.log
LOGGING_FILE_FOLDER = "/home/pi/Desktop/"


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


from tkinter import *
import PIL.Image
from PIL import ImageOps
from PIL import ImageFilter
from PIL import ImageEnhance
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
if SHUTDOWN_GPIO_USE: # TODO or when a gpio is used to capture an image
    import RPi.GPIO as GPIO
    from subprocess import call
import time
if STORE_PICTURE_ALSO_ON_USB_DEVICE:
    from shutil import copyfile
if LOGGING_ACTIVE:
    import logging

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
    BackgroundImage = 0
    TextFailure = ""
    ShutdownRequest = False

    def __init__(self):
        self.tk = Tk()
        self.state = True
        self.tk.attributes("-fullscreen", self.state)
        self.tk.bind("<F11>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        self.tk.bind("<Button-1>", self.take_picture)
        self.canvas = Canvas(self.tk, width=SCREEN_RESOLUTION[0],height=SCREEN_RESOLUTION[1],highlightthickness=0,bd=0,bg="black")
        self.canvas.pack(fill=BOTH, expand=YES)
        
        if LOGGING_ACTIVE:
            logging.basicConfig(filename=LOGGING_FILE_FOLDER + LOGGING_FILE_PREFIX + time.ctime() + ".log", format='%(asctime)s: %(levelname)s: %(message)s', level=logging.INFO)
            
            if CAMERA == CAMERA_DSLR:
                # configure gphoto logging
                gp.check_result(gp.use_python_logging())

        logging.info("Photobooth v%s started", VERSION)
        
        logging.info("Camera type: ")
        if CAMERA == CAMERA_DSLR:
            logging.info("DSLR")
        elif CAMERA == CAMERA_PI:
            logging.info("Pi")
        else:
            logging.warning("Unknown! Set a correct camera type!")
        
        # check if the folders already exist
        if not os.path.exists(PHOTO_PATH):
            os.makedirs(PHOTO_PATH)
        if not os.path.exists(TEMP_TRASH_FOLDER):
            os.makedirs(TEMP_TRASH_FOLDER)
            
        # create background image with effect once in init
        self.BackgroundImage = ImageOps.fit(PIL.Image.open(BACKGROUND_PICTURE), SCREEN_RESOLUTION)
                
        if BACKGROUND_EFFECT_GRAYSCALE: # may use a grayscale effect
            self.BackgroundImage = ImageOps.grayscale(self.BackgroundImage)
                
        if BACKGROUND_EFFECT_BLUR: # may use the blur effect
            self.BackgroundImage = self.BackgroundImage.filter(ImageFilter.BLUR)
            
        self.update_ImageListForRandPreview()
        
        if SHUTDOWN_GPIO_USE:
            GPIO.setmode(GPIO.BCM)
            if SHUTDOWN_GPIO_POLARITY:
                polarity = GPIO.RISING
            else:
                polarity = GPIO.FALLING
            if SHUTDOWN_GPIO_PULL:
                if SHUTDOWN_GPIO_POLARITY:
                    pull = GPIO.PUD_DOWN
                else:
                    pull = GPIO.PUD_UP
                GPIO.setup(SHUTDOWN_GPIO_PIN, GPIO.IN, pull_up_down=pull)
            else:
                GPIO.setup(SHUTDOWN_GPIO_PIN, GPIO.IN)
            GPIO.add_event_detect(SHUTDOWN_GPIO_PIN, polarity, callback=self.shutdownButtonEvent, bouncetime=200)
        
        self.tk.mainloop()
        
    def shutdownButtonEvent(self, channel):
        if SHUTDOWN_GPIO_USE:
            if channel == SHUTDOWN_GPIO_PIN:
                logging.warning("Shutting down request via GPIO PIN. Shutting down now...")
                Fullscreen_Window.ShutdownRequest = True
        
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
                    
                    # Resize Image, so all Images have the same size
                    self.resizedImg = ImageOps.fit(PIL.Image.open(self.image_list[self.randomnumber]), SCREEN_RESOLUTION)
                    # Load the resized Image with PhotoImage
                    self.resizedImg = PIL.ImageTk.PhotoImage(self.resizedImg)
                    # Put the image into the canvas object
                    self.canvas.create_image(0,0,anchor=NW,image=self.resizedImg)
                    
                    # refresh overlayed text
                    self.canvas.create_text(INFORMATION_TEXT_X,INFORMATION_TEXT_Y,text=INFORMATION_TEXT,font=INFORMATION_TEXT_FONT,width=INFORMATION_TEXT_WIDTH)
                    self.canvas.create_text(FAILURE_TEXT_X,FAILURE_TEXT_Y,text=self.TextFailure,font=FAILURE_TEXT_FONT,fill=FAILURE_TEXT_COLOR,width=FAILURE_TEXT_WIDTH)
                    
                self.LastChangeTimeSlideshow = time.time() # store time for next iteration
                
        elif self.StateSlideshow == STATE_SLIDESHOW_BACKGROUND: # show background
            now = time.time()
            if now - self.LastChangeTimeCountdown > (DELAY_BETWEEN_COUNTDOWN - COUNTDOWN_REFRESH_DELTA):

                # get the background image with already placed effects
                self.resizedImg  = self.BackgroundImage.copy()
                
                # paste the countdown image on top of the background image
                numberPic = PIL.Image.open(COUNTDOWN_FORMAT % (COUNTDOWN_IMAGE_FOLDER,COUNTDOWN_STYLE,self.Countdown))
                numberPic = numberPic.resize((int(SCREEN_RESOLUTION[0]/COUNTDOWN_WIDTH_FACTOR),int(SCREEN_RESOLUTION[1]/COUNTDOWN_HEIGHT_FACTOR)))
                self.resizedImg.paste(numberPic, (int(SCREEN_RESOLUTION[0]/2-SCREEN_RESOLUTION[0]/COUNTDOWN_WIDTH_FACTOR/2)+COUNTDOWN_OVERLAY_OFFSET_X,int(SCREEN_RESOLUTION[1]/2-SCREEN_RESOLUTION[1]/COUNTDOWN_HEIGHT_FACTOR/2)+COUNTDOWN_OVERLAY_OFFSET_Y), numberPic)
                
                #Load the resized Image with PhotoImage
                self.resizedImg = PIL.ImageTk.PhotoImage(self.resizedImg)
                #Put the image into the canvas object
                self.canvas.create_image(0,0,anchor=NW,image=self.resizedImg)
                
                # refresh overlayed text (just the failure message if available)
                self.canvas.create_text(FAILURE_TEXT_X,FAILURE_TEXT_Y,text=self.TextFailure,font=FAILURE_TEXT_FONT,fill=FAILURE_TEXT_COLOR,width=FAILURE_TEXT_WIDTH)
                
                self.LastChangeTimeCountdown = time.time() # store time for next iteration
            
        elif self.StateSlideshow == STATE_SLIDESHOW_CAPTURED_IMG: # show the captured picture
            if self.CapturedImage != 0: # if a picture was captured
                #Resize Image, so all Images have the same size
                self.resizedImg = ImageOps.fit(PIL.Image.open(self.CapturedImage), SCREEN_RESOLUTION)
                #Load the resized Image with PhotoImage
                self.resizedImg = PIL.ImageTk.PhotoImage(self.resizedImg)
                #Put the image into the canvas object
                self.canvas.create_image(0,0,anchor=NW,image=self.resizedImg)
                
                # refresh overlayed text
                # but only when a failure occurred, no info text here
                self.canvas.create_text(FAILURE_TEXT_X,FAILURE_TEXT_Y,text=self.TextFailure,font=FAILURE_TEXT_FONT,fill=FAILURE_TEXT_COLOR,width=FAILURE_TEXT_WIDTH)
            else: # failure case. Could not capture an image
                # get the background image with already placed effects
                self.resizedImg  = self.BackgroundImage.copy()
                
                #Load the resized Image with PhotoImage
                self.resizedImg = PIL.ImageTk.PhotoImage(self.resizedImg)
                #Put the image into the canvas object
                self.canvas.create_image(0,0,anchor=NW,image=self.resizedImg)
                
                # refresh overlayed text (just the failure message if available)
                self.canvas.create_text(FAILURE_TEXT_X,FAILURE_TEXT_Y,text=self.TextFailure,font=FAILURE_TEXT_FONT,fill=FAILURE_TEXT_COLOR,width=FAILURE_TEXT_WIDTH)

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
            
            # initialze variables for this iteration
            self.takePictureVar = False
            self.Countdown = COUNTDOWN_S
            self.TextFailure = ""
            
            ###### CHECK IF WE NEED TO SHOW LIVE PREVIEW OR BACKGROUND
            livepreviewavailable = False
            if TRY_TO_USE_LIVE_PREVIEW:
                if livepreview:
                    livepreviewavailable = True
            
            #button_takePhoto.wait_for_press()
            while self.takePictureVar is not True:
                if self.ShutdownRequest: # if there was a shutdown request via external button, shutdown here to perform a clean exit
                    call("sudo shutdown -h now", shell=True)
                time.sleep(0.1)
                    
            # change the shown picture to the background
            self.StateSlideshow = STATE_SLIDESHOW_BACKGROUND
            
            # set the new filename
            now = time.strftime("%Y%m%d_%H-%M-%S")
            file = "%s.jpg" % now
            imgPath = "%s%s" % (PHOTO_PATH,file)
            
            ###### INITIALIZE CAMERAS WHILE RUN TIME
            if CAMERA == CAMERA_DSLR:
                try:
                    #self.cameraContext = gp.gp_context_new()
                    self.camera = gp.check_result(gp.gp_camera_new())
                    gp.check_result(gp.gp_camera_init(self.camera))#, self.cameraContext))
                    #text = gp.check_result(gp.gp_camera_get_summary(self.camera, self.cameraContext))
                    if False: # TODO: prüfen, ob livepreview available ist
                        self.livepreview = True
                except:
                    logging.error('Could not find any DSLR camera')
                    self.TextFailure = "Could not find any DSLR camera.\nCheck camera's battery"
            
            ###### START LIVE PREVIEW OR SHOW BACKGROUND IMAGE
            if livepreviewavailable:
                if CAMERA == CAMERA_PI:
                    mycam.annotate_text_size=96
                    mycam.start_preview(resolution=(SCREEN_RESOLUTION))
                elif CAMERA == CAMERA_DSLR:
                    pass # TODO start live preview

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
                    time.sleep(DELAY_BETWEEN_COUNTDOWN)
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
            
            ###### CAPTURE IMAGE
            if CAMERA == CAMERA_PI:
                mycam.capture(myfile,format='jpeg',quality=100,thumbnail=(64,48,35))
            elif CAMERA == CAMERA_DSLR:
                try:
                    cameraFilePath = gp.check_result(gp.gp_camera_capture(self.camera, gp.GP_CAPTURE_IMAGE))
                    cameraFile = gp.check_result(gp.gp_camera_file_get(self.camera, cameraFilePath.folder, cameraFilePath.name, gp.GP_FILE_TYPE_NORMAL))
                    logging.info('get image from folder: %s, name: %s', cameraFilePath.folder, cameraFilePath.name)
                    gp.check_result(gp.gp_file_save(cameraFile, imgPath))
                except gp.GPhoto2Error:
                    logging.error("Could not capture image!")
                    self.TextFailure = "Could not capture an image.\nCheck camera's battery"
                    
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
            
            ###### DSLR: store image on camera memory card
            if CAMERA == CAMERA_DSLR:
                if DSLR_STORE_PICTURE_ON_CAMERA:
                    try:
                        localCameraFile = gp.check_result(gp.gp_file_open(imgPath))
                        gp.check_result(gp.gp_camera_folder_put_file(self.camera, CAMERA_FOLDER, file, gp.GP_FILE_TYPE_NORMAL, localCameraFile))
                    except gp.GPhoto2Error:
                        logging.error("Could not store image on camera!")
                        self.TextFailure = "Could not store image on camera"
            
            if STORE_PICTURE_ALSO_ON_USB_DEVICE:
                dirs = os.listdir(USB_DEVICE_MOUNT_POINT)
                for dir in dirs:
                    path = USB_DEVICE_MOUNT_POINT + dir + BKP_DEVICE_FOLDER_ON_USB_DEVICE
                    # check if the folders already exist
                    if not os.path.exists(path):
                        os.makedirs(path)
                    #print("Backup captured image to: %s" % path)
                    try:
                        copyfile(imgPath, path + file)
                    except FileNotFoundError:
                        logging.error("Could not backup file on usb device!")
                                
            time.sleep(TIME_TO_SHOW_CAPTURED_IMAGE)
            
            ###### CONTINUE WITH SLIDESHOW
            self.StateSlideshow = STATE_SLIDESHOW_IDLE
        
if __name__ == '__main__':

    try:
        
        # Starting Camera Thread
        _thread.start_new_thread(Fullscreen_Window.camTask,(Fullscreen_Window,))
        # Starting Gallery View
        _thread.start_new_thread(Fullscreen_Window(),(Fullscreen_Window,))
   

    except:
        print ("Error") 
    


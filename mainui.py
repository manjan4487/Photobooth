'''
Simple Photobooth Software
Created on 29.01.2018

Features:
 - use of Raspberry PI camera
 - use of DSLR (tested with Nikon D60)
 - use of remote USB mouse for wireless capturing
 - shutdown button for secure poweroff
 - fan support
 - individual backgrounds with few available effects
 - custom countdown pictures can be integrated very simple
 - countdown pictures can be scaled as desired
 - log files available for failure evaluation
 - live preview for Raspberry PI camera
 - prepared for live preview with DSLRs (not implemented yet)
 - live created additional backup of captured image on USB stick
 - failure messages are printed on display (e.g. camera's battery empty)

@author: KS (main frame from MJ)
'''

# Script version
VERSION = 0.06

# do not edit the following lines
CAMERA_PI = 0
CAMERA_DSLR = 1


##### EDIT HERE ######
# CAMERA can be either CAMERA_PI or CAMERA_DSLR
CAMERA = CAMERA_DSLR

# Defines the timing of changing the ImageView in the slideshow in seconds
SLIDESHOW_CHANGE_TIME_S = 4

SCREEN_RESOLUTION = (1920,1080)#(1680,1050)#(1280,960) #(1920,1080) # (height,width)

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
COUNTDOWN_S = 3 # e.g. 5 means countdown goes in range [5,4,3,2,1,0] + the first digit is shown while the camera is initialized

# choose a countdown style. Style name is used in PNG files like "Countdown_%s_x.png" % COUNTDOWN_STYLE, see COUNTDOWN_FORMAT
# You can create your own style: name the new files with the style name you have chosen here
COUNTDOWN_STYLE = 'classic'

# the folder with the countdown images
COUNTDOWN_IMAGE_FOLDER = PHOTOBOOTH_PATH + 'images/countdown/'

# the time that a captured image is displayed until the slideshow continues
TIME_TO_SHOW_CAPTURED_IMAGE = 7

# the time that shows a occurred failure message after trying to capture an image
TIME_TO_SHOW_FAILURE_MSG = 4

# time between two digits of the countdown (in s)
DELAY_BETWEEN_COUNTDOWN = 0.95

# time like DELAY_BETWEEN_COUNTDOWN but for the last iteration (when the last number is displayed)
DELAY_BETWEEN_COUNTDOWN_LAST_ITERATION = 0.9

# define if the live preview should be used if available (Pi Cam and a few DSLR cameras support live preview)
TRY_TO_USE_LIVE_PREVIEW = False

# background image to show if there is no live preview shown
BACKGROUND_PICTURE = PHOTOBOOTH_PATH + 'images/background/Background_Luck.jpg'

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
COUNTDOWN_WIDTH_FACTOR = 3.5
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

# define if you want to use a pwm to control an external fan
FAN_PWM_USE = True
FAN_PWM_PIN = 14
FAN_PWM_FREQ = 150
FAN_PWM_DUTY = 10

# information text that is shown during runtime
INFORMATION_TEXT = "Picture access in WIFI 'Photobooth':\nhttp://photobooth"
INFORMATION_TEXT_X = SCREEN_RESOLUTION[0] - 240
INFORMATION_TEXT_Y = SCREEN_RESOLUTION[1] - 30
INFORMATION_TEXT_FONT = ('Arial','18')
INFORMATION_TEXT_WIDTH = "350p"

FAILURE_TEXT_WIDTH = "1060p"
FAILURE_TEXT_X = SCREEN_RESOLUTION[0] - 890
FAILURE_TEXT_Y = SCREEN_RESOLUTION[1] - 580
FAILURE_TEXT_FONT = ('Arial','52')
FAILURE_TEXT_COLOR = "red"
FAILURE_TEXT_F_FOCUS = "Ups! Das war wohl nichts.\nDer Fokus konnte nicht gesetzt werden.\nVersuche es bitte noch einmal :)"
FAILURE_TEXT_F_NOCAM = "Ups! Das war wohl nichts.\nDie Kameraverbindung konnte nicht hergestellt werden.\nBatterie leer?"

# configuration for logging
LOGGING_ACTIVE = True
LOGGING_FILE_PREFIX = "photobooth_log_" # the ctime at script start is added to the log file *.log
LOGGING_FILE_FOLDER = "/home/pi/Desktop/Logs/"

# TODO use of gpio to capture an image

##### edit stop

##### DEVELOPER EDIT START #####

# file format used to find the countdown pictures
# first argument has to be the COUNTDOWN_STYLE and the second the number of the countdown
COUNTDOWN_FORMAT = '%sCountdown_%s_%s.png' # % (COUNTDOWN_IMAGE_FOLDER,COUNTDOWN_STYLE,i)

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
import threading
import sys
import os
import RPi.GPIO as GPIO
import time

if CAMERA == CAMERA_PI:
    from picamera import PiCamera
elif CAMERA == CAMERA_DSLR:
    import gphoto2 as gp
if SHUTDOWN_GPIO_USE:
    from subprocess import call
if STORE_PICTURE_ALSO_ON_USB_DEVICE:
    from shutil import copyfile
if LOGGING_ACTIVE:
    import logging

if sys.version_info[0] == 2:  # Just checking your Python version to import Tkinter properly.
    from Tkinter import *
else:
    from tkinter import *


class Fullscreen_Window:    
    takePictureVar = False
    StateSlideshow = STATE_SLIDESHOW_IDLE
    Countdown = 0
    CurrentDelay = 0
    CapturedImage = 0
    BackgroundImage = 0
    TextFailure = ""
    ShutdownRequest = False
    oldCountdownValue = 0
    resizedImage = None
    Mutex = threading.Lock()
    MutexFileAccess = threading.Lock()
    
    GPIO.setmode(GPIO.BCM)

    def __init__(self, master=None):
        self.tk = master
        self.state = True
        master.attributes("-fullscreen", self.state)
        master.bind("<F11>", self.toggle_fullscreen)
        master.bind("<Escape>", self.end_fullscreen)
        master.bind("<Button-1>", self.take_picture)
        self.canvas = Canvas(master, width=SCREEN_RESOLUTION[0],height=SCREEN_RESOLUTION[1],highlightthickness=0,bd=0,bg="black")
        self.canvas.pack(fill=BOTH, expand=YES)
        
        # check if the folders already exist
        if not os.path.exists(PHOTO_PATH):
            os.makedirs(PHOTO_PATH)
        if not os.path.exists(TEMP_TRASH_FOLDER):
            os.makedirs(TEMP_TRASH_FOLDER)
        if not os.path.exists(LOGGING_FILE_FOLDER):
            os.makedirs(LOGGING_FILE_FOLDER)
        
        if LOGGING_ACTIVE:
            t = time.strftime("%y-%m-%d_%H:%M:%S")
            logging.basicConfig(filename=LOGGING_FILE_FOLDER + LOGGING_FILE_PREFIX + t + ".log", format='%(asctime)s: %(levelname)s: %(message)s', level=logging.INFO)
            
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
            
        # create background image with effect once in init
        self.BackgroundImage = ImageOps.fit(PIL.Image.open(BACKGROUND_PICTURE), SCREEN_RESOLUTION)
                
        if BACKGROUND_EFFECT_GRAYSCALE: # may use a grayscale effect
            self.BackgroundImage = ImageOps.grayscale(self.BackgroundImage)
                
        if BACKGROUND_EFFECT_BLUR: # may use the blur effect
            self.BackgroundImage = self.BackgroundImage.filter(ImageFilter.BLUR)
            
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
            GPIO.add_event_detect(SHUTDOWN_GPIO_PIN, polarity, callback=self.shutdownButtonEvent, bouncetime=500)
            
        if FAN_PWM_USE:
            GPIO.setup(FAN_PWM_PIN, GPIO.OUT)
            p = GPIO.PWM(FAN_PWM_PIN, FAN_PWM_FREQ)
            p.start(FAN_PWM_DUTY)
            #p.ChangeDutyCycle(30)

    def shutdownButtonEvent(self, channel):
        if SHUTDOWN_GPIO_USE:
            if channel == SHUTDOWN_GPIO_PIN:
                logging.warning("Shutting down request via GPIO PIN. Shutting down now...")
                self.ShutdownRequest = True
        
    def take_picture(self, event=None): # gets called by button-1 (left mouse button)
        self.takePictureVar = True
        return "break" # TODO umschaltbar machen zwischen GPIO button und maus taste
    
    def toggle_fullscreen(self, event=None):
        self.state = not self.state
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"
        
    def updateGuiTask(self):
        lastChangeTimeSlideshow = 0
        lastChangeTimeCountdown = 0
        lastChangeTimeCaptured = 0
        
        toggleImageHolder = False
        old_items_to_delete = [] # on canvas
 
        while 1 :
            self.Mutex.acquire()
            state_tmp = self.StateSlideshow
            self.Mutex.release()
            if state_tmp == STATE_SLIDESHOW_IDLE: # show slideshow
                now = time.time()
                if now - lastChangeTimeSlideshow > SLIDESHOW_CHANGE_TIME_S:
                    image_list = []
                    self.MutexFileAccess.acquire()
                    # Get all Images in photoPath
                    for filename in glob.glob("%s*.jpg" % PHOTO_PATH):
                        image_list.append(filename)
                            
                    if len(image_list) > 0:
                        # Calc. random number for Image which has to be shown
                        randomnumber = randint(0, len(image_list)-1)

                        im=PIL.Image.open(image_list[randomnumber])

                        # Resize Image, so all Images have the same size
                        newImgTmp = ImageOps.fit(im, SCREEN_RESOLUTION)
                                                 
                        # store the new added elements on canvas to delete them in next iteration
                        # but first add the new elements on canvas to display the new elements
                        # before removing the old ones
                        old_items_tmp = []
                        
                        # Load the resized Image with PhotoImage and put the image into the canvas object
                        if toggleImageHolder:
                            newImg2 = PIL.ImageTk.PhotoImage(newImgTmp)
                            old_items_tmp.append(self.canvas.create_image(0,0,anchor=NW,image=newImg2))
                        else:
                            newImg = PIL.ImageTk.PhotoImage(newImgTmp)
                            old_items_tmp.append(self.canvas.create_image(0,0,anchor=NW,image=newImg))
                            
                        toggleImageHolder = not toggleImageHolder

                        # refresh overlayed text
                        old_items_tmp.append(self.canvas.create_text(INFORMATION_TEXT_X,INFORMATION_TEXT_Y,text=INFORMATION_TEXT,font=INFORMATION_TEXT_FONT,width=INFORMATION_TEXT_WIDTH))
                        old_items_tmp.append(self.canvas.create_text(FAILURE_TEXT_X,FAILURE_TEXT_Y,text=self.TextFailure,font=FAILURE_TEXT_FONT,fill=FAILURE_TEXT_COLOR,width=FAILURE_TEXT_WIDTH))
                        
                        # now the new items are shown on the display
                        # delete all old items from canvas to free the memory
                        for item_to_delete in old_items_to_delete:
                            self.canvas.delete(item_to_delete)
                        
                        # and copy the list of new added items
                        old_items_to_delete = old_items_tmp
                        
                    self.MutexFileAccess.release()
                    
                    lastChangeTimeSlideshow = now # store time for next iteration

            elif state_tmp == STATE_SLIDESHOW_BACKGROUND: # show background with countdown
                self.Mutex.acquire()
                countdown_tmp = self.Countdown
                self.Mutex.release()
                if countdown_tmp >= 0:
                    now = time.time()
                    if now - lastChangeTimeCountdown > DELAY_BETWEEN_COUNTDOWN:
                        # get the background image with already placed effects
                        newImgTmp = self.BackgroundImage.copy()
                        
                        # paste the countdown image on top of the background image
                        numberPic = PIL.Image.open(COUNTDOWN_FORMAT % (COUNTDOWN_IMAGE_FOLDER,COUNTDOWN_STYLE, self.Countdown))
                        numberPic = numberPic.resize((int(SCREEN_RESOLUTION[0]/COUNTDOWN_WIDTH_FACTOR),int(SCREEN_RESOLUTION[1]/COUNTDOWN_HEIGHT_FACTOR)))
                        newImgTmp.paste(numberPic, (int(SCREEN_RESOLUTION[0]/2-SCREEN_RESOLUTION[0]/COUNTDOWN_WIDTH_FACTOR/2)+COUNTDOWN_OVERLAY_OFFSET_X,int(SCREEN_RESOLUTION[1]/2-SCREEN_RESOLUTION[1]/COUNTDOWN_HEIGHT_FACTOR/2)+COUNTDOWN_OVERLAY_OFFSET_Y), numberPic)
                        
                        # temporary variable, for more explanation see state STATE_SLIDESHOW_IDLE
                        old_items_tmp = []
                                                 
                        # Load the resized Image with PhotoImage and put the image into the canvas object
                        if toggleImageHolder:
                            newImg2 = PIL.ImageTk.PhotoImage(newImgTmp)
                            old_items_tmp.append(self.canvas.create_image(0,0,anchor=NW,image=newImg2))
                        else:
                            newImg = PIL.ImageTk.PhotoImage(newImgTmp)
                            old_items_tmp.append(self.canvas.create_image(0,0,anchor=NW,image=newImg))
                        
                        toggleImageHolder = not toggleImageHolder
                        
                        # refresh overlayed text (just the failure message if available)
                        old_items_tmp.append(self.canvas.create_text(FAILURE_TEXT_X,FAILURE_TEXT_Y,text=self.TextFailure,font=FAILURE_TEXT_FONT,fill=FAILURE_TEXT_COLOR,width=FAILURE_TEXT_WIDTH))
                        
                        # now the new items are shown on the display
                        # delete all old items from canvas to free the memory
                        for item_to_delete in old_items_to_delete:
                            self.canvas.delete(item_to_delete)
                        
                        # and copy the list of new added items
                        old_items_to_delete = old_items_tmp
                        
                        lastChangeTimeCountdown = now # store time for next iteration
                        
                        self.Mutex.acquire()
                        self.Countdown = countdown_tmp - 1
                        self.Mutex.release()
                
            elif state_tmp == STATE_SLIDESHOW_CAPTURED_IMG: # show the captured picture
                now = time.time()
                if now - lastChangeTimeCaptured > TIME_TO_SHOW_CAPTURED_IMAGE:
                    # temporary variable, for more explanation see state STATE_SLIDESHOW_IDLE
                    old_items_tmp = []
                    
                    if self.CapturedImage != 0: # if a picture was captured
                        #Resize Image, so all Images have the same size
                        newImgTmp = ImageOps.fit(PIL.Image.open(self.CapturedImage), SCREEN_RESOLUTION)
                        
                        # Load the resized Image with PhotoImage and put the image into the canvas object
                        if toggleImageHolder:
                            newImg2 = PIL.ImageTk.PhotoImage(newImgTmp)
                            old_items_tmp.append(self.canvas.create_image(0,0,anchor=NW,image=newImg2))
                        else:
                            newImg = PIL.ImageTk.PhotoImage(newImgTmp)
                            old_items_tmp.append(self.canvas.create_image(0,0,anchor=NW,image=newImg))
                            
                        toggleImageHolder = not toggleImageHolder

                        # refresh overlayed text
                        # but only when a failure occurred, no info text here
                        old_items_tmp.append(self.canvas.create_text(FAILURE_TEXT_X,FAILURE_TEXT_Y,text=self.TextFailure,font=FAILURE_TEXT_FONT,fill=FAILURE_TEXT_COLOR,width=FAILURE_TEXT_WIDTH))
                    else: # failure case. Could not capture an image
                        # get the background image with already placed effects
                        newImgTmp  = self.BackgroundImage.copy()
                        
                        # Load the resized Image with PhotoImage and put the image into the canvas object
                        if toggleImageHolder:
                            newImg2 = PIL.ImageTk.PhotoImage(newImgTmp)
                            old_items_tmp.append(self.canvas.create_image(0,0,anchor=NW,image=newImg2))
                        else:
                            newImg = PIL.ImageTk.PhotoImage(newImgTmp)
                            old_items_tmp.append(self.canvas.create_image(0,0,anchor=NW,image=newImg))
                            
                        toggleImageHolder = not toggleImageHolder
                        
                        # refresh overlayed text (just the failure message if available)
                        old_items_tmp.append(self.canvas.create_text(FAILURE_TEXT_X,FAILURE_TEXT_Y,text=self.TextFailure,font=FAILURE_TEXT_FONT,fill=FAILURE_TEXT_COLOR,width=FAILURE_TEXT_WIDTH))

                    # now the new items are shown on the display
                    # delete all old items from canvas to free the memory
                    for item_to_delete in old_items_to_delete:
                        self.canvas.delete(item_to_delete)
                    
                    # and copy the list of new added items
                    old_items_to_delete = old_items_tmp
                    
                    lastChangeTimeCaptured = now
            
            # sleep for a short time in this thread
            time.sleep(0.03)
                    
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
            self.Mutex.acquire()
            self.Countdown = COUNTDOWN_S
            self.Mutex.release()
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
                time.sleep(0.02)

            # change the shown picture to the background
            self.Mutex.acquire()
            self.StateSlideshow = STATE_SLIDESHOW_BACKGROUND
            self.Mutex.release()
            
            # give the other thread some time to create the new background/image
            time.sleep(0.075)
            
            # set the new filename
            now = time.strftime("%Y%m%d_%H-%M-%S")
            file = "%s.jpg" % now
            imgPath = "%s%s" % (PHOTO_PATH,file)
            
            ###### INITIALIZE CAMERAS WHILE RUN TIME
            cameraInitialized = True
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
                    self.TextFailure = FAILURE_TEXT_F_NOCAM
                    cameraInitialized = False

            ###### START LIVE PREVIEW OR SHOW BACKGROUND IMAGE
            if livepreviewavailable:
                if CAMERA == CAMERA_PI:
                    mycam.annotate_text_size=96
                    mycam.start_preview(resolution=(SCREEN_RESOLUTION))
                elif CAMERA == CAMERA_DSLR:
                    pass # TODO start live preview

            ###### COUNTDOWN LOOP
            countdownOngoing = True
            while countdownOngoing:
                if livepreviewavailable:
                    if CAMERA == CAMERA_PI:
                        mycam.annotate_text = "%s" % self.Countdown
                    elif CAMERA == CAMERA_DSLR:
                        pass # TODO
                
                self.Mutex.acquire()
                if self.Countdown <= 0:
                    countdownOngoing = False
                self.Mutex.release()
                
                time.sleep(0.03)
                
            # end of loop
            
            time.sleep(DELAY_BETWEEN_COUNTDOWN_LAST_ITERATION)
            
            ###### POST LIVE PREVIEW
            if livepreviewavailable:
                if CAMERA == CAMERA_PI:
                    mycam.annotate_text = ""
                elif CAMERA == CAMERA_DSLR:
                    pass # TODO
                
            self.MutexFileAccess.acquire()
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
                    if cameraInitialized  == True:
                        self.TextFailure = FAILURE_TEXT_F_FOCUS
                    
                    # be sure that there is no corrupted image file, so move the file to temporary trash
                    tempTrashPath = "%sTRASH_%s" % (TEMP_TRASH_FOLDER, file)
                    os.rename(imgPath, tempTrashPath)
                    self.CapturedImage = 0 # we can not show a captured image on the screen
                
            myfile.close()
            self.MutexFileAccess.release()
            
            if livepreviewavailable:
                if CAMERA == CAMERA_PI:
                    mycam.stop_preview()
                elif CAMERA == CAMERA_DSLR:
                    pass # TODO ggf. die livePreview stoppen
            
            ###### SHOW THE CAPUTRED IMAGE
            self.Mutex.acquire()
            self.StateSlideshow = STATE_SLIDESHOW_CAPTURED_IMG
            self.Mutex.release()
            
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
            
            if self.CapturedImage != 0: # no failure or at least a picture could be captured
                time.sleep(TIME_TO_SHOW_CAPTURED_IMAGE)
            else: # the (annoying) failure message is shown for a shorter time
                time.sleep(TIME_TO_SHOW_FAILURE_MSG)
            
            ###### CONTINUE WITH SLIDESHOW
            self.Mutex.acquire()
            self.StateSlideshow = STATE_SLIDESHOW_IDLE
            self.Mutex.release()
        
if __name__ == '__main__':

    try:
        
        root = Tk()
        
        w = Fullscreen_Window(master=root)
   
        # Starting GUI Thread
        tGui = threading.Thread(target=Fullscreen_Window.updateGuiTask, args=(w,))
        # Starting Camera Thread
        tCam = threading.Thread(target=Fullscreen_Window.camTask, args=(w,))

        tGui.start()
        tCam.start()

        root.mainloop()

    except:
        print ("Error") 
    


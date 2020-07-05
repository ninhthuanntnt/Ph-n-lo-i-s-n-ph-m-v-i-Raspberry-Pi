from pathlib import Path
import shutil
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
import tkinter.ttk as ttk
from ttkthemes import ThemedStyle
import cv2
import PIL.Image
import PIL.ImageTk
import PIL.ImageDraw
import PIL.ImageFont
import pymysql.cursors
from threading import Thread
import threading
from multiprocessing import Process
from urllib.request import urlopen
import time
import gpiozero as GZ
import RPi.GPIO as GPIO
from picamera.array import PiRGBArray
from picamera import PiCamera
import requests
import enum
from orbdetector import *
from surfdetector import *
from database import *
from RpiMotorLib import RpiMotorLib
from firebaseservice import FirebaseService
# req = requests.get('http://192.168.1.13/control?var=framesize&val=6')



class SystemMode(enum.Enum):
    AUTO = 1
    MANUAL = 2
    
SYS_MODE = SystemMode.AUTO
isEnabledDetector = False
class NTNTApp:
    __root_folder = Path().absolute()
    __buttonSwitchModePin = 25
    
    def __init__(self, window, window_title, video_source=0, url=None):
        print(self.__root_folder)
        self.window = window  # is returned from Tk()
        self.window.title(window_title)
        self.window.attributes('-fullscreen', True)  
        self.fullScreenState = True
        
        self.isEnabledThreads = False
        #init firebase service
        self.firebaseService = FirebaseService()
        self.threadUpdateFirebaseData = threading.Thread(target=self.firebaseService.updateProductQuantityThread)
        self.threadUpdateFirebaseData.setDaemon(True)
        #init button switch mode
        self.buttonSwitchMode = GZ.Button(self.__buttonSwitchModePin, pull_up= True)
        self.buttonSwitchMode.when_pressed = self.switchSystemMode
        #init camera
        self.camera = PiCamera()
        self.camera.resolution = (640, 480)
        self.camera.framerate = 30
        self.rawCapture = PiRGBArray(self.camera, size=(640, 480))
        
        # Create video box
        self.isVidAlive = True
        
        # init database
        self.database = MyDatabase()
        # init detector
        self.listImageData = self.database.getAllData()
        self.database.close()

        self.detector = ORBDetector()
        #init rasp
        self.rasp = MyRasp()
        
        
        self.threadStepperMotor = threading.Thread(target = self.rasp.enableStepperMotor)
        #init thread video stream
        self.threadVideoStream = threading.Thread(target=self.video_stream)
        self.threadVideoStream.setDaemon(True)
        self.isVidAlive = False
        # Init element on window
        self.style = ThemedStyle(window)
        self.style.set_theme('radiance')
        #Create 3 frame
        self.frameToolsBar = ttk.Frame(window)
        self.frameActivity = ttk.Frame(window)
        self.frame1 = ttk.Frame(self.frameActivity, width=400, height=300)
        self.frame11 = ttk.Frame(self.frame1)
        seperator = ttk.Separator(self.frameActivity, orient=VERTICAL)
        self.frame2 = ttk.Frame(self.frameActivity, width=400, height=300)
        self.frame21 = ttk.Frame(self.frame2)
        self.frame22 = ttk.Frame(self.frame2)
        # init button, entry, label
        # inside frame tools bar
        self.btnShutdown = ttk.Button(self.frameToolsBar, text='Shutdown', command=self.shutdown)
        self.btnToggleFullScreen = ttk.Button(self.frameToolsBar, text='Toggle FullScreen', command=self.toggleFullScreen)
        self.btnSwitchMode = ttk.Button(self.frameToolsBar, text='Switch to MANUAL', command=self.switchSystemMode)
        self.btnSwitchDetector = ttk.Button(self.frameToolsBar, text='Switch to SURF', command = self.switchDetector)
        # inside frame1
        self.btnDetect = ttk.Button(self.frame11, text="Detect now", width=10, command=self.startDetect)
        self.btnStopDetect = ttk.Button(self.frame11, text="Stop detect", width=10, command=self.stopDetect)
        # Listbox
        labelListBox = ttk.Label(self.frame1, text="Chose 1 or 2 product for detecting:", font='Helvetica 12 bold underline')
        self.listBox = Listbox(self.frame1, selectmode= MULTIPLE)
        for i in range(0,len(self.listImageData)):
            self.listBox.insert(i, self.listImageData[i].name)
        self.btnLoadData = ttk.Button(self.frame11, text="Load data", command=self.loadData)
        
        # inside frame2
        label = ttk.Label(self.frame2, text="Fill form to add new logo:", font='Helvetica 12 bold underline')
        labelName = ttk.Label(self.frame21, text='Logo name:')
        self.inputName = ttk.Entry(self.frame21)
        labelData = ttk.Label(self.frame22, text='File(.PNG):')
        self.pathFileData = ''
        self.btnFileUpload = ttk.Button(self.frame22, text='Browse a image', command=self.showFileDialog)
        self.labelPathFileData = ttk.Label(self.frame2, text='')
        self.btnSubmitData = ttk.Button(self.frame2, text='Submit', command = self.submitData)

        #init layout
        # init 2 frame
        self.frameToolsBar.pack(fill=X)
        self.frameActivity.pack(fill=BOTH, expand=True)
        self.frame1.pack(fill=BOTH, expand=True, side = LEFT)
        seperator.pack(side=LEFT)
        self.frame2.pack(fill=BOTH, expand=True, side = LEFT)
        # init layout inside frame tools bar
        self.btnShutdown.pack(side = LEFT)
        self.btnToggleFullScreen.pack(side = LEFT)
        self.btnSwitchMode.pack(side = LEFT)
        self.btnSwitchDetector.pack(side=LEFT)
        # init layout inside frame1
        labelListBox.pack(fill=X, side=TOP, padx=10, pady=5)
        self.listBox.pack(fill=X, side=TOP, padx=10, pady=5)
        self.frame11.pack(fill=X, side=TOP, padx=10, pady=5)
        self.btnLoadData.pack(side=LEFT, expand=True)
        # init layout inside frame2
        label.pack(fill=X, side=TOP, padx=5, pady=5)
        self.frame21.pack(fill=X, side=TOP, padx=5, pady=5)
        labelName.pack(anchor=NW, padx=5, pady=5)
        self.inputName.pack(fill=X, padx=5, pady=5)
        self.frame22.pack(fill=X, side=TOP, padx=5, pady=5)
        labelData.pack(anchor=NW, padx=5, pady=5)
        self.btnFileUpload.pack(fill=X, padx=5, pady=5)
        self.labelPathFileData.pack(fill=X, side=TOP, padx=5, pady=5)
        self.btnSubmitData.pack(side=TOP)

        
        self.window.mainloop()
    def shutdown(self):
        answer = messagebox.askquestion('Shut down system', '''Are you sure to shutdown system.\n
                                                                All device will be stopped.''')
        if(answer == 'yes'):
            GPIO.setmode(GPIO.BCM)
            GPIO.cleanup()
            self.camera.close()
            cv2.destroyAllWindows()
            self.firebaseService.setStatusToFalse()
            exit()
    def toggleFullScreen(self):
        self.fullScreenState = not self.fullScreenState
        self.window.attributes("-fullscreen", self.fullScreenState)
    
    def switchSystemMode(self):
        global SYS_MODE
        print('press switch')
        if SYS_MODE == SystemMode.AUTO:
            SYS_MODE = SystemMode.MANUAL
            self.btnSwitchMode.config(text='Switch to AUTO')
            self.rasp.turnOnSwitchModeLed()
        elif SYS_MODE == SystemMode.MANUAL:
            SYS_MODE = SystemMode.AUTO
            self.btnSwitchMode.config(text='Switch to MANUAL')
            self.rasp.turnOffSwitchModeLed()
    def switchDetector(self):
        if type(self.detector).__name__ == 'ORBDetector':
            self.detector = SURFDetector()
            self.btnSwitchDetector.config(text='Switch to ORB')
        else:
            self.detector = ORBDetector()
            self.btnSwitchDetector.config(text='Switch to SURF')
    def video_stream(self):
        global SYS_MODE
        global isEnabledDetector
        cv2.namedWindow('Product detector')
        cv2.moveWindow('Product detector',600,0)
        for img in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):
            startTime = time.time()
            frame = img.array
            if(SYS_MODE != SystemMode.MANUAL and isEnabledDetector == True):
                box, name, coordinates = self.detector.detectObject(frame)
            else:
                coordinates = []
            
            if len(coordinates) == 0:
                self.rasp.reset()
            else:
                cv2.polylines(frame, [coordinates],
                              True, (255, 255, 255), 2)
                text = 'Name:{0}, Box: {1}'.format(name, box)
                cv2.putText(frame, text,(10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2, cv2.LINE_AA)
                
                if box == 1:
                    self.rasp.rotateToBox1()
                    self.firebaseService.addOneProduct(name)
                elif box == 2:
                    self.rasp.rotateToBox2()
                    self.firebaseService.addOneProduct(name)
                    
            cv2.imshow('Product detector', frame)
            cv2.waitKey(1)
            self.rawCapture.truncate(0)
            if not self.isVidAlive:
                break
        # video.release()
        cv2.destroyWindow('Product detector')
        while not self.isVidAlive:
            pass
        self.video_stream()
        
    def showFileDialog(self):
        self.pathFileData = filedialog.askopenfilename(
            initialdir='/home', title='Select data image', filetypes=(("Image", "*.*"), ("png files", "*.png"), ("jpg files", "*.jpg")))
        self.labelPathFileData.configure(text = self.pathFileData)
    
    def submitData(self):
        if(self.pathFileData == '' or self.inputName.get() ==''):
            messagebox.showerror('Error', 'Can\'t submit data. Please fill full field!')
        else:
            destination = self.__root_folder/'.image_train'
            source = self.pathFileData
            #add time into path to avoid having the same image name
        
            indexSlash = source.rfind('/')
            file = source[indexSlash + 1:]
            indexDot = file.rfind('.')
            fileName = file[:indexDot]
            extension = file[indexDot + 1:]
            fileName += '_' + str(round(time.time()))
            newFile = fileName + '.' + extension
            destination = destination/newFile
            
            print(source)
            print(destination)
            newFilePath = shutil.copy(source, destination)
            # Insert data to database
            imageData = ImageData(name=self.inputName.get(), path = str(newFilePath))
            print(imageData.path)
            trainImgTemp = cv2.imread(imageData.path, 0)
            trainKPTemp, trainDescTemp = self.detector.detectAndCompute(trainImgTemp, None)
            imageData.image = trainImgTemp
            imageData.trainKP = trainKPTemp
            imageData.trainDesc = trainDescTemp

            self.database.open()
            self.database.insertData(imageData)
            self.database.close()

            self.listImageData.append(imageData)
            self.listBox.insert(self.listBox.size()+1, imageData.name)
            # clear form
            self.pathFileData = ''
            self.inputName.delete(0, END)
            self.labelPathFileData.configure(text='')
   
        
    def startDetect(self):
        if(not self.isEnabledThreads):
            self.threadVideoStream.start()
            self.threadUpdateFirebaseData.start()
            self.threadStepperMotor.start()
            self.isEnabledThreads = True
        self.btnStopDetect.pack(side=LEFT, expand=True)
        self.btnDetect.pack_forget()
        
        self.isVidAlive = True
    
    def stopDetect(self):
        self.btnDetect.pack(side=LEFT, expand=True)
        self.btnStopDetect.pack_forget()
        
        self.isVidAlive = False
    def loadData(self):
        if hasattr(self,'frame12'):
            print('have frame12')
            self.frame12.pack_forget()
            self.frame12.destroy()
        self.frame12 = ttk.Frame(self.frame1)
        self.frame12.pack(fill=X, side=TOP, padx=10, pady=5)
        
        labelFrame12 = ttk.Label(self.frame12, text='Chose product to put inside box 1 and box 2',font='Helvetica 12 bold underline')        
        labelFrame12.pack(fill=X, side=TOP, padx=10, pady=5)
        self.buttonSubmitOrder = ttk.Button(self.frame12, text='Submit order', command = self.submitOrder)
        self.buttonSubmitOrder.pack(side=BOTTOM)
        
        curselection = self.listBox.curselection()
        newListImageData = []
        self.listOrderImageDatas = dict()
        for i in range(0,len(curselection)):
            currentImageData = self.listImageData[curselection[i]]
            #append to temporary list to fecth into detector
            newListImageData.append(currentImageData)
            #create list checkbutton to chose which is in box1 or box2
            frameRadiobutton = ttk.Frame(self.frame12)
            frameRadiobutton.pack(fill=X, side=TOP)
            self.listOrderImageDatas[currentImageData.id] = IntVar()
            self.listOrderImageDatas[currentImageData.id].set(1)
            
            labelNameProduct = ttk.Label(frameRadiobutton, text=currentImageData.name)
            radiobutton1 = ttk.Radiobutton(frameRadiobutton, text='Box 1', variable = self.listOrderImageDatas[currentImageData.id], value=1,
                                           command=lambda: self.testCheckbutton())
            radiobutton2 = ttk.Radiobutton(frameRadiobutton, text='Box 2', variable = self.listOrderImageDatas[currentImageData.id], value=2,
                                           command=lambda: self.testCheckbutton())
            labelNameProduct.pack(side=LEFT, padx = 1)
            radiobutton1.pack(side=LEFT, padx=1)
            radiobutton2.pack(side=LEFT, padx=1)
#         self.detector.setData(newListImageData)
        self.btnLoadData.pack_forget()
        self.btnLoadData.pack(side=LEFT, expand=True)
    
    def testCheckbutton(self):
        for key, val in self.listOrderImageDatas.items():
            print(str(key) + '-' + str(val.get()))
    def submitOrder(self):
        listImageDataForDetection = []
        
        for key, val in self.listOrderImageDatas.items():
            for imageData in self.listImageData:
                if(imageData.id == key):
                    imageData.box = val.get()
                    listImageDataForDetection.append(imageData)
        #reset detector to add new data
        if type(self.detector).__name__ == 'ORBDetector':
            print('create new orb')
            self.detector = ORBDetector()
        else:
            self.detector = SURFDetector()
            
        self.detector.setData(listImageDataForDetection)
        
        #firebase update
        tempDictProducts = {}
        for imageData in listImageDataForDetection:
            tempDictProducts[imageData.name] = 0
        
        print(tempDictProducts)
        self.firebaseService.updateProducts(tempDictProducts)
        
        
        self.btnDetect.pack(side=LEFT, expand=True)
        #unpack layout
        self.frame12.pack_forget()
        self.frame12.destroy()
    def __del__(self):
        print('end')
        self.camera.close()
        cv2.destroyAllWindows()

class MyRasp:
    __isEnabledStepperMotor = False
    __isRotating = False
    __pSensorPin = 16
    __servo1Pin=17
    __servo2Pin=22
    __button1Pin = 23
    __button2Pin = 24
    __led1Pin = 5
    __led2Pin = 6
    __switchModeLedPin = 4
    def __init__(self):
        defaultCorretion = 0.45
        maxPW=(2.0+defaultCorretion)/1000
        minPW=(1.0-defaultCorretion)/1000
        self.servo1 = GZ.Servo(self.__servo1Pin, min_pulse_width=minPW, max_pulse_width=maxPW, frame_width = 20/1000)
        self.servo2 = GZ.Servo(self.__servo2Pin, min_pulse_width=minPW, max_pulse_width=maxPW, frame_width = 20/1000)
        
        print ("Waiting for servo start")
        self.servo1.value = -1
        time.sleep(0.5)
        self.servo2.value = 1
        time.sleep(0.5)
        self.servo1.detach()
        self.servo2.detach()
        self.led1 = GZ.LED(self.__led1Pin)
        self.led2 = GZ.LED(self.__led2Pin)
        self.switchModeLed = GZ.LED(self.__switchModeLedPin)
        self.button1 = GZ.Button(self.__button1Pin, pull_up = True)
        self.button2 = GZ.Button(self.__button2Pin, pull_up = True)
        self.pSensor = GZ.Button(self.__pSensorPin)
        self.button1.when_pressed = self.pressButton1
        self.button2.when_pressed = self.pressButton2
        self.pSensor.when_pressed = self.detectObject
        # init stepper motor
        stepperMotor_pins = (14, 15, 18)
        direction = 20      
        step = 21
        self.stepperMotor = RpiMotorLib.A4988Nema(direction, step, stepperMotor_pins, "A4988")
    def rotateToBox1(self):
        if(not self.__isRotating):
            print('Box1')
            self.led1.on()
            self.servo1.value = 0.6
            time.sleep(0.4)
            self.servo1.value = -1
            time.sleep(0.3)
            self.led1.off()
            self.servo1.detach()
            self.__isRotating = True
            self.__isEnabledStepperMotor = True
    
    def rotateToBox2(self):
        if(not self.__isRotating):
            print('Box2')
            self.led2.on()
            self.servo2.value = -0.5
            time.sleep(0.4)
            self.servo2.value = 1
            time.sleep(0.3)
            self.led2.off()
            self.servo2.detach()
            self.__isRotating = True
            self.__isEnabledStepperMotor = True
    def pressButton1(self, pin):
        if SYS_MODE == SystemMode.MANUAL:
            self.rotateToBox1()
            self.__isRotating = False
        
    def pressButton2(self, pin):
        if SYS_MODE == SystemMode.MANUAL:
            self.rotateToBox2()
            self.__isRotating = False
        
    def turnOnSwitchModeLed(self):
        self.switchModeLed.on()
            
    def turnOffSwitchModeLed(self):
        self.switchModeLed.off()
        
    def reset(self):
        self.__isRotating = False
        
    def enableStepperMotor(self):
        global isEnabledDetector
        isEnabledDetector = False
        while(1):
            self.stepperMotor.motor_go(True, "Half" , 2, 0.0022, False, 0)   
            if(not self.__isEnabledStepperMotor):
                print('stop stepper motor')
                self.stepperMotor.motor_go(True, "Half", 500, 0.0022, False, 0)
                break
            
             
        isEnabledDetector = True
        count = 0
        while(not self.__isEnabledStepperMotor):
            time.sleep(0.5)
            if(count == 6):
                self.__isEnabledStepperMotor = True
                break
            count+=1
        print('enable stepper')
        self.enableStepperMotor()
        
    def detectObject(self):
        print('Detected object')
        self.__isEnabledStepperMotor = False
        
    def enableStepperMotorAfter3s(self):
        time.sleep(3)
        self.__isEnabledStepperMotor = True
        
if __name__ == '__main__':
    NTNTApp(Tk(), 'Nhận diện logo', 0)

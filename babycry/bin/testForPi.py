from matplotlib.mlab import find
import requests
import time
from time import sleep
import pyaudio
import numpy as np
import math
from datetime import datetime
import matplotlib.pyplot as plt
from detect_peaks import detect_peaks
from Naked.toolshed.shell import execute_js, muterun_js
from threading import Thread
from gpiozero import LED
import RPi.GPIO as GPIO
import wave
import urllib
GPIO.setmode(GPIO.BCM)  
GPIO.setup(23, GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(17, GPIO.IN) 
MinDetect = 50
Running = False
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
checkWF =False
WAVE_OUTPUT_FILENAME = "babycry.wav"
WEB_SERVER = 'http://192.168.137.7:3000'
DeviceID= "12345678"
UserID = ""
Window= 150
init =False
send = False
RECORD_SECONDS = 10
cryTime =0
p = pyaudio.PyAudio()
# plt.axis([ 0, 100,0,10000])
# plt.ion()
# plt.show()
ffs = [0]
amp = [0]
# line, = plt.plot(ffs)
babyDidCry = False
endFrame = 0
whiteL = LED(18)
yellowL= LED(24)
redL= LED(27)
greenL= LED(22)
framesForWav =[]
stream = 0
deviceID = {"dID": DeviceID}
isMoved = False


def motionDetect():
    global isMoved
    try:
        while True:
            i= GPIO.input(17)
            if i==0:
                yellowL.off()
                isMoved = False
                sleep(0.1)
            elif i==1:
                yellowL.on()
                isMoved= True
                sleep(0.1)
    except KeyboardInterrupt:
        pass  # print(r.text)

def recording():
    audio = pyaudio.PyAudio()
 
# start Recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, 
                    input=True,
                    output=False,
                    frames_per_buffer=chunk)
    print "recording..."
    frames = []
     
    for i in range(0, int(RATE / chunk * RECORD_SECONDS)):
        data =stream.read(chunk, exception_on_overflow = False)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    audio.terminate
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()


def checkState():
    try:
        while True:
            if init:
                try:
                    if Running == False:
                        status = "stopped"
                    else:
                        status = "started"
                    r = requests.get(WEB_SERVER+"/time",params={"dID": DeviceID,"status":status})
                   # print(r)
                    #present = datetime.now().isoformat()
                    if r.text == "start" and Running == False:
                        ChangeState()
                    elif r.text == "stop" and Running == True:
                        ChangeState()
                except:
                    pass 
                sleep(5)
            else:
                sleep(3)

    except KeyboardInterrupt:
        pass  # print(r.text)


def cryBlink():
    for x in range(0,6):
        whiteL.on()
        sleep(0.3)
        whiteL.off()
        sleep(0.3)

def ChangeState():
    global Running,stream,init
    if init== False:
        init= True
    print "key pressed"
    if Running == False:
        Running = True
        if stream!= 0 and stream.is_active():
            stream.start_stream()
        
    else:
        Running = False
        if stream!=0 and stream.is_stopped():
            stream.stop_stream()
        thread1 = Thread(target = greenBlink)
        thread1.start()

def toggle(channel):
    print "reset"
    r = requests.get(WEB_SERVER+"/reset",params=deviceID)
    ChangeState()

   # print Running

def checkWifi():
    try:
        while True:
            try:
                url = "https://www.google.com"
                urllib.urlopen(url)
                greenL.on()
                redL.off()
                return 0
            except:
                greenL.off()
                redL.on()
                sleep(1.5)
                redL.off()
                sleep(0.5)
    except KeyboardInterrupt:
        pass


GPIO.add_event_detect(23, GPIO.FALLING, callback=toggle, bouncetime=2000)

def Pitch(signal):
    signal = np.fromstring(signal, 'Int16')
    maXabs = sum(abs(i) for i in signal)/float(len(signal))
   # print(maXabs)
    #print maXabs
    if maXabs >MinDetect:
        crossing = [math.copysign(1.0, s) for s in signal]
        index = find(np.diff(crossing));
        f0=round(len(index) *RATE /(2*np.prod(len(signal))))
        return f0, maXabs;
    else:
        return 0,0

def createAndSend():
    checkWifi()
    #creatWave(framesForWav)
    recording()
    sendMessage()

def errorLight():
    greenL.off()
    whiteL.off()
    redL.on()
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        pass
def checkUserID(): 
    r = requests.get(WEB_SERVER+"/userID",params=deviceID)
    return r.text
 
def greenBlink():
    global checkWF
    whiteL.off()
    redL.off()
    if not checkWF:
        wifi= checkWifi()
        checkWF = True
   # print "here"
    while not Running:
        greenL.off()
        sleep(0.5) 
        greenL.on() 
        sleep(1.5) 

def sendMessage():
    global babyDidCry,framesForWav,send
    print "sending message"
    with open(WAVE_OUTPUT_FILENAME, 'rb') as f:
        r = requests.post(WEB_SERVER + "/post",data={"deviceID":DeviceID},files={'file': f})
   # print(r.text)
    babyDidCry = False
    print "babycry return to false"
    framesForWav =[]
    send = False



def creatWave(frames):
    print(len(frames))
    print "create wave file"
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(p.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

def detecting():
    global babyDidCry,Running,send,cryTime
    i=0
    
    #print "recording..."
    average = []
    greenL.on()


    try:
       # print "decteddd"
        userID = checkUserID()
        if userID != "success":
            raise Exception("user not registered")
    except Exception as e:
        print(e)
        errorLight()
    try:    
        stream = p.open(format = FORMAT,
        channels = CHANNELS,
        rate = RATE,
        input = True,
        output= True,
        frames_per_buffer = chunk)
    except:
        pass

    try:    
        while Running:
            data = stream.read(chunk, exception_on_overflow = False)

            if time.time()< cryTime and isMoved == True and babyDidCry == False:
                babyDidCry = True
                print "motion and cry detected"
                cryBlink()
            if babyDidCry == True:
                #if len(framesForWav) <500:
                #    framesForWav.append(data)
                if send == False:
                    print "starting to create wav and send..."
                    thread1 = Thread(target = createAndSend)
                    thread1.start()
                    send = True
                    

            #p = 20*np.log10(np.abs(np.fft.rfft(data[:2048])))
           # f = np.linspace(0, rate/2.0, len(p))
           # pl.plot(f, p)
            #pl.xlabel("Frequency(Hz)")
            #pl.ylabel("Power(dB)")
           # pl.show()
            Frequency, amplitude = Pitch(data)
           # print(Frequency)
            #print "%f Frequency" %Frequency
            ffs.append(Frequency)
            amp.append(amplitude)
            
            #if len(ffs) < 100 and np.count_nonzero(ffs)!=0:
                #average.append(sum(ffs)/np.count_nonzero(ffs))
            #elif np.count_nonzero(ffs)!=0:
              #  average.append(sum(ffs[len(ffs)-100:])/np.count_nonzero(ffs))
            # line.set_xdata(np.arange(len(ffs)))
            # line.set_ydata(ffs)
            #line2.set_xdata(np.arange(len(amp)))
            #line2.set_ydata(amp)
           # plt.plot(i, Frequency)
            # plt.draw()
            # plt.pause(0.001)
            # if i <100:
            #     plt.axis([ 0, 100,0,10000])
            # else:
            #      plt.axis([ 0, i,0,10000]) 
            if (i+1)% Window == 0:
                dist = Window-1
                avgPeak = []
                #js = []
                if np.count_nonzero(ffs[i-dist:])!=0:
                    peaks = detect_peaks(ffs[i-dist:], mph=1500, mpd=3,show = False)
                    averageAmp = np.average(amp[i-dist:])
                    if len(peaks) >0:
                        for j in peaks:
                           # js.append(j)
                            avgPeak.append(ffs[j+i-dist])
                        avgPeakResult = np.average(avgPeak)
                        stdPeak = np.std(avgPeak)
                    else:
                        avgPeakResult = 0
                        stdPeak = 0
                    print avgPeakResult, stdPeak,averageAmp, len(peaks), np.count_nonzero(ffs[i-99:])/float(len(ffs[i-99:]))
                    if np.average(avgPeak) <= 2500 and np.std(avgPeak) <200 and averageAmp >20 and len(peaks)>=3 and len(peaks) <14:
                        print "baby cry detected"
                        cryTime= time.time() + 10
                    else:
                        #pass
                       print "noise"
                else:
                    #pass
                    print "noise"
            i = i+1
        stream.stop_stream()
        stream.close()
    except KeyboardInterrupt:
        pass
        print(e)
        #errorLight()

    # while True: # ESC
    #    # x=sys.stdin.read(1)[0]
    #     plt.pause(0.05)    

def main():
    r = requests.get(WEB_SERVER+"/time",params={"dID": DeviceID,"status":"stopped"})
    thread1 = Thread(target = checkState )
    thread1.start()
    thread2 = Thread(target = motionDetect )
    thread2.start()
    try: 
        while True:
                greenBlink()
                detecting()
    except KeyboardInterrupt:   
            pass
            
main()
    #print("You pressed", x)

#termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)  
   # plt.pause(0.01)
#while True:
    


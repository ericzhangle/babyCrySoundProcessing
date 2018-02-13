from matplotlib.mlab import find
import requests
import pyaudio
import numpy as np
import math
import matplotlib.pyplot as plt
from detect_peaks import detect_peaks
from Naked.toolshed.shell import execute_js, muterun_js
from threading import Thread
import wave


MinDetect = 300
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 20
WAVE_OUTPUT_FILENAME = "babycry.wav"
WEB_SERVER = 'http://localhost:3000/'
DeviceID= "123456"
UserID = ""



p = pyaudio.PyAudio()
plt.axis([ 0, 100,0,10000])
plt.ion()
plt.ylabel('Frequency and Amplitude')
plt.xlabel("time")
plt.show()
ffs = [0]
amp = [0]
line, = plt.plot(ffs)
line2, = plt.plot(amp) # plot amp
babyDidCry = False
endFrame = 0
framesForWav =[]



def Pitch(signal):
    signal = np.fromstring(signal, 'Int16')
    maXabs = sum(abs(i) for i in signal)/float(len(signal))
    #print maXabs
    if maXabs >MinDetect:

        crossing = [math.copysign(1.0, s) for s in signal]
        index = find(np.diff(crossing));
        f0=round(len(index) *RATE /(2*np.prod(len(signal))))
        return f0, maXabs;
    else:
        return 0,0

def ceateAndSend():
    creatWave(framesForWav)
    sendMessage()

def checkUserID():
    deviceID = {"dID": DeviceID}
    r = requests.get('http://localhost:3000/userID',params=deviceID)
    return r.text
    

def sendMessage():
    global framesForWav,babyDidCry
    with open(WAVE_OUTPUT_FILENAME, 'rb') as f:
        r = requests.post(WEB_SERVER + "post",data={"deviceID":DeviceID},files={'file': f})
    print(r.text)
    babyDidCry = False
    framesForWav =[]



def creatWave(frames):
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(p.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

def detecting():
    global babyDidCry
    # userID = checkUserID()
    # if userID == "":
    #     print "device not registered"
    #     return
    stream = p.open(format = FORMAT,
    channels = CHANNELS,
    rate = RATE,
    input = True,
    output = True,
    frames_per_buffer = chunk)
    average = []
    for i in range(0, 5000):
        data = stream.read(chunk, exception_on_overflow = False)

        # if babyDidCry == True:
        #     if i < endFrame:
        #         framesForWav.append(data)
        #     elif i == endFrame:
        #         print "starting to create wav and send..."
        #         thread1 = Thread(target = ceateAndSend)
        #         thread1.start()
               # thread1.join()
                

        #p = 20*np.log10(np.abs(np.fft.rfft(data[:2048])))
       # f = np.linspace(0, rate/2.0, len(p))
       # pl.plot(f, p)
        #pl.xlabel("Frequency(Hz)")
        #pl.ylabel("Power(dB)")
       # pl.show()
        Frequency, amplitude = Pitch(data)
        #print "%f Frequency" %Frequency
        ffs.append(Frequency)
        amp.append(amplitude)
        
        #if len(ffs) < 100 and np.count_nonzero(ffs)!=0:
            #average.append(sum(ffs)/np.count_nonzero(ffs))
        #elif np.count_nonzero(ffs)!=0:
          #  average.append(sum(ffs[len(ffs)-100:])/np.count_nonzero(ffs))
        line.set_xdata(np.arange(len(ffs)))
        line.set_ydata(ffs)
        line2.set_xdata(np.arange(len(amp)))
        line2.set_ydata(amp)
        #plt.plot(i, Frequency)
        plt.draw()
        plt.pause(0.001)
        if i <100:
            plt.axis([ 0, 100,0,10000])
        else:
             plt.axis([ 0, i,0,10000]) 
        if (i+1)% 100 == 0:
            avgPeak = []
            if np.count_nonzero(ffs[i-99:])!=0:
                peaks = detect_peaks(ffs[i-99:], mph=2000, mpd=3,show = False)
                averageAmp = np.average(amp[i-99:])
                if len(peaks) >0:
                    for j in peaks:
                       # js.append(j)
                        avgPeak.append(ffs[i-99])
                    avgPeakResult = np.average(avgPeak)
                    stdPeak = np.std(avgPeak)
                else:
                    avgPeakResult = 0
                    stdPeak = 0
                print  avgPeakResult, stdPeak,averageAmp, len(peaks)
                if np.average(avgPeak) <= 5000 and np.std(avgPeak) <1000 and averageAmp >20 and len(peaks)>=3 and len(peaks) <14:
                    if babyDidCry == False:
                        babyDidCry = True
                        endFrame = i + 500

                    print "baby crying"
                else:
                    print "noise"
            else:
                print "noise"

    while True: # ESC
       # x=sys.stdin.read(1)[0]
        plt.pause(0.05)    


detecting()
    #print("You pressed", x)

#termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)  
   # plt.pause(0.01)
#while True:
    


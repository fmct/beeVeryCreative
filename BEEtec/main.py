'''

'''

import logging
import re
import sqlite3
import time
import os
from os.path import dirname, join
import sys
import serial
from serial.tools import list_ports
import  glob
import platform
from BEEtec import changeFilament
from BEEtec import Popups
from BEEtec import connectNewPrinter
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, \
    ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

Config.set('graphics', 'width', '960')
Config.set('graphics', 'height', '640')

Config.set('kivy','window_icon','data/icons/BeeVeryCreative.png')

logger = logging.getLogger('beeconsole')
logger.setLevel(logging.INFO)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# add the handlers to logger
logger.addHandler(ch)

logThread = None

class ShowcaseScreen(Screen):
    fullscreen = BooleanProperty(False)

    def add_widget(self, *args):
        if 'content' in self.ids:
            return self.ids.content.add_widget(*args)
        return super(ShowcaseScreen, self).add_widget(*args)


class ShowcaseApp(App):
    connectANewPrinter = connectNewPrinter.Connection()
    index = NumericProperty(-1)
    current_title = StringProperty()
    time = NumericProperty(0)
    show_sourcecode = BooleanProperty(False)
    sourcecode = StringProperty()
    screen_names = ListProperty([])
    hierarchy = ListProperty([])
    initialTemps = []
    selectButton1 = False
    selectButton2 = False
    selectButton3 = False
    selectButton4 = False
    conn = sqlite3.connect('database/printersTest.db')
    c = conn.cursor()
    def build(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS printersTest (id integer PRIMARY KEY , serialNumber int, initialDateTime string, timeHeating string, timePrinting string, spentFilament string, fileInfo file)''')
        self.title = 'Bee Very Creative'
        Clock.schedule_interval(self._update_clock, 1 / 60.)
        self.screens = {}
        self.available_screens = list([ #can be sorted if you want
            'ScreenManager'])
        self.screen_names = self.available_screens
        curdir = dirname(__file__)
        self.available_screens = [join(curdir, 'data', 'screens',
            '{}.kv'.format(fn).lower()) for fn in self.available_screens]
        self.go_next_screen()
        Clock.schedule_interval(self.timer, 0.3)
        Clock.schedule_interval(self.timerCalibrateTest, 0.03)
        Clock.schedule_interval(self.timerChangeFilament, 0.03)
        Clock.schedule_interval(self.timerConnecting, 0.03)
        Clock.schedule_interval(self.timerPrintTest, 0.0005)
        Clock.schedule_interval(self.timerAltSerialNum, 0.0005)
        Clock.schedule_interval(self.timerConnEnc, 0.03)
        w = self.root.ids.sm
        for printer in self.connectANewPrinter.connectedPrinters:
            self.connectANewPrinter.existsAnEmptySlice(self.root,printer)

    def on_pause(self):
        return True


    def on_resume(self):
        pass

    def go_next_screen(self):
        self.index = (self.index + 1) % len(self.available_screens)
        screen = self.load_screen(self.index)
        sm = self.root.ids.sm
        sm.switch_to(screen, direction='left')
        self.current_title = screen.name
        self.update_sourcecode()

    def go_screen(self, idx):
        self.index = idx

        self.update_sourcecode()

    def load_screen(self, index):
        if index in self.screens:
            return self.screens[index]
        screen = Builder.load_file(self.available_screens[index])
        self.screens[index] = screen
        return screen

    def update_sourcecode(self):
        if not self.show_sourcecode:
            self.root.ids.sourcecode.focus = False
            return
        self.root.ids.sv.scroll_y = 1

    def _update_clock(self, dt):
        self.time = time.time()

    #-----------------------Connect to a new Printer--------------------
    connecting = False
    view_connecting = None
    disconnected = False
    def isConnecting(self):
        self.view_connecting = Popups.connecting()
        self.connecting = True

    def timerConnecting(self,dt):
        w = self.root.ids.sm
        if self.connecting == True:
            self.connectNewPrinter()
            if self.canConnect():
                w.children[0].ids.sm.current = 'screen3'
            else:
                w.children[0].ids.sm.current = 'screen1'
                self.resetSlicePressed()
            self.connecting = False

    def delConnPrinter(self):
        w = self.root.ids.sm
        if self.slicePressedAndNotEmpty() is not None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    self.slicePressedAndNotEmpty().text = 'Empty'
                    self.connectANewPrinter.connectedPrinters.remove(printer)
        else:
            self.connectANewPrinter.connectedPrinters = self.connectANewPrinter.connectedPrinters[:-1]
        self.resetSlicePressed()
        w.children[0].ids.sm.current = 'screen1'

    def connectNewPrinter(self):
        w = self.root.ids.sm
        self.connecting = True
        self.connectANewPrinter.connect(self.root,self.view_connecting)
        t = (self.connectANewPrinter.initialDateTime,)
        self.c.execute(
           "INSERT INTO printersTest(initialDateTime) VALUES (?) ", t)
        self.conn.commit()
        self.resetNum()

    def canConnect(self):
        return self.connectANewPrinter.canConnect()

    def slicePressed(self):
        w = self.root.ids.sm
        if (self.selectButton1 == True and w.children[0].ids.firstPrinter.text == 'Empty'):
            return w.children[0].ids.firstPrinter
        elif (self.selectButton2 == True and w.children[0].ids.secondPrinter.text == 'Empty'):
            return w.children[0].ids.secondPrinter
        elif (self.selectButton3 == True and w.children[0].ids.thirdPrinter.text == 'Empty'):
            return w.children[0].ids.thirdPrinter
        elif (self.selectButton4 == True and w.children[0].ids.fourPrinter.text == 'Empty'):
            return w.children[0].ids.fourPrinter

    def slicePressedAndNotEmpty(self):
        w = self.root.ids.sm
        if (self.selectButton1 == True and w.children[0].ids.firstPrinter.text != 'Empty'):
            return w.children[0].ids.firstPrinter
        elif (self.selectButton2 == True and w.children[0].ids.secondPrinter.text != 'Empty'):
            return w.children[0].ids.secondPrinter
        elif (self.selectButton3 == True and w.children[0].ids.thirdPrinter.text != 'Empty'):
            return w.children[0].ids.thirdPrinter
        elif (self.selectButton4 == True and w.children[0].ids.fourPrinter.text != 'Empty'):
            return w.children[0].ids.fourPrinter

    def resetSlicePressed(self):
        self.selectButton1 = False
        self.selectButton2 = False
        self.selectButton3 = False
        self.selectButton4 = False

    def closeConnection(self):
        if self.slicePressedAndNotEmpty() is not None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    if(printer[0]['State'] == 'Heating'):
                        printer[1].cancelHeating()
                    if(self.isCalibration == True):
                        printer[1].cancelCalibration()
                        self.isCalibration = False
                    printer[1].beep()
                    printer[1]._beeCon.close()
                    self.connectANewPrinter.connectedPrinters.remove(printer)
                    self.slicePressedAndNotEmpty().text = 'Empty'
                    for aux in self.printerWithPic:
                        if printer[0]['Serial Number'] in aux[0]:
                            self.printerWithPic.remove(aux)
        else:
            self.connectANewPrinter.connectedPrinters[-1][1].beep()
            self.connectANewPrinter.connectedPrinters[-1][1]._beeCon.close()
            self.connectANewPrinter.connectedPrinters = self.connectANewPrinter.connectedPrinters[:-1]
        self.resetSlicePressed()
        self.resetValues()

    def chooseScreen(self,text):
        w = self.root.ids.sm
        if text == 'Empty':
            self.isConnecting()
        elif text != 'Empty':
            if self.slicePressedAndNotEmpty() is not None:
                serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
                for printer in self.connectANewPrinter.connectedPrinters:
                    if int(printer[0]['Serial Number']) == int(serialNumber):
                        if printer[4] == True:
                            printer[4] = False
                            if printer[0]['State'] == 'Ready':
                                w.children[0].ids.load_unload.disabled = False
                            else:
                                w.children[0].ids.load_unload.disabled = True
                            w.children[0].ids.sm.current = 'screen5'
                        else:
                            if printer[0]['State'] == 'Ready':
                                w.children[0].ids.cancelPrint.disabled = True
                                w.children[0].ids.LUWhiteFilament.disabled = False
                            else:
                                w.children[0].ids.cancelPrint.disabled = False
                                w.children[0].ids.LUWhiteFilament.disabled = True
                            w.children[0].ids.sm.current = 'screen13'

    #--------------Alter Serial Number----------------#

    def alterSerialNumber(self):
        w = self.root.ids.sm
        self.newSerialNumber = w.children[0].ids.textInput.text
        if (self.connectANewPrinter.connectedPrinters[-1][1].getPrinterMode() == 'Firmware'):
            try:
                self.connectANewPrinter.connectedPrinters[-1][1].goToBootloader()
            except AttributeError:
                self.connectANewPrinter.beeConn.connectToPrinterWithSN(self.connectANewPrinter.connectedPrinters[-1][0]['Serial Number'])
                self.connectANewPrinter.beeCmd = self.connectANewPrinter.beeConn.getCommandIntf()
                self.connectANewPrinter.mode = self.connectANewPrinter.beeCmd.getPrinterMode()
                self.connectANewPrinter.connectedPrinters[-1][1] = self.connectANewPrinter.beeCmd
        self.connectANewPrinter.connectedPrinters[-1][1].setSerialNumber(w.children[0].ids.textInput.text)
        self.connectANewPrinter.connectedPrinters[-1][2].write('Change the serial number from '
                                                               + self.connectANewPrinter.connectedPrinters[-1][0]['Serial Number']
                                                               + ' to ' + self.newSerialNumber + '\n')
        self.connectANewPrinter.connectedPrinters[-1][0]['Serial Number'] = self.newSerialNumber
        t = (self.connectANewPrinter.connectedPrinters[-1][0]['Serial Number'],)
        self.c.execute(
            "UPDATE printersTest set serialNumber = ? where initialDateTime = '" + self.connectANewPrinter.initialDateTime + "'", t)
        self.conn.commit()
        self.slicePressed().text = self.connectANewPrinter.listOfDictToArray(
            self.connectANewPrinter.connectedPrinters[-1][0])
        w.children[0].ids.goNextStep.disabled = False

    def getNumberInserted(self):
        w = self.root.ids.sm
        return w.children[0].ids.textInput.text

    def representsInt(self,s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def putNum(self,text):
        w = self.root.ids.sm
        w.children[0].ids.textInput.text += text

    def eraseNum(self):
        w = self.root.ids.sm
        w.children[0].ids.textInput.text = w.children[0].ids.textInput.text[:-1]

    def resetNum(self):
        w = self.root.ids.sm
        w.children[0].ids.textInput.text = ''
        w.children[0].ids.goNextStep.disabled = True

    def timerAltSerialNum(self,dt):
        w = self.root.ids.sm
        if w.children[0].ids.sm.current == 'screen3':
            if self.representsInt(w.children[0].ids.textInput.text):
                if len(w.children[0].ids.textInput.text) == 10:
                    w.children[0].ids.goNextStep.disabled = False
                else:
                    w.children[0].ids.goNextStep.disabled = True
            else:
                w.children[0].ids.goNextStep.disabled = True

    #-----------Connect new Encoder-----------------------------#
    printerWithPic = []
    def connectToEncoder(self):
        w = self.root.ids.sm
        system_name = platform.system()
        initialPorts = [(port.vid, port.pid, port.device,port.serial_number) for port in list_ports.comports() if port.device == '/dev/ttyACM0']
        timeToDiscEnc = time.time()
        disconnect = False
        ports = []
        connect = False
        newEnc = None
        while time.time() - timeToDiscEnc <= 9:
            try:
                ports = [(port.vid, port.pid, port.device,port.serial_number) for port in list_ports.comports() if port.device == '/dev/ttyACM0']
            except:
                pass
            if len(initialPorts) == 0:
                disconnect = True
                connect = True
                break
            if len(ports) == len(initialPorts) + 1:
                for i in ports:
                        if i not in initialPorts:
                            newEnc = i[3]
                disconnect = True
                connect = True
                break
            if len(ports) == len(initialPorts) - 1:
                disconnect = True
                if ports != []:
                    for i in initialPorts:
                        if i not in ports:
                            newEnc = i[3]
                else:
                    newEnc = initialPorts[0][3]
                timeToConEnc = time.time()
                while(time.time() - timeToConEnc <= 6):
                    try:
                        ports = [(port.vid, port.pid, port.device, port.serial_number) for port in list_ports.comports()
                                 if port.device == '/dev/ttyACM0']
                    except:
                        pass
                    if len(ports) == len(initialPorts):
                        for i in range(0, len(ports) - 1 if len(ports) > 1 else len(ports)):
                            if ports[i] not in initialPorts:
                                newEnc = ports[i][3]
                        connect = True
                        break
                break
        if connect == True and disconnect == True:
            done = False
            initTime = time.time()
            while time.time() - initTime <= 5 and done == False:
                ports = [(port.vid, port.pid, port.device, port.serial_number) for port in list_ports.comports()
                         if port.device == '/dev/ttyACM0']
                if len(initialPorts) == 0 and ports != []:
                    newEnc = ports[0][3]
                for port in ports:
                    if system_name == "Linux":
                        if port[0] is not None:
                            if port[3] == newEnc:
                                s = serial.Serial('/dev/ttyACM0', 115200)
                                if len(self.connectANewPrinter.connectedPrinters) != 0:
                                    if self.slicePressedAndNotEmpty() is not None:
                                        serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
                                        for printer in self.connectANewPrinter.connectedPrinters:
                                            if int(printer[0]['Serial Number']) == int(serialNumber):
                                                if self.printerWithPic != []:
                                                    for x in self.printerWithPic:
                                                        if port[3] not in x[1]:
                                                            while True:
                                                                s.write("M505\r\n")
                                                                aux = s.readline()
                                                                print aux
                                                                if (aux == "OK\n"):
                                                                    self.printerWithPic.append((printer[0]['Serial Number'],port[3]))
                                                                    printer[5] = s
                                                                    done = True
                                                                    w.children[0].ids.sm.current = 'screen4'
                                                                    break
                                                            break
                                                    else:
                                                        Popups.picAlreadyConnected(printer[0]['Serial Number'])
                                                else:
                                                    while True:
                                                        s.write("M505\r\n")
                                                        aux = s.readline()
                                                        print aux
                                                        if (aux == "OK\n"):
                                                            self.printerWithPic.append((printer[0]['Serial Number'], port[3]))
                                                            printer[5] = s
                                                            done = True
                                                            w.children[0].ids.sm.current = 'screen4'
                                                            break
                                break

    connectingEnc = False
    def isConnEnc(self):
        self.view_connecting = Popups.connecting()
        self.connectingEnc = True

    def timerConnEnc(self,dt):
        if self.connectingEnc == True:
            self.connectToEncoder()
            self.connectingEnc = False
            self.view_connecting.dismiss()

    #------------Flash Firmware and set Firmware string ---------------#

    def next2steps(self):
        try:
            self.disconnected = False
            self.alterSerialNumber()
            #-----Set Firmware String and Flash Firmware------------
            possibleFirmwares = []
            with open('firmware/firmware.properties','r') as f:
                possibleFirmwares += f.readlines()
                possibleFirmwares = [x.strip() for x in possibleFirmwares]
            for version in possibleFirmwares:
                if (self.connectANewPrinter.connectedPrinters[-1][0]['Product'] == 'BEETHEFIRST PLUS'):
                    found = re.search("beethefirstplus=",version)
                    if found:
                        self.stepsToFlashFirmware(version.split("=", 1)[1])

                elif (self.connectANewPrinter.connectedPrinters[-1][0]['Product'] == 'BEETHEFIRST PLUS A'):
                    found = re.search("beethefirstplusa=", version)
                    if found:
                        self.stepsToFlashFirmware(version.split("=", 1)[1])
                elif(self.connectANewPrinter.connectedPrinters[-1][0]['Product'] == 'BEETHEFIRST'):
                    found = re.search("beethefirst=",version)
                    if found:
                        self.stepsToFlashFirmware(version.split("=", 1)[1])
                elif(self.connectANewPrinter.connectedPrinters[-1][0]['Product'] == 'BEEINSCHOOL'):
                    found = re.search("beeinschool=", version)
                    if found:
                        self.stepsToFlashFirmware(version.split("=", 1)[1])
                elif (self.connectANewPrinter.connectedPrinters[-1][0]['Product'] == 'BEEINSCHOOL A'):
                    found = re.search("beeinschoola=", version)
                    if found:
                        self.stepsToFlashFirmware(version.split("=", 1)[1])
                else:
                    found = re.search("beeme=", version)
                    if found:
                        self.stepsToFlashFirmware(version.split("=", 1)[1])
        except:
            self.disconnected = True
            Popups.printerDisc()
            self.delConnPrinter()

    def stepsToFlashFirmware(self,FirmStr):
        if self.connectANewPrinter.connectedPrinters[-1][1].getPrinterMode() == 'Firmware':
            self.connectANewPrinter.connectedPrinters[-1][1].goToBootloader()
            self.flashAndGoToFirmware(FirmStr)
        else:
            self.connectANewPrinter.connectedPrinters[-1][1].setFirmwareString(FirmStr)

            self.flashAndGoToFirmware(FirmStr)

    def flashAndGoToFirmware(self,FirmStr):
        self.connectANewPrinter.connectedPrinters[-1][1].flashFirmware("firmware/" + FirmStr,
                                                                       FirmStr)
        try:
            self.connectANewPrinter.connectedPrinters[-1][1].goToFirmware()
        except AttributeError:
            self.connectANewPrinter.beeConn.connectToPrinterWithSN(self.newSerialNumber)
            self.connectANewPrinter.beeCmd = self.connectANewPrinter.beeConn.getCommandIntf()
            self.connectANewPrinter.mode = self.connectANewPrinter.beeCmd.getPrinterMode()
            self.connectANewPrinter.connectedPrinters[-1][1] = self.connectANewPrinter.beeCmd

    #--------------------Select filament--------------------

    def selectFilament(self):
        try:
            self.disconnected = False
            w = self.root.ids.sm
            #------Select filament------------------
            self.connectANewPrinter.connectedPrinters[-1][1].setFilamentString('A'+w.children[0].ids.label_one.text
                                                                               + w.children[0].ids.label_two.text + w.children[0].ids.label_three.text + ' - ' + w.children[0].ids.name_filament.text)
            self.heatingNoozle()
        except:
            self.disconnected = True
            Popups.printerDisc()
            self.delConnPrinter()

    def incNum(self,id):
        w = self.root.ids.sm
        if(id == 'one'):
            if (w.children[0].ids.label_one.text != '1'):
                w.children[0].ids.label_one.text = str(int(w.children[0].ids.label_one.text) + 1)
            else:
                w.children[0].ids.label_one.text = str(int(w.children[0].ids.label_one.text) - 1)
        elif(id == 'two'):
            if (w.children[0].ids.label_two.text != '3'):
                w.children[0].ids.label_two.text = str(int(w.children[0].ids.label_two.text) + 1)
            else:
                w.children[0].ids.label_two.text = '0'
        else:
            if (w.children[0].ids.label_three.text != '9'):
                w.children[0].ids.label_three.text = str(int(w.children[0].ids.label_three.text) + 1)
            else:
                w.children[0].ids.label_three.text = '0'

    def decNum(self, id):
        w = self.root.ids.sm
        if (id == 'one'):
            if (w.children[0].ids.label_one.text != '0'):
                w.children[0].ids.label_one.text = str(int(w.children[0].ids.label_one.text) - 1)
            else:
                w.children[0].ids.label_one.text = str(int(w.children[0].ids.label_one.text) + 1)
        elif (id == 'two'):
            if (w.children[0].ids.label_two.text != '0'):
                w.children[0].ids.label_two.text = str(int(w.children[0].ids.label_two.text) - 1)
            else:
                w.children[0].ids.label_two.text = '3'
        else:
            if (w.children[0].ids.label_three.text != '0'):
                w.children[0].ids.label_three.text = str(int(w.children[0].ids.label_three.text) - 1)
            else:
                w.children[0].ids.label_three.text = '9'

    def timerChangeFilament(self,dt):
        w = self.root.ids.sm
        w.children[0].ids.name_filament.text = changeFilament.getColorName('A'+w.children[0].ids.label_one.text+ w.children[0].ids.label_two.text + w.children[0].ids.label_three.text)
        w.children[0].ids.color_filament.canvas.before.children[0].rgba = changeFilament.getColor(w.children[0].ids.label_one.text+ w.children[0].ids.label_two.text + w.children[0].ids.label_three.text)
        if w.children[0].ids.name_filament.text != 'Wrong Number...':
            w.children[0].ids.heatingNozzle.disabled = False

    #--------------------Heating noozle--------------------------

    def heatingNoozle(self):
        w = self.root.ids.sm
        if self.slicePressedAndNotEmpty() != None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":",1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    # -----Register Initial Temps--------------
                    if (printer[0]['Product'] == 'BEETHEFIRST'):
                        self.initialTemps = [{'Nozzle Temp': printer[1].getNozzleTemperature()}]
                    else:
                        self.initialTemps = printer[1].getTemperatures()
                    printer[2].write('Initial temps: ' + str(self.initialTemps) + '\n')
                    printer[1].beep()
                    printer[1].startHeating(200)
                    printer[0]['Initial Time'] = time.time()
                    printer[0]['State'] = 'Heating'
        w.children[0].ids.heatingNozzle.disabled = True
        w.children[0].ids.name_filament.text = 'Wrong Number...'


    def timer(self,dt):
        try:
            w = self.root.ids.sm
            if len(self.connectANewPrinter.connectedPrinters) != 0:
                if self.slicePressedAndNotEmpty() is not None:
                    serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
                    for printer in self.connectANewPrinter.connectedPrinters:
                        if int(printer[0]['Serial Number']) == int(serialNumber):
                            if  printer[0]['State'] == 'Heating':
                                w.children[0].ids.pb.value = round(printer[1].getHeatingState(),2)
                                if(w.children[0].ids.pb.value >= 0.98):
                                    printer[1].goToLoadUnloadPos()
                                    w.children[0].ids.load_unload.disabled = False
                                    printer[0]['State'] = 'Ready'
                                    printer[0]["Final Time"] = time.time() - printer[0]['Initial Time']
                                    w.children[0].ids.pb.value = 1.0
                                    printer[2].write("Elapsed time heating: " + str(int(round(printer[0]["Final Time"] / 60,2))) + " minutes " + str(round(printer[0]["Final Time"],2) % 60) + " sec\n")
                                    if (printer[0]['Product'] == 'BEETHEFIRST'):
                                        printer[2].write('Final Noozle temp: ' + str(printer[1].getNozzleTemperature()) + '\n')
                                    else:
                                        printer[2].write(
                                            'Final temps: ' + str(printer[1].getTemperatures()) + '\n')
                                    t = (str(int(round(printer[0]["Final Time"] / 60,2))) + " min " + str(round(printer[0]["Final Time"],2) % 60) + " s",)
                                    self.c.execute(
                                        "UPDATE printersTest set timeHeating = ? where initialDateTime = '" + printer[3] + "'",
                                        t)
                                    self.conn.commit()
                            if printer[4] == True:
                                    w.children[0].ids.sm.current = 'screen1'
                                    self.resetSlicePressed()
        except:
            Popups.printerDisc()
            self.delConnPrinter()

    def goToInit(self):
        if self.slicePressedAndNotEmpty() is not None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    if printer[0]['State'] == 'Heating':
                        printer[4] = True
                    else:
                        Popups.already100()

    def resetValues(self):
        w = self.root.ids.sm
        w.children[0].ids.goNextStep.disabled = True
        w.children[0].ids.load_unload.disabled = True
        w.children[0].ids.pb.value = 0.0

    #------------Load and Unload----------------------------

    def unload(self):
        try:
            if self.slicePressedAndNotEmpty() is not None:
                serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
                for printer in self.connectANewPrinter.connectedPrinters:
                    if int(printer[0]['Serial Number']) == int(serialNumber):
                        printer[1].unload()
        except:
            Popups.printerDisc()
            self.delConnPrinter()

    def load(self):
        try:
            if self.slicePressedAndNotEmpty() is not None:
                serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
                for printer in self.connectANewPrinter.connectedPrinters:
                    if int(printer[0]['Serial Number']) == int(serialNumber):
                        printer[1].load()
        except:
            Popups.printerDisc()
            self.delConnPrinter()

    #---------Calibration--------------------------------
    isCalibration = False
    def startCalibration(self):
        self.resetValues()
        #----reset value of cancel heating, from this moment this variable need to be false
        self.isCalibration = True
        if self.slicePressedAndNotEmpty() is not None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    printer[1].startCalibration()
                    printer[4] = False

    def up005(self):
        if self.slicePressedAndNotEmpty() is not None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    printer[1].move(0,0,-0.05)

    def up05(self):
        if self.slicePressedAndNotEmpty() is not None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    printer[1].move(0, 0, -0.5)

    def down005(self):
        if self.slicePressedAndNotEmpty() is not None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    printer[1].move(0, 0, 0.05)

    def down05(self):
        if self.slicePressedAndNotEmpty() is not None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    printer[1].move(0, 0, 0.5)

    def goToNextPointCalibration(self):
        if self.slicePressedAndNotEmpty() is not None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    printer[1].goToNextCalibrationPoint()

    isTestCalib = False
    def testCalibration(self):
        w = self.root.ids.sm
        self.resetVarCalTest()
        self.isTestCalib = True
        self.isCalibration = False
        w.children[0].ids.calibtest.value = 0
        if self.slicePressedAndNotEmpty() is not None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    printer[1].transferSDFile('calibrationTest/calibration.gcode')
                    time.sleep(2)
                    printer[1].startSDPrint()

    def timerCalibrateTest(self,dt):
        w = self.root.ids.sm
        if len(self.connectANewPrinter.connectedPrinters) != 0:
            if self.isTestCalib == True:
                if self.slicePressedAndNotEmpty() is not None:
                    serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
                    for printer in self.connectANewPrinter.connectedPrinters:
                        if int(printer[0]['Serial Number']) == int(serialNumber):
                            printVariables = printer[1].getPrintVariables()
                            if len(printVariables) != 0:
                                try:
                                    executedLines = printVariables['Executed Lines']
                                    totalLines =  printVariables['Lines']
                                    w.children[0].ids.calibtest.value = ((executedLines*100)/totalLines)
                                    if executedLines == totalLines:
                                        self.connectANewPrinter.connectedPrinters[-1][1].setNozzleTemperature(200)
                                        w.children[0].ids.questionCal.opacity = 1
                                        w.children[0].ids.calTestOk.opacity = 1
                                        w.children[0].ids.smile.opacity = 1
                                        w.children[0].ids.sad.opacity = 1
                                        w.children[0].ids.calTestOk.disabled = False
                                        w.children[0].ids.calTestNotOk.opacity = 1
                                        w.children[0].ids.calTestNotOk.disabled = False
                                        self.isTestCalib = False
                                except KeyError:
                                    pass

    def resetVarCalTest(self):
        w = self.root.ids.sm
        w.children[0].ids.questionCal.opacity = 0
        w.children[0].ids.calTestOk.opacity = 0
        w.children[0].ids.smile.opacity = 0
        w.children[0].ids.sad.opacity = 0
        w.children[0].ids.calTestOk.disabled = True
        w.children[0].ids.calTestNotOk.opacity = 0
        w.children[0].ids.calTestNotOk.disabled = True

#------------Print test--------------------------------------
    def printFile(self):
        self.isCalibration = False
        fileToPrint = []
        with open('printTest/fileToPrint.txt', 'r') as f:
            fileToPrint += f.readlines()
            fileToPrint = [x.strip() for x in fileToPrint]
        for version in fileToPrint:
            found = re.search("path=", version)
            if found:
                if self.slicePressedAndNotEmpty() is not None:
                    serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
                    for printer in self.connectANewPrinter.connectedPrinters:
                        if int(printer[0]['Serial Number']) == int(serialNumber):
                            printer[1].beep()
                            printer[1].transferSDFile(version.split("=", 1)[1])
                            while True:
                                print printer[1].getTransferState()
                                if printer[1].getTransferState() == 1.0:
                                    time.sleep(2)
                                    while True:
                                        printer[5].write("M504\r\n")
                                        aux = printer[5].readline()
                                        print aux
                                        if (aux == "reset done \n"):
                                            break
                                    printer[1].startSDPrint()
                                    printer[0]['Initial Time'] = time.time()
                                    break
                            if self.slicePressed() is not None:
                                self.slicePressed().text = self.connectANewPrinter.listOfDictToArray(
                                    printer[0])
                            self.resetSlicePressed()
                            printer[0]['State'] = "SD_Print"
                            time.sleep(2)

    cancelPrint = False
    spentFil = ""
    def timerPrintTest(self,dt):
        w = self.root.ids.sm
        if self.slicePressedAndNotEmpty() != None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":",1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    if printer[0]['State'] == 'SD_Print':
                        printVariables = printer[1].getPrintVariables()
                        if len(printVariables) != 0:
                            try:
                                w.children[0].ids.cancelPrint.disabled = False
                                w.children[0].ids.LUWhiteFilament.disabled = True
                                executedLines = printVariables['Executed Lines']
                                totalLines = printVariables['Lines']
                                w.children[0].ids.timeRemain.text = "(Aprox. " + str(int(printVariables['Estimated Time'])- int(printVariables['Elapsed Time'])) + " minutes left.)"
                                w.children[0].ids.printTest.value = ((executedLines * 100) / totalLines)
                                if executedLines == totalLines:
                                    printer[0]['Final Time'] = time.time() - printer[0]['Initial Time']
                                    printer[2].write("Elapsed time printing: " + str( int(round(printer[0]['Final Time'] / 60, 2))) + " minutes " + str(
                                                                                        round(printer[0]['Final Time'], 2) % 60) + " sec\n")
                                    while True:
                                        printer[5].write("M506 S1\r\n")
                                        self.spentFil = printer[5].readline()
                                        t = (self.spentFil.replace("\n",""),)
                                        if self.spentFil.find("mm"):
                                            self.c.execute(
                                                "UPDATE printersTest set spentFilament = ? where initialDateTime = '" +
                                                printer[3] + "'", t)
                                            self.conn.commit()
                                            break
                                    t = (str(int(round(printer[0]['Final Time'] / 60, 2))) + " min " + str(
                                        round(printer[0]['Final Time'], 2) % 60) + " s",)
                                    self.c.execute(
                                        "UPDATE printersTest set timePrinting = ? where initialDateTime = '" + printer[3] + "'",
                                        t)
                                    self.conn.commit()
                                    #verificar melhor esta parte
                                    printer[2].write("Spent Filament: " + self.spentFil)
                                    printer[2].close()
                                    t = ('database/' + str(printer[0]['Product']) + '_Address_'
                                         + str(printer[0]['Address']),)
                                    self.c.execute(
                                        "UPDATE printersTest set fileInfo = ? where initialDateTime = '" + printer[
                                            3] + "'",
                                        t)
                                    self.conn.commit()
                                    printer[0]['State'] = "Ready"
                                    w.children[0].ids.timeRemain.text = "(0 minutes left.)    "
                                    self.changeButtons()
                            except KeyError:
                                pass
                        if self.cancelPrint == True:
                            printer[1].cancelPrint()
                            self.closeSpecificConn(printer)
                            self.cancelPrint = False
                    else:
                        printVariables = printer[1].getPrintVariables() #test this
                        if len(printVariables) != 0:
                            w.children[0].ids.cancelPrint.disabled = True
                            w.children[0].ids.LUWhiteFilament.disabled = False


    def closeSpecificConn(self,printer):
        w = self.root.ids.sm
        printer[1].beep()
        printer[1]._beeCon.close()
        self.connectANewPrinter.connectedPrinters.remove(printer)
        if self.slicePressedAndNotEmpty() is not None:
            self.slicePressedAndNotEmpty().text = 'Empty'
        w.children[0].ids.sm.current = 'screen1'
        self.resetSlicePressed()
        for aux in self.printerWithPic:
            print aux[0]
            if printer[0]['Serial Number'] in aux[0]:
                self.printerWithPic.remove(aux)


    def changeButtons(self):
        w = self.root.ids.sm
        w.children[0].ids.cancelPrint.disabled = True
        w.children[0].ids.LUWhiteFilament.disabled = False

#------------------ Load Unload with transparent filament----------------
    def loadFilamentTrans(self):
        if self.slicePressedAndNotEmpty() != None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":",1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    printer[1].beep()
                    printer[1].load()

    def unloadFilamentTrans(self):
        if self.slicePressedAndNotEmpty() != None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":",1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    printer[1].beep()
                    printer[1].unload()

    def closeCon(self):
        w = self.root.ids.sm
        if self.slicePressedAndNotEmpty() != None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":",1)[1]
            for printer in self.connectANewPrinter.connectedPrinters:
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    printer[1].beep()
                    printer[1]._beeCon.close()
                    self.connectANewPrinter.connectedPrinters = self.connectANewPrinter.connectedPrinters[:-1]
                    if self.slicePressedAndNotEmpty() is not None:
                        self.slicePressedAndNotEmpty().text = 'Empty'
                    w.children[0].ids.sm.current = 'screen1'
                    self.resetSlicePressed()

#--------------- Info about specific printer-----------------
    def getInfo(self):
        w = self.root.ids.sm
        if self.slicePressedAndNotEmpty() != None:
            serialNumber = self.slicePressedAndNotEmpty().text.split(":", 1)[1]
            print serialNumber
            for printer in self.connectANewPrinter.connectedPrinters:
                print printer[0]
                if int(printer[0]['Serial Number']) == int(serialNumber):
                    for rows in self.c.execute("Select * from printersTest where serialNumber = ?", (int(serialNumber),)):
                        if str(rows[2]) not in w.children[0].ids.initialDateTime.adapter.data:
                            w.children[0].ids.initialDateTime.adapter.data.append(str(rows[2]))
                            w.children[0].ids.timeHeating.adapter.data.append(str(rows[3]))
                            w.children[0].ids.timePrinting.adapter.data.append(str(rows[4]))
                            w.children[0].ids.spentFilament.adapter.data.append(str(rows[5]))
                        if printer[0]['State'] == 'Ready':
                            w.children[0].ids.timePrinting.adapter.data.pop(-1)
                            w.children[0].ids.spentFilament.adapter.data.pop(-1)
                            w.children[0].ids.timePrinting.adapter.data.insert(len(w.children[0].ids.timePrinting.adapter.data),str(rows[4]))
                            w.children[0].ids.spentFilament.adapter.data.insert(len(w.children[0].ids.spentFilament.adapter.data),str(rows[5]))

    def resetListViews(self):
        w = self.root.ids.sm
        w.children[0].ids.initialDateTime.adapter.data = ["Initial Date"]
        w.children[0].ids.timeHeating.adapter.data = ["Heat time"]
        w.children[0].ids.timePrinting.adapter.data = ["Print time"]
        w.children[0].ids.spentFilament.adapter.data = ["Spent fil"]

if __name__ == '__main__':
    ShowcaseApp().run()

import logging
import time as time2

from BEEtec import Popups
from threading import Thread

# connection = imp.load_source('module.name', 'C:/Users/fmcta/Desktop/BeeVeryCreative/BEEtec/BEEcom/beedriver/connection.py')
from BEEcom.beedriver import connection

logger = logging.getLogger('beeconsole')
logger.setLevel(logging.INFO)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# add the handlers to logger
logger.addHandler(ch)

logThread = None

class Connection:

    connectedPrinters = []
    beeConn = None
    beeCmd = None
    initialDateTime = None
    exit = False
    alreadyConnected = False
    cantConnect = True
    exitState = None

    mode = "None"

    def connect(self,root,view_connecting):
        self.initialDateTime = time2.strftime("%x")
        self.initialDateTime += ' ' + time2.strftime("%X")
        self.alreadyConnected = False
        self.exit = False
        self.cantConnect = True
        nextPullTime = time2.time() + 1
        logger.info("Waiting for printer connection...")
        count = 0
        self.beeConn = connection.Conn()
        initialPrinters = self.beeConn.getPrinterList()
        disconnect = False
        connect = False
        newSN = None
        timeToDisconnectPrinter = time2.time()
        while time2.time() - timeToDisconnectPrinter <= 9:
            try:
                printerlist = self.beeConn.getPrinterList()
            except:
                pass
            if(len(printerlist) == 0) and len(initialPrinters) == 0:
                disconnect = True
                connect = True
                break
            if len(printerlist) == len(initialPrinters) + 1:
                for i in printerlist:
                    for x in initialPrinters:
                        if i['Serial Number'] not in x['Serial Number']:
                            newSN = i['Serial Number']
                disconnect = True
                connect = True
                break
            if len(printerlist) == len(initialPrinters) - 1:
                disconnect = True
                if printerlist != []:
                    for i in initialPrinters:
                        for x in printerlist:
                            if i['Serial Number'] not in x['Serial Number']:
                                newSN = i['Serial Number']
                else:
                    newSN = initialPrinters[0]['Serial Number']
                timeToConnectPrinter = time2.time()
                while(time2.time() - timeToConnectPrinter <= 6):
                    printerlist = self.beeConn.getPrinterList()
                    if len(printerlist) == len(initialPrinters):
                        for i in range(0,len(printerlist)-1 if len(printerlist) > 1 else len(printerlist)):
                            if printerlist[i]['Serial Number'] != initialPrinters[i]['Serial Number']:
                                newSN = printerlist[i]['Serial Number']
                                print newSN
                        connect = True
                        break
                break
        print connect
        print disconnect
        if disconnect == True and connect == True:
            while (not self.alreadyConnected) and (not self.exit) and count <= 5:
                t = time2.time()
                if t > nextPullTime:
                    count += 0.25
                    printerlist = self.beeConn.getPrinterList()
                    if len(initialPrinters) == 0 and printerlist != []:
                        newSN = printerlist[0]['Serial Number']
                    for printer in printerlist:
                        if printer['Serial Number'] not in [self.connectedPrinters[i][0]['Serial Number'] for i in
                                                                                    range(0, len(self.connectedPrinters))] and printer['Serial Number'] == newSN:
                            self.beeConn.connectToPrinter(printer)
                            if self.beeConn.isConnected() is True:
                                self.beeCmd = self.beeConn.getCommandIntf()
                                self.mode = self.beeCmd.getPrinterMode()
                                if self.mode is None:
                                    logger.info('Printer not responding... cleaning buffer\n')
                                    self.beeCmd.cleanBuffer()
                                    self.beeConn.close()
                                    self.beeConn = None
                                    self.cantConnect = True
                                    self.alreadyConnected = False
                                    # return None
                                # Printer ready
                                else:
                                    saveInf = open('database/'+ str(printer['Product']) + '_Address_'
                                                   + str(self.beeConn.dev.address)+'.txt','w')
                                    self.connectedPrinters.append([printer,self.beeCmd,saveInf,self.initialDateTime,False,None])
                                    self.connectedPrinters[-1][0]["Address"] = self.beeConn.dev.address
                                    self.connectedPrinters[-1][0]["State"] = self.beeCmd.getStatus()
                                    self.connectedPrinters[-1][0]["Initial Time"] = 0.0
                                    self.connectedPrinters[-1][0]["Final Time"] = 0.0
                                    self.connectedPrinters[-1][2].write(
                                        self.listOfDictToArray(self.connectedPrinters[-1][0])+ ' Data de inicio: ' + str(self.initialDateTime) +'\n')
                                    w = root.ids.sm
                                    self.cantConnect = False
                                    self.exit = True
                                    break
                        else:
                            print count
                            if(float(count) == 2.5):
                                    self.cantConnect = False
                                    self.alreadyConnected = True
                                    break
                    nextPullTime = time2.time() + 1
        if disconnect == True:
            if self.cantConnect == False:
                if self.alreadyConnected:
                    view_connecting.dismiss()
                    time2.sleep(1)
                    logger.info('Printer already connected\n')
                    Popups.mantainWarning(self.alreadyConnected)
                else:
                    view_connecting.dismiss()
                    logger.info('Printer started in %s mode\n' % self.mode)
            else:
                logger.info('No printer found')
                view_connecting.dismiss()
                time2.sleep(1)
                Popups.mantainWarning(self.alreadyConnected)
        else:
            view_connecting.dismiss()
            time2.sleep(1)
            Popups.disconnectPrinter()

    def listOfDictToArray(self,printer):
        return str(printer['Product']) + ", " + "Serial number: " + str(printer['Serial Number'])

    def getConnectedPrinters(self):
        return self.connectedPrinters

    def canConnect(self):
        if self.cantConnect == False:
            if self.alreadyConnected == True:
                return False
            else:
                return True
        else:
            return False

    def getConn(self):
        return self.beeConn

    def getCmd(self):
        return self.beeCmd

    def existsAnEmptySlice(self,root,printer):
        w = root.ids.sm
        if(w.children[0].ids.firstPrinter.text == 'Empty'):
            w.children[0].ids.firstPrinter.text = self.listOfDictToArray(printer)
        elif w.children[0].ids.secondPrinter.text == 'Empty':
            w.children[0].ids.secondPrinter.text = self.listOfDictToArray(printer)
        elif w.children[0].ids.thirdPrinter.text == 'Empty':
            w.children[0].ids.thirdPrinter.text = self.listOfDictToArray(printer)
        elif w.children[0].ids.fourPrinter.text == 'Empty':
            w.children[0].ids.fourPrinter.text = self.listOfDictToArray(printer)
        else:
            print 'Nao existe espaco livre'

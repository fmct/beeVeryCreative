from kivy.uix.popup import ModalView
from kivy.uix.label import Label
from time import sleep
import threading, time



class ModalViewCustom(ModalView):
    pass

#------------------Connection------------------------#
def mantainWarning(alreadyConnected):
    view = ModalViewCustom(size_hint=(None, None), size=(450, 150))
    if(alreadyConnected == True):
        view.add_widget(Label(text='Printer Already Connected', font_size="30dp", color=(1, 0, 0, 1)))
    else:
        view.add_widget(Label(text='Printer Busy or not connected', font_size="30dp", color=(1, 0, 0, 1)))
    view.open()

def connectedTo(mode):
    view = ModalViewCustom(size_hint=(None, None), size=(500, 150))
    view.add_widget(Label(text='Printer started in %s mode\n' % mode, font_size="30dp", color=(0, 1, 0, 1)))
    view.open()

def picAlreadyConnected(printer):
    view = ModalViewCustom(size_hint=(None, None), size=(520, 150))
    view.add_widget(Label(text='Pic already connected to %s\n' % str(printer), font_size="30dp", color=(0, 1, 0, 1)))
    view.open()

def connecting():
    view = ModalViewCustom(size_hint=(None, None), size=(500, 150))
    view.add_widget(Label(text='Connecting...\n', font_size="30dp", color=(0, 1, 0, 1)))
    view.open()
    return view

def printerDisc():
    view = ModalViewCustom(size_hint=(None, None), size=(500, 150))
    view.add_widget(Label(text='Printer Disconnected\n', font_size="30dp", color=(1, 0, 0, 1)))
    view.open()
    time.sleep(2)
    view.dismiss()

def canceling():
    view = ModalViewCustom(size_hint=(None, None), size=(500, 150))
    view.add_widget(Label(text='Canceling...\n', font_size="30dp", color=(0, 1, 0, 1)))
    view.open()
    return view

def already100():
    view = ModalViewCustom(size_hint=(None, None), size=(500, 150))
    view.add_widget(Label(text='Already on 100 %...\n', font_size="30dp", color=(1, 0, 0, 1)))
    view.open()

def sliceNotEmpty():
    view = ModalViewCustom(size_hint=(None, None), size=(500, 150))
    view.add_widget(Label(text='That slice is not empty\n', font_size="30dp", color=(1, 0, 0, 1)))
    view.open()

def disconnectPrinter():
    view = ModalViewCustom(size_hint=(None, None), size=(500, 150))
    view.add_widget(Label(text='Disconnect and connect a Printer\n', font_size="30dp", color=(1, 0, 0, 1)))
    view.open()
#-----------------Serial Number----------------------------------#
def notInt():
    view = ModalViewCustom(size_hint=(None, None), size=(450, 150))
    view.add_widget(Label(text='The text inserted is not a number!\n', font_size="30dp", color=(1, 0, 0, 1)))
    view.open()

def notRightSize():
    view = ModalViewCustom(size_hint=(None, None), size=(450, 150))
    view.add_widget(Label(text='Please enter a 10 digit number!\n', font_size="30dp", color=(1, 0, 0, 1)))
    view.open()

def insertedACorrectNumber():
    view = ModalViewCustom(size_hint=(None, None), size=(450, 150))
    view.add_widget(Label(text='Entered number successfully\n', font_size="30dp", color=(0, 1, 0, 1)))
    view.open()

def notInBootloader():
    view = ModalViewCustom(size_hint=(None, None), size=(510, 150))
    view.add_widget(Label(text='The printer is not in Bootloader mode\n', font_size="30dp", color=(1, 0, 0, 1)))
    view.open()

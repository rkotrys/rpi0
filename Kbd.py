# -*- coding:utf-8 -*-
import time, datetime, sys, os, io
import threading
import subprocess as proc
import RPi.GPIO as GPIO

#GPIO define
KEY_UP_PIN     = 6 
KEY_DOWN_PIN   = 19
KEY_LEFT_PIN   = 5
KEY_RIGHT_PIN  = 26
KEY_PRESS_PIN  = 13
KEY1_PIN       = 21
KEY2_PIN       = 20
KEY3_PIN       = 16


#init GPIO
# for P4:
# sudo vi /boot/config.txt
# gpio=6,19,5,26,13,21,20,16=pu
GPIO.setmode(GPIO.BCM) 
GPIO.setup(KEY_UP_PIN,      GPIO.IN, pull_up_down=GPIO.PUD_UP)    # Input with pull-up
GPIO.setup(KEY_DOWN_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_LEFT_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_RIGHT_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY_PRESS_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY1_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Input with pull-up
GPIO.setup(KEY2_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Input with pull-up
GPIO.setup(KEY3_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Input with pull-up

class Kbd:
    buttons = { 'k1':0, 'k2':0, 'k3':0, 'up':0, 'down':0, 'left':0, 'right':0, 'enter':0 }
    keyid =   {'k1':KEY1_PIN,'k2':KEY2_PIN,'k3':KEY3_PIN, 
               'up':KEY_UP_PIN, 'down':KEY_DOWN_PIN, 'left':KEY_LEFT_PIN, 'right':KEY_RIGHT_PIN, 'enter':KEY_PRESS_PIN }
    handler = { 'k1':0, 'k2':0, 'k3':0, 'up':0, 'down':0, 'left':0, 'right':0, 'enter':0 }           
    
    def __init__(self):
        for k in self.handler.keys():
            self.handler[k] = self.keyhandle;
        self.x = threading.Thread( name='keydrv', target=self.keydrv, args=(0.1,), daemon=True)
        self.x.start()
    
    def keydrv( self, period ):
        while 1:
            self.read()
            time.sleep(period)
    
    def keyhandle( self, name, state ):
        print( u'{} is {}'.format( name, state ) )
        
    def sethanddle( self, name, handle ):
        self.handler[name] = handle
        
    def key(self,name):
        Kbd.read(self)
        return Kbd.buttons[name]     

    def read(self):
        for k in Kbd.buttons.keys():
            if GPIO.input(Kbd.keyid[k]): # button is released
                if Kbd.buttons[k] == 1:
                    Kbd.buttons[k] = 0
                    if callable(Kbd.handler[k]): 
                        Kbd.handler[k](k,'UP') 
            else: # button is pressed:
                if Kbd.buttons[k] == 0:
                    Kbd.buttons[k] = 1;
                    if callable(Kbd.handler[k]): 
                        Kbd.handler[k](k,'Down') 


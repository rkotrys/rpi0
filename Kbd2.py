#!/usr/bin/python
# -*- coding:utf-8 -*-

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

class Kbd2:
    keyid =   {'k1':KEY1_PIN,   'k2':KEY2_PIN,       'k3':KEY3_PIN,
               'up':KEY_UP_PIN, 'down':KEY_DOWN_PIN, 'left':KEY_LEFT_PIN, 'right':KEY_RIGHT_PIN, 'enter':KEY_PRESS_PIN }
    handler = { 'k1':0, 'k2':0, 'k3':0, 'up':0, 'down':0, 'left':0, 'right':0, 'enter':0 }

    def __init__(self):
        self.keynames = {v: k for k, v in Kbd2.keyid.items()}
        for k in self.handler.keys():
            self.handler[k] = self.keyhandle;
            GPIO.add_event_detect(Kbd2.keyid[k], GPIO.RISING, callback=self.handler[k], bouncetime=200)

    def keyhandle( self, pin  ):
        print( u'{} is pressed'.format( self.keynames[ pin ]  ) )

    def sethanddle( self, name, handle ):  
        GPIO.remove_event_detect( Kbd2.keyid[name] )
        self.handler[name] = handle
        GPIO.add_event_detect(Kbd2.keyid[name], GPIO.RISING, callback=self.handler[name], bouncetime=200)


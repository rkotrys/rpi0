#!/usr/bin/python
# -*- coding:utf-8 -*-

# /*****************************************************************************
# * | File        :	  showclock.py
# * | Author      :   Robert Kotrys
# * | Function    :   LCD 1.44' control app use with Raspberry Pi link service
# * | Info        :   require files: Kbd2.py, Clock.py, rplink.py, helper.py
# *----------------
# * | This version:   1.0.1
# * | Date        :   2022-01-23
# * | Info        :   include 'showclock' run file and 'lcd144.service'
# ******************************************************************************/



import time, sys, signal
#from functools import partial
import RPi.GPIO as GPIO
import Kbd2, Clock, rplink

# global components
kbd=None
clk=None
rpl=None
def main():
    # global components
    global kbd, clk, rpl
    #
    # command line args read 
    # usage:  python3 showclock.py <rpihub_address> <link period>
    link_address=sys.argv[1] if len(sys.argv)>1 else 'rpi.ontime24.pl'
    link_period=int(sys.argv[2]) if len(sys.argv)>2 else 1

    try:
        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigterm_handler)
        signal.signal(signal.SIGHUP, sighup_handler)
    
        # init global components
        # keyboard driver
        kbd = Kbd2.Kbd2()
        # 'rplink' and 'Clock' object create and init
        clk = Clock.clock(kbd)
        rpl=rplink.rplink(display='lcd144', rpilink_address=link_address, rpilink_period=link_period,localdata={'theme':clk.cnf["global"]["theme"]})
        rpl.set_clk_insance(clk)
        rpl.setlocaldata( {'msdid':clk.df['msdid'], 'essid':clk.df['essid'], 'coretemp':clk.df['coretemp'], 'memavaiable':clk.df['memavaiable'], 'cpus':clk.df['cpus']} )
        clk.menu.load("menu.csv")
        clk.set_rpl(rpl)

        # set kbd handlers
        # kbd.sethanddle( 'k3', clk.nextbk )
        kbd.sethanddle( 'k2', clk.sinfo )
        kbd.sethanddle( 'k1', clk.sinfo2 )
        kbd.sethanddle( 'left', clk.menu.start )
        #kbd.sethanddle( 'right', clk.menu.stop )
        kbd.sethanddle( 'enter', clk.menu.run )
        kbd.sethanddle( 'up', clk.menu.previous )
        kbd.sethanddle( 'down', clk.menu.next )

        # run main thread loop
        clk.run()

        while clk.go:
            time.sleep(3)
        clk.LCD.LCD_Clear()

    except IOError as e:
        print(e)
        rpl.logger.debug( u'[{}] detect IOError {}'.format(rpl.display, e) )
        clk.LCD.LCD_Clear()
        clk.go=False
        rpl.go=False
        rpl.stop()
        time.sleep(1)
        GPIO.cleanup()
        sys.exit( 0 )
        
    except KeyboardInterrupt:    
        rpl.logger.debug( u'[{}] exit by KeyboardInterrupt {}'.format(rpl.display) )
        clk.LCD.LCD_Clear()
        clk.go=False
        rpl.go=False
        rpl.stop()
        time.sleep(1)
        GPIO.cleanup()
        sys.exit( 0 )
    


# sugnal handlers
def sigint_handler(signum, frame):
    global clk,rpl
    rpl.logger.debug( u'[{}] exit by sigint'.format(rpl.display) )
    clk.LCD.LCD_Clear()
    clk.go=False
    rpl.go=False
    rpl.stop()
    time.sleep(1)
    GPIO.cleanup()
    sys.exit( 0 )    

def sigterm_handler(signum, frame):
    global clk, rpl
    rpl.logger.debug( u'[{}] exit by sigterm'.format(rpl.display) )
    clk.LCD.LCD_Clear()
    clk.go=False
    rpl.go=False
    rpl.stop()
    time.sleep(1) 
    GPIO.cleanup()
    sys.exit( 0 )    

def sighup_handler(signum, frame):
    global clk, rpl
    rpl.logger.debug( u'[{}] get SIGHUP'.format(rpl.display) )

if __name__ == '__main__':
    main()
    GPIO.cleanup()


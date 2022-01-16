import time, sys
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
    # init global components
    kbd = Kbd2.Kbd2()
    clk = Clock.clock(kbd)
    clk.menu.load("menu.csv")
    # 'rplink' object create and init
    rpl=rplink.rplink(display='lcd144', rpilink_address='rpi.ontime24.pl', rpilink_period=2,localdata={'theme':clk.cnf["global"]["theme"]})
    rpl.set_clk_insance(clk)
    rpl.setlocaldata( {'msdid':clk.df['msdid'], 'essid':clk.df['essid'], 'coretemp':clk.df['coretemp'], 'memavaiable':clk.df['memavaiable'], 'cpus':clk.df['cpus']} )

    # set kbd handlers
    kbd.sethanddle( 'k3', clk.nextbk )
    kbd.sethanddle( 'k2', clk.sinfo )
    kbd.sethanddle( 'k1', clk.sinfo2 )
    kbd.sethanddle( 'left', clk.menu.start )
    #kbd.sethanddle( 'right', clk.menu.stop )
    kbd.sethanddle( 'enter', clk.menu.run )
    kbd.sethanddle( 'up', clk.menu.previous )
    kbd.sethanddle( 'down', clk.menu.next )

    # run main thread
    clk.run()

if __name__ == '__main__':
    main()
    GPIO.cleanup()


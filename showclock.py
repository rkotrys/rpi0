import time, math, sys, csv
import subprocess as proc
from functools import partial
import RPi.GPIO as GPIO
import Kbd2, Clock

def main():
    kbd = Kbd2.Kbd2()
    clk = Clock.clock(kbd)
    clk.menu.load("menu.csv")

    kbd.sethanddle( 'k3', clk.nextbk )
    kbd.sethanddle( 'k2', clk.sinfo )
    kbd.sethanddle( 'k1', clk.sysexit )
    kbd.sethanddle( 'left', clk.menu.start )
    #kbd.sethanddle( 'right', clk.menu.stop )
    kbd.sethanddle( 'enter', clk.menu.run )
    kbd.sethanddle( 'up', clk.menu.previous )
    kbd.sethanddle( 'down', clk.menu.next )

    clk.run()

if __name__ == '__main__':
    main()
    GPIO.cleanup()


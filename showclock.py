import time, math, sys, csv
import subprocess as proc
from functools import partial
import Kbd2, Clock

#def sinfo(name, state):
#    print(u'Showinfo')


#try:
def menuload(filename):
    menucontent = []
    with open('menu.csv') as csvfile:
        r = csv.reader( csvfile )
        first = True
        for row in r:
            if first:
                first = False
                continue
            if row[0][0] == '#':
                continue
            row[0] = row[0].replace(u'|',u'\n')
            menucontent.append( row )
    return menucontent if len(menucontent)>0 else False

def myexec( label='', menu=False, arg=False ):
    if arg==False:
        return
    a = []
    for item in arg.split(' '):
        if item != '':
            a.append(item)
    r = str(proc.check_output( a ), encoding='utf-8').strip()
    print( label, r, '\n' )
    menu.active = False
#    return r


def pr0( label, menu ):
    if menu.parent.showinfo:
        menu.parent.sinfo('k2','UP')
    else:
        menu.parent.sinfo('k2','Down')
    menu.active = False

def pr1( label, menu ):
    proc.run(['/etc/netconf/setdhcpcd'])
    menu.active = False

def pr2( label, menu ):
    proc.run(['/etc/netconf/set_eth0_20.22'])
    menu.active = False

def pr3( label, menu ):
    proc.run(['/etc/netconf/set_eth0_40.22'])
    menu.active = False

def pr4( label, menu ):
    menu.active = False
    proc.run(['reboot','now'])
    time.sleep(3)

def pr5( label, menu ):
    menu.active = False
    proc.run(['shutdown','now'])
    time.sleep(3)

def py_call( toexec=None, label="label", menu=None ):
    print( label )
    if toexec != None:
        exec( toexec )
    


def main():
    m = menuload( 'menu.csv' )
    kbd = Kbd2.Kbd2()
    clk = Clock.clock(kbd)
    for item in m:
        if item[1] == 'f':
            clk.menu.add(item[0], partial( myexec, arg=item[2] ) )
#            print( 'menu: ', item[2] )
        if item[1] == 'p':
            clk.menu.add(item[0], partial( py_call, item[2] ) )

#    clk.menu.add('INFO', pr0 )
#    clk.menu.add('SET: dhcpcd', pr1 )
#    clk.menu.add('192.168.20.22', pr2 )
#    clk.menu.add('192.168.40.22', pr3 )
#    clk.menu.add('REBOOT', pr4 )
#    clk.menu.add('SHUTDOWN', pr5 )

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

#except:
#   print("except")
#   GPIO.cleanup()

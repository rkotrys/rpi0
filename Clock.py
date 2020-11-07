import time, math,sys,sched
import subprocess as proc
import threading
#import numpy as np
#import tr
import LCD_1in44
import LCD_Config

from PIL import Image,ImageDraw,ImageFont,ImageColor,ImageFilter
import Menu, Appconfig
import helper as hlp

class clock:
    images = ""
    backs = {}
    icons = {}
    cnf = None

    def __init__(self,kbd):
        clock.cnf = Appconfig.Appconfig("rpi0.ini")
        self.cnf = clock.cnf.dml
        clock.images = self.cnf["global"]["images"]
        for n in self.cnf["clock"]["icons"]:
            clock.icons[n] = int( self.cnf["clock"]["icons"][n], 16 )
        self.sheduler = sched.scheduler(time.time, time.sleep)
        self.cpu = 0
        self.mem = 0
        self.ind = 0
        self.bcolor = []
        self.wifi = []
        self.go = True
        self.msg = ""
        self.info = ""
        self.btscan = False
        self.btscan_count = 60
        self.showinfo = False
        self.btdev = {}
        self.kbd = kbd
        self.isonline = False
        self.btscan_color = tuple(self.cnf["clock"]["btscan_color"])
        self.s_color = tuple(self.cnf["clock"]["s_color"])
        self.m_color = tuple(self.cnf["clock"]["m_color"])
        self.h_color = tuple(self.cnf["clock"]["h_color"])
        self.outline_color = tuple(self.cnf["clock"]["outline_color"])
        self.arrowsize_h = self.cnf["clock"]["h_arrowsize"]
        self.arrowsize_m = self.cnf["clock"]["m_arrowsize"]
        self.arrowsize_s = self.cnf["clock"]["s_arrowsize"]
        self.menu = Menu.Menu( (128,128), [(3,63-12),(125,63+15)], self )

        for n in self.cnf["clock"]["faces"]:
            clock.backs[n] = Image.open( self.cnf["global"]["images"] + self.cnf["clock"]["faces"][n] ).resize( (128,128),Image.BICUBIC)
        self.icons = self.cnf["clock"]["icons"]
        self.font = ImageFont.truetype( self.cnf["global"]["fonts"]+self.cnf["clock"]["font_bold"], self.cnf["clock"]["font_bold_size"] )
        self.font12 = ImageFont.truetype(self.cnf["global"]["fonts"]+self.cnf["clock"]["font_mono"], self.cnf["clock"]["font_mono_size"])
        self.symbols = ImageFont.truetype(self.cnf["global"]["fonts"]+self.cnf["clock"]["font_symbol"], self.cnf["clock"]["font_symbol_size"])
        self.symbols_large = ImageFont.truetype(self.cnf["global"]["fonts"]+self.cnf["clock"]["font_symbol"], self.cnf["clock"]["font_symbol_large_size"])

        self.LCD = LCD_1in44.LCD()
        Lcd_ScanDir = LCD_1in44.SCAN_DIR_DFT  #SCAN_DIR_DFT = D2U_L2R
        self.LCD.LCD_Init(Lcd_ScanDir)
        self.LCD.LCD_Clear()
        self.x_cpuload = threading.Thread( name='cpuload', target=self.runcpu, args=(), daemon=True)
        self.x_cpuload.start()
        self.x_isonlinecheck = threading.Thread( name='isonlinecheck', target=self.isonlinecheck, args=('8.8.8.8'), daemon=True)
        self.x_isonlinecheck.start()

    def drawhands( self, t, r, image ):
        x = int(image.size[0]/2)
        y = int(image.size[1]/2)
        im = Image.new( "RGBA", image.size, (255,255,255,0) )
        dr = ImageDraw.Draw( im )
        dr.polygon( [(x-3,y), (x+3,y), (x+3,r[2]), (x+6,r[2]),(x,r[2]-self.arrowsize_h),(x-6,r[2]),(x-3,r[2])], fill=self.h_color, outline=self.outline_color )
        h = t[0] if t[0]<13 else t[0]-12
        him = im.rotate( -(h*30+t[1]*0.5), Image.BICUBIC )
        im = Image.new( "RGBA", image.size, (255,255,255,0) )
        dr = ImageDraw.Draw( im )
        dr.polygon( [(x-2,y), (x+2,y), (x+2,r[1]),(x+5,r[1]),(x,r[1]-self.arrowsize_m),(x-5,r[1]), (x-2,r[1])], fill = self.h_color, outline=self.outline_color )
        hmim =Image.alpha_composite( him, im.rotate( -(360*t[1])/60, Image.BICUBIC ) )
        im = Image.new( "RGBA", image.size, (255,255,255,0) )
        dr = ImageDraw.Draw( im )
        dr.line([ ( x, y+20 ), ( x, r[0]+self.arrowsize_h)], fill = self.s_color, width = 2 )
        dr.line([ ( x-3, r[0]+self.arrowsize_s ), ( x, r[0]), ( x+3, r[0]+self.arrowsize_s ), ( x-3, r[0]+self.arrowsize_s )], fill = self.s_color, width = 2 )
        dr.ellipse([x-7,y-7,x+7,y+7],fill=self.s_color,outline='#777')
        return Image.alpha_composite( hmim, im.rotate( -(360*t[2])/60, Image.BICUBIC ) )

    def isonlinecheck(self, ip='8.8.8.8'):
        while self.go:
            try:
                r = str(proc.check_output(['/bin/ping', '-c', '3', '-i', '0.2', '-w', '1', '-q', ip] ), encoding='utf-8').strip()
            except proc.CalledProcessError:
                r = '0 received'
            ind = int(r.find(' received'))
            if( int(r[ind-1:ind]) > 0 ):
                self.isonline=True
            else:
                self.isonline=False
            time.sleep(2)

    def runcpu(self):
        while self.go:
            memlines = str(proc.check_output(['free']), encoding='utf-8').strip().split('\n')
            cpulines = str(proc.check_output(['iostat','-c', '--dec=0', '1', '2']), encoding='utf-8').strip().split('\n')
            r = []
            for l in cpulines[7].split(' '):
                if l == '': continue
                r.append(int(l))
            self.cpu = r[5]
            r = []
            for l in memlines[1].split(' '):
                if l == '': continue
                r.append(l)
            self.mem = (100.0 * int(r[2])) / int(r[1]);
            time.sleep(2)

    def getnetdev(self):
        netdev={}
        with open('/proc/net/dev','r') as f:
            dev = f.read()
            for devname in ['eth0', 'eth1', 'wlan0', 'wlan1']:
                if dev.find(devname) > -1:
                    ip=str(proc.check_output([ 'ip', '-4', 'address', 'show', 'dev', devname ]), encoding='utf-8').strip().splitlines()[1].split()[1]
                    mac=str(proc.check_output([ 'ip', 'link', 'show', 'dev', devname ]), encoding='utf-8').strip().splitlines()[1].split()[1]
                    netdev[devname]=(devname,ip,mac)
        return netdev            

    def drowclockface(self):        
        iconcolor = tuple(self.cnf["clock"]["icons_color"])
        btscan_color = tuple(self.cnf["clock"]["btscan_color"])
        tm = time.localtime()
        image = clock.backs[self.cnf["global"]["theme"]].copy()
        self.clock_image = image
        im = Image.new( "RGBA", image.size, (0,0,0,255) )
        im.paste(image)
        draw = ImageDraw.Draw(im)
        draw.rectangle([(127-3,127),(127,int(127*(self.cpu/100.0)))], fill=tuple(self.cnf["clock"]["cpu_color"]), outline=tuple(self.cnf["clock"]["cpu_color_outline"]), width=1)
        draw.rectangle([(0,127),(3,int(127*(1 - self.mem/100.0)))], fill=tuple(self.cnf["clock"]["mem_color"]), outline=tuple(self.cnf["clock"]["mem_color_outline"]), width=1)
        with open('/sys/class/thermal/thermal_zone0/temp','r') as f:
            tempraw = f.read()
        self.msg = u"{}".format(tempraw[0:2]) + u'°'
        draw.text( ((128-self.font.getsize('40')[0])/2,82), self.msg, font=self.font, fill=iconcolor )
        hostname = str(proc.check_output(['hostname'] ), encoding='utf-8').strip()
        draw.text( ((128-self.font12.getsize(hostname)[0])/2,72), hostname, font=self.font12, fill=iconcolor )
        symbol = chr(clock.icons["wifi_off"])+u''
        wififlag=False
        ethflag=False
        for dev in self.netdev:
            if( dev[0][0:4]=='wlan' and dev[1]!="" ):
                symbol = chr(clock.icons["wifi"])+u''
                wififlag=True
                break
            if( dev[0][0:3]=='eth' and dev[1]!="" ):
                symbol = chr(clock.icons["eth"])+u''
                ethflag=True
                break
        if wififlag and ethflag:
            symbol = chr(clock.icons["wifi_eth"])+u''
            
        draw.text( (128-17,1), symbol, font=self.symbols, fill=iconcolor )
        if self.isonline:
            draw.text( (64-8,31), chr(clock.icons["globe"])+u'', font=self.symbols, fill=iconcolor )
        if self.btscan:
            draw.text( (1,1), chr(clock.icons["bt"])+u'', font=self.symbols, fill=self.btscan_color )
        else:
            draw.text( (1,1), chr(clock.icons["bt"])+u'', font=self.symbols, fill=iconcolor )
        im = Image.alpha_composite( im, self.drawhands( (tm[3],tm[4],tm[5]), (12, 25, 35), image ) )
        return im

    def runclock(self):
        if self.go:
            self.sheduler.enter(1,1,self.runclock)

        self.netdev = self.getnetdev()
        im = self.drowclockface()

        """ KEY2 - buttons action """
        if self.showinfo:
           imtext = Image.new( "RGBA", self.clock_image.size, (0,0,0,0) )
           drawtext = ImageDraw.Draw(imtext)
           drawtext.rectangle([0,0,127,127], fill=tuple(self.cnf["clock"]["self_info_fill"]), outline=tuple(self.cnf["clock"]["self_info_outline"]), width=2)
           drawtext.multiline_text( (1,1), self.info, font=self.font12, fill=tuple(self.cnf["clock"]["self_info_font_fill"]) )

        """ menu images overlay """
        menu = self.menu.show()
        if menu:
            self.LCD.LCD_ShowImage( Image.alpha_composite(im,menu),0,0)
        else:
            if self.showinfo:
                self.LCD.LCD_ShowImage( Image.alpha_composite(im,imtext),0,0)
            else:
                self.LCD.LCD_ShowImage( im,0,0)

    def run(self):
        self.sheduler.enter(1,1,self.runclock)
        self.sheduler.run()
        while self.go:
            time.sleep(5)
        self.LCD.LCD_Clear()


    def btscan_flag(self):
        if self.btscan:
            self.btscan = False
        else:
            self.btscan = True
            self.btscan_run()
        self.menu.active=False    

    def btscan_run(self):
        if self.btscan:
            self.sheduler.enter(60,100,self.btscan_run )
        self.bt_th = threading.Thread( name='btscan', target=self.btscan_exec, args=(), daemon=True)
        self.bt_th.start()

    def btscan_exec(self):
        output=str(proc.check_output(['./btscan.sh'] ), encoding='utf-8').strip().splitlines()
        for line in output:
            if line.find("Scanning")==-1:
                btid=line.strip().split()
                if self.btdev.get(btid[0])==None:
                    btname=""
                    if len(btid)>1:
                        btname = " ".join(btid[1:])
                    self.btdev[btid[0]]=btname
                    with open('btdev.txt', 'a') as f:
                        f.write( "{} {}\n".format(btid[0], btname) )
        #for item in self.btdev.items():
        #    print( "{} {}".format(item[0],item[1]) )            
        #print( output )


    """  buttons on right callbaks """
    def nextbk( self, pin ):
        """ KEY3 """
        #print( "size:{} ind={}".format(len(clock.baks), self.ind) )
        ind = [*clock.backs].index(self.cnf["global"]["theme"])
        if ind == len(clock.backs)-1:
            ind = 0
        else:
            ind += 1
        self.cnf["global"]["theme"]=[*clock.backs][ind]
        clock.cnf.save()

    def sysexit( self=None, pin=None ):
        """ KEY1 """
        print("EXIT!")
        self.go = False

    def sinfo(self, pin ):
        """ KEY2 """
        if self.showinfo==True:
            self.showinfo = False
        else:
            self.showinfo=True
            wlan1ip = str(proc.check_output(['./showip', 'wlan1'] ), encoding='utf-8').strip()
            self.info = u'hostname: ' + str(proc.check_output(['hostname'] ), encoding='utf-8').strip()
            self.info = self.info + u'\neth0:\n' + str(proc.check_output(['./showip', 'eth0'] ), encoding='utf-8').strip()
            self.info = self.info + u'\n' + str(proc.check_output(['./showmac', 'eth0'] ), encoding='utf-8').strip()
            self.info = self.info + u'\nwlan0:' + (u', wlan1:\n' if wlan1ip != '' else u'\n') + str(proc.check_output(['./showip', 'wlan0'] ), encoding='utf-8').strip()
            self.info = self.info + u'\n' + str(proc.check_output(['./showmac', 'wlan0'] ), encoding='utf-8').strip()
            if wlan1ip != '':
                self.info = self.info + u'\n' + wlan1ip
                self.info = self.info + u'\n' + str(proc.check_output(['./showmac', 'wlan1'] ), encoding='utf-8').strip()

            self.showinfo = True
            self.isonline()
            #print(self.info)

import time, sched, sys
import subprocess as proc
import threading, requests, json, base64

from PIL.ImageDraw import Draw
import LCD_1in44
import LCD_Config

from PIL import Image,ImageDraw,ImageFont,ImageColor,ImageFilter
import Menu, Appconfig
# import rplink
# import helper_old as hlp
import helper as rph

class clock:
    images = ""
    backs = {}
    icons = {}
    cnf = None

    def __init__(self,kbd):
        #  config data
        clock.cnf = Appconfig.Appconfig("rpi0.ini")
        self.cnf = clock.cnf.dml
        #  clock icons
        clock.images = self.cnf["global"]["images"]
        for n in self.cnf["clock"]["icons"]:
            clock.icons[n] = int( self.cnf["clock"]["icons"][n], 16 )
        # sheduler    
        self.sheduler = sched.scheduler(time.time, time.sleep)
        # keyboard driver
        self.kbd = kbd
        # menu driver
        self.menu = Menu.Menu( (128,128), [(3,63-12),(125,63+15)], self )
        # rplink service - initialize after clock init
        self.rpl=None
        # run flag
        self.go = True
        # state data
        self.cpu = 0
        self.mem = 0
        self.ind = 0
        self.bcolor = []
        self.wifi = []
        self.msg = ""
        self.info = ""
        self.rpilink_address = 'rpi.ontime24.pl'
        # get rpi info 
        self.df=None
        self.netdev=None
        # set is on-line flag
        self.isonline_flag = False
        self.isapactive = rph.hostapd_active()
        # bluetooth params
        self.btscan = False
        self.btscan_show = False
        self.btdev = {}
        # show info flag
        self.showinfo = False
        # temperature alarm
        self.temp_cpu_alarm = 50
        # set curent date time flag
        self.curent_date_time = False
        # clock hands colors and size
        self.s_color = tuple(self.cnf["clock"]["s_color"])
        self.m_color = tuple(self.cnf["clock"]["m_color"])
        self.h_color = tuple(self.cnf["clock"]["h_color"])
        self.outline_color = tuple(self.cnf["clock"]["outline_color"])
        self.arrowsize_h = self.cnf["clock"]["h_arrowsize"]
        self.arrowsize_m = self.cnf["clock"]["m_arrowsize"]
        self.arrowsize_s = self.cnf["clock"]["s_arrowsize"]
        # flags
        self.rpihub=False
        self.goodtime=False
        # clock face 'theme' 
        self.themes={}
        for n in self.cnf["clock"]["faces"]:
            clock.backs[n] = Image.open( self.cnf["global"]["images"] + self.cnf["clock"]["faces"][n] ).resize( (128,128),Image.BICUBIC)
        # fonts     
        self.icons = self.cnf["clock"]["icons"]
        self.font = ImageFont.truetype( self.cnf["global"]["fonts"]+self.cnf["clock"]["font_bold"], self.cnf["clock"]["font_bold_size"] )
        self.font12 = ImageFont.truetype(self.cnf["global"]["fonts"]+self.cnf["clock"]["font_mono"], self.cnf["clock"]["font_mono_size"])
        self.symbols = ImageFont.truetype(self.cnf["global"]["fonts"]+self.cnf["clock"]["font_symbol"], self.cnf["clock"]["font_symbol_size"])
        self.symbols_large = ImageFont.truetype(self.cnf["global"]["fonts"]+self.cnf["clock"]["font_symbol"], self.cnf["clock"]["font_symbol_large_size"])
        # display init
        self.LCD = LCD_1in44.LCD()
        Lcd_ScanDir = LCD_1in44.SCAN_DIR_DFT  #SCAN_DIR_DFT = D2U_L2R
        self.LCD.LCD_Init(Lcd_ScanDir)
        self.LCD.LCD_Clear()
        # threads ******************************
        self.x_cpuload = threading.Thread( name='cpuload', target=self.runcpu, args=(), daemon=True)
        self.x_cpuload.start()
        # end threads **************************

    """ set ref to rpl 'rplink' object """
    def set_rpl(self,rpl):
        self.rpl=rpl        

    """ thread """
    def runcpu(self):
        while self.go:
            memlines = str(proc.check_output(['free']), encoding='utf-8').strip().split('\n')
            stats=json.loads(str(proc.check_output(['iostat','-o', 'JSON', '--dec=0', '1', '2']), encoding='utf-8') )
            cpu=stats['sysstat']['hosts'][0]["statistics"][1]["avg-cpu"]['idle']
            self.cpu = int(cpu)
            r = []
            for l in memlines[1].split(' '):
                if l == '': continue
                r.append(l)
            self.mem = (100.0 * int(r[2])) / int(r[1]);
            time.sleep(2)

    # **************************************
    # drow methods
    def drawcpu(self,draw):
        draw.rectangle([(127-3,127),(127,int(127*(self.cpu/100.0)))], fill=tuple(self.cnf["clock"]["cpu_color"]), outline=tuple(self.cnf["clock"]["cpu_color_outline"]), width=1)
        draw.rectangle([(0,127),(3,int(127*(1 - self.mem/100.0)))], fill=tuple(self.cnf["clock"]["mem_color"]), outline=tuple(self.cnf["clock"]["mem_color_outline"]), width=1)

    def drawtemp(self,draw):
        #with open('/sys/class/thermal/thermal_zone0/temp','r') as f:
        #    tempraw = f.read()
        if self.df['coretemp'] > self.temp_cpu_alarm:
            color=(255,0,0)
        else:
            color=tuple(self.cnf["clock"]["icons_color"])
        self.msg = u"{:2.0f}".format(self.df['coretemp']) + u'°'
        draw.text( ((128-self.font.getsize('40')[0])/2,82), self.msg, font=self.font, fill=color )

    def drawhostname(self,draw):
        draw.text( ((128-self.font12.getsize(self.df['hostname'])[0])/2,72), self.df['hostname'], font=self.font12, fill=tuple(self.cnf["clock"]["icons_color"]) )

    def drawnetwork(self,draw):
        symbol = chr(clock.icons["wifi_off"])+u''
        wififlag=False
        ethflag=False
        for dev in self.netdev:
            if( dev[0:4]=='wlan' and self.netdev[dev][1]!="--" ):
                symbol = chr(clock.icons["wifi"])+u''
                wififlag=True
                #break
            if( dev[0:3]=='eth' and self.netdev[dev][1]!="--" ):
                symbol = chr(clock.icons["eth"])+u''
                ethflag=True
                #break
        if wififlag and ethflag:
            symbol = chr(clock.icons["wifi_eth"])+u''
        draw.rectangle([(128-17,1),(128,18)], fill='#00000011', outline='#00000011', width=1)
        draw.text( (128-17,1), symbol, font=self.symbols, fill=tuple(self.cnf["clock"]["icons_color"]) )

    def drawbt(self,draw):        
        draw.rectangle([(1,1),(17,17)], fill='#00000011', outline='#00000011', width=1)
        if self.btscan_show:
            draw.text( (1,1), chr(clock.icons["bt"])+u'', font=self.symbols_large, fill=tuple(self.cnf["btscan"]["btscan_color"]) )
        else:            
            draw.text( (1,1), chr(clock.icons["bt"])+u'', font=self.symbols, fill=tuple(self.cnf["clock"]["icons_color"]) )

    def drawonline(self, draw):
        if self.isonline_flag:
            if self.isapactive:
                icon=clock.icons["ap"]
            else:
                icon=clock.icons["globe"]
            draw.text( (64-8,31), chr(icon)+u'', font=self.symbols, fill=tuple(self.cnf["clock"]["icons_color"]) )

    def drawhands( self, t, r, image ):
        x = int(image.size[0]/2)
        y = int(image.size[1]/2)
        im = Image.new( "RGBA", image.size, (255,255,255,0) )
        dr = ImageDraw.Draw( im )
        #dr.polygon( [(x-3,y), (x+3,y), (x+3,r[2]), (x+6,r[2]),(x,r[2]-self.arrowsize_h),(x-6,r[2]),(x-3,r[2])], fill=self.h_color, outline=(50,50,50) )
        dr.polygon( [(x-3,y), (x+3,y), (x+3,r[2]), (x+6,r[2]),(x,r[2]-self.arrowsize_h),(x-6,r[2]),(x-3,r[2])], fill=self.h_color, outline=self.outline_color )
        h = t[0] if t[0]<13 else t[0]-12
        him = im.rotate( -(h*30+t[1]*0.5), Image.BICUBIC )
        im = Image.new( "RGBA", image.size, (255,255,255,0) )
        dr = ImageDraw.Draw( im )
        #dr.polygon( [(x-2,y), (x+2,y), (x+2,r[1]),(x+5,r[1]),(x,r[1]-self.arrowsize_m),(x-5,r[1]), (x-2,r[1])], fill = self.h_color, outline=(50,50,50) )
        dr.polygon( [(x-2,y), (x+2,y), (x+2,r[1]),(x+5,r[1]),(x,r[1]-self.arrowsize_m),(x-5,r[1]), (x-2,r[1])], fill = self.h_color, outline=self.outline_color )
        hmim =Image.alpha_composite( him, im.rotate( -(360*t[1])/60, Image.BICUBIC ) )
        im = Image.new( "RGBA", image.size, (255,255,255,0) )
        dr = ImageDraw.Draw( im )
        dr.line([ ( x, y+20 ), ( x, r[0]+self.arrowsize_h)], fill = self.s_color, width = 2 )
        dr.line([ ( x-3, r[0]+self.arrowsize_s ), ( x, r[0]), ( x+3, r[0]+self.arrowsize_s ), ( x-3, r[0]+self.arrowsize_s )], fill = self.s_color, width = 2 )
        dr.ellipse([x-7,y-7,x+7,y+7],fill=self.s_color,outline='#777')
        return Image.alpha_composite( hmim, im.rotate( -(360*t[2])/60, Image.BICUBIC ) )

    def drowclockface(self):        
        image = clock.backs[self.cnf["global"]["theme"]].copy()
        self.clock_image = image
        im = Image.new( "RGBA", image.size, (0,0,0,255) )
        im.paste(image)
        draw = ImageDraw.Draw(im)
        
        self.drawbt(draw)
        self.drawnetwork(draw)
        self.drawcpu(draw)       
        self.drawtemp(draw)
        self.drawhostname(draw)
        self.drawonline(draw)

        tm = time.localtime()
        #print("time:",tm[3],tm[4],tm[5],"\n")
        im = Image.alpha_composite( im, self.drawhands( (tm[3],tm[4],tm[5]), (12, 22, 35), image ) )
        
        return im

    """ thread """
    def runclock(self):
        if self.go:
            self.sheduler.enter(1,1,self.runclock)
        #self.netdev = rph.getnetdev()
        im = self.drowclockface()
        """ showinfo buttons action """
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

    """ btscan key/menu handle """
    def btscan_flag(self):
        if self.btscan:
            self.btscan = False
        else:
            self.btscan = True
            with open('btdev.txt', 'w') as f:
                f.write( "" )
            self.btscan_run()
        self.menu.active=False    

    """ thread sheduler for 'btscan_exec' """
    def btscan_run(self):
        if self.btscan:
            self.sheduler.enter( self.cnf["btscan"]["btscan_period"],100,self.btscan_run )
        self.bt_th = threading.Thread( name='btscan_exec', target=self.btscan_exec, args=(), daemon=True)
        self.bt_th.start()

    """ thread """
    def btscan_exec(self):
        #output=str(proc.check_output(['./btscan.sh'] ), encoding='utf-8').strip().splitlines()
        self.btscan_show=True
        output=str(proc.check_output(['sudo', 'hcitool', 'scan', '--length={}'.format( (self.cnf["btscan"]["btscan_time"] ) ) ] ), encoding='utf-8').strip().splitlines()
        self.btscan_show=False
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

    def setnextclockfacecolor(self,color=None):
        if color in self.cnf["clock"]["faces"]:
            self.cnf["global"]["theme"]=color
        else:    
            colors=list(self.backs.keys())
            try:
                next=colors[ colors.index(self.cnf["global"]["theme"]) + 1  ]
            except (ValueError, IndexError):
                next=colors[0]
            self.cnf["global"]["theme"]=next    
        clock.cnf.save()
        

    """  buttons on right - callbaks """
    def sinfo2( self=None, pin=None ):
        """ KEY1 """
        if self.showinfo==True:
            self.showinfo = False
        else:
            buf=str(proc.check_output(['df','-h'] ), encoding='utf-8').strip().splitlines()[1].strip().split()
            self.info = u'SN: ' + self.df['serial'] + u'\nChip: ' + self.df['chip'] + u'\nArch: ' + self.df['machine'] + u'\nRaspberry Pi OS'+ u'\n' + self.df['version'] + u'\nCore: ' + self.df['release'] + u'\nPTUUID: ' + self.df['puuid'] + '\nFS: ' + buf[1] + ', ' + buf[3] + ' free' + u'\nRAM: {:4.2f} GB'.format(float(self.df['memtotal']))
            self.showinfo = True

    def sinfo(self, pin ):
        """ KEY2 """
        if self.showinfo==True:
            self.showinfo = False
        else:
            self.info = u'host: ' + self.df['hostname']
            if self.isapactive:
                self.info = self.info + u'\nWL: {}\nPS: {}'.format(self.rpl.AP['ssid'], self.rpl.AP['wpa_passphrase'])
            for dev in self.netdev:
                self.info = self.info + u"\n{}:\n{}\n{}".format( dev, self.netdev[dev][1], self.netdev[dev][2] )
            self.showinfo = True
            #print(self.info)

    def nextbk( self, pin ):
        """ KEY3 """
        self.setnextclockfacecolor()    
        

    def getselfinfo(self):
        print("Info 2")
        return "info"

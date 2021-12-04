import time, math,sys,sched
import subprocess as proc
import threading, requests, json, base64

from PIL.ImageDraw import Draw
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
        self.isonline_flag = False
        self.btscan = False
        self.btscan_show = False
        self.showinfo = False
        self.rpilink_period = 3
        self.isonline_period = 1
        self.rpilink_address = 'rpi.ontime24.pl'
        self.temp_cpu_alarm = 50
        self.btdev = {}
        self.kbd = kbd
        self.hostinfo = hlp.hostinfo()
        self.mmcinfo = hlp.getmmcinfo()
        self.s_color = tuple(self.cnf["clock"]["s_color"])
        self.m_color = tuple(self.cnf["clock"]["m_color"])
        self.h_color = tuple(self.cnf["clock"]["h_color"])
        self.outline_color = tuple(self.cnf["clock"]["outline_color"])
        self.arrowsize_h = self.cnf["clock"]["h_arrowsize"]
        self.arrowsize_m = self.cnf["clock"]["m_arrowsize"]
        self.arrowsize_s = self.cnf["clock"]["s_arrowsize"]
        self.menu = Menu.Menu( (128,128), [(3,63-12),(125,63+15)], self )
        self.serial=''
        self.rpihub=False
        self.goodtime=False
        self.getdevinfo()
        self.themes={}
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
        self.x_isonline = threading.Thread( name='isonline', target=self.isonline, args=(), daemon=True)
        self.x_isonline.start()
        self.x_rplink = threading.Thread( name='rplink', target=self.rpilink, args=(), daemon=True)
        self.x_rplink.start()

    """ thread """
    def rpilink(self):
        while self.go:
            time.sleep(self.rpilink_period)    
            if self.isonline:
                if "eth0" in self.netdev.keys():
                    ip=self.netdev['eth0'][1]
                    emac=self.netdev['eth0'][2]
                else:
                    ip='--'
                    emac='--'
                if "wlan0" in self.netdev.keys():
                    wip=self.netdev['wlan0'][1]
                    wmac=self.netdev['wlan0'][2]
                else:
                    wip='--'
                    wmac='--'
                df = self.getdevinfo()
                df['ip']=ip
                df['wip']=wip
                df['emac']=emac
                df['wmac']=wmac
                df['theme']=self.cnf["global"]["theme"]
                x = requests.post( 'http://'+self.rpilink_address+'/?get=post', json=df, timeout=1)
                if x.status_code==200:
                    self.rpihub=True
                    # TODO: read respoce
                    r=json.loads(base64.standard_b64decode(x.text))
                    #print( base64.standard_b64decode(x.text) )
                    if r['status']=='OK':
                        if not self.goodtime:
                            curent_date_time=str(r['time']).split()
                            #proc.run(['/bin/timedatectl', 'set-ntp', 'false' ])
                            #print("STOP",curent_date_time[0]," ",curent_date_time[1],"\n");
                            #proc.run(['/bin/timedatectl', 'set-time', curent_date_time[0] ])
                            #print("date: "+curent_date_time[0]+"\n")
                            cp=proc.run(['/bin/timedatectl', 'set-time', curent_date_time[1] ])
                            print("time: "+curent_date_time[1]+"\n")
                            if cp.returncode==0:
                                self.goodtime=True
                        # theme
                        if r['cmd']['name']=='theme':
                            self.cnf["global"]["theme"]=r['cmd']['value']
                            clock.cnf.save()
                        # hostname    
                        if r['cmd']['name']=='hostname' and r['cmd']['sn']==self.serial:
                            new_hostname=r['cmd']['value']
                            if r['cmd']['sn']==self.serial:
                                proc.check_output(['/root/lcd144/setnewhostname.sh', new_hostname, self.hostname ] )
                                self.hostname=str(proc.check_output(['hostname'] ), encoding='utf-8').strip()
                        # reboot
                        if r['cmd']['name']=='reboot' and r['cmd']['sn']==self.serial:
                            result = proc.run(['/bin/systemctl', 'reboot'],capture_output=True, text=True);
                        # poweroff
                        if r['cmd']['name']=='poweroff' and r['cmd']['sn']==self.serial:
                            result = proc.run(['/bin/systemctl', 'poweroff'],capture_output=True, text=True);
                        # update agent software (LCD144)
                        if r['cmd']['name']=='update' and r['cmd']['sn']==self.serial:
                            result = proc.run(['/bin/git pull'], cwd='/root/'+r['cmd']['service'], shell=True, capture_output=True, text=True);
                            #print("stdout: ", result.stdout)
                            #print("stderr: ", result.stderr)
                                
                    else:
                        print( 'ERROR:' + r['status'] )    
                else:
                    self.rpihub=False
    #end of rpilink()

    """ thread """
    def isonline(self):
        while self.go:
            time.sleep(self.isonline_period)    
            try:
                r = str(proc.check_output(['/bin/ping', '-4', '-c', '3', '-i', '0', '-f', '-q', self.rpilink_address] ), encoding='utf-8').strip()
            except proc.CalledProcessError:
                r = '0 received'
            ind = int(r.find(' received'))
            if( int(r[ind-1:ind]) > 0 ):
                self.isonline_flag = True
            else:
                self.isonline_flag = False
    #end of isonline()            

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

    def getdevinfo(self):
        df = {}
        if len(self.serial) < 1:
            with open('/proc/cpuinfo','r') as f:
                output=str(f.read()).strip().splitlines()
            for line in output:
                l=str(line).strip().split()
                if len(l)>0 and l[0]=='Serial':
                    self.serial=l[2][8:]
                if len(l)>0 and l[0]=='Hardware':
                    self.chip=l[2]
                if len(l)>0 and l[0]=='Revision':
                    self.revision=l[2]
                if len(l)>0 and l[0]=='Model':
                    self.model=u' '.join(l[2:])
            with open('/proc/meminfo','r') as f:
                output=str(f.readline()).strip().split()
            self.memtotal= ( float(output[1]) / 1000000.0 )    
            self.release=str(proc.check_output(['uname','-r'] ), encoding='utf-8').strip()
            self.machine=str(proc.check_output(['uname','-m'] ), encoding='utf-8').strip()
            buf=str(proc.check_output(['blkid','/dev/mmcblk0'] ), encoding='utf-8').strip().split()[1]
            self.puuid=buf[8:16]
            self.version='???'
            with open('/etc/os-release','r') as f:
                output=f.readlines()
            for line in output:
                l=line.split('=')
                if l[0]!='VERSION':
                    continue
                else:
                    self.version=str(l[1]).strip() 
                    break   
        self.hostname=str(proc.check_output(['hostname'] ), encoding='utf-8').strip()

        df['serial']=self.serial
        df['chip']=self.chip
        df['revision']=self.revision
        df['model']=self.model
        df['memtotal']=self.memtotal
        df['release']=self.release
        df['machine']=self.machine
        df['hostname']=self.hostname
        df['puuid']=self.puuid
        df['version']=self.version
        return df

    def getnetdev(self):
        netdev={}
        with open('/proc/net/dev','r') as f:
            dev = f.read()
            for devname in ['eth0', 'eth1', 'wlan0', 'wlan1']:
                if dev.find(devname) > -1:
                    buf = str(proc.check_output([ 'ip', '-4', 'address', 'show', 'dev', devname ]), encoding='utf-8')
                    if len(buf)>1: 
                        ip=buf.strip().splitlines()[1].split()[1]
                    else:
                        ip='--'
                    mac=str(proc.check_output([ 'ip', 'link', 'show', 'dev', devname ]), encoding='utf-8').strip().splitlines()[1].split()[1]
                    netdev[devname]=(devname,ip,mac)
        return netdev            

    def drawcpu(self,draw):
        draw.rectangle([(127-3,127),(127,int(127*(self.cpu/100.0)))], fill=tuple(self.cnf["clock"]["cpu_color"]), outline=tuple(self.cnf["clock"]["cpu_color_outline"]), width=1)
        draw.rectangle([(0,127),(3,int(127*(1 - self.mem/100.0)))], fill=tuple(self.cnf["clock"]["mem_color"]), outline=tuple(self.cnf["clock"]["mem_color_outline"]), width=1)

    def drawtemp(self,draw):
        with open('/sys/class/thermal/thermal_zone0/temp','r') as f:
            tempraw = f.read()
        if (int)(tempraw[0:2])>self.temp_cpu_alarm:
            color=(255,0,0)
        else:
            color=tuple(self.cnf["clock"]["icons_color"])
        self.msg = u"{}".format(tempraw[0:2]) + u'°'
        draw.text( ((128-self.font.getsize('40')[0])/2,82), self.msg, font=self.font, fill=color )

    def drawhostname(self,draw):
        draw.text( ((128-self.font12.getsize(self.hostname)[0])/2,72), self.hostname, font=self.font12, fill=tuple(self.cnf["clock"]["icons_color"]) )

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
            if self.rpihub:
                globe_color=self.cnf["clock"]["mem_color"]
            else:
                globe_color=self.cnf["clock"]["icons_color"]
            draw.text( (64-8,31), chr(clock.icons["globe"])+u'', font=self.symbols, fill=tuple(globe_color) )

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
        
        self.drawnetwork(draw)
        self.drawbt(draw)
        self.drawcpu(draw)       
        self.drawtemp(draw)
        self.drawhostname(draw)
        self.drawonline(draw)

        tm = time.localtime()
        print("time:",tm[3],tm[4],tm[5],"\n")
        im = Image.alpha_composite( im, self.drawhands( (tm[3],tm[4],tm[5]), (12, 22, 35), image ) )
        return im

    def runclock(self):
        if self.go:
            #print("runclock: \n")
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


    """  buttons on right callbaks """
    def sinfo2( self=None, pin=None ):
        """ KEY1 """
        if self.showinfo==True:
            self.showinfo = False
        else:
            buf=str(proc.check_output(['df','-h'] ), encoding='utf-8').strip().splitlines()[1].strip().split()
            self.info = u'SN: ' + self.serial + u'\nChip: ' + self.chip + u'\nArch: ' + self.machine + ' ' + self.hostinfo['processor'] + '-CPU' u'\nRaspberry Pi OS'+ u'\n' + self.version + u'\nCore: ' + self.release + u'\nPTUUID: ' + self.puuid + '\nFS: ' + buf[1] + ', ' + buf[3] + ' free' + u'\nRAM: {:4.2f} GB'.format(float(self.memtotal))
            self.showinfo = True
        #print("EXIT!")
        #self.go = False

    def sinfo(self, pin ):
        """ KEY2 """
        if self.showinfo==True:
            self.showinfo = False
        else:
            self.info = u'host: ' + self.hostname
            for dev in self.netdev:
                self.info = self.info + u"\n{}:\n{}\n{}".format( dev, self.netdev[dev][1], self.netdev[dev][2] )
            self.showinfo = True
            #print(self.info)

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

    def getselfinfo(self):
        print("Info 2")
        return "info"

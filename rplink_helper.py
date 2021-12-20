#!/usr/bin/python
# -*- coding:utf-8 -*-

import time, sched, threading
from datetime import datetime
from PIL import Image,ImageDraw,ImageFont
import subprocess as proc
import SH1106
import config
import helper as h
from Kbd import Kbd
from rplink import rplink

class oled13:
    def __init__(self, rpilink_address='rpi.ontime24.pl'):
        # run flag
        self.go=True
        # sheduler
        self.s = sched.scheduler(time.time, time.sleep)
        # OLED 1.3' display driver
        self.disp = SH1106.SH1106()
        # Keyboard driver
        self.kbd=Kbd(self)
        # rpilink object
        self.rpilink=rplink(display='oled13', rpilink_address='rpi.ontime24.pl', rpilink_period=2)
        self.rpilink.setlocaldata( {'theme':'mono'} )
        # display state
        self.display_state=''
        self.display_timeout=10
        self.display_timeout_d=10
        # semafor for save 'image' modifications
        self.lock = threading.Lock()
        # network params
        self.rpilink_address = rpilink_address
        self.isonline_flag = False
        # dev info
        self.df=h.getrpiinfo()
        self.netdev=h.getnetdev()
        self.rpilink.setlocaldata( {'netdev':self.netdev, 'msdid':self.df['msdid'], 'essid':self.df['essid'], 'coretemp':self.df['coretemp'], 'memavaiable':self.df['memavaiable']} )
        # Initialize and clean the display.
        self.disp.Init()
        self.disp.clear()
        # Graphix items
        self.withe = 0
        self.black = 1
        self.image = None #Image.new('1', (self.disp.width, self.disp.height), "WHITE")
        self.font = ImageFont.truetype('fonts/cour.ttf', 26)
        self.font10 = ImageFont.truetype('fonts/cour.ttf',11)
        self.icon = ImageFont.truetype('fonts/segmdl2.ttf', 12)
        # drowinfo objects
        self.drowinfo=drowinfo(self,self.font10)
        # Set keyboard handler callback
        self.kbd.sethanddle( 'k1', self.k1_handle )
        self.kbd.sethanddle( 'k2', self.k2_handle )
        self.kbd.sethanddle( 'k3', self.k3_handle )
        self.kbd.sethanddle( 'enter', self.enter_handle )
        self.kbd.sethanddle( 'right', self.right_handle )
        self.kbd.sethanddle( 'left', self.left_handle )
        self.kbd.sethanddle( 'up', self.up_handle )
        self.kbd.sethanddle( 'down', self.down_handle )
        

    def drowicon( self,icon=0xEC44,x=1,y=1,show=False ):
        self.lock.acquire()
        draw = ImageDraw.Draw(self.image)
        draw.text( (x,y), chr(icon), font=self.icon, fill=self.withe)     
        if show:
            self.disp.ShowImage(self.disp.getbuffer(self.image))
        self.lock.release()
            
    def clock( self ):
        #print( "oled13.clock():\n")
        image = Image.new('1', (self.disp.width, self.disp.height), "WHITE")
        draw = ImageDraw.Draw(image)
        now = datetime.now() # current date and time
        buf = now.strftime("%H:%M:%S")
        (sx,sy)=self.font.getsize(buf)
        draw.text( ( int((128-sx)/2), 15 ), buf, font = self.font, fill = 0)
        self.ip=h.getip()
        (sx,sy)=self.font10.getsize(self.ip)
        draw.text((int((128-sx)/2),64-sy), self.ip, font = self.font10, fill = 0)
        draw.text((0,0), u'{:2.0f}\'C'.format(h.gettemp()), font = self.font10, fill = 0)
        #image=image.rotate(180) 
        self.lock.acquire()
        self.image = image
        self.lock.release()

    def status( self, content=" - Status -", drowinfo=None ):
        """ 
            status( self, content=" ", drowinfo=None, mode=True )
            content = list od str or multiline text to display
            drowinfo = instance of 'drowinfo' class
        """
        if self.display_timeout==self.display_timeout_d:
            self.kbd.sethanddle( 'up', drowinfo.key_up_handler )
            self.kbd.sethanddle( 'down', drowinfo.key_down_handler )
        if self.display_timeout==0:
            self.kbd.sethanddle( 'up', self.up_handle )
            self.kbd.sethanddle( 'down', self.down_handle )
        image=drowinfo.drow(content)
        self.lock.acquire()
        self.image = image
        self.lock.release()
              
        
    def show(self):
        #print( "oled13.show():\n")
        self.lock.acquire()
        self.disp.ShowImage(self.disp.getbuffer(self.image))    
        self.lock.release()

        
    def run(self):
        #print( "oled13.run():\n")
        self.s.run()
        
    def loop(self):
        if self.go:    
            #print( "oled13.loop():\n")
            self.s.enter(1, 1, self.loop ) 
            if self.display_state in ['status1', 'status2', 'status3']:
                if self.display_state=='status1':
                    content=h.getrpiinfo(False)
                if self.display_state=='status2':
                    content="K2 Status"
                if self.display_state=='status3':
                    content="K3 Status"
                self.status(drowinfo=self.drowinfo, content=content )    
                if self.display_timeout > 0:
                    self.display_timeout=self.display_timeout-1
                else:
                    self.display_state=''
                    self.display_timeout=self.display_timeout_d
            # clock() is the default    
            if self.display_state=='':         
                self.clock()
                # add online status info
                if h.online_status():
                    self.drowicon(icon=0xEC3F,x=128-12,y=0)
            self.show()
        else:  # self.go==False
            self.disp.clear()
            self.disp.reset()
            self.disp.command(0xAE);  #--turn off oled panel

# Keyboard callbacks handlers
        
    def k1_handle(self,name,state):
        if state=='Down':
            if self.display_state!='status1':
                self.display_state='status1'
            else:    
                self.display_state=''
                self.kbd.sethanddle( 'up', self.kbd.keyhandle )
                self.kbd.sethanddle( 'down', self.kbd.keyhandle )
            self.display_timeout=self.display_timeout_d
        #print( u'k1_handle: {} is {}'.format( name, state ) )

    def k2_handle(self,name,state):
        if state=='Down':
            if self.display_state!='status2':
                self.display_state='status2'
            else:    
                self.display_state=''
                self.kbd.sethanddle( 'up', self.kbd.keyhandle )
                self.kbd.sethanddle( 'down', self.kbd.keyhandle )
            self.display_timeout=self.display_timeout_d
        #print( u'k2_handle: {} is {}'.format( name, state ) )
        
    def k3_handle(self,name,state):
        if state=='Down':
            if self.display_state!='status3':
                self.display_state='status3'
            else:    
                self.display_state=''
                self.kbd.sethanddle( 'up', self.kbd.keyhandle )
                self.kbd.sethanddle( 'down', self.kbd.keyhandle )
            self.display_timeout=self.display_timeout_d
        #print( u'k3_handle: {} is {}'.format( name, state ) )

    def enter_handle(self,name,state):
        if state=='Down':
            self.go=False
        print( u'enter_handle: {} is {}'.format( name, state ) )
        print( u'exit!' )

    def right_handle(self,name,state):
        if state=='Down':
            print( u'rght_handle: {} is {}'.format( name, state ) )    

    def left_handle(self,name,state):
        if state=='Down':
            print( u'left_handle: {} is {}'.format( name, state ) )    

    def up_handle(self,name,state):
        if state=='Down':
            print( u'up_handle: {} is {}'.format( name, state ) )    

    def down_handle(self,name,state):
        if state=='Down':
            print( u'down_handle: {} is {}'.format( name, state ) )    
        

class drowinfo:
    def __init__(self, oled, font=None ):
        """ clock is reference to 'clock' instance """
        self.oled=oled
        if font!=None:
            self.font=font
        else:
            self.font=ImageFont.truetype('fonts/cour.ttf',11)
        self.info= []
        self.start= 0
        (sx,sy)= self.font.getsize('X')
        self.vspace=1
        self.maxly= self.oled.disp.height // int(sy+self.vspace)
        self.maxlx= self.oled.disp.width // int(sx)
        self.maxlines= 50    
        

    def setinfo(self,content):
        self.info=[]
        if isinstance(content, list):
            for line in content:
                line=str(line)
                while len(line)>0:
                    if len(line)<=self.maxlx:
                        self.info.append(line)
                        break
                    else:
                        self.info.append(line[0:self.maxlx])
                        line=line[self.maxlx:]
        else:
            for line in content.splitlines():
                while len(line)>0:
                    if len(line)<=self.maxlx:
                        self.info.append(line)
                        break
                    else:
                        self.info.append(line[0:self.maxlx])
                        line=line[self.maxlx:]    
        
    def drow(self,content=None):
        """ drowinfo class - display multilnies 'content' in OLED screen """
        if content!=None:
            self.setinfo(content)
        image = Image.new('1', (self.oled.disp.width, self.oled.disp.height), "WHITE")
        draw = ImageDraw.Draw(image)
        info=""
        for i in range( self.maxly ):
            if (self.start+i) < len(self.info):
                info=info+self.info[self.start+i]+"\n"
        draw.multiline_text( (1,1), info, font=self.font, spacing=self.vspace, fill = 0 )
        return image
    
    def key_up_handler(self,name,state):
        if state=='Down':
            if self.start>0:
                self.start=self.start-1
        self.oled.display_timeout=self.oled.display_timeout_d
        image=self.drow()
        self.oled.lock.acquire()
        self.oled.image = image
        self.oled.lock.release()
#        self.oled.show()
        
        
    def key_down_handler(self,name,state):
        if state=='Down':
            if self.start < (len(self.info)-self.maxly):
                self.start=self.start+1
        self.oled.display_timeout=self.oled.display_timeout_d
        image=self.drow()
        self.oled.lock.acquire()
        self.oled.image = image
        self.oled.lock.release()
 #       self.oled.show()
        
        


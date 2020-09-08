import time, math,sys,sched
import subprocess as proc
import threading
from PIL import Image,ImageDraw,ImageFont,ImageColor,ImageFilter

class Menu:

    def __init__(self,size,box,parent):
        """  joystic menu  """
        self.cnf = parent.cnf
        self.parent = parent
        self.active = False
        self.state = []
        self.size = size
        self.box = box
        self.selected = 0
        self.fill = tuple(self.cnf["menu"]["fill_color"])
        self.outline = tuple(self.cnf["menu"]["outline_color"])
        self.fontcolor = tuple(self.cnf["menu"]["font_color"])
        self.font = ImageFont.truetype( self.cnf["global"]["fonts"]+self.cnf["menu"]["font"], self.cnf["menu"]["font_size"] )

    def add(self,label,action):
        self.state.append({'label':label, 'action':action })

    def show(self):
        if self.active:
            im = Image.new('RGBA',(128,128),tuple(self.cnf["menu"]["bg_color"]))
            dr = ImageDraw.Draw(im)

            dr.rectangle( self.box,fill=self.fill, outline=self.outline)
            if len(self.state)>0:
                txtsize = dr.textsize( self.state[self.selected]['label'], font=self.font )
                dr.text( ((self.size[0]-txtsize[0])/2, (self.size[1]-txtsize[1])/2), self.state[self.selected]['label'], fill=self.fontcolor, font=self.font )
            else:
                txtsize = dr.textsize( '- no items -', font=self.font )
                dr.text( ((self.size[0]-txtsize[0])/2, (self.size[1]-txtsize[1])/2), '- no items -', fill=self.fontcolor, font=self.font )
            return im
        else:
            return False

    def run(self,name):
        if self.active:
            self.state[self.selected]['action']( label=self.state[self.selected]['label'], menu=self )

    def next(self,name):
        if self.active:
            if self.selected < len(self.state)-1:
                self.selected += 1
            else:
                self.selected = 0

    def previous(self,name):
        if self.active:
            if self.selected > 0:
                self.selected -= 1
            else:
                self.selected = len(self.state)-1

    def start(self,name):
        if not self.active:
            #print( "start" )
            self.active = True
        else:
            #print( "stop" )
            self.active = False


    def stop(self,name):
        print( "stop" )
        if self.active:
            self.active = False


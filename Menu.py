import time, math, sys, sched, csv
import subprocess as proc
import helper as h
import threading
from functools import partial
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
        self.fontdark = tuple(self.cnf["menu"]["fontdark_color"])
        self.font = ImageFont.truetype( self.cnf["global"]["fonts"]+self.cnf["menu"]["font"], self.cnf["menu"]["font_size"] )

    def myexec( self, label='', menu=False, arg=False ):
        if arg==False:
            return
        result = proc.run([arg],shell=True,capture_output=True,encoding='utf-8');        
        #r = str(proc.check_output( a ), encoding='utf-8').strip()
        #print( label, r, '\n' )
        menu.active = False
        #return r

    def py_call( self, toexec=None, label="label", menu=None ):
        exec( toexec )

    def add(self,label,action):
        self.state.append({'label':label, 'action':action })

    def load(self, filename):
        menucontent = []
        with open(filename) as csvfile:
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
            if len(menucontent)==0:  
                return False
            for item in menucontent:
                if item[1] == 'f':
                    self.add(item[0], partial( self.myexec, arg=item[2] ) )
                    #print( 'menu: ', item[2] )
                if item[1] == 'p':
                    self.add(item[0], partial( self.py_call, toexec=item[2] ) )
            return True

    def show(self):
        if self.active:
            im = Image.new('RGBA',(128,128),tuple(self.cnf["menu"]["bg_color"]))
            dr = ImageDraw.Draw(im)

            dr.rectangle( self.box,fill=self.fill, outline=self.outline)
            if len(self.state)>0:
                nextitem = (self.selected+1) % len(self.state )
                previousitem = self.selected-1
                if previousitem < 0:
                    previousitem = len(self.state )-1
                txtsize = dr.textsize( self.state[self.selected]['label'], font=self.font )
                txtsizep = dr.textsize( self.state[previousitem]['label'], font=self.font )
                txtsizen = dr.textsize( self.state[nextitem]['label'], font=self.font )
                dr.text( ((self.size[0]-txtsizep[0])/2, (self.size[1]-txtsize[1])/2-25), self.state[previousitem]['label'], fill=self.fontdark, font=self.font )
                dr.text( ((self.size[0]-txtsizen[0])/2, (self.size[1]-txtsize[1])/2+25), self.state[nextitem]['label'], fill=self.fontdark, font=self.font )
                dr.text( ((self.size[0]-txtsize[0])/2, (self.size[1]-txtsize[1])/2), self.state[self.selected]['label'], fill=self.fontcolor, font=self.font )
                #print( previousitem, nextitem, self.state[previousitem]['label'], self.state[nextitem]['label'] )
            else:
                txtsize = dr.textsize( '- no items -', font=self.font )
                dr.text( ((self.size[0]-txtsize[0])/2, (self.size[1]-txtsize[1])/2), '- no items -', fill=self.fontcolor, font=self.font )
            return im
        else:
            return False
    
    """ run key handler (activete/exec the menu action command)"""
    def run(self,name):
        if self.active:
            self.state[self.selected]['action']( label=self.state[self.selected]['label'], menu=self )

    """ next item key handler """
    def next(self,name):
        if self.active:
            if self.selected < len(self.state)-1:
                self.selected += 1
            else:
                self.selected = 0

    """ previous item key handler """
    def previous(self,name):
        if self.active:
            if self.selected > 0:
                self.selected -= 1
            else:
                self.selected = len(self.state)-1

    """ start/stop (activete or deactivate menu visibility) item key handler """
    def start(self,name):
        if not self.active:
            #print( "start" )
            self.active = True
        else:
            #print( "stop" )
            self.active = False


    """ stop (switcg off and deactivate menu visibility) item key handler """
    def stop(self,name):
        #print( "stop" )
        if self.active:
            self.active = False


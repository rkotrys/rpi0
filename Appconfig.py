#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys,os,time,json
import datetime as dt
import configparser as cnfp


class Appconfig:
    """ read, save and modyfy configyration files  """
    def __init__(self,filename):
        self.initconf = os.path.abspath(filename)
        self.curentconf=os.path.dirname( self.initconf ) + "/run_" + os.path.basename( filename )
        if os.path.isfile( self.curentconf ):
            if os.path.getctime( self.curentconf )>os.path.getctime( self.initconf ):
                self.filename = self.curentconf
            else:
                self.filename = self.initconf
        else:
            self.filename = self.initconf
        if not os.path.isfile( self.filename ):
            print("ERROR: No ini file '{}'\n".format(self.filename))
            quit()

        self.conf = cnfp.ConfigParser()
        self.conf.read(self.filename)
        self.dml = {}
        for s in self.conf.sections():
            self.dml[s] = {}
            _sec=self.conf[s]
            for k in _sec:
                if _sec[k][:5]=="json:":
                    buf=_sec[k][5:]
                    self.dml[s][k]=json.loads(buf)
                else:
                    self.dml[s][k]=_sec[k]
        self.save()

    def save(self,init=False):
        now = dt.datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
        conf = cnfp.ConfigParser()
        for section in self.dml:
            conf[section]={}
            for key in self.dml[section]:
                if type(self.dml[section][key]).__name__ == "str":
                    conf[section][key]=self.dml[section][key]
                else:
                    conf[section][key]="json:"+json.dumps(self.dml[section][key])
        if init:
            filename = self.initconf
        else:
            filename = self.curentconf
        with open(filename, 'w') as configfile:
            configfile.write(     "#-------------------------------------------------------\n" )
            if filename==self.curentconf:
                configfile.write( "# Do not modyfy! This file is overwriten on exit!\n" )
                configfile.write( "# Edit the file: {}\n".format(self.initconf) )
                configfile.write(     "#-------------------------------------------------------\n" )
            configfile.write( "# \n" )
            configfile.write( "# Init Conf: {}\n# Curent Conf: {}\n# Last update: {}\n".format(self.initconf,self.curentconf,dt_string) )
            configfile.write(     "#\n#-------------------------------------------------------\n#\n" )
            conf.write(configfile)


    def reload():
        self.conf = cnfp.ConfigParser()
        self.conf.read(self.filename)
        self.dml = {}
        for s in self.conf.sections():
            self.dml[s] = {}
            _sec=self.conf[s]
            for k in _sec:
                if _sec[k][:5]=="json:":
                    buf=_sec[k][5:]
                    self.dml[s][k]=json.loads(buf)
                else:
                    self.dml[s][k]=_sec[k]


#----------------------------------
#  TEST
#----------------------------------
#c = Appconfig("test.ini")
#c.set('global','ind',10)
#c.dml["global"]["ind"]=5
#print(c.dml['global'])
#c.save()
#quit()
#
#----------------------------------

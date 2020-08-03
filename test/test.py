#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, io, subprocess
from pathlib import Path

def readfile(filename):
    if os.path.isfile(filename):
        with open(filename,'r') as file:
            data = file.readline().strip().replace('\n','')
    else:
        data=False

    return data

def system_exec(command):
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8').strip().split('\n')

class Wifiscan:
    def __init__(self,dev="wlan0"):
        self.dev = dev
        self.res = system_exec("sudo iwlist {} scanning".format(dev))
        self.data = self.scan()

    def scan(self):
        self.data = {}
        f=list()
        for line in self.res:
            l = line.strip().replace('\n','')
            if len(l)>0:
                f.append( l )
        for l in f:
            n = f.index(l)
            if l.find("Cell")>-1:
                ofset=1
                net={}
                part = l.split(" ")
                net["mac"] = part[4]
                #data[part[1]] = net
                while (n+ofset) < len(f)-1 and f[n+ofset].find("Cell")==-1 :
                    if f[n+ofset].find("Channel")>-1:
                        part = f[n+ofset].split(":")
                        net["channel"]=part[1]
                        ofset=ofset+1
                    elif f[n+ofset].find("Frequency")>-1:
                        part = f[n+ofset].split(" ")
                        part = part[0].split(":")
                        net["frequency"]=part[1]
                        ofset=ofset+1
                    elif f[n+ofset].find("Encryption")>-1:
                        part = f[n+ofset].split(":")
                        net["encryption"]=part[1]
                        ofset=ofset+1
                    elif f[n+ofset].find("ESSID")>-1:
                        part = f[n+ofset].split(":")
                        net["essid"]=part[1].strip('"')
                        ofset=ofset+1
                    elif f[n+ofset].find("Mode")>-1:
                        part = f[n+ofset].split(":")
                        net["mode"]=part[1]
                        ofset=ofset+1
                    elif f[n+ofset].find("Quality")>-1:
                        part = f[n+ofset].split(" ")
                        part2 = part[0].split("=")
                        net["quality"]=part2[1]
                        part2 = part[3].split("=")
                        net["lavel"]=part2[1]
                        ofset=ofset+1
                    else:
                        ofset=ofset+1
                self.data[net["essid"]]=net
        return self.data

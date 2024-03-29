#!/usr/bin/python
# -*- coding:utf-8 -*-

# /*****************************************************************************
# * | File        :	  rplink.py
# * | Author      :   Robert Kotrys
# * | Function    :   Basic class to use with Raspberry Pi link service
# * | Info        :   require files: helper.py
# *----------------
# * | This version:   V1.0.2
# * | Date        :   2022-03-23
# * | Info        :   include 'rplink' run file and 'rplink.service'
# ******************************************************************************/


import sys, time, sched, threading, requests, json, base64, logging, logging.handlers,signal,subprocess
from logging.handlers import SysLogHandler
from logging import Formatter
from datetime import datetime
import subprocess as proc
import helper as h

class rplink:
    """ class 'rplink' xchange information and command with 'rpihub' server """
    def __init__(self, display, rpilink_address='rpi.ontime24.pl',rpilink_period=1, localdata={}):
        """ constructor """
        self.version='1.0.1'
        self.display=display
        self.clk=None
        self.rpilink_address=rpilink_address
        self.rplink_period=rpilink_period
        self.d=h.getrpiinfo()
        self.n=h.getnetdev()
        self.AP=h.getapparam()
        self.bthosts={}
        self.bthostsflag=False
        self.go=True
        self.isonline=False
        self.rpihub=False
        self.goodtime=False
        self.scan={}
        self.logger = logging.getLogger(self.display)
        self.logger.setLevel( logging.DEBUG )
        self.log_handler = SysLogHandler(facility=SysLogHandler.LOG_DAEMON, address='/dev/log')
        self.log_handler.setFormatter(Formatter(fmt='[%(levelname)s] %(filename)s:%(funcName)s:%(lineno)d \"%(message)s\"'))
        self.logger.addHandler( self.log_handler )
        self.logger.info('[{}] rpilink logger is start!'.format(self.display))
        self.localdata=localdata
        proc.run(['/bin/timedatectl', 'set-ntp', 'false' ])
        # start
        self.x_checklink = threading.Thread( name='checklink', target=self.checklink, args=(self.rpilink_address,self.rplink_period), daemon=True)
        self.x_rpilink = threading.Thread( name='rpilink', target=self.rpilink, args=(), daemon=True)
        self.x_get_wlans = threading.Thread( name='get_wlans', target=self.get_wlans, args=(), daemon=True)
        self.x_runbtscan= threading.Thread( name='runbtscan', target=self.runbtscan, args=(),  daemon=True)
        #self.x_checklink.start()
        self.x_rpilink.start()
        self.x_runbtscan.start()
        if self.AP==False:
            self.x_get_wlans.start()

    def set_clk_insance(self,clk):
        self.clk=clk
        self.clk.df=self.d
        self.clk.netdev=self.n
        
    def setlocaldata(self,data):
        for key, val in data.items():
            self.localdata[key]=val
            
    def rfcommreset(self):
        r = str( subprocess.run([ 'ps -ef  |grep -v "root "|grep -e "pi "'  ], shell=True, capture_output=True, text=True ).stdout ).strip().splitlines()
        no=1
        if len(r)>0:
            proc=[]
            for l in r:
                proc.append(l.split()[1].strip())
            for p in proc:
                subprocess.run([ 'kill -9 {}'.format(p)  ], shell=True, capture_output=True, text=True )    
                # print("kill {}".format(p))
            if self.clk!=None:
                self.clk.menu.active=False
                self.clk.info="\n!!!\n\nBT console reset\n\n!!!"
                self.clk.showinfo=True
                self.clk.showinfocount=3

                
            
    def stop(self):
        self.x_checklink.stop()
        self.x_get_wlans.stop()
        self.x_runbtscan.stop()
        if self.clk!=None:
            self.clk.go=False
            self.clk.x_cpuload.stop()
        self.go=False

    def reboot(self):
        proc.run(['/sbin/reboot', 'now']);
        self.x_checklink.stop()
        self.x_get_wlans.stop()
        self.x_runbtscan.stop()
        self.go=False
        if self.clk!=None:
            self.clk.go=False
            self.clk.x_cpuload.stop()
        #proc.run(['/sbin/reboot', 'now']);
        
    def poweroff(self):
        proc.run(['/sbin/shutdown', 'now']);
        self.x_checklink.stop()
        self.x_get_wlans.stop()
        self.x_runbtscan.stop()
        self.go=False
        if self.clk!=None:
            self.clk.go=False
            self.clk.x_cpuload.stop()
        #proc.run(['/sbin/shutdown', 'now']);

    def getlocaldata(self):
        return self.localdata
    
    def runbtscan(self):
        """ thread """
        while self.go:
            if self.bthostsflag:
                self.bthosts=h.get_bluetoothscan()
                self.logger.debug( u'[{}] rplink_command: bluetooth scan END'.format( self.display ) )
                self.bthostsflag=False
            else:
                time.sleep(1)
    
    def checklink(self,address='8.8.8.8',period=1):
        """ thread """
        while self.go:
            time.sleep(period)
            #self.logger.debug( u'[{}] ON-LINE STATUS: {}'.format(self.display, self.isonline) )
            self.isonline=h.online_status(address)
            if self.clk!=None:
                self.clk.isonline_flag=self.isonline

    def get_wlans(self):
        """ thread """
        while self.go:
            time.sleep(5)
            self.scan = h.get_wlans()
            time.sleep(5)
        
    def rpilink(self):
        """ thread """
        while self.go:
            time.sleep(self.rplink_period)    
            if self.x_checklink.is_alive()!=True:
                self.x_checklink=threading.Thread( name='checklink', target=self.checklink, args=(self.rpilink_address,self.rplink_period), daemon=True)
                self.x_checklink.start()
            if self.isonline:
                self.d=h.getrpiinfo(self.d)
                self.n=h.getnetdev()
                self.AP=h.getapparam()
                self.d['bluetooth']['bthosts']=self.bthosts
                if self.AP!=False:
                    self.AP['bridge']=True if 'br0' in self.n.keys() else False;
                    self.AP['stations']=h.getap_stalist()
                    self.AP['br0']='--' if self.AP['bridge']==False else self.n['br0'][1]
                if self.clk!=None:
                    self.clk.df=self.d
                    self.clk.netdev=self.n
                self.setlocaldata( {'msdid':self.d['msdid'], 'essid':self.d['essid'], 'coretemp':self.d['coretemp'], 'memavaiable':self.d['memavaiable'],'cpus':self.d['cpus'],'maxfreq':self.d['maxfrq'],'minfreq':self.d['minfrq'],'wlans':self.d['wlans'],'wlan_id':self.d['wlan_id'],'wlan_ch':self.d['wlan_ch']} )
                self.setlocaldata( {'scan':self.scan} )
                self.setlocaldata( {'AP':self.AP} )
                self.setlocaldata( {'bluetooth':self.d['bluetooth']} )
                #self.d['theme']= json.dumps({ 'display':self.display, 'localdata':self.localdata }) 
                tmp_buf = str(base64.standard_b64encode( bytes( json.dumps({ 'display':self.display, 'localdata':self.localdata }), 'utf-8' ) ))
                self.d['theme']=tmp_buf[ 2:(len(tmp_buf)-1) ]
                address_str = 'http://'+self.rpilink_address+'/?get=post'
                try:
                    x = requests.post( address_str, json=self.d, timeout=1)
                except requests.exceptions.RequestException as e:
                    self.logger.info( '[{}] post connection to {} fail'.format(self.display,self.rpilink_address) )
                    continue
                
                #self.logger.debug( '[{}] post connection to {} has status code {}'.format(self.display,self.rpilink_address,x.status_code) )
                if x.status_code==200:
                    self.rpihub=True
                    # read respoce
                    r=json.loads(base64.standard_b64decode(x.text))
                    #print( base64.standard_b64decode(x.text) )
                    if r['status']=='OK':
                        if not self.goodtime:
                            now=datetime.now()
                            date=now.strftime("%Y-%m-%d")
                            curent_date_time=str(r['time']).split()
                            if curent_date_time[0]!=date:
                                proc.run(['/bin/timedatectl', 'set-time', curent_date_time[0] ])
                            cp=proc.run(['/bin/timedatectl', 'set-time', curent_date_time[1] ])
                            if cp.returncode==0:
                                self.goodtime=True
                                if self.clk!=None:
                                    self.clk.goodtime=True

                        # set theme    
                        if r['cmd']['name']=='theme' and r['cmd']['sn']==self.d['serial']:
                            if self.localdata['theme']!='mono':
                                self.localdata['theme']=r['cmd']['value']
                                self.clk.setnextclockfacecolor(self.localdata['theme'])
                            self.logger.debug( u'[{}] rplink_command: hostname is chneged from {} to {}'.format(self.display,self.d['hostname'],r['cmd']['value']) )
                        # set hostname    
                        if r['cmd']['name']=='hostname' and r['cmd']['sn']==self.d['serial']:
                            h.hostname(r['cmd']['value'])
                            self.logger.debug( u'[{}] rplink_command: hostname is chneged from {} to {}'.format(self.display,self.d['hostname'],r['cmd']['value']) )
                        # set rootaccesskey
                        if r['cmd']['name']=='rootaccesskey' and r['cmd']['sn']==self.d['serial']:
                            h.addtextline( "/root/.ssh/authorized_keys", str(r['cmd']['value']).strip() )
                            self.logger.debug( u'[{}] rplink_command: root access key for {} is added'.format(self.display,self.d['hostname'] ) )
                        # set piaccesskey
                        if r['cmd']['name']=='piaccesskey' and r['cmd']['sn']==self.d['serial']:
                            h.addtextline( "/home/pi/.ssh/authorized_keys", str(r['cmd']['value']).strip() )
                            self.logger.debug( u'[{}] rplink_command: root access key for {} is added'.format(self.display,self.d['hostname'] ) )
                        # set pipass
                        if r['cmd']['name']=='pipass' and r['cmd']['sn']==self.d['serial']:
                            h.setuserpass('pi',str(r['cmd']['value']).strip())
                            self.logger.debug( u'[{}] rplink_command: user pi passwd for {} is changeed'.format(self.display,self.d['hostname'] ) )
                        # exec btdiscover
                        if r['cmd']['name']=='btdiscover' and r['cmd']['sn']==self.d['serial']:
                            h.btdiscover()
                            self.logger.debug( u'[{}] rplink_command: bluetootch discoverable on'.format(self.display) )
                        # exec btdiscoveroff
                        if r['cmd']['name']=='btdiscoveroff' and r['cmd']['sn']==self.d['serial']:
                            h.btdiscoveroff()
                            self.logger.debug( u'[{}] rplink_command: bluetootch discoverable off'.format(self.display) )
                        # exec btremove
                        if r['cmd']['name']=='btremove' and r['cmd']['sn']==self.d['serial']:
                            h.btremove( str( r['cmd']['value']).strip() )
                            self.logger.debug( u'[{}] rplink_command: remove bluetootch device {}'.format(self.display, str( r['cmd']['value']).strip() ) )
                        # exec btscan
                        if r['cmd']['name']=='btscan' and r['cmd']['sn']==self.d['serial']:
                             if self.bthostsflag==False:
                                self.bthostsflag=True
                                self.logger.debug( u'[{}] rplink_command: bluetooth scan START'.format( self.display ) )
                        # exec reboot
                        if r['cmd']['name']=='reboot' and r['cmd']['sn']==self.d['serial']:
                            if self.clk!=None:
                                self.clk.info=u'\n\n!!!\n system RELOAD\n!!!'
                                self.clk.showinfo=True
                            self.logger.debug( u'[{}] rplink_command: system reboot'.format(self.display) )
                            self.reboot()
                        # exec poweroff
                        if r['cmd']['name']=='poweroff' and r['cmd']['sn']==self.d['serial']:
                            if self.clk!=None:
                                self.clk.info=u'\n\n!!!\n system POWER OFF\n!!!'
                                self.clk.showinfo=True
                            self.logger.debug( u'[{}] rplink_command: system poweroff'.format(self.display) )
                            self.poweroff()
                        # exec towlanAP
                        if r['cmd']['name']=='towlanAP' and r['cmd']['sn']==self.d['serial']:
                            if self.clk!=None:
                                self.clk.info=u'\n\n!!!\n switch to:\n Routed AP mode\n and RELOAD\n!!!'
                                self.clk.showinfo=True
                            self.logger.debug( u'[{}] rplink_command: switch to wlanAP'.format(self.display) )
                            proc.run(['chmod 0700 /root/lcd144/clean/setap.sh'],shell=True)
                            proc.run(['/root/lcd144/clean/setap.sh >/root/lcd144/clean/setap.log'],shell=True,capture_output=True,encoding='utf-8');
                            proc.run(['chmod 0644 /root/lcd144/clean/setap.sh'],shell=True)
                            self.reboot()
                        # exec towlanBridgeAP
                        if r['cmd']['name']=='towlanBridgeAP' and r['cmd']['sn']==self.d['serial']:
                            if self.clk!=None:
                                self.clk.info=u'\n\n!!!\n switch to:\n Bridged AP mode\n and RELOAD\n!!!'
                                self.clk.showinfo=True
                            self.logger.debug( u'[{}] rplink_command: switch to towlanBridgeAP'.format(self.display) )
                            proc.run(['chmod 0700 /root/lcd144/clean/setbrap.sh'],shell=True)
                            proc.run(['/root/lcd144/clean/setbrap.sh >/root/lcd144/clean/setbrap.log'],shell=True,capture_output=True,encoding='utf-8');
                            proc.run(['chmod 0644 /root/lcd144/clean/setbrap.sh'],shell=True)
                            self.reboot()
                        # exec towlanClient
                        if r['cmd']['name']=='towlanClient' and r['cmd']['sn']==self.d['serial']:
                            if self.clk!=None:
                                self.clk.info=u'\n\n!!!\n switch to:\n WLAN Station mode\n and RELOAD\n!!!'
                                self.clk.showinfo=True
                            self.logger.debug( u'[{}] rplink_command: switch to wlan Client'.format(self.display) )
                            proc.run(['chmod 0700 /root/lcd144/clean/clean.sh'],shell=True)
                            proc.run(['/root/lcd144/clean/clean.sh >/root/lcd144/clean/clean.log'],shell=True,capture_output=True,encoding='utf-8');
                            proc.run(['chmod 0644 /root/lcd144/clean/clean.sh'],shell=True)
                            self.reboot()
                        # set updatewlan0ip
                        if r['cmd']['name']=='updatewlan0ip' and r['cmd']['sn']==self.d['serial']:
                            if self.clk!=None:
                                self.clk.info=u'\n\n!!!\n update IP to:\n '+str(r['cmd']['value']).strip()+'\n and RELOAD\n!!!'
                                self.clk.showinfo=True
                            h.setip(str(r['cmd']['value']).strip(),'wlan0','static')
                            self.logger.debug( u'[{}] rplink_command: IP for wlan0 update to {} for{}'.format(self.display, str(r['cmd']['value']).strip(), self.d['hostname'] ) )
                            self.logger.debug( u'[{}] rplink_command: system reboot'.format(self.display) )
                            self.reboot()
                        # exec update agent software <LCD144,|oled13>
                        if r['cmd']['name']=='update' and r['cmd']['sn']==self.d['serial']:
                            self.logger.debug( u'[{}] rplink_command: code update from git repo'.format(self.display) )
                            result = proc.run(['/bin/git pull'], cwd='/root/'+r['cmd']['service'], shell=True, capture_output=True, text=True);
                            #print("stdout: ", result.stdout)
                            #print("stderr: ", result.stderr)
                        # set wpa_supplicand.conf data for a WLAN conection
                        if r['cmd']['name']=='wlan_client' and r['cmd']['sn']==self.d['serial']:
                            self.logger.debug( u'[{}] rplink_command: set wlan client connection data essid: {} wpa_key: {}'.format(self.display, r['cmd']['essid'], r['cmd']['wpa_key']) )
                            out=h.set_wpa_supplicant(essid=r['cmd']['essid'],wpa_key=r['cmd']['wpa_key'])
                            with open('/etc/wpa_supplicant/wpa_supplicant.conf', "wt") as f:
                                f.write(out)
                            self.reboot()
                        if r['cmd']['name']=='apsetparams' and r['cmd']['sn']==self.d['serial']:
                            info=u'[{}] rplink_command: set AP params - ssid:"{}", pass: ***, hw_mode:{}, channel:{}, ignore_broadcast_ssid:{}'.format(self.display, r['cmd']['ssid'], r['cmd']['hw_mode'], r['cmd']['channel'], r['cmd']['ignore_broadcast_ssid'])
                            self.logger.debug( info )
                            params={ 'ssid':r['cmd']['ssid'],'wpa_passphrase':r['cmd']['wpa_passphrase'],'hw_mode':r['cmd']['hw_mode'],'channel':r['cmd']['channel'],'ignore_broadcast_ssid':r['cmd']['ignore_broadcast_ssid'] }
                            h.setapparam(params)
                            self.reboot()
                            
                    else:
                        self.logger.debug( u'[{}] rplink_responce_error: {}'.format(self.display, r['status']) )
                else:
                    if self.rpihub==True:
                        self.logger.debug( u'[{}] rplink_status_error: {}'.format(self.display, x.status_code ) )
                    self.rpihub=False
            else:
                if self.rpihub==True:
                    self.rpihub=False
                    self.logger.debug( '[{}] device is OF-Line, address {}'.format(self.display,self.rpilink_address) )
        else:
            self.x_rpilink.stop() 
            
            
                       
# use the rplink 'solo' as a system service
rpl=None
def main():
    global rpl
    link_address=sys.argv[1] if len(sys.argv)>1 else 'rpi.ontime24.pl'
    link_period=int(sys.argv[2]) if len(sys.argv)>2 else 1
    local_data={ 'theme': 'headless' }
    try:
        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigterm_handler)
        signal.signal(signal.SIGHUP, sighup_handler)
        rpl = rplink(display='solo',rpilink_address=link_address,rpilink_period=link_period, localdata=local_data)
        
        while rpl.go:
            time.sleep(1)
    
    except IOError as e:
        rpl.logger.debug( u'[{}] detect IOError {}'.format(rpl.display, e) )
        print(e)
        
    except KeyboardInterrupt:    
        rpl.logger.debug( u'[{}] exit by KeyboardInterrupt {}'.format(rpl.display) )
        rpl.stop()
        time.sleep(1)
        sys.exit( 0 )    


def sigint_handler(signum, frame):
    global rpl
    rpl.logger.debug( u'[{}] exit by sigint'.format(rpl.display) )
    rpl.stop()
    time.sleep(1)
    sys.exit( 0 )    

def sigterm_handler(signum, frame):
    global rpl
    rpl.logger.debug( u'[{}] exit by sigterm'.format(rpl.display) )
    rpl.stop()
    time.sleep(1) 
    sys.exit( 0 )    

def sighup_handler(signum, frame):
    global rpl
    rpl.logger.debug( u'[{}] get SIGHUP'.format(rpl.display) )


if __name__ == "__main__":
    main()

#end of rpilink()

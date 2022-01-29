#!/usr/bin/python
# -*- coding:utf-8 -*-

# /*****************************************************************************
# * | File        :	  rplink.py
# * | Author      :   Robert Kotrys
# * | Function    :   Basic class to use with Raspberry Pi link service
# * | Info        :   require files: helper.py
# *----------------
# * | This version:   V1.0.1
# * | Date        :   2022-01-23
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
        self.x_checklink.start()
        self.x_rpilink.start()
        if self.AP!=False:
            self.x_get_wlans.start()

    def set_clk_insance(self,clk):
        self.clk=clk
        self.clk.df=self.d
        self.clk.netdev=self.n
        
    def setlocaldata(self,data):
        for key, val in data.items():
            self.localdata[key]=val

    def getlocaldata(self):
        return self.localdata
    
    def stop(self):
        self.go=False

    def checklink(self,address='8.8.8.8',period=1):
        """ thread """
        while self.go:
            time.sleep(period)
            self.isonline=h.online_status(address)
            if self.clk!=None:
                self.clk.isonline_flag=self.isonline

    def get_wlans(self):
        """ thread """
        while self.go:
            time.sleep(1.5)
            self.scan = h.get_wlans()
            time.sleep(9.33)
        
    def rpilink(self):
        """ thread """
        while self.go:
            time.sleep(self.rplink_period)    
            if self.isonline:
                self.d=h.getrpiinfo(self.d)
                self.n=h.getnetdev()
                self.AP=h.getapparam()
                if self.AP!=False:
                    pass
                if self.clk!=None:
                    self.clk.df=self.d
                    self.clk.netdev=self.n
                self.setlocaldata( {'msdid':self.d['msdid'], 'essid':self.d['essid'], 'coretemp':self.d['coretemp'], 'memavaiable':self.d['memavaiable'],'cpus':self.d['cpus'],'maxfreq':self.d['maxfrq'],'minfreq':self.d['minfrq'],'wlans':self.d['wlans'],'wlan_id':self.d['wlan_id'],'wlan_ch':self.d['wlan_ch']} )
                self.setlocaldata( {'scan':self.scan} )
                self.setlocaldata( {'AP':self.AP} )
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
                        # exec reboot
                        if r['cmd']['name']=='reboot' and r['cmd']['sn']==self.d['serial']:
                            self.logger.debug( u'[{}] rplink_command: system reboot'.format(self.display) )
                            result = proc.run(['/bin/systemctl', 'reboot'],capture_output=True, text=True);
                        # exec poweroff
                        if r['cmd']['name']=='poweroff' and r['cmd']['sn']==self.d['serial']:
                            self.logger.debug( u'[{}] rplink_command: system poweroff'.format(self.display) )
                            result = proc.run(['/bin/systemctl', 'poweroff'],capture_output=True, text=True);
                        # exec towlanAP
                        if r['cmd']['name']=='towlanAP' and r['cmd']['sn']==self.d['serial']:
                            self.logger.debug( u'[{}] rplink_command: switch to wlanAP'.format(self.display) )
                            result = proc.run(['/root/clean/setap.sh'],capture_output=True, text=True);
                        # exec towlanClient
                        if r['cmd']['name']=='towlanClient' and r['cmd']['sn']==self.d['serial']:
                            self.logger.debug( u'[{}] rplink_command: switch to wlan Client'.format(self.display) )
                            result = proc.run(['/root/clean/clean.sh'],capture_output=True, text=True);
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
                            run = subprocess.run(['/sbin/reboot','now'], capture_output=True, encoding='utf-8')    
                        if r['cmd']['name']=='apsetparams' and r['cmd']['sn']==self.d['serial']:
                            info=u'[{}] rplink_command: set AP params - ssid:"{}", pass: ***, hw_mode:{}, channel:{}, ignore_broadcast_ssid:{}'.format(self.display, r['cmd']['ssid'], r['cmd']['hw_mode'], r['cmd']['channel'], r['cmd']['ignore_broadcast_ssid'])
                            self.logger.debug( info )
                            params={ 'ssid':r['cmd']['ssid'],'wpa_passphrase':r['cmd']['wpa_passphrase'],'hw_mode':r['cmd']['hw_mode'],'channel':r['cmd']['channel'],'ignore_broadcast_ssid':r['cmd']['ignore_broadcast_ssid'] }
                            h.setapparam(params)
                            proc.run(['systemctl', 'reboot']);
                            
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
        time.sleep(3)
        sys.exit( 0 )    


def sigint_handler(signum, frame):
    global rpl
    rpl.logger.debug( u'[{}] exit by sigint'.format(rpl.display) )
    time.sleep(3)
    sys.exit( 0 )    

def sigterm_handler(signum, frame):
    global rpl
    rpl.logger.debug( u'[{}] exit by sigterm'.format(rpl.display) )
    time.sleep(3) 
    sys.exit( 0 )    

def sighup_handler(signum, frame):
    global rpl
    rpl.logger.debug( u'[{}] get SIGHUP'.format(rpl.display) )


if __name__ == "__main__":
    main()

#end of rpilink()

#!/usr/bin/python
# -*- coding:utf-8 -*-

# /*****************************************************************************
# * | File        :	  helper.py
# * | Author      :   Robert Kotrys
# * | Function    :   Basic functions to use with Raspberry Pi devives
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2022-01-09
# * | Info        :   
# ******************************************************************************/

import subprocess

def getip():
    """ get a first IP v.4 address """
    ip="- no IP -"
    for dev in ('eth0','wlan0'):
        w=str( subprocess.run(["ip -4 a l "+dev+"|grep inet"], shell=True, capture_output=True, text=True ).stdout ).split()
        if( len(w)>1 ):
            ip = w[1]
            break
    return ip       

def setuserpass(user='pi',userpass='raspberry'):
    """ set user password """
    instr='echo "{}:{}"|chpasswd'.format(user,userpass)
    out = str( subprocess.run([ 'echo "{}:{}"|chpasswd'.format(user,userpass) ], shell=True, capture_output=True, text=True ).stdout )
    print("[setuserpass]\n"+out)

def settime(address="rpi.ontime24.pl"):
    """ get time from 'address' site and set the time to system clock """
    try:
        r = str(subprocess.check_output(['wget', '-O', '/tmp/datetime.txt', '-q', address+'/?get=datetime'] ), encoding='utf-8').strip()
    except subprocess.CalledProcessError:
        r= None
    if r!=None:
        with open("/tmp/datetime.txt","r") as f:
            dt = f.read().split()
    r = str(subprocess.check_output(['timedatectl', 'set-ntp', 'false'] ), encoding='utf-8').strip()    
    r = str(subprocess.check_output(['timedatectl', 'set-time', dt[0] ]), encoding='utf-8').strip()
    r = str(subprocess.check_output(['timedatectl', 'set-time', dt[1] ]), encoding='utf-8').strip()    

def gettemp():
    """ get the core temperature and return as float in 'C """
    with open('/sys/class/thermal/thermal_zone0/temp', "r") as file:
        tmp = float(file.read(5))/1000
    return tmp

def hostname(name=None):
    """ get system hostname od set 'name' as system hostname"""
    oldhostname=str( subprocess.run(["/bin/hostname"], capture_output=True, text=True ).stdout ).strip()
    if name!=None:
        # set hostname to name
        subprocess.run(["/bin/hostname", name])
        with open("/etc/hostname","w") as f:
            f.write(name)
        with open("/etc/hosts","r") as f:
            oldhosts=str(f.read()).splitlines()
        with open("/etc/hosts","w") as f:
            for line in oldhosts:
                if oldhostname in line:
                    f.write(line.replace(oldhostname, name)+'\n')
                else:     
                    f.write(line+'\n')
    else:
        # get hostname
        hostname=str( subprocess.run(["/bin/hostname"], capture_output=True, text=True ).stdout ).strip()
        return hostname

def find_net(buf):
    start=str(buf).find('network={')
    stop=str(buf).find('}')
    if start>-1 and stop > start:
        net=buf[start:(stop+1)]
    else:
        net=False
    if net!=False:
        ssid=net[net.find('ssid="')+len('ssid="'):]
        ssid=ssid[0:ssid.find('"')]
        return (net, ssid, buf[0:start]+buf[stop+1:])        
    else:
        return (False, '', buf)

def get_wlans_def():
    with open('/etc/wpa_supplicant/wpa_supplicant.conf','rt') as f:
        input=str(f.read()).strip()
        (net_def, ssid_name, buf) = find_net(input)
        if net_def==False:
            return False
    net_dic={}
    net_dic[ssid_name]=net_def
    while net_def!=False: 
        (net_def, ssid_name, buf) = find_net(buf)
        if net_def!=False:
            net_dic[ssid_name]=net_def
    return net_dic

def get_wlans(sortkey='level'):
    r = subprocess.run([ 'iwlist wlan0 scanning |grep -e Cell -e ESSID -e Quality -e  Channel:' ],shell=True,capture_output=True,encoding='utf-8')
    wlans_dic={}
    wlans=[]
    if r.returncode==0:
        #print(r.stdout)
        lines=str(r.stdout).strip().splitlines()
        i=0
        while i<(len(lines)-3):
            address = lines[i].strip().split()[4].strip()
            channel = lines[i+1].strip().split(':')[1].strip()
            level = lines[i+2].strip().split()[2].split('=')[1].strip()
            name = lines[i+3].strip().split(':')[1].strip().replace('"', '')
            wlans.append( {'address':address, 'channel':channel, 'level':level, 'name':name } )
            i += 4
        wlans.sort(reverse=True, key=lambda x:float(x[sortkey]))
    for item in wlans: wlans_dic[item['name']]=item 
    return wlans_dic

def set_wpa_supplicant( essid, wpa_key, add=True, priority=1, country='pl' ):
    if len(essid)>1 and len(wpa_key)>7:
        head=u"country={}\nupdate_config=1\nctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n".format(country)
        net=str(u'\nnetwork={\nscan_ssid=1\nssid=\"[[1]]\"\npsk=[[2]]\npriority=[[3]]\n}\n')
        r = subprocess.run(['echo '+str(wpa_key)+' |/bin/wpa_passphrase '+str(essid) ],shell=True,capture_output=True,encoding='utf-8')
        if r.returncode==0:
            psk=str(r.stdout).splitlines()[4].strip().split('=')[1]
            net=net.replace( '[[1]]', essid ).replace( '[[2]]', psk) .replace( '[[3]]', str(priority) )
            if add:
                net_dic=get_wlans_def()
                buf=head + net
                for n in net_dic.keys():
                    if n!=essid:
                        buf=buf+'\n'+net_dic[n]
            else:
                buf = head + net
            return( buf )
        else:
            return r.stdout+'\n'+r.stderr
    else:
        return "{} {}".format(essid, wpa_key)
    
def online_status(address="8.8.8.8"):
    """ check on-line status od 'address' host with ping command """
    try:
        r = str(subprocess.check_output(['/bin/ping', '-4', '-c', '3', '-i', '0', '-f', '-q', address] ), encoding='utf-8').strip()
    except subprocess.CalledProcessError:
        r = '0 received'
    ind = int(r.find(' received'))
    if( int(r[ind-1:ind]) > 0 ):
        return True
    else:
        return False        
    
def getnetdev():
    """ scan net devices and return basic prams as dictionary: netdev[devname]=(devname,ip,mac) """
    netdev={}
    with open('/proc/net/dev','r') as f:
        dev = f.read()
        for devname in ['eth0', 'eth1', 'wlan0', 'wlan1']:
            if dev.find(devname) > -1:
                buf = str(subprocess.check_output([ 'ip', '-4', 'address', 'show', 'dev', devname ]), encoding='utf-8')
                if len(buf)>1: 
                    ip=buf.strip().splitlines()[1].split()[1]
                else:
                    ip='--'
                mac=str(subprocess.check_output([ 'ip', 'link', 'show', 'dev', devname ]), encoding='utf-8').strip().splitlines()[1].split()[1]
                netdev[devname]=(devname,ip,mac)
    return netdev            
    
def getrpiinfo(dictionary=True, df={} ):
    """ getrpiinfo(out=True) collect RPi params and status information, return as dictionary """
    newdata = True if len(df)==0 else False
    df['hostname']=str(subprocess.check_output(['hostname'] ), encoding='utf-8').strip()
    netdev=getnetdev()
    if "eth0" in netdev.keys():
        ip=netdev['eth0'][1]
        emac=netdev['eth0'][2]
    else:
        ip='--'
        emac='--'
    if "wlan0" in netdev.keys():
        wip=netdev['wlan0'][1]
        wmac=netdev['wlan0'][2]
    else:
        wip='--'
        wmac='--'
    df['ip']=ip
    df['wip']=wip
    df['emac']=emac
    df['wmac']=wmac
    with open('/proc/meminfo','r') as f:
        df['memtotal']=int(str(f.readline()).strip().split()[1])//1000
        df['memfree']=int(str(f.readline()).strip().split()[1])//1000
        df['memavaiable']=int(str(f.readline()).strip().split()[1])//1000
    r = subprocess.run(['iwgetid', '-r'], capture_output=True, encoding='utf-8')
    ra = subprocess.run(['iwgetid', '-ra'], capture_output=True, encoding='utf-8')
    rc = subprocess.run(['iwgetid', '-rc'], capture_output=True, encoding='utf-8')
    if r.returncode==0:
        df['essid']   = str(r.stdout).strip()
        df['wlan_id'] = str(ra.stdout).strip()
        df['wlan_ch'] = str(rc.stdout).strip()
    else:
        df['essid']   = '--'    
        df['wlan_id'] = '--'
        df['wlan_ch'] = '--'
    df['coretemp']=gettemp()
    # static
    if newdata:
        r = subprocess.run(['/bin/lscpu'], capture_output=True, encoding='utf-8')
        if r.returncode==0:
            lines=str(r.stdout).strip().splitlines()
            df['cpus']=lines[2].split(':')[1].strip()
            df['mdl']=lines[9].split(':')[1].strip()
            df['maxfrq']=lines[11].split(':')[1].strip()
            df['minfrq']=lines[12].split(':')[1].strip()
        else:
            df['cpus']='--'
            df['mdl']='--'
            df['maxfrq']='--'
            df['minfrq']='--'
        with open('/boot/.id','r') as f:
            df['msdid']=str(f.readline()).strip()
        with open('/proc/cpuinfo','r') as f:
            output=str(f.read()).strip().splitlines()
        for line in output:
            l=str(line).strip().split()
            if len(l)>0 and l[0]=='Serial':
                df['serial']=l[2][8:]
            if len(l)>0 and l[0]=='Hardware':
                df['chip']=l[2]
            if len(l)>0 and l[0]=='Revision':
                df['revision']=l[2]
            if len(l)>0 and l[0]=='Model':
                df['model']=str(u' '.join(l[2:])).replace('Raspberry Pi','RPi')
        df['release']=str(subprocess.check_output(['uname','-r'] ), encoding='utf-8').strip()
        df['version']='???'
        with open('/etc/os-release','r') as f:
            output=f.readlines()
        for line in output:
            l=line.split('=')
            if l[0]!='VERSION':
                continue
            else:
                df['version']=str(l[1]).strip().replace('"','').replace("\n",'') 
                break   
        df['machine']=str(subprocess.check_output(['uname','-m'] ), encoding='utf-8').strip()
        buf=str(subprocess.check_output(['blkid','/dev/mmcblk0'] ), encoding='utf-8').strip().split()[1]
        df['puuid']=buf[8:16]
        buf=str(subprocess.check_output(['df','-h'] ), encoding='utf-8').strip().splitlines()[1].strip().split()
        df['fs_total']=buf[1]
        df['fs_free']=buf[3]
        wlans=get_wlans_def()
        wlans_str=u''
        for w in wlans.keys(): wlans_str += u'{},'.format(w)
        df['wlans']=wlans_str[0:len(wlans_str)-1] 

    if dictionary:
        return df
    else:
        return rpiinfo_str( df )
    
def rpiinfo_str( df ):
        buf=""
        buf = buf + u"{}\n".format(df['model'])
        buf = buf + u"host: {}\n".format(df['hostname'])
        buf = buf + u"msdid: {}\n".format(df['msdid'])
        buf = buf + u"ser: {}\n".format(df['serial'])
        buf = buf + u"puuid: {}\n".format(df['puuid'])
        buf = buf + u"HW:{} {}\n".format(df['chip'],df['machine'])
        buf = buf + u"Linux: {}\n".format(df['release'])
        buf = buf + u"ver: {}\n".format(df['version'])
        buf = buf + u"ESSID: {}\n".format(df['essid'])
        buf = buf + u"CPU temp: {:2.0f}\n".format(float(df['coretemp']))
        if len(df['ip'])>2:
            buf = buf + u"eth0 IP:\n {}\n".format(df['ip'])
        if len(df['wip'])>2:
            buf = buf + u"wlan0 IP:\n {}\n".format(df['wip'])
        if len(df['emac'])>2:
            buf = buf + u"eth0 MAC:\n {}\n".format(df['emac'])
        if len(df['wmac'])>2:
            buf = buf + u"wlan0 MAC:\n {}\n".format(df['wmac'])
        for key, value in df.items():
            if key in ['model', 'serial', 'hostname', 'chip', 'machine', 'puuid','release', 'version','essid','revision','msdid','coretemp','ip','wip','emac','wmac']:
                continue
            buf = buf + u"{}: {}\n".format(key,value)
        return buf
    

#!/bin/bash
#
# set bridged AP
#
SETAP="/root/lcd144/clean/setbrap"
#
# bridge-utils
BRU=`apt --installed list 2>/dev/null |grep bridge-utils`
if [ -z "$BRU" ]
then
echo "Install: bridge-utils"
apt-get install -q -y bridge-utils
fi
#
# hostapd
APSTATUS=`systemctl is-active hostapd`
if [ "$APSTATUS" != "active" ]
then
echo "Install: hostapd"
apt-get install -q -y hostapd
systemctl unmask hostapd
fi
systemctl enable hostapd
#
# dnsmasq
DNSMASQ=`systemctl is-active dnsmasq`
if [ "$DNSMASQ" == "active" ]
then
echo "Purge dnsmasq"
apt-get -q -y purge dnsmasq
fi
#
# netfilter-persistent iptables-persistent
NETF=`apt --installed list 2>/dev/null |grep -e netfilter-persistent -e iptables-persistent`
if [ -n "$NETF" ]
then
apt-get purge -y -q netfilter-persistent iptables-persistent
fi
#
echo "Delete MASQUERADE"
MASQ=`iptables -t nat -L POSTROUTING --line-numbers|grep MASQUERADE|nawk '{print $1}'`
for N in $MASQ
do
iptables -t nat -D POSTROUTING $N
done
#
# routed-ap.conf
if [ -e "/etc/sysctl.d/routed-ap.conf" ]
then
rm /etc/sysctl.d/routed-ap.conf
fi
echo "Copy config file"
cp -f $SETAP/dhcpcd.conf /etc/dhcpcd.conf
cp -f $SETAP/hostapd.conf /etc/hostapd/hostapd.conf
cp -f $SETAP/bridge-br0.netdev /etc/systemd/network/bridge-br0.netdev
cp -f $SETAP/br0-member-eth0.network  /etc/systemd/network/br0-member-eth0.network
#
# enable systemd-networkd
$SYSNET=`systemctl is-active systemd-networkd`
if [ "$SYSNET" != "active" ]
then
echo "Activate: systemd-networkd"
systemctl unmask systemd-networkd
systemctl enable systemd-networkd
fi
#
echo "Uncbock WLAN and bluetooth"
rfkill unblock wlan
rfkill unblock bluetooth
#
echo "Activate: apt autoremove"
apt-get -y -q autoremove
#
echo "AP bridged service is SET!!!"
#echo "in 1 s system will be rebooted"
#sleep 1
#systemctl reboot


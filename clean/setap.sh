#!/bin/bash
#
# set routed AP
#
SETAP="/root/lcd144/clean/setap"
#
#
# cleaning conf files
FILE="/etc/hostapd/hostapd.conf"
if test -f "$FILE"; then
rm -f $FILE
echo "Remove: $FILE"
fi
FILE="/etc/systemd/network/bridge-br0.netdev"
if test -f "$FILE"; then
rm -f $FILE
echo "Remove: $FILE"
fi
FILE="/etc/systemd/network/br0-member-eth0.network"
if test -f "$FILE"; then
echo "Remove: $FILE"
rm -f $FILE
fi
FILE="/etc/dnsmasq.conf"
if test -f "$FILE"; then
echo "Remove: $FILE"
rm -f $FILE
fi
#
# hostapd
STATUS=`apt --installed list 2>/dev/null |grep hostapd`
if [ -z $STATUS ]
then
apt-get -y -q install hostapd
echo "Inatalled: hostapd"
fi
systemctl unmask hostapd
systemctl enable hostapd
#
# dnsmasq
STATUS=`apt --installed list 2>/dev/null |grep dnsmasq`
if [ -z $STATUS ]
then
apt-get install -y -q dnsmasq
echo "Inatalled: dnsmasq"
fi
systemctl unmask dnsmasq
systemctl enable dnsmasq
#
# netfilter-persistent iptables-persistent
echo "Install: netfilter-persistent iptables-persistent"
NETF=`apt --installed list 2>/dev/null |grep -e netfilter-persistent -e iptables-persistent`
if [ -z $NETF ]
then
echo "Instaled: netfilter-persistent iptables-persistent"
apt-get install -y -q netfilter-persistent iptables-persistent
fi
#
# set NAT on eth0
echo "Set MASQUERADE"
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
echo "Save MASQUERADE"
netfilter-persistent save
#
# set conf files
cp $SETAP/dhcpcd.conf /etc/dhcpcd.conf
echo "Copy: $SETAP/dhcpcd.conf"
cp $SETAP/routed-ap.conf /etc/sysctl.d/routed-ap.conf
echo "Copy: $SETAP/routed-ap.conf"
cp $SETAP/dnsmasq.conf /etc/dnsmasq.conf
echo "Copy: $SETAP/dnsmasq.conf"
cp $SETAP/hostapd.conf /etc/hostapd/hostapd.conf
echo "Copy: $SETAP/hostapd.conf"
#
# unblock radio
rfkill unblock wlan
rfkill unblock bluetooth
echo "WLAN and Bluetooth unblocked"
#
echo "Activate: apt autoremove"
apt-get -y -q autoremove
# reboot
echo "AP service is SET!!!"
#echo "in 1s system will be rebooted"
#sleep 1
#systemctl reboot


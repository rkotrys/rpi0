#!/bin/bash
#
# clean access point config in RPI4
#
cp -f /root/lcd144/clean/clean/dhcpcd.conf /etc/dhcpcd.conf
cp -f /root/lcd144/clean/clean/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf
cp -f /root/lcd144/clean/bt/bluetooth.service /lib/systemd/system/bluetooth.service
cp -f /root/lcd144/clean/bt/rfcomm.service /etc/systemd/system/rfcomm.service
cp -f /root/lcd144/clean/bt/main.conf /etc/bluetooth/main.conf
cp -f /root/lcd144/clean/bt/rfcomm.conf /etc/bluetooth/rfcomm.conf
#
# rfcomm enable
RFCOMM=`systemctl is-active rfcomm`
if [ "$RFCOMM" != "active" ]
then
systemctl unmask rfcomm
systemctl enable frcomm
fi
#
FILE="/etc/sysctl.d/routed-ap.conf"
if test -f "$FILE"; then
rm -f $FILE
echo "Remove: $FILE"
fi
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
rm -f $FILE
echo "Remove: $FILE"
fi
FILE="/etc/dnsmasq.conf"
if test "$FILE"; then
rm -f $FILE
echo "Remove: $FILE"
fi
#
# netfilter-persistent iptables-persistent
echo "[netfilter-persistent iptables-persistent]"
NETF=`apt --installed list 2>/dev/null |grep -e netfilter-persistent -e iptables-persistent`
if [ -n $NETF ]
then
echo "Purge netfilter-persistent iptables-persistent"
apt-get purge -y -q netfilter-persistent iptables-persistent
fi
#
echo "Delete MASQUERADE"
iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
#
# hostapd
HOSTAPD=`systemctl is-active hostapd`
if [ "$HOSTAPD" == "active" ]
then
systemctl stop hostapd
systemctl disable hostapd
echo "purge hostapd"
apt-get purge -y -q hostapd
fi
#
# dnsmasq
DNSMASQ=`systemctl is-active dnsmasq`
if [ "$DNSMASQ" == "active" ]
then
systemctl stop dnsmasq
systemctl disable dnsmasq
echo "Purge dnsmasq"
apt-get purge -y -q dnsmasq
fi
#
# systemd-networkd
echo "systemd-networkd"
SYSTNET=`systemctl is-active systemd-networkd`
if [ "$SYSTNET" == "active" ]
then
echo "Disable systemd-networkd"
systemctl disable systemd-networkd
fi
#
#
echo "Activate: apt autoremove"
apt-get -y -q autoremove
#
# reboot
echo "AP service is CLEANED!!!"
#echo "in 3s system will be rebooted"
#sleep 3
#systemctl reboot


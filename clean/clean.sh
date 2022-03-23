#!/bin/bash
#
SYS_VERSION=`cat /etc/os-release|grep VERSION_ID|nawk -F= '{print $2}'|sed 's/"//g' - `
#
CLEANP="/root/lcd144/clean/clean"
CLEANBT="/root/lcd144/clean/bt"
# clean access point config in RPI4
#
cp -f $CLEANP/dhcpcd.conf /etc/dhcpcd.conf
cp -f $CLEANP/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf
cp -f $CLEANBT/rfcomm.service /etc/systemd/system/rfcomm.service
cp -f $CLEANBT/main.conf /etc/bluetooth/main.conf
cp -f $CLEANBT/rfcomm.conf /etc/bluetooth/rfcomm.conf
#
if [ $SYS_VERSION=="10" ]; then
cp -f $CLEANBT/bluetooth.service.10 /lib/systemd/system/bluetooth.service
fi
#
if [ $SYS_VERSION=="11" ]; then
cp -f $CLEANBT/bluetooth.service.11 /lib/systemd/system/bluetooth.service
fi
#
# rfcomm enable
RFCOMM=`systemctl is-active rfcomm`
if [ "$RFCOMM" != "active" ]
then
systemctl unmask rfcomm
systemctl enable rfcomm
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
#
# netfilter-persistent iptables-persistent
echo "[netfilter-persistent iptables-persistent]"
NETF=`apt --installed list 2>/dev/null |grep -e netfilter-persistent -e iptables-persistent`
if [ -n "$NETF" ]
then
echo "Purge netfilter-persistent iptables-persistent"
sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y -q netfilter-persistent iptables-persistent
fi
#
echo "Delete MASQUERADE"
_TMP=`iptables -t nat -L POSTROUTING --line-numbers|grep MASQUERADE|nawk '{print $1}'`
MASQ=`echo -e $_TMP|sort -b`
for N in $MASQ
do
iptables -t nat -D POSTROUTING $N
done
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


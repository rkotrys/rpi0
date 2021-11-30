#!/bin/bash
# change host name
#
# usage: setnewhostname.sh <new host name> <old host name>
#
/bin/hostname $1
echo $1 >/etc/hostname
cat /etc/hosts |grep -v $2 >/tmp/hosts
echo 128.0.1.1 $1 >>/tmp/hosts
mv /tmp/hosts /etc/hosts
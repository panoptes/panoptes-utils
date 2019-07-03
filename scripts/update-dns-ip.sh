#!/bin/bash -e

# Put this in a cronjob so name is updated on each reboot, i.e. crontab -e
# @reboot /home/panoptes/bin/update-dns-ip.sh 2>&1 >> /var/panoptes/logs/update-ip.sh

_DEVICE=${1:-enp0s25}
_DOMAIN="$(hostname)"
_HOSTKEY="${DNS_HOSTKEY}"
# _HOSTKEY="${DNS_HOSTKEY:-KEY_GOES_HERE}"

# Sleep if coming from cron so network can start
SLEEP_ME="${SLEEP_TIME:-0}"
sleep "${SLEEP_ME}"

_IP=$(ip address show ${_DEVICE} | grep 'inet\b' | awk '{print $2}' | cut -d/ -f1)

date +%F
printf "Updating %s with %s\n" "$_DOMAIN" "$_IP"

wget -qO- --read-timeout=0.0 --waitretry=5 --tries=400 "http://freedns.afraid.org/dynamic/update.php?${_HOSTKEY}&address=${_IP}"

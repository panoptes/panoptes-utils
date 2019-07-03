#!/bin/bash -e

_DEVICE=${1:-enp0s25}
_DOMAIN="$(hostname)"
_HOSTKEY="${DNS_HOSTKEY}"
_IP=$(ip address show ${_DEVICE} | grep 'inet\b' | awk '{print $2}' | cut -d/ -f1)

date +%F
printf "Updating %s with %s\n" "$_DOMAIN" "$_IP"

wget -qO- --read-timeout=0.0 --waitretry=5 --tries=400 "http://freedns.afraid.org/dynamic/update.php?${_HOSTKEY}&address=${_IP}"

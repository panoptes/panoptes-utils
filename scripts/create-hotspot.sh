#!/bin/bash -e

HOTSPOT_NAME="PanoptesHotspot"
SSID_NAME="panoptes-net"

if [[ -z "${HOTSPOT_PASS}" ]]; then
    #statements
    read -r -s -p "Enter password for ${SSID_NAME}: " HOTSPOT_PASS
    echo
fi

echo "Creating ${HOTSPOT_NAME}"
echo "ssid: ${SSID_NAME}"

nmcli con add type wifi ifname wlp2s0 con-name "${HOTSPOT_NAME}" autoconnect yes ssid "${SSID_NAME}"
nmcli con modify "${HOTSPOT_NAME}" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
nmcli con modify "${HOTSPOT_NAME}" wifi-sec.key-mgmt wpa-psk
nmcli con modify "${HOTSPOT_NAME}" wifi-sec.psk "${HOTSPOT_PASS}"
nmcli con up "${HOTSPOT_NAME}"

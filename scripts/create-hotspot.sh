#!/bin/bash -ie

usage() {
  echo -n "##################################################
# Create a local hotspot for devices to connect to.
#
##################################################

 $ $(basename $0)

 This script currently will read the environment variables
 $HOTSPOT_NAME and $HOTSPOT_PASS. If $HOTSPOT_PASS is not provided
 the script will prompt for user input. If using as a script, pass
 the environment variables when calling, as shown in examples below.

 Examples:

    # Start hotspot with default options, ask for password.
    scripts/create-hotspot.sh

    # Start hotspot with default options, set password.
    HOTSPOT_PASS="s3cr3t_p4ss" scripts/create-hotspot.sh

    # Start hotspot with custom name, set password.
    HOTSPOT_NAME="WifiName" HOTSPOT_PASS="s3cr3t_p4ss" scripts/create-hotspot.sh

    # Start hotspot with custom ssid, ask for password.
    SSID_NAME="pan000-wifi" scripts/create-hotspot.sh
"
}

START=${1:-help}
if [ "${START}" = 'help' ] || [ "${START}" = '-h' ] || [ "${START}" = '--help' ]; then
    usage
    exit 1
fi

HOTSPOT_NAME="${HOTSPOT_NAME:-PanoptesHotspot}"
SSID_NAME="${SSID_NAME:-panoptes-net}"

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

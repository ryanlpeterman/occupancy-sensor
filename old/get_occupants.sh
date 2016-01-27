#!/bin/bash
# Script to return the names of people
# Currently connected to the wifi
# Note: Must run this script with sudo

# create associative array containing key value pairs
declare -A lookup_table
lookup_table[2c:be:08:9b:18:dc]="Dan"
lookup_table[e8:50:8b:68:73:48]="Ryan"
lookup_table[88:53:2e:a9:40:5c]="Dan"


mac_address_list="$(arp-scan -l | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}')"
occupants=""

# loop through every address on network and check with lookup_table
for address in $mac_address_list
do
	last=${lookup_table[$address]}
	occupants="$occupants ${NEWLINE} $last"
done

# alter html file with occupants
cat occupants.html | sed "s/<p>.*<\/p>/<p>$occupants<\/p>/g" > occupants.html

# upload text file to server for viewing
# TODO
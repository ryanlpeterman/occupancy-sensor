#!/bin/bash

# supervisor script to rerun the python script in the
# event that it fails. Logs the errors for the sake
# of debugging later

touch supervisor_log.txt
chown $USER supervisor_log.txt

while true
do
	# Note: python script will catch Ctrl-C enless we
	# write a sig handler
	(./get_occupants.py ; date) >> supervisor_log.txt
done
#!/bin/bash

# supervisor script to rerun the python script in the
# event that it fails. Logs the errors for the sake
# of debugging later

touch supervisor_log.txt
chown $USER supervisor_log.txt

while true
do
	# printf for readability
	(printf "\n\n" ; date; printf "\n") >> supervisor_log.txt
	
	# Note: python script will catch Ctrl-C enless we 
	# write a sig handler
	(python get_occupants.py) >> supervisor_log.txt 2>&1
done

## Initial Problem

I lost my keys the other day and couldn't get into my apartment

## Current Problem

UCLA IEEE, the electrical engineering club on campus, has a lab in which there are parts available and many projects being worked on all the time by its members. However, the lab is only open when officers are in the lab for assistance, which is just about 24/7. The only problem is that because as engineers we are night dwellers, the lab is not consistently open in the morning and therefore its hard to tell if its okay to come in. Therefore this script is being moded to tell if officers are in the lab.

## Solution

How the look-up works:

	1. Use arp-scan to ask router for mac addresses of devices connected to the router
	2. Find what the corresponding person associated with that mac address is

How Slack Bot works:

	whois - prints out a list of the people currently in the lab by look-up method

	time - outputs the number of seconds the person has been in the lab since the 
	script has been running (this is updated everytime the rpi scans)

	help - prints out all options

## Future Features

1. Introduce natural language processing into the model such that the users don't need to 
type in exact queries similar to how Siri works.
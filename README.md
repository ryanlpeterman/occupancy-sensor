# Occupancy Sensor
Python script that runs on a Raspberry Pi inside of student group, UCLA IEEE's, lab. Scans wifi network once a minute to keep a list of officers that are in the lab. If members of the club message the bot on slack, it responds with list of officers available in the lab. Also keeps track of length of visits in lab. Here is an example screenshot of the help command:

![Screenshot](http://rpeterman.me/app/static/petermanbot.png)

## Problem
UCLA IEEE, the electrical engineering club on campus, has a lab that is only open when officers are in the lab for assistance. The lab is not consistently open in the morning since most officers are night dwellers and therefore its hard to tell if the lab is open. Therefore this script runs a Slack bot that members can message to tell if the lab is open.

## Technical Overview
How the look-up works:

1. Use arp-scan to ask router for mac addresses of devices connected to the router
2. Check if any MAC addresses match list of officers

How Slack Bot works:

Constantly pings Slack Python API for incomming messages and responds accordingly. Every minute the script performs a scan of the network
to update its records so the Slack messages contain the most up to date information.

## Basic Commands
```
whois - prints out a list of the people currently in the lab by look-up method
time - outputs the number of seconds the person has been in the lab since the script has been running
help - prints out all options
```

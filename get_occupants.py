# Author: Ryan Peterman
#
# Lab Occupancy Sensor - to tell if officers are in the lab
# 		for the general members
# TODO: 1. Write out the data to google sheets when the script fails (DONE)
#		2. Poll less often (DONE)
#		3. Add Status setting abilty to bot (DONE)
#		4. treat officers differently based on status (DONE)
#		5. treat errors so the program never crashes 
#		6. Add lab general statistics (busiest time of day)
# 		7. Add easter eggs
#		8. Add weekly statistics

import subprocess
import os
import json
import time
from slackclient import SlackClient
import gspread
from oauth2client.client import SignedJwtAssertionCredentials

# Token from slack for bot API
bot_token = ""

# list of officers
officer_list = []

class Officer:
	name = ""
	mac_addr = ""
	status = 0 # 0 == online, 1 == tracked 
	minutes = 0
	is_in_lab = False
	miss_count = 0 # if this gets to 5 we remove them from the list
				   # if they are seen on the scan we set it to 0
	# default constructor
	def __init__(self):
		self.name = ""
		self.mac_addr = ""
		self.status = 0
		self.minutes = 0
		self.is_in_lab = False
		self.miss_count = 0

	# print officer function
	def print_officer(self):
		print "-------------------------"
		for m_data in [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self,a))]:
			print m_data + " = " + str(getattr(self, m_data))

def run_scan():
	""" Returns a string of all the recognized people according to the list
	of MAC addresses in mac_addresses.txt in the cwd
	This function also populates officer_list times every time
	NOTE: YOU MUST RUN THIS AS ROOT AND HAVE ETHERNET CONENCTION"""

	# store arp output (max 20 retries)
	for attempt in xrange(20):
		try:
			arp_output = subprocess.check_output(["arp-scan", "-l"])
		except Exception:
			# skip break and try again if error when running arp-scan
			continue

		# break if arp-scan worked
		break

	# didnt work even after 20 tries
	if not arp_output:
		print "Error: arp-scan did not work correctly even after 20 tries"

	# used to add to miss count
	scan_hit = False

	# find if any officer mac address is found in the arp_output
	for officer in officer_list:
		for line in arp_output.splitlines():
			if officer.mac_addr in line:
				# we know they are in the lab
				officer.is_in_lab = True
				officer.miss_count = 0
				scan_hit = True

				# print "Found : " + officer.name

				# use this for timing statistics
				officer.minutes += 1
	
		# if this officer not found in arp-scan				
		if not scan_hit:
			officer.miss_count += 1
		# officer was found and set scan_hit back to false for next officer
		else:
			scan_hit = False

		# they have been missing for more than 5 minutes
		if officer.miss_count > 5:
			officer.is_in_lab = False
	

def exit_handler():
	# init google sheets api
	json_key = json.load(open('occupancy sensor-52452f4f1313.json'))
	scope = ['https://spreadsheets.google.com/feeds']
	credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), scope)
	gc = gspread.authorize(credentials)
	wks = gc.open("Lab Occupancy Sensor").sheet1

	# write-out all the data to google sheets
	for officer in officer_list:

		# holds cell of officer name
		cell = wks.find(officer.name)

		# write out the officers information TODO: don't hardcode this
		wks.update_cell(cell.row, 3, officer.status)
		wks.update_cell(cell.row, 4, officer.minutes)

	print "Wrote out to google sheets!"
		
def get_officers():

	# build up newline delimited string of officers
	officer_str = ""

	# bool for when only anonymous people in lab
	is_someone_in = False

	# if officer is in lab add to str
	for officer in officer_list:
		if officer.is_in_lab: 
			if not officer.status:
				officer_str += officer.name + "\n"
			else:
				is_someone_in = True
	
	# no officers to explicitly add
	if not officer_str:
		# an anoymous person is in the lab
		if is_someone_in:
			return "Someone is in the lab (their status is anonymous at the moment)!"
		else:
			return "To my knowledge it appears no one is in the lab. Please try again to be sure!"
	
	return officer_str

def get_top_officers():

	top_list = sorted(officer_list, key=lambda x: x.minutes , reverse=True)

	top_str = ""

	for index in xrange(1, 11):
		cur_officer =  top_list[index - 1]
		hours = cur_officer.minutes / 60
		minutes = cur_officer.minutes % 60

		if cur_officer.status:
			name = "John Cena (Anonymous)"
		else:
			name = cur_officer.name

		top_str += str(index) + ". " + name + " with " + str(hours) +" hours and " + str(minutes) + " minutes."+ "\n"

	return top_str


def init_officers():
	""" Populates all the officer objects with their data
	from the google sheets API"""
	json_key = json.load(open('occupancy sensor-52452f4f1313.json'))
	scope = ['https://spreadsheets.google.com/feeds']
	credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), scope)
	gc = gspread.authorize(credentials)
	# open worksheet
	wks = gc.open("Lab Occupancy Sensor").sheet1
	num_officers = wks.row_count - 1

	# create list of officer objects
	for i in xrange(num_officers):
		officer_list.append(Officer())

	# populate officer objects with data from spreadsheet
	for col_label in ["Name", "Mac Address", "Status", "Minutes"]:
		
		cell = wks.find(col_label)
		values = wks.col_values(cell.col)

		for value, officer in zip(values[1:], officer_list):
			
			if col_label == "Name":
				officer.name = str(value)
			elif col_label == "Mac Address":
				# lower because this is how arp-scan outputs it
				officer.mac_addr = str(value.lower())
			elif col_label == "Status":
				officer.status = int(value)
			elif col_label == "Minutes":
				officer.minutes = int(value)

	# # To print officers
	# for i in officer_list:
	# 	i.print_officer()

def main():
	# init bot token and officers from google sheets
	sc = SlackClient(bot_token)

	for attempt in xrange(20):
		try:
			init_officers()
		except Exception:
			if attempt == 19:
				# exit without running finally block
				# since we were not able to load from gdocs.
				# we do not want to overwrite with null values during cleanup
				os._exit(2)
			continue
		break


	# TODO: Dynamically find the bot's id using users.list
	# could cause problem if this changes for some reason
	bot_id = "U0H7GEEJW"

	# counts up after every sleep(1)
	# so we can poll when counter reachs 60 or 1 min
	counter = 0

	# conenct to the bots feed
	if sc.rtm_connect():
		while True:
			# read events from peterbot's feed
			try:
				events = sc.rtm_read()
			# in the event that it throws an error just set it
			# to an empty list and continue
			except Exception, e:
				# print to add to log
				print e
				events = []
				
			# print events
			# print counter

			for e in events:
				message = ""
				user_input = ""

				# format the input text
				if e.get("text"):
					user_input = e.get("text").lower().strip()

				# if bot received text "whois"
				if user_input == "whois":
					# reply with list of officers
					message = get_officers()

				elif user_input == "status":
					try:
						user_dict = json.loads(sc.api_call("users.info", user=e.get("user")))
					except Exception: 
						message = "Failed to load users when looking up your name"
					
					# grabs real name of user
					name = user_dict["user"]["profile"]["real_name"]

					for officer in officer_list:

						if officer.name == name:
							officer.status = 1 - officer.status

							if not officer.status:
								message = "You are currently tracked/online."
							
							else:
								message = "You are currently not tracked/offline. You are not visible to others but are still gaining time in the lab statistics. \n"
				
				elif user_input == "top":
					message = get_top_officers()

				elif user_input == "version":
					message = "petermanbot v B0.1.2 - I'm Beta as Fuck right now."				

				elif user_input == "time":
					try:
						user_dict = json.loads(sc.api_call("users.info", user=e.get("user")))
					except Exception: 
						message = "Failed to load users when looking up your name"
					
					# grabs real name of user
					name = user_dict["user"]["profile"]["real_name"]

					for officer in officer_list:
	
						if officer.name == name:
							minutes = officer.minutes % 60
							hours = officer.minutes / 60

							message = "You currently have a total of " + str(hours) + " hours, " + str(minutes) + " minutes in the lab." 

					if not message:
						message = "You are not in the google sheet."

				elif e.get("text"):
					message = "Here are the following commands I support:\n \
					whois - prints people currently in the lab \n \
					time - prints how long you were in the lab this past week \n \
					status - toggle your status to online/offline \n \
					top - prints the top ten time totals \n \
					version - prints current version \n"

				# if there is a message to send, then send it
				# will not respond if received from bot message to prevent
				# looping conversation with itself
				if message != "" and e.get("user") != bot_id:
					chan_id = e.get("channel")
					sc.api_call("chat.postMessage", as_user="true:", channel=chan_id, text=message)

			# delay
			time.sleep(1)
			counter += 1

			# run script to build up statistics
			if counter >= 60:
				counter = 0
				# run quietly
				run_scan()
	else:
		print "Connection Failed: invalid token"

# runs main if run from the command line
if __name__ == '__main__':
	try:
		main()
	finally:
		exit_handler()

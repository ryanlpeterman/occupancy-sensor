# Author: Ryan Peterman
#
# Lab Occupancy Sensor - to tell if officers are in the lab
# 		for the general members
# TODO: 1. Write out the data to google sheets when the script fails
#		2. Poll less often
#		3. Add Status setting abilty to bot
#		4. treat officers differently based on ability
#		5. treat errors so the program never crashes

import subprocess
import json
import time
from slackclient import SlackClient
import gspread
from oauth2client.client import SignedJwtAssertionCredentials

# Token from slack for bot API
bot_token = 0

# list of officers
officer_list = []

class Officer:
	name = ""
	mac_addr = ""
	device = ""
	status = ""
	hours = 0
	minutes = 0
	seconds = 0

	# default constructor
	def __init__(self):
		self.name = ""
		self.mac_addr = ""
		self.device = ""
		self.status = ""
		self.hours = 0
		self.minutes = 0
		self.seconds = 0

	# print officer function
	def print_officer(self):
		print "-------------------------"
		for m_data in [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self,a))]:
			print m_data + " = " + getattr(self, m_data)

def get_officers():
	""" Returns a string of all the recognized people according to the list
	of MAC addresses in mac_addresses.txt in the cwd
	This function also populates seconds dict everytime it is ran
	NOTE: YOU MUST RUN THIS AS ROOT AND HAVE ETHERNET CONENCTION"""

	# store arp output
	try:
		arp_output = subprocess.check_output(["arp-scan", "-l"])
	except Exception:
		return "arp-scan Failed! Please try again!\n"

	# build up newline delimited string of officers
	officer_str = ""

	# find if any officer mac address is found in the arp_output
	for line in arp_output.splitlines():
		for officer in officer_list:
			if officer.mac_addr in line:
				officer_str += officer.name + "\n"

	if not officer_str:
		return "To my knowledge it appears no one is in the lab. Please try again to be sure!"
	
	return officer_str
	

def test_chat():
	# initialize handle
	sc = SlackClient(bot_token)

	# get json object corresponding to opening chat with Ryan Peterman
	im_dict = json.loads(sc.api_call("im.open", user="U0F8HE81Y"))
	chan_id = str(im_dict["channel"]["id"])
	greet_str = "Hello!\n Nice to meet you!\n"

	# call chat.postMessage to send message to the person
	print sc.api_call("chat.postMessage", as_user="true:", channel=chan_id, text=greet_str)

def init_officers():
	""" Populates all the officer objects with their data
	from the google sheets API"""
	json_key = json.load(open('occupancy sensor-52452f4f1313.json'))
	scope = ['https://spreadsheets.google.com/feeds']
	# print hello

	credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), scope)

	gc = gspread.authorize(credentials)

	wks = gc.open("Lab Occupancy Sensor").sheet1

	# create list of officer objects
	num_officers = wks.row_count - 1

	for i in xrange(num_officers):
		officer_list.append(Officer())

	# populate officer objects with data from spreadsheet
	for col_label in ["Name", "Mac Address", "Device", "Status", "Hours", "Minutes", "Seconds"]:
		
		cell = wks.find(col_label)
		values = wks.col_values(cell.col)

		for value, officer in zip(values[1:], officer_list):
			
			if col_label == "Name":
				officer.name = value
			elif col_label == "Mac Address":
				# lower because this is how arp-scan outputs it
				officer.mac_addr = value.lower()
			elif col_label == "Device":
				officer.device = value
			elif col_label == "Status":
				officer.status = value
			elif col_label == "Hours":
				officer.hours = value
			elif col_label == "Minutes":
				officer.minutes = value
			elif col_label == "Seconds":
				officer.seconds = value
	# To print officers
	for i in officer_list:
		i.print_officer()

def main():
	# init bot token and officers from google sheets
	sc = SlackClient(bot_token)
	init_officers()

	# TODO: Dynamically find the bot's id using users.list
	# could cause problem if this changes for some reason
	bot_id = "U0H7GEEJW"

	if sc.rtm_connect():
		while True:
			events = sc.rtm_read()
			print events

			for e in events:
				message = ""
				user_input = ""

				if e.get("text"):
					user_input = e.get("text").lower()

				# if bot received text "whois"
				if user_input == "whois":
					# reply with list of officers
					message = get_officers()
					
				elif user_input == "time":
					user_dict = json.loads(sc.api_call("users.info", user=e.get("user")))
					
					# grabs real name of user in homes of it corresponding
					# to the name in the mac_addresses.txt file
					name = user_dict["user"]["profile"]["real_name"]

					# TODO fix this to be a better implementation of timing
					# if seconds.get(name):						
					# 	# reply with seconds of the corresponding user 
					# 	message = "In the last week, you have been in the lab for: " + str(seconds.get(name)) + " seconds."
					# else:
					# 	message = "Either your slack real_name doesn't match with my archives or you haven't been in the lab"
						

				elif e.get("text"):
					message = "Here are the following commands I support:\n \
					whois - prints people currently in the lab \n \
					time - prints how long you were in the lab this past week \n \
					help - prints out all options \n"

				# if there is a message to send, then send it
				# will not respond if received from bot message to prevent
				# looping conversation with itself
				if message != "" and e.get("user") != bot_id:
					chan_id = e.get("channel")
					sc.api_call("chat.postMessage", as_user="true:", channel=chan_id, text=message)

			# TODO run arp-scan quietly every minute or so quietly for statistics

			# delay
			time.sleep(1)
	else:
		print "Connection Failed: invalid token"

# runs main if run from the command line
if __name__ == '__main__':
	main()

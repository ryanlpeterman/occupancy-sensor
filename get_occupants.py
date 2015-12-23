# Author: Ryan Peterman
#
# Lab Occupancy Sensor - to tell if officers are in the lab
# 		for the general members
import subprocess
import json
import time
from slackclient import SlackClient

# Token from slack for bot API
bot_token = "xoxb-17254490642-gks3VD9Yce9fB9D3A9Os4TsY"
# OAuth Token for general API use
general_token = "xoxp-15280620342-15289484066-17250544964-ba0c4fdb04"

# Dictionary to contain the seconds in the lab associated with each person
seconds = {}

def get_officers():
	""" Returns a string of all the recognized people according to the list
	of MAC addresses in mac_addresses.txt in the cwd
	This function also populates seconds dict everytime it is ran
	NOTE: YOU MUST RUN THIS AS ROOT AND HAVE ETHERNET CONENCTION"""

	# first open the file containing mac addresses
	with open("mac_addresses.txt") as file:
		mac_addr = file.read().splitlines()

	# list of tuples containing officer & mac addr
	officers = []
	officer_list = []
	num_in_lab = 0

	# step by 2
	for i in range(0, len(mac_addr), 2):
		officers.append([mac_addr[i], mac_addr[i + 1]])

	# store arp output
	arp_output = subprocess.check_output(["arp-scan", "-l"])

	for line in arp_output.splitlines():
		for officer in officers:

			# if officer mac address in line
			if officer[1] in line:
				num_in_lab+=1
				officer_list.append(["officer" + str(num_in_lab),officer[0]])
	
	# build up newline delimited string of officers
	officer_str = ""

	# for all officers in the lab
	for officer in officer_list:

		# if officer does not have any time in the lab
		if not seconds.get(officer[1]):
			seconds[officer[1]] = 1
		else:
			seconds[officer[1]] += 1

		officer_str += officer[1] + '\n'

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

def main():
	sc = SlackClient(bot_token)

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

					if seconds.get(name):						
						# reply with seconds of the corresponding user 
						message = "In the last week, you have been in the lab for: " + str(seconds.get(name)) + " seconds."
					else:
						message = "Either your slack real_name doesn't match with my archives or you haven't been in the lab"
						

				elif user_input == "help":
					message = "Here are the following commands I support:\n \
					whois - prints people currently in the lab \n \
					time - prints how long you were in the lab this past week \n \
					help - prints out all options \n"

				# the user typed something that was not understood
				elif e.get("text"):
					message = "Hi, I'm sorry I don't quite understand. \n Try typing 'help' to see all options."
				
				# if there is a message to send, then send it
				# will not respond if received from bot message to prevent
				# looping conversation with itself
				if message != "" and e.get("user") != bot_id:
					chan_id = e.get("channel")
					sc.api_call("chat.postMessage", as_user="true:", channel=chan_id, text=message)

			# bot is idling run arp-scan quietly to build up statistics
			get_officers()

			# delay
			time.sleep(1)
	else:
		print "Connection Failed: invalid token"

# runs main if run from the command line
if __name__ == '__main__':
	main()

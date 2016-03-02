from slackclient import SlackClient
import time

def main():
	# read the api key into variable
	with open('key.txt', 'r') as key_file:
		bot_token = key_file.read().replace('\n', '')

	# init bot token and officers from google sheets
	sc = SlackClient(bot_token)



	# TODO: Dynamically find the bot's id using users.list
	# could cause problem if this changes for some reason
	bot_id = "U0H7GEEJW"

	# counts up after every sleep(1)
	# so we can poll when counter reachs 60 or 1 min
	counter = 0

	# connect to the bots feed
	if sc.rtm_connect():
		while True:
			# read events from peterbot's feed
			try:
				events = sc.rtm_read()
			# in the event that it throws an error just set it
			# to an empty list and continue
			except Exception, e:
				# print to add to log
				sys.stderr.write(e)
				events = []

			for e in events:
				user_input = ""
				message = ""

				# format the input text
				if e.get("text"):
					user_input = e.get("text").lower().strip()
					
					# return a message based on the user's input
					message = "Currently Under Maintainence (Lab is Open as of 10:21am)"

				# if there is a message to send, then send it
				# will not respond if received from bot message to prevent
				# looping conversation with itself
				if message and e.get("user") != bot_id:
					chan_id = e.get("channel")
					sc.api_call("chat.postMessage", as_user="true:", channel=chan_id, text=message)

			# delay
			time.sleep(1)
			counter += 1

			# run script to build up statistics
			if counter >= 60:
				counter = 0


	else:
		sys.stderr.write("Connection Failed: invalid token")

# runs main if run from the command line
if __name__ == '__main__':
	main()

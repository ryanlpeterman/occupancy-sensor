""" Author: Ryan Peterman

Lab Occupancy Sensor - to tell if anyone is in the lab"""

import subprocess
import os
import json
import time
from slackclient import SlackClient
import csv
import datetime

# to track stderr for bugfix
import sys
import traceback
import re

# For use when writing out to correct spreadsheet
START_WEEK = datetime.datetime.now().isocalendar()[1]

# assign new stderr
sys.stderr = NewStderr()

# save reference to old stderr
oldstderr = sys.stderr

# list of officers
officer_list = []

def check_output(s):
    """checks stderr for network error to properly exit"""

    # error strings to look out for
    e_str1 = "socket is already closed"
    e_str2 = "[Errno 110] Connection timed out"
    e_str3 = "Connection is already closed."

    if any(re.match(regex, s) for regex in [e_str1, e_str2, e_str3]):

        oldstderr.write("Caught Network Error\n")

        # print stack trace
        for line in traceback.format_stack():
            oldstderr.write(line.strip() + '\n')

        # exit in a well defined way
        exit_handler()

    else:
        oldstderr.write(s)

class NewStderr:
    """ Wrapper for Stderr Object to check stream while running"""
    def __init__(self):
        pass

    def __getattr__(self, name):
        """called when attribute not defined for NewStderr is accessed"""
        # if newstderr write is called
        if name == 'write':
            return lambda s: check_output(s)

        return getattr(oldstderr, name)

    def __setattr__(self, name, value):
        return setattr(oldstderr, name, value)

class Officer:
    """ Class to hold the data for each person """
    name = ""
    mac_addr = ""
    status = 0 # 0 == online, 1 == tracked
    minutes = 0
    is_in_lab = False
    week_min = 0
    miss_count = 0 # if this gets to 5 we remove them from the list
                   # if they are seen on the scan we set it to 0

    def __init__(self):
        self.name = ""
        self.mac_addr = ""
        self.status = 0
        self.minutes = 0
        self.week_min = 0
        self.is_in_lab = False
        self.miss_count = 0

    def print_officer(self):
        """ print officer function for debugging"""
        print "-------------------------"
        for m_data in [a for a in dir(self)
            if not a.startswith('__') and not callable(getattr(self, a))]:

            print m_data + " = " + str(getattr(self, m_data))

def run_scan():
    """ populates officer list with mac addresses seen in arp-scan,
    returns number of matches """

    # store arp output (max 20 retries)
    for _ in xrange(20):
        try:
            arp_output = subprocess.check_output(["arp-scan", "-l"])
        except Exception:
            # skip break and try again if error when running arp-scan
            continue

        # break if arp-scan worked
        break

    # didnt work even after 20 tries
    if not arp_output:
        sys.stderr.write("Error: arp-scan failed 20 times in a row")

    # number of hits
    num_hits = 0
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

        # if this officer not found in arp-scan
        if not scan_hit:
            officer.miss_count += 1

        # officer was found and set scan_hit back to false for next officer
        else:
            scan_hit = False

        # they have been missing for more than 5 minutes
        if officer.miss_count > 5:
            officer.is_in_lab = False

        # if they are in the lab then add a minute
        if officer.is_in_lab:
            officer.minutes += 1
            officer.week_min += 1
            num_hits += 1

    return num_hits

def get_occupants():
    """ Checks current list of officers to see who is in the lab """
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
            return "People are in the lab."
        else:
            return ("I Haven't seen anyone in the lab."
            "Please try again to be sure!")

    return officer_str

def get_top_officers(all_time):
    """ Returns a string of the top 10 total times among the officers """

    if all_time:
        top_list = sorted(officer_list, key=lambda x: x.minutes, reverse=True)
        top_str = "Top of all time: \n"
    else:
        top_list = sorted(officer_list, key=lambda x: x.week_min, reverse=True)
        top_str = "This Week's Top:\n"

    for index in xrange(1, 11):
        cur_officer = top_list[index - 1]

        if all_time:
            hours = cur_officer.minutes / 60
            minutes = cur_officer.minutes % 60
        else:
            hours = cur_officer.week_min / 60
            minutes = cur_officer.week_min % 60

        if cur_officer.status:
            name = "John Cena (Anonymous)"
        else:
            name = cur_officer.name

        top_str += (str(index) + ". " + name + " with " + str(hours) +
            " hours and " + str(minutes) + " minutes."+ "\n")

    return top_str

def init_officers():
    """ Populates all the officer objects with their data from csv"""

    file_handler = open('total_hours.csv', 'rb')
    reader = csv.reader(file_handler)
    # skip over header_list
    header_list = reader.next()

    for row in reader:

        # create officer object
        officer = Officer()

        for col_label, i  in zip(header_list, range(len(header_list))):
            if col_label == "Name":
                officer.name = str(row[i])
            elif col_label == "Mac Address":
                # lower because this is how arp-scan outputs it
                officer.mac_addr = str(row[i].lower())
            elif col_label == "Status":
                officer.status = int(row[i])
            elif col_label == "Minutes":
                officer.minutes = int(row[i])

        # add officer to officer list
        officer_list.append(officer)

    file_handler.close()

    # gets int corresponding to this week
    this_week = datetime.datetime.now().isocalendar()[1]

    # path to folder containing weekly records
    week_path = "weekly/" + str(this_week)

    # already have record for this week load it to weekly
    if os.path.isfile(week_path):
        file_handler = open(week_path, 'rb')
        reader = csv.reader(file_handler)
        # check every row of weekly csv
        for row in reader:
            # check all officers against current row
            for officer in officer_list:
                # if first col matches officer then set its weekly minutes
                if row[0] == officer.name:
                    officer.week_min = int(row[1])

    # file does not exist yet we create it and write all 0's to it
    else:
        file_handler = open(week_path, 'w')
        writer = csv.writer(file_handler)

        # write 0's out to weekly csv since its a new file
        for officer in officer_list:
            row = [officer.name, 0]
            writer.writerow(row)

        file_handler.close()

    for officer in officer_list:
        officer.print_officer()

def exit_handler():
    """ Writes out to the csv and exits """

    # open file
    file_handler = open('total_hours.csv', 'w')
    writer = csv.writer(file_handler)

    # Write out header
    header_list = ["Name", "Mac Address", "Status", "Minutes"]
    writer.writerow(header_list)

    # write out every officer as a row in csv
    for officer in officer_list:
        row = [officer.name, officer.mac_addr, officer.status, officer.minutes]
        writer.writerow(row)

    file_handler.close()

    # path to folder containing weekly records
    week_path = "weekly/" + str(START_WEEK)

    file_handler = open(week_path, 'w')
    writer = csv.writer(file_handler)

    # write 0's out to weekly csv since its a new file
    for officer in officer_list:
        row = [officer.name, officer.week_min]
        writer.writerow(row)

    file_handler.close()

    # exit without calling anything else
    os._exit(0)

def handle_input(user_input, event, slack_obj):
    """ returns the message that a user would receive based on their input """

    message = ""

    # if bot received text "whois"
    if user_input == "whois":
        # reply with list of officers
        message = get_occupants()

    elif user_input == "kill":
        try:
            user_dict = json.loads(slack_obj.api_call("users.info",
                user=event.get("user")))

        except Exception:
            message = "Failed to load users when looking up your name."

        # if the user's id is Ryan's
        if user_dict["user"]["id"] == "U0F8HE81Y":
            # print for debugging log
            print "Received kill command from slack"

            # send message to Ryan to let him know we are restarting the script
            message = "Killed it"
            chan_id = event.get("channel")
            slack_obj.api_call("chat.postMessage", as_user="true:",
                channel=chan_id, text=message)

            # exit script
            exit_handler()
        else:
            message = "Nice try, you don't have the power to kill."

    elif user_input == "status":
        try:
            user_dict = json.loads(slack_obj.api_call("users.info",
                user=event.get("user")))
        except Exception:
            message = "Failed to load users when looking up your name."

        # grabs real name of user
        name = user_dict["user"]["profile"]["real_name"]

        for officer in officer_list:
            if officer.name == name:
                officer.status = 1 - officer.status

                if not officer.status:
                    message = "You are currently tracked/online."

                else:
                    message = ("You are currently not tracked/offline. You are "
                        "not visible to others but are still gaining time in "
                        "the lab statistics. \n")

    elif user_input == "weektop":
        message = get_top_officers(False)

    elif user_input == "alltop":
        message = get_top_officers(True)

    elif user_input == "version":
        message = "petermanbot v B1.0.0 - Slimmed down and clean."

    elif "time" in user_input:
        try:
            user_dict = json.loads(slack_obj.api_call("users.info",
                user=event.get("user")))
        except Exception:
            message = "Failed to load users when looking up your name"

        # grabs real name of user
        name = user_dict["user"]["profile"]["real_name"]

        for officer in officer_list:
            if officer.name == name:

                if user_input == "alltime":
                    minutes = officer.minutes % 60
                    hours = officer.minutes / 60
                    message = ("You currently have a total of " + str(hours) +
                        " hours, " + str(minutes) +
                        " minutes in the lab for all time.")

                elif user_input == "weektime":
                    minutes = officer.week_min % 60
                    hours = officer.week_min / 60
                    message = ("You currently have a total of " + str(hours) +
                        " hours, " + str(minutes) +
                        " minutes in the lab for this week.")


        if not message:
            message = ("You are not in the google sheet or your"
                "mistyped \"alltime\" or \"weektime\"")

    else:
        message = ("Here are the following commands I support:\n"
        "whois - prints people currently in the lab \n"
        "weektime - prints how long you were in the lab this past week \n"
        "alltime - prints how long you were in lab for all time \n"
        "status - toggle your status to online/offline \n"
        "weektop - prints the top ten time totals for the week \n"
        "alltop - prints the top ten time totals for all time \n"
        "version - prints current version \n")

    return message

def main():
    """ main event loop for slack client polling"""

    # read the api key into variable
    with open('key.txt', 'r') as key_file:
        bot_token = key_file.read().replace('\n', '')

    # init bot token and officers from google sheets
    slack_obj = SlackClient(bot_token)

    init_officers()

    # the id of the bot
    bot_id = "U0H7GEEJW"

    # counts up after every sleep(1)
    # so we can poll when counter reachs 60 or 1 min
    counter = 0

    # connect to the bots feed
    if slack_obj.rtm_connect():
        while True:
            # read event_list from peterbot's feed
            try:
                event_list = slack_obj.rtm_read()
            # in the event that it throws an error just set it
            # to an empty list and continue
            except Exception, excep:
                # print to add to log
                sys.stderr.write(excep)
                event_list = []

            for event in event_list:
                user_input = ""
                message = ""

                # format the input text
                if event.get("text"):
                    user_input = event.get("text").lower().strip()

                    # return a message based on the user's input
                    message = handle_input(user_input, event, slack_obj)

                # if there is a message to send, then send it
                # will not respond if received from bot message to prevent
                # looping conversation with itself
                if message and event.get("user") != bot_id:
                    chan_id = event.get("channel")
                    slack_obj.api_call("chat.postMessage", as_user="true:",
                        channel=chan_id, text=message)

            # delay
            time.sleep(1)
            counter += 1

            # every minute
            if counter >= 60:
                counter = 0

                # run quietly
                num_hits = run_scan()

                # check time for every 10 minutes
                curr_time = time.localtime()
                if curr_time.tm_min % 10 == 0:

                    row = (str(curr_time.tm_hour) + ":" + str(curr_time.tm_min)
                        + "," + str(num_hits) + "\n")

                    with open("daily_activity/" + str(curr_time.tm_mday) +
                        ".csv", 'a') as file_handler:

                        file_handler.write(row)

                # new day
                if curr_time.tm_hour == 0:
                    # write out the hours to weekly total once a day
                    exit_handler()


    else:
        sys.stderr.write("Connection Failed: invalid token")

# runs main if run from the command line
if __name__ == '__main__':
    try:
        main()
    finally:
        exit_handler()

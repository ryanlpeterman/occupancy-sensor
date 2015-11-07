# Author: Ryan Peterman
#
# Lab Occupancy Sensor - to tell if officers are in the lab
# 		for the general members
import subprocess
import urllib

def main():

	# first open the file containing mac addresses
	with open("mac_addresses.txt") as file:
		mac_addr = file.read().splitlines()

	# list of tuples containing officer & mac addr
	officers = []
	officers_in_lab = []
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
				officers_in_lab.append(["officer" + str(num_in_lab),officer[0]])

	print officers_in_lab
	
	url = 'http://ryanlpeterman.bol.ucla.edu/script.php/'
	data = urllib.urlencode(dict(officers_in_lab))	
	content = urllib.urlopen(url=url, data=data)

if __name__ == '__main__':
	main()
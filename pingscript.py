# intended to be run as cronjob on a Linux system. Will not work on other OS's
# logs result of 5 pings to file specified by "dest", to track network health.
# Prepends date & time, and appends "VPN" if VPN was running
# automatically archives and renames old files.
import subprocess
from datetime import datetime

# _________________CHANGE AS NEEDED___________________
dest = "/home/philip/Desktop/pingtimes"
archive_folder = '/home/philip/PRIO/pingtimes_archive'
pingcount = 5

# 2020-02-01 . Should NOT specify clocktime (i.e. h/m/s).
date_format = '%Y-%m-%d'

# Note: this will only be written on the 1st of the month, at the top of the logfile.
file_abstract = f"CRONJOB OUTPUT. Each line is the result of {pingcount} pings. NOTE THAT VPN adds about 27 ms\n\n"
# ________________CHANGE ABOVE AS NEEDED______________


cmd = f"ping -c{pingcount} google.com"
MyOut = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8')
stdout, stderr = MyOut.communicate()

# if run from cmd line, output any error. Useful when debugging.
if stderr:
	print(stderr)

if stdout:
	now = datetime.now()

	# we only log the mdev line, with date prepended.
	stdout = stdout.split('\n')[-2]
	stdout = datetime.strftime(now, "%Y-%m-%d %H:%M:%S: ") + stdout

# in order to minimize file reads, we read only the leading lines once
# then give this info to all functions requiring it
# this is used when determining whether to backup target file, at "dest".
number_of_leading_lines = 10


def file_exists(dest):
	import os
	return os.path.exists(dest)


def return_leading_lines(dest):
	# cache leading lines
	# islice may perform better than a typical read for large files
	# as an example, my file reaches around 8000 lines by the end of the month
	from itertools import islice
	with open(dest) as f:
		lines = list(islice(f, number_of_leading_lines))
	return lines


def requires_archiving(does_file_exist, leading_lines, date_format):
	# returns True if following conditions are met:
	# today is 1st of the new month
	# AND there is a file on desktop
	# AND it contains old entries
	# else returns False
	if not does_file_exist:
		return False

	now = datetime.now()
	if now.day == 1:
		if does_file_exist:
			# determine if there are old entries in leading lines
			for line in leading_lines:
				try:
					# expects a date in format specified by date_format
					# separated from time or ping output by a space
					found_date = datetime.strptime(line.split()[0], date_format)
				except (IndexError, ValueError):
					# either list index out of range for lines ~1-2 (because those lines == "\n")
					# or ValueError because date_format doesn't match a line (like "\n")
					continue
				except Exception as e:
					# this is unexpected. Should not happen. So far has not happened.
					# Optionally, write a log to desktop to clarify error
					# Here we just print so any users terminal-testing the program know
					print("ERROR: unexpected exception\n", e)
					continue
				if found_date:
					if found_date.month != now.month:
						# there's an old entry, so we archive the file
						return True
	return False


def archive_file(source, archive_folder):
	import os
	from datetime import timedelta
	# convert now.month to previous month. Otherwise, we name archived files according to current month
	now = datetime.now().replace(day=1) - timedelta(days=1)
	backup_basename = 'pingtimes-' + now.strftime('%b').upper() + now.strftime('%Y')
	final = os.path.join(archive_folder, backup_basename)
	os.rename(source, final)


def determine_VPN_active():
	# without leading '/sbin/', loc_stdout can read...
	# RETURNED TRUE for input: /bin/sh: 1: ifconfig: not found
	loc_cmd = '/sbin/ifconfig tun0'
	loc_out = subprocess.Popen(loc_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8')
	loc_stdout, loc_stderr = loc_out.communicate()
	# if VPN is inactive, following line should be the result
	# tun0: error fetching interface information: Device not found
	if 'error fetching interface information' in loc_stdout:
		return False
	return True

def write(dest, VPN_active, prepend_abstract=False):
	# takes string destination to write to, bool VPN_active, bool prepend_abstract
	# writes to destination, appending VPN if True, leading with abstract if True
	if prepend_abstract:
		# create file, prepend abstract, write pingline + " VPN" if appropriate
		line_to_write = file_abstract + stdout
	else:
		line_to_write = stdout

	if VPN_active:
		# print('WRITE appending \'VPN\'')
		line_to_write += ' VPN'

	# the lines below can be returned from ifconfig when computer is resuming from standby
	# and has not yet reconnected to the internet
	# these were real results, 1.06ms apart
	# despite the crontab entry stipulating to run only every 2 mins
	# presumably 1st and 2nd ping attempts
	'''
	2020-02-11 19:25:05: ping: google.com: Name or service not known VPN
	2020-02-11 19:26:11: ping: google.com: Name or service not known VPN
	'''
	if 'Name or service not known' in line_to_write:
		return

	with open(dest, 'a+') as f:
		f.write(line_to_write + '\n')..


def main():
	f_exists = file_exists(dest)
	if f_exists:
		# we want to append ping results [with "VPN" if appropriate]
		write_abstract = False
		leading_lines = return_leading_lines(dest)
		req_archiving = requires_archiving(file_exists, leading_lines, date_format)
	else:
		# we want to create file, write abstract, add ping results [with "VPN" if appropriate]
		write_abstract = True
		req_archiving = False

	if req_archiving:
		archive_file(source=dest, archive_folder=archive_folder)
		# no need to delete old file - it's already been moved by archive_file(...)
		# we need to write the abstract because we're writing to a fresh file
		# - our archiving removed the old file
		write_abstract = True

	VPN_active = determine_VPN_active()
	write(dest, VPN_active, write_abstract)


if __name__ == '__main__':
	main()

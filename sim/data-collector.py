#!/usr/bin/env python
#
from data_classes import *
import os
import httplib
import re
import time
import sys
from subprocess import *
from optparse import OptionParser

parser = OptionParser ()
parser.add_option ("-v", "--verbose", action="store_true", default=False, 
                  help="Show verbose output (default == false).")
parser.add_option ("-u", "--use_old_commits", action="store_true", default=False,
                  help="Do not get commit info from Internet (default == false).")
parser.add_option ("-e", "--efficient", action="store_true", default=False,
                  help="Get commit data from Internet only if needed (default == false).")
parser.add_option ("-r", "--resume", action="store_true", default=False,
                  help="When data is already stored on disk, we can resume (default == false).")

(options, args) = parser.parse_args ()
verbose = options.verbose
use_old_commits = options.use_old_commits
effic = options.efficient
resume = options.resume

# Globally utilized regexes
ebuild_ext = re.compile ("\.ebuild$")
bugbump = re.compile ("\-r\d+")
dash_nums = re.compile ("(.*\-)(\d+)(\.py)$")
xmlherd = re.compile ('\s*<herd>(.+)</herd>.*')
sinxmlherd = re.compile ('\s*<herd>\s*$')
xmlmaint = re.compile ('\s*<maintainer>\s*$')
fullxmlmaint = re.compile ('\s*<maintainer>\s*<email>\s*(.+)@gentoo.org\s*</email>\s*</maintainer>\s*')
maint_email = re.compile ('\s*<email>(.+)@gentoo.org>?<?</email>.*')
strip_spaces = re.compile ('\s*(\w+)\s*')

# Global vars
dest_dir = "/tmp/3800"
sys.path.append (dest_dir)
cvs_dest = "/cvs"
bugs_dest = "/bugs"
repos = []
split = 10000
commits_seen = 0

# Other globalvars and initilizers
commit_ds_data = dest_dir + "/commit_ds_data-1.py"
cur_dir = os.getcwd ()
commit_data_file = ""
herd_file = dest_dir + "/herds.py"

def write_timestamp (file):
	if (verbose):
		print "Writing timestamp"
	open (file, "w")
	file.write (str (int (time.time ())))
	file.close ()

def update_repos (repos, dest, cvs_cmd):
	os.system ("mkdir -p " + dest)
	for repo in repos:
		ts_loc = dest + "/" + repo + "/" + ".synced"
		cmd = "cd " + dest + " && " + cvs_cmd

		if os.path.exists (dest + "/" + repo):
			ts = -1
			if os.path.exists (ts_loc):
				ts_file = open (ts_loc, "r")
				ts = int (ts_file.read ())
				ts_file.close ()
			now = int (time.time ())
			# Lets update; our repository is too old
			if (verbose):
				print "Repository Old. Updating..."
			if (now - 60 * 60 * 24) < ts or ts == -1: 
				os.system (cmd + " update " + repo)
				write_timestamp (ts_loc)
			#else: do nothing
		else:
			os.system (cmd + " co " + repo)
			write_timestamp (ts_loc)


def get_last_bug_num (web_page):
	web_page_lines = []
	append = 0
	line = ""
	for char in web_page:
		if (char == "<"):
			append = 1
		if (char == ">"):
			append = 0
			web_page_lines.append (line + char)
			line = ""
		if append:
			line += char
		else:
			continue

	aBug = re.compile ('\<a href=\"show_bug.cgi\?id=(\d+)\"\>')
	
	for line in web_page_lines.reverse ():
		mat = aBug.match (line)

		if (mat):
			# Returns the first one found, which is the last bug.
			return mat.group (1)

def parse_bug_report (unparsed_report):
	parsed_report = ""

	web_page_lines = []
	append_html = 0
	append_text = 0
	line = ""

	for char in unparsed_report:
		if (char == "<"):
			append_html = 1
		if (char == ">"):
			append_html = 0
			web_page_lines.append (line + char)
			line = ""
		if (append_html == 0 and append_text == 0 and char.isalpha ()):
			append_text = 1
		if (append_html == 1 and append_text == 1):
			append_text = 0
			web_page_lines.append (line + char)
			line = ""

		if (append_html or append_text):
			line += char

	resolution = re.compile ('\<a href=\"page.cgi\?id=fields\.html\#resolution\"\>')
	resolution_dup = re.compile ('\<td\>DUPLICATE')
	resolution_closed = re.compile ('\<td\>')

	priority = re.compile ('\<select name=\"priority\" id=\"priority\"\>')
	priority_val = re.compile ('\<option value=\"P(\d)\" selected\>')
	pri = 0

	severity = re.compile ('\<select name=\"bug_severity\" id=\"bug_severity\"\>')
	severity_val = re.compile ('\<option value=\"(\w+)\" selected\>')
	sev = 0

	for line in web_page_lines:
		# Extract Priorities
		if (priority.match (line)):
			pri = 1
		if (priority_val.match (line)):
			parsed_report += "priority = " + priority_val.match (line).group (1)
			pri = 0
		if (pri == 1):
			continue

		if (severity.match (line)):
			sev = 1
		if (severity_val.match (line)):
			parsed_report += "severity = " + severity_val.match (line).group (1)
			sev = 0
		if (sev == 1):
			continue
		

def update_bugzilla_data (dest):
	# First find the total number of bugs
	lat_bugs_url = 'http://bugs.gentoo.org/buglist.cgi?query_format=advanced&chfieldfrom=2008-01-21+16:02&chfieldto=2008-01-22%2004:02&chfield=%5BBug+creation%5D&order=bugs.bug_id'
	bugs_conn = httplib.HTTPConnection ("bugs.gentoo.org")
	bugs_conn.request ("GET", lat_bugs_url)
	resp = bugs_conn.getresponse ()
	if (resp.status != 200):
		print "Error: Could not download list of latest bugs. Make sure " \
		      "you have a connection to bugs.gentoo.org"
		sys.exit (-1)
		
	latest_bugs_pg = resp.read ()

	bugs_conn.close ()

	last_bug_num = get_last_bug_num (latest_bugs_pg)

	# Determine the last bug we have records of
	dirs = os.listdir (dest)
	
	our_last_bug_num = max (dirs)
		

	# Go through every bug that we do not have records 
	# for and download it
	i = our_last_bug_num or 1
	while (i <= last_bug_num):
		bug_url = "/show_bug.cgi?id=" + i
		bugs_conn.request ("GET", bug_url)
		resp = bugs_conn.getresponse ()
		if (resp.status != 200):
			print "Warning: Could not download page for bug " + i
		
		report = resp.read ()

		data = parse_bug_report (report)
	
		os.mkdir (dest + "/" + i)

		record = open (dest + "/" + i + "/" + i + ".rep", "w")
		record.write (data)
		record.close ()

def get_loc (file):
	file_h = open (file, "r")

	return len (file_h.read ().split ("\n"))

def extract_package_data (dest, repo):
	# Go through each category and each package in 
	# gentoo-x86.
	if (verbose):
		print "Starting to extract package data."
	rep = "/" + repo + "/"
	
	package_objects = {}

	categs = os.listdir (dest + rep)
	for cat in categs:
		if (verbose):
			print "Extracting from " + rep + cat
		if cat == "CVS" or not os.path.isdir (dest + rep + cat):
			continue
		packages = os.listdir (dest + rep + cat)
		for pack in packages:
			full = cat + "/" + pack
			if pack == "CVS" or not os.path.isdir (dest + rep + full):
				continue

			files = os.listdir (dest + rep + full)
			
			total_loc = 0
			maintainer = "null"
			for file in files:
				lfile = dest + rep + full + "/" + file
				if ebuild_ext.match (file):
					total_loc += get_loc (lfile)
				if (file == "metadata.xml"):
					#if (verbose):
					#	print "About to extract from " + lfile
					meta = open (lfile, "r")
					str_meta = meta.readlines ()
					meta.close ()
					herd = "null"
					maint_next = 0
					herd_next = 0
					for line in str_meta:
						if (sinxmlherd.match (line)):
							herd_next = 1
							continue
						if (herd_next == 1 and strip_spaces.match (line)):
							herd = strip_spaces.match (line).group (1)
							herd_next = 0
							break
						if (xmlherd.match (line)):
							herd = xmlherd.match (line).group (1)
							break
						if (xmlmaint.match (line)):
							maint_next = 1
							continue
						if (fullxmlmaint.match (line)):
							maintainer = fullxmlmaint.match (line).group (1)
							continue
						if (maint_next == 1 and maint_email.match (line)):
							maint_next = 0
							#print "Warning: Package (" + lfile + \
							#      ") is maintained by herd even though individual is listed."
							#continue
							maintainer = maint_email.match (line).group (1)

					if (maintainer == "null" and herd == "no-herd"):
						maintainer = "maintainer-wanted"

					if (maintainer == "null" and herd == "null"):
						print "Error: Ownership of package unknown"
						sys.exit (-3)
						
					if (maintainer == "null"):
						maintainer = "herd:" + herd

			if (verbose):
				print "Maintainer of " + full + " is " + maintainer
			package_objects.setdefault (full, PackageData (full, maintainer))
			package_objects[full].ebuild_loc = total_loc

	return package_objects
	
def get_commit_type (package, ebuild, dest):
	chlog = open (dest + package + "/ChangeLog", r)
	chlog_lines = chlog.readlines ()
	chlog.close ()

	base = sub ("\.ebuild$", "", ebuild)

	event = re.compile ("^*(" + base + ")")
	bugbump = re.compile ("\-r\d+")
	for line in chlog_lines:
		if (event.match (line)):
			if (bugbump. match (line)):
				return "bugbump"
			else:
				return "verbump"

def fix_bad_chars (str):
	new_str = ""

	for char in str:
		if (char == "+"):
			new_str += "\\" + char
		else:
			new_str += char
	return new_str

def init_commit_data_write ():
	commit_data_write = open (commit_ds_data, "w")

	commit_data_write.write ("all_commits = []\n\n")

	return commit_data_write

def finish_commit_data_write ():
	commit_data_file.close ()

def extract_commits_for_pack (log, dest):
	global commits_seen
	global commit_ds_data
	global commit_data_file

	if (verbose):
		print "Starting to extract commits for packages from " + dest

	rev = re.compile ("^revision \d+\.\d+")
	file = re.compile ("RCS file: \/.+\/(.+?/.+?)/(.+),v$")
	date = re.compile (".*date: (\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2}) ([\+\-]\d{4});.*")
	author = re.compile (".*author: (.+?);.*")
	commitid = re.compile (".*commitid: (.+?);.*")
	lines_changed = re.compile (".*lines: \+(\d+) \-(\d+);.*")
	commit_end = re.compile ("\-{28}")

	f = ""
	package = ""
	timestamp = ""
	dev = ""
	id = ""
	added = 0
	subtracted = 0
	rev_existed = False
	for line in log:
		if (rev.match (line)):
			rev_existed = True
		if (file.match (line)):
			package = file.match (line).group (1)
			f = package + "/" + file.match (line).group (2)
		if (date.match (line)):
			mat = date.match (line)
			ts = int (mat.group (1) + mat.group (2) + mat.group (3) + 
			          mat.group (4) + mat.group (5) + mat.group (6))
			timestamp = str (ts)
			if (len (timestamp) != 14):
				print "Error: Timetamp supposed to be 14 chars long: " + timestamp 
				sys.exit (-2)
		if (author.match (line)):
			dev = author.match (line).group (1)
		if (commitid.match (line)):
			id = commitid.match (line).group (1)
		if (lines_changed.match (line)):
			mat = lines_changed.match (line)
			added = int (mat.group (1))
			subtracted = int (mat.group (2))
		
		if (commit_end.match (line) and rev_existed):
			commit_data_file.write ("commit = " \
						 + "CommitData (\"" + package + "\",\"" \
						 + dev + "\",\"" + str (timestamp) + "\",\"" + f \
						 + "\",\"" + str (id) + "\")\n")
			commit_data_file.write ("commit.linesAdded = " + str (added) + "\n")
			commit_data_file.write ("commit.linesRemoved = " + str (subtracted) + "\n")
			commit_data_file.write ("commit.linesChanged = " + str (added + subtracted) + 
			                   "\n")
			if (ebuild_ext.match (f)):
				type = get_commit_type (package, f, dest)
				commit_data_file.write ("commit.typeOfCommit = \"" + type + "\"\n")
			else:
				commit_data_file.write ("commit.typeOfCommit = \"other\"\n")
			
			commit_data_file.write ("all_commits.append (commit)\n\n")
			# Clear the placeholder variable.
			rev_existed = False
			commits_seen += 1
			if (commits_seen == split):
				finish_commit_data_write ()
				# Switch to new writing location.
				if (not dash_nums.match (commit_ds_data)):
					print "Error: Something is wrong: " + commit_ds_data
					sys.exit (0)
				mat = dash_nums.match (commit_ds_data)
				beg = mat.group (1)
				cur = int (mat.group (2))
				end = mat.group (3)
				cur += 1
				commit_ds_data = beg + str (cur) + end
				if (verbose):
					print "New Commit DS Data file: " + commit_ds_data
				commit_data_file = init_commit_data_write ()
				commits_seen = 0

def extract_commit_and_dev_data (dest, repos):
	if (verbose):
		print "Starting to extract commit and developer data."

	for repo in repos:
		dot = re.compile ("^\.")
		rep = "/" + repo + "/"

		length = 0
		categs = os.listdir (dest + rep)
	
		for cat in categs:
			if (verbose):
				print "Gathering data from " + rep + cat
			if (cat == "skel.ebuild" or 
			    cat == "header.txt" or 
			    cat == "log_dump" or 
			    cat == "skel.ChangeLog" or 
			    cat == "skel.metadata.xml" or 
			    cat == "CVS" or 
			    cat == "files" or 
			    cat == "glep" or 
			    cat == "incoming" or 
			    dot.match (cat)):
				continue
				
			log_path = dest + rep + cat + "/log_dump"
			if (not use_old_commits):
				if (verbose):
					print "Gathering commit data from cvs..."

				if (effic and os.path.os.access(log_path, os.F_OK)):
					if (verbose): 
						print "Skipping because log_dump exists: " + log_path
				else:
					pak = dest + rep + cat
					cmd = "cd " + pak + " && cvs log > " + log_path
					cvs_log = -1
					if (verbose):
						cvs_log = Popen (cmd, shell=True, stdout=None, 
						                 stderr=STDOUT)
					else:
						cvs_log = Popen (cmd, shell=True, stdout=PIPE,
								 stderr=STDOUT)
					if (verbose):
						print cmd
	
					result = cvs_log.wait ()
					if (result != 0):
						print "Error: Failed to extract cvs log information " \
						      + "for " + cat
						sys.exit (-1)
					
					if (os.path.getsize (log_path) == 0):
						print "Error: nothing in commit log in " + cat
						sys.exit (-1)

			if (os.path.getsize (log_path) == 0):
				print "Warning: nothing in commit log in " + cat + " in " + log_path
				continue

			log_dump = open (log_path, "r")
			log_txt = log_dump.readlines ()
			log_dump.close ()

			if (verbose):
				print "Finished gathering commit data, going to extract it."
			extract_commits_for_pack (log_txt, dest + rep)

def extract_bug_data (dest, commmits):
	all_bugs = []

	# Date format: yyyy-mm-dd

	# We need to replace / with %2F for correct urls

	url = "http://bugs.gentoo.org/buglist.cgi?query_format=advanced&" + \
	      "short_desc_type=allwordssubstr&short_desc=" + package + "&" + \
	      "long_desc_type=substring&long_desc=&" + \
	      "bug_file_loc_type=allwordssubstr&bug_file_loc=&" + \
	      "status_whiteboard_type=allwordssubstr&status_whiteboard=&" + \
	      "keywords_type=allwords&keywords=&bug_status=UNCONFIRMED&" + \
	      "bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&" + \
	      "bug_status=RESOLVED&bug_status=VERIFIED&bug_status=CLOSED&" + \
	      "emailassigned_to1=1&emailtype1=substring&email1=&emailassigned_to2=1&" + \
	      "emailreporter2=1&emailcc2=1&emailtype2=substring&email2=&" + \
	      "bugidtype=include&bug_id=&votes=&chfieldfrom=" + start_date + "&" + \
	      "chfieldto=" + end_date + "&chfield=%5BBug+creation%5D&chfieldvalue=&" + \
	      "cmdtype=doit&order=Reuse+same+sort+as+last+time&field0-0-0=noop&" + \
	      "type0-0-0=noop&value0-0-0="

	# return all_bugs

def read_herd_data (dest_file):
	handle = open (dest_file, "r")
        all = handle.readlines ()
        handle.close ()
        full_str = ""
        for line in all:
                full_str += line
        exec (full_str)
        return herd_hash

def get_herd_data (dest_file):
	if (resume and os.path.isfile (dest_file)):
		return read_herd_data (dest_file)

	print "Downloading herds file..."
	herd_conn = httplib.HTTPConnection ("sources.gentoo.org")
	herd_conn.request ("GET", "/viewcvs.py/*checkout*/gentoo/xml/htdocs/proj/en/metastructure/herds/herds.xml?rev=HEAD&content-type=text%2Fplain")
	resp = herd_conn.getresponse ()
	if (resp.status != 200):
		print "Error: Unable to retrive herds.xml :("
		sys.exit (-1)

	herds = resp.read ()
	herdsl = herds.split ('\n')

	herd_name = re.compile ('\s*<name>(.+)</name>.*')

	herd_next = 0
	dev_next = 0
	name = ""
	herd_data = open (dest_file, "w")
	herd_data.write ("herd_hash = {}\n")
	for line in herdsl:
		if (sinxmlherd.match (line)):
			herd_next = 1
			continue
		if (herd_next):
			name = herd_name.match (line).group (1)
			herd_data.write ("herd_hash.setdefault (\"" + name + "\", [])\n")
			herd_next = 0
			continue
		if (xmlmaint.match (line)):
			dev_next = 1
			continue
		if (dev_next):
			if (not maint_email.match (line)):
				print "Error: Count not match maintainer email on: " + line
				sys.exit (-1)
			dev = maint_email.match (line).group (1)
			herd_data.write ("herd_hash[\"" + name + "\"].append (\"" + dev + "\")\n")
			dev_next = 0
			continue

	herd_data.close ()
	return read_herd_data (dest_file)

def remove_dupes (array):
	tmp_hash = {}

	for i in array:
		tmp_hash.setdefault (i, "")

	ret_arr = []
	for key in tmp_hash.keys ():
		ret_arr.append (key)

	return ret_arr

def get_cur_devs_from_metadata (packages):
	mw_intree_cnt = 0
	cur_devs_hash = {}
	herded = re.compile ("herd:(.+)")
	for pack in packages.items ():
	        if (herded.match (pack[1].maintainer)):
	                herd = herded.match (pack[1].maintainer).group (1)
	                if (not herd_hash.has_key (herd)):
	                        print "Warning: Broken Metadata..." + herd + " does not exist in herds.xml"
	                        print "Warning: Package with broken metadata is " + pack[0]
	                        print "Warning: Considering as unmaintained package."
	                        mw_intree_cnt += 1
	                        continue
	                for i in herd_hash[herd]:
	                        cur_devs_hash.setdefault (i, "")
	        elif (pack[1].maintainer == "maintainer-wanted" or
	              pack[1].maintainer == "maintainer-needed" or
	              pack[1].maintainer == "null"):
                	mw_intree_cnt += 1
		else:
                	print pack[0]
                	print "Inserting...." + pack[1].maintainer
                	cur_devs_hash.setdefault (pack[1].maintainer, "")

	return (mw_intree_cnt,cur_devs_hash)

def extract_list_of_devs (url):
	devs_conn = httplib.HTTPConnection ("www.gentoo.org")
        devs_conn.request ("GET", url)
        resp = devs_conn.getresponse ()
        if (resp.status != 200):
                print "Error: Could not download list of developers. Make sure " \
                      "you have a connection to www.gentoo.org"
                sys.exit (-1)

        devs_html = resp.read ()

	devs_conn.close ()
	
	aDev = re.compile ("\s*<th class=\"infohead\" style=\"text-align:left\"><b>(.+)</b></th>\s*")
	line = ""
	devs_hash = {}
	for char in devs_html:
		if (char == "\n"):
			if (aDev.match (line)):
				devs_hash.setdetault (aDev.match (line).group (1), "")
			line = ""	
		line += char
	
	return devs_hash

def get_retired_devs_from_site ():
	url = "http://www.gentoo.org/proj/en/devrel/roll-call/userinfo.xml?statusFilter=Retired"
	return extract_list_of_devs (url)

def get_cur_devs_from_site ():
	url = "http://www.gentoo.org/proj/en/devrel/roll-call/userinfo.xml"
        return extract_list_of_devs (url)
	
if (not resume):
	cvs = "cvs -d :pserver:anonymous@anoncvs.gentoo.org:/var/cvsroot " 
	repos.append ("gentoo-x86")

	update_repos (repos, dest_dir + cvs_dest, cvs)
	#update_bugzilla_data (dest_dir + bugs_dest)
	
	commit_data_file = init_commit_data_write ()
	extract_commit_and_dev_data (dest_dir + cvs_dest, repos)
	finish_commit_data_write ()

herd_hash = get_herd_data (herd_file)
packages = extract_package_data (dest_dir + cvs_dest, "gentoo-x86")

#(mv_intree_cnt, cur_devs_hash) = get_cur_devs_from_metadata
cur_devs_hash = get_cur_devs_from_site ()

#print "Total number of maintainer-wanted packages: " + str (mw_intree_cnt)
print "Total number of developers maintaining a package via a herd or individually: " + str (len (cur_devs_hash))
sys.exit (0)

### Debuggging Stuff ###

def dbg_print_commit_print (commit_objs):
	if (verbose):
		print "Debug data for commits"
	for obj in commit_objs:
		print ""
		print obj.package
                print obj.dev
                print obj.date
                print obj.file
                print obj.rev
                print obj.bugsPostCommit
                print obj.linesAdded
                print obj.linesRemoved
                print obj.linesChanged
                print obj.lang_committed
                print obj.typeOfCommit
		print "============"

def dbg_print_package_data (pkg_objs):
	if (verbose):
		print "Debug data for packages"
	for obj in pkg_objs.values ():
		print ""
		print obj.name
		print obj.maintainer
		print obj.lang_of_package
		print obj.ebuild_loc
		print obj.install_time

### Data Mining Completed...Time Comuptation Of Results ###

def return_all_filenames ():
	basic = dash_nums.match (os.path.basename (commit_ds_data)).group (1)
	data_files = re.compile ("^" + basic + "\d+\.py$")
	
	files = []
	all = os.listdir (dest_dir)
	for file in all:
		if (data_files.match (file)):
			files.append (file)

	return files

def load_commit_and_dev_data (data_file):
	if (verbose):
		print "Loading from file: " + data_file
	handle = open (data_file, "r")
	all = handle.readlines ()
	handle.close ()
	full_str = ""
	for line in all:
		full_str += line
	exec (full_str)
	return all_commits

def compute_time_interval (start, end):
	if (start == 30000000000000 or end == 0):
		print "Error: Date not catured correctly. Start: " + str (start)  + " . End: " + str (end)
		sys.exit (-2)
	if (len (str (start)) != 14 or len (str (end)) != 14):
		print "Error: Timestamp sort. Start: " + str (start)  + " . End: " + str (end)
		sys.exit (-2)
	beg = time.mktime(time.strptime (str (start), "%Y%m%d%H%M%S"))
	end = time.mktime(time.strptime (str (end), "%Y%m%d%H%M%S"))
	return (end - beg) / 60 / 60 / 24

def avg (list):
	return sum (list) / len (list)

def var (list, avg):
	sum = 0
	for el in list:
		sum += (el - avg)**2

	return sum / (len (list) - 1)

def print_commit_statistics_per_dev (dev_hash):
	total_lpd = []
	year1_lpd = []
	year2_lpd = []
	year3_lpd = []
	old_lpd = []

	cur_total_lpd = []
	cur_year1_lpd = []
        cur_year2_lpd = []
        cur_year3_lpd = []
        cur_old_lpd = []

	for dev in dev_hash.keys ():
		if (verbose):
			print "Preparing to print data for " + dev + " (" + dev_hash[dev][2] + " " + dev_hash[dev][3] + ")"
		time_interval = compute_time_interval (dev_hash[dev][2], dev_hash[dev][3])
		work_rate = -1
		if (time_interval):
			work_rate = dev_hash[dev][1] / time_interval
		if (verbose):
			print "Developer " + dev + " changed " + str (dev_hash[dev][1]) + \
			      " lines across " + str (dev_hash[dev][0]) + " commits in a time interval of " + \
			      str (time_interval) + " (" + str (dev_hash[dev][2]) + " to " + str (dev_hash[dev][3]) + \
			      ") days. He works at a rate of " + str (work_rate) + \
			      " lines of code per day."

		if (work_rate > 1000 or time_interval < 1 or work_rate == -1):
			print "Warning: " + dev + " is a workalcholic with a work rate of " + str (work_rate) + ". Not counting him."
			continue

		total_lpd.append (work_rate)
		if (time_interval <= 365):
			year1_lpd.append (work_rate)
		elif (time_interval <= 365 * 2 and time_interval > 365):
			year2_lpd.append (work_rate)
		elif (time_interval <= 365 * 3 and time_interval > 365 * 2):
			year3_lpd.append (work_rate)
		else:
			old_lpd.append (work_rate)

		# Non-Retired Developers Only
		if (cur_devs_hash.has_key (dev)):
			cur_devs_hash[dev] = "used"
			cur_total_lpd.append (work_rate)
			if (time_interval <= 365):
				cur_year1_lpd.append (work_rate)
			elif (time_interval <= 365 * 2 and time_interval > 365):
				cur_year2_lpd.append (work_rate)
			elif (time_interval <= 365 * 3 and time_interval > 365 * 2):
				cur_year3_lpd.append (work_rate)
			else:
				cur_old_lpd.append (work_rate)
	if (verbose):
		print "Unused devs: "
		for key in cur_devs_hash:
			if not cur_devs_hash[key] == "used":
				print key
		print "==============="
	
	twr = avg (total_lpd)
	print "Total developers committing: " + str (len (total_lpd))
	print "Total work rate: " + str (twr)
	print "Total variance: " + str (var (total_lpd, twr))
	oydr = avg (year1_lpd)
	print "One year developer work rate: " + str (oydr)
	print "One year developer variance: " + str (var (year1_lpd, oydr))
	tydr = avg (year2_lpd)
        print "Two year developer work rate: " + str (tydr)
        print "Two year developer variance: " + str (var (year2_lpd, tydr))
	thydr = avg (year3_lpd)
	print "Three year developer work rate: " + str (thydr)
	print "Three year developer variance: " + str (var (year3_lpd, thydr))
	oldr = avg (old_lpd)
	print "Oldtimer work rate: " + str (oldr)
	print "Oldtimer developer variance: " + str (var (old_lpd, oldr))

	### Current Developers ###
	ctwr = avg (cur_total_lpd)
	print "Total current developers committing: " + str (len (cur_total_lpd))
	print "Current Developer Total Work Rate: " + str (ctwr)
	print "Total variance: " + str (var (cur_total_lpd, ctwr))
	coydr = avg (cur_year1_lpd)
        print "One year developer work rate: " + str (coydr)
        print "One year developer variance: " + str (var (cur_year1_lpd, coydr))
        ctydr = avg (cur_year2_lpd)
        print "Two year developer work rate: " + str (ctydr)
        print "Two year developer variance: " + str (var (cur_year2_lpd, ctydr))
        cthydr = avg (cur_year3_lpd)
        print "Three year developer work rate: " + str (cthydr)
        print "Three year developer variance: " + str (var (cur_year3_lpd, cthydr))
        coldr = avg (cur_old_lpd)
        print "Oldtimer work rate: " + str (coldr)
        print "Oldtimer developer variance: " + str (var (cur_old_lpd, coldr))

data_files = return_all_filenames ()

devs_data = {}

for data_file in data_files:
	all_commits = load_commit_and_dev_data (dest_dir + "/" + data_file)
	for com in all_commits:
		devs_data.setdefault (com.dev, [0, 0, 0, 0, ""])
		devs_data[com.dev][0] += 1
		devs_data[com.dev][1] += com.linesChanged
		if (devs_data[com.dev][2] == 0 or devs_data[com.dev][2] > com.date):
			devs_data[com.dev][2] = com.date
		if (devs_data[com.dev][3] < com.date):
			devs_data[com.dev][3] = com.date
		devs_data[com.dev][4] = com.package


print_commit_statistics_per_dev (devs_data)

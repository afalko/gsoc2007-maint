class PackageData:
	def __init__ (self, name, maint):
		# Name must be full category name
		self.name = name
		self.maintainer = maint

		# Can be derived from patches
		self.lang_of_package = "unknown"
		# loc stands for lines of code...-1 means we have not measured 
		# ... for now we take the size of the latest ebuild only
		self.ebuild_loc = -1 
		# Default to this to none if we have not/cannot measure this
		self.install_time = "none"

class BugData:
	def __init__ (self, bug_num, package):
		self.num = bug_num
		# This attribute allows us to measure the popularity of each package
		self.package = package

		self.title = ""
		self.date_reported = 0
		self.date_closed = 0
		self.priority = 0

class CommitData:
	def __init__ (self, package, committer, date, file, rev_number):
		self.package = package
		self.dev = committer
		self.date = date
		self.file = file
		self.rev = rev_number

		self.bugsPostCommit = []
		self.linesAdded = 0
		self.linesRemoved = 0
		self.linesChanged = 0

		# Bash is default for ebuilds
		self.lang_committed = "bash"
		self.typeOfCommit = "null" # can be either bugbump or verbump

class DeveloperDailyData:
	def __init__ (self, timestamp, cvs_repo):
		self.repo = cvs_repo 
		self.timestamp = timestamp

		 # Lists the commit objects
		self.commitsPerDeveloper = {}


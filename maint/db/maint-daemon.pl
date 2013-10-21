#!/usr/bin/perl
# maint-daemom for maint
# Generates a configuration file with preprocessed variables.

# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License


use DBI;
use Proc::Daemon;

use strict;

use vars qw [ $dbh $dbType $dbName $dbUsr $dbPasswd 
			$defPnts $webLoc $org $sendmail $servMail 
			@privUsrs $cacheLoc $maintPP $maintPath 
			$zillaLoc $devRegex $logFile $refRate 
			$curTime $maintDelInt $vtRefInt $abanInt 
			$apusr $apgrp $valInt $debug $libdir 
			$admin ];

open CONFIG, "/home/andrey/maint/conf/maint.conf"
                or die "Could not open config file: $!";
my @config = <CONFIG>;

SWITCH: for (@config) {
	next if (/^\#/ || /^\s*$/);
        /^dbType\s*=\s*(.+)\s*$/  && do { $dbType = $1; next };
        /^dbName\s*=\s*(.+)\s*$/  && do { $dbName = $1; next };
        /^dbUsr\s*=\s*(.+)\s*$/   && do { $dbUsr = $1; next };
        /^dbPasswd\s*=\s*(.+)\s*$/
                                && do { $dbPasswd = $1; next };
        /^default vote points\s*=\s*(.+)\s*$/
                                && do { $defPnts = $1; next };
        /^sendmailPath\s*=\s*(.+)\s*$/
                                && do { $sendmail = $1; next };
	/^admin email\s*=\s*(.+)\s*$/
				&& do { $admin = $1; next };
        /^email from\s*=\s*(.+)\s*$/
                                && do { $servMail = $1; next };
        /^location of maint on your web space\s*=\s*(.+)\s*$/
                                && do { $webLoc = $1; next };
        /^privledged user ids\s*=\s*(.+)\s*$/
                                && do { my $temp = $1;
                                        @privUsrs = split /\:/, $temp; next };
	/^cache location\s*=\s*(.+)\s*$/
				&& do { $cacheLoc = $1; next };
	/^organization\s*=\s*(.+)\s*$/
				&& do { $org = $1; next };
	/^apache user\s*=\s*(.+)\s*$/
				&& do { $apusr = $1; next };
	/^apache group\s*=\s*(.+)\s*$/
				&& do { $apgrp = $1; next };
	/^default tasks per page\s*=\s*(.+)\s*$/
				&& do { $maintPP = $1; next };
	/^maintPath\s*=\s*(.+)\s*$/
				&& do { $maintPath = $1; next };
	/^bugzilla location\s*=\s*(.+)\s*$/
				&& do { $zillaLoc = $1; next };
	/^developer regex\s*=\s*(.+)\s*$/
				&& do { $devRegex = $1; next };
	/^log file\s*=\s*(.+)\s*$/
				&& do { $logFile = $1; next };
	/^daemon refresh rate\s*=\s*(.+)\s*$/
				&& do { $refRate = $1; next };
	/^committed task delete interval\s*=\s*(.+)\s*$/
				&& do { $maintDelInt = $1; next };
	/^vote reset period\s*=\s*(.+)\s*$/
				&& do { $vtRefInt = $1; next };
	/^mark abandoned after\s*=\s*(.+)\s*$/
				&& do { $abanInt = $1; next };
	/^time to give users to validate\s*=\s*(.+)\s*$/
				&& do { $valInt = $1; next };
	/^debug\s*=\s*(.+)\s*$/
				&& do { $debug = $1; next };
	/^libdir\s*=\s*(.+)\s*$/
				&& do { $libdir = $1; next };
        die "Can't process request because I do not know what this means: $_";
}
close CONFIG;
@config = ();

open LOGFILE, ">>$logFile" or die "Can't open log file: $!";

die "Run make sqlite before continuing." if (! -e $dbName);

select LOGFILE;

$dbh = DBI->connect("dbi:$dbType:$dbName", "$dbUsr", "$dbPasswd")
	or die "Connection to database failed: $DBI::errstr";

open CACHE, ">$cacheLoc" or die "Can't open cache file for writing: $!.
        Try running as root.\n";
&genCache;

Proc::Daemon::Init();
open STDERR, ">>$logFile";

print &getTime . "maint-daemon started.\n";

$curTime = &getCurTime;

my $vtAddTime = $curTime + $vtRefInt;
while (1) {
	$curTime = &getCurTime;
	print STDOUT $curTime;

	&remStale;

	&addPoints;

	&remUser;

	&markAban;
	
	sleep $refRate;
}

sub remStale {
	# Removes tasks that have been set as committed x time ago.
	return if ($maintDelInt =~ /none/);

	my $timeOld = $curTime - $maintDelInt;

	my $sth = $dbh->prepare("DELETE FROM task WHERE status = ? 
			AND dateModified < ?");
	$sth->execute("Committed", $timeOld) if ($sth);

	print &getTime . "Committed tasks deleted.\n" if ($debug);

}

sub addPoints {
	# Adds voting points to users after a x timeinterval. 
	return if ($vtRefInt =~ /none/);

	if ($curTime > $vtAddTime) {
		my $sth = $dbh->prepare("UPDATE user SET points = ? 
			WHERE points < ?");
		$sth->execute($defPnts, $defPnts) if ($sth);

		$vtAddTime = $curTime + $vtRefInt;
	} else { 
		return;
	}

	print &getTime . "Voting points regenerated.\n" if ($debug);
}

sub remUser {
	# Removes users who have not verified after time x.
	return if ($valInt =~ /none/);

	my $oldTime = $curTime - $valInt;

	my $sth = $dbh->prepare("DELETE FROM user 
			WHERE registrationDate < ? 
			AND NOT validationCode = ?");
	$sth->execute($oldTime, 'NULL') if ($sth);

	print &getTime . "Non-validated users removed.\n" if ($debug);
}

sub markAban {
	# Mark tasks as abondoned if they are in Working, CommitReady, 
	# or Committing status and have not been modified 
	# after time x. 
	my $oldTime = $curTime - $abanInt;

	my $sth = $dbh->prepare("UPDATE task SET status = ? WHERE 
			(status = ? OR
			status = ? OR
			status = ?) AND
			dateModified < ?");
	$sth->execute("Abandoned", "Working", "CommitReady", "Committing", $oldTime) 
			if ($sth);

	print &getTime . "Tasks marked abandoned.\n" if ($debug);
}

sub getCurTime {
	return time();
}

sub getTime {
	# Returns the current in uniform format.
        my @time = localtime(time);

	my $zero1 = '0' if ($time[1] < 10);
	my $zero2 = '0' if ($time[2] < 10);
	my $zero0 = '0' if ($time[0] < 10);

        return $time[4] . "/" . $time[3] . "/" . ($time[5]+1900) .
                " " . $zero2 . $time[2] . ":" . $zero1 . $time[1] . 
		":" . $zero0 . $time[0] . 
		" ";
}

sub genCache {
	select CACHE;
	
	print '$dbType = ' . qq('$dbType';\n);
	print '$dbName = ' . qq('$dbName';\n);
	print '$dbUsr = ' . qq('$dbUsr';\n);
	print '$dbPasswd = ' . qq('$dbPasswd';\n);
	print '$defPnts = ' . qq('$defPnts';\n);
	print '$sendmail = ' . qq('$sendmail';\n);
	print '$servMail = ' . qq('$servMail';\n);
	print '$webLoc = ' . qq('$webLoc';\n);
	my $str = join qq(', '), @privUsrs;
	print '@privUsrs = ' . qq(\('$str'\);\n);
	print '$cacheLoc = ' . qq('$cacheLoc';\n);
	print '$org = ' . qq('$org';\n);
	print '$maintPP = ' . qq('$maintPP';\n);
	print '$maintPath = ' . qq('$maintPath';\n);
	print '$zillaLoc = ' . qq('$zillaLoc';\n);
	print '$devRegex = ' . qq('$devRegex';\n);
	print '$logFile = ' . qq('$logFile';\n);
	print '$refRate = ' . qq('$refRate';\n);
	print '$debug = ' . qq('$debug';\n);
	print '$libdir = ' . qq('$libdir';\n);
	print '$admin = ' . qq('$admin';\n);
	print "\n1";

	select LOGFILE;
	close CACHE;

	system ("chown $apusr:$apgrp $cacheLoc");
	system ("chmod 0640 $cacheLoc");

	print &getTime . "Cache generated successfully.\n";
}

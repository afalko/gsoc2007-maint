#!/usr/bin/perl -w
#
# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License.
use DBI;
use strict;

use vars qw [ $dbh $dbType $dbName $dbUsr $dbPasswd 
		$defPnts $webLoc
		$sendmail $servMail $admin
		@privUsrs $zillaLoc $devRegex 
		$logFile $debug 
		$extraCondition ];

my $cacheLoc = "/var/run/maint.cache";

if (! -e $cacheLoc) {
	print "Did you forget to start maint-daemon?\n";
	exit;
}

require "$cacheLoc";

{ # Scope $ver: START
my $ver = 0;
for (@privUsrs) {
	$ver = 1 if ($< eq $_ );

}
if ($ver == 0) {
	die "Make sure to add privledged users to tsk.conf and that you run 
tsk as one of those users.";
}
} # Scope $ver: END

sub connectDB {
	$dbh = DBI->connect("dbi:$dbType:$dbName", "$dbUsr", "$dbPasswd") 
			or die "Connection to database failed: $DBI::errstr";
}

sub openLog {
	 open LOGFILE, ">>$logFile" or die "Could not open log file: $!" if ($logFile);
}

sub disconnectDB {
	$dbh->disconnect;
}

# Gets total number of users or tasks recorded in database.
sub getNum {
	my $db = shift;
	
	my $sth = $dbh->prepare("SELECT COUNT(*) FROM $db");
	$sth->execute();
	
	my @res = $sth->fetchrow_array;
	
	print "$res[0]\n";
	return $res[0];
}

# Gets number of points user has left to vote with.
sub getPoints {
	my $curUsr = shift;
	
	my $in1 = $dbh->prepare("SELECT points FROM user
                        WHERE displayName=?");
        $in1->execute($curUsr);

	my @rem = $in1->fetchrow_array;

	print "$rem[0]\n";
	return $rem[0];
}

# Takes (task to display, current user logged in, what to sort by). 
# Returns array of values for task x (task name, url, status, votes, 
# deleteable or not).
sub getTskData {
	my $dispNum = shift;
	my $curUsr = shift;
	my $sortBy = shift;
	my $way = shift;
	my $condition = shift;
	my $del = 0;

	$way = 'DESC' if (!$way);

	if ($condition) {
		$condition = $condition . $extraCondition;
	} else {
		$extraCondition =~ s/ AND/WHERE/;
		$condition = $extraCondition;
	}

	#die "SELECT taskDesc, link, status,
	#                        user_displayName, votes, user_working, taskID
	#			                        FROM task $condition ORDER BY $sortBy $way";
	
	my $sth = $dbh->prepare("SELECT taskDesc, link, status, 
			user_displayName, votes, user_working, taskID
			FROM task $condition GROUP BY taskDesc ORDER BY $sortBy $way");

	my ($maintName, $url, $status, $usr, $votes, $working, $maintID);
	if ($sth) {
		$sth->execute();
		my $res = $sth->fetchall_arrayref;
		my $ref = $res->[$dispNum];

		return if (!$ref); # db is empty

		($maintName, $url, $status, $usr, $votes, $working, $maintID) = @$ref;
	} else {
		die "Cannot access the database.";
	}

	my $cnt = $dbh->prepare("SELECT COUNT(taskID) FROM task $condition");

	my $maintCnt;
	if ($cnt) {
		$cnt->execute();
		$maintCnt = ($cnt->fetchrow_array)[0];
	} else {
		die "Cannot access the database.";
	}

	$del = 1 if (($usr eq $curUsr) or &dev($curUsr));

	#$working = 'Nihil' if (!$working);

	return "$maintName, $url, $status, $votes, $working, $del, $maintID, $maintCnt\n" 
		if ($sth && $cnt);
	
}

sub appendStatCond {
	my $status = shift;

	$extraCondition = " AND status = \"$status\"";
}

sub findTskName {
	my $dispNum = shift;
	my $curUsr = shift;
        my $sortBy = shift;
        my $way = shift;
        my $keyword = shift;
	my $del = 0;

	my $condition = "WHERE taskDesc LIKE \"\%$keyword\%\"";

	&getTskData($dispNum, $curUsr, $sortBy, $way, $condition);
}

sub findUserTsks {
	my $dispNum = shift;
        my $curUsr = shift;
        my $sortBy = shift;
        my $way = shift;
	my $usr = shift;
        my $del = 0;

        my $condition = "WHERE user_displayName=\"$usr\"";

	&getTskData($dispNum, $curUsr, $sortBy, $way, $condition);
}

sub findUserWorkTsks {
	my $dispNum = shift;
        my $curUsr = shift;
        my $sortBy = shift;
        my $way = shift;
        my $usr = shift;
        my $del = 0;

        my $condition = "WHERE user_working=\"$usr\"";

        &getTskData($dispNum, $curUsr, $sortBy, $way, $condition);
}

# $sub is either "Submitted" for "Modified"
sub findTskAftDa {
	my $dispNum = shift;
        my $curUsr = shift;
        my $sortBy = shift;
        my $way = shift;
	my $date = shift;
	my $sub = shift;
        my $del = 0;

	$date =~ s/\+/ /;

        die "Syntax error: input is supposed to be either \"Modified\" or " .
                        "\"Submitted\""
                        if (!($sub eq "Submitted" or $sub eq "Modified"));

        my $condition = "WHERE date$sub >= $date";

	print LOGFILE &getTime . "Setting condition to find tasks after " .
			"$date.\n" if ($debug);

	&getTskData($dispNum, $curUsr, $sortBy, $way, $condition)
}

sub findTskBetDa {
        my $dispNum = shift;
        my $curUsr = shift;
        my $sortBy = shift;
        my $way = shift;
        my $startDate = shift;
	my $endDate = shift;
        my $sub = shift;
        my $del = 0;

        $startDate =~ s/\+/ /;
	$endDate =~ s/\+/ /;

        die "Syntax error: input is supposed to be either \"Modified\" or " .
                        "\"Submitted\" got \"$sub\"."
                        if (!($sub eq "Submitted" or $sub eq "Modified"));

        my $condition = "WHERE date$sub >= $startDate AND date$sub <= $endDate";

	print LOGFILE &getTime . "Setting condition to find tasks between " .
			"$startDate and $endDate.\n" if ($debug);

        &getTskData($dispNum, $curUsr, $sortBy, $way, $condition)
}

sub findTskBefDa {
        my $dispNum = shift;
        my $curUsr = shift;
        my $sortBy = shift;
        my $way = shift;
        my $date = shift;
        my $sub = shift;
        my $del = 0;

        $date =~ s/\+/ /;

        die "Syntax error: input is supposed to be either \"Modified\" or " . 
                        "\"Submitted\""
                        if (!($sub eq "Submitted" or $sub eq "Modified"));

        my $condition = "WHERE date$sub <= $date";

	print LOGFILE &getTime . "Setting condition to find tasks before " . 
			"$date.\n" if ($debug);

        &getTskData($dispNum, $curUsr, $sortBy, $way, $condition)
}

sub getTskIDData {
	my $taskID = shift;
        my $curUsr = shift;
	my $funcCall = shift;
        my $del = 0;
	
	my $sth = $dbh->prepare("SELECT taskDesc, link, status, 
			user_displayName, votes, user_working 
			FROM task WHERE taskID=?");
	$sth->execute($taskID);

	my ($maintName, $url, $status, $usr, $votes, $working) 
			= $sth->fetchrow_array;

	$del = 1 if (($usr eq $curUsr) or &dev($curUsr));
	
	if (!$funcCall) {
		print "$maintName, $url, $status, $votes, $working, $del\n";
	} else {
		return "$maintName, $url, $status, $votes, $working, $del";
	}
}
	
sub getCurTime {
	return time();

	# The below method is deprecated.
	#my @time = localtime(time);
	
	#return ($time[5]+1900) . "-" . $time[4] . "-" . $time[3] . 
	#	" " . $time[2] . ":" . $time[1] . ":" . $time[0];
}

# Adds a new task to the database. Takes (task display name, URL or task or 
# bug number, current user logged in). Return success(1) or failure(0).
sub addTsk {
	my $maintName = shift;
	my $url = shift;
	my $curUsr = shift;

	$maintName =~ s/^\s*//; # Remove leading whitespace.
	$maintName =~ s/\s*$//; # Remove trailing whitespace.

	$url = $zillaLoc . "show_bug.cgi?id=" . $url if ($url =~ /^\d+$/);

	my $curTime = &getCurTime;

	my $sth = $dbh->prepare("INSERT INTO task 
			(taskDesc, link, user_displayName, dateSubmitted) 
			values(?,?,?,?)");
	$sth->execute($maintName, $url, $curUsr, $curTime);
}

# Passwords are md5sum encrypted.
sub addUsr {
	my $userName = shift;
	my $email = shift;
	my $passwd = shift;
	
	my $retVal;
	$userName = $email if (!$userName);

	if (&usrExists($userName)) {
		print "Username already exists. Please try another username.\n";
	} else {
		my $dev;
		if ($email =~/$devRegex/) {
			$dev = 1;
		} else {
			$dev = 0;
		}

		my $sth = $dbh->prepare("INSERT INTO user 
				(displayName, email, dev, points, passwd, 
				validationCode, registrationDate) 
				values(?,?,?,?,?,?,?)");

		die "Failed to insert $userName into the database." if (!$sth);
			
		my $verCode = &createValCode;
		$sth->execute($userName, $email, $dev, $defPnts, $passwd, $verCode, &getCurTime);

		$retVal = &sendVerif($userName, $email, $verCode);
	}

	print LOGFILE &getTime . "Creating new user: $userName.\n";

	return $retVal;
}

sub modTsk {
	my $maintID = shift;
	my $newDesc = shift;
	my $newUrl = shift;
	my $curUsr = shift;

	my ($curDesc, $curUrl, $status, $votes, $working, $del) =
		split /, /, &getTskIDData($maintID, $curUsr, "1");

	if (!($del == 1)) {
		print "You, $curUsr, do not have permission to modify this task.\n";
		exit;
	}

	my $sth = $dbh->prepare("UPDATE task SET taskDesc = ?, link = ? 
			WHERE taskID = ?");
	$sth->execute($newDesc, $newUrl, $maintID);

	print "Task modified successfully\n";

	print LOGFILE &getTime . "$curUsr modifed task.\n" if ($debug);
}

# Creates validation URL.
sub createValCode {
	my $alphaBeta = 'abcdefghijklmnopqrstuvwxyz1234567890';
	my @alphaBeta = split //, $alphaBeta;
	
	my $str = $alphaBeta[int(rand(35))];
	for (1..(10 + int(rand(40)))) {
		$str = $str . $alphaBeta[int(rand(35))];
	}
	
	return $str;
}

sub validateUsr {
	my $code = shift;
	my $usr = shift;

	my $in = $dbh->prepare("SELECT validationCode FROM user WHERE 
			displayName=?");
	$in->execute($usr);

	my @valCode = $in->fetchrow_array;

	if ($valCode[0] eq 'NULL') {
		return "$usr appears to already be validated.";
	}

	if ($code eq $valCode[0]) {
		my $sth = $dbh->prepare("UPDATE user SET validationCode=? 
				WHERE displayName = ?");
		$sth->execute('NULL', $usr);

		print LOGFILE &getTime . "$usr validated.\n" if ($debug);

		return "$usr validated.";
	} else {
		return "Validation code does not match.";
	}
}

sub vote {
	my $vote = shift;
	my $taskID = shift;
	my $curUsr = shift;

	my $neg = 0;

	if ($vote =~ /^-/) {
		$neg = 1;
		$vote =~ s/-//;
	}
	
	my $usrPnts = &getPoints($curUsr);	

	if ($usrPnts >= $vote) {
		if ($neg) {
			my $sth = $dbh->prepare("UPDATE task SET
                                votes=votes-$vote, dateModified=? 
				WHERE taskID=?");
                        $sth->execute(&getCurTime, $taskID);
		} else {
			my $sth0 = $dbh->prepare("UPDATE task SET 
				votes=votes+$vote, dateModified=? 
				WHERE taskID=?");
			$sth0->execute(&getCurTime, $taskID);

			# Record the user's vote here. There are his 
			# points if the task he voted for gets committed.
			my $sth1 = $dbh->prepare("INSERT INTO vote 
                                VALUES(?,?,?)");
                        $sth1->execute($curUsr,$taskID,$vote);
		}
		
		my $sth2 = $dbh->prepare("UPDATE user SET points=points-$vote 
			WHERE displayName=?");
		$sth2->execute($curUsr);

		print "Vote went through\n";

		print LOGFILE &getTime . "Votes cast by $curUsr.\n" if ($debug);
	} else {
		print "Error: $curUsr does not have enough points ($usrPnts) " 
			. "to cast $vote votes.\n";
	}
}

sub cngStat {
	my $taskID = shift;
	my $status = shift;
	my $curUsr = shift;
	
	if (($status eq "Committing" or $status eq "Committed") 
			&& ! &dev($curUsr)) {
		print "Error: Only developers can set to $status status.\n"; 
		return;
	}
	
	my $sth = $dbh->prepare("UPDATE task SET status=?, dateModified=?, 
			user_working=? WHERE taskID=?"); 
	$sth->execute($status, &getCurTime, $curUsr, $taskID);
	
	if ($status eq "Committed") {
		# Find if any users casted votes for this task 
		# and add the votes back on to the users.
		my $sth1 = $dbh->prepare("SELECT amount, user_displayName 
				FROM vote WHERE 
				task_taskID=?");
		$sth1->execute($taskID);

		my @out = $sth1->fetchrow_array;
		
		my $sth2 = $dbh->prepare("UPDATE user SET points=points+? 
				WHERE displayName=?");
		$sth2->execute($out[0], $out[1]);

		# Delete the voting data to prevent cheating
		my $sth3 = $dbh->prepare("DELETE FROM vote 
				WHERE task_taskID=?");
		$sth3->execute($taskID);
	}

	print "Status changed successfully.\n";
}

sub dev {
	my $usr = shift;
	
	my $in = $dbh->prepare("SELECT dev FROM user 
                        WHERE displayName=?");
	
	my @dev;
	if ($in) {
		$in->execute($usr);
		@dev = $in->fetchrow_array;
	} else {
		# Do nothing no users registered in database.
	}

	return $dev[0] if ($in);
}

sub printRank {
	my $usr = shift;

	print &dev($usr) . "\n";
}

sub delTsk {
	my $taskID = shift;
	my $usr = shift;

	my $in = $dbh->prepare("SELECT user_displayName, dateModified 
				FROM task WHERE taskID=?");
	$in->execute($taskID);

	my @res = $in->fetchrow_array;

	if (&dev($usr) or ($res[0] eq $usr && !($res[1] eq "NULL"))) {
		my $sth = $dbh->prepare("DELETE FROM task WHERE 
				taskID=?");
		$sth->execute($taskID);

		print "Deleted Successfully.\n";

		print LOGFILE &getTime . "Task by ID $taskID deleted by $usr.\n";
	} else {
		print "Only developers or users owning an unmodified task " . 
				"can delete a task\n";
	}
}

sub delUsr {
	my $usr = shift;
	my $curUsr = shift;

	if (&dev($curUsr) or ($curUsr eq $usr)) {
		my $sth = $dbh->prepare("DELETE FROM user WHERE 
				displayName=?");
		$sth->execute($usr);

		print LOGFILE &getTime . "$usr deleted by $usr.\n";
	} else {
		print "Only developers can delete users. And users can " . 
				"delete themselves\n";
	}
}

sub passGood {
	my $usr = shift;
	my $pass = shift;
	
	my $sth = $dbh->prepare("SELECT displayName,passwd,validationCode FROM 
			user WHERE displayName = ?");
	$sth->execute($usr);

	my @out = $sth->fetchrow_array;

	if (!@out) {
		return "User does not exist\n";
	}

	if (!($out[2] eq 'NULL')) {
		return "User has not yet validated\n";
	}

	$pass =~ /^(..)/;

	my $salt = $1;

	my $realPass = &encrypt($out[1], $salt);

	if ($out[0] eq $usr) {
		if ($realPass eq $pass) {
			print LOGFILE &getTime . "$usr logs in.\n" if ($debug);

			return "User exists and password matches\n";
		} else {
			return "User exists, but password does not match\n";
		}
	} else {
		return "User does not exist\n";
	}
}

sub encrypt {
        my $pass = shift;
	my $salt = shift;
        
	return crypt($pass, $salt);
}

sub cngPasswd {
	my $usr = shift;
	my $curPass = shift;
	my $newPass = shift;

        my $sth = $dbh->prepare("SELECT passwd FROM user
                        WHERE displayName = ?");
        $sth->execute($usr);

        my @out = $sth->fetchrow_array;

        $curPass =~ /^(..)/;

        my $salt = $1;

        my $realPass = &encrypt($out[0], $salt);

	if ($realPass eq $curPass) {
		my $in = $dbh->prepare("UPDATE user SET passwd=? 
                        WHERE displayName=?");
		$in->execute($newPass, $usr);
		print "Password changed successfully\n";

		print LOGFILE &getTime . "$usr changes password successfully.\n" if ($debug);
	} else {
		print "You current password does not match what you " . 
				"inputted\n";
	}
}

sub usrExists {
	my $usr = shift;

	my $sth = $dbh->prepare("SELECT displayName FROM user
			WHERE displayName=?");

        $sth->execute($usr);
	my @out = $sth->fetchrow_array;

	if (@out) {
		return 1;
	} else {
		return 0;
	}
}

sub untaintSendmail {
	my $sendmail = shift;

	if ($sendmail =~ /^((\/\w+)+)(\/sendmail)$/) {
		$ENV{PATH} = "";
                return "$1$3";
        } else {
                die "Could not untaint sendmail command."
        }
}

#Emails user verification code.
sub sendVerif {
	my $usr = shift;
	my $email = shift;
	my $verCode = shift;

	my $sendmail_cmd = &untaintSendmail ($sendmail);
	if ($sendmail =~ /^((\/\w+)+)(\/sendmail)$/) {
		$sendmail_cmd = "$1$3";
	} else {
		die "Could not untaint sendmail command."
	}
	
	open EMAIL, "|/$sendmail_cmd -oi -t" or die "Can't open sendmail: $!";

	select EMAIL;

	print "To: $email\n";
	print "From: $servMail\n";
	print "Subject: Your verification code\n\n";

	my $sth = $dbh->prepare("SELECT validationCode FROM user
		WHERE displayName = ?");
        $sth->execute($usr);

	my @ver = $sth->fetchrow_array;

	if ($ver[0]) {
		print "Hi $usr, \n\n" . 
			"Your verification code for maint is: $ver[0] \n\n" . 
			"I suggest you copy and paste in the following " .
			"place: http://$webLoc/verify.cgi";
	} else {
		print "Hi $usr, \n\n" . 
			"It appears that http://$webLoc is having technical " . 
			"difficulties. Please notify $admin that you " . 
			"recieved this email. You will have to re-register " . 
			"once things are normal. \n\n" .
			"We appologize for the inconvenience.";
	}

	select STDOUT;
	close EMAIL;

	print LOGFILE &getTime . "Verification sent to $email for $usr\n";

	return "Verification Sent.";
}

sub getEmail {
	my $usr = shift;
	
	my $sth = $dbh->prepare("SELECT email FROM user
                        WHERE displayName = ?");
        $sth->execute($usr);

        my @email = $sth->fetchrow_array;

	if (!$email[0]) {
		die "User does not exist.";
	}

	return $email[0];
}

sub pwReset {
	my $usr = shift;

	my $email = &getEmail($usr);

	my $sendmail_cmd = &untaintSendmail ($sendmail);
	open EMAIL, "|/$sendmail_cmd -oi -t" or die "Can't open sendmail: $!";

	select EMAIL;

	print "To: $email\n";
        print "From: $servMail\n";
        print "Subject: Your password for $webLoc\n\n";

        my $sth = $dbh->prepare("SELECT passwd FROM user
                WHERE displayName = ?");
        $sth->execute($usr);

        my @passwd = $sth->fetchrow_array;

        print "Hi $usr,

Your password for maint is: $passwd[0]

You can change it in your preferences: http://$webLoc/prefs.cgi";

        select STDOUT;
        close EMAIL;

	print LOGFILE &getTime . "$usr requested his password.\n";

	return 1;
}

sub getPrefs {
	my $usr = shift;

	my $sth = $dbh->prepare("SELECT pref_tskpp FROM user 
			WHERE displayName = ?");
	$sth->execute($usr);

	my @prefs = $sth->fetchrow_array;

	print "$prefs[0]\n";
}

sub setPrefs {
	my $usr = shift;
	my $maintPP = shift;

	my $sth = $dbh->prepare("UPDATE user SET pref_tskpp=?
			WHERE displayName=?");
	$sth->execute($maintPP, $usr);

	print LOGFILE &getTime . "$usr set his preferences.\n" if ($debug);
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
1

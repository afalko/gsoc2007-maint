#!/usr/bin/env perl -wT
# Tsk: addtask.cgi

# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License

use CGI qw [ :standard ];
use CGI::Carp qw [ warningsToBrowser fatalsToBrowser ];
use HTTP::Date;
use Untaint;
use strict;

use lib "/var/run";

use vars qw [ $org $admin ];

require "maint.cache";

my $descKey = param('descKey');
my $authKey = param('authKey');
my $usrWork = param('usrWork');
my $startDateMon = param('startDateMon');
my $startDateDay = param('startDateDay');
my $startDateYear = param('startDateYear');
my $startDateHour = param('startDateHour');
my $startDateMin = param('startDateMin');
my $startDateSec = param('startDateSec');
my $endDateMon = param('endDateMon');
my $endDateDay = param('endDateDay');
my $endDateYear = param('endDateYear');
my $endDateHour = param('endDateHour');
my $endDateMin = param('endDateMin');
my $endDateSec = param('endDateSec');
my $modifOnly = param('modifOnly');
my $onlyStatus = param('onlyStatus');

$descKey = untaint(qr(.*), $descKey);
$authKey = untaint(qr(.*), $authKey);
$usrWork = untaint(qr(.*), $usrWork);
$startDateMon = untaint(qr(\d?\d?), $startDateMon);
$startDateDay = untaint(qr(\d?\d?), $startDateDay);
$startDateYear = untaint(qr(\d?\d?\d?\d?), $startDateYear);
$startDateHour = untaint(qr(\d?\d?), $startDateHour);
$startDateMin = untaint(qr(\d?\d?), $startDateMin);
$startDateSec = untaint(qr(\d?\d?), $startDateSec);
$endDateMon = untaint(qr(\d?\d?), $endDateMon);
$endDateDay = untaint(qr(\d?\d?), $endDateDay);
$endDateYear = untaint(qr(\d?\d?\d?\d?), $endDateYear);
$endDateHour = untaint(qr(\d?\d?), $endDateHour);
$endDateMin = untaint(qr(\d?\d?), $endDateMin);
$endDateSec = untaint(qr(\d?\d?), $endDateSec);
$onlyStatus = untaint(qr((Any)|(Reported)|(Working)|(Abandoned)|(CommitReady)|(Committing)|(Committed)), $onlyStatus);

if ($modifOnly) {
	$modifOnly = 1;
} else {
	$modifOnly = 0;
}

# If nothing.
if (!($descKey || $authKey || $usrWork || $onlyStatus ||
		$startDateMon || $startDateDay || $startDateYear ||
		$startDateHour || $startDateMin || $startDateSec || 
		$endDateMon || $endDateDay || $endDateYear ||
		$endDateHour || $endDateMin || $endDateSec)) {
	&printForm;
}

if ($descKey) {
        print redirect(-uri=>"index.cgi?showKey=$descKey;onlyStatus=$onlyStatus");
} elsif ($authKey) {
        print redirect(-uri=>"index.cgi?showTsk=$authKey;onlyStatus=$onlyStatus");
} elsif ($usrWork) {
	print redirect(-uri=>"index.cgi?usrWork=$usrWork;onlyStatus=$onlyStatus");
} elsif ($startDateMon && $startDateDay && $startDateYear 
		&& $endDateMon && $endDateDay && $endDateYear) {
	my $startTime;
	if ($startDateHour || $startDateMin || $startDateSec) {
                $startTime = &formatTime($startDateMon, $startDateDay, $startDateYear,
                                $startDateHour, $startDateMin, $startDateSec);
        } else {
                $startTime = &formatTime($startDateMon, $startDateDay, $startDateYear, 0, 0, 0);
        }

	my $endTime;
	if ($endDateHour || $endDateMin || $endDateSec) {
                $endTime = &formatTime($endDateMon, $endDateDay, $endDateYear,
                                $endDateHour, $endDateMin, $endDateSec);
        } else {
                $endTime = &formatTime($endDateMon, $endDateDay, $endDateYear, 0, 0, 0);
        }

	print redirect(-uri=>"index.cgi?startDate=$startTime;endDate=$endTime;modifOnly=$modifOnly;onlyStatus=$onlyStatus")
} elsif ($startDateMon && $startDateDay && $startDateYear) {
	my $fedTime;
	if ($startDateHour || $startDateMin || $startDateSec) {
		$fedTime = &formatTime($startDateMon, $startDateDay, $startDateYear,
				$startDateHour, $startDateMin, $startDateSec);
	} else {
		$fedTime = &formatTime($startDateMon, $startDateDay, $startDateYear, 0, 0, 0);
	}
	print redirect(-uri=>"index.cgi?startDate=$fedTime;modifOnly=$modifOnly;onlyStatus=$onlyStatus")
} elsif ($endDateMon && $endDateDay && $endDateYear) {
        my $fedTime;
        if ($endDateHour || $endDateMin || $endDateSec) {
                $fedTime = &formatTime($endDateMon, $endDateDay, $endDateYear,
                                $endDateHour, $endDateMin, $endDateSec);
        } else {
                $fedTime = &formatTime($endDateMon, $endDateDay, $endDateYear, 0, 0, 0);
        }
        print redirect(-uri=>"index.cgi?endDate=$fedTime;modifOnly=$modifOnly");
} elsif ($onlyStatus) {
	print redirect(-uri=>"index.cgi?onlyStatus=$onlyStatus;modifOnly=$modifOnly");
} else {
	# Redirect back here 
	&printForm("I am sorry. I am unable to run your search. <br>Before you tell $admin 
		what you tried to do. <br>Make sure that you filled out all required fields for the dates.<br><br>");
}

sub printForm {
	my $error = shift;

	print 
		header,
		start_html(-title=>"Advanced Search Page",
                                -style=>{'src'=>'interface.css'}),
                qq(<h1>Advanced Search Page</h1>),
                qq(<table border=0 width=100%><tr>
                                <td WIDTH=9%></td>
                                <td ALIGN=center><a href="index.cgi?">Return to Main</a></td>
                                <td ALIGN=right width=9%><a href="help.html">Click here for help</a></td>
                   </tr></table>),br,br,
		"$error",
		start_form,
		"Find tasks by description keyword: ",
		textfield('descKey'),br,br,
		"Find tasks by author: ",
		textfield('authKey'),br,br,
		"Find tasks where the person working is: ",
		textfield('usrWork'),br,br,
		"Find tasks by range of time*: ",br,
		textfield(-name=>'startDateMon', -size=>2, -maxlength=>2),"-",
		textfield(-name=>'startDateDay', -size=>2, -maxlength=>2),"-",
		textfield(-name=>'startDateYear', -size=>4, -maxlength=>4)," ",
		textfield(-name=>'startDateHour', -size=>2, -maxlength=>2),":",
		textfield(-name=>'startDateMin', -size=>2, -maxlength=>2),":",
		textfield(-name=>'startDateSec', -size=>2, -maxlength=>2),"(Start Date**) ",br,
		textfield(-name=>'endDateMon', -size=>2, -maxlength=>2),"-",
                textfield(-name=>'endDateDay', -size=>2, -maxlength=>2),"-",
                textfield(-name=>'endDateYear', -size=>4, -maxlength=>4)," ",
                textfield(-name=>'endDateHour', -size=>2, -maxlength=>2),":",
                textfield(-name=>'endDateMin', -size=>2, -maxlength=>2),":",
                textfield(-name=>'endDateSec', -size=>2, -maxlength=>2),"(End Date**)",br,
		checkbox(-name=>'modifOnly', -label=>"Find modified tasks only."),br,br,
		"Only show task of status: ", popup_menu("onlyStatus", 
				['Any', 'Reported','Working','Abandoned','CommitReady','Committing','Committed'],
				'Any'),br,br,
		submit('Search'),end_form,br,br,
		"*Both date fields do not have to be entered; Only only one is required.",br,
		"**Date is entered in this format: MM-DD-YYYY hour:min:sec (the hour, minutes, and seconds are optional)",
		end_html;
		exit;
}

sub format {
        my $input = shift;

        my @chars = split //, $input;

        return "\\" . join ("\\", @chars);
}

sub formatTime {
	my $dateMon = shift;
	my $dateDay = shift;
	my $dateYear = shift;
	my $dateHour = shift;
	my $dateMin = shift; 
	my $dateSec = shift;

	if (!$dateHour || !$dateMin) {
		$dateHour = "00";
		$dateMin = "00";
		$dateSec = "00";
	}
	
	return str2time("$dateYear-$dateMon-$dateDay $dateHour:$dateMin:$dateSec");
}

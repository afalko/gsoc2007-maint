#!/usr/bin/env perl -wT

# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License

use CGI qw [ :standard ];
use CGI::Carp qw [ warningsToBrowser fatalsToBrowser ];
use strict;

use lib ".";

use db::maint;

&connectDB;

use lib "/var/run";

use vars qw [ $maintPath $org $maintPP 
		$usr $params $sortParams $totalTasks ];

require "maint.cache";

if (my $info = cookie('maint-auth')) {
	#my $info = cookie('maint-auth');
	my ($lusr, $passwd) = split / /, $info;
	# The goto allows us to skip over the if block.
	goto noauth if (!$lusr);

	my $out = &passGood($lusr,$passwd);
	if ($out eq "User exists and password matches\n") {
		$usr = $lusr;
	} elsif ($out eq "User has not yet validated\n") {
		print redirect(-uri=>"verify.cgi?");
	} else {
		# Empty cookie
		my $cookie = cookie(-name => "maint-auth",
		                    -expires => 'now',
				    -value => "");
		print redirect(-uri=>"login.cgi?error=1", -cookie=>$cookie);
	}
}

# Label goto in above if sends us here.
noauth:

if ($usr) {
	my $prefs = &getPrefs ($usr);
	chomp($prefs);
	
	$prefs =~ /(.*)/;
	$maintPP = $1 if ($1);
}

if (my $prefs = cookie('maint-prefs')) {
	$maintPP = $prefs;
}

my $maintAdded = param('taskadded');
my $maintDeleted = param('taskDeleted');
my $maintModified = param('taskModifed');
my $start = param('start');
my $maintPPt = param('maintPP');
my $sortBy = param('sortBy');
my $asc = param('asc');
my $showTsk = param('showTsk');
my $showKey = param('showKey');
my $usrWork = param('usrWork');
my $startDate = param('startDate');
my $endDate = param('endDate');
my $modifOnly = param('modifOnly');
my $onlyStatus = param('onlyStatus');

if ($modifOnly) {
        $params = $params . ";modifOnly=$modifOnly";
}

if ($onlyStatus) {
	$params = $params . ";onlyStatus=$onlyStatus";
}

if ($onlyStatus eq "Any" || !$onlyStatus) {
	$onlyStatus = "";
} else {
	$onlyStatus = "--showTaskOfStatus=$onlyStatus";
}

if ($modifOnly == 1) {
	$modifOnly = 'Modified';
} else {
	$modifOnly = 'Submitted';
}

my $prefsCook;
if ($maintPPt) {
	$maintPP = $maintPPt;
	$prefsCook = cookie(-name => "maint-prefs", 
			-expires => '1m', 
			-value => "$maintPP");
}

if ($showTsk) {
	$params = ";showTsk=$showTsk";
} elsif ($showKey) {
	$params = ";showKey=$showKey";
} elsif ($usrWork) {
	$params = ";usrWork=$usrWork";
} else {

}

if ($sortBy) {
	$params = $params . ";sortBy=$sortBy";
}

if ($asc) {
	$params = $params . ";asc=1";
}

if ($startDate) {
	$params = $params . ";startDate=$startDate";
}

if ($endDate) {
        $params = $params . ";endDate=$endDate";
}

print header -cookie=>$prefsCook;

print qq(<html>
	<head>
		<title>Task List for $org</title>
		<link rel="stylesheet" type="text/css" href="index.css">
	</head>

	<body>);

if ($usr) {
	print qq(<table border=0 align=center width=100%>
			<tr>
			<td align=left width=25%>
				<form method="post">
				<input type="text" name="showKey"/>
				<input type="submit" value="Search"/>
				</form>
				<a href="search.cgi">Advanced Search</a>
			</td>
			<td align=left width=30%>
				<form method="post">
                                Show all tasks submitted by: <input type="text" name="showTsk"/>
                                <input type="submit" value="Go"/>
                                </form>
				<a href="index.cgi?showTsk=$usr">My submitted tasks</a></td>
			<td align=right width=30%>You are logged in as ) . $usr . qq(</td>
			<td align=right width=10%><a href="prefs.cgi">Preferences</a></td>
			<td align=right width=5%><a href="logout.cgi">Logout</a></td>
			</tr>
		</table>);

#<a href="index.cgi?showTsk=$usr">My submitted tasks</a>
} else {
	print qq(<table border=0 align=center width=100%>
		<tr>
			<tr>
                        <td align=left width=25%>
                                <form method="post">
                                <input type="text" name="showKey"/>
                                <input type="submit" value="Search"/>
                                </form>
                                <a href="search.cgi">Advanced Search</a>
                        </td>
			<td align=left width=35%>
                                <form method="post">
                                Show all tasks submitted by: <input type="text" name="showTsk"/>
                                <input type="submit" value="Go"/>
                                </form>
                        </td>
			<td align=right width=15%><a href="login.cgi">Login</a>
			<a href="register.cgi">Register</a></td>
		</tr>
		</table><p>);
}
print qq(<p>);


print qq(<h1>Task List for $org</h1><p>
	<table border=0 align=center width=100%><tr>
		<td width=9%></td>
		<td align=center width=82%><a href="index.cgi?">Return to Main</a></td>
		<td align=right width=9%><a href="help.html">Click here for help</a></td>
	</tr></table>);

if ($usr) {
	my $remVotes = &getPoints ($usr);

	print qq(<p>Task added. I have brought you back to main page. ) .
		qq(<a href="index.cgi?showKey=$maintAdded">See Task</a>.<br>) 
			if ($maintAdded);
	print qq(Task deleted.<br>) if ($maintDeleted eq "1");
	print qq(Task modified.<br>) if ($maintModified eq "1");

	print qq(<table border=0 width=100%><tr>
				<td align=left width=50%><a href="addtask.cgi">Add Task</a></td>
				<td align=right width=50%>You have $remVotes voting points remaining</td>
		 </tr></table>);
}

$start = 0 if ($start < 0);
&printTable($start, $start + $maintPP);

sub printTable {
	my $start = shift;
	my $end = shift;
	$sortBy = 'votes' if (!$sortBy);

	my $delete = 'Delete';
	$delete = 'Not logged in' if (!$usr);

	print qq(<table border=1 width=100% class="main">
		<tr align="CENTER" valign="CENTER" class="main">);

	my $way;
	if ($asc == 1) {
	        $way = 'ASC';
	} else {
	        $way = 'DESC';
	}

	$params = "" if (!$params);
	$sortParams = $params;
	$sortParams =~ s/asc=\d//;
        $sortParams =~ s/sortBy=\w+//;

	if (!$asc) {
		print qq(<th width="45%"><span class="header">
			<a href="index.cgi?sortBy=taskDesc;asc=1$sortParams">Task Description</a>
		 </span></th>
  		 <th width="15%"><span class="header">
		 	<a href="index.cgi?sortBy=status;asc=1$sortParams">Status</a>
		 </span></th>
		 <th><span class="header">
			<a href="index.cgi?sortBy=votes;asc=1$sortParams">Votes</a>
		 </span></th>);
	} else {
		print qq(<th width="45%"><span class="header">
				<a href="index.cgi?sortBy=taskDesc$sortParams">Task Description</a></span>
			 </th>
			 <th width="15%"><span class="header">
			 	<a href="index.cgi?sortBy=status$sortParams">Status</a>
			 </span></th>
                         <th><span class="header">
			 	<a href="index.cgi?sortBy=votes;asc=0$sortParams">Votes</a>
			 </span></th>);
	}

	#print qq(<th width="95">Vote</th> 
	print qq(<th></th></tr>) if ($usr);

	print "" . &getRows($start, $end, $usr, $sortBy, $way) . qq(</tr></table>);

	my $next = $end;
	my $prev = $start - $maintPP - 1;
	$prev = 0 if ($prev < 0);

	print qq(<table border=0 width=100%><tr>);
	# Blank out previous if there no where to go.
	if ($next > $maintPP + 1) {
		print qq(<td align=left width=20%><a href="index.cgi?start=$prev;maintPP=$maintPP$params">Previous</a></td>);
	} else {
		print qq(<td align=left width=20%>Previous</td>);
	}
	print qq(<td align=center width=60%>
				<form method="post">
				Number to display per page: 
				<input type="text" name="maintPP" size="3" maxlength="3" value="$maintPP"/>
				<input type="submit" name="Set" value="Set" /><br>
				</form>		
			</td>);
	if (int ($next) < int ($totalTasks)) {
		print qq(<td align=right width=20%><a href="index.cgi?start=$next;maintPP=$maintPP$params">Next</a></td>);
	} else {
		print qq(<td align=right width=20%>Next</td>);
	}
	print qq(</tr></table>);

	print end_html;
	&disconnectDB;
	exit 0;
}

sub getRows {
	my $start = shift;
	my $end = shift;
	my $usr = shift;
	my $sortBy = shift;
	my $way = shift;

	my $str = '';
	for ($start..$end - 1) {
		my $out;
	
		if ($showTsk) {
			$out = &findUserTsks ($_,$usr,$sortBy,$way,$showTsk);
		} elsif ($showKey) {
			$out = &findTskName ($_,$usr,$sortBy,$way,$showKey);
		} elsif ($usrWork) {
			$out = &findUserWorkTsks ($_,$usr,$sortBy,$way,$usrWork);
		} elsif ($startDate && $endDate) {
			$out = &findTskBetDa ($_,$usr,$sortBy,$way,$startDate,$endDate,$modifOnly);
		} elsif ($startDate) {
			$out = &findTskAftDa ($_,$usr,$sortBy,$way,$startDate,$modifOnly);
		} elsif ($endDate) {
			$out = &findTskBefDa ($_,$usr,$sortBy,$way,$endDate,$modifOnly);
		} else {
			$out = &getTskData ($_,$usr,$sortBy,$way);
		}

		my $maint = $out;
		my $dev = &printRank ($usr);
		# 1: Task diplay name
		# 2: Url
		# 3: Status
		# 4: Votes
		# 5: Whether the current user is working on the task
		# 6: Whether the task is deletable by the current user
		# 7: The task IDa
		# 8: Total tasks
		$maint =~ /(.*), (.*), (.*), (.*), (.*), (.*), (.*), (.*)/;
		
		last if (!$maint);
		
		# Deprecated
		#my $delBox = '';
		#if ($6 == 1) {
		#	$delBox = checkbox("del_$7", '', 'on', ' ');
		#}

		$totalTasks = $8 || 0;

		my $xis = "";
		if ($5) {
			$xis = "$5 is " if (($3 eq 'Committing') 
						or ($3 eq 'Working'));
			$xis = "$5 " if ($3 eq 'Committed');
			$xis = "$5 marked " if ($3 eq 'CommitReady');
		}

		my $statMenu;
		if ($dev) { # Devs see full menu
			$statMenu = popup_menu("status_$7", 
				['Reported','Working','Abandoned','CommitReady','Committing','Committed'], 
				"$3");
		} elsif ((($3 eq 'Working') && !($usr eq $5)) || 
			!$usr || 
			($3 eq 'Committing' || $3 eq 'Committed')) {
				$statMenu = popup_menu("status_$7",
                                	["$3"],
                                	"$3");
		} elsif (!($3 eq 'Working') || 
			($3 eq 'Working' && $usr eq $5)) { # Task not marked working by someone else.
				if (!($3 eq 'Reported' || $3 eq 'Working' ||
					$3 eq 'Abandoned' || $3 eq 'CommitReady')) {
					$statMenu = popup_menu("status_$7",
                                		['Reported','Working','Abandoned','CommitReady', "$3"],
                                		"$3");
				} else {
					$statMenu = popup_menu("status_$7",
						['Reported','Working','Abandoned','CommitReady'],
						"$3");
				}
		} else { 
			print "You might have stumbled on a bug. Provide the following 
output in you bug report: \"OUT: $out USER: $usr\<br\>\"";
		}

		
		my $maintID_hidden = hidden('maintID', $7);

		my $submit = submit('Submit') if ($usr);

		$str = $str . qq(<tr class="faint" onmouseover="className='$3';" onmouseout="className='faint';">); 
		
		$str = $str . start_form(-action=>"oper.cgi") if ($usr);

		if ($6 == 1) { # If deleteable, then modifiable ;).
			$str = $str . qq(<td width="65%">
					<table border=0 width=100%><tr>
					<td><span class="tbrows">
						<a href=$2>$1</a>
					</span></td>
					<td align=right width=90><span class="tbrows">
						<a href="modify.cgi?modTsk=$7">Modify</a> | 
						<a href="delTask.cgi?delTsk=$7">Delete</a>
					</span></td></tr></table></td>);
		} else {
			$str = $str . qq(<td width="65%"><span class="tbrows"><a href=$2>$1</a></span></td>);

		}
		
		
		$str = $str . qq(<td width="15%">$xis$statMenu</td>);

		if ($usr) {
			$str = $str . qq(<td width="145">) . 
					'<table border=0 width=145 align=center><tr><td>' . 
					"<td align=left width=40%>$4" .
					'</td><td align=right>' . 
					textfield(-name=>"vote_amount_$7", -size=>2, -maxlength=>2, -default=>0) . 
					'</td><td align=left>' . 
					radio_group(-name=>"operation_$7", -values=>['+', '-'], default=>'') . 
					'</td></tr></table></td>' .
					qq($maintID_hidden) . hidden("statWas", $3) . 
					qq(<td align=center width=50>$submit</td>) . end_form;
		} else {
			$str = $str . "<td align=center width=5%>$4</td>";
		}
		
		$str = $str . '</tr>';

	}

	#$str =~ s/,$//; # Remove trailing comma.
	return 	$str;
}


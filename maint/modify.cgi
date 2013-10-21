#!/usr/bin/env perl -wT
# Tsk: addtask.cgi

# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License

use CGI qw [ :standard ];
use CGI::Carp qw [ warningsToBrowser fatalsToBrowser ];
use Untaint;
use strict;

use lib "/var/run";

use vars qw [ $maintPath $usr $org ];

require "maint.cache";

$ENV{PATH} = untaint(qr(.*), $ENV{PATH});
$maintPath = untaint(qr(maint$), $maintPath);

if (my $info = cookie('maint-auth')) {
        #my $info = cookie('maint-auth');
        my ($lusr, $passwd) = split / /, $info;
	$lusr = untaint(qr(.+), &format($lusr));
        $passwd = untaint(qr(.+), &format($passwd));
        my $out = `$maintPath --checkPassword=$lusr,$passwd`;
        if ($out eq "User exists and password matches\n") {
                $usr = $lusr;
        } else {
                print redirect(-uri=>"login.cgi?error=1");
        }
}

my $modTsk = param('modTsk');
my $taskDesc = param('taskDesc');
my $url = param('url');

$modTsk = untaint(qr(\d+), $modTsk);
$taskDesc = untaint(qr(.+), $taskDesc);
$url = untaint(qr(.+), $url); 

if ($modTsk) {
	print redirect(-uri=>"index.cgi?") if (!$usr);
	my $out = `$maintPath --getTaskByID=$modTsk,$usr`;

	chomp $out;
	my ($curDesc, $curUrl, $status, $votes, $working, $del) = 
			split /, /, $out;

	# Check if the user is allowed to modify the task.
	print redirect(-uri=>"index.cgi?") if (!($del == 1));

	# If change was made.
	if (($taskDesc && $url) && 
		!($taskDesc eq $curDesc) || !($url eq $curUrl)) {
		
		$taskDesc = &format($taskDesc);
		$url = &format($url);
		my $out = `$maintPath --modifyTask=$modTsk,$taskDesc,$url,$usr`;
		
		if ($out eq "Task modified successfully\n") {
			print redirect(-uri=>"index.cgi?taskModified=1");
		}
		
		&printForm("$out<br><br>", $curDesc, $curUrl, $modTsk);
	}

	&printForm("" , $curDesc, $curUrl, $modTsk);
} else {
	# Redirect to index if someone is trying to hack.
	print redirect(-uri=>"index.cgi?");
}

sub printForm {
	my $error = shift;
	my $curDesc = shift;
	my $curUrl = shift;
	my $maintID = shift;

	print 
		header,
		start_html(-title=>"Modify Task for $org",
                                -style=>{'src'=>'interface.css'}),
                qq(<h1>Modify Task for $org</h1>),
                qq(<table border=0 width=100%><tr>
                                <td WIDTH=9%></td>
                                <td ALIGN=center><a href="index.cgi?">Return to Main</a></td>
                                <td ALIGN=right width=9%><a href="help.html">Click here for help</a></td>
                   </tr></table>),p,
		"$error",
		start_form,
		"Task Description: ",textfield('taskDesc', $curDesc),br,br,
		"URL (or bug number): ",textfield('url', $curUrl),br,br,
		hidden('modTsk', $maintID),
		submit('Modify'),qq(   <a href="index.cgi?">Cancel</a>),
		end_form,
		end_html;
		exit;
}

sub format {
        my $input = shift;

        my @chars = split //, $input;

        return "\\" . join ("\\", @chars);
}

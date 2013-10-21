#!/usr/bin/env perl -wT
# Tsk: addtask.cgi
#
# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License

use CGI qw [ :standard ];
use CGI::Carp qw [ warningsToBrowser fatalsToBrowser ];
use Untaint;
use strict;

use lib ".";

use db::maint;

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
        my $out = &passGood ($lusr,$passwd);
        if ($out eq "User exists and password matches\n") {
                $usr = $lusr;
        } else {
                print redirect(-uri=>"login.cgi?error=1");
        }
}

my $maintDesc = param('taskDesc');
my $url = param('url');

&printForm if (!($maintDesc && $url));
&printForm("Error: All fields are mandatory.<br><br>") if (!($maintDesc || $url));

$maintDesc = untaint(qr(.+), &format($maintDesc));
$url = untaint(qr(.+), &format($url));

my $out = &addTsk ($maintDesc,$url,$usr);

sub format {
	my $input = shift;

	my @chars = split //, $input;

	return "\\" . join ("\\", @chars);
}

print redirect(-uri=>"index.cgi?taskadded=$maintDesc");

sub printForm {
	my $error = shift;
	print 
		header,
		start_html(-title=>"Add Task for $org", 
				-style=>{'src'=>'interface.css'}),
		qq(<h1>Add Task for $org</h1>),
		qq(<table border=0 width=100%><tr>
	        	        <td width=9%></td>
				<td align=center><a href="index.cgi?">Return to Main</a></td>
		                <td align=right width=9%><a href="help.html">Click here for help</a></td>
	           </tr></table>),p,
		"You may add a task here. Keep your description concise, but ",
		"at the same time detailed enough to contain a summary of ",
		"what you think needs to be done.",
		"You many enter any url that points to more information about ",
		"the task you are entering. For your conveniance, you may ",
		"input a bug number for $org instead of having to enter the ",
		"full URL.",br,br,
		"$error",
		start_form,
		"Task Description: ",textfield('taskDesc'),br,br,
		"URL (or bug number): ",textfield('url'),br,br,
		<center>,submit('Add Task'),
		end_form
		end_html;
		exit;
}

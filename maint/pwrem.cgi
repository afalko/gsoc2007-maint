#!/usr/bin/env perl -wT
# Tsk: login.cgi

# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License

use CGI qw [ :standard ];
use CGI::Carp qw [ warningsToBrowser fatalsToBrowser ];
use strict;

use lib ".";

use db::maint;

use lib "/var/run";

require "maint.cache";

my $displayName = param('displayName');

&connectDB;
if ($displayName) {
	my $res = &pwReset ($displayName);
	&disconnectDB;
	&printForm ("Error: Could not send password reminder. Make " .
                   "sure the username you entered is correct.")
		   if (!$res == 1);
	print
                header,
                start_html("Password Reminder Page"),
		"Your password has been sent to ",
		"the email you registered with. If you forgot the ", 
		"email address you registered with, we ", 
		"cannot help you.",p,
		qq(<a href="index.cgi">Re-direct to main</a>.),
                end_html;
	
	sleep 5;
	redirect(-uri=>"index.cgi");
        exit;
} else {
	&printForm;
}

&disconnectDB;
print redirect(-uri=>"index.cgi");

sub printForm {
	my $error = shift || "";
	print
        	header,
		$error,
		start_html(-title=>"Password Reminder",
                                -style=>{'src'=>'interface.css'}),
                qq(<h1>Password Reminder</h1>),
                qq(<table border=0 width=100%><tr>
                                <td WIDTH=9%></td>
                                <td ALIGN=center><a href="index.cgi?">Return to Main</a></td>
                                <td ALIGN=right 9%><a href="help.html">Click here for help</a></td>
                   </tr></table>),br,br,
		"Enter the username you registered with. An ",
		"email will be sent to the email account you ",
		"used to register.",br,br,
        	start_form,
        	"Username: ",textfield('displayName'),br,br,
        	submit('Send Reminder'),
        	end_form,
		end_html;
	exit;
}

#!/usr/bin/env perl -wT
# Tsk: verify.cgi

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

use vars qw [ $maintPath ];

require "maint.cache";

my $displayName = param('displayName');
my $verCode = param('verCode');

&printForm(qq(We need to verify that the email you provided is correct. <br>
		Enter data into both fields.<br><br>)) if (!($displayName && $verCode)); 
&printForm("Error: You did not enter your username.<br><br>") if (!$displayName);
&printForm("Error: You have to enter the verification code you recieved via email.<br><br>") 
		if (!$verCode);

&connectDB;
my $out = &validateUsr ($verCode,$displayName);
&disconnectDB;

if ($out eq "Validation code does not match.") {
	&printForm("Error: You entered an incorrect verification code or username. Please try again.<br><br>");
} elsif ($out eq "$displayName validated.") {
	# Delete the cookie.
	my $cookie = cookie(-name => "maint-auth",
	        -expires => '-1m',
		-value => "");
	print redirect(-uri=>'login.cgi?justverified=1');
} elsif ($out eq "$displayName appears to already be validated.") {
	&printForm("To reassure you: you are already verified."); 
} else {
	&printForm("Unknown error: please file bug. Please include this output: $maintPath --validateUser=$verCode,$displayName ==> $out");
}

sub printForm {
	my $error = shift;
	print 
		header,
		start_html("Verification Form"),
		start_html(-title=>"Verification Form",
                                -style=>{'src'=>'interface.css'}),
                qq(<h1>Verification Form</h1>),
                qq(<table border=0 width=100%><tr>
                                <td WIDTH=9%></td>
                                <td ALIGN=center><a href="index.cgi?">Return to Main</a></td>
                                <td ALIGN=right width=9%><a href="help.html">Click here for help</a></td>
                   </tr></table>),br,br,
		"You have been emailed a verification code. Enter it into this form.",br,br,
		"$error",
		start_form,
		"Username: ",textfield('displayName'),br,br,
		"Verification Code: ",textfield('verCode'),br,br,
		submit('Verify'),
		end_form
		end_html;
		exit;
}


#!/usr/bin/env perl -wT
# Tsk: register.cgi

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

use vars qw [ $maintPath $org $admin ];

require "maint.cache";

my $displayName = param('displayName');
my $email = param('email');
my $passwd = param('passwd');
my $passwdVer = param('passwd-ver');

if (!$displayName && !$email && !$passwd && !$passwdVer) {
	&printForm;
}
&printForm("Error: Email is a mandatory field.<br><br>") 
		if (!$email);
&printForm("Error: Password is a mandatory field.<br><br>") 
		if (!($passwd || $passwdVer));
&printForm("Error: The passwords you entered did not match.<br><br>") 
		if (!($passwd eq $passwdVer));
&printForm("Error: Not a valid email address.<br><br>") 
		if (!($email =~ /.+\@.+\..+$/));

&connectDB;
my $out = &addUsr ($displayName,$email,$passwd);
&disconnectDB;
if ($out eq "Username already exists. Please try another username.\n") {
	&printForm("Error: $out<br><br>");
} elsif ($out eq "Verification Sent.") {
	print redirect(-uri=>"verify.cgi");
} else {
	print 
		header,
		"Error: Cannot add user. This might be a bug 
				please contact $admin and attach 
				any text displayed below: ",br,
		"$out::&addUsr ($displayName,$email,$passwd);",
		start_html("Task List for $ENV{SERVER_NAME}"),
		end_html;
}


sub printForm {
	my $error = shift;
	print 
		header,
		start_html(-title=>"Registration Page",
                                -style=>{'src'=>'interface.css'}),
                qq(<h1>Registration Page</h1>),
                qq(<table border=0 width=100%><tr>
                                <td WIDTH=9%></td>
                                <td ALIGN=center><a href="index.cgi?">Return to Main</a></td>
                                <td ALIGN=right width=9%><a href="help.html">Click here for help</a></td>
                   </tr></table>),p,
		start_form,
		"$error",
		"Username (optional)*: ",textfield('displayName'),br,br,
		"Email Address: ",textfield('email'),br,br,
		"Password**: ",password_field('passwd'),br,br,
		"Verify Password: ",password_field('passwd-ver'),br,br,
		<center>,submit('Submit'),br,br,
		"*Email will be used as username if you leave it blank.",br,
		"**Password must be alpha-numeric.",
		end_form,
		end_html;
		exit;
}

sub encrypt {
        my $pass = shift;
        my $alphaBeta = 'abcdefghijklmnopqrstuvwxyz1234567890';
        my @alphaBeta = split //, $alphaBeta;
        return crypt($pass,
                $alphaBeta[rand(@alphaBeta)] . $alphaBeta[rand(@alphaBeta)]);
}

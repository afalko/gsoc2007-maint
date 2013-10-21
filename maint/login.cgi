#!/usr/bin/env -wT
# Tsk: login.cgi

# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License

use CGI qw [ :standard ];
use CGI::Carp qw [ warningsToBrowser fatalsToBrowser ];
use strict;

my $displayName = param('displayName');
my $passwd = param('passwd');
my $error = param('error');
my $verified = param('justverified');
my $newPass = param('newPass');

if ($error eq "1") {
	&printForm("The username and password combination " .
		"you entered is incorrect.<br><br>");
}

if (!$passwd && !$displayName) {
	&printForm;
}

if (!$passwd) {
	&printForm("Error: You did not enter a password.<br><br>");
}

if (!$displayName) {
	&printForm("Error: You did not enter your username.<br><br>");
}

$passwd = &encrypt($passwd);

my $cookie = cookie( 	-name => "maint-auth",
			-expires => '1m',
			-value => "$displayName $passwd");

print redirect(-uri=>"index.cgi", -cookie=>$cookie);

sub printForm {
	my $error = shift;
	print
        	header,
		start_html(-title=>"Login Page",
                                -style=>{'src'=>'interface.css'}),
                qq(<h1>Login Page</h1>),
                qq(<table border=0 width=100%><tr>
                                <td WIDTH=9%></td>
                                <td ALIGN=center><a href="index.cgi?">Return to Main</a></td>
                                <td ALIGN=right width=9%><a href="help.html">Click here for help</a></td>
                   </tr></table>),br,br;
	print "You have been verified. You can now login.",br,br
			if ($verified eq "1");
	print "You have to login with your new password.",br,br
			if ($newPass eq "1");
	print
        	start_form,
        	"Username: ",textfield('displayName'),br,br,
        	"Password: ",password_field('passwd'),br,br,
		"$error",
        	<center>,submit('Login'),br,br,
        	end_form,
		"Don't have a login name? Please ",
		qq(<a href="register.cgi">register</a>.),br,
		"Forgot your password? Please go ",
		qq(<a href="pwrem.cgi">here</a>.),br,
		"Forgot to verify your email? Please ",
		qq(<a href="verify.cgi">verify</a>.),
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

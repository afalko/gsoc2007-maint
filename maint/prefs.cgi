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

use vars qw [ $maintPath $usr $org 
		$defmaintPP ];

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

my $prefs = `$maintPath --getPreferences=$usr`;
chomp($prefs);

$prefs =~ /(.*)/;

$defmaintPP = $1 if ($1);

my $taskPP = param('taskPP');
my $curPass = param('curPass');
my $newPass = param('newPass');
my $newPass2 = param('newPass2');

&printForm if (!($taskPP || $curPass || $newPass || $newPass2));
&printForm("", "You can't have an empty password.\n") if ($curPass && !$newPass);
&printForm("", "The new passwords that you entered do not match.\n") 
		if (!($newPass eq $newPass2));


$taskPP = untaint(qr(\d+), $taskPP);
$curPass = untaint(qr(\w+), $curPass);
$newPass = untaint(qr(\w+), $newPass);
$newPass2 = untaint(qr(\w+), $newPass2);

if ($taskPP) {
	my $out = `$maintPath --setPreferences=$usr,$taskPP`;
	print redirect(-uri=>"index.cgi");
}

if ($curPass) {
	$curPass = &encrypt($curPass);
	my $out = `$maintPath --changePassword=$usr,$curPass,$newPass`;
	if ($out eq "Password changed successfully\n") {
		print redirect(-uri=>"login.cgi?newPass=1");
	} else {
		&printForm("", $out);
	}
}

sub printForm {
	my $error = shift;
	my $error2 = shift;
	
	my $user = &unformat($usr);

	print 
		header,
		start_html(-title=>"$user\'s Preferences",
                                -style=>{'src'=>'interface.css'}),
                qq(<h1>$user\'s Preferences</h1>),
                qq(<table border=0 width=100%><tr>
                                <td WIDTH=9%></td>
                                <td ALIGN=center><a href="index.cgi?">Return to Main</a></td>
                                <td ALIGN=right width=9%><a href="help.html">Click here for help</a></td>
                   </tr></table>),br,br,
		"$error",
		start_form,
		"Tasks Per Page: ",textfield('taskPP', "$defmaintPP"),br,br,
		submit('Set Preferences'),
		end_form,br,
		qq(<B><BIG>),"_" x 96,qq(</BIG></B>),br,br,
		"$error2",br,br,
		start_form,
		"Current Password: ",password_field('curPass'),br,
		"New Password: ",password_field('newPass'),br,
		"Repeat New Password: ",password_field('newPass2'),br,br,
		submit('Set New Password'),
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

sub format {
        my $input = shift;

        my @chars = split //, $input;

        return "\\" . join ("\\", @chars);
}

sub unformat {
        my $input = shift;

        my @chars = split /\\/, $input;

        return join ("", @chars);
}


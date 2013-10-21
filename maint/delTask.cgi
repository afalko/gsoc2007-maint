#!/usr/bin/env perl -wT
# Tsk: oper.cgi

# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License

use CGI qw [ :standard ];
use CGI::Carp qw [ warningsToBrowser fatalsToBrowser ];
use Untaint;
use strict;

use lib "/var/run";

use vars qw [ $maintPath $org $usr $admin ];

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

my $del = param("delTsk");

$del = untaint(qr(\d+), $del);

if ($del) {
	my $out = `$maintPath --deleteTask=$del,$usr`;
	&printError("Error: $out: <br><br>") if (!($out eq "Deleted Successfully.\n"));
	print redirect(-uri=>"index.cgi?taskDeleted=1"); # Premature redirect since the 
							 # other operations are 
							 # irrelevent now.
}

print redirect(-uri=>"index.cgi");

sub printError {
	my $error = shift;
	print
                header,
		start_html(-title=>"Delete Task for $org",
                                -style=>{'src'=>'interface.css'}),
                qq(<h1>Delete Task for $org</h1>),
                qq(<table border=0 width=100%><tr>
                                <td width=9%></td>
                                <td ALIGN=center><a href="index.cgi?">Return to Main</a></td>
                                <td ALIGN=right width=9%><a href="help.html">Click here for help</a></td>
                   </tr></table>),br,br,
		"It appears that an error has occurred when deleting a task",
		"Please notify $admin and attach the below output (if any):",br,br,
                "$error",
                end_html;
		exit;
}

sub format {
        my $input = shift;

        my @chars = split //, $input;

        return "\\" . join ("\\", @chars);
}

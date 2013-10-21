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

my $maintID = param("maintID");
$maintID = untaint(qr(\d+), $maintID);
my $stat = param("status_$maintID");
my $statWas = param("statWas");
my $vote = param("vote_amount_$maintID");
my $oper = param("operation_$maintID");
my $del = param("del_$maintID");

$stat = untaint(qr((Reported)|(Working)|(Abandoned)|(CommitReady)|(Committing)|(Committed)), $stat);
$statWas = untaint(qr((Reported)|(Working)|(Abandoned)|(CommitReady)|(Committing)|(Committed)), $statWas);
$vote = untaint(qr(\d\d?), $vote) if ($vote);
$oper = untaint(qr(\+|\-), $oper);
#$del = untaint(qr(0|1), $del) if ($del);

if ($del) {
	my $out = `$maintPath --deleteTask=$maintID,$usr`;
	&printError($out) if (!($out eq "Deleted Successfully.\n"));
	print redirect(-uri=>"index.cgi?taskDeleted=1"); # Premature redirect since the 
							 # other operations are 
							 # irrelevent now.
}

if (!($stat eq $statWas)) {
	my $out = `$maintPath --changeStatus=$maintID,$stat,$usr`;
	&printError($out) if (!($out eq "Status changed successfully.\n"));
}

if ($vote > 0) {
	my $out = `$maintPath --vote=$oper$vote,$maintID,$usr`;
	&printError($out) if (!($out =~ /Vote went through\n$/));
}

print redirect(-uri=>"index.cgi");

sub printError {
	my $error = shift;
	print
                header,
                start_html("Error Page for $org"),
		qq(<h1>Error Page for $org</h1>),
                qq(<table border=0 width=100%><tr>
                                <td WIDTH=9%></td>
                                <td ALIGN=center><a href="index.cgi?">Return to Main</a></td>
                                <td ALIGN=right width=9%><a href="help.html">Click here for help</a></td>
                   </tr></table>),p,
		"If you find yourself on this page, please contact ",
		"$admin and include the below output (if any): ",p,
                "$error",
                end_html;
		exit;
}

sub format {
        my $input = shift;

        my @chars = split //, $input;

        return "\\" . join ("\\", @chars);
}

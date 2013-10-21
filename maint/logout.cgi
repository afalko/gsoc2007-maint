#!/usr/bin/env perl -wT
# Tsk: login.cgi

# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License

use CGI qw [ :standard ];
use CGI::Carp qw [ warningsToBrowser fatalsToBrowser ];
use strict;

# Create empty cookie
my $cookie = cookie( 	-name => "maint-auth",
			-expires => 'now',
			-value => "");

print redirect(-uri=>"index.cgi", -cookie=>$cookie);

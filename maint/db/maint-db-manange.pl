#!/usr/bin/perl -w 
# Copyright 2007 Andrey Falko
#
# Program is distributed under the terms
# of the GNU General Public License


use strict;

use DBI;

use vars qw [ $dbType $dbName $dbUsr $dbPasswd $libdir ];

my $confFile = "/home/andrey/tsk/bin/tsk.conf";

open CONFIG, $confFile
		or die "Could not open config file: $!";
my @config = <CONFIG>;

SWITCH: for (@config) {
	/^dbType\s*=\s*(.+)\s*$/	&& do { $dbType = $1; next };
	/^dbName\s*=\s*(.+)\s*$/	&& do { $dbName = $1; next };
	/^dbUsr\s*=\s*(.+)\s*$/		&& do { $dbUsr = $1; next };
	/^dbPasswd\s*=\s*(.+)\s*$/	&& do { $dbPasswd = $1; next };
	/^libdir\s*=\s*(.+)\s*$/	&& do { $libdir = $1; next };
}
close CONFIG;
@config = ();

if ($dbType eq "sqlite") {
	die "No extra configuration needed for sqlite.\n";
} elsif ($dbType eq "mysql") {
	if (!($dbUsr || $dbPasswd || $dbName)) {
		die "You must supply the correct database options in ".
		"$confFile. Please read comments in $confFile for more ".
		"information.\n";
	}
	print "Please provide your mysql administrator username (Default: root): ";
	chomp (my $root = <STDIN>);
	$root = 'root' if (!$root);
	print "Please provide your mysql password for $root: ";
	system('stty','-echo');
	chomp (my $passwd = <STDIN>);
	system('stty','echo');

	my $host = 'localhost';

	my $dbh = DBI->connect("dbi:$dbType:mysql", "$root", "$passwd", { RaiseError => 1, AutoCommit => 1 })
	                or die "Connection to database failed: $DBI::errstr";
	my $sth = $dbh->prepare("GRANT ALL PRIVILEGES ON $dbName\.* TO \'$dbUsr\'@\'$host\' 
			IDENTIFIED BY \'$dbPasswd\' WITH GRANT OPTION");
	$sth->execute();
	
	my $flu = $dbh->prepare("FLUSH PRIVILEGES");
	$flu->execute();

	$dbh->disconnect;

	system ("mysql --password=$dbPasswd -u $dbUsr < $libdir/blankdb.mysql") 
			or die "Could not make database: $!";
} else {
	die "The database (dbType = $dbType) specified in $confFile is ".
	"either not yet supported or entered incorrectly. Please read ".
	"comments in $confFile for more information.\n";
}

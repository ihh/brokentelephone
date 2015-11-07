#!/usr/bin/perl

use strict;
use warnings;

use FindBin;
use lib $FindBin::Bin;

use Newick;

die "Usage: $0 <reference tree file> <test tree files...>\n" unless @ARGV > 1;

my $reftree = Newick->from_file (shift @ARGV);
for my $testfile (@ARGV) {
    my $testtree = Newick->from_file ($testfile);
    $testfile =~ s/\s/_/g;
    print $testfile, " ", $reftree->robinson_foulds($testtree), "\n";
}

#!/usr/bin/env perl -w

use Newick;

die "Usage: $0 <max_depth> <texfile>" unless @ARGV == 2;

my $max_depth = shift;
my $texfile = shift;

open T, "<$texfile";
while (<T>) {
    if (/handout.(\d+).*% (\d+)/) {
	$name{$2} = $1;
    }
}

sub tree {
    my ($depth) = @_;
    return $depth>0 ? ("(".tree($depth-1).",".tree($depth-1).")") : "";
}

my $tree = Newick->parse (tree($max_depth).";");

for $n (0..@{$tree->node_name}-1) {
    $tree->node_name->[$n] = $name{$n} if exists $name{$n};
}

print $tree->to_string;

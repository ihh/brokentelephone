
all: bin/evolve sheet.pdf.open

bin/%: %.cc
	mkdir -p bin
	g++ -g -lstdc++ -o $@ $<
#	g++ -g -O3 -lstdc++ -o $@ $<

# Edit Makefile.defs to contain the dictionaries, initial phrases, and evolution rules
include Makefile.defs

# autogen quotes
%.tex: %.src
	cat $< | perl -e '@x=<>;@y=(0..@x-1);for$$i(0..@x-1){$$j=int(rand(@x-$$i))+$$i;@x[$$i,$$j]=@x[$$j,$$i];@y[$$i,$$j]=@y[$$j,$$i];chomp$$x[$$i];print$$x[$$i],"\t",$$y[$$i],"\n"}' | perl -e '$$n=0;while(<>){if(/     /){s/\s+/ /g;if(/(.*)\s(\d+)\s*$$/){print"\\handout{",++$$n,"}{$$1}  % $$2\n"}}}' >$@

# consensus. hardwired for 32 leaves (5 branches, hence 5 spaces of indent)
%.consensus: %
	grep "     " $< | perl -e 'while(<>){@f=split;for$$n(0..@f-1){$$c[$$n]->{$$f[$$n]}++}}for$$n(0..@c-1){%c=%{$$c[$$n]};@w=sort{$$c{$$a}<=>$$c{$$b}}keys%c;print$$w[@w-1]," "}' >$@

%.cols: %
	egrep "^     " $< | perl/cols >$@

# true sentence
%.root: %
	cat $< | head -1 >$@

# Tree
%.tree: %.tex
	./recover_tree.pl 5 $< >$@

# PDFs
sheet.pdf: sheet.tex TEXT.tex
	pdflatex $<

sheet.pdf.open: sheet.pdf
	open $<

TEXT.tex: $(TEXT).tex
	cp $< $@

# dictionary
DICT = scowl.txt

# evolve syntax:
# bin/evolve [dictionary file] [mean edits per word, per branch] [max edits per letter, per branch] [symmetric tree depth, in branches] [root sentence, dictionary words separated by spaces...]

# default settings
#EVOLVE = bin/evolve $(DICT) .8 .5 5
EVOLVE = bin/evolve $(DICT) .8 .5 5
EVOLVE_SLOW = bin/evolve $(DICT) .7 .5 5

# Example of use:
#  $(EVOLVE) The sky above the port was the color of television tuned to a dead channel >GIBSON
#  make TEXT=GIBSON sheet.pdf

# keep intermediates
.SECONDARY:

# no suffix rules
.SUFFIXES:

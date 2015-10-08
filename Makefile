
all: evolve sheet.pdf.open

%: %.cc
	g++ -O3 -lstdc++ -o $@ $<

# Makefile.defs contains the dictionaries, initial phrases, and evolution rules
include Makefile.defs

# autogen quotes
%.tex: %
	cat $< | perl -e '@x=<>;@y=(0..@x-1);for$$i(0..@x-1){$$j=int(rand(@x-$$i))+$$i;@x[$$i,$$j]=@x[$$j,$$i];@y[$$i,$$j]=@y[$$j,$$i];chomp$$x[$$i];print$$x[$$i],"\t",$$y[$$i],"\n"}' | perl -e '$$n=0;while(<>){if(/     /){s/\s+/ /g;if(/(.*)\s(\d+)\s*$$/){print"\\handout{",++$$n,"}{$$1}  % $$2\n"}}}' >$@

# consensus. hardwired for 32 leaves (5 branches, hence 5 spaces of indent)
%.consensus: %
	grep "     " $< | perl -e 'while(<>){@f=split;for$$n(0..@f-1){$$c[$$n]->{$$f[$$n]}++}}for$$n(0..@c-1){%c=%{$$c[$$n]};@w=sort{$$c{$$a}<=>$$c{$$b}}keys%c;print$$w[@w-1]," "}' >$@

# PDFs
sheet.pdf: sheet.tex TEXT.tex
	pdflatex $<

sheet.pdf.open: sheet.pdf
	open -a /Applications/Preview.app $<

TEXT.tex: $(TEXT).tex
	cp $< $@

# keep intermediates
.SECONDARY:

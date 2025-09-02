# brokentelephone

Phylogenetic alignment parlor game.

How to build:

- You'll need Python, and LaTeX, and Simon Willison's [llm](https://github.com/simonw/llm), possibly an API key
- Create a file `Makefile.defs` that has the following:
    - A line saying `TEXT = SomeFilenamePrefix`
    - A rule to build a file `SomeFilenamePrefix.src` using the [telephone_tree.py](https://github.com/ihh/brokentelephone/blob/master/telephone_tree.py) script
- Type `make`

Check out [Makefile.defs.example](https://github.com/ihh/brokentelephone/blob/master/Makefile.defs.example) for examples.
For example, your `Makefile.defs` might look like this:

    TEXT = ORTON
    
    ORTON.src:
    	python telephone_tree.py "Cleanse my heart. Give me the ability to rage correctly" --prompt-distance '4-8' >$@

(The quote is from [Joe Orton's diaries](https://en.wikipedia.org/wiki/Joe_Orton).)
An example handout generated from this source text is [here](https://github.com/ihh/brokentelephone/blob/master/example.pdf).
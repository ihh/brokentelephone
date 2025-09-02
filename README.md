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

    TEXT = GIBSON

    GIBSON.src:
    	python telephone_tree.py "The sky above the port was the color of television tuned to a dead channel" --prompt-distance '6-12' >$@

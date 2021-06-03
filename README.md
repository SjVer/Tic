# Tic
An attempt at making a simple programming language
<br/>

### How It Works
Tic is a compiled language. The compiler itself is written completely in Python and really only converts the Tic code to c code, which in turn gets compiled by a c compiler.

The compiler consists out of 4 "modules":
- The main script
- The lexer
- The parser
- The emitter

Anyone that did some research into what's behind a compiler will know what these do, however, I'll explain it in short for the ones that don't. <br/> <br/>
The main script is what ties all of it together. This is the script you need to run when compiling your own script. (It comes with a few options, run `./ticcomp --help` to see those.)

The lexer has the job of turning the Tic script into something the rest of the compiler can work with. It removes whitespaces and comments, and replaces all keywords, strings, etc. with tokens.

Then, the parser uses those tokens to generate lines of c code. During this process it also makes sure that the code that has been inserted is valid and does not contain any errors.

The rest of the job is the emitter's. This module simply takes the lines generated by the parser to construct the full c script.

All that's left then is for the main script to compile that c script using e.g. gcc and voila! Your Tic executable is done.


### Documentation
The full documentation is [here](Documentation.md) <br/>
Code examples can be found in /test

### Ticide
The IDE for Tic, Ticide can be downloaded from the releases page. <br/>
See `Editor.md` for more information.

### Credits
[Sjoerd Vermeulen](https://github.com/SjVer) (me) <br/>
[This tutorial](http://web.eecs.utk.edu/~azh/blog/teenytinycompiler1.html) (really reccomend it!)
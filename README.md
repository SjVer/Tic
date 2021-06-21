# Tic
An attempt at making a simple programming language.
<br/>

### What is Tic really?
First things first; Tic is a recreational project. I am working on this programming language for nothing but fun, and thus it is unfair to compare it with other languages. Other than that Tic is a transpiled language. It is a little typed, as you do not have to declare variables with a specific type, but the language detects that for you. This means that variables declared with a string value will remain strings. E.g. a number assigned to a string variable will be converted into a string. (e.g. 1 will become "1".) Another thing to note is that there's no such thing as scopes. When a variable is declared it can be used for the rest of the script. Any wrong code will probably be detected by the transpiler itself but on some rare occasion the assigned c compiler will be the one catching it. Lastly, both the transpiler and IDE included in this project are being written on a Linux device. I honestly cannot guarantee that it'll work on anything else. The compiling part probably won't.


### Why Tic?
There's a good few reasons why Tic is the way it is, why it's unique amongst other languages and why it's good. <br/><br/>
First of all, Tic is very intuitive. Even when completely new to this language you should be able to easily see what a script does. Take an example of a function: (please note that function parameters or not yet supported. They're being worked on.)
```
Function myfunction Takes
	{number} x, {number} y
Does
	Print "x plus y is: "
	PrintLine x + y
EndFunction

Call myfunction With 2, 3
```
This clear and self-explanitory syntax can be a lot more accessible for starting programmers than e.g. C's function syntax:
```c
#include <stdio.h>

void myfunction(int x, int y) {
	printf("x plus y is: %d", x+y);
}

int main(void) {
	myfunction(2, 3);
	return 0;
}
```
<br/>
Another reason why Tic looks the way it does is (of course) because I like it that way. It's unique and charming in a way not many other languages are. And what it lacks in functionality so far, it makes up for with being a lot of fun to make.


### How It Works
Tic is a transpiled language. The compiler itself is written completely in Python and really only converts the Tic code to c code, which in turn gets compiled by a c compiler.

The compiler consists out of 4 "modules":
- The main script
- The lexer
- The parser
- The emitter

Anyone that did some research into what's behind a compiler will know what these do, however, I'll explain it in short for the ones that don't. <br/> <br/>
The main script is what ties all of it together. This is the script you need to run when compiling your own script. (It comes with a few options, run `ticcomp --help` or `./ticcomp --help` depending on whether you're using the package or script, to see those.)

The lexer has the job of turning the Tic script into something the rest of the compiler can work with. It removes whitespaces and comments, and replaces all keywords, strings, etc. with tokens.

Then, the parser uses those tokens to generate lines of c code. During this process it also makes sure that the code that has been inserted is valid and does not contain any errors.

The rest of the job is the emitter's. This module simply takes the lines generated by the parser to construct the full c script.

All that's left then is for the main script to compile that c script using e.g. gcc and voila! Your Tic executable is done.

### Compiler Options
The ticcomp compiler can be ran with a few different optional arguments:
* `-o FILE / --output FILE`   - specifies the output file 
* `-c PATH / --compiler PATH` -  specifies the c compiler
* `-v / --verbose`            - runs the compiler in verbose mode
* `-r / --run`                - runs the compiled executable after compilation
* `-p / --preserve-temp`      - preserves the temporary c file
* `-g / --generate-header`    - generates the c header file for the script (as only output)

### Documentation
The full documentation is [here](Documentation.md) <br/>
Code examples can be found in the `test` directory.

### TicIDE
The IDE for Tic. TicIDE can be downloaded from the releases page. <br/>
See `Editor.md` for more information.

### Credits
[Sjoerd Vermeulen](https://github.com/SjVer) (me) <br/>
[This tutorial](http://web.eecs.utk.edu/~azh/blog/teenytinycompiler1.html) (really reccomend it!)
<br/>
<br/>
By the way, if you know of anything significant that uses the .tic extension please let me know! Thanks!

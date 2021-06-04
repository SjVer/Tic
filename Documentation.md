# Tic Documentation
All currently implemented features are documented here.
Example scripts can be found in the 'test/' directory.
<br/>
<br/>
## Syntaxes
**Label** <br/>
Defines a label to jump to using `GoTo`
```
Label <name>
```
<br/>

**GoTo** <br/>
Jumps to predefined label defined with `Label`
```
GoTo <label>
```
<br/>

**Print** <br/>
Prints a string or expression to the console
```
Print "<string>"
Print <number>
Print <variable>
Print <expression>
```
<br/>

**PrintLine** <br/>
Similar  to `Print`, but with a trailing newline.
```
PrintLine "<string>"
PrintLine <number>
PrintLine <variable>
PrintLine <expression>
```
<br/>

**Declare** <br/>
Declares a new variable. The type will be automatically detected and cannot be changed throughout the script.
```
Declare <name> = <number>
Declare <name> = "<string>"
Declare <name> = <bool>
```
<br/>

**Input** <br/>
Waits for user input and assigns it to a variable. This variable must have been declared.
```
Input <variable>
```
<br/>

**Assign** <br/>
Assigns a value to a variable, this variable must have been declared.
```
Assign <variable> = <value>
```
<br/>

**If** <br/>
Executes a block of code if the given comparison results to true. This comparison can contain `Or` and `And` statements as well.
```
If <comparison> Then
	<code to execute>
EndIf

If <comparison> Or <comparison> Then
	<code to execute>
EndIf

If <comparison> And <comparison> Then
	<code to execute>
EndIf
```
<br/>

**Then** <br/>
See `If`
<br/> <br/>

**EndIf** <br/>
See `If`
<br/> <br/>

**While** <br/>
Loops a block of code while the given comparison results to true.
```
While <comparison> Repeat
	<code to execute>
EndWhile
```
<br/>

**Repeat** <br/>
See `While`
<br/> <br/>

**EndWhile** <br/>
See `While`
<br/> <br/>

**For** <br/>
Repeats a block of code using a variable that starts at a given value, ends at a given value and increments by a given value. (As of right now the end value must be larger than the start value.)
```
For <variable>, <start value>, <end value>, <increment> Do
	<code to execute>
EndFor
```
<br/>

**Do** <br/>
See `For`
<br/> <br/>

**EndFor** <br/>
See `For`
<br/> <br/>

**Function** <br/>
Declares a function. This function can be called once declared, just like in most other languages.
As of right now parameters and the passing of those is not yet supported, but it is being worked on.
(The use of parameters is not blocked, but the compiling will result in errors.)
```
Function <name> Does
	<code to execute>
EndFunction
```
When parameters are implemented fully the syntax for a function with variables will be as follows:
```
Function <name> Takes <parameters seperated by a comma> Does
	<code to execute>
EndFunction
``` 
<br/>

**Does** <br/>
See `Function`
<br/> <br/>

**EndFunction** <br/>
See `Function`
<br/> <br/>

**Takes** <br/>
See `Function` (not yet implemented)
<br/> <br/>

**Call** <br/>
Calls a predeclared function. As of right now passing parameters is not yet supported, but it is being worked on.
(The use of parameters is not blocked, but the compiling will result in errors.)
```
Call <name>
```
When parameters are implemented fully the syntax for a calling a function with parameters will be as follows:
```
Call <name> With <variables seperated by a comma>
``` 
<br/>

**With** <br/>
See `Call`
<br/> <br/>

**Exit** <br/>
Terminates the program with the given exit code
```
Exit <number>
Exit <expression>
Exit <variable>
```
<br/>

**Sleep** <br/>
Pauses for a given amount of seconds
```
Sleep <number>
Sleep <expression>
Sleep <variable>
```
<br/>


## Supported operators
All supported operators behave as normal <br/>

| <!-- -->    |
|--- |
| =  |
| +  |
| -  |
| *  |
| /  |
| == |
| != |
| >  |
| >= |
| <  |
| <= |
<br/>

## miscellaneous Tokens
| | | |
|-|-|-|
| EOF | End of file |
| NEWLINE | Newline |
| NUMBER | Number |
| IDENT | Variable |
| STRING | String |
| COMMA | Comma |
| BOOL | Boolean |
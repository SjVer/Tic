# AttemptLang Documentation
All currently implemented features are documented here.
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

**Input** <br/>
Waits for user input and assigns it to a variable
```
Input <variable>
```
<br/>

**Assign** <br/>
Assigns a value to a variable
```
Assign <variable> = <value>
```
<br/>

**If** <br/>
Executes a block of code if the given comparison results to true
```
If <comparison> Then
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
Loops a block of code while the given comparison results to true
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
For <variable> <start value> <end value> <increment> Do
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
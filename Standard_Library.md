# Standard Library
This is a list of all modules in Tic's standard library and their functions and variables. These modules can be imported using e.g. `Use math`, or `Use all` if you want to import all of them.

### math
#### Functions
**pow**:  Takes two numbers, base and power. Returns the result.
**sqrt**: Returns the square root of the given number.
**sin**:  Returns the sine of the given number. 
**cos**:  Returns the cosine of the given number. 
**tan**:  Returns the tangent of the given number. 
**log**:  Returns the logarithm of the given number. 
**round**: Takes two numbers. Returns the first number rounded to the amount of decimals given as the second number.
#### Variables
**PI**:  π = 3.141592…
**E**:   e = 2.718281…	
**TAU**: τ = 6.283185…

### file
#### Functions
**createfile**: Takes a path (string) and creates that file.
**removefile**: Takes a path (string) and removes that file.
**writefile**:  Takes a path (string) and text (string) and writes that text to the file.
**readfile**:  Returns the contents of the file given as a string (path).
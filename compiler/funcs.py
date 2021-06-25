import sys
import os
from lex import *
import random
import string
import tempfile
# from tokens import DataTypes

def randStr(N):
	# generates a random string of length N
	return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(N))

# "PRINT" (expression | string)
def funcPRINT(self, TokenType):
	self.nextToken()

	if self.checkToken(TokenType.STRING):
		# Simple string, so print it.
		self.emitter.emitLine("printf(\"" + self.curToken.text + "\");")
		self.nextToken()

	elif self.checkToken(TokenType.NUMBER) and (self.checkPeek(TokenType.NEWLINE) or self.checkPeek(TokenType.EOF)):
		# number
		self.emitter.emitLine("printf(\"" + self.curToken.text + "\\n\");")
		self.nextToken()

	elif self.checkToken(TokenType.IDENT) and (self.checkPeek(TokenType.NEWLINE) or self.checkPeek(TokenType.EOF)):
		# ident
		
		# check if defined
		if not self.checkVar(self.curToken.text):
			self.abort(f"Print: Attempted to print undeclared variable '{self.curToken.text}'", self.curToken.line)
		
		# detect variable type and emit based off that
		if self.checkVar(self.curToken.text, TokenType.STRING):
			# var contains string
			self.emitter.emitLine("printf(\"%" + f"s\", {self.curToken.text});")

		elif self.checkVar(self.curToken.text, TokenType.NUMBER):
			# var contains number
			# the emitted code checks if number is int or float and prints accordingly
			self.emitter.emitLine(f"if(roundf({self.curToken.text}) == {self.curToken.text})"+'{')
			self.emitter.emitLine(f"printf(\"%d\", (int){self.curToken.text});")
			self.emitter.emitLine("}else{")
			# self.emitter.emitLine(f"printf(\"%.3f\", {self.curToken.text});"+'}')
			i = randStr(10)
			a = randStr(10)
			self.emitter.emitLine("int "+i+"=1;")
			self.emitter.emitLine("while(1){")
			self.emitter.emitLine("float "+a+"="+self.curToken.text+"*powf(10,"+i+");")
			self.emitter.emitLine("if("+a+"==(int)"+a+")")
			self.emitter.emitLine("break;")
			self.emitter.emitLine(i+"++;}")
			self.emitter.emitLine("printf(\"%."+"*f\","+i+","+self.curToken.text+");}")

		elif self.checkVar(self.curToken.text, TokenType.BOOL):
			self.emitter.emitLine("printf(\"%" + f"s\", {self.curToken.text}?\"true\":\"false\");")
		# self.emitter.emitLine("char *string = (char *)" + self.curToken.text + ";")
		# self.emitter.emitLine("printf(\"%" + "s\", " + "string" + ");")
		self.nextToken()

	else:
		# Expect an expression and print the result as a float.
		# self.emitter.emit("printf(\"%" + ".3f\", (float)(")
		tempvar = randStr(10)
		self.emitter.emit("float "+tempvar+"=")
		self.expression()
		self.emitter.emitLine(";")
		#
		self.emitter.emitLine(f"if(roundf({tempvar}) == {tempvar})"+'{')
		self.emitter.emitLine(f"printf(\"%d\", (int){tempvar});")
		self.emitter.emitLine("}else{")
		# self.emitter.emitLine(f"printf(\"%.3f\", {self.curToken.text});"+'}')
		i = randStr(10)
		a = randStr(10)
		self.emitter.emitLine("int "+i+"=1;")
		self.emitter.emitLine("while(1){")
		self.emitter.emitLine("float "+a+"="+tempvar+"*powf(10,"+i+");")
		self.emitter.emitLine("if("+a+"==(int)"+a+")")
		self.emitter.emitLine("break;")
		self.emitter.emitLine(i+"++;}")
		self.emitter.emitLine("printf(\"%."+"*f\","+i+","+tempvar+");}")

# "PRINTLN" (expression | string)
def funcPRINTLN(self, TokenType):
	funcPRINT(self, TokenType)
	self.emitter.emitLine('printf(\"\\n\");')

# "IF" (comparison ["OR" comparison]) "THEN" block "ENDIF"		
def funcIF(self, TokenType, nested=False):
	self.nextToken()
	self.emitter.emit("if((")
	self.comparison()

	self.match(TokenType.THEN)
	self.nl()
	self.emitter.emitLine(")){")

	scope = self.downScope()

	# Zero or more statements in the body.
	while not self.checkToken(TokenType.ENDIF):
		self.statement()
		if self.checkToken(TokenType.ELIF):
			self.emitter.emit('}else ')
			funcIF(self, TokenType, True)
		elif self.checkToken(TokenType.ELSE):
			self.emitter.emitLine("}else{")
			self.nextToken()
			self.nextToken()

	self.match(TokenType.ENDIF, not nested)
	self.emitter.emitLine("}" if not nested else "")
	self.upScope()

# "WHILE" comparison "REPEAT" block "ENDWHILE"
def funcWHILE(self, TokenType):
	self.nextToken()
	self.emitter.emit("while((")
	self.comparison()

	self.match(TokenType.REPEAT)
	self.nl()
	self.emitter.emitLine(")){")

	self.downScope()

	self.parsing_loop = True
	# Zero or more statements in the loop body.
	while not self.checkToken(TokenType.ENDWHILE):
		self.statement()

	self.match(TokenType.ENDWHILE)
	self.parsing_loop = False
	self.emitter.emitLine("}")
	self.upScope()

# "BREAK"
def funcBREAK(self, TokenType):
	if not self.parsing_loop:
		self.abort('Break can only be used inside a For- or While-loop')
	else:
		self.emitter.emitLine('break;')
	self.nextToken()

# "LABEL" ident
def funcLABEL(self, TokenType):
	self.nextToken()

	# Make sure this label doesn't already exist.
	if self.curToken.text in self.labelsDeclared:
		self.abort("Label: Label already exists: " + self.curToken.text, self.curToken.line)
	self.labelsDeclared.add(self.curToken.text)

	self.emitter.emitLine(self.curToken.text + ": ;")
	self.match(TokenType.IDENT)

# "GOTO" ident
def funcGOTO(self, TokenType):
	self.nextToken()
	self.labelsGotoed.add(self.curToken.text)
	self.emitter.emitLine("goto " + self.curToken.text + ";")
	self.match(TokenType.IDENT)

# "SET" ident = expression
def funcSET(self, TokenType):
	self.nextToken()
	
	varname = self.curToken.text
	if not self.checkVar(varname):
		self.abort(f"Set: Variable {varname} not declared", self.curToken.line)
	self.emitter.emit(varname + ' = ')

	vartype = self.getVarType(varname)

	self.nextToken()
	self.match(TokenType.EQ)

	# check if type is correct (excuse idents)
	if self.curToken.kind != self.getVarType(varname) and not self.checkToken(TokenType.IDENT):
		self.abort('Set: Attempted to assign a ' + self.curToken.kind.name.lower() + ' to a variable declared with type ' + self.getVarType(varname).name.lower() + f' ({self.curToken.text} to {varname})', self.curToken.line)

	# emit shit
	if self.getVarType(varname) == TokenType.STRING:
		self.emitter.emit("\"" + self.curToken.text + "\";")
		self.match(self.getVarType(varname))
		# self.nextToken()

	elif self.getVarType(varname) != TokenType.NUMBER:
		self.emitter.emit(self.curToken.text + ';')
		self.match(self.getVarType(varname))
		# self.nextToken()

	# elif self.variablesDeclared[varname]

	else:
		# can be either number or expression
		if not self.checkPeek(TokenType.NEWLINE) and not self.checkPeek(TokenType.EOF):
			# expression
			self.expression()
			self.emitter.emit(';')
		else:
			self.emitter.emit(self.curToken.text + ';')
			self.match(TokenType.NUMBER)
			# self.nextToken()

# "DECLARE" type ident = (expression | string | number)
def funcDECLARE(self, TokenType):
	self.nextToken()

	ishinted = False
	hinttoken = None
	templine = ""

	dontcontinue = False
	# self.emitter.emit(self.curToken.text + " = ")

	if self.checkToken(TokenType.HINT):
		# type is hinted. no need for init value
		ishinted = True
		hinttoken = self.curToken

		if self.curToken.text == 'string':
			vartype = TokenType.STRING
		elif self.curToken.text == 'number':
			vartype = TokenType.NUMBER
		elif self.curToken.text == 'bool':
			vartype = TokenType.BOOL

		## self.emitter.emit(self.curToken.emittext + " ")
		templine += self.curToken.emittext + " "
		self.nextToken()

	varname = self.curToken.text
	##  self.emitter.emit(varname)
	templine += varname
	self.match(TokenType.IDENT, False)

	if not ishinted:
		self.nextToken()
		self.match(TokenType.EQ)
		templine += "="
		##  self.emitter.emit("=")

	elif not self.checkPeek(TokenType.NEWLINE) and not self.checkPeek(TokenType.EOF):
		# init value given
		self.nextToken()
		# print(self.peekToken.kind)
		self.match(TokenType.EQ)
		templine += "="
		## self.emitter.emit("=")
	else:
		self.nextToken()
		dontcontinue = True

	if not dontcontinue:# and not ishinted:
		# if self.checkToken(TokenType.STRING):
		if self.checkToken(TokenType.STRING):
			# variable contains string
			vartype = TokenType.STRING
			##  self.emitter.emit("\"" + self.curToken.text + "\"")
			if not ishinted:
				templine = "char *" + templine
				vartype = TokenType.STRING
			templine += "\""+self.curToken.text+"\""
			self.nextToken()

		elif self.checkToken(TokenType.BOOL):
			# variable contains boolean
			vartype = TokenType.BOOL
			if not ishinted:
				templine = "bool " + templine
				vartype = TokenType.BOOL
			templine += self.curToken.text
			##  self.emitter.emit(self.curToken.text)
			self.nextToken()
				
		else:
			# vartype = TokenType.NUMBER
			if not self.checkPeek(TokenType.NEWLINE) and not self.checkPeek(TokenType.EOF):
				# expression
				if not ishinted:
					templine = "float " + templine
					vartype = TokenType.NUMBER
				templine += self.get_current_expression(True)
				##  self.expression()
			else:
				# number
				## self.emitter.emit(self.curToken.text)
				if not ishinted:
					templine = "float " + templine
					vartype = TokenType.NUMBER
				templine += self.curToken.text
				self.nextToken()

	elif not dontcontinue and ishinted:
		templine += self.curToken.text
		self.match(vartype)

	#  Check if ident exists in symbol table. If not, declare it.
	if not self.checkVar(varname):

		# if self.parsing_function:
		# 	self.curFuncVars[varname] = vartype
		# 	self.emitter.emitLine(templine + ';')
		if self.generating_header:
			self.variablesDeclared[varname] = vartype
			self.emitter.headerLine(templine + ';')
		else:
			# self.variablesDeclared[varname] = vartype
			self.addVar(varname, vartype)
			# self.emitter.emitLine("// DECLARATION OF \""+varname+"\"", True)
			## self.emitter.emitBeforeCode(templine + ';\n')
			# self.emitter.headerLine(" // DECLARED AT LINE "+str(self.curToken.line)+':', True)
			# self.emitter.headerLine(templine + ';')
			self.emitter.emitLine(templine + ';')

	# var already exists. abort
	else:
		self.abort(f"Declare: Variable '{varname}' is already declared.", self.curToken.line)

	# self.emitter.emitLine(";")
	# self.nextToken()
	# self.nl()

# "INPUT" ident
def funcINPUT(self, TokenType):
	self.nextToken()

	varname = self.curToken.text

	# check variable exists else abort
	if not self.checkVar(varname):
		self.abort("Input: Attempted to assign input to undeclared variable " + varname, self.curToken.line)

	vartype = self.variablesDeclared[varname]

	# generate the right scanf format for each data type
	if vartype == TokenType.NUMBER:
		self.emitter.emitLine("scanf(\"%" + "f\", &" + varname + ");")

	elif vartype == TokenType.STRING:
		tempstr = randStr(10)
		self.emitter.emitLine("char "+tempstr+"[1000];")
		self.emitter.emitLine("scanf(\"%" + f"s\", &{tempstr});")
		self.emitter.emitLine(varname+"="+tempstr+";")
		# self.emitter.emitLine("scanf(\"%" + "s\", " + varname + ");")

	elif vartype == TokenType.BOOL:
		# declare and scan a temporary variable to catch the user input
		# so we can check it later (but first convert to lowercase)
		tempvar = "tempvar"+randStr(10)
		self.emitter.emitLine(f"char {tempvar}[5];")
		self.emitter.emitLine("scanf(\"%"+f"s\", {tempvar});")
		# convert to lowercase using:
		# for(int i = 0; str[i]; i++){
		#	str[i] = tolower(str[i]);
		# }
		tempint = "tempint"+randStr(5)
		self.emitter.emitLine(f"for(int {tempint} = 0; {tempvar}[{tempint}]; {tempint}++)"+"{")
		self.emitter.emitLine(f"{tempvar}[{tempint}] = tolower({tempvar}[{tempint}]);"+"}")
		# the rest (compare the lowercase input with 'true' and return true if they are the same, else false)
		self.emitter.emitLine(f"if(strcmp({tempvar}, \"true\")==0)"+"{")
		self.emitter.emitLine(varname + "=true;")
		self.emitter.emitLine("}else{")
		self.emitter.emitLine(varname + "=false;}")

	self.match(TokenType.IDENT)

# "EXIT" (expression | number | ident)
def funcEXIT(self, TokenType):
	self.nextToken()
	
	if self.checkToken(TokenType.NUMBER):
		if not self.checkPeek(TokenType.NEWLINE) and not self.checkPeek(TokenType.EOF):
			# expression
			self.emitter.emit("exit(")
			self.expression()
			self.emitter.emitLine(");")
		
		else:
			# Simple number, exit with it.
			self.emitter.emitLine("exit(" + self.curToken.text + ");")
			self.nextToken()
			
	elif self.checkToken(TokenType.IDENT):
		# ident
		self.emitter.emitLine("exit(" + self.curToken.text + ");")
		self.nextToken()
	else:
		self.abort(f"Exit: Expected numeric exit code, not '{self.curToken.text}' ({self.curToken.kind.name})", self.curToken.line)

# "FOR" (ident) "COMMA" (expression | number | ident) "COMMA" (expression | number | ident) "COMMA" (expression | number | ident) "DO" block "ENDFOR"
def funcFOR(self, TokenType):

	self.emitter.emit('for(')
	self.nextToken()

	self.match(TokenType.IDENT, False)
	forvar = self.curToken.text
	isnewforvar = True

	self.downScope()

	if not self.checkVar(forvar):
		self.addVar(forvar, TokenType.NUMBER)
		isnewforvar = True
	elif self.checkVar(forvar, TokenType.NUMBER):
		isnewforvar = False
	else:
		self.abort('For: Variable \"'+forvar+"\" is already declared and not of type NUMBER")

	self.emitter.emit(("int " if isnewforvar else "") + forvar + '=')

	self.nextToken()
	self.match(TokenType.COMMA, False)

	for i in range(3):
		self.nextToken()

		if self.checkToken(TokenType.NUMBER):
			if not self.checkPeek(TokenType.COMMA):
				# expression
				self.expression()
			else:
				# number
				self.emitter.emit(self.curToken.text)
				self.nextToken()

		elif self.checkToken(TokenType.IDENT):
			# ident
			if not self.checkPeek(TokenType.COMMA):
				# expression
				self.expression()
			else:
				# ident
				self.emitter.emit(self.curToken.text)
				self.nextToken()

		else:
			self.abort(f"For: Expected number or expression, not not '{self.curToken.text}' ({self.curToken.kind.name})", self.curToken.line)

		if i < 2:
			self.match(TokenType.COMMA, False)
			if i == 0:
				self.emitter.emit(';' + forvar + '<=')
			else:
				self.emitter.emit(';' + forvar + '+=')
		else:
			self.match(TokenType.DO)
			self.nl()
			self.emitter.emitLine("){")

	self.parsing_loop = True
	# Zero or more statements in the loop body.
	while not self.checkToken(TokenType.ENDFOR):
		self.statement()

	self.match(TokenType.ENDFOR)
	self.parsing_loop = False
	self.emitter.emitLine("}")
	self.upScope()
		
# "SLEEP" (expression | number | ident)
def funcSLEEP(self, TokenType):
	self.nextToken()
	
	if self.checkToken(TokenType.NUMBER):
		if not self.checkPeek(TokenType.NEWLINE) and not self.checkPeek(TokenType.EOF):
			# expression
			self.emitter.emit("sleep(")
			self.expression()
			self.emitter.emitLine(");")
		
		else:
			# Simple number, exit with it.
			self.emitter.emitLine("sleep(" + self.curToken.text + ");")
			self.nextToken()
			
	elif self.checkToken(TokenType.IDENT):
		# ident
		self.emitter.emitLine("sleep(" + self.curToken.text + ");")
		self.nextToken()
	else:
		self.abort(f"Sleep: Expected number or expression, not '{self.curToken.text}' ({self.curToken.kind.name})", self.curToken.line)

# "FUNC" ident ["TAKES" (idents)] "DOES" block "ENDFUNC"
def funcFUNCTION(self, TokenType):
	self.nextToken()

	# self.parsing_function = True
	# self.curFuncVars = {}
	funcscope = self.downScope()

	# self.emitter.function('void ' + self.curToken.text + '(')
	self.emitter.emit('void ' + self.curToken.text + '(')
	name = self.curToken.text

	hasargs = False
	funcargs = {}

	# Make sure this function doesn't already exist.
	if self.curToken.text in self.functionsDeclared:
		self.abort("Function: Function already exists: " + self.curToken.text, self.curToken.line)

	self.nextToken()
	if self.checkToken(TokenType.TAKES):

		# self.abort('Functions with arguments are not yet supported. Sorry!')

		hasargs = True
		indented_takes = False
		# has args
		self.nextToken()

		if self.checkToken(TokenType.NEWLINE):
			indented_takes = True
			self.nextToken()

		while not self.checkToken(TokenType.DOES):
			# expect "{HINT} IDENT, " etc..

			self.match(TokenType.HINT, False)
			vartoken = self.curToken
			if self.curToken.text == "number":
				vartype = TokenType.NUMBER
			if self.curToken.text == "string":
				vartype = TokenType.STRING
			if self.curToken.text == "bool":
				vartype = TokenType.BOOL
			self.nextToken()
			self.match(TokenType.IDENT, False)

			## print("varname: " + self.curToken.text + " type: " + vartype.name)
			## print(self.curToken.emittext)
			## self.emitter.function()
			# self.emitter.function(vartoken.emittext + " " + self.curToken.text)
			self.emitter.emit(vartoken.emittext + " " + self.curToken.text)

			# self.curFuncVars[self.curToken.text] = vartype
			self.addVar(self.curToken.text, vartype)
			funcargs[self.curToken.text] = vartype

			self.nextToken()
			# expect DOES (after newline if indented) or COMMA
			if self.checkToken(TokenType.COMMA):
				# self.emitter.function(',')
				self.emitter.emit(',')
				self.nextToken()
			elif indented_takes:
				self.match(TokenType.NEWLINE)
				# self.match(TokenType.NEWLINE):
				# self.emitter.function('){\n')
				self.emitter.emit('){\n')
			else:
				# self.emitter.function('){\n')
				self.emitter.emit('){\n')

	else:
		# no vars
		# self.emitter.function('void) {\n')
		self.emitter.emit('void) {\n')

	self.match(TokenType.DOES)
	self.nl()
	# Zero or more statements in the function body.
	# self.emitter.override_emit_to_func = True
	while not self.checkToken(TokenType.ENDFUNC):
		self.statement()
	# self.emitter.override_emit_to_func = False

	self.match(TokenType.ENDFUNC)
	# self.emitter.function('}')
	self.emitter.emitLine('} // END OF FUNCTION '+name)

	# remove local args from list of args if they dont already exist globally
	# if hasargs:
		# for arg in localargs:
			# if not arg[1]:
				# del self.variablesDeclared[arg[0]]
	self.functionsDeclared[name] = funcargs

	self.upScope()
	# self.parsing_function = False
	# self.curFuncVars = {}

# "CALL" ident ["WITH" ident ["COMMA" ident etc...]]
def funcCALL(self, TokenType):
	self.nextToken()
	self.match(TokenType.IDENT, False)
	if not self.curToken.text in self.functionsDeclared.keys():
		self.abort("Call: Calling function before declaration: " + self.curToken.text, self.curToken.line)

	argsamount = len(list(self.functionsDeclared[self.curToken.text]))
	funcname = self.curToken.text
	self.emitter.emit(self.curToken.text + "(")
	self.nextToken()

	# first generate the call of the wrapper but store information for the wrapper in the process
	# if func needs args check for them
	if argsamount > 0:
		# localargs = {}

		if not self.checkToken(TokenType.WITH):
			self.abort(f"Call: Function '{funcname}' requires {argsamount} arguments", self.curToken.line)
		
		self.nextToken()
		for i in range(argsamount):
			# self.emitter.emit(self.curToken.text)
			argname = list(self.functionsDeclared[funcname])[i]
			
			if self.checkToken(self.functionsDeclared[funcname][argname]):
				# given parameter is correct datatype (no ident)
				self.emitter.emit(self.curToken.text)

			elif self.checkToken(TokenType.IDENT):
				# given parameter is ident, check if correct datatype

				# first check if var exists
				if not self.checkVar(self.curToken.text):
					self.abort("Call: Variable \"" + self.curToken.text + "\" not defined", self.curToken.line)


				# if not self.variablesDeclared[self.curToken.text] \
					# == self.functionsDeclared[funcname][argname]:
				if not self.checkVar(self.curToken.text, self.functionsDeclared[funcname][argname]):
					self.abort("Call: Parameter \""+argname+"\" needs to be of type " + \
						self.functionsDeclared[funcname][argname], self.curToken.line)
				else:
					self.emitter.emit(self.curToken.text)
			else:
				# wrong parameter
				self.abort("Call: Parameter \""+argname+"\" needs to be of type " + \
						self.functionsDeclared[funcname][argname].name, self.curToken.line)

			self.nextToken()

			if i < argsamount - 1:
				self.match(TokenType.COMMA)
				self.emitter.emit(',')
			else:
				self.emitter.emitLine(');')

	else:
		# no args
		self.emitter.emitLine(');')

	if not self.checkToken(TokenType.NEWLINE):
		self.abort(f"Call: Function '{funcname}' takes {argsamount} arguments", self.curToken.line)

# "RETURN" (ident | number | string | bool | expression)
def funcRETURN(self, TokenType):
	self.abort("Return is not yet supported. Sorry!", self.curToken.line)

	# cannot return if not inside function
	if not self.emitter.override_emit_to_func:
		self.abort("Return: Cannot return outside of a function", self.curToken.line)


	self.nextToken()
	
	if self.checkToken(TokenType.NUMBER):
		if not self.checkPeek(TokenType.NEWLINE) and not self.checkPeek(TokenType.EOF):
			# expression
			self.emitter.emit("return(")
			self.expression()
			self.emitter.emitLine(");")
		
		else:
			# Simple number, exit with it.
			self.emitter.emitLine("return " + self.curToken.text + ";")
			self.nextToken()
			
	elif self.checkToken(TokenType.IDENT) or self.checkToken(TokenType.BOOL):
		# ident or bool
		self.emitter.emitLine("return " + self.curToken.text + ";")
		self.nextToken()

	elif self.checkToken(TokenType.STRING):
		# string
		self.emitter.emitLine("return \"" + self.curToken.text + "\";")
		self.nextToken()

	else:
		self.abort(f"Return: Expected return value, not '{self.curToken.text}' ({self.curToken.kind.name})", self.curToken.line)

# "StartWith HINT IDENT, etc..
def funcSTARTW(self, TokenType):
	self.nextToken()

	if not self.allowstartwith:
		self.abort("StartWith: This syntax can only be used at the start of the script", self.curToken.line)

	def handlevar(isfirst=False):
		# emit type and varname to main parameters
		if not isfirst:
			self.emitter.emitMainArg(",")
		self.emitter.emitMainArg(self.curToken.emittext + " ")
		self.emitter.emitMainCall(self.curToken.emittext + " ")

		if self.curToken.text == "number":
			vartype = TokenType.NUMBER
		if self.curToken.text == "string":
			vartype = TokenType.STRING
		if self.curToken.text == "bool":
			vartype = TokenType.BOOL

		self.match(TokenType.HINT)
		self.emitter.emitMainArg(self.curToken.text)
		self.emitter.maincallargs.append(self.curToken.text)
		# self.variablesDeclared[self.curToken.text] = vartype
		self.addVar(self.curToken.text, vartype)

		self.emitter.emitMainCall(self.curToken.text)
		varname = self.curToken.text
		if vartype == TokenType.NUMBER:
			self.emitter.emitMainCallLine("=atof(argv["+\
				str(len(self.emitter.maincallargs))+"]);")
		elif vartype == TokenType.STRING:
			self.emitter.emitMainCallLine("=argv["+\
				str(len(self.emitter.maincallargs))+"];")
		elif vartype == TokenType.BOOL:
			self.emitter.emitMainCallLine(";")
			self.emitter.emitMainCallLine("if(strcmp(argv["+\
				str(len(self.emitter.maincallargs))+"], \"true\") == 0)")
			self.emitter.emitMainCallLine(varname+"=true;")
			self.emitter.emitMainCallLine("else")
			self.emitter.emitMainCallLine(varname+"=false;")

		self.match(TokenType.IDENT)

	handlevar(True)

	while not self.checkToken(TokenType.NEWLINE):
		self.match(TokenType.COMMA)
		handlevar()

# "USE" (IDENT | STRING)
def funcUSE(self, TokenType):
	self.nextToken()

	curdir = os.getcwd()

	# either IDENT (script in cur. dir or in search path) or STRING (path)	
	if self.checkToken(TokenType.IDENT):
		if not os.path.exists(os.path.join(curdir, self.curToken.text+".tic")):
			self.abort("Use: Script \""+self.curToken.text+"\" not found in current directory", self.curToken.line)
		inclfile = os.path.join(curdir, self.curToken.text+".tic")
	elif self.checkToken(TokenType.STRING):
		if not self.curToken.text[0] == "/":
			# rel. path
			path = os.path.join(curdir, self.curToken.text+".tic")
		else:
			path = os.path.join(curdir, self.curToken.text+".tic")
		if not os.path.exists(path):
			self.abort("Use: Script \""+path+"\" not found", self.curToken.line)
		inclfile = path

	self.print("\nINCLUDING:")

	# header files
	headerfile = os.path.join(tempfile.gettempdir(), randStr(10)+".h")
	self.headerfiles.add(headerfile)

	# comp command
	ticcomp = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ticcomp")
	cmd = f"{ticcomp} {inclfile} -g -o {headerfile}"
	returnval = os.system(cmd)

	# check comp. success
	returnval = int(bin(returnval).replace("0b", "").rjust(16, '0')[:8], 2)
	if returnval != 0:
		print('Compilation of '+inclfile+' failed with exit code ', returnval)
		sys.exit(returnval)
	self.print("Compiling "+inclfile+" completed.")

	with open(headerfile) as f:
		for line in f:
			# funcdef
			if line.startswith("// DEFFUNC"):
				funcdict = {}

				self.print("\nIMPORTING FUNCTION:")
				self.print("    LINE: "+line[:-1])

				# first get func name
				funcname = line.split('!')[1]#.split('!')[0]
				self.print("    NAME: "+funcname)

				# get arg count
				argc = line.split('[')[1].split(']')[0]
				self.print("    ARG COUNT: "+str(argc))

				# get args (format: "// DEFFUNC!name![arg count]{argname:argtype}etc..")
				if '{' in line:
					args = []
					for arg in line.split('{'):
						if '}' in arg:
							fullarg = arg.split('}')[0]
							argname = fullarg.split(':')[0]
							argtype = fullarg.split(':')[1]

							funcdict[argname] = eval("TokenType."+argtype)

							self.print("    - ARG: "+argname+" ("+argtype+")")

				self.functionsDeclared[funcname] = funcdict
				# self.emitter.inc

			# vardef
			elif line.startswith("// DEFVAR"):
				self.print("\nIMPORTING VARIABLE:")
				self.print("    LINE: "+line[:-1])

				varname = line.split('!')[1]
				self.print("    NAME: "+varname)
				vartype = eval("TokenType."+line.split('{')[1].split('}')[0])
				self.print("    TYPE: "+str(vartype))
				# self.variablesDeclared[varname] = vartype
				self.addVar(varname, vartype)

			# includedef
			elif line.startswith("// INCL"):
				headers = []
				self.print("\nIMPORTING INCLUDES:")
				self.print("    LINE: "+line[:-1])

				inclist = line.split('[')[1].split(']')[0].split(',')
				for incl in inclist:
					self.print("    - INCLUDE: "+incl)
					# self.include(incl)
					headers.append(incl)

				self.print()
				for header in headers:
					self.include(header)
				break

			else:
				# funcdefs and headers will always be on top so the rest can be skipped
				break

	self.print("DONE INCLUDING\n")
	self.include(headerfile, False)
	self.nextToken()

# "EMITC" (IDENT | STRING)
def funcEMITC(self, TokenType):
	self.nextToken()
	self.used_emitc = True
	if self.checkToken(TokenType.STRING):
		self.emitter.emitLine(self.curToken.text)
	else:
		self.abort('EmitC: EmitC only takes a string, not \"'+self.curToken.text+"\"", self.curToken.line)
	self.nextToken()
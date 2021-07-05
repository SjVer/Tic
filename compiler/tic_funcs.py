from tic_lex import *
import random, string, tempfile, sys, os
from termcolor import colored
# from tic_imports import FuncPropterties, VarProperties
# from tokens import DataTypes

class VarProperties:
	def __init__(self, vartype, mutable: bool, isfield=False, classname=False):
		self.type = vartype
		# self.emittext = emittext
		self.isfield = isfield
		self.classname = classname
		self.mutable: bool = mutable

class FuncPropterties:
	def __init__(self, params: dict, optargc: int, 
		doesreturn: bool, returntype = None, 
		ismethod = False, classname=False):

		self.params: dict = params
		self.optargc: int = optargc
		self.doesreturn: bool = doesreturn
		self.returntype = returntype
		self.ismethod = ismethod
		self.classname = classname

def randStr(N):
	# generates a random string of length N
	return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(N))

# "PRINT" (expression | string)
def funcPRINT(self, TokenType, from_printline=False):
	self.nextToken()

	if self.checkToken(TokenType.STRING):
		# Simple string, so print it.
		self.emitter.emitLine("printf(\"" + self.curToken.text + "\");")
		self.nextToken()

	elif self.checkToken(TokenType.NUMBER) and not self.atExpression():
		# number
		self.emitter.emitLine("printf(\"" + self.curToken.text + "\\n\");")
		self.nextToken()

	elif self.checkToken(TokenType.IDENT) and not self.atExpression():
		# ident
		
		# check if defined
		if not self.checkVar(self.curToken.text):
			self.abort("Print"+("Line" if from_printline else "")+\
				f": Attempted to print undeclared variable '{self.curToken.text}'", self.curToken.line)
		
		# detect variable type and emit based off that
		if self.checkVar(self.curToken.text, TokenType.STRING):
			# var contains string
			self.emitter.emitLine("printf(\"%" + f"s\", {self.getVarStr(self.curToken.text)});")

		elif self.checkVar(self.curToken.text, TokenType.NUMBER):
			# var contains number
			# the emitted code checks if number is int or float and prints accordingly
			self.emitter.emitLine(f"if(roundf({self.getVarStr(self.curToken.text)}) == {self.getVarStr(self.curToken.text)})"+'{')
			self.emitter.emitLine(f"printf(\"%d\", (int){self.getVarStr(self.curToken.text)});")
			self.emitter.emitLine("}else{")
			# self.emitter.emitLine(f"printf(\"%.3f\", {self.curToken.text});"+'}')
			i = randStr(10)
			a = randStr(10)
			b = randStr(10)
			self.emitter.emitLine("int "+i+"=1;")
			self.emitter.emitLine("while(1){")
			self.emitter.emitLine("float "+a+"="+self.getVarStr(self.curToken.text)+"*powf(10,"+i+");")
			self.emitter.emitLine("float "+b+"=round("+a+");")
			# self.emitter.emitLine("if("+a+"==(int)"+a+"){")
			self.emitter.emitLine("if("+a+"=="+b+"){")
			self.emitter.emitLine("break;}")
			self.emitter.emitLine(i+"++;}")
			self.emitter.emitLine("printf(\"%."+"*f\","+i+","+self.getVarStr(self.curToken.text)+");}")

		elif self.checkVar(self.curToken.text, TokenType.BOOL):
			self.emitter.emitLine("printf(\"%" + f"s\", {self.getVarStr(self.curToken.text)}?\"true\":\"false\");")
		# self.emitter.emitLine("char *string = (char *)" + self.curToken.text + ";")
		# self.emitter.emitLine("printf(\"%" + "s\", " + "string" + ");")
		self.nextToken()

	elif self.atExpression():
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

	else:
		self.abort('Print: Unexpected value of type '+self.curToken.kind.name+' ("'+self.curToken.text+'")')

# "PRINTLN" (expression | string)
def funcPRINTLN(self, TokenType):
	funcPRINT(self, TokenType, True)
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
		print(list(self.getVars()))
		self.abort(f"Set: Variable \"{varname}\" not declared", self.curToken.line)
	self.emitter.emit(self.getVarStr(varname) + ' = ')

	vartype = self.getVarType(varname)
	mutable = self.checkVarMutability(varname)
	if not mutable:
		self.abort(f"Set: Variable \"{varname}\" is a constant and cannot be set", self.curToken.line)

	self.nextToken()
	self.match(TokenType.EQ)

	# check if type is correct (excuse idents)
	if self.curToken.kind != self.getVarType(varname) and not self.checkToken(TokenType.IDENT):
		self.abort('Set: Attempted to assign a ' + \
			self.curToken.kind.name.lower() + ' to a variable declared with type ' + \
			self.getVarType(varname).name.lower() + f' ({self.curToken.text} to {varname})', self.curToken.line)

	# emit shit
	if self.getVarType(varname) == TokenType.STRING:
		self.emitter.emitLine("\"" + self.curToken.text + "\";")
		self.match(self.getVarType(varname))
		# self.nextToken()

	elif self.getVarType(varname) != TokenType.NUMBER:
		self.emitter.emitLine(self.curToken.text + ';')
		self.match(self.getVarType(varname))
		# self.nextToken()

	# elif self.variablesDeclared[varname]

	else:
		# can be either number or expression
		if self.atExpression():
			# expression
			self.expression()
			self.emitter.emitLine(';')
		else:
			self.emitter.emitLine(self.curToken.text + ';')
			self.match(TokenType.NUMBER)
			# self.nextToken()

# "DECLARE" type ident = (expression | string | number)
def funcDECLARE(self, TokenType):
	self.nextToken()

	ishinted = False
	hinttoken = None
	templine = ""
	isconstant = False

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

		isconstant = self.curToken.hintprops.const

		if self.curToken.hintprops.opt:
			self.abort('Declare: Optional variables can only be function parameters', self.curToken.line)

		## self.emitter.emit(self.curToken.emittext + " ")
		templine += self.curToken.hintprops.emittext + " "
		self.nextToken()

	varname = self.curToken.text
	if "'s " in varname:
		self.abort("Declare: Cannot declare fields of an instance", self.curToken.line)
	##  self.emitter.emit(varname)
	templine += 'USR_' + varname
	self.match(TokenType.IDENT, False)

	if not ishinted or isconstant:
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

	if not dontcontinue and not isconstant:
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
			if self.atExpression():
				# expression
				if not ishinted:
					templine = "float " + templine
					vartype = TokenType.NUMBER
				templine += self.get_current_expression()
				##  self.expression()
			else:
				# number
				## self.emitter.emit(self.curToken.text)
				if not ishinted:
					templine = "float " + templine
					vartype = TokenType.NUMBER
				templine += self.curToken.text
				self.nextToken()

	elif (not dontcontinue and ishinted) or isconstant:
		if vartype == TokenType.STRING:
			templine += '"'+self.curToken.text+'"'
		else:
			templine += self.curToken.text
		self.match(vartype)

	# elif isconstant:

	#  Check if ident exists in symbol table. If not, declare it.
	if not self.checkVar(varname):

		self.addVar(varname, vartype, not isconstant)
		if self.generating_header:

			if self.parsing_function:
				self.emitter.emitLine(templine + ';')
			else:
				self.emitter.headerLine(templine + ';')

		else:
			self.emitter.emitLine(templine + ';')

	# var already exists. abort
	else:
		self.abort(f"Declare: Variable '{varname}' is already declared.", self.curToken.line)

# "INPUT" ident
def funcINPUT(self, TokenType):
	self.nextToken()

	varname = self.curToken.text
	varstr = self.getVarStr(varname)

	# check variable exists else abort
	if not self.checkVar(varname):
		self.abort("Input: Attempted to assign input to undeclared variable " + varname, self.curToken.line)

	vartype = self.getVarType(varname)

	# generate the right scanf format for each data type
	if vartype == TokenType.NUMBER:
		self.emitter.emitLine("scanf(\"%" + "f\", &" + varstr + ");")

	elif vartype == TokenType.STRING:
		tempstr = randStr(10)
		self.emitter.emitLine("char "+tempstr+"[1000];")
		self.emitter.emitLine("scanf(\"%" + f"s\", &{tempstr});")
		self.emitter.emitLine(varstr+"="+tempstr+";")
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
		self.emitter.emitLine(varstr + "=true;")
		self.emitter.emitLine("}else{")
		self.emitter.emitLine(varstr + "=false;}")

	self.match(TokenType.IDENT)

# "EXIT" (expression | number | ident)
def funcEXIT(self, TokenType):
	self.nextToken()
	
	if self.checkToken(TokenType.NUMBER):
		if self.atExpression():
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
		self.emitter.emitLine("exit(" + self.getVarStr(self.curToken.text) + ");")
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
		self.addVar(forvar, TokenType.NUMBER, True)
		isnewforvar = True
	elif self.checkVar(forvar, TokenType.NUMBER):
		isnewforvar = False
	else:
		self.abort('For: Variable \"'+forvar+"\" is already declared and not of type NUMBER")

	self.emitter.emit(("int " if isnewforvar else "") + self.getVarStr(forvar) + '=')

	self.nextToken()
	self.match(TokenType.COMMA, False)

	for i in range(3):
		self.nextToken()

		if self.checkToken(TokenType.NUMBER):
			if self.atExpression():
				# expression
				self.expression()
			else:
				# number
				self.emitter.emit(self.curToken.text)
				self.nextToken()

		elif self.checkToken(TokenType.IDENT):
			# ident
			if self.atExpression():
				# expression
				self.expression()
			else:
				# ident
				self.emitter.emit(self.getVarStr(self.curToken.text))
				self.nextToken()

		else:
			self.abort(f"For: Expected number or expression, not not '{self.curToken.text}' ({self.curToken.kind.name})", self.curToken.line)

		if i < 2:
			self.match(TokenType.COMMA, False)
			if i == 0:
				self.emitter.emit('; USR_' + forvar + '<=')
			else:
				self.emitter.emit('; USR_' + forvar + '+=')
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
		if self.atExpression():
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
		self.emitter.emitLine("sleep(" + self.getVarStr(self.curToken.text) + ");")
		self.nextToken()
	else:
		self.abort(f"Sleep: Expected number or expression, not '{self.curToken.text}' ({self.curToken.kind.name})", self.curToken.line)

# "FUNC" ident ["TAKES" (idents)] "DOES" block "ENDFUNC"
def funcFUNCTION(self, TokenType, inclass=False, classname=None, classdict=None):
	self.nextToken()

	if self.generating_header:
		self.emitter.override_emit_to_func = True
		self.parsing_function = True

	funcscope = self.downScope()

	if inclass:
		for field in classdict['fields']:
			self.addVar("self's " + field, classdict['fields'][field].type, \
				not classdict['fields'][field].mutable)
		# self.emitter.startGetStr()

	self.emitter.emit('VARGOHERE USR_' +(classname + "_METHOD_" if inclass else "") +self.curToken.text + '(')
	name = self.curToken.text

	doesreturn = False
	hasargs = False
	funcargs = {}
	optargc = 0

	# pass class fields if parsing method
	if inclass and classdict['fields'] != {}:
		for field in classdict['fields']:

			vartype = classdict['fields'][field].type
			if vartype == TokenType.STRING:
				self.emitter.emit('char *')
			elif vartype == TokenType.NUMBER:
				self.emitter.emit('float ')
			elif vartype == TokenType.BOOL:
				self.emitter.emit('bool ')

			self.emitter.emit('CURRENTINSTANCEFIELD_'+field)
			if field != list(classdict['fields'])[-1]:
				self.emitter.emit(',')

	# Make sure this function doesn't already exist.
	if self.curToken.text in self.functionsDeclared:
		self.abort("Function: Function already exists: " + self.curToken.text, self.curToken.line)

	self.nextToken()
	if self.checkToken(TokenType.TAKES):

		hasargs = True
		optgiven = False

		# has args
		self.nextToken()
		if self.checkToken(TokenType.NEWLINE):
			self.nl()

		while not self.checkToken(TokenType.DOES):

			# expect "{HINT} IDENT, " etc..

			if self.checkToken(TokenType.DOES):
				break

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

			if inclass and classdict['fields'] != {}:
				self.emitter.emit(',')
			self.emitter.emit(vartoken.hintprops.emittext + " USR_" + self.curToken.text)

			# if optional param only optional params can follow
			if optgiven and not vartoken.hintprops.opt:
				self.abort('Function: Only optional parameters can follow an optional parameter',self.curToken.line)
			optgiven = vartoken.hintprops.opt

			if self.checkVar(self.curToken.text):
				self.abort("Function: Parameter \""+self.curToken.text+'" already exists',self.curToken.line)

			self.addVar(self.curToken.text, vartype, True)

			# curtok here: ident
			argname = self.curToken.text
			self.nextToken()

			default = None
			if optgiven:
				if self.checkToken(TokenType.EQ):
					# init value given
					self.nextToken()
					default = self.curToken.text
					self.match(vartype)
					optargc += 1

			funcargs[argname] = {'type': vartype, 'opt': optgiven, 'default': default}

			# expect DOES (after newline if indented) or COMMA
			if self.checkToken(TokenType.COMMA):
				# self.emitter.function(',')
				self.emitter.emit(',')
				self.nextToken()

				if self.checkToken(TokenType.NEWLINE):
					self.nl()

				self.match(TokenType.HINT, False)

			else:
				if self.checkToken(TokenType.NEWLINE):
					self.nl()
				self.match(TokenType.DOES, False)
				break

		self.emitter.emitLine('){');

	elif (not inclass) or (classdict['fields'] == {}):
		# no vars
		# self.emitter.function('void) {\n')
		self.emitter.emitLine('void) {')
	else:
		self.emitter.emitLine('){')

	self.match(TokenType.DOES)
	self.nl()

	# Zero or more statements in the function body.
	while not self.checkToken(TokenType.ENDMETH if inclass else TokenType.ENDFUNC):
		self.statement()

	self.match(TokenType.ENDMETH if inclass else TokenType.ENDFUNC)

	if self.checkToken(TokenType.FRETURN):
		doesreturn = True
		# function returns smth
		self.nextToken()
		self.match(TokenType.IDENT, False)
		if not self.checkVar(self.curToken.text):
			self.abort("Returning: Attempted to return a undeclared variable: \""+self.curToken.text+'"', self.curToken.line)
		
		retvar = self.curToken.text
		vartype = self.getVarType(self.curToken.text)
		if vartype == TokenType.STRING:
			varstr = "char *"
		elif vartype == TokenType.BOOL:
			varstr = "bool"
		else:
			varstr = "float"
		self.nextToken()

	else:
		# function returns nothing
		varstr = "void"

	# print('replacing VARGOHERE USR_'+name + ' with '+ varstr + ' USR_'+name)
	if self.generating_header:
		self.emitter.functions = \
			self.emitter.functions.replace('VARGOHERE USR_'+name, varstr + ' USR_'+name)
	elif inclass:
		self.emitter.code = \
			self.emitter.code.replace('VARGOHERE USR_'+classname+'_METHOD_'+name,\
				varstr + ' USR_'+classname+'_METHOD_'+name)

	else:
		self.emitter.code = \
			self.emitter.code.replace('VARGOHERE USR_'+name, varstr + ' USR_'+name)

	if doesreturn:
		self.emitter.emitLine('return(USR_'+retvar+');')
	self.emitter.emitLine('} // END OF FUNCTION '+name)

	if inclass:
		classdict['methods'][name] = {'props': FuncPropterties(
			funcargs, optargc, doesreturn, (vartype if doesreturn else None),
			True, classname)}
	else:
		self.addFunc(name, funcargs, optargc, doesreturn, (vartype if doesreturn else None))

	# self.functionsDeclared[name] = funcprops
	self.upScope()

	if self.generating_header:
		self.emitter.override_emit_to_func = False
		self.parsing_function = False

	# if inclass:
		# classdict['methods'][name]['code'] = self.emitter.finishGetStr()
		# return self.emitter.finishGetStr()

# "CALL" ident ["WITH" ident ["COMMA" ident etc...]]
def funcCALL(self, TokenType, from_return=False):
	self.nextToken()
	self.match(TokenType.IDENT, False)
	if not self.curToken.text in self.functionsDeclared.keys():
		self.abort(("Return" if from_return else "Call")+": Calling function before declaration: " + self.curToken.text, self.curToken.line)

	params = self.functionsDeclared[self.curToken.text].params
	optargc = self.functionsDeclared[self.curToken.text].optargc
	doesreturn = self.functionsDeclared[self.curToken.text].doesreturn
	ismethod = self.functionsDeclared[self.curToken.text].ismethod
	classname = self.functionsDeclared[self.curToken.text].classname
	
	if from_return and not doesreturn:
		self.abort("Return: Function \""+self.curToken.text+'" does not return a value', self.curToken.line)

	argsamount = len(list(params))
	funcname = self.curToken.text

	if ismethod:
		instname = funcname.split("'s ")[0]

		self.emitter.emit("USR_"+classname+"_METHOD_"+self.curToken.text.split("'s ")[1]+'(')
		for field in self.classesDeclared[classname]['fields']:
			fielddict = self.classesDeclared[classname]['fields']
			self.emitter.emit(instname + "___INSTANCEOF_"+classname+"_CLASS___"+field)
			if field != list(self.classesDeclared[classname]['fields'])[-1]:
				self.emitter.emit(',')

	else:
		self.emitter.emit("USR_"+self.curToken.text + "(")
	self.nextToken()

	givenargs = 0

	# first generate the call of the wrapper but store information for the wrapper in the process
	# if func needs args check for them
	if argsamount > 0:

		# atopts = False
		nextisopt = False

		if not self.checkToken(TokenType.WITH):
			# print(self.curToken.kind.name)
			if optargc:
				self.abort(("Return" if from_return else "Call")+f": Function '{funcname}' requires {argsamount - optargc - 1} to {argsamount} arguments", self.curToken.line)
			else:
				self.abort(("Return" if from_return else "Call")+f": Function '{funcname}' requires {argsamount} argument"+('s' if argsamount>1 else ''), self.curToken.line)

		self.nextToken()
		for i in range(argsamount):
			# self.emitter.emit(self.curToken.text)
			argname = list(params)[i]
			vardict = params[argname]
			vartype = vardict['type']
			isopt = vardict['opt']
			default = vardict['default']
			# atopts = isopt

			if len(list(params)) >= i+2:
				nextisopt = list(params)[i+1]


			if not (self.checkToken(vartype) or \
				(self.checkToken(TokenType.IDENT) and self.checkVar(self.curToken.text, vartype))):
				if not self.checkVar(self.curToken.text):
					self.abort(("Return" if from_return else "Call")+": Variable \""+self.curToken.text+\
						"\" has not been declared", self.curToken.line)
				# not correct type or var with correct type
				self.abort(("Return" if from_return else "Call")+": Parameter \""+argname+"\" needs to be of type " + \
					vartype.name + ", not \"" + self.curToken.text +\
					 '" (' + self.curToken.kind.name + ')', self.curToken.line)

			if self.checkToken(TokenType.STRING):
				self.emitter.emit('"'+self.curToken.text+'"')
				self.nextToken()
			elif self.checkToken(TokenType.BOOL):
				self.emitter.emit(self.curToken.text)
				self.nextToken()

			elif self.checkToken(TokenType.NUMBER, TokenType.IDENT):
				if self.atExpression():
					self.expression()

				# elif self.checkToken(TokenType.IDENT):
				else:

					self.emitter.emit(self.getVarStr(self.curToken.text) \
						if self.checkToken(TokenType.IDENT)\
						else self.curToken.text)
					self.nextToken()

			givenargs += 1

			if i < argsamount - 1:
				if nextisopt:
					if self.checkToken(TokenType.COMMA):
						# another arg given
						self.emitter.emit(',')
						self.nextToken()

					elif self.checkToken((TokenType.TO if from_return else TokenType.NEWLINE)):
						# no other args given

						for x in range(givenargs, givenargs+argsamount-1-i):
							curarg = params[list(params)[x]]
							argtype = curarg['type']
							default = curarg['default']

							if default == "None":
								if argtype == TokenType.STRING:
									self.emitter.emit(',""')
								elif argtype == TokenType.NUMBER:
									self.emitter.emit(',0')
								elif argtype == TokenType.BOOL:
									self.emitter.emit(',false')
							else:
								if argtype == TokenType.STRING:
									self.emitter.emit(',"'+default+'"')
								else:
									self.emitter.emit(','+default)

						self.emitter.emitLine(');')
						break
				# if not self.checkToken(TokenType.COMMA):
					# self.abort(f'Call: Expected {argsamount} arguments followed by a NEWLINE', self.curToken.line)
			else:
				if not self.checkToken(TokenType.TO if from_return else TokenType.NEWLINE):
					self.abort(("Return" if from_return else "Call")+f": Expected a maximum of {argsamount} arguments followed by "+\
						('"To"' if from_return else 'a NEWLINE'), self.curToken.line)
				self.emitter.emitLine(');')

	else:
		# no args
		self.emitter.emitLine(');')

	if not self.checkToken(TokenType.TO if from_return else TokenType.NEWLINE):
		self.abort(("Return" if from_return else "Call")+": Expected "+('"To"' if from_return else " a NEWLINE")+f" after {givenargs} argument"+("s" if argsamount!=1 else "")+", not " + self.curToken.kind.name, self.curToken.line)

# "RETURN" ident ["WITH" (ident|number|string|bool)"COMMA"+] "TO" ident
def funcRETURN(self, TokenType):
	if not self.checkPeek(TokenType.IDENT):
		self.abort("Return: Expected name after \"Return\"")
	funcname = self.peekToken.text

	self.emitter.startGetStr()

	funcCALL(self, TokenType, True)

	templine = self.emitter.finishGetStr()

	self.nextToken()
	destvar = self.curToken.text

	if not self.checkVar(destvar):
		self.abort('Return: Attempted to return to an undeclared variable: \"'+destvar+'"', self.curToken.line)
	elif not self.checkVarMutability(destvar):
		self.abort('Return: Attempted to return to a constant variable: \"'+destvar+'"', self.curToken.line)
	
	elif not self.checkVar(destvar, self.functionsDeclared[funcname].returntype):
		self.abort('Return: Function "'+funcname+'" returns type '+self.functionsDeclared[funcname].returntype.name+\
			' but destination variable "'+destvar+'" is of type '+self.getVarType(destvar).name, self.curToken.line)

	self.match(TokenType.IDENT)

	self.emitter.emitLine('USR_' + destvar + '=' + templine)

# "STARTW" hint ident, etc..
def funcSTARTW(self, TokenType):
	self.nextToken()

	if not self.allowstartwith:
		self.abort("StartWith: This syntax can only be used at the start of the script", self.curToken.line)

	def handlevar(isfirst=False):
		# emit type and varname to main parameters
		if not isfirst:
			self.emitter.emitMainArg(",")
		self.emitter.emitMainArg(self.curToken.hintprops.emittext + " ")
		self.emitter.emitMainCall(self.curToken.hintprops.emittext + " ")

		if self.curToken.text == "number":
			vartype = TokenType.NUMBER
		if self.curToken.text == "string":
			vartype = TokenType.STRING
		if self.curToken.text == "bool":
			vartype = TokenType.BOOL

		self.match(TokenType.HINT)
		self.emitter.emitMainArg('USR_'+self.curToken.text)
		self.emitter.maincallargs.append(self.curToken.text)
		# self.variablesDeclared[self.curToken.text] = vartype
		self.addVar(self.curToken.text, vartype, True)

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

# "USE" (ident | string)
def funcUSE(self, TokenType):
	self.nextToken()

	curdir = os.getcwd()
	isinstdlib = False

	# either IDENT (script in cur. dir or in search path) or STRING (path)	
	if self.checkToken(TokenType.IDENT):
		# must be in stdlibpath
		if not os.path.exists(os.path.join(self.stdlibpath, self.curToken.text+".tic")):
			self.abort("Use: Script \""+self.curToken.text+"\" not found in standard library", self.curToken.line)
		inclfile = os.path.join(self.stdlibpath, self.curToken.text+".tic")
		isinstdlib = True
	
	elif self.checkToken(TokenType.STRING):
		if not self.curToken.text[0] == "/":
			# rel. path
			path = os.path.join(curdir, self.curToken.text+".tic")
		else:
			path = os.path.join(curdir, self.curToken.text+".tic")
		if not os.path.exists(path):
			self.abort("Use: Script \""+path+"\" not found", self.curToken.line)
		inclfile = path

	self.print(colored("\nINCLUDING: "+self.curToken.text +\
	(" FROM STDLIB" if isinstdlib else "") , 'magenta'))

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

	# read funcs n vars
	with open(headerfile) as f:
		for line in f:
			# funcdef
			if line.startswith("// DEFFUNC"):
				funcdict = {}
				funcname = line.split('!')[1]#.split('!')[0]
				argc = line.split('[')[1].split(']')[0].split(':')[0]
				optargc = line.split('[')[1].split(']')[0].split(':')[1]
				doesreturn = eval(line.split('(')[1].split(':')[0])
				returntype = line.split('(')[1].split(':')[1].split(')')[0]
				if returntype != "None":
					returntype = eval('TokenType.'+returntype)
				else:
					returntype = None

				if not isinstdlib:
					self.print("\nIMPORTING FUNCTION:")
					self.print("    LINE: "+line[:-1])
					self.print("    NAME: "+funcname)
					self.print("    RETURNS: " +str(doesreturn))
					self.print("    RETURNTYPE: " +str(returntype))
					self.print("    ARG COUNT: "+str(argc))
					self.print("    OPT. ARG COUNT: "+str(optargc))

				# get args (format: "// DEFFUNC!name![arg count]{argname:argtype}etc..")
				if '{' in line:
					args = []
					for arg in line.split('{'):
						if '}' in arg:
							fullarg = arg.split('}')[0]
							argname = fullarg.split(':')[0]
							argtype = eval('TokenType.'+fullarg.split(':')[1].split(':')[0])
							isopt = eval(fullarg.split(':')[2].split(':')[0])
							default = fullarg.split(':')[3].split(':')[0]
							funcdict[argname] = {'type': argtype, 'opt': isopt, 'default': default}
							if not isinstdlib:
								self.print("    - ARG: "+argname+" ("+str(argtype)+")")

				# self.functionsDeclared[funcname] = funcdict
				self.addFunc(funcname, funcdict, optargc, doesreturn, returntype)
				# self.emitter.inc

			# vardef
			elif line.startswith("// DEFVAR"):
				varname = line.split('!')[1]
				vartype = eval("TokenType."+line.split('{')[1].split('}')[0])
				mutable = eval(line.split('[')[1].split(']')[0])

				if not isinstdlib:
					self.print("\nIMPORTING VARIABLE:")
					self.print("    LINE: "+line[:-1])
					self.print("    NAME: "+varname)
					self.print("    TYPE: "+str(vartype))
					self.print("    MUTA: "+str(mutable))
				# self.variablesDeclared[varname] = vartype
				self.addVar(varname, vartype, mutable)

			# includedef
			elif line.startswith("// INCL"):
				headers = []
				inclist = line.split('[')[1].split(']')[0].split(',')
				if not isinstdlib:
					self.print("\nIMPORTING INCLUDES:")
					self.print("    LINE: "+line[:-1])
				for incl in inclist:
					if not isinstdlib:
						self.print("    - INCLUDE: "+incl)
					# self.include(incl)
					headers.append(incl)

				if not isinstdlib:
					self.print()
				for header in headers:
					self.include(header)
				break

			else:
				# funcdefs and headers will always be on top so the rest can be skipped
				break

	if False:
		self.print('\n\nGENERATED HEADER CODE:')
		self.print('==================================\n\n')
		if self.verbose: os.system('highlight -O ansi --force '+headerfile+'')        
		self.print('\n\n==================================\n\n')

	self.print(colored("\nDONE INCLUDING", 'magenta'))
	self.include(headerfile, False)
	self.nextToken()

# "EMITC" (ident | string)
def funcEMITC(self, TokenType):
	self.nextToken()
	self.used_experimental = True
	if self.checkToken(TokenType.STRING):
		a = randStr(10)
		self.emitter.emitLine(self.curToken.text.replace('\\\\', a).replace('\\', '').replace(a, '\\'))
	else:
		self.abort('EmitC: EmitC only takes a string, not \"'+self.curToken.text+"\"", self.curToken.line)
	self.nextToken()

# "INCLC" string
def funcINCLC(self, TokenType):
	self.nextToken()
	self.include(self.curToken.text, False)
	self.match(TokenType.STRING)
	self.used_experimental = True

# "RAISE" string [number]
def funcRAISE(self, TokenType):
	self.nextToken()
	self.emitter.emit('printf("\\033[1;31m')
	self.emitter.emit(self.curToken.text)
	self.emitter.emitLine('\\n\\033[0m");')
	self.match(TokenType.STRING)
	if self.checkToken(TokenType.NUMBER):
		self.emitter.emit('exit(')
		self.emitter.emit(self.curToken.text)
		self.emitter.emitLine(');')
		self.match(TokenType.NUMBER)
		self.nextToken()
	elif self.checkToken(TokenType.IDENT):
		if not self.checkVar(self.curToken.text, TokenType.NUMBER):
			self.abort('Raise: Exit code can only be a number or a variable containing a number', self.curToken.line)
		self.emitter.emit('exit(')
		self.emitter.emit(self.getVarStr(self.curToken.text))
		self.emitter.emitLine(');')
		self.match(TokenType.IDENT)
		self.nextToken()
	else:
		self.emitter.emitLine('exit(1);')

# "CLASS" ident "Has" [hint ident ["COMMA"]]+ "DOES" [function]+ "ENDCLASS"
def funcCLASS(self, TokenType):
	self.nextToken()
	classname = self.curToken.text
	classdict = {"fields": {}, "methods": {}}
	self.match(TokenType.IDENT)

	hasfields = False
	hasmethods = False

	self.downScope()

	if self.checkToken(TokenType.HAS):
		# has args
		hasfields = True
		self.nextToken()
		if self.checkToken(TokenType.NEWLINE):
			self.nl()

		while not self.checkToken(TokenType.DOES):

			# expect "{HINT} IDENT, " etc..

			if self.checkToken(TokenType.DOES):
				break

			self.match(TokenType.HINT, False)
			vartoken = self.curToken
			vartext = self.curToken.text

			if "optional" in self.curToken.text:
				self.abort("Class: Optional fields are not allowed")

			isconstant = False
			if "constant " in self.curToken.text:
				isconstant = True
				vartext = vartext.replace('constant ', '')

			if vartext == "number":
				vartype = TokenType.NUMBER
			elif vartext == "string":
				vartype = TokenType.STRING
			elif vartext == "bool":
				vartype = TokenType.BOOL
			self.nextToken()
			self.match(TokenType.IDENT, False)

			# self.emitter.emit(vartoken.hintprops.emittext + " " + self.curToken.text)
			varprops = VarProperties(vartype, isconstant)
			classdict["fields"][self.curToken.text] = varprops

			if self.checkVar(self.curToken.text):
				self.abort("Class: Variable \""+self.curToken.text+'" already exists',self.curToken.line)
			# self.addVar(self.curToken.text, vartype, isconstant)

			# curtok here: ident
			self.nextToken()

			# expect DOES (after newline if indented) or COMMA
			if self.checkToken(TokenType.COMMA):
				self.nextToken()

				if self.checkToken(TokenType.NEWLINE):
					self.nl()

				self.match(TokenType.HINT, False)
			else:
				if self.checkToken(TokenType.NEWLINE):
					self.nl()
				if self.checkToken(TokenType.ENDCLASS):
					break
				else:
					self.match(TokenType.DOES, False)
					break

		self.classesDeclared[classname] = classdict

	# if self.checkToken(TokenType.NEWLINE):
	# 	self.nl()

	if self.checkToken(TokenType.ENDCLASS):
		self.match(TokenType.ENDCLASS)
		return

	self.match(TokenType.DOES)
	self.nl()

	while not self.checkToken(TokenType.ENDCLASS):
		self.match(TokenType.METH, False)
		# methodcode = funcFUNCTION(self, TokenType, inclass=True, classname=classname, classdict=classdict)
		funcFUNCTION(self, TokenType, inclass=True, classname=classname, classdict=classdict)
		# print(methodcode)
		# self.emitter.emitLine(methodcode)
		if self.checkToken(TokenType.NEWLINE):
			self.nl()

	self.match(TokenType.ENDCLASS)
	self.upScope()

# "INSTAN" ident "OF" ident
def funcINSTAN(self, TokenType):
	self.nextToken()

	instname = self.curToken.text
	self.match(TokenType.IDENT)
	if self.checkVar(instname):
		self.abort(f'Instance: Variable "{instname}" already exists', self.curToken.line)

	self.match(TokenType.OF)

	classname = self.curToken.text
	self.match(TokenType.IDENT)
	if not classname in self.classesDeclared:
		self.abort(f'Instance: Cannot make an instance of undeclared class "{classname}"', self.curToken.line)

	formatstr = instname + '___INSTANCEOF_' + classname + '_CLASS___'
	# classdict = self.classesDeclared[classname]
	fielddict = self.classesDeclared[classname]["fields"]

	# emit fields
	for field in fielddict:
		# self.emitter.
		vartype = fielddict[field].type
		if vartype == TokenType.STRING:
			self.emitter.emitLine('char *'+formatstr+field+';')
		elif vartype == TokenType.BOOL:
			self.emitter.emitLine('bool '+formatstr+field+';')
		elif vartype == TokenType.NUMBER:
			self.emitter.emitLine('float '+formatstr+field+';')
		self.addVar(instname + "'s " + field, vartype, \
			not fielddict[field].mutable, True, classname)

	methoddict = self.classesDeclared[classname]["methods"]
	for method in methoddict:
		self.functionsDeclared[\
		instname + "'s " + method\
		] = methoddict[method]["props"]

	print(list(self.functionsDeclared))
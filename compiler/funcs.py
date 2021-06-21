import sys
from lex import *
import random
import string
# from tokens import DataTypes

def randStr(N):
	# generates a random string of length N
	return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(N))

# "PRINT" (expression | string)
def funcPRINT(host, TokenType):
	host.nextToken()

	if host.checkToken(TokenType.STRING):
		# Simple string, so print it.
		host.emitter.emitLine("printf(\"" + host.curToken.text + "\");")
		host.nextToken()

	elif host.checkToken(TokenType.NUMBER) and (host.checkPeek(TokenType.NEWLINE) or host.checkPeek(TokenType.EOF)):
		# number
		host.emitter.emitLine("printf(\"" + host.curToken.text + "\\n\");")
		host.nextToken()

	elif host.checkToken(TokenType.IDENT) and (host.checkPeek(TokenType.NEWLINE) or host.checkPeek(TokenType.EOF)):
		# ident
		
		# check if defined
		if not host.curToken.text in host.variablesDeclared:
			host.abort(f"Print: Attempted to print undeclared variable '{host.curToken.text}'")
		
		# detect variable type and emit based off that
		if host.variablesDeclared[host.curToken.text] == TokenType.STRING:
			# var contains string
			host.emitter.emitLine("printf(\"%" + f"s\", {host.curToken.text});")

		elif host.variablesDeclared[host.curToken.text] == TokenType.NUMBER:
			# var contains number
			# the emitted code checks if number is int or float and prints accordingly
			host.emitter.emitLine(f"if(roundf({host.curToken.text}) == {host.curToken.text})"+'{')
			host.emitter.emitLine(f"printf(\"%d\", (int){host.curToken.text});")
			host.emitter.emitLine("}else{")
			# host.emitter.emitLine(f"printf(\"%.3f\", {host.curToken.text});"+'}')
			i = randStr(10)
			a = randStr(10)
			host.emitter.emitLine("int "+i+"=1;");
			host.emitter.emitLine("while(1){");
			host.emitter.emitLine("float "+a+"="+host.curToken.text+"*powf(10,"+i+");");
			host.emitter.emitLine("if("+a+"==(int)"+a+")");
			host.emitter.emitLine("break;");
			host.emitter.emitLine(i+"++;}");
			host.emitter.emitLine("printf(\"%."+"*f\","+i+","+host.curToken.text+");}");

		elif host.variablesDeclared[host.curToken.text] == TokenType.BOOL:
			host.emitter.emitLine("printf(\"%" + f"s\", {host.curToken.text}?\"true\":\"false\");")
		# host.emitter.emitLine("char *string = (char *)" + host.curToken.text + ";")
		# host.emitter.emitLine("printf(\"%" + "s\", " + "string" + ");")
		host.nextToken()

	else:
		# Expect an expression and print the result as a float.
		host.emitter.emit("printf(\"%" + ".3f\", (float)(")
		host.expression()
		host.emitter.emitLine("));")

# "PRINTLN" (expression | string)
def funcPRINTLN(host, TokenType):
	funcPRINT(host, TokenType)
	host.emitter.emitLine('printf(\"\\n\");')
	# host.nextToken()

	# if host.checkToken(TokenType.STRING):
	# 	# Simple string, so print it.
	# 	host.emitter.emitLine("printf(\"" + host.curToken.text + "\\n\");")
	# 	host.nextToken()

	# elif host.checkToken(TokenType.IDENT):
	# 	# ident
	# 	host.emitter.emitLine("printf(\"%" + "s\\n\", " + host.curToken.text + ");")
	# 	host.nextToken()

	# elif host.checkToken(TokenType.NUMBER):
	# 	# number
	# 	host.emitter.emitLine("printf(\"" + host.curToken.text + "\\n\");")
	# 	host.nextToken()

	# else:
	# 	# Expect an expression and print the result as a float.
	# 	host.emitter.emit("printf(\"%" + ".2f\\n\", (float)(")
	# 	host.expression()
	# 	host.emitter.emitLine("));")

# "IF" (comparison ["OR" comparison]) "THEN" block "ENDIF"		
def funcIF(host, TokenType):
	host.nextToken()
	host.emitter.emit("if((")
	host.comparison()

	host.match(TokenType.THEN)
	host.nl()
	host.emitter.emitLine(")){")

	# Zero or more statements in the body.
	while not host.checkToken(TokenType.ENDIF):
		host.statement()
		if host.checkToken(TokenType.ELSE):
			host.emitter.emitLine("}else{")
			host.nextToken()
			host.nextToken()

	host.match(TokenType.ENDIF)
	host.emitter.emitLine("}")

# "WHILE" comparison "REPEAT" block "ENDWHILE"
def funcWHILE(host, TokenType):
	host.nextToken()
	host.emitter.emit("while((")
	host.comparison()

	host.match(TokenType.REPEAT)
	host.nl()
	host.emitter.emitLine(")){")

	# Zero or more statements in the loop body.
	while not host.checkToken(TokenType.ENDWHILE):
		host.statement()

	host.match(TokenType.ENDWHILE)
	host.emitter.emitLine("}")

# "LABEL" ident
def funcLABEL(host, TokenType):
	host.nextToken()

	# Make sure this label doesn't already exist.
	if host.curToken.text in host.labelsDeclared:
		host.abort("Label: Label already exists: " + host.curToken.text)
	host.labelsDeclared.add(host.curToken.text)

	host.emitter.emitLine(host.curToken.text + ":")
	host.match(TokenType.IDENT)

# "GOTO" ident
def funcGOTO(host, TokenType):
	host.nextToken()
	host.labelsGotoed.add(host.curToken.text)
	host.emitter.emitLine("goto " + host.curToken.text + ";")
	host.match(TokenType.IDENT)

# "SET" ident = expression
def funcSET(host, TokenType):
	host.nextToken()
	
	varname = host.curToken.text
	if not varname in host.variablesDeclared:
		host.abort(f"Set: Variable {varname} not declared")
	host.emitter.emit(varname + ' = ')

	vartype = host.variablesDeclared[varname]

	host.nextToken()
	host.match(TokenType.EQ)

	# check if type is correct (excuse idents)
	if host.curToken.kind != host.variablesDeclared[varname] and not host.checkToken(TokenType.IDENT):
		host.abort('Set: Attempted to assign a ' + host.curToken.kind.name.lower() + ' to a variable declared with type ' + host.variablesDeclared[varname].name.lower() + f' ({host.curToken.text} to {varname})')

	# emit shit
	if host.variablesDeclared[varname] == TokenType.STRING:
		host.emitter.emit("\"" + host.curToken.text + "\";")
		host.match(host.variablesDeclared[varname])
		host.nextToken()

	elif host.variablesDeclared[varname] != TokenType.NUMBER:
		host.emitter.emit(host.curToken.text + ';')
		host.match(host.variablesDeclared[varname])
		host.nextToken()

	# elif host.variablesDeclared[varname]

	else:
		# can be either number or expression
		if not host.checkPeek(TokenType.NEWLINE) and not host.checkPeek(TokenType.EOF):
			# expression
			host.expression()
			host.emitter.emit(';')
		else:
			host.emitter.emit(host.curToken.text + ';')
			host.match(TokenType.NUMBER)
			host.nextToken()

# "DECLARE" type ident = (expression | string | number)
def funcDECLARE(host, TokenType):
	host.nextToken()

	ishinted = False
	hinttoken = None
	templine = ""

	dontcontinue = False
	# host.emitter.emit(host.curToken.text + " = ")

	if host.checkToken(TokenType.HINT):
		# type is hinted. no need for init value
		ishinted = True
		hinttoken = host.curToken

		if host.curToken.text == 'string':
			vartype = TokenType.STRING
		elif host.curToken.text == 'number':
			vartype = TokenType.NUMBER
		elif host.curToken.text == 'bool':
			vartype = TokenType.BOOL

		## host.emitter.emit(host.curToken.emittext + " ")
		templine += host.curToken.emittext + " "
		host.nextToken()

	varname = host.curToken.text
	##  host.emitter.emit(varname)
	templine += varname
	host.match(TokenType.IDENT, False)

	if not ishinted:
		host.nextToken()
		host.match(TokenType.EQ)
		templine += "="
		##  host.emitter.emit("=")

	elif not host.checkPeek(TokenType.NEWLINE) and not host.checkPeek(TokenType.EOF):
		# init value given
		host.nextToken()
		# print(host.peekToken.kind)
		host.match(TokenType.EQ)
		templine += "="
		## host.emitter.emit("=")
	else:
		host.nextToken()
		dontcontinue = True

	if not dontcontinue and not ishinted:
		# if host.checkToken(TokenType.STRING):
		if host.checkToken(TokenType.STRING):
			# variable contains string
			vartype = TokenType.STRING
			##  host.emitter.emit("\"" + host.curToken.text + "\"")
			if not ishinted:
				templine = "char *" + templine
				vartype = TokenType.STRING
			templine += "\""+host.curToken.text+"\""
			host.nextToken()

		elif host.checkToken(TokenType.BOOL):
			# variable contains boolean
			vartype = TokenType.BOOL
			if not ishinted:
				templine = "bool " + templine
				vartype = TokenType.BOOL
			templine += host.curToken.text
			##  host.emitter.emit(host.curToken.text)
			host.nextToken()
				
		else:
			# vartype = TokenType.NUMBER
			if not host.checkPeek(TokenType.NEWLINE) and not host.checkPeek(TokenType.EOF):
				# expression
				if not ishinted:
					templine = "float " + templine
					vartype = TokenType.NUMBER
				templine += host.get_current_expression(True)
				##  host.expression()
			else:
				# number
				## host.emitter.emit(host.curToken.text)
				if not ishinted:
					templine = "float " + templine
					vartype = TokenType.NUMBER
				templine += host.curToken.text
				host.nextToken()

	elif not dontcontinue and ishinted:
		templine += host.curToken.text
		host.match(vartype)

	#  Check if ident exists in symbol table. If not, declare it.
	if varname not in host.variablesDeclared:
		### if host.emitter.override_emit_to_func:
		###    host.variablesDeclared_in_function[varname] = varname in host.variablesDeclared
		host.variablesDeclared[varname] = vartype

		# if vartype == TokenType.STRING:
		#     deftype = 'char *{}'
		# elif vartype == TokenType.NUMBER:
		#     deftype = 'float {}'
		# elif vartype == TokenType.BOOL:
		#     deftype = 'bool {}'     

		# host.nextToken()
		# host.emitter.headerLine(deftype.format(varname) + ";")
		host.emitter.emitLine(templine + ';')
		# host.nextToken()
	
	# var already exists. abort
	else:
		host.abort(f"Declare: Variable '{varname}' is already declared.")

	# host.emitter.emitLine(";")
	# host.nextToken()
	# host.nl()

# "INPUT" ident
def funcINPUT(host, TokenType):
	host.nextToken()

	varname = host.curToken.text

	# check variable exists else abort
	if varname not in host.variablesDeclared:
		host.abort("Input: Attempted to assign input to undeclared variable " + varname)

	vartype = host.variablesDeclared[varname]

	# generate the right scanf format for each data type
	if vartype == TokenType.NUMBER:
		host.emitter.emitLine("scanf(\"%" + "f\", &" + varname + ");")

	elif vartype == TokenType.STRING:
		tempstr = randStr(10)
		host.emitter.emitLine("char "+tempstr+"[1000];")
		host.emitter.emitLine("scanf(\"%" + f"s\", &{tempstr});")
		host.emitter.emitLine(varname+"="+tempstr+";")
		# host.emitter.emitLine("scanf(\"%" + "s\", " + varname + ");")

	elif vartype == TokenType.BOOL:
		# declare and scan a temporary variable to catch the user input
		# so we can check it later (but first convert to lowercase)
		tempvar = "tempvar"+randStr(10)
		host.emitter.emitLine(f"char {tempvar}[5];")
		host.emitter.emitLine("scanf(\"%"+f"s\", {tempvar});")
		# convert to lowercase using:
		# for(int i = 0; str[i]; i++){
		#	str[i] = tolower(str[i]);
		# }
		tempint = "tempint"+randStr(5)
		host.emitter.emitLine(f"for(int {tempint} = 0; {tempvar}[{tempint}]; {tempint}++)"+"{")
		host.emitter.emitLine(f"{tempvar}[{tempint}] = tolower({tempvar}[{tempint}]);"+"}")
		# the rest (compare the lowercase input with 'true' and return true if they are the same, else false)
		host.emitter.emitLine(f"if(strcmp({tempvar}, \"true\")==0)"+"{")
		host.emitter.emitLine(varname + "=true;")
		host.emitter.emitLine("}else{")
		host.emitter.emitLine(varname + "=false;}")

	host.match(TokenType.IDENT)

# "EXIT" (expression | number | ident)
def funcEXIT(host, TokenType):
	host.nextToken()
	
	if host.checkToken(TokenType.NUMBER):
		if not host.checkPeek(TokenType.NEWLINE) and not host.checkPeek(TokenType.EOF):
			# expression
			host.emitter.emit("exit(")
			host.expression()
			host.emitter.emitLine(");")
		
		else:
			# Simple number, exit with it.
			host.emitter.emitLine("exit(" + host.curToken.text + ");")
			host.nextToken()
			
	elif host.checkToken(TokenType.IDENT):
		# ident
		host.emitter.emitLine("exit(" + host.curToken.text + ");")
		host.nextToken()
	else:
		host.abort(f"Exit: Expected numeric exit code, not '{host.curToken.text}' ({host.curToken.kind.name})")

# "FOR" (ident) "COMMA" (expression | number | ident) "COMMA" (expression | number | ident) "COMMA" (expression | number | ident) "DO" block "ENDFOR"
def funcFOR(host, TokenType):

	host.emitter.emit('for(int ')
	host.nextToken()

	host.match(TokenType.IDENT, False)
	forvar = host.curToken.text
	islocal = forvar in host.variablesDeclared
	host.variablesDeclared[forvar] = TokenType.NUMBER
	host.emitter.emit(host.curToken.text + '=')

	host.nextToken()
	host.match(TokenType.COMMA, False)

	for i in range(3):
		host.nextToken()

		if host.checkToken(TokenType.NUMBER):
			if not host.checkPeek(TokenType.COMMA):
				# expression
				# print("expression: ", host.curToken.text, ' and ', host.peekToken.text)
				host.expression()
				# print('expression done. currtoken: ', host.curToken.text)
			else:
				# number
				# print("number: ", host.curToken.text, ' and ', host.peekToken.text)
				host.emitter.emit(host.curToken.text)
				host.nextToken()

		elif host.checkToken(TokenType.IDENT):
			# ident
			if not host.checkPeek(TokenType.COMMA):
				# expression
				# print("expression: ", host.curToken.text, ' and ', host.peekToken.text)
				host.expression()
				# print('expression done. currtoken: ', host.curToken.text)
			else:
				# ident
				# print("ident: ", host.curToken.text, ' and ', host.peekToken.text)
				host.emitter.emit(host.curToken.text)
				host.nextToken()

		else:
			host.abort(f"For: Expected number or expression, not not '{host.curToken.text}' ({host.curToken.kind.name})")

		if i < 2:
			# print(host.curToken.text)
			
			host.match(TokenType.COMMA, False)
			if i == 0:
				host.emitter.emit(';' + forvar + '<=')
			else:
				host.emitter.emit(';' + forvar + '+=')
		else:
			host.match(TokenType.DO)
			host.nl()
			host.emitter.emitLine("){")

	# Zero or more statements in the loop body.
	while not host.checkToken(TokenType.ENDFOR):
		host.statement()

	host.match(TokenType.ENDFOR)
	host.emitter.emitLine("}")
	if islocal:
		host.variablesDeclared.remove(forvar)
		
# "SLEEP" (expression | number | ident)
def funcSLEEP(host, TokenType):
	host.nextToken()
	
	if host.checkToken(TokenType.NUMBER):
		if not host.checkPeek(TokenType.NEWLINE) and not host.checkPeek(TokenType.EOF):
			# expression
			host.emitter.emit("sleep(")
			host.expression()
			host.emitter.emitLine(");")
		
		else:
			# Simple number, exit with it.
			host.emitter.emitLine("sleep(" + host.curToken.text + ");")
			host.nextToken()
			
	elif host.checkToken(TokenType.IDENT):
		# ident
		host.emitter.emitLine("sleep(" + host.curToken.text + ");")
		host.nextToken()
	else:
		host.abort(f"Sleep: Expected number or expression, not '{host.curToken.text}' ({host.curToken.kind.name})")

# "FUNC" ident ["TAKES" (idents)] "DOES" block "ENDFUNC"
def funcFUNCTION(host, TokenType):
	host.nextToken()
	host.emitter.function('void ' + host.curToken.text + '(')
	name = host.curToken.text

	hasargs = False
	localargs = set()
	funcargs = {}

	# Make sure this function doesn't already exist.
	if host.curToken.text in host.functionsDeclared:
		host.abort("Function: Function already exists: " + host.curToken.text)

	host.nextToken()
	if host.checkToken(TokenType.TAKES):

		# host.abort('Functions with arguments are not yet supported. Sorry!')

		hasargs = True
		indented_takes = False
		# has args
		host.nextToken()

		if host.checkToken(TokenType.NEWLINE):
			indented_takes = True
			host.nextToken()

		while not host.checkToken(TokenType.DOES):
			# expect "{HINT} IDENT, " etc..

			host.match(TokenType.HINT, False)
			vartoken = host.curToken
			if host.curToken.text == "number":
				vartype = TokenType.NUMBER
			if host.curToken.text == "string":
				vartype = TokenType.STRING
			if host.curToken.text == "bool":
				vartype = TokenType.BOOL
			host.nextToken()
			host.match(TokenType.IDENT, False)

			# print("varname: " + host.curToken.text + " type: " + vartype.name)
			# print(host.curToken.emittext)
			# host.emitter.function()
			host.emitter.function(vartoken.emittext + " " + host.curToken.text)

			localargs.add((host.curToken.text, (host.curToken.text in host.variablesDeclared))) # append to list of local args and tell wether arg is also global or not
			funcargs[host.curToken.text] = vartype
			host.variablesDeclared[host.curToken.text] = vartype # temporarily append to defined args to avoid false errors

			host.nextToken()
			# expect DOES (after newline if indented) or COMMA
			if host.checkToken(TokenType.COMMA):
				host.emitter.function(',')
				host.nextToken()
			elif indented_takes:
				host.match(TokenType.NEWLINE)
				# host.match(TokenType.NEWLINE):
				host.emitter.function('){\n')
			else:
				host.emitter.function('){\n')

	else:
		# no vars
		host.emitter.function('void) {\n')

	host.match(TokenType.DOES)
	host.nl()
	# Zero or more statements in the function body.
	host.emitter.override_emit_to_func = True
	while not host.checkToken(TokenType.ENDFUNC):
		host.statement()
	host.emitter.override_emit_to_func = False
	host.variablesDeclared_in_function = {}

	host.match(TokenType.ENDFUNC)
	host.emitter.function('}')

	# remove local args from list of args if they dont already exist globally
	if hasargs:
		for arg in localargs:
			if not arg[1]:
				del host.variablesDeclared[arg[0]]
	## remove locally declared variables if not in global scope
	##  for var in host.variablesDeclared_in_function:
	## 	 if not host.variablesDeclared_in_function[var]:
	## 		del host.variablesDeclared[var]

	host.functionsDeclared[name] = funcargs

# "CALL" ident ["WITH" ident ["COMMA" ident etc...]]
def funcCALL(host, TokenType):
	host.nextToken()
	host.match(TokenType.IDENT, False)
	if not host.curToken.text in host.functionsDeclared.keys():
		host.abort("Call: Calling function before declaration: " + host.curToken.text)

	argsamount = len(list(host.functionsDeclared[host.curToken.text]))
	funcname = host.curToken.text
	host.emitter.emit(host.curToken.text + "(")
	host.nextToken()

	# first generate the call of the wrapper but store information for the wrapper in the process
	# if func needs args check for them
	if argsamount > 0:
		# localargs = {}

		if not host.checkToken(TokenType.WITH):
			host.abort(f"Call: Function '{funcname}' requires {argsamount} arguments")
		
		host.nextToken()
		for i in range(argsamount):
			# host.emitter.emit(host.curToken.text)
			argname = list(host.functionsDeclared[funcname])[i]
			
			if host.checkToken(host.functionsDeclared[funcname][argname]):
				# given parameter is correct datatype (no ident)
				host.emitter.emit(host.curToken.text)

			elif host.checkToken(TokenType.IDENT):
				# given parameter is ident, check if correct datatype

				# first check if var exists
				if host.curToken.text not in host.variablesDeclared:
					host.abort("Call: Variable \"" + host.curToken.text + "\" not defined")


				if not host.variablesDeclared[host.curToken.text] \
					== host.functionsDeclared[funcname][argname]:
					host.abort("Call: Parameter \""+argname+"\" needs to be of type " + \
						host.functionsDeclared[funcname][argname])
				else:
					host.emitter.emit(host.curToken.text)
			else:
				# wrong parameter
				host.abort("Call: Parameter \""+argname+"\" needs to be of type " + \
						host.functionsDeclared[funcname][argname].name)

			host.nextToken()

			if i < argsamount - 1:
				host.match(TokenType.COMMA)
				host.emitter.emit(',')
			else:
				host.emitter.emitLine(');')

	else:
		# no args
		host.emitter.emitLine(');')

	if not host.checkToken(TokenType.NEWLINE):
		host.abort(f"Call: Function '{funcname}' takes {argsamount} arguments")

# "RETURN" (ident | number | string | bool | expression)
def funcRETURN(host, TokenType):
	host.abort("Return is not yet supported. Sorry!")

	# cannot return if not inside function
	if not host.emitter.override_emit_to_func:
		host.abort("Return: Cannot return outside of a function")


	host.nextToken()
	
	if host.checkToken(TokenType.NUMBER):
		if not host.checkPeek(TokenType.NEWLINE) and not host.checkPeek(TokenType.EOF):
			# expression
			host.emitter.emit("return(")
			host.expression()
			host.emitter.emitLine(");")
		
		else:
			# Simple number, exit with it.
			host.emitter.emitLine("return " + host.curToken.text + ";")
			host.nextToken()
			
	elif host.checkToken(TokenType.IDENT) or host.checkToken(TokenType.BOOL):
		# ident or bool
		host.emitter.emitLine("return " + host.curToken.text + ";")
		host.nextToken()

	elif host.checkToken(TokenType.STRING):
		# string
		host.emitter.emitLine("return \"" + host.curToken.text + "\";")
		host.nextToken()

	else:
		host.abort(f"Return: Expected return value, not '{host.curToken.text}' ({host.curToken.kind.name})")

# "StartWith HINT IDENT, etc..
def funcSTARTW(host, TokenType):
	host.nextToken()

	if not host.allowstartwith:
		host.abort("StartWith: This syntax can only be used at the start of the script")

	def handlevar(isfirst=False):
		# emit type and varname to main parameters
		if not isfirst:
			host.emitter.emitMainArg(",")
		host.emitter.emitMainArg(host.curToken.emittext + " ")
		host.emitter.emitMainCall(host.curToken.emittext + " ")

		if host.curToken.text == "number":
			vartype = TokenType.NUMBER
		if host.curToken.text == "string":
			vartype = TokenType.STRING
		if host.curToken.text == "bool":
			vartype = TokenType.BOOL

		host.match(TokenType.HINT)
		host.emitter.emitMainArg(host.curToken.text)
		host.emitter.maincallargs.append(host.curToken.text)
		host.variablesDeclared[host.curToken.text] = vartype

		host.emitter.emitMainCall(host.curToken.text)
		varname = host.curToken.text
		if vartype == TokenType.NUMBER:
			host.emitter.emitMainCallLine("=atof(argv["+\
				str(len(host.emitter.maincallargs))+"]);")
		elif vartype == TokenType.STRING:
			host.emitter.emitMainCallLine("=argv["+\
				str(len(host.emitter.maincallargs))+"];")
		elif vartype == TokenType.BOOL:
			host.emitter.emitMainCallLine(";")
			host.emitter.emitMainCallLine("if(strcmp(argv["+\
				str(len(host.emitter.maincallargs))+"], \"true\") == 0)")
			host.emitter.emitMainCallLine(varname+"=true;")
			host.emitter.emitMainCallLine("else")
			host.emitter.emitMainCallLine(varname+"=false;")

		host.match(TokenType.IDENT)

	handlevar(True)

	while not host.checkToken(TokenType.NEWLINE):
		host.match(TokenType.COMMA)
		handlevar()
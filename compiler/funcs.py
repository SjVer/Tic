import sys
from lex import *
import random
import string

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
			host.emitter.emitLine(f"printf(\"%.3f\", {host.curToken.text});"+'}')

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

# "IF" (comparison) "THEN" block "ENDIF"		
def funcIF(host, TokenType):
	host.nextToken()
	host.emitter.emit("if(")
	host.comparison()

	host.match(TokenType.THEN)
	host.nl()
	host.emitter.emitLine("){")

	# Zero or more statements in the body.
	while not host.checkToken(TokenType.ENDIF):
		host.statement()

	host.match(TokenType.ENDIF)
	host.emitter.emitLine("}")

# "WHILE" comparison "REPEAT" block "ENDWHILE"
def funcWHILE(host, TokenType):
	host.nextToken()
	host.emitter.emit("while(")
	host.comparison()

	host.match(TokenType.REPEAT)
	host.nl()
	host.emitter.emitLine("){")

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
	host.labelsDeclared[host.curToken.text] = TokenType.NUMBER

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
		# host.match(host.variablesDeclared[varname])
		host.nextToken()

	elif host.variablesDeclared[varname] != TokenType.NUMBER:
		host.emitter.emit(host.curToken.text + ';')
		# host.match(host.variablesDeclared[varname])
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
			# host.match(TokenType.NUMBER)
			host.nextToken()

# "DECLARE" type ident = (expression | string | number)
def funcDECLARE(host, TokenType):
	host.nextToken()

	varname = host.curToken.text

	host.emitter.emit(host.curToken.text + " = ")
	host.match(TokenType.IDENT)
	host.match(TokenType.EQ)

	if host.checkToken(TokenType.STRING):
	    # variable contains string
	    vartype = TokenType.STRING
	    host.emitter.emit("\"" + host.curToken.text + "\"")
	    host.nextToken()

	elif host.checkToken(TokenType.BOOL):
		# variable contains boolean
	    host.emitter.emit(host.curToken.text)
	    vartype = TokenType.BOOL
	    host.nextToken()
			
	else:
		vartype = TokenType.NUMBER
		if not host.checkPeek(TokenType.NEWLINE) and not host.checkPeek(TokenType.EOF):
			# expression
			host.expression()
		else:
			# number
			host.emitter.emit(host.curToken.text)
			host.nextToken()

	#  Check if ident exists in symbol table. If not, declare it.
	if varname not in host.variablesDeclared:
	    host.variablesDeclared[varname] = vartype

	    if vartype == TokenType.STRING:
	        deftype = 'char *{}'
	    elif vartype == TokenType.NUMBER:
	        deftype = 'float {}'
	    elif vartype == TokenType.BOOL:
	        deftype = 'bool {}'     

	    # host.nextToken()
	    host.emitter.headerLine(deftype.format(varname) + ";")
	
	# var already exists. abort
	else:
		host.abort(f"Declare: Variable '{varname}' is already declared.")

	host.emitter.emitLine(";")

# "INPUT" ident
def funcINPUT(host, TokenType):
	host.nextToken()

	varname = host.curToken.text

	# check variable exists else abort
	if varname not in host.variablesDeclared:
		host.abort("Input: Attempted to assign input to undeclared variable " + varname)
	#host.variablesDeclared[host.curToken.text] = 'lol'
	# 	host.emitter.headerLine("float " + host.curToken.text + ";")

	# Emit scanf but also validate the input. If invalid, set the variable to 0 and clear the input.
	# host.emitter.emitLine("if(0 == scanf(\"%" + "f\", &" + host.curToken.text + ")) {")
	# host.emitter.emitLine(host.curToken.text + " = 0;")
	# host.emitter.emit("scanf(\"%")
	# host.emitter.emitLine("*s\");")
	# host.emitter.emitLine("}")
	vartype = host.variablesDeclared[varname]

	# generate the right scanf format for each data type
	if vartype == TokenType.NUMBER:
		host.emitter.emitLine("scanf(\"%" + "f\", &" + varname + ");")

	elif vartype == TokenType.STRING:
		host.emitter.emitLine("scanf(\"%" + "s\", " + varname + ");")

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
			host.emitter.emit("return (")
			host.expression()
			host.emitter.emitLine(");")
		
		else:
			# Simple number, exit with it.
			host.emitter.emitLine("return " + host.curToken.text + ";")
			host.nextToken()
			
	elif host.checkToken(TokenType.IDENT):
		# ident
		host.emitter.emitLine("return " + host.curToken.text + ";")
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

	# Make sure this function doesn't already exist.
	if host.curToken.text in host.functionsDeclared:
		host.abort("Function: Function already exists: " + host.curToken.text)

	host.nextToken()
	if host.checkToken(TokenType.TAKES):
		hasargs = True
		# has args
		host.nextToken()
		while not host.checkToken(TokenType.DOES):
			# expect ident
			host.match(TokenType.IDENT, False)
			host.emitter.function('void *' + host.curToken.text)

			localargs.add((host.curToken.text, (host.curToken.text in host.variablesDeclared))) # append to list of local args and tell wether arg is also global or not
			host.variablesDeclared[host.curToken.text] = 'something'# temporarily append to defined args to avoid false errors

			host.nextToken()
			# expect DOES or COMMA
			if host.checkToken(TokenType.DOES):
				host.emitter.function('){\nprintf(\"\\n\\n%'+'i\", x);')
			elif host.checkToken(TokenType.COMMA):
				host.emitter.function(',')
				host.nextToken()

			## BUSY WITH PASSING VARS TO FUNCTION N STUFF
	else:
		host.emitter.function('void) {\n')

	host.match(TokenType.DOES)
	host.nl()
	# Zero or more statements in the function body.
	host.emitter.override_emit_to_func = True
	while not host.checkToken(TokenType.ENDFUNC):
		host.statement()
	host.emitter.override_emit_to_func = False

	host.match(TokenType.ENDFUNC)
	host.emitter.function('}')

	# remove local args from list of args if they dont already exist globally
	if hasargs:
		for arg in localargs:
			if not arg[1]:
				del host.variablesDeclared[arg[0]]

	host.functionsDeclared[name] = len(localargs) # tuple of name and amount of args

# "CALL" ident ["WITH" ident ["COMMA" ident etc...]]
def funcCALL(host, TokenType):
	host.nextToken()
	host.match(TokenType.IDENT, False)
	if not host.curToken.text in host.functionsDeclared.keys():
		host.abort("Call: Calling function before setment: " + host.curToken.text)

	# instead of calling the function generate and call a wrapper to make sure that arguments work

	argsamount = host.functionsDeclared[host.curToken.text]
	funcname = host.curToken.text
	host.nextToken()

	# first generate the call of the wrapper but store information for the wrapper in the process
	# if func needs args check for them
	if argsamount > 0:
		host.emitter.emit(host.curToken.text + ('1' if host.curToken.text + '_wrapper' in host.emitter.wrappers else '') + '_wrapper(')
		localargs = {}

		if not host.checkToken(TokenType.WITH):
			host.abort(f"Call: Function '{funcname}' requires {argsamount} arguments")
		
		for i in range(argsamount):
			host.nextToken()
			if host.checkToken(TokenType.NUMBER):
				if not host.checkPeek(TokenType.NEWLINE) and not host.checkPeek(TokenType.EOF) and not host.checkPeek(TokenType.COMMA):
					# expression
					host.emitter.emit("(")
					localargs[host.get_current_expression()] = 'float'
					host.expression()
					host.emitter.emit(")")
				
				else:
					# Simple number, exit with it.
					host.emitter.emit(host.curToken.text)
					localargs[host.curToken.text] = 'float' if '.' in host.curToken.text else 'int'
					host.nextToken()
					
			elif host.checkToken(TokenType.IDENT):
				# ident
				host.emitter.emit(host.curToken.text)
				# handle var type
				vartype = host.variablesDeclared[host.curToken.text]
				localargs[host.curToken.text] = (
					'string' if vartype == TokenType.STRING else
					'float' if vartype == TokenType.NUMBER else
					'bool' if vartype == TokenType.BOOL else 'float')
				host.nextToken()

			elif host.checkToken(TokenType.BOOL):
				# bool
				host.emitter.emit(host.curToken.text)
				localargs[host.curToken.text] = 'bool'
				host.nextToken()

			elif host.checkToken(TokenType.STRING):
				# string
				localargs[host.curToken.text] = 'char*'
				host.emitter.emit("\"" + host.curToken.text + "\"")
				host.nextToken()

			else:
				host.abort(f"Call: Expected number, string, bool or expression, not '{host.curToken.text}' ({host.curToken.kind.name}) Function '{funcname}' takes {argsamount} arguments")
			if i != argsamount - 1:
				host.emitter.emit(',')
			else:
				host.emitter.emit(');\n')
		# host.nextToken()

		# generate wrapper for calling to fix the parameter issue
		wrappercode = f"void {funcname + ('1' if funcname + '_wrapper' in host.emitter.wrappers else '')}_wrapper("

		randvars = []
		for arg, i in zip(localargs.keys(), range(len(localargs.keys()))):
			# iterate over the local arguments
			randvar = "randvar"+randStr(5)
			while randvar in randvars:
				randvar = "randvar"+randStr(5)
			randvars.append(randvar)
			wrappercode += localargs[arg] + ' ' + randvar
			if i != argsamount - 1:
				wrappercode += ','


		wrappercode += "){\n" + funcname + "("

		for arg, varname in zip(localargs.keys(), randvars):
			wrappercode += '&' if localargs[arg] in ['float', 'int', 'bool', ''] else ''
			wrappercode += varname
			if not varname == randvars[-1]:
				wrappercode += ','

		wrappercode += ');}'

		host.emitter.wrapperFunc(wrappercode)

	else:
		# no args
		host.emitter.emitLine(funcname + '();')

	if not host.checkToken(TokenType.NEWLINE):
		host.abort(f"Call: Function '{funcname}' takes {argsamount} arguments")

import sys
from lex import *

# "PRINT" (expression | string)
def funcPRINT(host, TokenType):
	host.nextToken()

	if host.checkToken(TokenType.STRING):
		# Simple string, so print it.
		host.emitter.emitLine("printf(\"" + host.curToken.text + "\");")
		host.nextToken()

	else:
		# Expect an expression and print the result as a float.
		host.emitter.emit("printf(\"%" + ".2f\", (float)(")
		host.expression()
		host.emitter.emitLine("));")

# "PRINTLN" (expression | string)
def funcPRINTLN(host, TokenType):
	host.nextToken()

	if host.checkToken(TokenType.STRING):
		# Simple string, so print it.
		host.emitter.emitLine("printf(\"" + host.curToken.text + "\\n\");")
		host.nextToken()

	else:
		# Expect an expression and print the result as a float.
		host.emitter.emit("printf(\"%" + ".2f\\n\", (float)(")
		host.expression()
		host.emitter.emitLine("));")

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
	host.labelsDeclared.add(host.curToken.text)

	host.emitter.emitLine(host.curToken.text + ":")
	host.match(TokenType.IDENT)

# "GOTO" ident
def funcGOTO(host, TokenType):
	host.nextToken()
	host.labelsGotoed.add(host.curToken.text)
	host.emitter.emitLine("goto " + host.curToken.text + ";")
	host.match(TokenType.IDENT)

# "ASSIGN" ident = expression
def funcASSIGN(host, TokenType):
	host.nextToken()

	#  Check if ident exists in symbol table. If not, declare it.
	if host.curToken.text not in host.symbols:
		host.symbols.add(host.curToken.text)
		host.emitter.headerLine("float " + host.curToken.text + ";")

	host.emitter.emit(host.curToken.text + " = ")
	host.match(TokenType.IDENT)
	host.match(TokenType.EQ)
	
	host.expression()
	host.emitter.emitLine(";")

# "INPUT" ident
def funcINPUT(host, TokenType):
	host.nextToken()

	# If variable doesn't already exist, declare it.
	if host.curToken.text not in host.symbols:
		host.symbols.add(host.curToken.text)
		host.emitter.headerLine("float " + host.curToken.text + ";")

	# Emit scanf but also validate the input. If invalid, set the variable to 0 and clear the input.
	host.emitter.emitLine("if(0 == scanf(\"%" + "f\", &" + host.curToken.text + ")) {")
	host.emitter.emitLine(host.curToken.text + " = 0;")
	host.emitter.emit("scanf(\"%")
	host.emitter.emitLine("*s\");")
	host.emitter.emitLine("}")
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

# "FOR" (ident) (expression | number | ident) (expression | number | ident) (expression | number | ident) "DO" block "ENDFOR"
def funcFOR(host, TokenType):

	host.emitter.emit('for(int ')
	host.nextToken()

	host.match(TokenType.IDENT, False)
	forvar = host.curToken.text
	islocal = forvar in host.symbols
	host.symbols.add(forvar)
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
		host.symbols.remove(forvar)
		
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
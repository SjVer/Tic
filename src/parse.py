import sys
from lex import *

# Parser object keeps track of current token and checks if the code matches the grammar.
class Parser:
	def __init__(self, lexer, emitter):
		self.lexer = lexer
		self.emitter = emitter
		
		self.symbols = set()        # Variables declared so far.
		self.labelsDeclared = set() # Labels declared so far.
		self.labelsGotoed = set()   # Labels goto'ed so far.
		
		self.curToken = None
		self.peekToken = None
		self.nextToken()
		self.nextToken()    # Call this twice to initialize current and peek.

	# Return true if the current token matches.
	def checkToken(self, kind):
		return kind == self.curToken.kind

	# Return true if the next token matches.
	def checkPeek(self, kind):
		return kind == self.peekToken.kind

	def checkPeekMultiple(self, *args):
		for kind in args:
			if kind == self.peekToken.kind:
				return true
		return false

	# Try to match current token. If not, error. Advances the current token.
	def match(self, kind, next = True):
		if not self.checkToken(kind):
			self.abort("Expected " + kind.name + ", got " + self.curToken.kind.name)
		if next:
			self.nextToken()

	# Advances the current token.
	def nextToken(self):
		self.curToken = self.peekToken
		self.peekToken = self.lexer.getToken()
		# No need to worry about passing the EOF, lexer handles that.

	def abort(self, message):
		sys.exit("Error. " + message)
	
	
	# Production rules.
		
	# program ::= {statement}
	def program(self):
		self.emitter.headerLine("#include <stdio.h>")
		self.emitter.headerLine("#include <unistd.h>")
		self.emitter.headerLine("int main(void){")
		
		# Since some newlines are required in our grammar, need to skip the excess.
		while self.checkToken(TokenType.NEWLINE):
			self.nextToken()

		# Parse all the statements in the program.
		while not self.checkToken(TokenType.EOF):
			self.statement()

		# Wrap things up.
		self.emitter.emitLine("return 0;")
		self.emitter.emitLine("}")

		# Check that each label referenced in a GOTO is declared.
		for label in self.labelsGotoed:
			if label not in self.labelsDeclared:
				self.abort("Attempting to GoTo to undeclared label: " + label)
	
	# One of the following statements...
	def statement(self):
		# Check the first token to see what kind of statement this is.

		# "PRINT" (expression | string)
		if self.checkToken(TokenType.PRINT):
			self.nextToken()

			if self.checkToken(TokenType.STRING):
				# Simple string, so print it.
				self.emitter.emitLine("printf(\"" + self.curToken.text + "\");")
				self.nextToken()

			else:
				# Expect an expression and print the result as a float.
				self.emitter.emit("printf(\"%" + "d\", (")
				self.expression()
				self.emitter.emitLine("));")

		# "PRINTLN" (expression | string)
		elif self.checkToken(TokenType.PRINTLN):
			self.nextToken()

			if self.checkToken(TokenType.STRING):
				# Simple string, so print it.
				self.emitter.emitLine("printf(\"" + self.curToken.text + "\\n\");")
				self.nextToken()

			else:
				# Expect an expression and print the result as a float.
				self.emitter.emit("printf(\"%" + "d\\n\", (")
				self.expression()
				self.emitter.emitLine("));")
				
		# "IF" comparison "THEN" block "ENDIF"
		elif self.checkToken(TokenType.IF):
			self.nextToken()
			self.emitter.emit("if(")
			self.comparison()

			self.match(TokenType.THEN)
			self.nl()
			self.emitter.emitLine("){")

			# Zero or more statements in the body.
			while not self.checkToken(TokenType.ENDIF):
				self.statement()

			self.match(TokenType.ENDIF)
			self.emitter.emitLine("}")

		# "WHILE" comparison "REPEAT" block "ENDWHILE"
		elif self.checkToken(TokenType.WHILE):
			self.nextToken()
			self.emitter.emit("while(")
			self.comparison()

			self.match(TokenType.REPEAT)
			self.nl()
			self.emitter.emitLine("){")

			# Zero or more statements in the loop body.
			while not self.checkToken(TokenType.ENDWHILE):
				self.statement()

			self.match(TokenType.ENDWHILE)
			self.emitter.emitLine("}")
		
		# "LABEL" ident
		elif self.checkToken(TokenType.LABEL):
			self.nextToken()

			# Make sure this label doesn't already exist.
			if self.curToken.text in self.labelsDeclared:
				self.abort("Label already exists: " + self.curToken.text)
			self.labelsDeclared.add(self.curToken.text)

			self.emitter.emitLine(self.curToken.text + ":")
			self.match(TokenType.IDENT)

		# "GOTO" ident
		elif self.checkToken(TokenType.GOTO):
			self.nextToken()
			self.labelsGotoed.add(self.curToken.text)
			self.emitter.emitLine("goto " + self.curToken.text + ";")
			self.match(TokenType.IDENT)

		# "ASSIGN" ident = expression
		elif self.checkToken(TokenType.ASSIGN):
			self.nextToken()

			#  Check if ident exists in symbol table. If not, declare it.
			if self.curToken.text not in self.symbols:
				self.symbols.add(self.curToken.text)
				self.emitter.headerLine("float " + self.curToken.text + ";")

			self.emitter.emit(self.curToken.text + " = ")
			self.match(TokenType.IDENT)
			self.match(TokenType.EQ)
			
			self.expression()
			self.emitter.emitLine(";")

		# "INPUT" ident
		elif self.checkToken(TokenType.INPUT):
			self.nextToken()

			# If variable doesn't already exist, declare it.
			if self.curToken.text not in self.symbols:
				self.symbols.add(self.curToken.text)
				self.emitter.headerLine("float " + self.curToken.text + ";")

			# Emit scanf but also validate the input. If invalid, set the variable to 0 and clear the input.
			self.emitter.emitLine("if(0 == scanf(\"%" + "f\", &" + self.curToken.text + ")) {")
			self.emitter.emitLine(self.curToken.text + " = 0;")
			self.emitter.emit("scanf(\"%")
			self.emitter.emitLine("*s\");")
			self.emitter.emitLine("}")
			self.match(TokenType.IDENT)

		# "EXIT" (expression | number | ident)
		elif self.checkToken(TokenType.EXIT):
			self.nextToken()
			
			if self.checkToken(TokenType.NUMBER):
				if not self.checkPeek(TokenType.NEWLINE) and not self.checkPeek(TokenType.EOF):
					# expression
					self.emitter.emit("return (")
					self.expression()
					self.emitter.emitLine(");")
				
				else:
					# Simple number, exit with it.
					self.emitter.emitLine("return " + self.curToken.text + ";")
					self.nextToken()
					
			elif self.checkToken(TokenType.IDENT):
				# ident
				self.emitter.emitLine("return " + self.curToken.text + ";")
				self.nextToken()
			else:
				self.abort("Expected numeric exit code, not '" + self.curToken.text + "'")
		
		# "FOR" (ident) (expression | number | ident) (expression | number | ident) (expression | number | ident) "DO" block "ENDFOR"
		elif self.checkToken(TokenType.FOR):

			self.emitter.emit('for(int ')
			self.nextToken()

			self.match(TokenType.IDENT, False)
			forvar = self.curToken.text
			islocal = forvar in self.symbols
			self.symbols.add(forvar)
			self.emitter.emit(self.curToken.text + '=')

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

				elif self.checkToken(TokenType.IDENT):
					# ident
					self.emitter.emit(self.curToken.text)

				else:
					self.abort("Expected number or expression, not '" + self.curToken.text + "'")

				if i < 2:
					self.nextToken()
					self.match(TokenType.COMMA, False)
					if i == 0:
						self.emitter.emit(';' + forvar + '<=')
					else:
						self.emitter.emit(';' + forvar + '+=')
				else:
					self.match(TokenType.DO)
					self.nl()
					self.emitter.emitLine("){")

			# Zero or more statements in the loop body.
			while not self.checkToken(TokenType.ENDFOR):
				self.statement()

			self.match(TokenType.ENDFOR)
			self.emitter.emitLine("}")
			if islocal:
				self.symbols.remove(forvar)
				

		# "SLEEP" (expression | number | ident)
		elif self.checkToken(TokenType.SLEEP):
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
				self.abort("Expected number or expression, not '" + self.curToken.text + "'") 
		
		# This is not a valid statement. Error!
		else:
			self.abort("Invalid statement at '" + self.curToken.text + "' (" + self.curToken.kind.name + ")")
			
		# Newline.
		self.nl()
	
	# comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+
	def comparison(self):
		self.expression()
		# Must be at least one comparison operator and another expression.
		if self.isComparisonOperator():
			self.emitter.emit(self.curToken.text)
			self.nextToken()
			self.expression()
		# Can have 0 or more comparison operator and expressions.
		while self.isComparisonOperator():
			self.emitter.emit(self.curToken.text)
			self.nextToken()
			self.expression()
	
	# expression ::= term {( "-" | "+" ) term}
	def expression(self):
		self.term()
		# Can have 0 or more +/- and expressions.
		while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
			self.emitter.emit(self.curToken.text)
			self.nextToken()
			self.term()


	# term ::= unary {( "/" | "*" ) unary}
	def term(self):
		self.unary()
		# Can have 0 or more *// and expressions.
		while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
			self.emitter.emit(self.curToken.text)
			self.nextToken()
			self.unary()


	# unary ::= ["+" | "-"] primary
	def unary(self):
		# Optional unary +/-
		if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
			self.emitter.emit(self.curToken.text)
			self.nextToken()        
		self.primary()
	
	# primary ::= number | ident
	def primary(self):
		if self.checkToken(TokenType.NUMBER): 
			self.emitter.emit(self.curToken.text)
			self.nextToken()
		elif self.checkToken(TokenType.IDENT):
			# Ensure the variable already exists.
			if self.curToken.text not in self.symbols:
				self.abort("Referencing variable before assignment: " + self.curToken.text)

			self.emitter.emit(self.curToken.text)
			self.nextToken()
		else:
			# Error!
			self.abort("Unexpected token at '" + self.curToken.text + "'")
	
	# nl ::= '\n'+
	def nl(self):
		
		# Require at least one newline.
		self.match(TokenType.NEWLINE)
		# But we will allow extra newlines too, of course.
		while self.checkToken(TokenType.NEWLINE):
			self.nextToken()
			
	# Return true if the current token is a comparison operator.
	def isComparisonOperator(self):
		return (self.checkToken(TokenType.GT) or
			self.checkToken(TokenType.GTEQ) or
			self.checkToken(TokenType.LT) or
			self.checkToken(TokenType.LTEQ) or
			self.checkToken(TokenType.EQEQ) or
			self.checkToken(TokenType.NOTEQ) )

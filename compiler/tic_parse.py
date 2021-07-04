import sys, os
from tic_lex import *
from tic_tokens import Types
from copy import deepcopy
from termcolor import colored

class Scope:
	def __init__(self, variables: dict = {}):
		self.variablesDeclared = variables

class VarProperties:
	def __init__(self, vartype: TokenType, mutable: bool):
		self.type: TokenType = vartype
		self.mutable: bool = mutable

class FuncPropterties:
	def __init__(self, params: dict, optargc: int, doesreturn: bool, returntype: TokenType = None):
		self.params: dict = params
		self.optargc: int = optargc
		self.doesreturn: bool = doesreturn
		self.returntype: TokenType = returntype

# Parser object keeps track of current token and checks if the code matches the grammar.
class Parser:
	def __init__(self, lexer, emitter, verbose, generating_header, sourcefile, stdlibpath):
		self.lexer = lexer
		self.emitter = emitter
		self.verbose = verbose
		self.generating_header = generating_header
		self.sourcefile = sourcefile
		self.stdlibpath = stdlibpath

		self.includes = set() # includes needed
		self.headerfiles = set()

		self.variablesDeclared = {} # Variables declared so far. key is name and value is type

		self.labelsDeclared = set() # Labels declared so far.
		self.labelsGotoed = set()   # Labels goto'ed so far.

		self.functionsDeclared = {} # key is name and value is amount of args and their types

		self.parsing_function = False
		self.parsing_loop = False
		self.parsing_expr = False

		self.scopes = []
		self.curscope = None

		self.allowstartwith = True
		self.used_experimental = False

		self.curToken = None
		self.peekToken = None
		self.prevToken = None
		self.stmtToken = None

		self.addVar('THIS_FILE', TokenType.STRING, True)
		if not self.generating_header:
			self.emitter.includeLine('#define THIS_FILE "'+self.sourcefile+'"', True)
		self.includes.add('stdio')
		self.emitter.includes += '#include <stdio.h>\n'
		self.nextToken(doprint=False)
		self.nextToken(doprint=False)    # Call this twice to initialize current and peek.

	# Return true if the current token matches.
	def checkToken(self, *kinds) -> bool:
		for kind in kinds:
			if self.curToken.kind == kind:
				return True
		return False

	# Return true if the next token matches.
	def checkPeek(self, *kinds) -> bool:
		for kind in kinds:
			if self.peekToken.kind == kind:
				return True
		return False

	def checkType(self, *types) -> bool:
		for toktype in types:
			if self.curToken.kind.value.type == toktype:
				return True
		return False

	def checkPeekType(self, *types) -> bool:
		for toktype in types:
			if self.peekToken.kind.value.type == toktype:
				return True
		return False

	# Try to match current token. If not, error. Advances the current token.
	def match(self, kind, next = True) -> None:
		if not self.checkToken(kind):
			self.abort("Expected " + kind.name + ", got " + 
				self.curToken.kind.name + " ('" + self.curToken.text + "')", self.curToken.line)
		if next:
			self.nextToken()

	# Check if var exists in correct scope (and if of correct type if kind is given)
	def checkVar(self, varname, kind = False) -> bool:
		if kind:
			return varname in (self.curscope.variablesDeclared if self.curscope else self.variablesDeclared) \
			and (self.curscope.variablesDeclared[varname].type if self.curscope else self.variablesDeclared[varname].type) == kind
		return varname in (self.curscope.variablesDeclared if self.curscope else self.variablesDeclared)

	# gets dict of all vars in current scope
	def getVars(self) -> dict:
		if self.curscope:
			return self.curscope.variablesDeclared.copy()
		return self.variablesDeclared.copy()

	# Adds a variable to the current scope
	def addVar(self, varname, kind, const) -> None:
		props = VarProperties(kind, const)
		if self.curscope:
			self.curscope.variablesDeclared[varname] = props
		else:
			self.variablesDeclared[varname] = props

	# gets type of var
	def getVarType(self, varname):
		if not self.checkVar(varname):
			raise ValueError(varname + ' does not exist so cant get type')
		if self.curscope:
			return self.curscope.variablesDeclared[varname].type
		return self.variablesDeclared[varname].type

	def checkVarMutability(self, varname):
		if not self.checkVar(varname):
			return False
		elif self.curscope:
			return self.curscope.variablesDeclared[varname].mutable
		return self.variablesDeclared[varname].mutable

	def addFunc(self, name, funcargs, optargc, doesreturn, returntype):
		props = FuncPropterties(funcargs, optargc, doesreturn)
		if doesreturn:
			props.returntype = returntype
		self.functionsDeclared[name] = props

	# Creates a scope that inherits all variables from current scope
	def createChildScope(self) -> Scope:
		return Scope((self.curscope.variablesDeclared.copy() if self.curscope \
			else self.variablesDeclared.copy()))

	# goes down a new scope
	def downScope(self) -> None:
		scope = self.createChildScope()
		self.scopes.append(scope)
		self.curscope = self.scopes[-1]
		return scope      

	# Goes back up one scope
	def upScope(self) -> None:
		self.scopes.pop()
		self.curscope = self.scopes[-1] if len(self.scopes) != 0 else None

	# Advances the current token.
	def nextToken(self, templexer = None, doprint=True) -> None:
		self.curToken = self.peekToken

		if templexer == None:
			self.peekToken = self.lexer.getToken()
			# No need to worry about passing the EOF, lexer handles that.

			# check for includes and add to headers if needed
			if self.curToken != None and self.curToken.kind.value.include != None:
				for include in self.curToken.kind.value.include:
					self.include(include)
		else:
			self.peekToken = templexer.getToken()

		# if self.curToken:
			# print(colored('nextToken'+(' in expression' if self.parsing_expr else '')+': '+self.curToken.kind.name + ' ' + \
				# str(self.curToken.line) + ' "' + self.curToken.text + '"', 'green'))

	def backToken(self):
		prevToken = self.curToken.prevToken
		self.peekToken = self.curToken
		self.curToken = prevToken
		self.prevToken = self.curToken.prevToken

	# Adds a header to the included headers if it isn't already included
	def include(self, header, inlib=True) -> None:
		if header.endswith('.h'):
			header = header[:-2]
		if not header in self.includes:
			self.includes.add(header)
			if inlib:
				self.emitter.includeLine(f"#include <{header}.h>")
			else:
				self.emitter.includeLine(f"#include \"{header}.h\"")

	# Aborts with message n shit
	def abort(self, message, line=False, inclstmtline=True) -> None:
		for file in self.headerfiles:
			os.remove(file)

		if not isinstance(line, int):
			raise ValueError

		msg = colored("Parse Error", 'red', attrs=['bold']) + ": " + message + '.'

		if self.parsing_expr:
			msg += " (while parsing an expression)"

		if line:
			msg += " (at line "+str(line)+""
			if inclstmtline:
				msg += " in statement "+self.stmtToken.kind.name+" at line "+str(self.stmtToken.line)+")\n"
			else:
				msg += ")\n"
			with open(self.sourcefile, 'r') as f:
				lines = f.readlines()

				if len(lines) < line+1:
					if len(lines) > 2:
						msg += "\n    "+(' ' if line-2 < 10 else '')+str(line-2)+'│ '+lines[line-3].strip('\n')+''
					
					if len(lines) > 1:
						msg += "\n    "+(' ' if line-1 < 10 else '')+str(line-1)+'│ '+lines[line-2].strip('\n')+''
					
					msg += "\n "+colored("-> "+(' ' if line < 10 else '')+str(line), "red", attrs=['bold'])+'│ '+\
						lines[line-1].strip('\n')+''

				elif line-1 < 1:
					msg += "\n "+colored("-> "+(' ' if line < 10 else '')+str(line), "red", attrs=['bold'])+'│ '+\
						lines[line-1].strip('\n')+''

					if len(lines) > 2:
						msg += "\n    "+(' ' if line-1 < 10 else '')+str(line+1)+'│ '+lines[line].strip('\n')+''
					
					if len(lines) > 3:
						msg += "\n    "+(' ' if line-2 < 10 else '')+str(line+2)+'│ '+lines[line+1].strip('\n')+''
					
				else:
					msg += "\n    "+(' ' if line-1 < 10 else '')+str(line-1)+'│ '+lines[line-2].strip('\n')+''
					msg += "\n "+(' ' if line < 10 else '')+colored("-> "+str(line), "red", attrs=['bold'])+'│ '+\
						lines[line-1].strip('\n')+''
					msg += "\n    "+(' ' if line+1 < 10 else '')+str(line+1)+'│ '+lines[line].strip('\n')+''

		
		# msg += '\n\nCurrent Token: ' + self.curToken.kind.name + ' ("' + self.curToken.text.strip('\n') + '")'
		# msg += '\nToken chain: '
		# tmp = ""
		# for i in range(5):
		# 	tmp += self.curToken.kind.name + '!'
		# 	self.backToken()
		# tmp = tmp.split('!')
		# tmp.reverse()
		# msg += tmp[0] + ', '.join(tmp[1:])

		# msg += "\nUpcoming tokens: "
		# for i in range(2):
		# 	self.nextToken()
		# 	msg += self.curToken.kind.name + ', '
		# self.nextToken()
		# msg += self.curToken.kind.name

		msg += "\n\nIf you wish to report a bug, create an issue at https://github.com/SjVer/Tic or message sjoerd@marsenaar.com"
		# raise AttributeError ("FOR DEBUGGING")
		sys.exit(msg)

	# prints only if verbose
	def print(self, message="") -> None:
		if self.verbose:
			print(message)


	# gets current expression as string
	def get_current_expression(self) -> str:
		# if use_templexer:
			# oldcur, oldpeek = self.curToken, self.peekToken
			# templexer = deepcopy(self.lexer)
		# else:
			# templexer = self.lexer
		# express = ''
		self.emitter.startGetStr()
		while self.atExpression():
			# express += self.curToken.text
			self.expression()
			# self.nextToken(templexer)
		express = self.emitter.finishGetStr()
		print('returning:',express)
		# if use_templexer:
			# self.curToken, self.peekToken = oldcur, oldpeek
		return express

	def atExpression(self):
		if self.checkToken(TokenType.NUMBER, TokenType.IDENT) and self.checkPeekType(Types.OPERATOR):
			# print('\ncurToken:',self.curToken.kind.name)
			# print('peekToken:',self.peekToken.kind.name)
			# print('so true')
			return True
		elif self.checkToken(TokenType.MINUS) and self.checkPeek(TokenType.NUMBER, TokenType.IDENT, TokenType.CALL):
			# print('\ncurToken:',self.curToken.kind.name)
			# print('peekToken:',self.peekToken.kind.name)
			# print('so true')
			return True
		# print('\ncurToken:',self.curToken.kind.name)
		# print('peekToken:',self.peekToken.kind.name, self.peekToken.kind.value.type)
		# print('so false')
		return False
	# parsing


	# program ::= {statement}
	def program(self) -> None:
		
		# Since some newlines are required in our grammar, need to skip the excess.
		while self.checkToken(TokenType.NEWLINE):
			self.nextToken(doprint=False)

		# Parse all the statements in the program.
		while not self.checkToken(TokenType.EOF):
			self.statement()
			self.allowstartwith = False

		# Check that each label referenced in a GOTO is declared.
		for label in self.labelsGotoed:
			if label not in self.labelsDeclared:
				self.abort("GoTo: Attempting to go to undeclared label: " + label)

		if "START" in self.labelsDeclared:
			# specific entry point specified in script. start from there
			self.emitter.specific_entry = True

	# One of the following statements...
	def statement(self) -> None:
		# Check the first token to see what kind of statement this is.
		
		for kind in TokenType:
			if self.checkToken(kind):
				if kind.value.execute == None:
					self.abort("Invalid statement at '" + self.curToken.text + "' (" + self.curToken.kind.name + ")", self.curToken.line, False)
				# found token
				self.print(colored("\nTOKEN: " + kind.name + " (line "+str(self.curToken.line)+")", 'blue', attrs=['bold']))
				self.emitter.emitLine("// TOKEN: "+self.curToken.kind.name+ " Line: "+str(self.curToken.line), True)

				self.stmtToken = self.curToken
				kind.value.execute(self, TokenType)
				break
			
		# This is not a valid statement. Error!
		else:
			self.abort("Invalid statement: '" + self.curToken.text + "' (" + self.curToken.kind.name + ")", self.curToken.line)
			
		# Newline.
		self.nl()
	
	# comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+
	def comparison(self) -> None:

		if self.checkToken(TokenType.STRING) or (self.checkToken(TokenType.IDENT) and \
		self.checkVar(self.curToken.text, TokenType.STRING)):
			# comparison with string
			self.include('string')
			self.emitter.emit('(strcmp(')

			# == comparison
			if self.peekToken.kind in [TokenType.EQEQ,  TokenType.NOTEQ]:
				eqeq = self.peekToken.kind == TokenType.EQEQ

				# self.nextToken()
				if self.checkToken(TokenType.STRING):
					self.emitter.emit("\""+self.curToken.text+"\"")
				elif self.checkToken(TokenType.IDENT):
					self.emitter.emit(self.curToken.text)

				self.emitter.emit(',')
				self.nextToken() # the == or !=

				self.nextToken()
				if self.checkToken(TokenType.STRING):
					self.emitter.emit("\""+self.curToken.text+"\"")
				elif self.checkToken(TokenType.IDENT):
					self.emitter.emit(self.curToken.text)
				self.emitter.emit(')==0)' if eqeq else ')!=0)')
				self.nextToken()

			elif self.peekToken.kind in [TokenType.THEN, TokenType.OR, \
			TokenType.AND, TokenType.REPEAT, TokenType.DO]:
				# just check if string isnt empty
				if self.checkToken(TokenType.STRING):
					self.emitter.emit("\""+self.curToken.text+"\"")
				elif self.checkToken(TokenType.IDENT):
					self.emitter.emit(self.curToken.text)                
				self.emitter.emit(",\"\")!=0)")
				self.nextToken()

			self.nextToken()

		# if the comparison is just a bool use it
		elif self.checkVar(self.curToken.text, TokenType.BOOL):
			self.emitter.emit(self.curToken.text)
			self.nextToken()
			if self.checkToken(TokenType.THEN):
				return
		else:
			self.expression()
		# Must be at least one comparison operator and another expression.
		if self.isComparisonOperator():
			self.emitter.emit(self.curToken.text)
			self.nextToken()
			self.expression()

		# allow "OR" and "AND"
		if self.checkToken(TokenType.OR):
			self.emitter.emit(')||(')
			self.nextToken()
			self.expression()
		elif self.checkToken(TokenType.AND):
			self.emitter.emit(')&&(')
			self.nextToken()
			self.expression()

		# Can have 0 or more comparison operator and expressions.
		while True:
			if self.isComparisonOperator():
				self.emitter.emit(self.curToken.text)
				self.nextToken()
				self.expression()
			elif self.checkToken(TokenType.OR):
				self.emitter.emit(')||(')
				self.nextToken()
				self.expression()
			elif self.checkToken(TokenType.AND):
				self.emitter.emit(')&&(')
				self.nextToken()
				self.expression()
			else:
				break
	
	# expression ::= floordiv {( "-" | "+" ) floordiv}
	def expression(self) -> None:
		self.parsing_expr = True

		self.floordiv() #term()
		# Can have 0 or more +/- and expressions.
		while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
			self.emitter.emit(self.curToken.text)
			self.nextToken()
			self.floordiv() #term()

		self.parsing_expr = False

	# floordiv ::= term {"//" term}
	def floordiv(self):
		self.emitter.startGetStr()
		self.term()
		left = self.emitter.finishGetStr()
		# print('left:',left)
		# print('curtok:',self.curToken.kind.name)
		isflooring = False
		# self.nextToken()

		while self.checkToken(TokenType.DSLASH, TokenType.MOD):
			isflooring = True
			if self.checkToken(TokenType.DSLASH):
				self.emitter.emit('floor(')
				self.emitter.emit(left)
				self.emitter.emit('/')
			elif self.checkToken(TokenType.MOD):
				self.emitter.emit('fmod(')
				self.emitter.emit(left)
				self.emitter.emit(',')

			# print("floordiv curtoken:",self.curToken.kind)
			if self.checkToken(TokenType.DSLASH, TokenType.MOD):
				self.nextToken()
				self.term()

		if not isflooring:
			self.emitter.emit(left)
		else:
			self.include('math')
			self.emitter.emit(')')

	# term ::= unary {( "/" | "*" ) unary}
	def term(self) -> None:
		self.unary()
		# Can have 0 or more *// and expressions.
		while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
			self.emitter.emit(self.curToken.text)

			self.nextToken()
			self.unary()

	# unary ::= ["+" | "-"] primary
	def unary(self) -> None:
		# Optional unary +/-
		if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
			self.emitter.emit(self.curToken.text)
			self.nextToken()        
		self.primary()
	
	# primary ::= number | ident | bool | string
	def primary(self) -> None:
		if self.checkToken(TokenType.NUMBER) or self.checkToken(TokenType.BOOL): 
			self.emitter.emit(self.curToken.text)
			self.nextToken()

		elif self.checkToken(TokenType.IDENT):
			# Ensure the variable already exists.
			if not self.checkVar(self.curToken.text):
				self.abort("Referencing variable before declaration: " + self.curToken.text)

			elif not self.checkVar(self.curToken.text):
				self.abort('Variable in expression used before declaration: "'+self.curToken.text+'"')
			elif not (self.checkVar(self.curToken.text, TokenType.NUMBER) or self.checkVar(self.curToken.text, TokenType.BOOL)):
				self.abort(f'Variable "{self.curToken.text}" in expression must be of type NUMBER or BOOL, not ' + \
					self.getVarType(self.curToken.text).name, self.curToken.line)

			self.emitter.emit(self.curToken.text)

			self.nextToken()

		else:
			# Error!
			self.abort("Unexpected token at '" + self.curToken.text + "' (in primary)")
	
	# nl ::= '\n'+
	def nl(self) -> None:
		# Require at least one newline.
		self.match(TokenType.NEWLINE)
		# But we will allow extra newlines too, of course.
		while self.checkToken(TokenType.NEWLINE):
			self.nextToken()
			
	# Return true if the current token is a comparison operator.
	def isComparisonOperator(self) -> bool:
		return self.checkToken(TokenType.GT,\
			TokenType.GTEQ,\
			TokenType.LT,\
			TokenType.LTEQ,\
			TokenType.EQEQ,\
			TokenType.NOTEQ)
		
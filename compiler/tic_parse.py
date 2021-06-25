import sys, os
from lex import *
from copy import deepcopy

class Scope:
    def __init__(self, variables: dict = {}):
        self.variablesDeclared = variables

# Parser object keeps track of current token and checks if the code matches the grammar.
class Parser:
    def __init__(self, lexer, emitter, verbose, generating_header):
        self.lexer = lexer
        self.emitter = emitter
        self.verbose = verbose
        self.generating_header = generating_header

        self.includes = set() # includes needed
        self.headerfiles = set()

        self.variablesDeclared = {} # Variables declared so far. key is name and value is type

        self.labelsDeclared = set() # Labels declared so far.
        self.labelsGotoed = set()   # Labels goto'ed so far.

        self.functionsDeclared = {} # key is name and value is amount of args and their types

        self.parsing_loop = False

        self.scopes = []
        self.curscope = None

        self.allowstartwith = True
        self.used_emitc = False

        self.curToken = None
        self.peekToken = None

        self.includes.add('stdio')
        self.emitter.includes += '#include <stdio.h>\n'
        self.nextToken(doprint=False)
        self.nextToken(doprint=False)    # Call this twice to initialize current and peek.

    # Return true if the current token matches.
    def checkToken(self, kind) -> bool:
        #
        return kind == self.curToken.kind

    # Return true if the next token matches.
    def checkPeek(self, kind) -> bool:
        #
        return kind == self.peekToken.kind

    # Try to match current token. If not, error. Advances the current token.
    def match(self, kind, next = True) -> None:
        if not self.checkToken(kind):
            self.abort("Expected " + kind.name + ", got " + 
            	self.curToken.kind.name + " ('" + self.curToken.text + "')", self.curToken.line)
        if next:
            self.nextToken()

    # Check if var exists in correct scope (and if of correct type if kind is given)
    def checkVar(self, varname, kind = False) -> bool:
        # if self.parsing_function:
        #     if kind:
        #         return varname in self.curFuncVars and self.curFuncVars[varname] == kind or \
        #         varname in self.variablesDeclared and self.variablesDeclared[varname] == kind
        #     return varname in self.curFuncVars or varname in self.variablesDeclared
        # elif kind:
        if kind:
            return varname in (self.curscope.variablesDeclared if self.curscope else self.variablesDeclared) \
            and (self.curscope.variablesDeclared[varname] if self.curscope else self.variablesDeclared[varname]) == kind
        return varname in (self.curscope.variablesDeclared if self.curscope else self.variablesDeclared)
        # return varname in self.variablesDeclared

    # Adds a variable to the current scope
    def addVar(self, varname, kind) -> None:
        if self.curscope:
            self.curscope.variablesDeclared[varname] = kind
        else:
            self.variablesDeclared[varname] = kind

    # gets type of var
    def getVarType(self, varname):
        if not self.checkVar(varname):
            raise ValueError(varname + ' does not exist so cant get type')
        if self.curscope:
            return self.curscope.variablesDeclared[varname]
        return self.variablesDeclared[varname]

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

    # Adds a header to the included headers if it isn't already included
    def include(self, header, inlib=True) -> None:
        if not header in self.includes:
            self.includes.add(header)
            if inlib:
                self.emitter.includeLine(f"#include <{header}.h>")
            else:
                self.emitter.includeLine(f"#include \"{header}\"")

    # Aborts with message n shit
    def abort(self, message, line=False) -> None:
        for file in self.headerfiles:
            os.remove(file)

        # raise ValueError("Parse Error: " + message + "\nIf you wish to report a bug, create an issue at https://github.com/SjVer/Tic or message sjoerd@marsenaar.com")
        sys.exit("Parse Error: " + message + ((" (at line "+str(line)+")") if line else "")+\
        "\nIf you wish to report a bug, create an issue at https://github.com/SjVer/Tic or message sjoerd@marsenaar.com")
        # print('test')

    # prints only if verbose
    def print(self, message="") -> None:
        if self.verbose:
            print(message)

    # gets current expression as string
    def get_current_expression(self, save_pos=False) -> str:
        oldcur, oldpeek = self.curToken, self.peekToken
        express = ''
        templexer = deepcopy(self.lexer)
        while not self.checkToken(TokenType.NEWLINE) and not self.checkToken(TokenType.EOF) and not self.checkToken(TokenType.COMMA):
            express += self.curToken.text
            self.nextToken(templexer)
        if not save_pos:
            self.curToken, self.peekToken = oldcur, oldpeek
        return express

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
                    self.abort("Invalid statement at '" + self.curToken.text + "' (" + self.curToken.kind.name + ")", self.curToken.line)
                # found token
                self.print("\nTOKEN: " + kind.name + " (line "+str(self.curToken.line)+")")
                self.emitter.emitLine("// TOKEN: "+self.curToken.kind.name+ " Line: "+str(self.curToken.line), True)

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
    
    # expression ::= term {( "-" | "+" ) term}
    def expression(self, in_func=False) -> None:
        self.term(in_func)
        # Can have 0 or more +/- and expressions.
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            if in_func:
                self.emitter.function(self.curToken.text)
            else:
                self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.term(in_func)

    # term ::= unary {( "/" | "*" ) unary}
    def term(self, in_func=False) -> None:
        self.unary(in_func)
        # Can have 0 or more *// and expressions.
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            if in_func:
                self.emitter.function(self.curToken.text)
            else:
                self.emitter.emit(self.curToken.text)

            self.nextToken()
            self.unary(in_func)

    # unary ::= ["+" | "-"] primary
    def unary(self, in_func=False) -> None:
        # Optional unary +/-
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            if in_func:
                self.emitter.function(self.curToken.text)
            else:
                self.emitter.emit(self.curToken.text)
            self.nextToken()        
        self.primary(in_func)
    
    # primary ::= number | ident | bool | string
    def primary(self, in_func=False) -> None:
        if self.checkToken(TokenType.NUMBER) or self.checkToken(TokenType.BOOL): 
            if in_func:
                self.emitter.function(self.curToken.text)
            else:
                self.emitter.emit(self.curToken.text)
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            # Ensure the variable already exists.
            if not self.checkVar(self.curToken.text):
                self.abort("Referencing variable before declaration: " + self.curToken.text
                    + (f"\nDeclared variables: {', '.join([k for k in (self.variablesDeclared.keys() if not self.parsing_function else self.curFuncVars)])}" if self.verbose else ''))

            if in_func:
                self.emitter.function(self.curToken.text)
            else:
                self.emitter.emit(self.curToken.text)

            self.nextToken()
        # elif self.checkToken(TokenType.STRING):



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
        return (self.checkToken(TokenType.GT) or
            self.checkToken(TokenType.GTEQ) or
            self.checkToken(TokenType.LT) or
            self.checkToken(TokenType.LTEQ) or
            self.checkToken(TokenType.EQEQ) or
            self.checkToken(TokenType.NOTEQ) )
        
import sys
from lex import *
from copy import deepcopy

# import funcs
# from funcs import *

# Parser object keeps track of current token and checks if the code matches the grammar.
class Parser:
    def __init__(self, lexer, emitter, verbose):
        self.lexer = lexer
        self.emitter = emitter
        self.verbose = verbose

        self.includes = set() # includes needed
        self.variablesDeclared = {} # Variables declared so far. key is name and value is type
        self.labelsDeclared = set() # Labels declared so far.
        self.labelsGotoed = set()   # Labels goto'ed so far.
        self.functionsDeclared = {} # key is name and value is amount of args

        self.variablesDeclared_in_function = {} # will be temporarily filled with vars of function
                                                # and emptied when the funcion is done parsing

        self.allowstartwith = True

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken()    # Call this twice to initialize current and peek.

    # Return true if the current token matches.
    def checkToken(self, kind):
        #
        return kind == self.curToken.kind

    # Return true if the next token matches.
    def checkPeek(self, kind):
        #
        return kind == self.peekToken.kind

    # Try to match current token. If not, error. Advances the current token.
    def match(self, kind, next = True):
        if not self.checkToken(kind):
            self.abort("Expected " + kind.name + ", got " + 
            	self.curToken.kind.name + " ('" + self.curToken.text + "')")
        if next:
            self.nextToken()

    # Advances the current token.
    def nextToken(self, templexer = None):
        self.curToken = self.peekToken

        if self.curToken != None and self.verbose:
            print("TOKEN: "+self.curToken.kind.name)

        if templexer == None:
            self.peekToken = self.lexer.getToken()
            # No need to worry about passing the EOF, lexer handles that.

            # check for includes and add to headers if needed
            if self.curToken != None and self.curToken.kind.value.include != None:
                for include in self.curToken.kind.value.include:
                    if not include in self.includes:
                        self.includes.add(include)
                        self.emitter.includeLine(f"#include <{include}.h>")
        else:
            self.peekToken = templexer.getToken()

    def abort(self, message):
        # raise ValueError("Parse Error: " + message + "\nIf you wish to report a bug, create an issue at https://github.com/SjVer/Tic or message sjoerd@marsenaar.com")
        sys.exit("Parse Error: " + message + "\nIf you wish to report a bug, create an issue at https://github.com/SjVer/Tic or message sjoerd@marsenaar.com")
        # print('test')

    # gets current expression as string
    def get_current_expression(self, save_pos=False):
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
    def program(self):
        
        # Since some newlines are required in our grammar, need to skip the excess.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

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
    def statement(self):
        # Check the first token to see what kind of statement this is.
        
        for kind in TokenType:
            if self.checkToken(kind):
                if kind.value.execute == None:
                    self.abort("Invalid statement at '" + self.curToken.text + "' (" + self.curToken.kind.name + ")")
                # found token
                if self.verbose:
                    print("\nTOKEN: " + kind.name)
                kind.value.execute(self, TokenType)
                break
			
        # This is not a valid statement. Error!
        else:
            self.abort("Invalid statement at '" + self.curToken.text + "' (" + self.curToken.kind.name + ")")
            
        # Newline.
        self.nl()
    
    # comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+
    def comparison(self):

        # if the comparison is just a bool use it
        if self.curToken.text in self.variablesDeclared and self.variablesDeclared [self.curToken.text] == TokenType.BOOL:
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
    def expression(self, in_func=False):
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
    def term(self, in_func=False):
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
    def unary(self, in_func=False):
        # Optional unary +/-
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            if in_func:
                self.emitter.function(self.curToken.text)
            else:
                self.emitter.emit(self.curToken.text)
            self.nextToken()        
        self.primary(in_func)
    
    # primary ::= number | ident
    def primary(self, in_func=False):
        if self.checkToken(TokenType.NUMBER) or self.checkToken(TokenType.BOOL): 
            if in_func:
                self.emitter.function(self.curToken.text)
            else:
                self.emitter.emit(self.curToken.text)
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            # Ensure the variable already exists.
            if self.curToken.text not in self.variablesDeclared:
                self.abort("Referencing variable before declaration: " + self.curToken.text
                    + (f"\nDeclared variables: {', '.join([k for k in self.variablesDeclared.keys()])}" if self.verbose else ''))

            if in_func:
                self.emitter.function(self.curToken.text)
            else:
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
        
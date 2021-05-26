import sys
from lex import *

# import funcs
# from funcs import *

# Parser object keeps track of current token and checks if the code matches the grammar.
class Parser:
    def __init__(self, lexer, emitter):
        self.lexer = lexer
        self.emitter = emitter

        self.includes = set()
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

    # Try to match current token. If not, error. Advances the current token.
    def match(self, kind, next = True):
        if not self.checkToken(kind):
            self.abort("Expected " + kind.name + ", got " + 
            	self.curToken.kind.name + " ('" + self.curToken.text + "')")
        if next:
            self.nextToken()

    # Advances the current token.
    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()
        # No need to worry about passing the EOF, lexer handles that.

        # check for includes and add to headers if needed
        if self.curToken != None and self.curToken.kind.value.include != None:
            if not self.curToken.kind.value.include in self.includes:
                self.includes.add(self.curToken.kind.value.include)
                self.emitter.headerLine(f"#include <{self.curToken.kind.value.include}.h>")

    def abort(self, message):
        sys.exit("Parse Error: " + message + "\nIf you wish to report a bug, create an issue at https://github.com/SjVer/AttemptLang or message sjoerd@marsenaar.com")
    
    # Production rules.
        
    # program ::= {statement}
    def program(self):
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
                self.abort("GoTo: Attempting to go to undeclared label: " + label)
    
    # One of the following statements...
    def statement(self):
        # Check the first token to see what kind of statement this is.
        
        for kind in TokenType:
            if self.checkToken(kind):
                # found token
                kind.value.execute(self, TokenType)
                break
			
        # This is not a valid statement. Error!
        else:
            self.abort("Invalid statement at " + self.curToken.text + " (" + self.curToken.kind.name + ")")
            
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

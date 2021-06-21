import enum, sys
from tokens import *

class Lexer:
    def __init__(self, input, verbose):
        self.source = input + '\n' 	# Source code to lex as a string. Append a newline to simplify lexing/parsing the last token/statement.
        self.curChar = ''   		# Current character in the string.
        self.curPos = -1    		# Current position in the string.
        self.nextChar()

        self.verbose = verbose
	
    # Process the next character.
    def nextChar(self):
        self.curPos += 1
        if self.curPos >= len(self.source):
            self.curChar = '\0'  # EOF
        else:
            self.curChar = self.source[self.curPos]
        		
    # Return the lookahead character.
    def peek(self):
        if self.curPos + 1 >= len(self.source):
            return '\0'
        return self.source[self.curPos + 1]

    # Invalid token found, print error message and exit.
    def abort(self, message):
        sys.exit("Lexing error. " + message)

    # Skip whitespace except newlines, which we will use to indicate the end of a statement.
    def skipWhitespace(self):
        while self.curChar == ' ' or self.curChar == '\t' or self.curChar == '\r':
            self.nextChar()

    # Skip comments in the code.
    def skipComment(self):
        if self.curChar == '#':
            while self.curChar != '\n':
                self.nextChar()
                 
    # Return the next token.
    def getToken(self):
        self.skipWhitespace()
        self.skipComment()
        token = None

        # Check the first character of this token to see if we can decide what it is.
        # If it is a multiple character operator (e.g., !=), number, identifier, or keyword then we will process the rest.
        if self.curChar == '+':
            token = Token(self.curChar, TokenType.PLUS)
            
        elif self.curChar == '-':
            token = Token(self.curChar, TokenType.MINUS)
            
        elif self.curChar == '*':
            token = Token(self.curChar, TokenType.ASTERISK)
            
        elif self.curChar == '/':
            token = Token(self.curChar, TokenType.SLASH)
            
        elif self.curChar == '\n':
            token = Token(self.curChar, TokenType.NEWLINE)
        
        elif self.curChar == ',':
            token = Token(self.curChar, TokenType.COMMA)

        elif self.curChar == '\0':
            token = Token('', TokenType.EOF)
            
        elif self.curChar == '=':
            # Check whether this token is = or ==
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.EQEQ)
            else:
                token = Token(self.curChar, TokenType.EQ)
                
        elif self.curChar == '>':
            # Check whether this is token is > or >=
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.GTEQ)
            else:
                token = Token(self.curChar, TokenType.GT)
                
        elif self.curChar == '<':
                # Check whether this is token is < or <=
                if self.peek() == '=':
                    lastChar = self.curChar
                    self.nextChar()
                    token = Token(lastChar + self.curChar, TokenType.LTEQ)
                else:
                    token = Token(self.curChar, TokenType.LT)
                    
        elif self.curChar == '!':
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.NOTEQ)
            else:
                self.abort("Expected !=, got !" + self.peek())
                
        elif self.curChar == '\"':
            # Get characters between quotations.
            self.nextChar()
            startPos = self.curPos

            while self.curChar != '\"':
                # Don't allow special characters in the string. No escape characters, newlines, tabs, or %.
                # We will be using C's printf on this string.
                #if self.curChar == '\r' or self.curChar == '\n' or self.curChar == '\t' or self.curChar == '\\' or self.curChar == '%':
                #    self.abort("Illegal character in string: '" + self.curChar + "'")
                self.nextChar()

            tokText = self.source[startPos : self.curPos] # Get the substring.


            token = Token(tokText, TokenType.STRING)

        elif self.curChar == "{":
            # datatype
            self.nextChar()
            startPos = self.curPos

            while self.curChar != "}":
                self.nextChar()

            tokText = self.source[startPos : self.curPos]

            if not DataTypes.checkIfDataType(tokText):
                self.abort("Expected valid datatype, not \""+tokText+"\"")

            token = Token(tokText, TokenType.HINT, DataTypes.getEmitText(tokText))
            
        elif self.curChar.isdigit():
            # Leading character is a digit, so this must be a number.
            # Get all consecutive digits and decimal if there is one.
            startPos = self.curPos
            while self.peek().isdigit():
                self.nextChar()
            if self.peek() == '.': # Decimal!
                self.nextChar()

                # Must have at least one digit after decimal.
                if not self.peek().isdigit(): 
                    # Error!
                    self.abort("Illegal character in number.")
                while self.peek().isdigit():
                    self.nextChar()

            tokText = self.source[startPos : self.curPos + 1] # Get the substring.
            token = Token(tokText, TokenType.NUMBER)
            
        elif self.curChar.isalpha():
            # Leading character is a letter, so this must be an identifier or a keyword.
            # Get all consecutive alpha numeric characters.
            startPos = self.curPos
            while self.peek().isalnum():
                self.nextChar()

            # Check if the token is in the list of keywords.
            tokText = self.source[startPos : self.curPos + 1] # Get the substring.
            keyword = Token.checkIfKeyword(tokText)
            if keyword == None: # Identifier
                if tokText == 'true' or tokText == 'false':
                    token = Token(tokText, TokenType.BOOL)
                else:
                    token = Token(tokText, TokenType.IDENT)
            else:   # Keyword
                token = Token(tokText, keyword)
                
        else:
            # Unknown token!
            self.abort("Unknown token: '" + self.curChar + "'")
			
        self.nextChar()
        if self.verbose:
            print('LEX: Token ' + token.kind.name)
        return token

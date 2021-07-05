import enum, sys
from tic_tokens import *
from termcolor import colored

class Lexer:
    def __init__(self, input, verbose):
        self.source = input + '\n' 	# Source code to lex as a string. Append a newline to simplify lexing/parsing the last token/statement.
        self.curChar = ''   		# Current character in the string.
        self.curPos = -1    		# Current position in the string.
        self.nextChar()

        self.oldtoken = None
        self.linecount = 1

        self.verbose = verbose
	
    # Process the next character.
    def nextChar(self):
        self.curPos += 1
        if self.curPos >= len(self.source):
            self.curChar = '\0'  # EOF
        else:
            self.curChar = self.source[self.curPos]

    # Return the lookahead character.
    def peek(self, ahead=1):
        if self.curPos + ahead >= len(self.source):
            return '\0'
        return self.source[self.curPos + ahead]

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

            if self.peek() == '*':
                self.nextChar()
                self.nextChar()
                # comment block
                while True:
                    if self.curChar == "*" and self.peek() == '#':
                        self.nextChar()
                        break
                    elif self.curChar == '\n':
                        self.linecount += 1
                    self.nextChar()
                self.nextChar()
                self.nextChar()

            else:
                while self.curChar != '\n':
                    self.nextChar()
                 
    # Return the next token.
    def getToken(self):
        self.skipComment()
        self.skipWhitespace()
        self.skipComment()
        self.skipWhitespace()
        token = None

        # print('curchar: "'+self.curChar+'"')

        # Check the first character of this token to see if we can decide what it is.
        # If it is a multiple character operator (e.g., !=), number, identifier, or keyword then we will process the rest.
        if self.curChar == '+':
            token = Token(self.curChar, TokenType.PLUS, self.oldtoken, self.linecount)
            
        elif self.curChar == '-':
            token = Token(self.curChar, TokenType.MINUS, self.oldtoken, self.linecount)
            
        elif self.curChar == '*':
            token = Token(self.curChar, TokenType.ASTERISK, self.oldtoken, self.linecount)
            
        elif self.curChar == '/':
            if self.peek() == '/':
                self.nextChar()
                token = Token('//', TokenType.DSLASH, self.oldtoken, self.linecount)
            else:
                token = Token(self.curChar, TokenType.SLASH, self.oldtoken, self.linecount)
            
        elif self.curChar == '%':
            token = Token(self.curChar, TokenType.MOD, self.oldtoken, self.linecount)

        elif self.curChar == '\n':
            token = Token(self.curChar, TokenType.NEWLINE, self.oldtoken, self.linecount)
            self.linecount += 1
        
        elif self.curChar == ',':
            token = Token(self.curChar, TokenType.COMMA, self.oldtoken, self.linecount)

        elif self.curChar == '\0':
            token = Token('', TokenType.EOF, self.oldtoken, self.linecount)
            
        elif self.curChar == '=':
            # Check whether this token is = or ==
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.EQEQ, self.oldtoken, self.linecount)
            else:
                token = Token(self.curChar, TokenType.EQ, self.oldtoken, self.linecount)
                
        elif self.curChar == '>':
            # Check whether this is token is > or >=
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.GTEQ, self.oldtoken, self.linecount)
            
            # elif self.peek() == '>':
            #     # >>
            #     self.nextChar()
            #     token = Token('>>', TokenType.ACCESS, self.oldtoken, self.linecount)

            else:
                token = Token(self.curChar, TokenType.GT, self.oldtoken, self.linecount)
                
        elif self.curChar == '<':
                # Check whether this is token is < or <=
                if self.peek() == '=':
                    lastChar = self.curChar
                    self.nextChar()
                    token = Token(lastChar + self.curChar, TokenType.LTEQ, self.oldtoken, self.linecount)
                else:
                    token = Token(self.curChar, TokenType.LT, self.oldtoken, self.linecount)
                    
        elif self.curChar == '!':
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.NOTEQ, self.oldtoken, self.linecount)
            else:
                self.abort("Expected !=, got !" + self.peek() + " at line "+str(self.linecount))
                
        elif self.curChar == '\"':
            # Get characters between quotations.
            self.nextChar()
            startPos = self.curPos

            while self.curChar != '\"':
                # Don't allow special characters in the string. No escape characters, newlines, tabs, or %.
                # We will be using C's printf on this string.
                if self.curChar == '\r' or self.curChar == '\n' or self.curChar == '\t' or self.curChar == '%': # or self.curChar == '\\' 
                   self.abort("Illegal character in string: '" + self.curChar + "' at line "+str(self.linecount))
                
                elif self.curChar == "\\" and (self.peek() in ['"', "%"]):
                    self.nextChar()
                    # self.nextChar()

                self.nextChar()

            tokText = self.source[startPos : self.curPos]#.replace('\\', '\\') # Get the substring.

            token = Token(tokText, TokenType.STRING, self.oldtoken, self.linecount)

        elif self.curChar == "{":
            # datatype
            self.nextChar()
            startPos = self.curPos

            while self.curChar != "}":
                self.nextChar()
                if not self.curChar.isalpha() and not self.curChar == ' ' and not self.curChar == '}':
                    self.abort("Illegal character in type hint at line "+str(self.linecount))

            tokText = self.source[startPos : self.curPos]

            hintprops = HintProps()
            if tokText.startswith('constant '):
                hintprops.const = True
                tokText = tokText.replace('constant ', '')
            elif tokText.startswith('optional '):
                hintprops.opt = True
                tokText = tokText.replace('optional ', '')

            if not DataTypes.checkIfDataType(tokText):
                self.abort("Expected (optinally \"constant\" or \"optional\" followed by a) valid datatype, not \""+tokText+"\" at line "+str(self.linecount))
            hintprops.emittext = DataTypes.getEmitText(tokText)

            token = Token(tokText, TokenType.HINT, self.oldtoken, self.linecount, hintprops)
  
        # elif self.curChar == "'":
        #     if self.peek() == 's' and self.peek(2) == ' ':
        #         self.nextChar()       
        #         self.nextChar()
        #         token = Token("'s", TokenType.ACCESS, self.oldtoken, self.linecount)       

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
            token = Token(tokText, TokenType.NUMBER, self.oldtoken, self.linecount)
            
        elif self.curChar.isalpha() or self.curChar == '_':
            # Leading character is a letter, so this must be an identifier or a keyword.
            # Get all consecutive alpha numeric characters.
            startPos = self.curPos
            while self.peek().isalnum() or self.peek() == '_' or \
                self.peek() == "'" and self.peek(2) == 's' and self.peek(3) == ' ':

                if self.curChar == "'" and self.peek() == 's' and self.peek(2) == ' ':
                    # access field or method
                    self.nextChar()
                    self.nextChar()
                    self.nextChar()
                
                self.nextChar()

            # Check if the token is in the list of keywords.
            tokText = self.source[startPos : self.curPos + 1] # Get the substring.
            keyword = Token.checkIfKeyword(tokText)
            if keyword == None: # Identifier
                if tokText == 'true' or tokText == 'false':
                    token = Token(tokText, TokenType.BOOL, self.oldtoken, self.linecount)
                else:
                    token = Token(tokText, TokenType.IDENT, self.oldtoken, self.linecount)
            else:   # Keyword
                token = Token(tokText, keyword, self.oldtoken, self.linecount)
                
        # else:
        if not token:
            # Unknown token!
            self.abort("Unknown token: '" + self.curChar + "' at line: "+str(self.linecount+1) +\
                "\n" +self.source.split('\n')[self.linecount])
			
        self.nextChar()
        
        # print("\t\toldtoken:", self.oldtoken.kind if self.oldtoken != None else None, 'newtoken:',token.kind)
        self.oldtoken = token

        if self.verbose:
            print(colored('LEX: Token ' + token.kind.name + ', ' + token.text, 'red'))
        return token

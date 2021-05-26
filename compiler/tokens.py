import enum, sys

from funcs import *

# Token contains the original text and the type of token.
class Token:
    def __init__(self, tokenText, tokenKind):
        self.text = tokenText   # The token's actual text. Used for identifiers, strings, and numbers.
        self.kind = tokenKind   # The TokenType that this token is classified as.
        
    @staticmethod
    def checkIfKeyword(tokenText):
        for kind in TokenType:
            # Relies on all keyword enum values being 1XX.
            if kind.value.keyword == tokenText and kind.value.type == Types.KEYWORD:
                return kind
        return None

# types of tokens
class Types(enum.Enum):
    SYMBOL = 0
    KEYWORD = 1
    OPERATOR = 2

# token values
class TokenTypeItem:
    def __init__(self, ttype: Types, keyword: str = None, func = None, include = None):
        self.type = ttype
        if self.type == Types.KEYWORD:
            if keyword == None:
                raise TypeError(f"TokenType of type {self.type.name} needs a keyword as 3rd argument") 
            #if func == None:
            #    raise TypeError(f"TokenType of type {self.type.name} needs a function as 4th argument")
            self.keyword = keyword
            self.execute = func
        else:
            if keyword != None or func != None:
                raise TypeError(f"TokenType of type {self.type.name} only requires an id and type")
            self.keyword = None
            self.execute = None
        self.include = include

# TokenType is our enum for all the types of tokens.
class TokenType(enum.Enum):
    EOF     = TokenTypeItem(Types.SYMBOL)
    NEWLINE = TokenTypeItem(Types.SYMBOL)
    NUMBER  = TokenTypeItem(Types.SYMBOL)
    IDENT   = TokenTypeItem(Types.SYMBOL)
    STRING  = TokenTypeItem(Types.SYMBOL)
    COMMA   = TokenTypeItem(Types.SYMBOL)
    # Keywords. (101-200)
    LABEL   = TokenTypeItem(Types.KEYWORD, 'Label',     func=funcLABEL)
    GOTO    = TokenTypeItem(Types.KEYWORD, 'GoTo',      func=funcGOTO)
    PRINT   = TokenTypeItem(Types.KEYWORD, 'Print',     func=funcPRINT,     include='stdio')
    PRINTLN = TokenTypeItem(Types.KEYWORD, 'PrintLine', func=funcPRINTLN,   include='stdio')
    INPUT   = TokenTypeItem(Types.KEYWORD, 'Input',     func=funcINPUT,     include='stdio')
    ASSIGN  = TokenTypeItem(Types.KEYWORD, 'Assign',    func=funcASSIGN)
    IF      = TokenTypeItem(Types.KEYWORD, 'If',        func=funcIF)
    THEN    = TokenTypeItem(Types.KEYWORD, 'Then')
    ENDIF   = TokenTypeItem(Types.KEYWORD, 'EndIf')
    WHILE   = TokenTypeItem(Types.KEYWORD, 'While',     func=funcWHILE)
    REPEAT  = TokenTypeItem(Types.KEYWORD, 'Repeat')
    ENDWHILE= TokenTypeItem(Types.KEYWORD, 'EndWhile')
    FOR     = TokenTypeItem(Types.KEYWORD, 'For',       func=funcFOR)
    DO      = TokenTypeItem(Types.KEYWORD, 'Do')
    ENDFOR  = TokenTypeItem(Types.KEYWORD, 'EndFor')
    EXIT    = TokenTypeItem(Types.KEYWORD, 'Exit',      func=funcEXIT)
    SLEEP   = TokenTypeItem(Types.KEYWORD, 'Sleep',     func=funcSLEEP,     include='unistd')
    # Operators. (201-)
    EQ      = TokenTypeItem(Types.OPERATOR)
    PLUS    = TokenTypeItem(Types.OPERATOR)
    MINUS   = TokenTypeItem(Types.OPERATOR)
    ASTERISK= TokenTypeItem(Types.OPERATOR)
    SLASH   = TokenTypeItem(Types.OPERATOR)
    EQEQ    = TokenTypeItem(Types.OPERATOR)
    NOTEQ   = TokenTypeItem(Types.OPERATOR)
    LT      = TokenTypeItem(Types.OPERATOR)
    LTEQ    = TokenTypeItem(Types.OPERATOR)
    GT      = TokenTypeItem(Types.OPERATOR)
    GTEQ    = TokenTypeItem(Types.OPERATOR)

import enum, sys

from tic_funcs import *

# Token contains the original text and the type of token.
class Token:
    def __init__(self, tokenText, tokenKind, prevToken, line, hintprops=None):
        self.text = tokenText   # The token's actual text. Used for identifiers, strings, and numbers.
        self.kind = tokenKind   # The TokenType that this token is classified as.
        self.line = line
        self.prevToken = prevToken
        if self.kind == TokenType.HINT:
            if not hintprops:
                raise AttributeError("TokenType.HINT needs hintprops")
            self.hintprops = hintprops

    @staticmethod
    def checkIfKeyword(tokenText):
        for kind in TokenType:
            if kind.value.keyword == tokenText and kind.value.type == Types.KEYWORD:
                return kind
        return None

class HintProps:
    def __init__(self):
        self.emittext = ""
        self.const = False
        self.opt = False


# types of tokens
class Types(enum.Enum):
    SYMBOL = 0
    KEYWORD = 1
    OPERATOR = 2

class DataTypes(enum.Enum):
    string = 'char *'
    number = 'float'
    bool = 'bool'

    @staticmethod
    def checkIfDataType(text) -> bool:
        for kind in DataTypes:
            if kind.name == text:
                return True
        return False

    @staticmethod
    def getEmitText(text):
        for kind in DataTypes:
            if kind.name == text:
                return kind.value
        return None

# token values
class TokenTypeItem:
    def __init__(self, ttype: Types, keyword: str = None, func = None, include: list = None, datatype=None):
        self.type = ttype
        if self.type == Types.KEYWORD:
            if keyword == None:
                raise TypeError(f"TokenType of type {self.type.name} needs a keyword as 3rd argument") 
            #if func == None:
            #    raise TypeError(f"TokenType of type {self.type.name} needs a function as 4th argument")
            self.keyword = keyword
            self.execute = func
        else:
            # if keyword != None or func != None:
                # raise TypeError(f"TokenType of type {self.type.name} only requires an id and type")
            self.keyword = keyword
            self.execute = None
        self.include = include

# TokenType is our enum for all the types of tokens.
class TokenType(enum.Enum):
    EOF     = TokenTypeItem(Types.SYMBOL)
    NEWLINE = TokenTypeItem(Types.SYMBOL)
    NUMBER  = TokenTypeItem(Types.SYMBOL)
    IDENT   = TokenTypeItem(Types.SYMBOL)
    STRING  = TokenTypeItem(Types.SYMBOL,   include=['string'])
    COMMA   = TokenTypeItem(Types.SYMBOL)
    BOOL    = TokenTypeItem(Types.SYMBOL,   include=['stdbool'])
    HINT    = TokenTypeItem(Types.SYMBOL,   include=['stdbool', 'string'])
    # Keywords
    LABEL   = TokenTypeItem(Types.KEYWORD, 'Label',     func=funcLABEL)
    GOTO    = TokenTypeItem(Types.KEYWORD, 'GoTo',      func=funcGOTO)
    PRINT   = TokenTypeItem(Types.KEYWORD, 'Print',     func=funcPRINT,     include=['math'])
    PRINTLN = TokenTypeItem(Types.KEYWORD, 'PrintLine', func=funcPRINTLN,   include=['math'])
    INPUT   = TokenTypeItem(Types.KEYWORD, 'Input',     func=funcINPUT,     include=['string', 'ctype'])
    DECLARE = TokenTypeItem(Types.KEYWORD, 'Declare',   func=funcDECLARE)
    SET     = TokenTypeItem(Types.KEYWORD, 'Set',       func=funcSET)
    IF      = TokenTypeItem(Types.KEYWORD, 'If',        func=funcIF)
    OR      = TokenTypeItem(Types.KEYWORD, 'Or')
    AND     = TokenTypeItem(Types.KEYWORD, 'And')
    THEN    = TokenTypeItem(Types.KEYWORD, 'Then')
    ELSE    = TokenTypeItem(Types.KEYWORD, 'Else')
    ELIF    = TokenTypeItem(Types.KEYWORD, 'ElseIf')
    ENDIF   = TokenTypeItem(Types.KEYWORD, 'EndIf')
    WHILE   = TokenTypeItem(Types.KEYWORD, 'While',     func=funcWHILE)
    REPEAT  = TokenTypeItem(Types.KEYWORD, 'Repeat')
    BREAK   = TokenTypeItem(Types.KEYWORD, 'Break',     func=funcBREAK)
    ENDWHILE= TokenTypeItem(Types.KEYWORD, 'EndWhile')
    FOR     = TokenTypeItem(Types.KEYWORD, 'For',       func=funcFOR)
    DO      = TokenTypeItem(Types.KEYWORD, 'Do')
    ENDFOR  = TokenTypeItem(Types.KEYWORD, 'EndFor')
    EXIT    = TokenTypeItem(Types.KEYWORD, 'Exit',      func=funcEXIT,      include=['stdlib'])
    SLEEP   = TokenTypeItem(Types.KEYWORD, 'Sleep',     func=funcSLEEP,     include=['unistd'])
    FUNC    = TokenTypeItem(Types.KEYWORD, 'Function',  func=funcFUNCTION)
    TAKES   = TokenTypeItem(Types.KEYWORD, 'Takes')
    DOES    = TokenTypeItem(Types.KEYWORD, 'Does')
    ENDFUNC = TokenTypeItem(Types.KEYWORD, 'EndFunction')
    CALL    = TokenTypeItem(Types.KEYWORD, 'Call',      func=funcCALL)
    WITH    = TokenTypeItem(Types.KEYWORD, 'With')
    FRETURN = TokenTypeItem(Types.KEYWORD, 'Returning')
    RETURN  = TokenTypeItem(Types.KEYWORD, 'Return',    func=funcRETURN)
    TO      = TokenTypeItem(Types.KEYWORD, 'To')
    STARTW  = TokenTypeItem(Types.KEYWORD, 'StartWith', func=funcSTARTW,    include=['stdlib', 'string'])
    USE     = TokenTypeItem(Types.KEYWORD, 'Use',       func=funcUSE)
    EMITC   = TokenTypeItem(Types.KEYWORD, 'EmitC',     func=funcEMITC,     include=['stdlib', 'stdbool', 'stdio', 'string', 'math', 'ctype'])
    INCLC   = TokenTypeItem(Types.KEYWORD, 'InclC',     func=funcINCLC)
    # Operators
    EQ      = TokenTypeItem(Types.OPERATOR)
    PLUS    = TokenTypeItem(Types.OPERATOR)
    MINUS   = TokenTypeItem(Types.OPERATOR)
    ASTERISK= TokenTypeItem(Types.OPERATOR)
    SLASH   = TokenTypeItem(Types.OPERATOR)
    DSLASH  = TokenTypeItem(Types.OPERATOR)
    MOD     = TokenTypeItem(Types.OPERATOR)
    EQEQ    = TokenTypeItem(Types.OPERATOR)
    NOTEQ   = TokenTypeItem(Types.OPERATOR)
    LT      = TokenTypeItem(Types.OPERATOR)
    LTEQ    = TokenTypeItem(Types.OPERATOR)
    GT      = TokenTypeItem(Types.OPERATOR)
    GTEQ    = TokenTypeItem(Types.OPERATOR)

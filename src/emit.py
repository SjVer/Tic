import os

# Emitter object keeps track of the generated code and outputs it.
class Emitter:
    def __init__(self, fullPath):
        self.fullPath = fullPath
        
        # make sure dirs exist
        if not os.path.exists(os.path.dirname(fullPath)):
            print("DONT EXITST")
            os.mkdir(os.path.join(os.getcwd(), os.path.dirname(fullPath)))
        
        self.header = ""
        self.code = ""

    def emit(self, code):
        self.code += code

    def emitLine(self, code):
        self.code += code + '\n'

    def headerLine(self, code):
        self.header += code + '\n'

    def writeFile(self):
        with open(self.fullPath, 'w') as outputFile:
            outputFile.write(self.header + self.code)

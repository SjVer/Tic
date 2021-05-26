import os

# Emitter object keeps track of the generated code and outputs it.
class Emitter:
    def __init__(self, tempfile, verbose):
        self.tempfile = tempfile
        
        self.verbose = verbose

        self.header = ""
        self.code = ""

    def emit(self, code):
        if self.verbose:
            print("EMIT: " + code)
        self.code += code

    def emitLine(self, code):
        if self.verbose:
            print("EMIT: " + code)
        self.code += code + '\n'

    def headerLine(self, code):
        self.header += code + '\n'

    def writeFile(self):
        self.tempfile.write(self.header + self.code)
        self.tempfile.seek(0)
        # print(self.header + self.code)
        #with open(self.tempfile, 'w') as outputFile:
        #    outputFile.write(self.header + self.code)

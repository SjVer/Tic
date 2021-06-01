import os

# Emitter object keeps track of the generated code and outputs it.
class Emitter:
    def __init__(self, tempfile, verbose):
        self.tempfile = tempfile
        self.verbose = verbose

        self.override_emit_to_func = False

        self.includes = ""
        self.wrappers = ""
        self.functions = ""
        self.header = ""
        self.code = ""

    def emit(self, code):
        if self.verbose:
            print("EMIT: " + code)
        if self.override_emit_to_func:
            self.functions += code + '\n'
        else:
            self.code += code + '\n'

    def emitLine(self, code):
        if self.verbose:
            print("EMIT: " + code)
        if self.override_emit_to_func:
            self.functions += code + '\n'
        else:
            self.code += code + '\n'

    def headerLine(self, code):
        if self.verbose:
            print("EMIT HEADER: " + code)
        self.header += code + '\n'

    def includeLine(self, code):
        if self.verbose:
            print("EMIT INCLUDE: " + code)
        self.includes += code + '\n'

    def wrapperFunc(self, code):
        if self.verbose:
            print("EMIT WRAPPER: " + code)
        self.wrappers += code + '\n'

    def function(self, code):
        if self.verbose:
            print("EMIT FUNCTION: " + code)
        self.functions += code

    def writeFile(self):
        text = self.includes + "\n\n\n" + self.header + "\n\n//funcs:\n\n" + self.functions + "\n\n//wraps:\n\n" + self.wrappers + "\n\n//code:\n\nint main(void){\n" + self.code + "\nreturn 0;\n}"
        self.tempfile.write(text)
        self.tempfile.seek(0)
        # print("\nCode:\n\n" + text + "\n\n\n")
        print('\n\ngenerated code:\n--------------------------\n')
        os.system('clang-format ' + self.tempfile.name)        
        print('\n\n--------------------------\n\n')
        #with open(self.tempfile, 'w') as outputFile:
        #    outputFile.write(self.header + self.code)

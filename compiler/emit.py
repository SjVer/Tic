import os, subprocess

# Emitter object keeps track of the generated code and outputs it.
class Emitter:
	def __init__(self, tempfile, verbose, keep_c_file):
		self.tempfile = tempfile
		self.verbose = verbose
		self.keep_c_file = keep_c_file

		self.specific_entry = False
		self.override_emit_to_func = False

		self.includes = ""
		self.functions = ""
		self.header = ""
		self.maincall = ""
		self.maincallargs = []
		self.mainargs = ""
		self.code = ""

	def emit(self, code):
		if self.verbose:
			print("EMIT"+(" FUNCTION" if self.override_emit_to_func else "")+": " + code)
		if self.override_emit_to_func:
			self.functions += code + '\n'
		else:
			self.code += code + '\n'

	def emitLine(self, code):
		if self.verbose:
			print("EMIT"+(" FUNCTION" if self.override_emit_to_func else "")+": " + code)
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

	def emitMainArg(self, code):
		if self.verbose:
			print("EMIT MAINARG: "+code)
		self.mainargs += code

	def emitMainCall(self, code):
		if self.verbose:
			print("EMIT MAINCALL: " + code)
		self.maincall += code

	def emitMainCallLine(self, code):
		if self.verbose:
			print("EMIT MAINCALL: " + code)
		self.maincall += code + "\n"

	def function(self, code):
		if self.verbose:
			print("EMIT FUNCTION: " + code)
		self.functions += code

	def writeFile(self):
		code = \
			self.includes + "\n\n" + self.header + \
			"\n\n//funcs:\n\n" + self.functions + \
			"\n\n//code:\n\nint MAIN("+(self.mainargs if self.mainargs != "" else "void")+"){\n" +\
			('goto START;' if self.specific_entry else '') + \
			self.code + "\nreturn 0;\n}" +\
			"\n\n//maincall:\n\nint main(int argc, char *argv[]){\n" + \
			"if(argc-1 != "+str(len(self.maincallargs))+") {printf(\"Expected "+\
			str(len(self.maincallargs))+" arguments, got %"+"d.\\n\", argc-1);return 1;}"+\
			self.maincall + "return MAIN("+\
			(','.join(self.maincallargs) if self.maincallargs != [] else "")+"); }"

		if not self.keep_c_file:
			self.tempfile.write(code)
			self.tempfile.seek(0)

		else:
			with open(self.tempfile, 'w') as f:
				f.write(code)

			text = subprocess.Popen(["clang-format", self.tempfile], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')

			with open(self.tempfile, 'w') as f:
				f.write(text)


		if self.verbose:
			print('\n\ngenerated code:\n--------------------------\n')
			os.system('clang-format ' + (self.tempfile.name if not self.keep_c_file else self.tempfile))        
			print('\n\n--------------------------\n\n')


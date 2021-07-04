import os, subprocess
from termcolor import colored

# Emitter object keeps track of the generated code and outputs it.
class Emitter:
	def __init__(self, tempfile, verbose, keep_c_file, generate_header):
		self.tempfile = tempfile
		self.verbose = verbose
		self.keep_c_file = keep_c_file
		self.generate_header = generate_header

		self.specific_entry = False
		self.override_emit_to_func = False

		self.override_emit_to_str = False
		self.override_emit_to_str_mute = True
		self.tempstr = ""

		self.includes = ""
		self.functions = ""
		self.header = ""
		self.pre_code = ""
		self.maincall = ""
		self.maincallargs = []
		self.mainargs = ""
		self.code = ""

	def startGetStr(self, mute=True):
		self.override_emit_to_str = True
		self.override_emit_to_str_mute = mute
		self.tempstr = ""

	def finishGetStr(self) -> str:
		self.override_emit_to_str = False
		retval = self.tempstr
		self.tempstr = ""
		return retval

	def emit(self, code, silent=False):

		if self.override_emit_to_str:
			if not self.override_emit_to_str_mute and self.verbose and not silent:
				print(colored("EMIT TEMP"+(" FUNCTION" if self.override_emit_to_func else ""), 'yellow')+": " + code.strip())
			self.tempstr += code
			return

		if self.verbose and not silent and not self.override_emit_to_str:
			print(colored("EMIT"+(" FUNCTION" if self.override_emit_to_func else ""), 'yellow')+": " + code.strip())
		if self.override_emit_to_func:
			self.functions += code
		else:
			self.code += code

	def emitLine(self, code, silent=False):
		#
		self.emit(code + '\n', silent)

	def headerLine(self, code, silent=False):
		if self.verbose and not silent:
			print(colored("EMIT HEADER", 'magenta')+": " + code)
		self.header += code + '\n'

	def includeLine(self, code, silent = False):
		if self.verbose and not silent:
			print(colored("EMIT INCLUDE", 'magenta')+": " + code)
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

	def emitBeforeCode(self, code, silent=False):
		if self.verbose and not silent:
			print("EMIT PRE-CODE: "+code.strip())
		self.pre_code += code

	# def function(self, code):
	# 	if self.verbose:
	# 		print("EMIT FUNCTION: " + code)
	# 	self.functions += code

	def writeFile(self, funcs=None, includes=None, variables=None):
		code = self.includes + "\n\n" + self.header
		code += "\n\n" + self.functions
		code += "\n\n//code:\n\nint MAIN("+(self.mainargs if self.mainargs != "" else "void")+"){\n"
		code += self.pre_code + "\n"
		code += ('goto START;' if self.specific_entry else '') + self.code + "\nreturn 0;\n}"
		code += "\n\n//maincall:\n\nint main(int argc, char *argv[]){\n"
		code += "if(argc-1 != "+str(len(self.maincallargs))+") {printf(\"Expected "
		code += str(len(self.maincallargs))+" arguments, got %"+"d.\\n\", argc-1);return 1;}"
		code += self.maincall + "return MAIN("
		code += (','.join(self.maincallargs) if self.maincallargs != [] else "")+"); }"

		if self.generate_header:
			code = ""

			# genererate a line that includes the name, arg amount and args of the function
			# so that the parser of another script can read that

			for func in list(funcs):
				ffunc = funcs[func]
				code += "// DEFFUNC!"+func+"!"
				code +="["+str(len(list(ffunc.params)))+":"+str(ffunc.optargc)+']'
				if funcs[func].params != {}:
					for par in list(ffunc.params):

						code += "{"+par+":"+ffunc.params[par]['type'].name+\
								":"+str(ffunc.params[par]['opt'])+':'+\
								str(ffunc.params[par]['default'])+'}'

				code += '('+str(ffunc.doesreturn)+':'+str(ffunc.returntype).replace('TokenType.', '')+')\n'

			# do the same with variables
			for var in list(variables):
				code += "// DEFVAR!"+var+"!"
				code += "{"+variables[var].type.name+"}"
				code += "["+str(variables[var].mutable)+']\n'

			# do the same with headers
			code += "// INCL["
			for incl in includes:
				code += incl
				if incl != list(includes)[-1]:
					code += ","	
			code += "]\n"

			code += "#ifndef " + os.path.splitext(os.path.basename(self.tempfile))[0].upper() + '_H\n'
			code += "#define " + os.path.splitext(os.path.basename(self.tempfile))[0].upper() + '_H\n'
			code += "\n"+self.includes
			code += "\n\n"+self.header
			code += "\n\n"+self.functions
			code += "\n\n#endif"
			# sys.exit(1)
		# print(code)

		if not self.keep_c_file:
			self.tempfile.write(code)
			self.tempfile.seek(0)
			text = subprocess.Popen(["clang-format", self.tempfile.name], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
			self.tempfile.write(text)
			self.tempfile.seek(0)

		else:
			with open(self.tempfile, 'w') as f:
				f.write(code)

			text = subprocess.Popen(["clang-format", self.tempfile], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')

			with open(self.tempfile, 'w') as f:
				f.write(text)

		if self.verbose:
			print('\n\ngenerated code:\n--------------------------\n')
			os.system('highlight -O ansi --force ' + (self.tempfile.name if not self.keep_c_file else self.tempfile)+'')        
			print('\n--------------------------\n\n')
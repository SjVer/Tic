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
		code = self.includes + "\n\n\n" + self.header + \
		"\n\n//funcs:\n\n" + self.functions + "\n\n//wraps:\n\n" + \
		self.wrappers + "\n\n//code:\n\nint main(void){\n" + ('goto START;' if self.specific_entry else '') + \
		self.code + "\nreturn 0;\n}"

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
			print(text)
			#os.system('clang-format ' + self.tempfile.name)        
			print('\n\n--------------------------\n\n')

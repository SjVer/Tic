class Configs:
	def __init__(self):
		self.current_file_var = "THIS_FILE"

		self.variable_prefix = "USRVAR_"
		self.function_prefix = "USRFUNC_"

		self.field_accessor = "'s "
		self.instance_field_format = "{}___INSTANCEOF_{}_CLASS___{}"
		self.method_format = self.function_prefix + "{}_METHOD_{}"
		self.current_instance_variable = "self"
		self.method_this_prefix = "CURRENTINSTANCEFIELD_"


configs = Configs()
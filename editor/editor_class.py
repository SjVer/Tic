from pathlib import Path
from windows import *
from gi.repository import Pango as pango
from gi.repository import GtkSource as gtksource
from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk
import gi, os, enum

gi.require_version('Gtk', '3.0')

gi.require_version('GtkSource', '3.0')


class Editor(BuildEditor):
	"""Instance for single editor widget"""
	
	def __init__(self, parent_notebook):
		super().__init__() # build
		self.parent_notebook = parent_notebook
		self._filepath = None
		setattr(self.scrollwindow, 'parent_editor', self)
		self.buffer.connect('changed', self.changed)
		self.saved = True
	
	def close_self(self):
		# close this page
		self.parent_notebook.remove_page(self.parent_notebook.get_current_page())	

	def set_text(self, text, no_undo = True):
		if no_undo:
			self.buffer.begin_not_undoable_action()
		self.buffer.set_text(text)
		if no_undo:
			self.buffer.end_not_undoable_action()
		self.update_label()

	def update_label(self):
		self.parent_notebook.update_label_for_child(self.parent_notebook, self.scrollwindow, 
			('*' if not self.saved else '') + self.filename)

	@property
	def filename(self):
		if self._filepath is not None:
			return os.path.split(self._filepath)[1]
		else:
			return "Untitled"
	
	@filename.setter
	def filename(self, value):
		if self._filepath is not None:
			filedir = os.path.split(self._filepath)[0]
			self._filepath = os.path.join(filedir, value)
		else:
			raise AttributeError("filepath not set")
	
	def savefile(self, prompt=True):
		if not prompt:
			filepath = os.path.join(str(Path.home()), self.filename) if self._filepath is None else self._filepath
			self.save_or_load_into_editor(file=filepath, action='save')
		else:
			self.filedialog('Save file as', "SAVE")
		self.saved = True
		self.update_label()
	
	def loadfile(self, prompt=True):
		if not prompt:
			filepath = self._filepath
			if filepath is None:
				self.set_text('')
			else:
				with open(self._filepath, 'w') as f:
					self.set_text(f.read())
					self.buffer.set_language(self.lm.guess_language(self.filename))
		else:
			self.filedialog('Open file', 'OPEN')
		
	def filedialog(self, _title, _action):
		dlg = gtk.FileChooserDialog(title=_title, action=eval(f"gtk.FileChooserAction.{_action}"))
		dlg.add_button(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL)
		
		if _action == "SAVE":
			dlg.add_button(gtk.STOCK_SAVE, gtk.ResponseType.OK)
		elif _action == "OPEN":
			dlg.add_button(gtk.STOCK_OPEN, gtk.ResponseType.OK)
		
		dlg.set_do_overwrite_confirmation(True)
		dlg.set_current_folder(str(Path.home()) if self._filepath is None else os.path.split(self._filepath)[0])
		if _action == 'SAVE':
			dlg.set_current_name(self.filename)
		
		if dlg.run() == gtk.ResponseType.OK:
			newfilepath = os.path.join(dlg.get_current_folder(), dlg.get_filename())
			self._filepath = newfilepath
			if _action == "SAVE":
				print(f'Saving file {self._filepath}')
				with open(self._filepath, 'w') as f:
					f.write(self.buffer.get_text(self.buffer.get_start_iter(), self.buffer.get_end_iter(), True))
				self.saved = True
			elif _action == "OPEN":
				print(f'Loading file {self._filepath}')
				with open(self._filepath, 'r') as f:
					self.set_text(f.read())
					self.buffer.set_language(self.lm.guess_language(self.filename))
				self.saved = True
		dlg.destroy()
		self.update_label()
	
	def save_or_load_into_editor(self, file: str, action: str, editor_is_source: bool = True, text: str = None):
		"""load or save file. if editor_is_true is true, (it is by default) the text will be saved from
		this instance's text view. Else the argument text must be specified. the latter two arguments have
		no effect when action is 'load'"""
		if action == "save":
			if editor_is_source:
				text = self.buffer.get_text(self.buffer.get_start_iter(), self.buffer.get_end_iter(), True)
			
			with open(file, 'w') as f:
				print('saving: ', text)
				f.write(text)

		elif action == "load":
			with open(file, 'r') as f:
				text = f.read()
			self.set_text(text)
			self.buffer.set_language(self.lm.guess_language(self.filename))
		else:
			raise AttributeError(f'action {action} is not allowed. use "save" or "load"')

	def changed(self, *args):
		self.saved = False
		self.update_label()

if __name__ == "__main__":
	# noinspection PyDeprecation
	import imp, os
	
	modpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'attemptide')
	attemptide = imp.load_source('attemptide', modpath)
	os.system('cls' if os.name in ('nt', 'dos') else 'clear')
	attemptide.MainWindow()

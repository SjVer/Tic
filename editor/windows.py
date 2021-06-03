# ----- imports -----
import gi, webbrowser, fcntl, os, tempfile, subprocess, codecs
from subprocess import Popen, PIPE

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
# from gi.repository import Vte as vte
# from gi.repository import Glib as glib
# import glib
from gi.repository import GObject

gi.require_version('GtkSource', '3.0')
from gi.repository import GtkSource as gtksource
from gi.repository import Pango as pango
# -------------------


def update_label_for_child(self, child, text):
	# update specific label
	self.set_tab_label_text(child, text)

class BuildMainWindow:
	def __init__(self):
		print('Building MainWindow')

		self.window = gtk.Window()
		self.window.connect("destroy", gtk.main_quit)

		self.box = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=3)
		self.window.add(self.box)

		# output view
		self.output_view = gtk.TextView()
		# self.box.pack_end(self.output_view, False, True, 0)
		self.output_view.set_size_request(10, 150)
		self.output_view.set_editable(False)
		self.output_view.set_left_margin(10)
		self.output_view.modify_font(pango.FontDescription("monospace 11"))
		# self.output_view.hide()

		self.notebook = gtk.Notebook()
		setattr(self.notebook, "update_label_for_child", update_label_for_child)
		self.box.pack_end(self.notebook, True, True, 0)

		# menu stuff
		self.menubar_box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.menubar_box.set_homogeneous(False)
		self.box.pack_start(self.menubar_box, False, True, 0)
		self.menubar = gtk.MenuBar()
		# self.menubar.modify_bg(gtk.StateType.NORMAL, gdk.Color(60355,60355,60355))
		self.menubar.set_hexpand(True)
		self.menubar_box.pack_start(self.menubar, False, True, 0)

		# accels
		self.accelgr = gtk.AccelGroup()
		self.window.add_accel_group(self.accelgr)
		key, mod = gtk.accelerator_parse('Escape')
		self.accelgr.connect(key, mod, gtk.AccelFlags.VISIBLE, self.hide_terminal)

		# menuitems

		# file
		self.filemenu = self.FileSubMenu()
		self.filem = gtk.MenuItem("File")
		self.filem.set_submenu(self.filemenu)
		self.menubar.append(self.filem)

		# edit
		self.editmenu = self.EditSubMenu()
		self.editm = gtk.MenuItem('Edit')
		self.editm.set_submenu(self.editmenu)
		self.menubar.append(self.editm)

		# run
		self.runmenu = self.RunSubMenu()
		self.runm = gtk.MenuItem('Run')
		self.runm.set_submenu(self.runmenu)
		self.menubar.append(self.runm)

		# help
		self.help_item = gtk.MenuItem(label='Help')
		self.help_item.connect('activate', self.on_help_clicked)
		self.menubar.append(self.help_item)
		
	def FileSubMenu(self):
		menu = gtk.Menu()

		self.file_menu_item_new = gtk.MenuItem(label='New')
		self.file_menu_item_new.connect('activate', self.new_editor)
		menu.append(self.file_menu_item_new)
		key, mod = gtk.accelerator_parse("<Control>N")
		self.file_menu_item_new.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		self.file_menu_item_open = gtk.MenuItem(label='Open')
		x = True
		self.file_menu_item_open.connect('activate', self.new_editor_load )
		menu.append(self.file_menu_item_open)
		key, mod = gtk.accelerator_parse("<Control>O")
		self.file_menu_item_open.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		self.file_menu_item_close = gtk.MenuItem(label='Close')
		self.file_menu_item_close.connect('activate', self.remove_current_page)
		menu.append(self.file_menu_item_close)
		key, mod = gtk.accelerator_parse("<Control>W")
		self.file_menu_item_close.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		self.file_menu_item_save = gtk.MenuItem(label='Save')
		self.file_menu_item_save.connect('activate', self.save_current_page)
		menu.append(self.file_menu_item_save)
		key, mod = gtk.accelerator_parse("<Control>S")
		self.file_menu_item_save.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		self.file_menu_item_save_as = gtk.MenuItem(label='Save As')
		self.file_menu_item_save_as.connect('activate', self.save_current_page_as)
		menu.append(self.file_menu_item_save_as)
		key, mod = gtk.accelerator_parse("<Control><Shift>S")
		self.file_menu_item_save_as.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		menu.append(gtk.SeparatorMenuItem())

		self.file_menu_item_quit = gtk.MenuItem(label='Quit')
		self.file_menu_item_quit.connect('activate', self.main_quit)
		menu.append(self.file_menu_item_quit)
		key, mod = gtk.accelerator_parse("<Control>Q")
		self.file_menu_item_quit.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		menu.show_all()
		return menu

	def EditSubMenu(self):
		menu = gtk.Menu()

		# undo
		self.edit_menu_item_undo = gtk.MenuItem(label='Undo')
		self.edit_menu_item_undo.connect('activate', self.undo_current_editor)
		menu.append(self.edit_menu_item_undo)
		key, mod = gtk.accelerator_parse("<Control>Z")
		self.edit_menu_item_undo.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		# redo
		self.edit_menu_item_redo = gtk.MenuItem(label='Redo')
		self.edit_menu_item_redo.connect('activate', self.redo_current_editor)
		menu.append(self.edit_menu_item_redo)
		key, mod = gtk.accelerator_parse("<Control>Y")
		self.edit_menu_item_redo.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)
		
		menu.append(gtk.SeparatorMenuItem())

		# cut
		self.edit_menu_item_cut = gtk.MenuItem(label='Cut')
		self.edit_menu_item_cut.connect('activate', print)
		menu.append(self.edit_menu_item_cut)
		key, mod = gtk.accelerator_parse("<Control>X")
		self.edit_menu_item_cut.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		# copy
		self.edit_menu_item_copy = gtk.MenuItem(label='Copy')
		self.edit_menu_item_copy.connect('activate', print)
		menu.append(self.edit_menu_item_copy)
		key, mod = gtk.accelerator_parse("<Control>C")
		self.edit_menu_item_copy.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		# paste
		self.edit_menu_item_paste = gtk.MenuItem(label='Paste')
		self.edit_menu_item_paste.connect('activate', print)
		menu.append(self.edit_menu_item_paste)
		key, mod = gtk.accelerator_parse("<Control>V")
		self.edit_menu_item_paste.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		# select all
		self.edit_menu_item_select_all = gtk.MenuItem(label='Select all')
		self.edit_menu_item_select_all.connect('activate', print)
		menu.append(self.edit_menu_item_select_all)
		key, mod = gtk.accelerator_parse("<Control>A")
		self.edit_menu_item_select_all.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		menu.append(gtk.SeparatorMenuItem())
		
		# find
		self.edit_menu_item_find = gtk.MenuItem(label='Find')
		self.edit_menu_item_find.connect('activate', print)
		menu.append(self.edit_menu_item_find)
		key, mod = gtk.accelerator_parse("<Control>F")
		self.edit_menu_item_find.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		# replace
		self.edit_menu_item_replace = gtk.MenuItem(label='Replace')
		self.edit_menu_item_replace.connect('activate', print)
		menu.append(self.edit_menu_item_replace)
		key, mod = gtk.accelerator_parse("<Control>Z")
		self.edit_menu_item_replace.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		# menu.append(gtk.SeparatorMenuItem())

		menu.show_all()
		return menu

	def RunSubMenu(self):
		menu = gtk.Menu()

		self.run_menu_item_run = gtk.MenuItem(label='Run')
		self.run_menu_item_run.connect('activate', self.run)
		menu.append(self.run_menu_item_run)
		key, mod = gtk.accelerator_parse("<Control>B")
		self.run_menu_item_run.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		self.run_menu_item_run_in_terminal = gtk.MenuItem(label='Run in terminal')
		self.run_menu_item_run_in_terminal.connect('activate', self.run_in_terminal)
		menu.append(self.run_menu_item_run_in_terminal)
		key, mod = gtk.accelerator_parse("<Control><Shift>B")
		self.run_menu_item_run_in_terminal.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		#self.run_menu_item_run_in_terminal_input = gtk.MenuItem(label='Run with input')
		# self.run_menu_item_run_in_terminal_input.connect('activate', self.run_in_terminal_input)
		#menu.append(self.run_menu_item_run_in_terminal_input)

		menu.append(gtk.SeparatorMenuItem())

		#self.run_menu_item_compile = gtk.MenuItem(label='Compile only')
		# self.run_menu_item_compile.connect('activate', self.compile)
		#menu.append(self.run_menu_item_compile)
		#key, mod = gtk.accelerator_parse("<Control><Shift>C")
		#self.run_menu_item_compile.add_accelerator('activate', self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		#menu.append(gtk.SeparatorMenuItem())

		self.run_menu_item_hide = gtk.MenuItem(label='Hide terminal')
		self.run_menu_item_hide.connect('activate', self.hide_terminal)
		menu.append(self.run_menu_item_hide)
		key, mod = gtk.accelerator_parse("Escape")
		self.run_menu_item_hide.add_accelerator("activate", self.accelgr, key, mod, gtk.AccelFlags.VISIBLE)

		menu.show_all()
		return menu

	def on_help_clicked(self, button):
		# redirect to webpage
		webbrowser.open("https://github.com/SjVer/Tic")

	def remove_current_page(self, *args):
		# remove current editor
		if self.notebook.get_n_pages() > 1 or True:
			self.notebook.remove_page(self.notebook.get_current_page())

	def toggle_show_output(self):
		if self.output_view.get_visible():
			self.output_view.hide()
		else:
			self.output_view.show()

	def non_block_read(self, output):
	    ''' even in a thread, a normal read with block until the buffer is full '''
	    fd = output.fileno()
	    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
	    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
	    op = output.read()
	    if op == None:
	        return ''
	    return op.decode('utf-8')

	def update_run_output(self):
		buf = self.output_view.get_buffer()
		buf.set_text(buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True) + self.non_block_read(self.proc.stdout))
		return self.proc.poll() is None

	def run(self, *args):
		self.show_terminal(True)

		ed = self.notebook.get_children()[self.notebook.get_current_page()].parent_editor
		self.output_view.get_buffer().set_text('')

		if ed._filepath is None or not ed.saved:
			def response(dlg, response):
				if response == gtk.ResponseType.YES:
					ed.savefile()
					dlg.destroy()
					self.run()
				else:
					dlg.destroy()
				return
			dlg = gtk.MessageDialog(parent=self.window,
					flags=gtk.DialogFlags.MODAL,
					type=gtk.MessageType.WARNING,
					buttons=gtk.ButtonsType.YES_NO,
					message_format=f"Script {ed.filename} has unsaved changes. Do you wish to save them first?")
			dlg.connect('response', response)
			dlg.show()

		elif not os.path.exists(ed._filepath):
			def destroy(dlg, *args):
				dlg.destroy()
			dlg = gtk.MessageDialog(parent=self.window,
					flags=gtk.DialogFlags.MODAL,
					type=gtk.MessageType.MESSAGE_ERROR,
					buttons=gtk.ButtonsType.OK,
					message_format=f"File {ed._filepath} does not exist!.")
			dlg.connect("response", destroy)
			dlg.show()
			return

		binFileHandle, binFileName = tempfile.mkstemp()

		compile_command =["/usr/bin/ticcomp", ed._filepath, "-o", binFileName]
		p = Popen(compile_command, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
		output, error = p.communicate()
		output = output.decode("utf-8")
		error = error.decode("utf-8")

		print('done', p.returncode)
		if p.returncode != 0:
			self.failed_compile(p.returncode, error)
			return

		os.close(binFileHandle)
		p = Popen(binFileName, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=1)
		p.stdin.write(str.encode('1'))

		output, error = p.communicate()
		output = output.decode("utf-8")

		self.output_view.get_buffer().set_text(output)
		os.remove(binFileName)

	def failed_compile(self, exit_code, text):
		def destroy(dlg, *args):
			dlg.destroy()
		dlg = gtk.MessageDialog(parent=self.window,
				flags=gtk.DialogFlags.MODAL,
				type=gtk.MessageType.ERROR,
				buttons=gtk.ButtonsType.OK,
				message_format=f"Compilation failed.\nExit code: {exit_code}\nOutput:\n{text}")
		dlg.connect("response", destroy)
		dlg.show()
		return		

	def run_in_terminal(self, *args):
		ed = self.notebook.get_children()[self.notebook.get_current_page()].parent_editor
		binFileHandle, binFileName = tempfile.mkstemp()
		compile_command ="/usr/bin/ticcomp " + ed._filepath + " -o " + binFileName
		run_command =  binFileName
		command = f"{compile_command} && {run_command}"
		os.system("x-terminal-emulator -e 'bash -c \""+command+"; echo; echo script finished. press enter to close the terminal...; read\"'")
		os.remove(binFileName)

	def show_terminal(self, show):
		if show:
			print('showing terminal')
			try:
				self.box.remove(self.notebook)
				self.box.pack_end(self.output_view, False, True, 0)
				# self.output_view.show()
				self.output_view.show_now()
				self.box.pack_end(self.notebook, True, True, 0)
			except:
				print('cannot show terminal')
		else:
			print('hiding terminal')
			try:
				self.box.remove(self.output_view)
			except:
				print('cannot hide terminal')
	def hide_terminal(self, *args):
		self.show_terminal(False)

	def undo_current_editor(self, *args):
		self.get_current_editor().buffer.undo()
	def redo_current_editor(self, *args):
		self.get_current_editor().buffer.redo()

class BuildEditor:
	def __init__(self):
		print('Building Editor')
		self.view = gtksource.View()
		setattr(self.view, 'parent_editor', self)
		self.view.modify_font(pango.FontDescription("monospace 11"))
		self.view.set_show_line_numbers(True)
		self.view.set_show_line_marks(True)
		self.buffer = self.view.get_buffer()
		# set language, syntax highlighting
		self.lm = gtksource.LanguageManager.new()
		self.buffer.set_highlight_syntax(True)
		self.buffer.create_tag("invisible", invisible=True)
		self.manager = gtksource.StyleSchemeManager().get_default()
		self.scheme = self.manager.get_scheme("monokai")
		self.buffer.set_style_scheme(self.scheme)
		self.view.set_vexpand(False)
		self.scrollwindow = gtk.ScrolledWindow()
		self.scrollwindow.add(self.view)

if __name__ == "__main__":
	# noinspection PyDeprecation
	import imp, os
	
	modpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'attemptide')
	attemptide = imp.load_source('attemptide', modpath)
	os.system('cls' if os.name in ('nt', 'dos') else 'clear')
	attemptide.MainWindow()

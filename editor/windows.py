# ----- imports -----
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk

gi.require_version('GtkSource', '3.0')
from gi.repository import GtkSource as gtksource
from gi.repository import Pango as pango
# -------------------


def update_label_for_child(notebook, child, text):
	# update specific label
	notebook.set_tab_label_text(notebook, child, text)


class BuildMainWindow:
	def __init__(self):
		print('Building MainWindow')
		self.window = gtk.Window()
		self.window.connect("destroy", gtk.main_quit)
		self.box = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=3)
		self.window.add(self.box)
		self.notebook = gtk.Notebook()
		setattr(self.notebook, "update_label_for_child", update_label_for_child)
		# self.box.add(self.notebook)
		self.box.pack_end(self.notebook, True, True, 0)


class BuildEditor:
	def __init__(self):
		print('Building Editor')
		self.view = gtksource.View()
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


if __name__ == "__main__":
	# noinspection PyDeprecation
	import imp, os
	
	modpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'attemptide')
	attemptide = imp.load_source('attemptide', modpath)
	os.system('cls' if os.name in ('nt', 'dos') else 'clear')
	attemptide.MainWindow()

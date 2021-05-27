# ----- imports -----
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk

gi.require_version('GtkSource', '3.0')
from gi.repository import GtkSource as gtksource
from gi.repository import Pango as pango


# -------------------


class BuildEditor:

	def __init__(self):
		self.view = gtksource.View()
		self.view.modify_font(pango.FontDescription("monospace 11"))
		self.view.set_show_line_numbers(True)
		self.view.set_show_line_marks(True)
		self.buffer = self.view.get_buffer()
		# set language, syntax highlighting
		self.lm = gtksource.LanguageManager.new()
		lang = self.lm.guess_language('test.py')
		self.buffer.set_highlight_syntax(True)
		self.buffer.set_language(lang)
		self.buffer.create_tag("invisible", invisible=True)
		self.manager = gtksource.StyleSchemeManager().get_default()
		self.scheme = self.manager.get_scheme("monokai")
		self.buffer.set_style_scheme(self.scheme)
		self.window = gtk.Window()
		self.window.connect("destroy", gtk.main_quit)
		self.window.add(self.view)
		self.window.show_all()


if __name__ == "__main__":
	import imp, os

	modpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'attemptide')
	attemptide = imp.load_source('attemptide', modpath)
	os.system('cls' if os.name in ('nt', 'dos') else 'clear')
	attemptide.Editor()



import sys
import os
import os.path as osp
import gtk
import gtk.glade
import gobject

_main_module = sys.modules[__name__]
_main_dir = osp.dirname( _main_module.__file__)
_toplevel = osp.abspath(osp.join(_main_dir,"..",".."))

try:
    import projman
    import projman.projmanedit
except ImportError:
    if "projman" in sys.modules:
        del sys.modules["projman"]
    sys.path.insert(0,_toplevel) # for projman
    print "using path=", sys.path[0]
    import projman
    import projman.projmanedit

from projman.readers import ProjectXMLReader
from projman.writers.projman_writer import write_tasks_as_xml
from projman.projmanedit.gui.taskedit import TaskEditor

GLADE=projman.projmanedit.GLADE

XMLFILTER = gtk.FileFilter()
XMLFILTER.set_name("XML file")
XMLFILTER.add_pattern("*.xml")
ANYFILTER = gtk.FileFilter()
ANYFILTER.set_name("Any file")
ANYFILTER.add_pattern("*")

import gtksourceview2


def glade_custom_handler(glade, function_name, widget_name,
			str1, str2, int1, int2):
    if function_name == "create_sourceview":
        widget = gtksourceview2.View()
    else:
        debug("Unknown custom widget : %s/%s", function_name, widget_name )
        widget = None
    if widget:
        widget.show()
    return widget

gtk.glade.set_custom_handler( glade_custom_handler )

class MainApp(gobject.GObject):
    """The main application
    """
    __gsignals__ = {'project-changed': (gobject.SIGNAL_RUN_FIRST,
                                        gobject.TYPE_NONE,
                                        () ),
                    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.project_file = None
        self.project = None
        self.files = None
        self.ui = gtk.glade.XML(GLADE,"window_main")
        self.ui.signal_autoconnect(self)
        # build specific ui controlers
        self.taskeditor = TaskEditor( self )

    def on_new_cmd_activate(self,*args):
        print "new", args

    def on_open_cmd_activate(self,*args):
        print "open", args
        dlg = gtk.FileChooserDialog(title=u"Open project",
                                    action=gtk.FILE_CHOOSER_ACTION_OPEN,)
        dlg.add_button( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL )
        dlg.add_button( gtk.STOCK_OK, gtk.RESPONSE_OK )
        dlg.add_filter( XMLFILTER )
        dlg.add_filter( ANYFILTER )
        res = dlg.run()
        fname = dlg.get_filename()
        dlg.destroy()
        if res!=gtk.RESPONSE_OK:
            return
        self.load_project( fname )

    def load_project(self, fname):
        self.project_file = fname
        reader = ProjectXMLReader( fname, None )
        self.project, self.files = reader.read()
        self.emit("project-changed")
        
    def on_save_cmd_activate(self,*args):
        print "save", args
        basedir = osp.dirname( self.project_file )
        task_file = osp.join( basedir, self.files['tasks'] )
        write_tasks_as_xml( task_file, self.project )

    def on_save_as_cmd_activate(self,*args):
        print "save as", args

    def on_quit_cmd_activate(self, *args):
        gtk.main_quit()

    def on_window_main_destroy(self, *args):
        gtk.main_quit()


app = MainApp()

if len(sys.argv)>1:
    app.load_project( sys.argv[1] )

gtk.main()



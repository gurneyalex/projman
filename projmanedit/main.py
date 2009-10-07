

import sys
import os
import os.path as osp
import gtk
import gtk.glade
import gobject
import gtksourceview2

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
from projman.renderers import GanttRenderer, HandlerFactory
from projman.writers.projman_writer import write_tasks_as_xml
from projman.lib._exceptions import MalformedProjectFile
from projman.scheduling.csp import CSPScheduler

from projman.projmanedit.gui.taskedit import TaskEditor
from projman.projmanedit.gui.editors import (ProjectEditor, ResourceEditor,
                                             ActivitiesEditor, SchedulingUI)

GLADE=projman.projmanedit.GLADE

XMLFILTER = gtk.FileFilter()
XMLFILTER.set_name("XML file")
XMLFILTER.add_pattern("*.xml")
ANYFILTER = gtk.FileFilter()
ANYFILTER.set_name("Any file")
ANYFILTER.add_pattern("*")


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
        self.resourceeditor = ResourceEditor( self )
        self.projecteditor = ProjectEditor( self )
        self.activitieseditor = ActivitiesEditor( self )
        self.scheduling_ui = SchedulingUI( self )

    def get_project_path(self):
        return osp.dirname(osp.abspath(self.project_file))

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
        if res != gtk.RESPONSE_OK:
            return
        self.load_project( fname )

    def load_project(self, fname):
        print "load project", fname
        reader = ProjectXMLReader( fname, None, True )
        try:
            self.project, self.files = reader.read()
        except MalformedProjectFile, exc:
            self.pop_up_bad_project(fname, exc)
            return
        self.project_file = fname
        self.emit("project-changed")

    def pop_up_bad_project(self, fname, exc):
        msg = "Could not open malformed project '%s' : %s" % (fname, exc)
        dlg = gtk.MessageDialog(parent=None, flags=0,
                                type=gtk.MESSAGE_WARNING,
                                buttons=gtk.BUTTONS_OK,
                                message_format= msg)
        dlg.run()
        dlg.destroy()

    def on_notebook1_switch_page(self, notebook, page, page_index):
        if notebook.get_tab_label(notebook.get_nth_page(page_index)).get_text() == "Tasks":
            self.taskeditor.update_on_switch_page()

    def on_save_cmd_activate(self,*args):
        print "save", args
        basedir = osp.dirname( self.project_file )
        task_file = osp.join( basedir, self.files['tasks'] )
        # XXX should write all files, not only task file
        write_tasks_as_xml( task_file, self.project )
        self.load_project(self.project_file)

    def on_save_as_cmd_activate(self,*args):
        print "save as", args
        dlg = gtk.FileChooserDialog('Save as...',
                                    None,
                                    gtk.FILE_CHOOSER_ACTION_SAVE,
                                    (gtk.STOCK_CANCEL,
                                     gtk.RESPONSE_CANCEL,
                                     gtk.STOCK_SAVE,
                                     gtk.RESPONSE_OK))
        dlg.add_filter( XMLFILTER )
        dlg.add_filter( ANYFILTER )
        res = dlg.run()
        fname = dlg.get_filename()
        dlg.destroy()
        if res!=gtk.RESPONSE_OK:
            return
        write_tasks_as_xml( fname, self.project )
        self.load_project(self.project_file)

    def on_quit_cmd_activate(self, *args):
        gtk.main_quit()

    def on_window_main_destroy(self, *args):
        gtk.main_quit()

USAGE = "USAGE : projman-gui <path/to/project.xml>"

def run():
    app = MainApp()
    if len(sys.argv)>1:
        if '-h' in sys.argv or '--help' in sys.argv:
            print USAGE
            return
        app.load_project( sys.argv[1] )
    gtk.main()

if __name__ == '__main__':
    run()




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
from projman.renderers import GanttRenderer, HandlerFactory
from projman.writers.projman_writer import write_tasks_as_xml, write_schedule_as_xml
from projman.projmanedit.gui.taskedit import TaskEditor
from projman.lib._exceptions import MalformedProjectFile
from projman.scheduling.csp import CSPScheduler


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
        except MalformedProjectFile, infos:
            exc, msg = infos
            print "%s: Could not load project %s : %s" % (exc, fname, msg)
            return # do something ...
        self.project_file = fname
        scheduler = CSPScheduler(self.project)
        scheduler.schedule()
        self.project = scheduler.project
        schedule_file = osp.join(self.get_project_path(), self.files["schedule"])
        write_schedule_as_xml(schedule_file, self.project)

        handler = HandlerFactory("svg")
        # it works !! but HOW  ??? ......
        options = handler
        options.timestep = 1
        options.detail = 2
        options.depth = 0
        options.view_begin = None
        options.view_end = None
        options.showids = False
        options.rappel = False
        options.output = None
        options.selected_resource = None
        options.format = "svg" # ce n est plus le format par defaut ...
        options.del_ended = False
        options.del_empty = False
        # end of mystic code ...
        renderer = GanttRenderer(options, handler)
        output = osp.join(self.get_project_path(),  "gantt.svg")
        stream = handler.get_output(output)
        try:
            renderer.render(self.project, stream)
        except AttributeError, exc:
            print "ERROR [could not render Gantt; skipping]:", exc
        self.taskeditor.w("gantt_image").set_from_file(output)
        self.emit("project-changed")

    def on_save_cmd_activate(self,*args):
        print "save", args
        basedir = osp.dirname( self.project_file )
        task_file = osp.join( basedir, self.files['tasks'] )
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


app = MainApp()

if len(sys.argv)>1:
    app.load_project( sys.argv[1] )

gtk.main()

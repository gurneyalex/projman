

import gtk
import gobject
from projman.lib.constants import LOAD_TYPE_MAP
from projman.lib.task import Task
from projman.readers.base_reader import MODEL_FACTORY
import gtksourceview2

LANGUAGES = gtksourceview2.language_manager_get_default().get_language_ids()
LANGUAGES.sort()
assert "docbook" in LANGUAGES
XMLLANG = gtksourceview2.language_manager_get_default().get_language("docbook")
print LANGUAGES

class TaskEditor(gobject.GObject):

    __gsignals__ = {'task-changed': (gobject.SIGNAL_RUN_FIRST,
                                     gobject.TYPE_NONE,
                                     (gobject.TYPE_PYOBJECT,) ),
                    }

    def __init__(self, app):
        gobject.GObject.__init__(self)
        self.app = app
        self.w = app.ui.get_widget
        self.current_task = None
        self.current_task_path = None
        self.task_popup = None
        self.setup_ui()
        app.ui.signal_autoconnect(self)
        app.connect("project-changed", self.on_project_changed )
        self.w("spinbutton_duration").get_adjustment().set_all(0,0,100000,1,1,1)
        
    def setup_ui(self):
        self.setup_task_tree()
        self.setup_constraints_tree()
        self.setup_resources_tree()

    def build_task_tree_popup(self, task_path, del_task=True):
        task_popup = gtk.Menu()
        add_item = gtk.MenuItem("Add task")
        add_item.connect("activate", self.popup_add_task, task_path )
        task_popup.attach(add_item, 0, 1, 0, 1 )
        add_item = gtk.MenuItem("Add milestone")
        add_item.connect("activate", self.popup_add_milestone, task_path )
        task_popup.attach(add_item, 0, 1, 1, 2 )
        if del_task and task_path is not None:
            del_item = gtk.MenuItem("Delete task")
            del_item.connect("activate", self.popup_del_task, task_path )
            task_popup.attach(del_item, 0, 1, 2, 3 )
        task_popup.show_all()
        return task_popup
        

    def setup_resources_tree(self):
        tree = self.w("treeview_task_resources")
        self.resources_model = gtk.ListStore(gobject.TYPE_STRING, # type
                                             gobject.TYPE_STRING, # id
                                             gobject.TYPE_INT,    # usage
                                             gobject.TYPE_STRING, # color
                                             )
        col = gtk.TreeViewColumn( u"Type", gtk.CellRendererText(), text=0, foreground=3 )
        tree.append_column( col )
        col = gtk.TreeViewColumn( u"ID", gtk.CellRendererText(), text=1, foreground=3 )
        tree.append_column( col )
        col = gtk.TreeViewColumn( u"Usage", gtk.CellRendererText(), text=2, foreground=3 )
        tree.append_column( col )
        tree.set_model( self.resources_model )

    def setup_constraints_tree(self):
        tree = self.w("treeview_task_constraints")
        self.constraints_model = gtk.ListStore(gobject.TYPE_STRING, # type
                                               gobject.TYPE_STRING, # date or res_id
                                               gobject.TYPE_STRING, # color (inherited or not)
                                               )
        col = gtk.TreeViewColumn( u"Type", gtk.CellRendererText(), text=0, foreground=2 )
        tree.append_column( col )
        col = gtk.TreeViewColumn( u"Arg", gtk.CellRendererText(), text=1, foreground=2 )
        tree.append_column( col )
        tree.set_model( self.constraints_model )

    def setup_task_tree(self):
        self.task_model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        tree = self.w('treeview_all_tasks')
        col = gtk.TreeViewColumn( u"Task", gtk.CellRendererText(), text=1 )
        tree.append_column(col)
        col = gtk.TreeViewColumn( u"Title", gtk.CellRendererText(), text=0 )
        tree.append_column(col)
        tree.set_model( self.task_model )
        sel = tree.get_selection()
        sel.connect("changed", self.on_task_selection_changed )

    def refresh_task_list(self, sel_task_id=None, sel_task=None):
        model = self.task_model
        model.clear()
        tasks = [ (self.app.project.root_task,None) ]
        while tasks:
            task,parent = tasks.pop()
            row = task.title, task.id
            itr = model.append( parent, row )
            for t in task.children:
                tasks.append( (t, itr) )
        tree = self.w('treeview_all_tasks')
        tree.expand_all()
        if sel_task:
            sel_task_id = sel_task.id
        if sel_task_id:
            # select the task
            itr = self.get_task_iter_from_id( sel_task_id )
            tree.get_selection().select_iter( itr )
            
    def get_task_from_path(self, path):
        root_task = self.app.project.root_task
        itr = self.task_model.get_iter( path )
        if itr:
            task_id = self.task_model.get_value( itr, 1 )
            return root_task.get_task( task_id )
        else:
            return None
        
    def get_task_iter_from_id(self, task_id):
        itr = self.task_model.get_iter_first()
        while itr:
            tid = self.task_model.get_value( itr, 1 )
            if task_id == tid:
                return itr
            itr = self.task_model.iter_next( itr )
            
    def on_project_changed(self, app):
        """Propagates the fact that the project file
        has changed"""
        print app.project
        print app.files
        self.refresh_task_list()

    def on_task_selection_changed(self, sel):
        model, itr = sel.get_selected()
        task_id = model.get_value(itr, 1)
        self.current_task = self.app.project.root_task.get_task(task_id)
        self.current_task_path = model.get_path( itr )
        self.update_task_info()

    def update_task_info(self):
        task = self.current_task
        # update widgets value
        self.w("entry_task_id").set_text( task.id )
        self.w("entry_task_title").set_text( task.title )
        #buf = .get_buffer()
        buf = gtksourceview2.Buffer()
        self.w("textview_task_description").set_buffer( buf )
        if task.description_format == "rest":
            buf.set_language(None)
        else:
            buf.set_language( XMLLANG )
        buf.set_text( task.description_raw )
        self.w("spinbutton_duration").get_adjustment().set_value( task.duration )
        self.w("combobox_scheduling_type").set_active( task.load_type )

        self.constraints_model.clear()
        child = task
        color = "black"
        while child:
            for constraint_type, arg in child.task_constraints:
                self.constraints_model.append( (constraint_type, arg, color ) )
            child = child.parent
            color = "gray"

        if isinstance(task, Task):
            child = task
        else:
            # Milestones don't have resources
            child = None 
        color = "black"
        while child and not child.resource_constraints:
            child = child.parent
            color = "gray"
        
        self.resources_model.clear()
        if child:
            for res_type, res_id, res_usage in child.resource_constraints:
                self.resources_model.append( (res_type, res_id, res_usage, color) )

    def on_entry_task_title_changed(self, entry):
        itr = self.task_model.get_iter( self.current_task_path )
        title = entry.get_text()
        self.current_task.title = title
        self.task_model.set_value( itr, 0, title )
        
    def on_spinbutton_duration_changed(self, spin):
        dur = self.w("spinbutton_duration").get_adjustment().get_value()
        self.current_task.duration = dur


    def on_treeview_all_tasks_button_press_event(self, treeview, event):
        if event.button != 3:
            return None
        x = int(event.x)
        y = int(event.y)
        time = event.time
        pthinfo = treeview.get_path_at_pos(x, y)
        if pthinfo is not None:
            #print pthinfo
            path, col, cellx, celly = pthinfo
            treeview.grab_focus()
            treeview.set_cursor( path, col, 0)
        else:
            path = None
        if self.task_popup:
            self.task_popup.destroy()
        self.task_popup = self.build_task_tree_popup(path)
        self.task_popup.popup( None, None, None, event.button, time)
        return 1

    def popup_add_task(self, item, path):
        root_task = self.app.project.root_task
        parent_task = self.get_task_from_path( path )
        if not parent_task:
            parent_task = root_task
        if not isinstance(parent_task, Task):
            print "XXX: CAN'T ADD TASK TO MILESTONE"
            return
        ids = set([ task.id for task in root_task.flatten() ])
        i = 1
        while 1:
            new_id = parent_task.id+"_%s"%i
            if new_id not in ids:
                break
            i = i + 1
        new_task = MODEL_FACTORY.create_task( new_id )
        parent_task.append( new_task )
        self.refresh_task_list(task_id=new_id)

    def popup_add_milestone(self, item, path):
        pass
        
    def popup_del_task(self, item, path):
        task = self.get_task_from_path( path )
        parent = task.parent
        if not parent:
            print "XXX: CAN'T DELETE ROOT"
            return
        if task.children:
            print "XXX: TASK HAS CHILDREN"
            return
        parent.remove( task )
        self.refresh_task_list(task=parent)
        

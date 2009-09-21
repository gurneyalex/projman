# -*- coding:utf-8 -*-
import os
import gtk
import gtksourceview2
import gobject
from projman.lib.constants import LOAD_TYPE_MAP, TASK_CONSTRAINTS
from projman.lib.task import Task
from projman.readers.base_reader import MODEL_FACTORY
from projman.projmanedit.gui.editors import BaseEditor

LANGUAGES = gtksourceview2.language_manager_get_default().get_language_ids()
LANGUAGES.sort()
assert "docbook" in LANGUAGES
XMLLANG = gtksourceview2.language_manager_get_default().get_language("docbook")
print LANGUAGES

ADD_TASK_MSG = ("Warning : Adding a Task as a child of Task(%s) will reset"
" the load value of it. \n Are you sure ?")
ADD_MILESTONE = ("Warning : Adding a Milestone as a child of Task(%s) will "
" reset the load value of it. \n Are you sure ?")

class TaskEditor(BaseEditor):

    __gsignals__ = {'task-changed': (gobject.SIGNAL_RUN_FIRST,
                                     gobject.TYPE_NONE,
                                     (gobject.TYPE_PYOBJECT,) ),
                    }

    def __init__(self, app):
        BaseEditor.__init__(self, app)
        self.current_task = None
        self.current_task_path = None
        self.task_popup = None
        self.setup_ui()
        app.ui.signal_autoconnect(self)
        self.w("spinbutton_duration").get_adjustment().set_all(0,0,100000,0.1,1,1)

    def setup_ui(self):
        self.constraints_type_model = gtk.ListStore(gobject.TYPE_STRING)
        for v in TASK_CONSTRAINTS:
            self.constraints_type_model.append( (v,) )
        self.setup_task_tree()
        self.setup_constraints_tree()
        self.setup_resources_tree()

    def build_task_tree_popup(self, task_path, del_task=True):
        task_popup = gtk.Menu()
        task = self.get_task_from_path(task_path)

        if not self.app.project is None:
            if self.app.project.root_task and task_path and task.TYPE != "milestone":
                add_item = gtk.MenuItem("Add task")
                add_item.connect("activate", self.popup_add_task, task_path )
                task_popup.attach(add_item, 0, 1, 0, 1 )
                add_item = gtk.MenuItem("Add milestone")
                add_item.connect("activate", self.popup_add_milestone, task_path )
                task_popup.attach(add_item, 0, 1, 1, 2 )

        if del_task and task_path is not None:
            if task.TYPE != "milestone":
                del_item = gtk.MenuItem("Delete task")
            else:
                del_item = gtk.MenuItem("Delete milestone")
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
                                             gobject.TYPE_BOOLEAN, # editable
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
                                               gobject.TYPE_BOOLEAN, # editable
                                               )
        rend = gtk.CellRendererCombo()
        rend.set_property('model', self.constraints_type_model )
        rend.set_property('has-entry', False)
        rend.set_property('text-column', 0)
        rend.connect('edited', self.on_constraint_type_edited )
        col = gtk.TreeViewColumn( u"Type", rend, text=0, foreground=2, editable=3 )
        tree.append_column( col )
        rend = gtk.CellRendererCombo()
        rend.set_property('model', self.task_model)
        rend.set_property('text-column', 1)
        rend.connect('edited', self.on_constraint_arg_edited )
        col = gtk.TreeViewColumn( u"Arg", rend, text=1, foreground=2, editable=3 )
        tree.append_column( col )
        tree.set_model( self.constraints_model )
        tree.enable_model_drag_dest( [ ("task", gtk.TARGET_SAME_APP, 0) ],
                                     gtk.gdk.ACTION_COPY )

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

        # enable drag & drop
        tree.enable_model_drag_dest( [ ("task", gtk.TARGET_SAME_APP, 0) ],
                                     gtk.gdk.ACTION_COPY|gtk.gdk.ACTION_MOVE )
        tree.enable_model_drag_source( gtk.gdk.BUTTON1_MASK,
                                       [ ("task", gtk.TARGET_SAME_APP, 0) ],
                                       gtk.gdk.ACTION_COPY|gtk.gdk.ACTION_MOVE )
        tree.connect("drag-data-received", self.drag_task_received )
        tree.connect("drag-data-get", self.drag_task_get )
        tree.connect("drag-data-delete", self.drag_task_deleted )

    def drag_task_received(self, treeview, context, x, y, selection, info, timestamp):
        print "DRAG RECEIVED:", x, y, info
        print "CTX:", context.action
        root_task = self.app.project.root_task
        task_src_id = selection.data
        task_src = root_task.get_task(task_src_id)
        if not task_src:
            return
        if context.action == gtk.gdk.ACTION_COPY:
            task_new = task_src.copy() # XXX
        elif context.action == gtk.gdk.ACTION_MOVE:
            task_new = task_src

        row = [ task_new.title, task_new.id ]
        drop_info = treeview.get_dest_row_at_pos(x, y)
        parent_id = None  # the parent task id
        sibling_id = None # the closest sibling id or None (append)
        sibling_pos = None # 1: before, 2: after
        if drop_info:
            # drop happened on an item
            model = treeview.get_model()
            path, position = drop_info
            iter = model.get_iter(path)
            sibling_id = model.get_value( iter, 1 )
            parent_itr = model.iter_parent( iter )
            parent_id = model.get_value( parent_itr, 1 )
            parent_dest = root_task.get_task( parent_id )
            if position == gtk.TREE_VIEW_DROP_BEFORE:
                # insert it before the given item
                sibling_pos = 1
                model.insert_before(parent_itr, iter, row )
            elif position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
                # append it after the children of the given item
                if task_src_id == sibling_id:
                    # a task dropped on itself
                    return
                parent_id = sibling_id
                sibling_id = None
                model.append( iter, row )
            else:
                # insert it after the given item
                sibling_pos = 2
                model.insert_after(parent_itr, iter, row)
        else:
            # append it after the children of the root item
            position = None
            parent_dest = root_task
            parent_itr = model.get_iter_first()
            parent_id = model.get_value( parent_itr, 1 )
            sibling_id = None
            model.append( parent_itr, row )

        if context.action == gtk.gdk.ACTION_MOVE:
            task_src.parent.remove( task_src )

        print "DROP", parent_id, task_new.id, position
        if sibling_id is None:
            parent_dest.append( task_new )
        else:
            idx = 0
            for i,c in enumerate(parent_dest.children):
                if c.id == sibling_id:
                    break
            if sibling_pos==2:
                i+=1
            parent_dest.insert(i,task_new)
        context.finish(True, True, timestamp)

    def drag_task_deleted(self, treeview, context):
        print "DRAG DELETED:", context

    def drag_task_get(self, treeview, context, selection, target_id, etime):
        print "DATA GET", target_id
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        tid = model.get_value(iter, 1)
        selection.set(selection.target, 8, tid)

    def refresh_task_list(self, sel_task_id=None, sel_task=None):
        model = self.task_model
        model.clear()
        tasks = [ (self.app.project.root_task, None) ]
        while tasks:
            task, parent = tasks.pop(0)
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

    def _get_sublevel_tasks(self, task_id, itr):
        retour = None
        if not itr:
            return
        tid = self.task_model.get_value( itr, 1 )
        if task_id == tid:
            return itr
        else:
            if self.task_model.iter_has_child(itr):
                retour = self._get_sublevel_tasks(task_id,
                                                  self.task_model.iter_children(itr))
                if retour != None:
                    return retour
            retour = self._get_sublevel_tasks(task_id,
                                              self.task_model.iter_next(itr))
            if retour != None:
                return retour

    def get_task_iter_from_id(self, task_id):
        itr = self.task_model.get_iter_first()
        itr_ = self._get_sublevel_tasks(task_id, itr)
        if itr_ != None:
            return itr_
        else:
            return itr

    def on_project_changed(self, app):
        """Propagates the fact that the project file
        has changed"""
        print "X X X project_changed :" ,
        print app.project, app.files
        self.refresh_task_list()

    def on_task_selection_changed(self, sel):
        model, itr = sel.get_selected()
        if not itr:
            return
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
        buf.connect("changed", self.on_textview_task_description_changed )
        self.w("textview_task_description").set_buffer( buf )
        if task.description_format == "rest":
            buf.set_language(None)
            self.w("combobox_description_format").set_active(1)
        elif task.description_format == "docbook":
            buf.set_language( XMLLANG )
            self.w("combobox_description_format").set_active(0)
        else:
            self.w("combobox_description_format").set_active(2)

        #securité acces load si taches filles
        has_child = task.children
        if has_child:
            task.duration = 0.0
        self.w("spinbutton_duration").set_sensitive(not has_child)
        self.w("combobox_scheduling_type").set_sensitive(not has_child)

        if task.TYPE == "milestone":
            self.w("combobox_scheduling_type").set_sensitive(False)
            self.w("spinbutton_duration").set_sensitive(False)

        buf.set_text( task.description_raw )
        self.w("spinbutton_duration").get_adjustment().set_value( task.duration )
        self.w("combobox_scheduling_type").set_active( task.load_type )

        self.constraints_model.clear()
        child = task
        color = "black"
        while child:
            for constraint_type, arg in child.task_constraints:
                self.constraints_model.append( (constraint_type, arg, color,
                                                color=='black' ) )
            child = child.parent
            color = "gray"
        if isinstance(task, Task):
            # Milestones don't have resources
            self._update_resources_view(task)

    def _update_resources_view(self, task):
        color = "black"
        while task and not task.resource_constraints:
            task = task.parent
            color = "gray"

        self.resources_model.clear()
        if task:
            for constraint in task.resource_constraints:
                print repr(constraint)
                res_type, res_id = constraint
                res_usage = None # FIXME
                self.resources_model.append( (res_type, res_id, res_usage,
                                              color, color=='black') )


    def on_entry_task_title_changed(self, entry):
        itr = self.task_model.get_iter( self.current_task_path )
        title = entry.get_text()
        self.current_task.title = title
        self.task_model.set_value( itr, 0, title )

    def on_entry_task_id_changed(self, entry):
        itr = self.task_model.get_iter( self.current_task_path )
        task_id = entry.get_text()
        self.current_task.id = task_id
        self.task_model.set_value( itr, 1, task_id )

    def on_spinbutton_duration_changed(self, spin):
        dur = self.w("spinbutton_duration").get_adjustment().get_value()
        self.current_task.duration = dur

    def on_combobox_scheduling_type_changed(self, combo):
        model = combo.get_model()
        iter = combo.get_active_iter()
        load_type = model.get_value(iter, 0)
        self.current_task.load_type = LOAD_TYPE_MAP[load_type]
        self.update_task_info()

    def on_combobox_description_format_changed(self, combo):
        model = combo.get_model()
        iter = combo.get_active_iter()
        description_format = model.get_value(iter, 0)
        self.current_task.description_format = description_format.lower()

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
        if path is None:
            return
        root_task = self.app.project.root_task
        parent_task = self.get_task_from_path( path )

        if not parent_task.children:
            dlg = gtk.MessageDialog(parent=None, flags=0,
                                    type=gtk.MESSAGE_QUESTION,
                                    buttons=gtk.BUTTONS_YES_NO,
                                    message_format= ADD_TASK_MSG % parent_task.id)
            ret = dlg.run()
            dlg.destroy()
            if ret == gtk.RESPONSE_NO:
                return

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
        new_task.title = "#TODO"
        new_task.description_raw = "#TODO"
        parent_task.append( new_task )
        self.refresh_task_list(sel_task_id=new_id)

    def popup_add_milestone(self, item, path):
        if path is None:
            return
        root_task = self.app.project.root_task
        parent_task = self.get_task_from_path( path )

        if not parent_task.children:
            dlg = gtk.MessageDialog(parent=None, flags=0,
                                    type=gtk.MESSAGE_QUESTION,
                                    buttons=gtk.BUTTONS_YES_NO,
                                    message_format= ADD_MILESTONE % parent_task.id)
            ret = dlg.run()
            dlg.destroy()
            if ret == gtk.RESPONSE_NO:
                return

        if not parent_task:
            parent_task = root_task
        if not isinstance(parent_task, Task):
            print "XXX: CAN'T MILESTONE TASK TO MILESTONE"
            return
        ids = set([ task.id for task in root_task.flatten() ])
        i = 1
        while 1:
            new_id = "milestone_"+parent_task.id+"_%s"%i
            if new_id not in ids:
                break
            i = i + 1
        new_task = MODEL_FACTORY.create_milestone( new_id )
        new_task.TYPE="milestone"
        new_task.load_type=LOAD_TYPE_MAP["milestone"]
        new_task.title = "#TODO"
        parent_task.append( new_task )
        self.refresh_task_list(sel_task_id=new_id)

    def popup_del_task(self, item, path):
        task = self.get_task_from_path( path )
        parent = task.parent
        if not parent:
            dlg = gtk.MessageDialog(parent=None, flags=0,
                                    type=gtk.MESSAGE_WARNING,
                                    buttons=gtk.BUTTONS_OK,
                                    message_format= "Error : Root task can't be deleted.")
            dlg.run()
            dlg.destroy()
            return
        if task.children:
            dlg = gtk.MessageDialog(parent=None, flags=0,
                                    type=gtk.MESSAGE_WARNING,
                                    buttons=gtk.BUTTONS_OK,
                                    message_format= "Error : Can't delete task(%s), task has children." % task.id)
            dlg.run()
            dlg.destroy()
            return
        parent.remove( task )
        self.refresh_task_list(sel_task=parent)

    def on_textview_task_description_changed(self, buf):
        _beg = buf.get_start_iter()
        _end = buf.get_end_iter()
        txt = buf.get_text( _beg, _end )
        self.current_task.description_raw = txt

    def on_constraint_type_edited(self, renderer, path, new_text):
        itr = self.constraints_model.get_iter( path )
        constr, value = self.constraints_model.get( itr, 0, 1 )
        assert constr in TASK_CONSTRAINTS
        self.current_task.task_constraints.remove( (constr, value) )
        self.current_task.add_task_constraint( new_text, value )
        self.constraints_model.set_value( itr, 0, new_text )

    def on_constraint_arg_edited(self, renderer, path, new_text):
        itr = self.constraints_model.get_iter( path )
        constr, value = self.constraints_model.get( itr, 0, 1 )
        self.current_task.task_constraints.remove( (constr, value) )
        self.current_task.add_task_constraint( constr, new_text )
        self.constraints_model.set_value( itr, 1, new_text )

    def on_button_project_resources_show_button_press_event(self, button, evt):
        print "go to resource page ?"
        self.w("notebook1").set_current_page(1)

    def on_button_project_activities_show_button_press_event(self, button, evt):
        self.w("notebook1").set_current_page(2)

    def on_button_project_tasks_show_button_press_event(self, button, evt):
        self.w("notebook1").set_current_page(3)

    def on_button_project_schedule_show_button_press_event(self, button, evt):
        self.w("notebook1").set_current_page(4)

    def on_notebook1_switch_page(self, notebook, page, page_index):
        print "notebook switch to page %s" % page
        if notebook.get_tab_label(notebook.get_nth_page(page_index)).get_text() == "Tasks":
            if self.current_task is None:
                print dir(self.app.project)
                self.current_task = self.app.project.root_task
            self.refresh_task_list(sel_task=self.current_task)
            self.update_task_info()

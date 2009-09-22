# -*- coding:utf-8 -*-
import gtk
import gobject
from projman.lib.calendar import Calendar
from projman.lib.resource import Resource
from projman.lib.resource_role import ResourceRole
from projman.lib.task import Task


class BaseEditor(gobject.GObject):
    """class for some functionalities for all editors"""

    def __init__(self, app):
        gobject.GObject.__init__(self)
        self.app = app
        self.w = app.ui.get_widget
        app.connect("project-changed", self.on_project_changed )

    def on_project_changed(self, app):
        """interface for project changed"""


class ProjectEditor(BaseEditor):
    """class for the project Box and other general stuff"""

    def __init__(self, app):
        BaseEditor.__init__(self, app)

    def on_project_changed(self, app):
        self.schedule_project()
        self.setup_project_files_path()

    def schedule_project(self):
        """TODO : method to schedule project and render gantt"""

    def setup_project_files_path(self):
        for field in ('tasks', 'activities', 'resources', 'schedule'):
            self.w("entry_project_%s_file" % field).set_text(self.app.files[field])
        self.w("window_main").set_title("Projman - " + str(self.app.project_file))


class ResourceEditor(BaseEditor):

    def __init__(self, app):
        BaseEditor.__init__(self, app)
        self.resources_model = None # defined in setup_resources_list as gtk.ListStore
        self.resources_role_model = None # defined in setup_resource_roles_list
        self.calendar_model = None # defined in setup_calendar_list
        self.offday_model = None # defined in setup_offdays_list
        self.current_cal = None # set dynamically
        self.setup_ui()

    def setup_ui(self):
        self.calendar_ids = gtk.ListStore(gobject.TYPE_STRING)
        self.setup_resources_list()
        self.setup_resource_roles_list()
        self.setup_calendar_list()
        self.setup_offday_list()

    def on_project_changed(self, app):
        self.update_calendar_info()
        self.update_resources_info()
        self.update_resource_roles_info()

    def setup_resources_list(self):
        tree = self.w("treeview_resources")
        self.resources_model = gtk.ListStore(gobject.TYPE_STRING, # cal_id
                                             gobject.TYPE_STRING, # name
                                             gobject.TYPE_STRING, # color
                                             gobject.TYPE_BOOLEAN, # editable
                                             )
        rend = gtk.CellRendererCombo()
        rend.set_property('model', self.calendar_ids )
        rend.set_property('has-entry', False)
        rend.set_property('text-column', 0)
        rend.connect('edited', self.on_calendar_type_edited )
        tree.append_column( gtk.TreeViewColumn( u"Cal_ID", rend, text=0,
                            foreground=2, editable=3 ) )
        tree.append_column( gtk.TreeViewColumn( 'Name', gtk.CellRendererText(),
                           text=1, foreground=2 ) )
        tree.set_model( self.resources_model )

    def setup_resource_roles_list(self):
        tree = self.w("treeview_resource_roles")
        self.resource_roles_model = gtk.ListStore(gobject.TYPE_STRING, # type
                                                  gobject.TYPE_STRING, # id
                                                  gobject.TYPE_STRING, # usage
                                                  gobject.TYPE_STRING, # cost
                                                  gobject.TYPE_STRING, # color
                                                  gobject.TYPE_BOOLEAN, # editable
                                                 )
        for name, text_num in [('ID', 1), ('Usage', 2), ('Cost/h', 3)]:
            tree.append_column( gtk.TreeViewColumn( name, gtk.CellRendererText(),
                         text=text_num, foreground=4 ) )
        tree.set_model( self.resource_roles_model )

    def setup_calendar_list(self):
        tree = self.w("treeview_calendars")
        self.calendar_model = gtk.ListStore(gobject.TYPE_STRING, # cal_id
                                             gobject.TYPE_STRING, # cal_name
                                             gobject.TYPE_STRING, # color
                                             gobject.TYPE_BOOLEAN, # editable
                                             )
        tree.append_column( gtk.TreeViewColumn( 'Cal_ID', gtk.CellRendererText(),
                           text=0, foreground=2 ) )
        tree.append_column( gtk.TreeViewColumn( 'Name', gtk.CellRendererText(),
                           text=1, foreground=2 ) )
        tree.set_model( self.calendar_model )

        tree.get_selection().connect("changed", self.on_calendar_selection_changed )

    def setup_offday_list(self):
        tree = self.w("treeview_offdays")
        self.offday_model = gtk.ListStore(gobject.TYPE_STRING, # month
                                             gobject.TYPE_STRING, # day
                                             gobject.TYPE_BOOLEAN, # editable
                                             )
        for name, col in (('Month', 0), ('Day', 1)):
            tree.append_column( gtk.TreeViewColumn( name, gtk.CellRendererText(),
                           text=col, foreground=2 ) )
        tree.set_model( self.offday_model )

    def update_resources_info(self):
        res_set = self.app.project.resource_set
        resources = [res for res in res_set.children if isinstance(res, Resource)]
        editable = True # TODO
        self.resources_model.clear()
        for res in resources:
            self.resources_model.append( (res.calendar, res.name, "blue", editable) )

    def update_resource_roles_info(self):
        model = self.resource_roles_model
        res_set = self.app.project.resource_role_set
        editable = True # XXX
        model.clear()
        for role in res_set.children:
            if isinstance(role, ResourceRole):
                rate = '%s %s' % (role.hourly_cost, role.unit)
                model.append( (None, role.id, role.name, rate, "blue", editable) )

    def update_calendar_info(self):
        "print update calendar infos"
        resources = self.app.project.resource_set
        cal_ids = self.calendar_ids
        cal_ids.clear()
        #for cal in set(res.calendar for res in resources if isinstance(res, Resource)):
            #cal_ids.append( (cal,) )
        for cal in set(res.id for res in resources if isinstance(res, Calendar)):
            cal_ids.append( (cal,) )
        cal_ids.append( ('<new>',) )
        proj_cals = [res for res in self.app.project.resource_set.children
                if isinstance(res, Calendar)]
        for cal in proj_cals:
            self.calendar_model.append( (cal.id, cal.name, "darkgreen", False ))

    def on_calendar_selection_changed(self, sel):
        model, itr = sel.get_selected()
        print "show new calendar", model, itr
        cal_id = model.get_value(itr, 0)
        cal = self.app.project.get_resource(cal_id)
        print 'cal id:', cal_id, cal
        # update weekdays
        for day, val in cal.weekday.items():
            working = (val=="working")
            self.w('checkbutton_%s' %day).set_active(working)
        # update offdays
        offdays = self.offday_model
        offdays.clear()
        for month, day in cal.national_days:
            offdays.append( (str(month), str(day), False) )
        # XXX use cal.timeperiods (which are DateTime.DateTime objects)
        offdays.append( ('XXX : Movable', 'Days', False) )

    def on_calendar_type_edited(self):
        print "# update calendar type"

    def update_working_days(self, cal):
        print """show working days of the given calendar"""

class ActivitiesEditor(BaseEditor):

    def __init__(self, app):
        BaseEditor.__init__(self, app)
        self.activities_model = None
        self.current_activity_path = None
        self.current_activity_itr = None
        self.setup_activities_tree()


    def on_project_changed(self, app):
        self.refresh_activities_list()

    def setup_activities_tree(self):
        self.activities_model = gtk.TreeStore(gobject.TYPE_STRING)
        tree = self.w('treeview_all_activities')
        col = gtk.TreeViewColumn( u"Activities", gtk.CellRendererText(), text=0 )
        tree.append_column(col)
        tree.set_model( self.activities_model )
        sel = tree.get_selection()
        sel.connect("changed", self.on_activities_selection_changed )

    def on_activities_selection_changed(self, sel):
        model, itr = sel.get_selected()
        if not itr:
            return
        self.current_activity_path = model.get_path( itr )
        self.current_activity_itr = itr
        self.update_activities_info()

    def get_iter_by_task_activity_id(self, id):
        model = self.activities_model
        itr = model.get_iter_first()
        while itr != None:
            if id == model.get_value(itr,0):
                return itr
            else:
                itr = model.iter_next(itr)
        return itr

    def get_res_iter_from_id_sublevels(self, res_id, itr):
        if itr !=  None:
            rid = self.activities_model.get_value( itr, 0 )
            if res_id == rid:
                return itr
            else:
                next_iter = self.activities_model.iter_next(itr)
                return self.get_res_iter_from_id_sublevels(res_id, next_iter)
        else:
            return None

    def get_iter_by_res_activity_id(self, res_id, itr):
        iter_childern = self.activities_model.iter_children(itr)
        itr_ = self.get_res_iter_from_id_sublevels(res_id, iter_children)
        if itr_ != None:
            return itr_
        else:
            return None

    def refresh_activities_list(self, sel_activity_id=None):
        model = self.activities_model
        model.clear()
        ligne=0
        for activity in self.app.project.activities:
            if activity[5]=="past":
                itr = self.get_iter_by_task_activity_id(activity[3])
                if itr is None:
                    itr_ = model.append( itr, [activity[3]])
                    model.append( itr_, [activity[2]])
                else:
                    if self.get_iter_by_res_activity_id(activity[2],itr) != None:
                        model.append( itr, ["%s (%s)" % (activity[2], ligne)] )
                    else:
                        model.append( itr_, [activity[2]])
            ligne = ligne + 1


    def get_activity_by_res_task_id(self, rid, tid):
        for activity in self.app.project.activities:
            if activity[2] == rid and activity[3] == tid:
                return activity
        return None

    def get_activity_by_line_id(self, line_id):
        ligne = 0
        for activity in self.app.project.activities:
            if str(ligne) == str(line_id):
                return activity
            ligne = ligne + 1
        return None

    def update_activities_info(self):
        model = self.activities_model
        type_activity = model.iter_depth(model.get_iter(self.current_activity_path))

        curr_itr = self.current_activity_itr
        if type_activity == 0:
            self.w("entry_activities_id").set_text(model.get_value(curr_itr, 0))
            self.w("entry_activities_from").set_sensitive(False)
            self.w("entry_activities_to").set_sensitive(False)
            self.w("spinbutton_activities_usage").set_sensitive(False)
            self.w("combobox_activities_resource").set_sensitive(False)
            self.w("entry_activities_from").set_text("")
            self.w("entry_activities_to").set_text("")
            self.w("spinbutton_activities_usage").set_value(0)

        if type_activity == 1:
            res_id = model.get_value(curr_itr, 0)
            if res_id.find("(") > 0:
                line = res_id[res_id.find("(")+1:res_id.find(")")]
                res_id = res_id[0:res_id.find("(")]
                activity = self.get_activity_by_line_id(line)
            else:
                iii = self.activities_model.iter_parent(curr_itr)
                val = self.activities_model.get_value( iii, 0)
                activity = self.get_activity_by_res_task_id(res_id, val)
            self.w("entry_activities_id").set_text(res_id)
            self.w("entry_activities_from").set_sensitive(True)
            self.w("entry_activities_to").set_sensitive(True)
            self.w("spinbutton_activities_usage").set_sensitive(True)
            self.w("combobox_activities_resource").set_sensitive(False)
            self.w("entry_activities_from").set_text(str(activity[0].date))
            self.w("entry_activities_to").set_text(str(activity[1].date))
            self.w("spinbutton_activities_usage").set_value(int(activity[4]))


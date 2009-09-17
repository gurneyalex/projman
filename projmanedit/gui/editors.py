# -*- coding:utf-8 -*-

import gobject


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
        self.setup_project_files_path()

    def setup_project_files_path(self):
        for field in ('tasks', 'activities', 'resources', 'schedule'):
            self.w("entry_project_%s_file" % field).set_text(self.app.files[field])
        self.w("window_main").set_title("Projman - " + str(self.app.project_file))



class ResourceEditor(BaseEditor):

    def __init__(self, app):
        BaseEditor.__init__(self, app)

    def on_project_changed(self, app):
        print  "call 'ResourceEditor.on_project_changed'"



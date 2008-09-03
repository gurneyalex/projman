# Copyright (c) 2000-2008 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
""" base classes for rendering """

from projman.renderers.resource import ResourcesRenderer, ResourcesDrawer
from projman.renderers.gantt import GanttRenderer, GanttDrawer
from projman.renderers.abstract import AbstractRenderer, ROW_HEIGHT

class GanttResourcesRenderer(ResourcesRenderer, GanttRenderer):
    
    def __init__(self, options, handler, colors_file=None, colors_stream=None):
        AbstractRenderer.__init__(self, options)
        self.drawer = GanttResourcesDrawer(options, handler, colors_file,
                                           colors_stream)
        self._draw_resources = {}
        
    def render(self, project, stream):
        """
        render the task as a gantt & resources diagram
        """
        AbstractRenderer.render(self, project, stream)
        self.drawer._handler.save_result(stream)
       
    def _render_body(self, project) :
        GanttRenderer._render_body(self, project)
        ResourcesRenderer._render_body(self, project)

    def render_resource(self, resource, project) :
        """
        generate events for a given resource
        """
        self.drawer.set_color_set(self._i)
        self._i += 1
        self.render_total_occupation(project, resource)

class GanttResourcesDrawer(ResourcesDrawer, GanttDrawer):
    def _init_table(self):
        """ initialize fields needed by the table"""
        GanttDrawer._init_table(self) 
        ResourcesDrawer._init_table(self)

    def _get_table_dimension(self, project):
        """ calculate dimension of the table"""
        #retreive attributes from mother classes
        width_gantt, height_gantt = GanttDrawer._get_table_dimension(self, project) 
        width_res, height_res = ResourcesDrawer._get_table_dimension(self, project)
        #calculate height_resource_reduced
        nb_resources = len(project.resource_set.get_resources())
        nb_tasks = len(project.root_task.flatten())
        height_resource_reduced = ROW_HEIGHT*(5+nb_tasks+nb_resources*2)
        width = max(width_gantt, width_res)
        height = height_gantt+height_resource_reduced
        return width, height
                    

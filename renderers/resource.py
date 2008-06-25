# Copyright (c) 2000-2005 LOGILAB S.A. (Paris, FRANCE).
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
"""
rendering resources diagrams
"""

__revision__ = "$Id: resource.py,v 1.4 2006-04-13 13:07:27 nico Exp $"

import logging
log = logging.getLogger()

from logilab.common.tree import NodeNotFound

from projman.lib import date_range
from projman.lib.constants import HOURS_PER_DAY
from projman.renderers.abstract import \
     AbstractRenderer, AbstractDrawer, TODAY, \
     TITLE_COLUMN_WIDTH, FIELD_COLUMN_WIDTH, ROW_HEIGHT
from mx.DateTime import oneHour

class ResourcesRenderer(AbstractRenderer) :

    AbstractRenderer.DEFAULT_OPTIONS.update({'selected-resource' : None})
    
    def __init__(self, options, handler,
                 colors_file=None, colors_stream=None):
        """
        Creates concrete renderer with a matching associate drawer:
        ResourceDrawer
        """
        AbstractRenderer.__init__(self, options)
        self.drawer = ResourcesDrawer(options,
                                      handler, colors_file, colors_stream)
        self._draw_resources = {}
       
    def render(self, project, stream):
        """
        render the task as a resources diagram
        """
        AbstractRenderer.render(self, project, stream)
        self.drawer._handler.save_result(stream)
     
    def _render_body(self, project) :
        """
        Generate events to draw a diagram for the resources activities description.
        
        concrete renderer should use the 'write' method or override this method
        to return the generated content.
        """
        self.drawer.main_title("Resources activities")
        self.drawer.draw_timeline()
        self.drawer.close_line()
        # print the resources informations
        resources = [resource for resource in project.resource_set.children 
                     if resource.TYPE == 'resource']
        if self.options.selected_resource:
            resources = [resource for resource in resources
                         if resource.id == self.options.selected_resource]
        for resource in resources:
            self.render_resource(resource, project)
        
    def render_resource(self, resource, project) :
        """
        generate events for a given resource
        """
        self.drawer.set_color_set(self._i)
        self._i += 1
        self.render_total_occupation(project, resource)
        # print activities for this resource
        grouped = project.activities.groupby('resource','task')
        if resource.id in grouped:
            for t_id, activities in grouped[resource.id].iteritems():
                try:
                    task = project.get_task(t_id)
                    self.render_activity(project, task, resource, activities)
                except NodeNotFound:
                    print 'ignoring unknown', t_id
        self.drawer.open_line()
        self.drawer.main_title("")
        self.drawer.draw_timeline()
        self.drawer.close_line()

    def render_activity(self, project, task, resource, activities):
        """
        generate event for a resource activity
        """
        if self.options.del_ended and task.is_finished():
            log.info("  ignoring task", task.id, "for it's finished ",
                     " and using option --del-ended (or -D)")
            return
        if self.options.del_empty:
            begin = self.drawer._timeline_days[0]
            end = self.drawer._timeline_days[-1] + 1
            for a_begin, a_end, _, _, _, _ in activities:
                if (begin <= a_begin <= end) or (begin <= a_end <= end) :
                    break
            else :
                log.info("  ignoring task", task.id,
                         "for it has no activity within diagram bounds",
                         "and using option --del-empty (or -D)")
                return
        #else: option --keep-empty set. Draw all
        self.drawer.set_color_set(self._i)
        self._i += 1
        self.drawer.open_line()
        self.drawer.main_content(task.title, project, 2, task)
        self.drawer.activity_timeline(activities, resource)
        self.drawer.close_timeline()
        self.drawer.close_line()

    def render_total_occupation(self, project, resource):
        """
        generate event for global activity
        """
        log.info("Drawing occupation for", resource.name)
        self.drawer.set_color_set(self._i)
        self._i += 1
        self.drawer.open_line()
        self.drawer.main_content(resource.name)
        self.drawer.occupation_timeline(project, resource)
        self.drawer.close_timeline()
        self.drawer.close_line()
        
class ResourcesDrawer(AbstractDrawer) :
    """
    Concrete renderer which uses a std handler to draw a Resources diagram
    """
        
    def _get_table_dimension(self, project):
        """
        calculate dimension of the table
        """
        project.get_factor()
        self.factor=project.factor
        # calculate width
        width = TITLE_COLUMN_WIDTH
        if self.options.rappel:
            width *= 2
        if self.options.showids :
            width += FIELD_COLUMN_WIDTH
        if self.options.detail > 1 :
            width += FIELD_COLUMN_WIDTH*2
        if self.options.detail > 0 :
            width += FIELD_COLUMN_WIDTH*4
        width += len(self._timeline_days)*self._timestepwidth
        # calculate height
        nb_resources = len(project.resource_set.get_resources())
        nb_tasks = len(project.root_task.flatten())
        height = ROW_HEIGHT*(nb_tasks*nb_resources)
        return (width, height)
 
    # table heads #############################################################

    def legend(self):
        """ write the diagram's legend (calls private method)"""
        self._legend_task()
        self.open_line()
        self.close_line()
        self._legend_resource()
        self.close_line()
        
    def _legend_resource(self):
        """ write the diagram's legend of resources """
        self._draw_text('Resources Legend', style='italic', weight='bold')
        self._x += FIELD_COLUMN_WIDTH*3
        self._draw_rect(FIELD_COLUMN_WIDTH-10,
                  ROW_HEIGHT,
                  fillcolor=self._colors['EVEN_SET']['RESOURCE_UNAVAILABLE'])
        self._handler.draw_line(self._x + 1 , self._y + 1, 
                          self._x + FIELD_COLUMN_WIDTH - 10,
                          self._y + ROW_HEIGHT, 
                          color=self._colors['CONSTRAINT'])
        self._x += FIELD_COLUMN_WIDTH-10
        self._draw_text('unavailable', weight='bold')
        self._x += FIELD_COLUMN_WIDTH+10

    # project table content ###################################################

    def set_bg_color(self, day, available):
        """ set background color for a day"""
        if day.date == TODAY.date:
            bgcolor = self._color_set['TODAY']
        elif not available:
            bgcolor = self._colors['EVEN_SET']['RESOURCE_UNAVAILABLE']
        elif day.day_of_week in (5, 6):
            bgcolor = self._color_set['WEEKEND']
        else:
            bgcolor = self._color_set['WEEKDAY']
        return bgcolor

    def draw_separator_resources(self):
        if self.options.timestep == 'day':
            timestep = 1
        elif self.options.timestep == 'week':
            timestep = 7
        elif self.options.timestep == 'month':
            timestep = 31
        self._handler.draw_line(self._x, self._y, 
                                    self._x + FIELD_COLUMN_WIDTH/timestep,
                                    self._y, 
                                    color=(204, 204, 204))

    def occupation_timeline(self, project, resource):
        """
        write a timeline day for a resource occupation
        """
        for day in date_range(self.view_begin, self.view_end):
            # draw background
            self._handler.draw_rect(self._x, self._y, self._daywidth, ROW_HEIGHT,
                            fillcolor=self._colors['EVEN_SET']['RESOURCE_UNAVAILABLE'])
            for d in range(self.factor):
                day_ = day + oneHour * d*(HOURS_PER_DAY / self.factor)
                if day_.hour >= 12:
                    day_ += oneHour
                act = project.activities.select('resource', resource.id)
                if act:
                    act = act.select('begin', day_)
                usage = project.get_total_usage(resource.id, day_)
                available = resource.is_available(day_) and \
                               (day_ < self.view_end) and usage and act
                self._occupation_timeline(available, 1./self.factor, day_, d)
                if usage > 1:
                    log.info(" Warning! usage", usage, "for", resource.id, "on", day_)
            #draw separators
            self.draw_separator_resources()
            # update abscisse
            self._x += self._daywidth 

    def _occupation_timeline(self, available, usage, day, d):
        """
        write a day for a resource occupation
        """
        width = self._daywidth        
        height = 0
        color = None
        if not available:
            if usage:
                color = self._colors['TASK_SET']['problem']
                height = ROW_HEIGHT
        else:
            if usage > 1:
                color = self._colors['TASK_SET']['problem']
                height = ROW_HEIGHT
            elif 0 < usage <= 1:
                color = self._color_set['RESOURCE_USED']
                height = ROW_HEIGHT*min(usage, 1)
        if day.date == TODAY.date and not(color == self._color_set['RESOURCE_USED']):
            color = self._color_set['TODAY']
            height = ROW_HEIGHT
        if color and (available or color == self._color_set['TODAY']):
                self._handler.draw_rect(self._x+1, self._y+ROW_HEIGHT-height*(d+1),
                                width, height,
                                fillcolor=color)  # occupation totale(taches confondues)

    def activity_timeline(self, activities, resource):
        """write a day for a task"""
        task = activities[0][3]
        for day in date_range(self.view_begin, self.view_end):
            available = resource.is_available(day)
            bgcolor = self.set_bg_color(day, available)
            #draw backgrgound
            self._handler.draw_rect(self._x, self._y, self._daywidth, ROW_HEIGHT,
                                fillcolor=bgcolor)

            for d in range(self.factor):
                day_ = day + oneHour * d*(HOURS_PER_DAY / self.factor)
                if day_.hour >= 12:
                    day_ += oneHour
                for begin, end, _, _, usage, _ in activities:
                    if begin <= day_ < end:
                        if usage > 1:
                            log.info("    usage", usage,
                                     "for", resource.id, "on", day)
                            break
                        self._activity_timeline(available, usage, day, d)
            self._activity_timeline(False, 0, day, d)
            self.draw_separator_resources()
            # update abscisse
            self._x += self._daywidth

    def _activity_timeline(self, available, usage, day, d):
        """write a day for a task"""
        width = self._daywidth
        height = 0
        if 0 < usage <= 1:
            if available:
                color = self._color_set['RESOURCE_USED']
                height = ROW_HEIGHT*min(usage, 1)
            else:
                color = self._colors['TASK_SET']['problem']
                height = ROW_HEIGHT
        elif usage > 1:
            color = self._colors['TASK_SET']['problem']
            height = ROW_HEIGHT
        else:
            color = None

        if color:
            self._handler.draw_rect(self._x+1, self._y+ROW_HEIGHT-height*(d+1),
                                        width, height,
                                        fillcolor=color)


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
base classes for rendering
"""

__revision__ = "$Id: gantt.py,v 1.2 2005-09-08 14:26:06 nico Exp $"

from projman import verbose
from projman.lib import date_range
from projman.renderers.abstract import \
     AbstractRenderer, AbstractDrawer, TODAY, \
     TITLE_COLUMN_WIDTH, FIELD_COLUMN_WIDTH, ROW_HEIGHT
from logilab.common.tree import NodeNotFound

class GanttRenderer(AbstractRenderer) :
    """
    Render a Gantt diagram
    """
    
    def __init__(self, option_container, handler, colors_file=None, colors_stream=None) :
        AbstractRenderer.__init__(self, option_container)
        self.drawer = GanttDrawer(option_container.get_render_options(),
                                  handler, colors_file, colors_stream)
        
    def render(self, task, stream):
        """
        render the task as a gantt diagram
        """
        AbstractRenderer.render(self, task, stream)
        self.drawer._handler.save_result(stream)
    
    def _render_body(self, project) :
        """
        generate events to draw a Gantt diagram for the task description
        
        concrete renderer should use the 'write' method or override this method
        to return the generated content.
        """
        self.drawer.main_title('Gantt diagram')
        self.drawer.draw_timeline()
        self.drawer.close_line()

        begin_p, end_p = project.get_task_date_range(project.root_task)
        self.render_node(project.root_task, project, begin_p, end_p)
        for task in self._pending_constraints:
            for c_type, c_id in task.task_constraints:
                try:
                    ct = task.get_node_by_id(c_id)
                except NodeNotFound :
                    ct = None
                if ct and ct in self._visible_tasks:
                    self.drawer.task_constraints(c_type, task, ct)

    def render_node(self, node, project, begin_p, end_p):
        """
        render self and children
        """
        if node.TYPE == 'milestone':
            self.render_milestone(node, project)
        else:
            self.render_task(node, project)
        # hide task under the depth limit
        if self.options['depth'] and node.depth() >= self.options['depth'] :
            return
        
        # hide task out of the time line
        if begin_p and end_p:
            if end_p < self.drawer._timeline_days[0] or \
                   begin_p > self.drawer._timeline_days[-1]: 
                return
            
        # render subtasks
        if node.children:
            for node_child in node.children:
                self.render_node(node_child, project, begin_p, end_p)
                        
    def render_task(self, task, project):
        """
        generate event for a given task 
        """
        verbose("drawing task", task.id)
        if self.option_container.delete_ended and task.is_finished():
            verbose(task.id, "  finished, thus ignored")
            return
        self.drawer.set_color_set(self._i)
        self._i += 1
        self._visible_tasks[task] = 1
        for val in task.task_constraints:
            if val:
                self._pending_constraints[task] = 1
                break

        self.drawer.open_line()
        self.drawer.main_content(task.title or task.id,
                                 project, task.depth(), task)
        
        if self.options['showids'] :
            self.drawer.simple_content(task.title)
                
        begin, end = project.get_task_date_range(task)
        
        for day in self.drawer._timeline_days:
            self.drawer.task_timeline(task, True, task.children, '', day,
                                      begin, end, project)
        self.drawer.close_timeline()

        if self.options['rappel']:
            self.drawer.main_content(task.title or task.id,
                                     project, task.depth(), task)
        # close table row
        self.drawer.close_line()

    def render_milestone(self, milestone, project):
        """
        generate event for a given task 
        """
        verbose("drawing task", milestone.id)
        self.drawer.set_color_set(self._i)
        self._i += 1
        self._visible_tasks[milestone] = 1
        for val in milestone.task_constraints:
            if val:
                self._pending_constraints[milestone] = 1
                break
        depth = milestone.depth()
        self.drawer.open_line()
        self.drawer.main_content(milestone.title or milestone.id,
                                 project, depth, milestone)
        
        if self.options['showids'] :
            self.drawer.simple_content(milestone.title)

        
        # print task calendar
        for d in self.drawer._timeline_days:
            self.drawer.milestone_timeline(d, milestone, project)
        self.drawer.close_timeline()

        if self.options['rappel']:
            self.drawer.main_content(milestone.title or milestone.id,
                                     project, depth, milestone)
        # close table row
        self.drawer.close_line()

class GanttDrawer(AbstractDrawer) :
    """
    Draw a Gantt diagram
    """
    
    ## AbstractDrawer interface #############################################
    
    def _init_table(self):
        """
        initialize fields needed by the table
        """
        AbstractDrawer._init_table(self)
        # mapping to save tasks coordonates
        self._tasks_slots = {}
        # current task
        self._ctask = None
        
    def _get_table_dimension(self, project):
        """
        calculate dimension of the table
        """
        #calculate width
        width = TITLE_COLUMN_WIDTH
        if self.options['rappel']:
            width *= 2
        if self.options['showids'] :
            width += FIELD_COLUMN_WIDTH
        if self.options['detail'] > 1 :
            width += FIELD_COLUMN_WIDTH*2
        if self.options['detail'] > 0 :
            width += FIELD_COLUMN_WIDTH*4
        width += len(self._timeline_days)*self._timestepwidth
        #calculate height
        height = ROW_HEIGHT * (5 + project.get_nb_tasks())
        return (width, height)
    
    # project table head/tail #################################################

    def legend(self):
        """
        write the diagram's legend of tasks
        """
        self._legend_task()

    # project table content ###################################################

    def task_timeline(self, task, worked, is_container, text, first_day,
                      begin, end, project):
        """
        write a timeline day for the task (i.e. <timestep> days)
        """
        last_day = first_day+self._timestep
        for day in date_range(first_day, last_day):
            worked = False
            if begin and end and begin <= day <= end:
                if is_container or project.is_in_allocated_time(task.id, day):
                    worked = True
            self._task_timeline(worked, is_container,
                                day == begin,
                                day == end,
                                True, # ??
                                day == last_day,
                                day)
        
    def _task_timeline(self, worked, is_container, first, last, begin, end, day):
        """
        write a day for a task
        """
        # background color
        if day.date == TODAY.date :
            bgcolor = self._color_set['TODAY']
        elif day.day_of_week in (5, 6):
            bgcolor = self._color_set['WEEKEND']
        else:
            bgcolor = self._color_set['WEEKDAY']
        # foreground color
        if worked:
            color = self._color
            coords = self._tasks_slots.setdefault(self._ctask, [])
            coords.append( (self._x, self._y) )
        else:
            color = bgcolor
        # dx, dy, dw, dh
        if begin and end:
            dx, dy, dw, dh = 0, 0, 0, 0
        elif begin:
            dx, dy, dw, dh = 1, 1, -1, -2
        elif end:
            dx, dy, dw, dh = 0, 1, -1, -2
        else:
            dx, dy, dw, dh = 0, 1, 0, -2
        # draw bg and fg rectangles
        width = self._daywidth
        self._handler.draw_rect(self._x+dx, self._y+dy, max(width+dw, 0),
                                ROW_HEIGHT+dh, fillcolor=bgcolor)
        if not is_container:
            self._handler.draw_rect(self._x+dx,
                                    self._y+dy+ROW_HEIGHT*0.125,
                                    max(width+dw, 0),
                                    ROW_HEIGHT*0.75+dh, fillcolor=color)
        # draw... what?
        if worked and is_container:
            x = self._x
            line_width = round(ROW_HEIGHT/12.)
            y = self._y+5*line_width
            end_width = ROW_HEIGHT/4
            r_x = x
            r_width = width
            if first:
                self._handler.draw_poly(((x, y),
                                         (x+end_width, y),
                                         (x, y+ROW_HEIGHT*7/12)),
                                        fillcolor=color)
                r_x = r_x +5
                r_width -= 5
            if last:
                x = x + width
                self._handler.draw_poly(((x, y),
                                         (x-end_width, y),
                                         (x, y+ROW_HEIGHT*7/12)),
                                        fillcolor=color)
                r_width -= 5
            self._handler.draw_rect(r_x, y, max(r_width, 0),
                                    ROW_HEIGHT-10*line_width, fillcolor=color)
            
        # record position
        self._x += width

    def milestone_timeline(self, day, milestone, project):
        """
        Iterate over each day to draw corresponding milestone
        """
        self._ctask = milestone
        last_day = day + self.options['timestep']
        begin, end = project.get_task_date_range(milestone)
        assert begin == end
        
        for day in date_range(day, last_day):
            draw = (day == begin)
            self._milestone_timeline(day, draw)

    def _milestone_timeline(self, day, draw):
        """
        Effectively draw a milestone
        """
        # background color
        if day.date == TODAY.date :
            bgcolor = self._color_set['TODAY']
        elif day.day_of_week in (5, 6):
            bgcolor = self._color_set['WEEKEND']
        else:
            bgcolor = self._color_set['WEEKDAY']

        width = self._daywidth
        self._handler.draw_rect(self._x, self._y, max(width, 0),
                          ROW_HEIGHT, fillcolor=bgcolor)
        # draw milestone as diamond
        if draw:
            x, y = self._x, self._y
            self._tasks_slots.setdefault(self._ctask, []).append((x, y))
            self._handler.draw_poly(((x+width, y+ROW_HEIGHT/2), 
                                     (x+width/2, y+ROW_HEIGHT), 
                                     (x, y+ROW_HEIGHT/2), 
                                     (x+width/2, y)),
                                    fillcolor=self._colors['CONSTRAINT'])
        # record position
        self._x += width
        
    def task_constraints(self, type_constraint, task, constraint_task):
        """
        draw a constraint between from task to constraint_task
        """
        # check that constrained task is in the diagram
        if not self._tasks_slots.has_key(constraint_task) or \
               not self._tasks_slots.has_key(task):
            return
        if type_constraint.startswith('begin'):
            index1 = 0
            offset1 = 0
        else:
            index1 = -1
            offset1 = self._daywidth
        if type_constraint.endswith('begin'):
            index2 = 0
            offset2 = 0
        else:
            index2 = -1
            offset2 = self._daywidth
        x1, y1 = self._tasks_slots[task][index1]
        x1 += offset1
        y1 += ROW_HEIGHT/2
        x2, y2 = self._tasks_slots[constraint_task][index2]
        x2 += offset2
        y2 += ROW_HEIGHT/2
        # split line according to differents configuration
        # just for a better visibility
        if x1 > x2:
            x_ = (x1+x2) / 2
            self._handler.draw_line(x1, y1, x_, y1,
                                    color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x_, y2, x2, y2,
                                    color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x_, y1, x_, y2,
                                    color=self._colors['CONSTRAINT'])
        elif y2 <= y1:
            self._handler.draw_line(x2, y2,
                              x2+FIELD_COLUMN_WIDTH/3, y2,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x2+FIELD_COLUMN_WIDTH/3, y2,
                              x2+FIELD_COLUMN_WIDTH/3, y1-ROW_HEIGHT/2,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x2+FIELD_COLUMN_WIDTH/3, y1-ROW_HEIGHT/2,
                              x1, y1-ROW_HEIGHT/2,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x1, y1-ROW_HEIGHT/2,
                              x2-FIELD_COLUMN_WIDTH/3, y1-ROW_HEIGHT/2,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x1, y1-ROW_HEIGHT/2,
                              x1-FIELD_COLUMN_WIDTH/3, y1-ROW_HEIGHT/2,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x1-FIELD_COLUMN_WIDTH/3, y1-ROW_HEIGHT/2,
                              x1-FIELD_COLUMN_WIDTH/3, y1,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x1-FIELD_COLUMN_WIDTH/3, y1,
                              x1, y1,
                              color=self._colors['CONSTRAINT'])
        else:
            self._handler.draw_line(x2, y2,
                              x2+FIELD_COLUMN_WIDTH/3, y2,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x2+FIELD_COLUMN_WIDTH/3, y2,
                              x2+FIELD_COLUMN_WIDTH/3, y1+ROW_HEIGHT/2,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x2+FIELD_COLUMN_WIDTH/3, y1+ROW_HEIGHT/2,
                              x1, y1+ROW_HEIGHT/2,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x1, y1+ROW_HEIGHT/2,
                              x2-FIELD_COLUMN_WIDTH/3, y1+ROW_HEIGHT/2,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x1, y1+ROW_HEIGHT/2,
                              x1-FIELD_COLUMN_WIDTH/3, y1+ROW_HEIGHT/2,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x1-FIELD_COLUMN_WIDTH/3, y1+ROW_HEIGHT/2,
                              x1-FIELD_COLUMN_WIDTH/3, y1,
                              color=self._colors['CONSTRAINT'])
            self._handler.draw_line(x1-FIELD_COLUMN_WIDTH/3, y1,
                              x1, y1,
                              color=self._colors['CONSTRAINT'])
            
        self._handler.draw_poly(((x1+2, y1), (x1-4, y1+4), (x1-4, y1-4)),
                          fillcolor=self._colors['CONSTRAINT'])

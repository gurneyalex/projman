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
"""
base classes for rendering Gantt diagrams
"""

from projman.lib import date_range
from projman.lib.constants import HOURS_PER_DAY
from projman.renderers.abstract import \
     AbstractRenderer, AbstractDrawer, TODAY, \
     TITLE_COLUMN_WIDTH, FIELD_COLUMN_WIDTH, ROW_HEIGHT, oneDay
from logilab.common.tree import NodeNotFound
from mx.DateTime import oneHour

class GanttRenderer(AbstractRenderer) :
    """
    Render a Gantt diagram
    """
    
    def __init__(self, options, handler, colors_file=None, colors_stream=None) :
        AbstractRenderer.__init__(self, options)
        self.drawer = GanttDrawer(options, handler, colors_file, colors_stream)
        
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
        # XXX TODO: get rid of these coords hacks in self.drawer
        # we must *not* use a state machine anymore, IMHO
        x_ = self.drawer._x
        self.drawer.draw_timeline()
        self.drawer.close_line()

        y_min = self.drawer._y

        self.render_node(project.root_task, project)

        y_max = self.drawer._y
        first_day = self.drawer._timeline_days[0]
        last_day = self.drawer._timeline_days[-1]+self.drawer._timestep
        rnge = self.drawer._timeline_all_days
        self.drawer.draw_separator_gantt(rnge, x_, y_min, y_max)
        self.drawer.draw_weekends_bg(rnge, x_, y_min, y_max)

        for task in self._pending_constraints:
            for c_type, c_id, priority in task.task_constraints:
                try:
                    ct = task.get_node_by_id(c_id)
                except NodeNotFound :
                    ct = None
                if ct and ct in self._visible_tasks:
                    self.drawer.task_constraints(c_type, task, ct, project.factor)        

    def render_node(self, node, project):
        """
        render self and children
        """
        # hide task under the depth limit
        if self.options.depth and node.depth() >= self.options.depth :
            return
        
        begin_p, end_p = project.get_task_date_range(node)
        # hide task out of the time line
        if begin_p and end_p:
            if end_p < self.drawer._timeline_days[0] or \
                   begin_p > self.drawer._timeline_days[-1]: 
                return
            
        if node.TYPE == 'milestone':
            self.render_milestone(node, project)
        else:
            self.render_task(node, project)
        # render subtasks
        if node.children:
            for node_child in node.children:
                self.render_node(node_child, project)
                
    def render_task(self, task, project):
        """
        generate event for a given task 
        """
        project.get_factor()
        factor = project.factor
        if self.options.del_ended and task.is_finished():
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
        
        if self.options.showids :
            self.drawer.simple_content(task.title)
                
        task_begin, task_end = project.get_task_date_range(task)
        task_end -= oneHour * HOURS_PER_DAY / factor
        x = self.drawer._x
        self.drawer.task_timeline_bg()
        if not task.children:
            self.drawer._x = x
            self.drawer.render_leaf_task(task, task_begin, task_end, project)
            
        if task.children:
            self.drawer._x = x
            self.drawer.render_root_task(task, task_begin, task_end, project)

        self.drawer.close_timeline()
        if self.options.rappel:
            self.drawer.main_content(task.title or task.id,
                                     project, task.depth(), task)
        # close table row
        self.drawer.close_line()


    def render_milestone(self, milestone, project):
        """
        generate event for a given task
        """
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

        if self.options.showids :
            self.drawer.simple_content(milestone.title)

        # print task calendar
        for d in self.drawer._timeline_days:
            self.drawer.milestone_timeline(d, milestone, project)
        self.drawer.close_timeline()

        if self.options.rappel:
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
        if self.options.rappel:
            width *= 2
        if self.options.showids :
            width += FIELD_COLUMN_WIDTH*1
        if 0 and self.options.detail > 1 :
            width += FIELD_COLUMN_WIDTH*2
        if 0 and self.options.detail > 0 :
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

    def render_leaf_task(self, task, task_begin, task_end, project):
        factor = project.factor
        width = self._daywidth / factor
        ddays = (task_begin - self._timeline_days[0]).days
        x = self._x + width * (ddays * factor) 
        w = ((task_end-task_begin).days + 1) * width * factor
        self._handler.draw_rect(x,
                                self._y+0+ROW_HEIGHT*0.125,
                                max(w+0, 0),
                                ROW_HEIGHT*0.75+0, fillcolor=self._color)
        coords = self._tasks_slots.setdefault(self._ctask, [])
        coords.extend( [(x-width/2, self._y), (x-width/1+max(w+0, 0), self._y)] )

        # be sure weekends do not seems to be working days
        day = task_begin
        while day <= task_end:
            if day.day_of_week in (5,6):
                self._handler.draw_rect(x,
                                        self._y+1,
                                        self._daywidth,
                                        ROW_HEIGHT-2, fillcolor=self._color_set['WEEKDAY'])
            day += oneDay
            x += self._daywidth
                
            
        
    def render_root_task(self, task, task_begin, task_end, project):
        factor = project.factor
        width = self._daywidth / factor
        ddays = (task_begin - self._timeline_days[0]).days
        x = self._x + width * (ddays * factor) 
        w = ((task_end-task_begin).days + 1) * width * factor

        line_width = (ROW_HEIGHT/12.)
        y = self._y+5*line_width
        end_width = ROW_HEIGHT/4
        r_x = x
        r_width = w

        # XXX TODO
        #if task.link:
        #    self.open_link(task.link)

        # XXX TODO: merge these 3 paths in one poly
        self._handler.draw_rect(r_x, y, max(r_width, 0),
                                ROW_HEIGHT-10*line_width, fillcolor=self._color)

        self._handler.draw_poly(((x, y),
                                 (x+end_width, y),
                                 (x, y+ROW_HEIGHT*7/12)),
                                fillcolor=self._color)
        r_width -= 5
        r_x = x + w
        self._handler.draw_poly(((r_x, y),
                                 (r_x-end_width, y),
                                 (r_x, y+ROW_HEIGHT*7/12)),
                                fillcolor=self._color)

        #if task.link:
        #    self.close_link()
        coords = self._tasks_slots.setdefault(self._ctask, [])
        coords.extend( [(x-width/2, self._y), (x + r_width, self._y)] )

    def task_timeline_bg(self):
        """Draw the background of a timeline"""
        rnge = self._timeline_all_days
        first_day = rnge[0]
        last_day = rnge[-1]+self._timestep
        # XXX This is useless...
        daywidth = self._daywidth
        # first draw one big rectangle
        self._handler.draw_rect(self._x, self._y+1, daywidth*len(rnge),
                                ROW_HEIGHT-2, fillcolor=self._color_set['WEEKDAY'])
        # draw today
        if TODAY.day_of_week not in (5,6) and first_day <= TODAY <= last_day:
            n = int((TODAY - first_day).days)
            self._handler.draw_rect(self._x+n*daywidth, self._y+1,
                                    daywidth, ROW_HEIGHT-2,
                                    fillcolor=self._color_set['TODAY'])
            
    def draw_weekends_bg(self, rnge, x_min, y_min, y_max):
        daywidth = self._daywidth
        #bgcolor = self._color_set['WEEKEND']
        bgcolor = (100,0,0,50)
        first_day = rnge[0]
        last_day = rnge[-1]
        n0 = (12 - first_day.day_of_week)%7
        for i in range(n0, len(rnge), 7):
            self._handler.draw_rect(x_min+i*daywidth, y_min,
                                    2*daywidth, y_max-y_min,
                                    fillcolor=bgcolor)

    def draw_separator_gantt(self, rnge, x_min, y_min, y_max):
        daywidth = self._daywidth
        color = (204,204,204)
        if self._timestep == 1:
            for n in range(len(rnge)):
                self._handler.draw_line(x_min+n*daywidth, y_min-ROW_HEIGHT,
                                        x_min+n*daywidth, y_max+ROW_HEIGHT,
                                        color=color)
                self._handler.draw_dot(x_min+(n+0.5)*daywidth, y_min,
                                       x_min+(n+0.5)*daywidth, y_max,
                                       4,
                                       color=color)
        elif self._timestep == 7:
            for n,day in enumerate(rnge):
                if day.day_of_week == 0:
                    self._handler.draw_line(x_min+n*daywidth, y_min-ROW_HEIGHT,
                                            x_min+n*daywidth, y_max+ROW_HEIGHT,
                                            color=color)
                else:
                    self._handler.draw_dot(x_min+n*daywidth, y_min,
                                           x_min+n*daywidth, y_max,
                                           4,
                                           color=color)          

        else: # timestep == month
            for n,day in enumerate(rnge):
                if day.day == 1:
                    self._handler.draw_line(x_min+n*daywidth, y_min-ROW_HEIGHT,
                                            x_min+n*daywidth, y_max+ROW_HEIGHT,
                                            color=color)
                #elif day.day_of_week == 0:
                #    self._handler.draw_dot(self._x+n*daywidth, self._y,
                #                       self._x+n*daywidth, self._y+ROW_HEIGHT,
                #                       4,
                #                       color=(204,204,204))          
                # les pointilles genent la lecture du graphe

    def milestone_timeline(self, day, milestone, project):
        """
        Iterate over each day to draw corresponding milestone
        """
        self._ctask = milestone
        last_day = day + self._timestep
        begin, end = project.get_task_date_range(milestone)
        assert begin == end
        for day in date_range(day, last_day):
            draw = (day == begin)
            self._milestone_timeline(day, draw, project.factor)

    def _milestone_timeline(self, day, draw, factor):
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
        first_day = self._timeline_days[0]
        last_day = self._timeline_days[-1]+self._timestep
        rnge = list( date_range( first_day, last_day ) )
        self._handler.draw_rect(self._x, self._y, max(width, 0),
                          ROW_HEIGHT, fillcolor=bgcolor)
        self.draw_separator_gantt([day], self._x, self._y, self._y)

        # draw milestone as diamond
        if draw:
            x, y = self._x, self._y
            self._tasks_slots.setdefault(self._ctask, []).append((x, y))
            self._handler.draw_poly(((x+(width-1)/factor, y+ROW_HEIGHT/2), # right
                                     (x+width/(2*factor), y+ROW_HEIGHT*3/4), # top
                                     (x+1, y+ROW_HEIGHT/2), # left
                                     (x+width/(2*factor), y+ROW_HEIGHT/4)), # bottom
                                    fillcolor=self._colors['CONSTRAINT'])
        # record position
        self._x += width
        
    def task_constraints(self, type_constraint, task, constraint_task, factor):
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
            offset2 = self._daywidth / factor
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
            points = ((x1,y1), (x_,y1), (x_,y2), (x2,y2))
        else:
            if y2 <= y1:
                sign = -1.0
            else:
                sign = +1.0
            points = ((x2,y2),
                      (x2+FIELD_COLUMN_WIDTH/3, y2),
                      (x2+FIELD_COLUMN_WIDTH/3, y1 + sign*ROW_HEIGHT/2),
                      (x1-FIELD_COLUMN_WIDTH/3, y1 + sign*ROW_HEIGHT/2),
                      (x1-FIELD_COLUMN_WIDTH/3, y1),
                      (x1, y1))
        self._handler.draw_poly(points, color=self._colors['CONSTRAINT'], close=False)
        self._handler.draw_poly(((x1+2, y1), (x1-4, y1+4), (x1-4, y1-4)),
                                fillcolor=self._colors['CONSTRAINT'],
                                close=True)

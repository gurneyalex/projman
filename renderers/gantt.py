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

from projman.lib import date_range
from projman.renderers.abstract import \
     AbstractRenderer, AbstractDrawer, TODAY, \
     TITLE_COLUMN_WIDTH, FIELD_COLUMN_WIDTH, ROW_HEIGHT
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
        self.drawer.draw_timeline()
        self.drawer.close_line()

        begin_p, end_p = project.get_task_date_range(project.root_task)
        self.render_node(project.root_task, project, begin_p, end_p)
        for task in self._pending_constraints:
            for c_type, c_id, priority in task.task_constraints:
                try:
                    ct = task.get_node_by_id(c_id)
                except NodeNotFound :
                    ct = None
                if ct and ct in self._visible_tasks:
                    self.drawer.task_constraints(c_type, task, ct, project.factor)        

    def render_node(self, node, project, begin_p, end_p):
        """
        render self and children
        """
        if node.TYPE == 'milestone':
            self.render_milestone(node, project)
        else:
            self.render_task(node, project)
        # hide task under the depth limit
        if self.options.depth and node.depth() >= self.options.depth :
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
                
        begin, end = project.get_task_date_range(task)
        end -= oneHour * 8 /factor
        self.drawer.task_timeline_bg()
        for day in self.drawer._timeline_days:
            self.drawer.task_timeline(task, True, task.children, '', day,
                                          begin, end, project)
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

    def task_timeline(self, task, worked, is_container, text, first_day,
                      begin, end, project):
        """
        write a timeline day for the task (i.e. <timestep> days)
        """
        last_day = first_day + self._timestep - (15 +8 / project.factor) * oneHour
        for d in range(self._timestep):
            for i in range(project.factor):
                day_ = d + first_day + i*(1./project.factor)*8*oneHour
                if day_.hour >= 12:
                    day_ += oneHour
                worked = False
                if begin and end and begin <= day_ <= end:
                    if is_container or project.is_in_allocated_time(task.id, day_):
                        worked = True
                if task.link and begin == day_:
                    self.open_link(task.link)
                self._task_timeline(worked, is_container,
                                        day_ == begin,
                                        day_ == end,
                                        day_ == first_day,
                                        day_ == end,
                                        day_,
                                        project.factor)
                if task.link and end == day_:
                    self.close_link()
                

    def task_timeline_bg( self ):
        """Draw the background of a timeline"""
        first_day = self._timeline_days[0]
        last_day = self._timeline_days[-1]+self._timestep
        rnge = list( date_range( first_day, last_day ) )
        daywidth = self._daywidth
        self._handler.draw_rect(self._x, self._y+1, daywidth*len(rnge),
                                ROW_HEIGHT-2, fillcolor=self._color_set['WEEKDAY'])
        # draw week-end days-
        for n, day in enumerate(rnge):
            if day.date == TODAY.date :
                bgcolor = self._color_set['TODAY']
            elif day.day_of_week in (5, 6):
                bgcolor = self._color_set['WEEKEND']
            else:
                continue
            self._handler.draw_rect(self._x+n*daywidth, self._y+1, daywidth,
                                    ROW_HEIGHT-2, fillcolor=bgcolor)

        # affichage separateurs
        self.draw_separator_gantt(rnge)

    def draw_separator_gantt(self, rnge):
        daywidth = self._daywidth
        if self._timestep == 1:
            for n in range(len(rnge)):
                self._handler.draw_line(self._x+n*daywidth, self._y,
                                  self._x+n*daywidth, self._y+ROW_HEIGHT,
                                  color=(204,204,204))
                self._handler.draw_dot(self._x+(n+0.5)*daywidth, self._y,
                                  self._x+(n+0.5)*daywidth, self._y+ROW_HEIGHT,
                                  4,
                                  color=(204,204,204))
        elif self._timestep == 7:
            for n,day in enumerate(rnge):
                if day.day_of_week == 0:
                    self._handler.draw_line(self._x+n*daywidth, self._y,
                                       self._x+n*daywidth, self._y+ROW_HEIGHT,
                                       color=(204,204,204))
                else:
                    self._handler.draw_dot(self._x+n*daywidth, self._y,
                                       self._x+n*daywidth, self._y+ROW_HEIGHT,
                                       4,
                                       color=(204,204,204))          

        else: # timestep == month
            for n,day in enumerate(rnge):
                if day.day == 1:
                    self._handler.draw_line(self._x+n*daywidth, self._y,
                                      self._x+n*daywidth, self._y+ROW_HEIGHT,
                                      color=(204,204,204))
                #elif day.day_of_week == 0:
                #    self._handler.draw_dot(self._x+n*daywidth, self._y,
                #                       self._x+n*daywidth, self._y+ROW_HEIGHT,
                #                       4,
                #                       color=(204,204,204))          
                # les pointilles genent la lecture du graphe

    def _task_timeline(self, worked, is_container, first, last, begin, end, day, factor):
        """
        write a day for a task
        """
        width = self._daywidth / factor
        if not worked:
            self._x += width
            return

        OFFSETS = {
            (True,True)  : (0, 0, 0, 0),
            (True,False) : (1, 1, -1, -2),
            (False,True) : (0, 1, -1, -2),
            (False,False): (0, 1, 0, -2), }
        dx, dy, dw, dh = OFFSETS[ (begin,end) ]

        color = self._color
        coords = self._tasks_slots.setdefault(self._ctask, [])
        coords.append( (self._x, self._y) )

        # draw bg and fg rectangles
        if worked and not is_container:
            self._handler.draw_rect(self._x+dx,
                                    self._y+dy+ROW_HEIGHT*0.125,
                                    max(width+dw, 0),
                                    ROW_HEIGHT*0.75+dh, fillcolor=color)
        # draw... what?
        elif worked and is_container:
            x = self._x
            line_width = round(ROW_HEIGHT/12.)
            y = self._y+5*line_width
            end_width = ROW_HEIGHT/4
            r_x = x
            r_width = width
            self._handler.draw_rect(r_x, y, max(r_width, 0),
                           ROW_HEIGHT-10*line_width, fillcolor=color)

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
        self._x += width

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
        self.draw_separator_gantt([day])

        # draw milestone as diamond
        if draw:
            x, y = self._x, self._y
            self._tasks_slots.setdefault(self._ctask, []).append((x, y))
            self._handler.draw_poly(((x+(width-2)/factor, y+ROW_HEIGHT/2), #coin droit
                                     (x+width/(2*factor), y+ROW_HEIGHT*3/4), #haut
                                     (x+2, y+ROW_HEIGHT/2), #gauche
                                     (x+width/(2*factor), y+ROW_HEIGHT/4)), # bas
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

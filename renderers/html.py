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
Projman - (c)2000-2005 LOGILAB <contact@logilab.fr> - All rights reserved.
Home: http://www.logilab.org/projman

Render a Project to HTML.
"""

from projman.lib import *
from projman.renderers.resource import *

HTML_CSS = {
    'project':           ('class="project"','',''),
    'timeline':          ('class="timeline"','',''),
    'resource':          ('class="resource"','',''),
    'holiday':           ('class="holiday"','',''),
    'workday':           ('class="workday"','',''),
    'today':             ('class="today"','',''),
    'calendar':          ('class="calendar"','',''),
    'cont_todo':         ('class="cont_todo"','',''),
    'cont_ready':        ('class="cont_ready"','',''),
    'cont_run':          ('class="cont_run"','',''),
    'cont_done':         ('class="cont_done"','',''),
    'leaf_todo':         ('class="leaf_todo"','',''),
    'leaf_ready':        ('class="leaf_ready"','',''),
    'leaf_run':          ('class="leaf_run"','',''),
    'leaf_done':         ('class="leaf_done"','',''),
    'leaf_problem':      ('class="leaf_problem"','',''),
    'leaf_date_todo':    ('class="leaf_date_todo"','',''),
    'leaf_date_ready':   ('class="leaf_date_ready"','',''),
    'leaf_date_run':     ('class="leaf_date_run"','',''),
    'leaf_date_done':    ('class="leaf_date_done"','',''),
    'leaf_date_problem': ('class="leaf_date_problem"','',''),
    'cont_date_todo':    ('class="cont_date_todo"','',''),
    'cont_date_ready':   ('class="cont_date_ready"','',''),
    'cont_date_run':     ('class="cont_date_run"','',''),
    'cont_date_done':    ('class="cont_date_done"','',''),
    'cont_date_problem': ('class="cont_date_problem"','',''),
    }

COLOR_TASK = { 'todo' :  ("6666FF", "AAAAFF", "9999FF"),
               'ready':  ("66FF66", "AAFFAA", "99FF99"),
               'run'  :  ("FF8800", "FFBB44", "FFBB33"),
               'done' :  ("666666", "AAAAAA", "BBBBBB"),
               'problem':("FF0000", "FF8888", "")
               }
HTML_NOCSS = {
    'project':           ('','<font size="3" color="orangered">','</font>'),
    'timeline':          ('','',''),
    'resource':          ('','<b>','</b>'),
    'holiday':           ('bgcolor="#DDDDDD"','',''),
    'workday':           ('bgcolor="#%s"'%COLOR_TASK['todo'][0],'',''),
    'today':             ('', '<font size="1">','</font>'),
    'calendar':          ('','',''),
    'cont_todo':         ('bgcolor="#%s"'%COLOR_TASK['todo'][2],'<i>','</i>'),
    'cont_ready':        ('bgcolor="#%s"'%COLOR_TASK['ready'][2],'<i>','</i>'),
    'cont_run':          ('bgcolor="#%s"'%COLOR_TASK['run'][2],'<i>','</i>'),
    'cont_done':         ('bgcolor="#%s"'%COLOR_TASK['done'][2],'<i>','</i>'),
    'leaf_todo':         ('bgcolor="#%s"'%COLOR_TASK['todo'][2],'',''),
    'leaf_ready':        ('bgcolor="#%s"'%COLOR_TASK['ready'][2],'',''),
    'leaf_run':          ('bgcolor="#%s"'%COLOR_TASK['run'][2],'',''),
    'leaf_done':         ('bgcolor="#%s"'%COLOR_TASK['done'][2],'',''),
    'leaf_problem':      ('bgcolor="#%s"'%COLOR_TASK['problem'][2],'',''),
    'leaf_date_todo':    ('bgcolor="#%s"'%COLOR_TASK['todo'][0],'',''),
    'leaf_date_ready':   ('bgcolor="#%s"'%COLOR_TASK['ready'][0],'',''),
    'leaf_date_run':     ('bgcolor="#%s"'%COLOR_TASK['run'][0],'',''),
    'leaf_date_done':    ('bgcolor="#%s"'%COLOR_TASK['done'][0],'',''),
    'leaf_date_problem': ('bgcolor="#%s"'%COLOR_TASK['problem'][0],'',''),
    'cont_date_todo':    ('','',''),
    'cont_date_ready':   ('','',''),
    'cont_date_run':     ('','',''),
    'cont_date_done':    ('','',''),
    'cont_date_problem': ('','',''),
    }


class ResourcesHTMLRenderer(ResourcesRenderer) :
    """render a project to a gantt HTML diagram"""
    
    def __init__(self, options, css=None):
        ResourcesRenderer.__init__(self, options)
        if css:
            self._ref = HTML_CSS
        else:
            self._ref = HTML_NOCSS

    def open_table(self, activities):
        """ open the table where the resources diagram will be located """
        self._resource = None
        self.write("<table border='0'>\n")
        
    def close_table(self):
        """ close the table where the resources diagram is located """
        self.write("</table>\n")

    def open_line(self):
        """ open a new line in the table """
        self.write("<tr>")
    def close_line(self):
        """ close a table's line """
        self.write("</tr>")
        

    # project heads ######################################################
    def main_title(self, title):
        """ write the main description column's title """
        self.write("<th colspan='2' %s>%s %s%s</th>\n" % (
            self._ref['project'][0], self._ref['project'][1],
            title, self._ref['project'][2]))
        
    def simple_title(self, title, tail=0):
        """ write a simple description column's title """
        self.write("<th>%s</th>" % (title or '&nbsp;'))
            
    def timeline_title(self, date, today=0):
        """ write a timeline column title """
        if today:
            classe = 'today'                
        else :
            classe = 'timeline'
        self.write("<th %s>%s%s%s</th>" % (self._ref[classe][0],
                                           self._ref[classe][1],
                                           date, self._ref[classe][2]))

    def legend(self) :
        """ write the diagram's legend """
        self.write("<table cellpadding='3'><tr><td>Legend</td>")
        for t in ('todo', 'ready', 'run', 'problem'):
            attrs = self._ref['leaf_date_%s'%t]
            self.write("<td %s>%s%s%s</td>" % (attrs[0], attrs[1], t, attrs[2]))
        self.write("</tr></table>")
        
    # project table content ###################################################
    def main_content(self, content, depth=0, activities=None):
        """ write a main cell's content """
        if activities is not None:
            self._colspan = 0
            self.open_line()
            classe = 'project'
        else:
            classe = status_class = 'resource'
        self._colspan = 0    
        self._attrs = attrs = self._ref[classe]
        self.write("<tr valign='top'><td %s>%s&nbsp;%s</td><td %s>%s%s%s</td>" \
                   % (self._ref[status_class][0], self._ref[status_class][1],
                      self._ref[status_class][2], attrs[0],
                      attrs[1], content or "&nbsp;", attrs[2]))

    def simple_content(self, content):
        """ write a simple cell content """
        attrs = self._attrs
        self.write("<td %s>%s%s%s</td>" % (attrs[0],
                                           attrs[1], content or '&nbsp;',
                                           attrs[2]))

    def close_timeline(self):
        """ close a table's time line """
        if self._resource is not None:
            self.flush_resource_cells()
        else:
            self.flush_task_cells('')

    def flush_task_cells(self, text):
        """ flush pending task timeline cells """
        if self._colspan:
            _attrs = self._status_attrs
            self.write("<td colspan='%s' %s>%s%s%s</td>" % (
                self._colspan, _attrs[0], _attrs[1],
                (text or '&nbsp;'), _attrs[2]))
        
    # resources table content ##################################################

    def flush_resource_cells(self):
        """ flush pending resource timeline cells """
        workday = self._ref['workday']
        if self._colspan:
            self.write("<td colspan='%s' %s>%s%s</td>" % (
                self._colspan, workday[0], workday[1],workday[2]))
            self._colspan = 0

    def resource_timeline(self, usage, worked, text, day, resource):
        """ write a timeline day for a resource """
        self._resource = 1
        if not worked:
            self.flush_resource_cells()
            attrs = self._ref['holiday']
            self.write("<td %s>%s%s%s</td>" % (attrs[0], attrs[1], text, attrs[2]))
        elif not usage:
            self.flush_resource_cells()
            attrs = self._ref['calendar']
            self.write("<td %s>%s%s%s</td>" % (attrs[0], attrs[1], text, attrs[2]))
        else :
            self._colspan += 1

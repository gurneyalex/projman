# -*- coding: ISO-8859-1 -*-
# Copyright (c) 2000-2002 LOGILAB S.A. (Paris, FRANCE).
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
""" xml exportation utilities """

__revision__ = "$Id: tasks_dates_writer.py,v 1.16 2005-09-06 17:09:28 nico Exp $"

from projman.writers.tasks_costs_writer import TasksCostsDOMWriter
from projman.writers.docbook_writers import NO_NS

class TasksDatesDOMWriter(TasksCostsDOMWriter):   
    """
    return the dom representation of the tasks view.
    """

    def __init__(self, projman, options):
        TasksCostsDOMWriter.__init__(self, projman, options)
        self.ENTETE = u"Tableau récapitulatif des dates"

    def layout_node(self):
        """ create a DOM node <t_group> """
        t_group = self._doc.createElementNS(NO_NS, 'tgroup')
        t_group.setAttributeNS(NO_NS, 'cols', "4")
        t_group.setAttributeNS(NO_NS, 'align', 'left')
        t_group.setAttributeNS(NO_NS, 'colsep', "1")
        t_group.setAttributeNS(NO_NS, 'rowsep', "1")
        t_group.appendChild(self.colspec_node("c0", "3*"))
        t_group.appendChild(self.colspec_node("c1", "2*"))
        t_group.appendChild(self.colspec_node("c2", "2*"))
        t_group.appendChild(self.colspec_node("c3", "1*"))
        return t_group
    
    def table_head_node(self):
        """ create a DOM node <thead> """ 
        t_head = self._doc.createElementNS(NO_NS, 'thead')
        row = self._doc.createElementNS(NO_NS, 'row')
        # task column
        entry = self.entry_node()
        row.appendChild(entry)
        # begin
        entry = self.entry_node('left', u'Date de début')
        row.appendChild(entry)
        # end
        entry = self.entry_node('left', u'Date de fin')
        row.appendChild(entry)
        # length
        entry = self.entry_node('center', u'Durée (jours)')
        row.appendChild(entry)
        t_head.appendChild(row)
        return t_head
        
    def row_element(self, task, task_cost, level=0):
        """ create a DOM element <row> with values in task node"""
        row = self._doc.createElementNS(NO_NS, 'row')
        # indentation
        indent = u'\xA0 '*level
        # task title
        entry = self.entry_node('left', indent+task.title)
        row.appendChild(entry)
        # task begin & end
        date_begin, date_end = self.projman.get_task_date_range(task)
        entry = self.entry_node('left', date_begin.date)
        row.appendChild(entry)
        entry = self.entry_node('left', date_end.date)
        row.appendChild(entry)
        # task length
        duration = date_end+1 - date_begin
        entry = self.entry_node('left', str(duration.absvalues()[0]))
        row.appendChild(entry)
        return row

    def empty_row_element(self, task, level=0):
        """ create a DOM element <row> with values in task node"""
        row = self._doc.createElementNS(NO_NS, 'row')
        # indentation
        indent = u'\xA0 '*level
        # task title
        entry = self.entry_node('left', indent+task.title)
        row.appendChild(entry)
        # task begin & end
        date_begin, date_end = self.projman.get_task_date_range(task)
        entry = self.entry_node('left', date_begin.date)
        row.appendChild(entry)
        entry = self.entry_node('left', date_end.date)
        row.appendChild(entry)
        # task length
        duration = date_end+1 - date_begin
        entry = self.entry_node('left', str(duration.absvalues()[0]))
        row.appendChild(entry)
        return row

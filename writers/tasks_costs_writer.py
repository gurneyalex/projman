# -*- coding: ISO-8859-1 -*-
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
xml exportation utilities
"""

__revision__ = "$Id: tasks_costs_writer.py,v 1.24 2005-11-10 11:34:30 arthur Exp $"

from projman.writers.docbook_writers import AbstractTaskWriter
from projman.writers.docbook_writers import NO_NS
from projman import format_monetary

class TasksCostsDOMWriter(AbstractTaskWriter):   
    """
    return the dom representation of the tasks view.
    """

    def __init__(self, project, options):
        AbstractTaskWriter.__init__(self, project, options)
        self.ENTETE = u"Tableau récapitulatif des coûts."
        self.table = None
        self.layout = None

    def open_tree(self, root):
        """formats and writes begining of doc according to docbook format.
        """
        # init
        AbstractTaskWriter.open_tree(self, root)
        # create table for project
        self.table = self.table_node()
        self.tree_root.appendChild(self.table)
        # fill title
        self.table.appendChild(self.title_node(self.ENTETE))
        # fill column information for table
        self.layout = self.layout_node()
        # table head
        self.layout.appendChild(self.table_head_node())
        # table body
        t_body = self.table_body_node()
        self.layout.appendChild(t_body)
        self.tree.append(t_body)

    def close_tree(self):
        """formats & writes end of doc according to docbook format.
        """
        # close table for project
        self.table.appendChild(self.layout)
        # optional display
        AbstractTaskWriter.close_tree(self)

    def _build_task_node(self, task, level=0):
        """ format a task in table
        """
        # global calculation
        AbstractTaskWriter._build_task_node(self, task, level)
        # FIXME: task_cost has already been computed in
        #        AbstractTaskWriter._build_task_node !
        try:
            task_cost = self.projman.tasks.get_cell_by_ids(task.id, 'cost') or 0
        except KeyError:
            task_cost = 0
        if task_cost:
            row = self.row_element(task, task_cost, level)
        else:
            row = self.empty_row_element(task, level)

        # add row
        t_body = self.tree[-1].appendChild(row)
        # print children
        for each in task.children:
            self._build_task_node(each, level+1)

## formating methods  ########################################################
    def layout_node(self):
        """ create a DOM node <t_group> """
        t_group = self._doc.createElementNS(NO_NS, 'tgroup')
        t_group.setAttributeNS(NO_NS, 'cols', "4")
        t_group.setAttributeNS(NO_NS, 'align', 'left')
        t_group.setAttributeNS(NO_NS, 'colsep', "1")
        t_group.setAttributeNS(NO_NS, 'rowsep', "1")
        t_group.appendChild(self.colspec_node("c0", "3*"))
        t_group.appendChild(self.colspec_node("c1", "1*"))
        t_group.appendChild(self.colspec_node("c2", "2*"))
        t_group.appendChild(self.colspec_node("c3", "1*"))
        return t_group

    def table_head_node(self):
        """ create a DOM node <thead> """ 
        t_head = self._doc.createElementNS(NO_NS, 'thead')
        row = self._doc.createElementNS(NO_NS, 'row')
        entry = self.entry_node()
        row.appendChild(entry)
        entry = self.entry_node('left', u'Charge (jours.homme)')
        row.appendChild(entry)
        entry = self.entry_node('left', u'Ressources')
        row.appendChild(entry)
        entry = self.entry_node('right', u'Coût (euros)')
        row.appendChild(entry)
        t_head.appendChild(row)
        return t_head
        
    def entry_node(self, align='', value=u''):
        """ create a DOM node <entry> """
        entry = self._doc.createElementNS(NO_NS, 'entry')
        if align and value:
            entry.setAttributeNS(NO_NS, 'align', align)
            entry.appendChild(self._doc.createTextNode(value))
        return entry

    def colspec_node(self, colname, colwidth):
        """ create a DOM node <colspec> """
        colspec = self._doc.createElementNS(NO_NS, 'colspec')
        colspec.setAttributeNS(NO_NS, 'colname', colname)
        colspec.setAttributeNS(NO_NS, 'colwidth', colwidth)
        return colspec

    def table_node(self):
        """ create a DOM node <table> """
        table = self._doc.createElementNS(NO_NS, 'table')
        return table

    def table_body_node(self):
        """ create a DOM node <tbody>"""
        element = self._doc.createElementNS(NO_NS, 'tbody')
        return element

    def row_element(self, task, task_cost, level=0):
        """ create a DOM element <row> with values in task node"""
        row = self._doc.createElementNS(NO_NS, 'row')
        # indentation
        indent = u'\xA0 '*level
        # task title
        entry = self.entry_node('left', indent+task.title)
        row.appendChild(entry)
        # task duration
        duration = task.duration and unicode(task.duration) or u''
        entry = self.entry_node('left', duration)
        row.appendChild(entry)
        # task cost by resources
        costs, durations = self.projman.get_task_costs(task.id)
        # FIXME = do we what number of days for each resource or monetary cost for each resource.
        r_info = ['%s(%s)' % (r_id, format_monetary(cost)) 
                  for r_id, cost in durations.items() if r_id]
        entry = self.entry_node('left', ', '.join(r_info))
        row.appendChild(entry)
        # task global cost
        # FIXME hack : a (containing) task with no resources has global cost of 1!
        if durations.keys() == [u''] and task_cost == 1.:
            entry = self.entry_node('right', 0)
        else:
            entry = self.entry_node('right', format_monetary(task_cost))
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
        row.appendChild(self.entry_node())
        row.appendChild(self.entry_node())
        row.appendChild(self.entry_node())
        return row

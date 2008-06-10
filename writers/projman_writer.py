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

__revision__ = "$Id: projman_writer.py,v 1.17 2005-11-11 15:53:21 nico Exp $"

import logging
from logilab.common.visitor import Visitor
from projman.lib.constants import BEGIN_AT_DATE, END_AT_DATE, AT_DATE
from projman.lib.constants import REVERSE_LOAD_TYPE_MAP
from projman.lib.task import MileStone
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET
log = logging.getLogger("writer") # in case we use it one day


EXT_DATE_FORMAT = u'%Y-%m-%d'

#TEMP
import sys

# this function has been taken from http://infix.se/2007/02/06/gentlemen-indent-your-xml
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + "  "
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# xml exportation methods ######################################################

def write_schedule_as_xml(filename, project):
    root = schedule_as_dom(project)
    indent(root)
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="UTF-8")

def write_tasks_as_xml(filename, project):
    root = tasks_as_dom(project)
    indent(root)
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="UTF-8")

# dom utilities ################################################################

def schedule_as_dom(project):
    """
    returns dom representation of project's schedule
    """
    doc = ET.Element("schedule")
    for task in project.root_task.leaves():
        if isinstance(task, MileStone):
            element = ET.SubElement( doc, 'milestone', id=task.id )
        else:
            element = ET.SubElement( doc, 'task', id=task.id )

        # add date-constraints
        begin, end = project.get_task_date_range(task)
        if element.tag == "task":
            ET.SubElement( element, "constraint-date", type=BEGIN_AT_DATE ).text = str(begin)
            ET.SubElement( element, "constraint-date", type=END_AT_DATE ).text = str(end)
            if task.priority is not None:
                ET.SubElement(element, 'priority').text = str(task.priority)
            ET.SubElement(element, 'status').text = project.get_task_status(task)
        else:
            ET.SubElement( element, "constraint-date", type=AT_DATE ).text = str(begin)

        # task_constraints
        for ctype, ctask_id, priority in task.task_constraints:
            ET.SubElement(element, "constraint-task", type=ctype, idref=ctask_id)

        if element.tag == "milestone":
            continue # milestone don't need more
        # global cost
        costs = project.get_task_costs(task.id, task.duration)[0]
        global_cost = ET.SubElement(element, 'global-cost', unit='XXX')
        global_cost.text = '%.1f' % sum(costs.values())
        # cost by resource
        if costs:
            costs_list = ET.SubElement(element, 'costs_list')
            for res_id, res_cost in costs.items():
                cost = ET.SubElement(costs_list, 'cost', idref=res_id)
                cost.text = '%.1f' % res_cost
        # report planned_activities only
        # (since only results of shceduling are written
        grouped = project.activities.groupby('src', 'task', 'resource')
        try:
            planned = grouped['plan'][task.id]
        except KeyError:
            continue

        rlist = ET.SubElement(element, 'report-list')
        for r_id, rows in planned.iteritems():
            for begin, end, resource, planned_task, usage, _ in rows:
                usage = usage or 1
                act_element = ET.SubElement(rlist, 'report',
                                            idref=r_id,
                                            usage='%f' % usage)
                act_element.set('from', str(begin))
                act_element.set('to', str(end) )
    return doc

class TasksVisitor:
    def __init__(self):
        self.parents = []

    def visit_root(self, node):
        elem = ET.Element('task', id=node.id)
        self.set_common_attr( node, elem )
        for rtype, rid in node.resource_constraints:
            ET.SubElement( elem, "constraint-resource",
                           idref=rid, type=rtype )
        
        self.parents.append(elem)
        for c in node.children:
            c.accept( self )
        return elem

    def visit_task(self, node):
        elem = ET.SubElement( self.parents[-1], 'task', id=node.id )
        elem.set("load-type", REVERSE_LOAD_TYPE_MAP[node.load_type] )
        elem.set("load", str(node.duration) )
        self.set_common_attr( node, elem )

        for rtype, rid in node.resource_constraints:
            ET.SubElement( elem, "constraint-resource",
                           idref=rid, type=rtype )
        
        self.parents.append( elem )
        for c in node.children:
            c.accept( self )
        self.parents.pop()

    def visit_milestone(self, node):
        elem = ET.SubElement( self.parents[-1], 'milestone', id=node.id )
        self.set_common_attr( node, elem )

    def set_common_attr(self, node, elem):
        if node.title:
            el = ET.SubElement( elem, "label")
            el.text = node.title
        if node.description_raw:
            if node.description_format=='docbook':
                text = u"<description format='docbook'>%s</description>" % node.description_raw
                el = ET.fromstring(text.encode("utf-8"))
                elem.append( el )
            elif node.description_format=='rest':
                el = ET.SubElement( elem, "description", format="rest" )
                el.text = node.description_raw
            else:
                text = u"<description>%s</description>" % node.description_raw
                el = ET.fromstring(text.encode("utf-8"))
                elem.append( el )
        for ctype, tid, priority in node.task_constraints:
            ET.SubElement( elem, "constraint-task", type=ctype, idref=tid )

        for ctype, date, priority in node.date_constraints:
            el = ET.SubElement( elem, "constraint-date", type=ctype )
            el.text = date.strftime("%F")

def tasks_as_dom(project):
    """
    returns dom representation of project's schedule
    """
    visitor = TasksVisitor()
    return visitor.visit_root( project.root_task )

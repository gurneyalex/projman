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
try:
    from xml.dom.ext import PrettyPrint, Print
except ImportError:
    def PrettyPrint(*args):
        print args
    def Print(*args):
        print args
from xml.dom.minidom import DOMImplementation
from logilab.common.visitor import Visitor
from projman.lib.constants import BEGIN_AT_DATE, END_AT_DATE, AT_DATE
from projman.lib.task import MileStone
#from xml.dom.DOMImplementation import DOMImplementation

log = logging.getLogger("writer") # in case we use it one day


EXT_DATE_FORMAT = u'%Y-%m-%d'

#TEMP
import sys

# xml exportation methods ######################################################

def write_schedule_as_xml(filename, project):
    file_object = file(filename, 'w')
    dom = schedule_as_dom(project)
    PrettyPrint(dom, stream=file_object)
    file_object.close()

# dom utilities ################################################################

implementation = DOMImplementation()
NO_NS = None

def Document(root=None):
    """ return a DOM document node """
    dummy = None
    return implementation.createDocument(NO_NS, root, dummy)

def constraint_as_empty_dom(doc, dictio, node_type):
    """ return a DOM node for a constraint without a value """
    element = doc.createElementNS(NO_NS, 'constraint-%s' % node_type)
    for ctype, value in dictio.items():
        element.setAttributeNS(NO_NS, ctype, value)
    return element

def resource_as_empty_dom(doc, id_res):
    """ return a DOM node for a constraint without a value """
    element = doc.createElementNS(NO_NS, 'resource')
    element.setAttributeNS(NO_NS, 'idref', id_res)
    return element

def constraint_as_dom(doc, type_constraint, value, constraint_type):
    """ return a DOM node for a constraint """
    element = doc.createElementNS(NO_NS, 'constraint-%s' % constraint_type)
    element.setAttributeNS(NO_NS, 'type', type_constraint)
    element.appendChild(doc.createTextNode(str(value)))
    return element

def text_node(doc, name, value):
    """ create a DOM node <name> with a <value> text node child """
    element = doc.createElementNS(NO_NS, name)
    element.appendChild(doc.createTextNode(value))
    return element

def schedule_as_dom(project):
    """
    returns dom representation of project's schedule
    """
    doc = Document('schedule')
    root = doc.documentElement
    for task in project.root_task.leaves():
        tagtype="task"
        if isinstance(task, MileStone):
            tagtype="milestone"
        element = doc.createElementNS(NO_NS, tagtype)

        element.setAttributeNS(NO_NS, 'id', task.id)
        # add date-constraints
        begin, end = project.get_task_date_range(task)
        if tagtype=="task":
            constraint = constraint_as_dom(doc, BEGIN_AT_DATE,
                                           begin.date, 'date')
            element.appendChild(constraint)
            constraint = constraint_as_dom(doc, END_AT_DATE, end.date, 'date')
            element.appendChild(constraint)
            # priorities
            if task.priority is not None:
                element.appendChild(text_node(doc, 'priority', str(task.priority)))
            # status
            element.appendChild(text_node(doc, 'status',
                                          project.get_task_status(task)))
        else:
            constraint = constraint_as_dom(doc, AT_DATE,
                                           begin.date, 'date')
            element.appendChild(constraint)


        # task_constraints
        for ctype, ctask_id in task.task_constraints:
            dic =  {'type' : ctype, 'idref' : ctask_id}
            element.appendChild(constraint_as_empty_dom(doc, dic, 'task'))

        if tagtype=="milestone":
            root.appendChild(element)
            continue
        # global cost
        costs = project.get_task_costs(task.id)[0]
        global_cost = text_node(doc, 'global-cost', '%.1f' % (sum(costs.values())))
        global_cost.setAttributeNS(NO_NS, 'unit', 'XXX')
        element.appendChild(global_cost)
        # cost by resource
        if costs:
            costs_list = doc.createElementNS(NO_NS, 'costs_list')
            for res_id, res_cost in costs.items():
                cost = text_node(doc, 'cost', '%.1f' % res_cost)
                cost.setAttributeNS(NO_NS, 'idref', res_id)
                costs_list.appendChild(cost)
            element.appendChild(costs_list)
        # report planned_activities only
        # (since only results of shceduling are written
        grouped = project.activities.groupby('src', 'task', 'resource')
        try:
            planned = grouped['plan'][task.id]
        except KeyError:
            pass
        else:
            rlist = doc.createElementNS(NO_NS, 'report-list')
            for r_id, rows in planned.iteritems():
                for begin, end, resource, planned_task, usage, _ in rows:
                    usage = usage or 1
                    act_element = doc.createElementNS(NO_NS, 'report')
                    act_element.setAttributeNS(NO_NS, 'idref', r_id)
                    act_element.setAttributeNS(NO_NS, 'from', begin.date)
                    act_element.setAttributeNS(NO_NS, 'to', end.date)
                    act_element.setAttributeNS(NO_NS, 'usage', '%f' % usage)
                    rlist.appendChild(act_element)
            element.appendChild(rlist)
        root.appendChild(element)
    return doc



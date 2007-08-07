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
from projman import LOG_CONF
from xml.dom.ext import PrettyPrint, Print
from xml.dom.minidom import DOMImplementation
from logilab.common.visitor import Visitor
from logilab.common.tree import PrefixedDepthFirstIterator as _Iterator
from projman.lib.constants import BEGIN_AT_DATE, END_AT_DATE
#from xml.dom.DOMImplementation import DOMImplementation

log = logging.getLogger("writer") # in case we use it one day

class PrefixedDepthFirstIterator(_Iterator):
    """overrides the original one because it doesn't
    use the iter protocol
    """
    def __iter__(self):
        return self

    def next(self):
        value = _Iterator.next(self)
        if value is None:
            raise StopIteration()

EXT_DATE_FORMAT = u'%Y-%m-%d'

#TEMP
import sys

# xml exportation methods ######################################################

def as_xml_dom(node):
    """
    return the tasks tree as a DOM tree
    """
    return ProjmanDOMVisitor().visit(node)
        
def as_xml_stream(node, pretty=True, stream=None):
    """ 
    return the tasks tree as a XML stream
    if stream is not None, write into the given stream
    """
    dom = as_xml_dom(node)
    # write the project description as xml to a buffer
    if stream is None:
        from cStringIO import StringIO
        _stream = StringIO()
    else:
        _stream = stream
    if pretty:
        PrettyPrint(dom, stream=_stream)
    else:
        Print(dom, stream=_stream)
    if stream is None:
        _stream.seek(0)
    return _stream
        
def as_xml_string(node, pretty=True):
    """ 
    return the tasks tree as a XML string
    """
    return as_xml_stream(node, pretty=pretty).read()

def write_schedule_as_xml(filename, project):
    file_object = file(filename, 'w')
    dom = schedule_as_dom(project)
    PrettyPrint(dom, stream=file_object)
    file_object.close()
    
def write_activities_as_xml(filename, project):
    file_object = file(filename, 'w')
    dom = activities_as_dom(project)
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

def activities_as_dom(project):
    """
    returns dom representation of project's activities table
    """
    doc = Document('activities')
    activities_root = doc.documentElement
    grouped = project.activities.groupby('src', 'task', 'resource')
    grouped = grouped['past']
    for t_id in grouped:
        report_list = doc.createElementNS(NO_NS, 'reports-list')
        report_list.setAttributeNS(NO_NS, 'task-id', t_id)
        for r_id in grouped[t_id]:
            for begin, end, _, _, usage, _ in grouped[t_id][r_id]:
                usage = usage or '1'
                element = doc.createElementNS(NO_NS, 'report')
                element.setAttributeNS(NO_NS, 'idref', r_id)
                element.setAttributeNS(NO_NS, 'from', begin.date)
                element.setAttributeNS(NO_NS, 'to', end.date)
                element.setAttributeNS(NO_NS, 'usage', '%f' % usage)
                report_list.appendChild(element)
        activities_root.appendChild(report_list)
    return doc

def schedule_as_dom(project):
    """
    returns dom representation of project's schedule
    """
    doc = Document('schedule')
    root = doc.documentElement
    for task in project.root_task.leaves():
        element = doc.createElementNS(NO_NS, "task")
        element.setAttributeNS(NO_NS, 'id', task.id)
        # add date-constraints
        begin, end = project.get_task_date_range(task)
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
        # task_constraints
        for ctype, ctask_id in task.task_constraints:
            dic =  {'type' : ctype, 'idref' : ctask_id}
            element.appendChild(constraint_as_empty_dom(doc, dic, 'task'))
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


# Projman DOM Visitor #######################################################

class ProjmanDOMVisitor(Visitor):   
    """
    return the dom representation of the projman objects, without data included
    from other files
    """
    
    def __init__(self):
        Visitor.__init__(self, PrefixedDepthFirstIterator)
        self._type_of_days = {}

    def _visit(self, node):
        """ override Visitor._visit """
        done = {}
        for next_node in self._get_iterator(node):
            result_node = next_node.accept(self)
            if result_node:
                # FIXME: rewrite me
                if done:
                    done[next_node.parent.id].appendChild(result_node)
                done[next_node.id] = result_node


    def close_visit(self, result):
        """ the visit ends """
        return self._doc
    
    def visit_resource(self, node):
        """ visit a resource node """
        doc = self._doc
        res_element = doc.createElementNS(NO_NS, 'resource')
        res_element.setAttributeNS(NO_NS, 'type', node.type)
        res_element.setAttributeNS(NO_NS, 'id', node.id)
        node.name and res_element.appendChild(text_node(doc, 'label', node.name))
        cal_element = doc.createElementNS(NO_NS, 'use-calendar')
        cal_element.setAttributeNS(NO_NS, 'idref', node.calendar)
        res_element.appendChild(cal_element)
        cost = text_node(doc, 'hourly-rate', str(node.hourly_rate[0]))
        cost.setAttributeNS(NO_NS, 'unit', str(node.hourly_rate[1]))
        res_element.appendChild(cost)  
        return res_element
        
    
    def visit_resourcesset(self, node):
        """ visit a resourcesset node """
        self._doc = doc = Document('resources-list')
        root = doc.documentElement
        root.setAttributeNS(NO_NS, 'id', node.id)
        return root
        

    def visit_calendar(self, node, root=None):
        """ visit a calendar node """
        doc = self._doc
        cal_element = doc.createElementNS(NO_NS, 'calendar')
        calendar = node
        cal_element.setAttributeNS(NO_NS, 'id', calendar.id)
        calendar.name and cal_element.appendChild(text_node(doc, 'label',
                                                            calendar.name))

        # get the name of default working_day and nonworking_day
        d_w_name = node.type_working_days[node.default_working][0]
        d_nw_name = node.type_nonworking_days[node.default_nonworking]
        
        # set the type of days by looking to working type first
        # and then nonworking types
        e = doc.createElementNS(NO_NS, 'day-types')
        for cal_type in calendar.type_working_days:
            day = doc.createElementNS(NO_NS, 'day-type')
            cal_id = str(node.id)+'_'+str(cal_type)
            day.setAttributeNS(NO_NS, 'id', cal_id)
            label = doc.createElementNS(NO_NS, 'label')
            working_days = calendar.type_working_days[cal_type]
            label.appendChild(doc.createTextNode(working_days[0]))
            day.appendChild(label)
            intervals_list = working_days[1]
            for index in range(0, len(intervals_list)):
                i = doc.createElementNS(NO_NS, 'interval')
                start = (u'').join(str(intervals_list[index][0]).split(':'))[:4]
                end = (u'').join(str(intervals_list[index][1]).split(':'))[:4]
                i.setAttributeNS(NO_NS, 'start', start)
                i.setAttributeNS(NO_NS, 'end', end)
                day.appendChild(i)
            e.appendChild(day)
            cal_element.appendChild(e)
            self._type_of_days[node.type_working_days[cal_type][0]] = cal_id
        for cal_type in calendar.type_nonworking_days:
            day = doc.createElementNS(NO_NS, 'day-type')
            cal_id = str(node.id)+'_'+str(int(cal_type)+len(self._type_of_days))
            day.setAttributeNS(NO_NS, 'id', cal_id)
            label = doc.createElementNS(NO_NS, 'label')
            nonworking_days = calendar.type_nonworking_days[cal_type]
            label.appendChild(doc.createTextNode(nonworking_days))
            day.appendChild(label)
            e.appendChild(day)
            cal_element.appendChild(e)
            self._type_of_days[node.type_nonworking_days[cal_type]] = cal_id

        d_w = doc.createElementNS(NO_NS, 'default-working')
        d_w_id = self._type_of_days[d_w_name]
        d_w.setAttributeNS(NO_NS, 'idref', d_w_id)
        d_nw = doc.createElementNS(NO_NS, 'default-nonworking')
        d_nw_id = self._type_of_days[d_nw_name]
        d_nw.setAttributeNS(NO_NS, 'idref', d_nw_id)
        cal_element.appendChild(d_w)
        cal_element.appendChild(d_nw)

        if calendar.weekday:
            for weekday in calendar.weekday:
                day_element = doc.createElementNS(NO_NS, 'day')
                day_element.setAttributeNS(NO_NS, 'type',
                                  self._type_of_days[calendar.weekday[weekday]])
                day_element.appendChild(doc.createTextNode(weekday))
                cal_element.appendChild(day_element)

        if calendar.national_days:
            for national_day in calendar.national_days:
                nd_element = doc.createElementNS(NO_NS, 'day')
                nd_element.setAttributeNS(NO_NS, 'type', 
                                  self._type_of_days[calendar.type_nonworking_days[calendar.default_nonworking]])
                nd_element.appendChild(doc.createTextNode(national_day))
                cal_element.appendChild(nd_element)
                
        if calendar.timeperiods != []:
            for from_date, to_date, cal_type in calendar.timeperiods:
                timeperiod = doc.createElementNS(NO_NS, 'timeperiod')
                timeperiod.setAttributeNS(NO_NS, 'from', str(from_date.date))
                timeperiod.setAttributeNS(NO_NS, 'to', str(to_date.date))
                timeperiod.setAttributeNS(NO_NS, 'type',
                                          self._type_of_days[cal_type])
                cal_element.appendChild(timeperiod)
        start = doc.createElementNS(NO_NS, 'start-on')
        if calendar.start_on is not None:
            start.appendChild(doc.createTextNode(calendar.start_on.date))
        cal_element.appendChild(start)
        
        stop = doc.createElementNS(NO_NS, 'stop-on')
        if calendar.stop_on is not None:
            stop.appendChild(doc.createTextNode(calendar.stop_on.date))
        cal_element.appendChild(stop)
        return cal_element
                    
    def visit_project(self, node):
        """ visit a project node """
        if node.parent is None:
            self._doc = doc = Document('project')
            proj_element = doc.documentElement
            self.visit_task(node, proj_element)
        else:
            doc = self._doc
            proj_element = doc.createElementNS(NO_NS, 'project')
            self.visit_task(node, proj_element) 
        return proj_element
    
    def visit_milestone(self, node, mile_element=None):
        """ visit a milestone node """
        doc = self._doc
        if mile_element is None:
            mile_element = doc.createElementNS(NO_NS, 'milestone')
        mile_element.setAttributeNS(NO_NS, 'id', node.id)
        # label
        node.title and mile_element.appendChild(text_node(doc, 'label',
                                                          node.title))
        # description
        node.description and mile_element.appendChild(text_node(doc,
                                                                'description',
                                                     node.description))
        # date constraints
        for const_type, date in node.date_constraints.items():
            if date is not None:
                mile_element.appendChild(constraint_as_dom(doc, const_type, 
                            date.Format(EXT_DATE_FORMAT), 'date'))
        for const_type in node.task_constraints:
            for const_id in node.task_constraints[const_type]:
                dictio = {'type' : const_type, 'idref' : const_id}
                mile_element.appendChild(constraint_as_empty_dom(doc, dictio,
                                                                 'task'))
        return mile_element
    
    def visit_task(self, node, task_element=None):
        """ visit a task node """
        doc = self._doc
        if task_element is None:
            task_element = doc.createElementNS(NO_NS, 'task')
        self.visit_milestone(node, task_element)
        # priority
        node.priority and node.priority != -1 \
                      and task_element.appendChild(text_node(doc, 'priority',
                                                  str(node.priority)))
        if not node.children:
            node.duration and task_element.appendChild(text_node(doc, 'duration',
                                                      str(node.duration)))
            node.progress and task_element.appendChild(text_node(doc, 'progress',
                                                      '%s'%node.progress))
        for const_type, id_res, usage in node.get_resource_constraints():
            dictio = {'type':const_type, 
                      'usage':'%f' % usage, 
                      'idref': id_res}
            if node.TYPE == 'project':
                task_element.appendChild(resource_as_empty_dom(doc, id_res))    
            else:
                task_element.appendChild(constraint_as_empty_dom(doc,
                                                                 dictio,
                                                                 'resource'))
        return task_element

    def visit_schedule(self, node, element=None):
        """visit a schedule"""
        sys.stderr.write('[%s] taks_global_cost='% node.id \
                         + '%.1f' % (node.tasks_global_cost) \
                         + ' schedule=%s\n'% str(element))

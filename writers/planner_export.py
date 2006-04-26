# copyright (c) 2004 LOGILAB S.A. (Paris, FRANCE).
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

__revision__ = "$Id: planner_export.py,v 1.5 2005-09-06 17:09:26 nico Exp $"


from mx.DateTime import now
from xml.dom.ext import PrettyPrint, Print
from xml.dom.minidom import DOMImplementation
from logilab.common.visitor import Visitor
from logilab.common.tree import PrefixedDepthFirstIterator
from projman.lib.constants import BEGIN_AFTER_DATE, BEGIN_AT_DATE, BEGIN_BEFORE_DATE, \
     END_AFTER_DATE, END_AT_DATE, END_BEFORE_DATE, \
     BEGIN_AFTER_END, BEGIN_AFTER_BEGIN,\
     END_AFTER_END, END_AFTER_BEGIN
import sys

EXT_DATE_FORMAT = '%Y-%m-%d'

# xml exportation methods ######################################################

def as_xml_dom(node):
    """ 
    return the tasks tree as a DOM tree
    """
    return DOMVisitor().visit(node)
        
def as_xml_stream(node, pretty=1, stream=None):
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
        
def as_xml_string(node, pretty=1):
    """ 
    return the tasks tree as a XML string
    """
    return as_xml_stream(node, pretty=pretty).read()

def _translate_predecessor(type):
    """ translate from projman definition to planner definition """
    dict = {'ss':BEGIN_AFTER_BEGIN,
            'sf':BEGIN_AFTER_END,
            'fs':END_AFTER_BEGIN,
            'ff':END_AFTER_END}
    for planner_value in dict:
        if dict[planner_value] == type:
            return planner_value
    raise TypeError

# dom utilities ################################################################
implementation = DOMImplementation()
NO_NS = None

def document(root=None):
    """ return a DOM document node """
    #dt = implementation.createDocumentType(root, None, 'mrproject-0.6.dtd')
    dt = None
    return implementation.createDocument(NO_NS, root, dt)

def empty_dom(doc,  constraint_type, dict):
    """ return a DOM node for a constraint without a value """
    empty_dom_node = doc.createElementNS(NO_NS, constraint_type)
    for type in dict:
        empty_dom_node.setAttributeNS(NO_NS, type, dict[type])
    return empty_dom_node

def constraint_as_empty_dom(doc, dict, constraint_type):
    """ return a DOM node for a constraint without a value """
    empty_dom = doc.createElementNS(NO_NS, 'contraint-%s' % constraint_type)
    for type in dict:
        empty_dom.setAttributeNS(NO_NS, type, dict[type])
    return empty_dom

def constraint_as_dom(doc, type, value, constraint_type):
    """ return a DOM node for a constraint """
    c = doc.createElementNS(NO_NS, 'constraint-%s' % constraint_type)
    c.setAttributeNS(NO_NS, 'type', type)
    c.appendChild(doc.createTextNode(value))
    return c

def text_node(doc, name, value):
    """ create a DOM node <name> with a <value> text node child """
    c = doc.createElementNS(NO_NS, name)
    c.appendChild(doc.createTextNode(value))
    return c


# manipulation function ######################################################

def duration_to_seconds(duration, hour_per_day):
    """ translate duration in days to seconds """ 
    #TODO take into account the number of hours worked per day 
    # assumption of 8 hours/day
    if duration:
        return str(int(int(duration) * hour_per_day * 60 * 60))
    return str(0)
    
# Planner DOM Visitor ########################################################
class PlannerDOMVisitor(Visitor):   
    """
    return the dom representation of the planner object, without data included
    from other files
    """
    
    def __init__(self, day_type={}):
        Visitor.__init__(self, PrefixedDepthFirstIterator)
        self.allocations = []
        self.first_task = 0
        self.all_calendars = []
        self.all_resources = []
        self._type_of_days = {}
        self.all_tasks = {}
        self.id_translation = {'day-type':{'Working' :'1', 'Nonworking':'2','Use base':'3'}}
        self.all_projects = []
        self.current_schedule = None
        
    def _visit(self, projman):
        """ override Visitor._visit """
        #XXX BEURK! used for obtaining ressets to calculate duration
        self._stored_projman = projman
        

        #visit all projects in projman
        for node_proj in projman.projects:
            store_root = None
            done = {}
            first = 0
            self._doc = doc = document('project')
            self.all_resources = []
            self.all_calendars = []
            self.all_tasks = {}
            #visit ressourceset
            for node_rss in projman.resource_sets:
                iter = self._get_iterator(node_rss)
                n = iter.next()
                while n:
                    result = n.accept(self)
                    n = iter.next()

            iter = self._get_iterator(node_proj)
            n = iter.next()
            if not store_root:
                store_root = n
            self.all_projects.append(self._doc)
            self.current_schedule = projman.get_schedule(node_proj.id)
        
            while n:
                result = n.accept(self)
                if result :
                    if done:
                        id = self.translate_id(n.parent.id, n.parent.TYPE)
                        done[id].appendChild(result)
                    else : 
                        first = 1 
                    id = self.translate_id(n.id, n.TYPE)
                    done[id] = result
                    #add calendars information before task infos
                    if first:
                        cal = doc.createElementNS(NO_NS, 'calendars')
                        d_types = doc.createElementNS(NO_NS, 'day-types')
                        if self._type_of_days:
                            for d_t in self._type_of_days:
                                d_type = doc.createElementNS(NO_NS, 'day-type')
                                d_type.setAttributeNS(NO_NS, 'id', d_t)
                                d_type.setAttributeNS(NO_NS, 'name', self._type_of_days[d_t])
                                d_type.setAttributeNS(NO_NS, 'description', '')
                                d_types.appendChild(d_type)
                        cal.appendChild(d_types)
                        for c in self.all_calendars:
                            cal.appendChild(c)
                        id = self.translate_id(store_root.id, store_root.TYPE)
                        done[id].appendChild(cal)
                        first = 0
                n = iter.next()
        
            tasks = doc.createElementNS(NO_NS, 'tasks')
            for t in self.all_tasks:
                if not self.all_tasks[t].parentNode:
                    tasks.appendChild(self.all_tasks[t])
            id = self.translate_id(store_root.id, store_root.TYPE)
            done[id].appendChild(tasks)
        
            res = doc.createElementNS(NO_NS, 'resources')
            for r in self.all_resources:
                res.appendChild(r)

            if done:
                id = self.translate_id(store_root.id, store_root.TYPE)
            done[id].appendChild(res)
            a = doc.createElementNS(NO_NS, 'allocations')
            for i in self.allocations:
                a.appendChild(i)
            if done:
                id = self.translate_id(store_root.id, store_root.TYPE)
                done[id].appendChild(a)
        
    def close_visit(self, result):
        """ the visit ends """
        return self.all_projects
    
    def visit_resource(self, node):
        """ visit a resource node """
        doc = self._doc
        e = doc.createElementNS(NO_NS, 'resource')
        e.setAttributeNS(NO_NS, 'type', node.type)
        id = self.translate_id(node.id, node.TYPE)
        e.setAttributeNS(NO_NS, 'id', id)
        e.setAttributeNS(NO_NS, 'name', node.name)
        e.setAttributeNS(NO_NS, 'type', node.type or '1')
        e.setAttributeNS(NO_NS, 'units', '0')
        e.setAttributeNS(NO_NS, 'note', 'toto')
        e.setAttributeNS(NO_NS, 'std-rate', '')
        e.setAttributeNS(NO_NS, 'ovt-rate', '')
        e.setAttributeNS(NO_NS, 'group', '')
        if node.calendar != '':
            id_cal = self.translate_id(node.calendar, 'calendar')
            e.setAttributeNS(NO_NS, 'calendar', id_cal)
        ps = doc.createElementNS(NO_NS, 'properties')
        p = doc.createElementNS(NO_NS, 'property')
        p.setAttributeNS(NO_NS, 'name', 'cost')
        p.setAttributeNS(NO_NS, 'value', '')
        ps.appendChild(p)
        e.appendChild(ps)
        self.all_resources.append(e)
        return None
        
    
    def visit_resourcesset(self, node):
        """ visit a resourcesset node """
        return None 

    def visit_project(self, node):
        """ visit a project node """
        doc = self._doc
        if not node.parent:
            p = doc.documentElement
        else:
            return self.visit_task(node)

        p.setAttributeNS(NO_NS, 'name', node.title)
        p.setAttributeNS(NO_NS, 'company', '')
        p.setAttributeNS(NO_NS, 'phase', '')
        p.setAttributeNS(NO_NS, 'manager', '')
        p.setAttributeNS(NO_NS, 'mrproject-version', '2')
        if BEGIN_AT_DATE in node.date_constraints:
            date = node.date_constraints[BEGIN_AT_DATE]
            p.setAttributeNS(NO_NS, 'project-start', \
                date.Format('%Y%m%dT%H%M%SZ'))
        elif self.current_schedule:
            date = self.current_schedule.global_begin
            p.setAttributeNS(NO_NS, 'project-start', \
                date.Format('%Y%m%dT%H%M%SZ'))
        else:
            date = now()
            p.setAttributeNS(NO_NS, 'project-start', \
                 date.Format('%Y%m%dT%H%M%SZ'))


        # create the task node associated to projman project object
        e = doc.createElementNS(NO_NS, 'task')
        id = self.translate_id(node.id, 'task')
        # label
        e.setAttributeNS(NO_NS, 'name', node.title)
        e.setAttributeNS(NO_NS, 'type', 'normal')
        #TODO calculate duration
        duration = self.calculate_duration(node)
        e.setAttributeNS(NO_NS, 'duration', str(int(duration)))
        #TODO can we determine if we are in a fixed-duration type situation?
        e.setAttributeNS(NO_NS, 'scheduling', 'fixed-work')
        #TODO calculate work
        #duration_to_seconds(node._work, node._hours_per_day))
        work = duration
        e.setAttributeNS(NO_NS, 'work', str(int(work))) 
        e.setAttributeNS(NO_NS, 'percent-complete', str(node.progress))
        res_constraints = node.get_resource_constraints()
        for res_type, id_res, usage in res_constraints:
            id = self.translate_id(node.id, node.TYPE)
            id_res = self.translate_id(id_res, 'resource')
            dict = {'task-id' : id, \
                    'resource-id': id_res, \
                    'units' : str(usage)}
            allocation = doc.createElementNS(NO_NS, 'allocation')
            for each in dict:
                allocation.setAttributeNS(NO_NS, each, dict[each])
            self.allocations.append(allocation)

        e.setAttributeNS(NO_NS, 'id', id )
        # label
        node.title and e.setAttributeNS(NO_NS, 'name', node.title)
        # add date constraints necessarry for Planner
        if date:
            e.setAttributeNS(NO_NS, 'start', date.Format('%Y%m%dT%H%M%SZ'))
            constraint = doc.createElementNS(NO_NS, 'constraint')
            constraint.setAttributeNS(NO_NS, 'type', 'must-start-on')
            constraint.setAttributeNS(NO_NS, 'time', date.Format('%Y%m%dT%H%M%SZ')) 
            e.appendChild(constraint)
        else:
            date = now()
            e.setAttributeNS(NO_NS, 'start', date.Format('%Y%m%dT%H%M%SZ'))
            constraint = doc.createElementNS(NO_NS, 'constraint')
            constraint.setAttributeNS(NO_NS, 'type', 'must-start-on')
            constraint.setAttributeNS(NO_NS, 'time', date.Format('%Y%m%dT%H%M%SZ')) 
            e.appendChild(constraint)

        end = _get_end_project(node)
        if not end:
            e.setAttributeNS(NO_NS, 'end', '')
        else:
            e.setAttributeNS(NO_NS, 'end', end.Format('%Y%m%dT%H%M%SZ'))

        # task-constraints
        if node.task_constraints:
            #create predecessors tag
            pre_s = doc.createElementNS(NO_NS, 'predecessors')
            i = 1
            for type in node.task_constraints:
                p_type = _translate_predecessor(type).upper()
                for id in node.task_constraints[type]:
                    id = self.translate_id(id, 'task')
                    in_dic = {'predecessor-id' : id, 'id' : str(i), 'type' : p_type}
                    pre_s.appendChild(empty_dom(doc, 'predecessor', in_dic ))
                    i += 1
            e.appendChild(pre_s)
        if self.all_tasks and node.parent:
            if node.parent.id in self.all_tasks:
                self.all_tasks[node.parent.id].appendChild(e)
        self.all_tasks[node.id] = e 
        

        return p
    
   
    def visit_milestone(self, node, e=None):
        """ visit a milestone node """
        doc = self._doc
        if e is None:
            e = doc.createElementNS(NO_NS, 'task')
            e.setAttributeNS(NO_NS, 'type', 'milestone')
            e.setAttributeNS(NO_NS, 'duration', str(0))
            e.setAttributeNS(NO_NS, 'work', str(0)) 
        id = self.translate_id(node.id, 'task')
        e.setAttributeNS(NO_NS, 'id', id )
        # label
        node.title and e.setAttributeNS(NO_NS, 'name', node.title)
        # task-constraints (before date constraints since
        # task constraint => date constraint 'des que possible'
        is_task_constraint = 0
        if node.task_constraints:
            #create predecessors tag
            pre_s = doc.createElementNS(NO_NS, 'predecessors')
            i = 1
            for type in node.task_constraints:
                p_type = _translate_predecessor(type).upper()
                #flag up if there is a predecessing constraint
                if type.startswith("begin") and len(node.task_constraints[type]) > 0:
                    is_task_constraint = 1
                #format output
                for id in node.task_constraints[type]:
                    id = self.translate_id(id, 'task')
                    in_dic = {'predecessor-id' : id, 'id' : str(i), 'type' : p_type}
                    pre_s.appendChild(empty_dom(doc, 'predecessor', in_dic ))
                    i += 1
            e.appendChild(pre_s)
        # date constraints
        start = 0
        end = 0
        for date_type, date in node.date_constraints.items():
            if date_type == BEGIN_AT_DATE:
                self._fill_date_details(e, date, is_task_constraint, 'must-start-on')
                start = 1
            elif date_type == BEGIN_BEFORE_DATE:
                self._fill_date_details(e, date)
                start = 1
            elif date_type == END_AT_DATE:
                e.setAttributeNS(NO_NS, 'end', date.Format('%Y%m%dT%H%M%SZ'))
                end = 1
            elif date_type == BEGIN_AFTER_DATE:
                self._fill_date_details(e, date, is_task_constraint, 'start-no-earlier-than')
                start = 1
        if not start:
            if self.current_schedule:
                date = self.current_schedule.tasks_timeslot[node.id][0]
            else:
                date = now()
            self._fill_date_details(e, date, is_task_constraint, 'must-start-on')
        if not end:
            e.setAttributeNS(NO_NS, 'end', '')
        if self.all_tasks:
            if node.parent.id in self.all_tasks:
                self.all_tasks[node.parent.id].appendChild(e)
        self.all_tasks[node.id] = e 
        return None

    def _fill_date_details(self, father, date, attribute_only=True, constraint_type=None):
        father.setAttributeNS(NO_NS, 'start', date.Format('%Y%m%dT%H%M%SZ'))
        if not attribute_only:
            constraint = self._doc.createElementNS(NO_NS, 'constraint')
            constraint.setAttributeNS(NO_NS, 'type', constraint_type)
            constraint.setAttributeNS(NO_NS, 'time', date.Format('%Y%m%dT%H%M%SZ')) 
            father.appendChild(constraint)
    
    def visit_task(self, node, e=None):
        """ visit a task node """
        doc = self._doc
        if e is None:
            e = doc.createElementNS(NO_NS, 'task')
        # label
        e.setAttributeNS(NO_NS, 'name', node.title)
        e.setAttributeNS(NO_NS, 'type', 'normal')
        #TODO calculate duration
        duration = self.calculate_duration(node)
        e.setAttributeNS(NO_NS, 'duration', str(int(duration)))
        #TODO can we determine if we are in a fixed-duration type situation?
        e.setAttributeNS(NO_NS, 'scheduling', 'fixed-work')
        #TODO calculate work
        #duration_to_seconds(node._work, node._hours_per_day))
        work = duration
        e.setAttributeNS(NO_NS, 'work', str(int(work)) )
        e.setAttributeNS(NO_NS, 'percent-complete', str(node.progress))
        res_constraints = node.get_resource_constraints()
        for res_type, id_res, usage in res_constraints:
            id = self.translate_id(node.id, node.TYPE)
            id_res = self.translate_id(id_res, 'resource')
            dict = {'task-id' : id, \
                    'resource-id': id_res, \
                    'units' : str(usage)}
            allocation = doc.createElementNS(NO_NS, 'allocation')
            for each in dict:
                allocation.setAttributeNS(NO_NS, each, dict[each])
            self.allocations.append(allocation)
        return self.visit_milestone(node, e)

    def visit_calendar(self, node, root=None):
        """ visit a calendar node """
        doc = self._doc
        e = doc.createElementNS(NO_NS, 'calendar')
        id = self.translate_id(node.id, node.TYPE)
        e.setAttributeNS(NO_NS, 'id', id)
        e.setAttributeNS(NO_NS, 'name', node.name)
        w = doc.createElementNS(NO_NS, 'default-week')
        for weekday in node.weekday:
            if node.weekday[weekday] == 'Use base':
                id = str(int(self.translate_id('Use base', 'day-type')) -1)
            elif node.default_working != '' and \
                    node.weekday[weekday] == node.type_working_days[node.default_working][0]:
                id = str(int(self.translate_id('Working', 'day-type')) -1)
            elif node.default_nonworking != '' and \
                    node.weekday[weekday] == node.type_nonworking_days[node.default_nonworking]:
                id = str(int(self.translate_id('Nonworking', 'day-type')) -1)
            else:
                id = str(int(self.translate_id(node.weekday[weekday], 'day-type')) - 1 )
            w.setAttributeNS(NO_NS, weekday, id)
        e.appendChild(w)
        
        odt = doc.createElementNS(NO_NS, 'overridden-day-types')
        for t_d in node.type_working_days:
            od = doc.createElementNS(NO_NS, 'overridden-day-type')
            if node.default_working == t_d:
                id = str(int(self.translate_id('Working', 'day-type')) -1)
            else:
                id = str(int(self.translate_id(node.type_working_days[t_d][0], 'day-type')) - 1)
            od.setAttributeNS(NO_NS, 'id', id)
            intervals_list = node.type_working_days[t_d][1]
            for index in range(0,len(intervals_list)):
                i = doc.createElementNS(NO_NS, 'interval')
                start = ('').join(str(intervals_list[index][0]).split(':'))[:4]
                end = ('').join(str(intervals_list[index][1]).split(':'))[:4]
                i.setAttributeNS(NO_NS, 'start', start)
                i.setAttributeNS(NO_NS, 'end', end)
                od.appendChild(i)
            odt.appendChild(od)
        e.appendChild(odt)
        
        ds = doc.createElementNS(NO_NS, 'days')
            
        for timeperiod in node.timeperiods:
            type = timeperiod[2]
            datetime = timeperiod[0]
            to_date = timeperiod[1]
            while datetime <= to_date:
                d = doc.createElementNS(NO_NS, 'day')
                d.setAttributeNS(NO_NS, 'date', ('').join(datetime.date.split('-')))
                d.setAttributeNS(NO_NS, 'type', 'day-type')
                if node.default_working != '' and \
                       type == node.type_working_days[node.default_working][0]:
                    id = str(int(self.translate_id('Working', 'day-type')) - 1)
                elif node.default_nonworking != '' and \
                         type == node.type_nonworking_days[node.default_nonworking]:
                    id = str(int(self.translate_id('Nonworking', 'day-type')) - 1)
                elif type == 'Use base':
                    id = str(int(self.translate_id('Use base', 'day-type')) - 1)
                else :
                    id = str(int(self.translate_id(type, 'day-type')) -1 )
                d.setAttributeNS(NO_NS, 'id', id)
                ds.appendChild(d)
                datetime = datetime + 1
        e.appendChild(ds)

        if self._type_of_days == {}:
            for t_day in node.type_working_days:
                if t_day == node.default_working:
                    id = str(int(self.translate_id('Working', 'day-type')) - 1)
                    self._type_of_days[id] = 'Working'
                else:
                    id = str(int(self.translate_id(node.type_working_days[t_day][0], 'day-type'))\
                         - 1)
                    self._type_of_days[id] = node.type_working_days[t_day][0]

            for t_day in node.type_nonworking_days:
                if t_day == node.default_nonworking:
                    id = str(int(self.translate_id('Nonworking', 'day-type')) - 1)
                    self._type_of_days[id] = 'Nonworking'
                elif node.type_nonworking_days[t_day] == 'Use base':
                    id = str(int(self.translate_id('Use base', 'day-type')) - 1)
                    self._type_of_days[id] = 'Use base'
                else:
                    id = str(int(self.translate_id(node.type_nonworking_days[t_day], 'day-type'))\
                         - 1)
                    self._type_of_days[id] = node.type_nonworking_days[t_day]
            id = str(int(self.translate_id('Use base', 'day-type')) - 1)
            self._type_of_days[id] = 'Use base'
            
        if node.parent.TYPE == 'resourcesset':
            self.all_calendars.append(e)

        if node.children != []:
            for child in node.children:
                e.appendChild(self.visit_calendar(child, node))
            
        if root is not None:
            return e
        else:
            return None

    def translate_id(self, id, type):
        """ translate string id (projman) to integer ids (planner) """
        if type not in self.id_translation:
            self.id_translation[type] = {}
        if id in self.id_translation[type]:
            return str(self.id_translation[type][id])
        else:
            new_id = len(self.id_translation[type])+1
            self.id_translation[type][id] = new_id
            return str(new_id)
    
    def calculate_duration(self, node):
        """ calculate number of seconds depending on task/resource/calendars """
        begin, end = node.get_date_range()
        task_duration = 0
        day_duration = int(node.duration)
        if begin == 0:
            begin = now()
        if end == 0:
            end = now() + 2 * day_duration
        current_date = begin
        while current_date <= end:
            if node.resource_constraints:
                for res_type, res_id, usage in node.resource_constraints:
                    res = self._stored_projman.get_resource(res_id)
                    daily_duration = res.get_duration_of_work(current_date)
                    task_duration += daily_duration * int(usage) / 100
                    if daily_duration:
                        day_duration -= 1   
                    if day_duration == 0:
                        break
                current_date += 1
                if day_duration == 0:
                    break
            else:
                daily_duration = 8 * 60 * 60
                task_duration += daily_duration
                if daily_duration:
                    day_duration -= 1   
                if day_duration == 0:
                    break
                current_date += 1
        return task_duration
            
def _get_begin_project(project):
    """
    set a begin date for project node
    """
    begin = now()
    node = project

    if BEGIN_AT_DATE in node.date_constraints:
        return node.date_constraints[BEGIN_AT_DATE]
    
    all_tasks = node.flatten()
    for task in all_tasks:
        if BEGIN_AT_DATE in task.date_constraints:
            if task.date_constraints[BEGIN_AT_DATE] <= begin:
                begin = task.date_constraints[BEGIN_AT_DATE]

    return begin

def _get_end_project(project):
    """
    set a end date for project node
    """
    end = now()
    node = project

    if END_AT_DATE in node.date_constraints:
        return node.date_constraints[END_AT_DATE]
    
    all_tasks = node.flatten()
    for task in all_tasks:
        if END_AT_DATE in task.date_constraints:
            if task.date_constraints[END_AT_DATE] >= end:
                end = task.date_constraints[END_AT_DATE]

    return end
            

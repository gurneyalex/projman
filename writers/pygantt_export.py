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
import sys 
from xml.dom.ext import PrettyPrint, Print
from xml.dom.minidom import DOMImplementation
from logilab.common.visitor import Visitor
from logilab.common.tree import PrefixedDepthFirstIterator

EXT_DATE_FORMAT = '%Y-%m-%d'

# xml exportation methods ######################################################

def as_xml_dom(node):
    """ 
    return the tasks tree as a DOM tree
    """
    return ProjmanDOMVisitor().visit(node)
        
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
    
# dom utilities ################################################################
implementation = DOMImplementation()
NO_NS = None

def Document(root=None):
    """ return a DOM document node """
    if root == 'project':
        dt = implementation.createDocumentType(root, None, None)#'project.dtd')
    elif root == 'resources-list':
        dt = implementation.createDocumentType(root, None, 'resources.dtd')
    else:
        dt = None
    return implementation.createDocument(NO_NS, root, dt)

def constraint_as_empty_dom(doc, type, id):
    """ return a DOM node for a constraint without a value """
    c = doc.createElementNS(NO_NS, 'constraint')
    c.setAttributeNS(NO_NS, 'type', type)
    c.appendChild(doc.createTextNode(id))
    return c

def constraint_as_dom(doc, type, value):
    """ return a DOM node for a constraint """
    c = doc.createElementNS(NO_NS, 'constraint')
    c.setAttributeNS(NO_NS, 'type', type)
    c.appendChild(doc.createTextNode(value))
    return c

def text_node(doc, name, value):
    """ create a DOM node <name> with a <value> text node child """
    c = doc.createElementNS(NO_NS, name)
    c.appendChild(doc.createTextNode(value))
    return c


# Projman DOM Visitor ##################################################################
class PyganttDOMVisitor(Visitor):   
    """
    return the dom representation according to pygantt dtd of the projman objects,
    without data included from other files
    """
    
    def __init__(self):
        Visitor.__init__(self, PrefixedDepthFirstIterator)
        self.all_resources = []
        self.all_calendars = []
        self.all_projects = []
        self.all_tasks = {}
        
    def _visit(self, projman):
        """ override Visitor._visit """
        for node_proj in projman.projects:
        
            store_root = None
            done = {}
            first = 0
            self._doc = doc = Document('project')
            
            self.all_calendars = []
            self.all_resources = []
            self.all_tasks = {}
            
            #visit ressourceset
            for node_rss in projman.resource_sets:
                iter = self._get_iterator(node_rss)
                n = iter.next()
                while n:
                    result = n.accept(self)
                    n = iter.next()

            #visit project path
            iter = self._get_iterator(node_proj)
            n = iter.next()
            if not store_root:
                store_root = n
            self.all_projects.append(self._doc)

            while n:
                result = n.accept(self)
                if result :
                    if done:
                        done[n.parent.id].appendChild(result)
                    else : 
                        first = 1 
                    done[n.id] = result
                n = iter.next()

            res = doc.createElementNS(NO_NS, 'resources-list')
            for r in self.all_resources:
                res.appendChild(r)
            done[store_root.id].appendChild(res)
            
            for c in self.all_calendars:
                res.appendChild(c)
            if done :
                done[store_root.id].appendChild(res)
        
            for t in self.all_tasks:
                if not self.all_tasks[t].parentNode:
                    done[store_root.id].appendChild(self.all_tasks[t])
 
        
    def close_visit(self, result):
        """ the visit ends """
        return self.all_projects

    def visit_resource(self, node):
        """ visit a resource node """
        # create resource node
        doc = self._doc
        e = doc.createElementNS(NO_NS, 'resource')
        # set attributes
        e.setAttributeNS(NO_NS, 'type', node.type)
        e.setAttributeNS(NO_NS, 'id', node.id)
        node.name and e.appendChild(text_node(doc, 'label', node.name))
        # construction of calendar (heritage in projman whereas none in pygantt)
        cal_ref = node.calendar
        default_worktime = 0.0
        n = node
        # visit tree seeking for childish calendars
        while cal_ref not in (None, '', 'c_'):
            c = doc.createElementNS(NO_NS, 'use-timetable')
            c.setAttributeNS(NO_NS, 'idref', cal_ref)
            e.appendChild(c)
            c_init = node.get_node_by_id(cal_ref)
            # use first non-zero value as number of hour per day
            default_worktime = default_worktime or c_init.get_default_wt_in_hours()
            if c_init.parent.TYPE == 'calendar':
                c_parent = c_init.parent
                cal_ref = c_parent.id
            else:
                cal_ref = None
        # write unitcost attribute
        daily_cost = node.hourly_rate[0]*default_worktime
        if daily_cost:
            e.setAttributeNS(NO_NS, 'unitcost', str(daily_cost))
        # conclude
        self.all_resources.append(e)
        return None
        
    def visit_resourcesset(self, node):
        """ visit a resourcesset node """
        pass

    def visit_calendar(self, node, root=None):
        """ visit a calendar node """
        doc = self._doc
        tt = doc.createElementNS(NO_NS, 'timetable')
        calendar = node
        tt.setAttributeNS(NO_NS, 'id', calendar.id)
        calendar.name and tt.appendChild(text_node(doc, 'label', calendar.name))
        if calendar.timeperiods:
            for timeperiod in calendar.timeperiods:
                if not calendar.is_a_working_type(timeperiod[2]):
                    t_off = doc.createElementNS(NO_NS, 'timeoff')
                    t_off.setAttributeNS(NO_NS, 'from', timeperiod[0].date)
                    t_off.setAttributeNS(NO_NS, 'to', timeperiod[1].date)
                    tt.appendChild(t_off)
        if calendar.weekday:
            for weekday in calendar.weekday:
                if not calendar.is_a_working_type(calendar.weekday[weekday]):
                    d_off = doc.createElementNS(NO_NS, 'dayoff')
                    d_off.setAttributeNS(NO_NS, 'type', 'weekday')
                    d_off.appendChild(doc.createTextNode(weekday))
                    tt.appendChild(d_off)
        if calendar.national_days:
            for national_d in calendar.national_days:
                d_off = doc.createElementNS(NO_NS, 'dayoff')
                d_off.setAttributeNS(NO_NS, 'type', 'holiday')
                d_off.appendChild(doc.createTextNode(national_d))
                tt.appendChild(d_off)
        self.all_calendars.append(tt)
        return None
                    
    def visit_project(self, node):
        """ visit a project node """
        doc = self._doc
        if not node.parent:
            p = doc.documentElement
        else:
            p = doc.createElementNS(NO_NS, 'project')
        return self.visit_task(node, p)
        
    
    def visit_milestone(self, node, e=None):
        """ visit a milestone node """
        doc = self._doc
        if e is None:
            e = doc.createElementNS(NO_NS, 'task')
        e.setAttributeNS(NO_NS, 'id', node.id)
        # label
        if node.TYPE == 'milestone':
            node.title and e.appendChild(text_node(doc, 'label', node.title))
        # date constraints
        for type, date in node.date_constraints.items():
            if date is not None:
                e.appendChild(constraint_as_dom(doc, type, date.date))
        for type in node.task_constraints:
            for id in node.task_constraints[type]:
                e.appendChild(constraint_as_empty_dom(doc, type, id))
        if self.all_tasks:
            if node.parent.id in self.all_tasks:
                self.all_tasks[node.parent.id].appendChild(e)
        self.all_tasks[node.id] = e
        if node.TYPE == 'project':
            return e
        else:
            return None
    
    def visit_task(self, node, e=None):
        """ visit a task node """
        doc = self._doc
        if e is None:
            e = doc.createElementNS(NO_NS, 'task')
        e.appendChild(text_node(doc, 'label', node.title))
        for res_type, id_res, usage in node.resource_constraints:
            use_r = doc.createElementNS(NO_NS, 'use-resource')
            use_r.setAttributeNS(NO_NS, 'idref', id_res)
            e.appendChild(use_r)
        if node.priority:
            e.appendChild(text_node(doc, 'priority', str(node.priority)))
        node.duration and e.appendChild(text_node(doc, 'duration', str(node.duration)))
        node.progress and e.appendChild(text_node(doc, 'progress', str(node.progress)+'%'))
        return self.visit_milestone(node, e)
        

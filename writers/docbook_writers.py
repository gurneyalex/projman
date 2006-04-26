# -*- coding: ISO-8859-1 -*-
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
""" Defines:
* AbstractWriter, abstract base class to write docbook files listing tasks
* DefaultWriter, simplest implementation wriring names & description
"""

__revision__ = "$Id: docbook_writers.py,v 1.19 2006-02-09 18:34:59 nico Exp $"

import sys
from xml.dom.ext import PrettyPrint, Print
from xml.dom.minidom import DOMImplementation

from logilab.common.compat import set

from projman import format_monetary

EXT_DATE_FORMAT = u'%Y-%m-%d'
FULL_DATE_FORMAT = u'%d/%m/%Y'
NO_NS = None

# dom utilities ################################################################
IMPLEMENTATION = DOMImplementation()

def document(root=None):
    """return a DOM document node"""
    return IMPLEMENTATION.createDocument("http://www.logilab.org/2004/Documentor", root, None)

# Writer Interface  #######################################################
class AbstractWriter:   
    """
    Abstract class to write docbook files listing tasks.
    """

    # FIXME: rename self.projman to self.project
    def __init__(self, projman):
        self._doc =  document("dr:root")
        self.projman = projman
        self.tree = None

    def open_tree(self, root):
        """
        formats & writes begining of doc according to docbook format.
        """
        raise NotImplementedError("method 'open_tree' must be overridden")

    def close_tree(self):
        """
        formats & writes end of doc according to docbook format.
        """
        raise NotImplementedError("method 'close_tree' must be overridden")

    def build_tree(self):
        """
        create a DOM node corresponding to a task.
        """
        raise NotImplementedError("method 'build_tree' must be overridden")
    
    # xml exportation methods ###################################################

    def as_xml_dom(self):
        """
        formats & writes generic info: head & tail.
        Calls 'visit' to display specific information.
        """
        if self._doc is None:
            raise Exception("internal error: document must be created before call to visit")
        root = self._doc.documentElement
        self.tree = [root]
        self.open_tree(root)
        self.build_tree()
        self.close_tree()
        return self._doc

    def as_xml_stream(self, pretty=1, stream=None):
        """ 
        return the tasks tree as a XML stream
        if stream is not None, write into the given stream
        """
        dom = self.as_xml_dom()
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

    def as_xml_string(self, pretty=True):
        """ 
        return the tasks tree as a XML string
        """
        return self.as_xml_stream(pretty=pretty).read()


# Abstract Writer  #######################################################

TOTAL_COST = u"Le coût total du projet se chiffre à "\
             "%s euros HT, soit %s euros TTC."

TOTAL_DATE = u"L'ensemble du projet se déroule entre le %s et le %s."

TOTAL_DURATION = u"La charge totale du projet se chiffre à %s."

TOTAL_DURATION_UNIT = u"1 jour.homme"
TOTAL_DURATION_UNITS_ROUND = u"%i jours.homme"
TOTAL_DURATION_UNITS = u"%.1f jours.homme"

def get_daily_labor(number):
    """return a string with unit jour(s).homme"""
    if number == 1.: # float not int...
        return TOTAL_DURATION_UNIT
    elif int(number) == number:
        return TOTAL_DURATION_UNITS_ROUND % number
    else:
        return TOTAL_DURATION_UNITS % number

TVA = 19.6

class AbstractTaskWriter(AbstractWriter):   
    """
    Implements default behaviour for all Task Writers:
    global calculation and common display.
    """
    def __init__(self, projman, options):
        AbstractWriter.__init__(self, projman)
        self.options = options
        self.project_cost = 0.0
        self.project_duration = 0.0
        self.used_resources = set()
        self.tree_root = None
        self.project = None
        self.lang = 'fr'
        
    def open_tree(self, root):
        """formats & writes begining of doc according to docbook format.
        """
        self.root = root
        self.project = self.projman.root_task
        object_node = self.object_node(self.project.id)
        self.root.appendChild(object_node)
        self.tree.append(object_node)
        self.tree_root = object_node

    def close_tree(self):
        """formats & writes end of doc according to docbook format.
        """
        # display rates       
        if self.options.is_displaying_rates():
            self.root.appendChild(self.rate_node())
        # display total costs
        if self.options.is_displaying_cost():
            self.root.appendChild(self.cost_node())
        # display total duration
        if self.options.is_displaying_duration():
            self.root.appendChild(self.duration_node())

    def build_tree(self):
        """buid a node for each task."""
        for task in self.project.children:
            self._build_task_node(task)
            
    def _build_task_node(self, task, level=0):
        """
        make global calculation: cost, duration, ressources' rate.
        """
        try:
            task_cost = self.projman.get_task_total_cost(task.id)
        except KeyError:
            task_cost = 0
        self.project_cost += task_cost
        # compute global duration
        self.project_duration += task.duration
        # set used_resources for legend
        grouped = self.projman.costs.groupby('task', 'resource')
        # grouped[task.id] is a dictionnary (res_id/rows)
        self.used_resources |= set(grouped.get(task.id, []))

    # formating methods  ########################################################
    def object_node(self, task_id): 	 
        """create a DOM node <section> with a attribute id"""
        assert type(task_id) is unicode
        node = self._doc.createElementNS(NO_NS, 'dr:object')
        node.setAttributeNS(NO_NS, 'id', task_id)
        node.setAttributeNS(NO_NS, 'lang', self.lang) # FIXME what if english?
        return node 	 

    def section_node(self, task_id=None): 	 
        """create a DOM node <section> with a attribute id""" 	 
        node = self._doc.createElementNS(NO_NS, 'section')
        if task_id:
            assert type(task_id) is unicode
            node.setAttributeNS(NO_NS, 'id', task_id)
        return node 	 

    def title_node(self, title):
        """create a DOM node <title> title </title> node"""
        assert type(title) is unicode
        node = self._doc.createElementNS(NO_NS, 'title')
        node.appendChild(self._doc.createTextNode(title))
        return node

    def para_node(self, text):
        """create a DOM node <para> text </para> node"""
        assert type(text) is unicode
        node = self._doc.createElementNS(NO_NS, 'para')
        node.appendChild(self._doc.createTextNode(text))
        return node

    def formalpara_node(self):
        """ create a DOM node <formalpara>"""
        node = self._doc.createElementNS(NO_NS, 'formalpara')
        return node

    def rate_node(self):
        """create a section with rates per resource."""
        # display rates
        object_rate = self.object_node(u"rates")
        section_rate = self.section_node(u"rate_section")
        object_rate.appendChild(section_rate)
        resources = [self.projman.get_resource(r_id) for r_id \
                     in self.used_resources]
        section_rate.appendChild(self.title_node(u"Tarifs journaliers"))
        section_rate.appendChild(self.para_node(u"Coût pour une journée type de travail:"))
        section_rate.appendChild( self.legend_node(resources))
        return object_rate

    def legend_node(self, resources):
        """ create a DOM node <itemizedlist> containing the legend of table"""
        list_items = self._doc.createElementNS(NO_NS, 'itemizedlist')
        for resource in resources:
            item = self._doc.createElementNS(NO_NS, 'listitem')
            para = self._doc.createElementNS(NO_NS, 'para')
            r_calendar = resource.get_node_by_id(resource.calendar)
            nb_hours_per_day = float(r_calendar.get_default_worktime() / 3600)
            cost_per_day = resource.hourly_rate[0] * nb_hours_per_day
            r_info = resource.id+' : '+resource.name+' ('+\
                     format_monetary(cost_per_day)+' '\
                     +resource.hourly_rate[1]+')'
            para.appendChild(self._doc.createTextNode(r_info))
            item.appendChild(para)
            list_items.appendChild(item)
        return list_items

    def cost_node(self):
        """create a section with total cost."""
        # display project cost
        object_cost = self.object_node(u"total-cost")
        section_cost = self.section_node(u"cost_section")
        object_cost.appendChild(section_cost)
        section_cost.appendChild(self.title_node(u"Coût total"))
        section_cost.appendChild(self.para_node(
            TOTAL_COST % (format_monetary(self.project_cost),
                          format_monetary(self.project_cost * (1+TVA/100)))))
        return object_cost

    def duration_node(self):
        """create a section with total duration."""
        # display project duration
        object_duration = self.object_node(u"total-duration")
        section_duration = self.section_node(u"duration_section")
        object_duration.appendChild(section_duration)
        section_duration.appendChild(self.title_node(
            u"Durée totale"))
        date_begin, date_end = self.projman.get_task_date_range(self.project)
        section_duration.appendChild(self.para_node(
            TOTAL_DATE % (date_begin.strftime(FULL_DATE_FORMAT),
                          date_end.strftime(FULL_DATE_FORMAT))))
        section_duration.appendChild(self.para_node(
            TOTAL_DURATION %  get_daily_labor(self.project.maximum_duration())))
        return object_duration

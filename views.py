# -*- coding: utf-8 -*-
#
# Copyright (c) 2006 LOGILAB S.A. (Paris, FRANCE).
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
"""provide view classes used to generate Documentor/Docbook views of the project
"""

from projman import format_monetary
from projman.lib._exceptions import ViewException
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET
    
# dom utilities ################################################################

DR_NS = "{http://www.logilab.org/2004/Documentor}"
ET._namespace_map[DR_NS[1:-1]] = "dr"

def document(root=None):
    """return a DOM document node"""
    root = ET.Element(DR_NS + (root or "root") )
    return ET.ElementTree(root)

class DocbookHelper:
    """a helper class to generate docboock"""

    def __init__(self, lang='fr'):
        self.lang = lang

    def object_node(self, parent, task_id):
        """create a DOM node <section> with a attribute id"""
        assert isinstance(task_id, basestring)
        node = ET.SubElement( parent, DR_NS + "object", id=task_id, lang=self.lang )
        return node

    def table_layout_node(self, parent, nbcols, align='left', colsep=1, rowsep=1,
                          colspecs=None):
        layout = ET.SubElement( parent, "tgroup", cols=str(nbcols),
                                align=align, colsep=str(colsep),
                                rowsep=str(rowsep) )
        if colspecs:
            for i, colspec in enumerate(colspecs):
                ET.SubElement( layout, "colspec", colname="c%s"%i, colwidth=colspec )
        return layout

    def table_cell_node(self, parent, align='', value=u''):
        """ create a DOM node <entry> """
        entry = ET.SubElement(parent, 'entry')
        if align and value:
            entry.set('align', align)
            entry.text = value

    def section(self, parent, title, id=None):
        section = ET.SubElement(parent, "section")
        if id:
            section.set("id",id)
        assert isinstance(title,unicode)
        ET.SubElement(section,"title").text = title
        return section

    def para(self, parent, text):
        assert isinstance(text, unicode)
        ET.SubElement(parent, "para").text = text

    def formalpara(self, parent, title, id=None):
        para = ET.SubElement(parent,"formalpara")
        if id:
            para.set("id",id)
        assert isinstance(title, unicode)
        ET.SubElement(para,"title").text = title
        return para

# other utilities and abstract classes ########################################

# FIXME handle english (lang='en')

TVA = 19.6
EXT_DATE_FORMAT = u'%Y-%m-%d'
FULL_DATE_FORMAT = u'%d/%m/%Y'
DATE_NOT_SPECIFIED = "non spécifié"
TOTAL_DATE = u"L'ensemble du projet se déroule entre le %s et le %s."
TOTAL_DURATION = u"La charge totale se chiffre à %s."
TOTAL_DURATION_UNIT = u"%.1f jour.homme"
TOTAL_DURATION_UNITS = u"%.1f jours.homme"

def get_daily_labor(number):
    """return a string with unit jour(s).homme"""
    if number <= 1.:
        return TOTAL_DURATION_UNIT % number
    else:
        return TOTAL_DURATION_UNITS % number

class CostData:
    """handle global calculation: cost, duration, ressources' rate
    """

    def __init__(self, projman):
        self.projman = projman
        self.project_cost = 0.0
        self.project_duration = 0.0
        self._used_resources = set()
        self.compute(projman.root_task)

    def compute(self, project):
        for task in project.children:
            self._compute(task)

    def _compute(self, task, level=0):
        try:
            task_cost = self.projman.get_task_total_cost(task.id, task.duration)
        except KeyError:
            task_cost = 0
        self.project_cost += task_cost
        # compute global duration
        self.project_duration += task.duration
        # set used_resources for legend
        grouped = self.projman.costs.groupby('task', 'resource')
        # grouped[task.id] is a dictionnary (res_id/rows)
        self._used_resources |= set(grouped.get(task.id, []))
        for each in task.children:
            self._compute(each, level+1)

    def used_resources(self):
        return [self.projman.get_resource(rid) for rid in self._used_resources if rid]


class XMLView:
    name = None

    def __init__(self, config):
        self.config = config
        self.max_level =  self.config.level

    def unique_id(self, nid):
        # use getattr since not all commands support task-root option
        vtask_root = self.config.task_root
        if vtask_root:
            return '%s-%s' % (vtask_root, nid)
        return nid

    def generate(self, xmldoc, projman):
        """return a dr:object node for the rate section view"""
        self._init(projman, xmldoc)
        root = xmldoc.getroot()
        obj = self.dbh.object_node(root, self.unique_id(self.name))
        self.add_content_nodes(obj)
        return obj
    
    def _init(self, projman, xmldoc=None, dbh=None):
        """initialize view members necessary for content generation"""
        self.projman = projman
        if self.config.task_root == None:
            self.config.task_root = self.projman.root_task.id
        self.dbh = dbh or DocbookHelper()
        try:
            self.cdata = projman.__view_cost_data
        except AttributeError:
            self.cdata = projman.__view_cost_data = CostData(projman)

    def subview_content_nodes(self, parent, viewklass):
        """instantiate the given view class and return its content nodes"""
        view = viewklass(self.config)
        view._init(self.projman, dbh=self.dbh)
        view.add_content_nodes( parent )

    def add_content_nodes(self, parent):
        raise NotImplementedError

# actual views ################################################################

class RatesSectionView(XMLView):
    name = 'rates-section'
    
    def add_content_nodes(self, parent):
        section = self.dbh.section(parent, u"Tarifs journaliers", id=self.unique_id('rate-section'))
        self.dbh.para(section, u"Coût pour une journée type de travail:")
        resources = self.cdata.used_resources()
        self.add_resources_rates(section, resources)

    def add_resources_rates(self, parent, resources):
        """ create a DOM node <itemizedlist> containing the legend of table"""
        list_items = ET.SubElement(parent, "itemizedlist")
        for resource in resources:
            nb_hours_per_day = resource.get_default_wt_in_hours()
            cost_per_day = resource.hourly_rate[0] * nb_hours_per_day
            r_info = '%s : %s (%s %s)' % (resource.id, resource.name,
                                          format_monetary(cost_per_day),
                                          resource.hourly_rate[1])
            item = ET.SubElement(list_items, "listitem")
            self.dbh.para( item, r_info )


class DurationSectionView(XMLView):
    name = 'duration-section'

    def add_content_nodes(self, parent):
        section = self.dbh.section(parent, u"Durée totale", id=self.unique_id(u"duration-section"))
        self.subview_content_nodes(section, DateParaView)
        self.subview_content_nodes(section, DurationParaView)

class DateParaView(XMLView):
    name = 'dates-para'

    def add_content_nodes(self, parent):
        begin, end = self.projman.get_task_date_range(self.projman.root_task)
        text = TOTAL_DATE % (begin.strftime(FULL_DATE_FORMAT),
                             end.strftime(FULL_DATE_FORMAT))
        self.dbh.para(parent, text)
        ET.SubElement(parent,"para").text = text

class DurationParaView(XMLView):
    name = 'duration-para'

    def add_content_nodes(self, parent):
        text = TOTAL_DURATION % get_daily_labor(self.projman.root_task.maximum_duration())
        ET.SubElement(parent,"para").text = text

class CostTableView(XMLView):
    name = 'cost-table'
    ENTETE = u"Tableau récapitulatif des coûts."

    def add_content_nodes(self, parent):
        """return a dr:object node for the cost table view"""
        self.projman.update_caches()
        table = ET.SubElement(parent,"table")
        ET.SubElement(table, "title").text = self.ENTETE
        # fill column information for table
          # find resources
        root = self.projman.get_task(self.config.task_root)
        resources = self.projman.get_resources()
        set_res = []
        for res in resources:
            set_res.append( self.projman.get_resource(res))
        root_resources = root.get_linked_resources(set_res)
        len_ = len(root_resources)
        specs = [u'3*']
        for i in range(len_):
            specs.append(u'1*')
        specs.append(u'1*')
        self.set_res = []
        for i in range(len_):
            res = root_resources.pop()
            self.set_res.append(res)
          # create table 
        layout = self.dbh.table_layout_node(table, len_+2, colspecs=specs)
        head = self.table_head(layout, len_+2)
        # table body
        tbody = ET.SubElement(layout, "tbody")
        for child in self.projman.root_task.children:
            if child.TYPE == 'task' and child.level:
                self._build_task_node(tbody, child, child.level+1)

    def table_head(self, parent, len_):
        """ create a DOM node <thead> """
        thead = ET.SubElement(parent, 'thead')
        row =  ET.SubElement(thead,'row')
        self.dbh.table_cell_node(row, 'left', u'Tâches')
        for i in range(len_ - 2):
            res = self.set_res[i]
            self.dbh.table_cell_node(row, 'center', u'%s' %res)
        self.dbh.table_cell_node(row, 'right', u'Coût (euros)')
        return thead

    def _build_task_node(self, tbody, task, level=1):
        """format a task in as a row in the table"""
        if not task.children:
            self.row_element(tbody, task, level)
        elif task.children and level <= self.max_level:
            self.empty_row_element(tbody, task, level)
            for child in task.children:
                self._build_task_node(tbody, child, level+1)
        else:
            self.synthesis_row_element(tbody, task, level)

    def row_element(self, tbody, task, level=1):
        """ create a DOM element <row> with values in task node"""
        row = ET.SubElement(tbody, 'row')
        indent = u'\xA0 '*(level-1)
        costs, durations = self.projman.get_task_costs(task.id, task.duration)
        # task title
        self.dbh.table_cell_node(row, 'left', indent+task.title)
        # task duration
        for res in self.set_res:
            if task.children:
                self.dbh.table_cell_node(row)
            else:
                if res in durations:
                    duration = durations[res]
                    self.dbh.table_cell_node(row, 'center', "%s" %duration)
                else:
                    self.dbh.table_cell_node(row) 
        # task cost by resources
        if task.children:
            self.dbh.table_cell_node(row)
        else:
            cost = 0
            for res in costs:
                cost += costs[res]
            self.dbh.table_cell_node(row,'rigth', u'%s' %cost)
        return row

    def empty_row_element(self, tbody, task, level=0):
        """ create a DOM element <row> with values in task node"""
        row =  ET.SubElement(tbody, 'row')
        indent = u'\xA0 '*(level-1)
        # task title
        self.dbh.table_cell_node(row, 'left', indent+task.title)
        for res in self.set_res:
            self.dbh.table_cell_node(row)
        self.dbh.table_cell_node(row)
        return row

    def synthesis_row_element(self, tbody, task, level):
        durations_ = {}
        # task title
        row = ET.SubElement(tbody, 'row')
        indent = u'\xA0 '*(level-1)
        self.dbh.table_cell_node(row, 'left', indent+task.title)
        for res in self.set_res:
            durations_.setdefault(res,0)
        durations_ = {}
        costs_ = 0
        for child in task.children:
            if child.children:
                raise ViewException('task %s can not have children to generate views' %child.id)
            costs, durations = self.projman.get_task_costs(child.id, child.duration)
            for res in durations:
                if not res in durations_:
                    durations_.setdefault(res, 0)
                durations_[res] += durations[res]
                costs_ += costs[res]
        for res in self.set_res:
            if res in durations_:
                self.dbh.table_cell_node(row, 'center', "%s" %durations_[res])
            else:
                self.dbh.table_cell_node(row)
        self.dbh.table_cell_node(row,'rigth', u'%s' %costs_)
        
class CostParaView(XMLView):
    name = 'cost-para'
    TOTAL_COST = u"Le coût total se chiffre à %s euros HT, soit %s euros TTC en appliquant les taux actuellement en vigueur."

    def add_content_nodes(self, parent):
        """return a dr:object node for the cost paragraph view"""
        cost = self.cdata.project_cost
        text = self.TOTAL_COST % (format_monetary(cost),
                                  format_monetary(cost * (1+TVA/100)))
        ET.SubElement(parent, 'para').text = text

class TasksListSectionView(XMLView):
    name = 'tasks-list-section'

    def add_content_nodes(self, parent):
        """return a dr:object node for the tasks list section view"""
        self.projman.update_caches()
        for child in self.projman.root_task.children:
            self._build_task_node(parent, child)

    def _build_task_node(self, parent, task):
        section = self.dbh.section(parent, task.title, id=task.id)
        if task.children:
            self._build_tables(task,section)
            self.add_para_total_load(section, task)
            if  self.config.display_dates:
                self.add_dates(section, task)
            # print children
            for child in task.children:
                self._build_task_node(section, child)
        else:
            # task is a real task (leaf without any sub task)
            # fill description
            if task.description != "":
                # create xml-like string
                # encode it and create XML tree from it
                # FIXME !!!
                assert isinstance(task.description, unicode), task.description
                desc = "<?xml version='1.0' encoding='UTF-8'?><para>%s</para>" \
                       % task.description.encode('utf8')
                try:
                    description_doc = ET.fromstring(desc)
                except Exception, exc:
                    print desc
                    raise
                section.append( description_doc )
            
            # add resources' info
            if task.TYPE == 'task' :
                self.resource_node(section, task)

            # add date constraints
            if self.config.display_dates:
                self.add_dates(section, task)
        return section

    def add_dates(self, parent, task):
        """print begin and end of  task"""
        para = self.dbh.formalpara(parent,u'Dates')
        para = ET.SubElement(parent,"para")
        list_ = ET.SubElement(para, "itemizedlist")
        debut, fin = self.projman.get_task_date_range(task)
        item = ET.SubElement(list_,'listitem')
        self.dbh.para(item, u"Date de début : %s" %debut.Format(EXT_DATE_FORMAT))
        item = ET.SubElement(list_,'listitem')
        self.dbh.para(item, u"Date de fin :   %s" %fin.Format(EXT_DATE_FORMAT))
            
    def add_para_total_load(self, parent, task):
         """print total load (load for each resources)"""
         para = self.dbh.formalpara(parent,u'Charge totale')
         para = ET.SubElement(parent,"para")
         list_ = ET.SubElement(para, "itemizedlist")
         tot_load = []
         # from Table project.cost, find load for each resources
         # for this task (only load of his child)
         for cost in self.projman.costs:
             if self.projman.get_task(cost[0]) in task.children:
                 tot_load.append( (cost[1], cost[2], cost[0]))
         # probleme: Lorsque la tache a des subtaches qui ont des subtaches ...,
         # on ne connait pas tourtes les resources qui interviennent
             for child in task.children:
                 if self.projman.get_task(cost[0]) in child.children:
                     tot_load.append( (cost[1], cost[2], cost[0]))
         while tot_load:
             # find a resource working on task (children of task)
             res_id = tot_load[0][0]
             load = tot_load[0][1]
             child_id = tot_load[0][2]
             tot_load.remove(tot_load[0])
             length = len(tot_load)
             list_to_remove = []
             # find all works of this resource
             for n in range(length):
                 couple = tot_load[n]
                 if couple[0] == res_id:
                     load += couple[1]
                     list_to_remove.append(couple)
             # get skill of the resource
             if self.projman.resource_role_set.width() > 1: #use new definition of resources
                 resource = self.projman.get_resource(res_id)
                 child  = self.projman.get_task(child_id)
                 res_type = child.task_type
                 res_role = self.projman.resource_role_set.get_resource_role(res_type)
                 role = res_role.name
             else:  # use old definition
                 res = self.projman.get_resource(res_id)
                 role = res.type
             # remove resource from the list of tasks
             for elt in list_to_remove:
                 tot_load.remove(elt)
             #print list of load
             item = ET.SubElement(list_,'listitem')
             self.dbh.para(item, u"%s : %s jour.hommes" %(role, load))
             
            
    def resource_node(self, parent, task):
        """ create a DOM node
        <formalpara>
          <title>Charge et répartition</title>

          <para>
            <itemizedlist>
              <listitem><para>role (res_id) : duration jours.homme</para></listitem>
              <listitem><para>   ...    </para></listitem>
            </itemizedlist>
          </para>
        </formalpara>
        """
        # use new resources definition:
        para = self.dbh.formalpara(parent,u'Charge totale')
        para = ET.SubElement(parent,"para")
        list_ = ET.SubElement(para, "itemizedlist")
        for cost in self.projman.costs:
            if cost[0] == task.id:
                res_id = cost[1]
                resource = self.projman.get_resource(res_id)
                if task.task_type:  # use new resources definition
                    res_role =  self.projman.resource_role_set.get_resource_role(task.task_type)
                    role = res_role.name
                else:  # use old definition of resource roles
                    role = resource.type
                duration = cost[2]
                item = ET.SubElement(list_,'listitem')
                self.dbh.para(item, u"%s (%s) : %s " %(role, resource.name, duration))
        return para

    def _build_tables(self, task, section):
        """ build tables of principal information of the task
        one for duration of subtasks and date of end of subtasks
        and another to describe deliverables"""

        # table of subtasks
        table = ET.SubElement(section,"informaltable")
        layout = self.dbh.table_layout_node(table, 2, colspecs=('2*', '1*'))
        self.table_head_task(layout)
          # table body
        tbody = ET.SubElement(layout, "tbody")
          # ligns of table
        for child in task.children:
            self.row_element(child, tbody)
        # table of liverables
        table = ET.SubElement(section,"informaltable")
        if self.config.display_dates:
            layout = self.dbh.table_layout_node(table, 2, colspecs=('2*', '1*'))
        else:
            layout = self.dbh.table_layout_node(table, 1, colspecs=("1*"))
        self.table_head_milestone(layout)
        # table body
        tbody = ET.SubElement(layout, "tbody")
        row = ET.SubElement(tbody, 'row')
        self.dbh.table_cell_node(row, 'left', u'Version 1')
        if self.config.display_dates:
            # find end of tasks
            _, end = self.projman.get_task_date_range(task)
            self.dbh.table_cell_node(row, 'left', u'%s' %end.Format(EXT_DATE_FORMAT))
        
    def table_head_task(self, parent):
        """ create a DOM node <thead> for the task table """
        thead = ET.SubElement(parent, 'thead')
        row = ET.SubElement(thead,'row')
        self.dbh.table_cell_node(row, 'left', u'Tâches contenues')
        self.dbh.table_cell_node(row, 'left', u'Charge')
        return thead

    def table_head_milestone(self, parent):
        """ create a DOM node <thead> for the milestone table """
        thead = ET.SubElement(parent, 'thead')
        row = ET.SubElement(thead,'row')
        self.dbh.table_cell_node(row, 'left', u'Livrables produits')
        if  self.config.display_dates:
            self.dbh.table_cell_node(row, 'left', u'Date de livraison')
        return thead

    def row_element(self, task, tbody):
        """ create a DOM element <row> with values in task node"""
        if task.children:
            row = ET.SubElement(tbody, 'row')
            # task title
            self.dbh.table_cell_node(row, 'left', task.title)
            # task duration and role of resources
            duration = 0
            resources = set()
            for child in task.children:
                duration += child.duration
                if child.task_type: #use new project description
                    res_type = set(child.task_type)
                    # get role title
                    res_role = self.projman.resource_role_set.get_resource_role(res_type)
                    role = res_role.name
                else: # use old project description
                    res_ = child.get_resources()
                    res = res_.pop()
                    res = self.projman.get_resource(res)
                    role = res.type
                    resources.add(role)
            string = u'%s' %resources.pop()
            for role in resources:
                string += ', %s' %role
            self.dbh.table_cell_node(row, 'left',string +u' : %s j.h' %duration)
        else:
            row = ET.SubElement(tbody, 'row')
            # task title
            self.dbh.table_cell_node(row, 'left', task.title)
            # task duration and role of resources
            duration = task.duration and unicode(task.duration) or u''
            if task.task_type: #use new project description
                res_type = task.task_type
                # get role title
                res_role = self.projman.resource_role_set.get_resource_role(res_type)
                role = res_role.name
            else: # use old project description
                resources = task.get_resources()
                res_id = resources.pop() # en pratique, on n'associe jamais
                                         # des resources avec des competences differentes
                                         # sur une meme tache ( d'ou pop)
                res = self.projman.get_resource(res_id)
                role = res.type
            self.dbh.table_cell_node(row, 'left', u'%s : %s j.h' %(role, duration))
            # compute end of the task (used in second table)
            return row
    
class DurationTableView(XMLView):
    name = 'duration-table'
    ENTETE = u"Tableau récapitulatif des dates."

    def add_content_nodes(self, parent):
        """return a dr:object node for the cost table view"""
        self.projman.update_caches()
        table = ET.SubElement(parent,"table")
        ET.SubElement(table,"title").text = self.ENTETE
        # fill column information for table
        layout = self.dbh.table_layout_node(table, 3, colspecs=('3*', '1*', '1*'))
        self.table_head(layout)
        # table body
        tbody = ET.SubElement(layout, "tbody")
        for child in self.projman.root_task.children:
            if child.TYPE == 'task':
                self._build_task_node(tbody, child, child.level)

    def synthesis_row_element(self, parent, task, level):
        begin, end = self.projman.get_task_date_range(task)
        row =  ET.SubElement(parent, 'row')
        # indentation
        indent = u'\xA0 '*(level-1)
        # task title
        self.dbh.table_cell_node(row, 'left', indent + u'Synthèse' + task.title)
        # task begin & end
        date_begin, date_end = self.projman.get_task_date_range(task)
        self.dbh.table_cell_node(row, 'center', date_begin.date)
        self.dbh.table_cell_node(row, 'center', date_end.date)
        return row

    def _build_task_node(self, tbody, task, level=0):
        """format a task in as a row in the table"""
        if task.children and level < self.max_level:
            self.row_empty_element(tbody, task, level)
            for child in task.children:
                self._build_task_node(tbody, child, level+1)
            self.synthesis_row_element(tbody, task, level+1)
        else:
            self.row_element(tbody, task, level)
            
    def table_head(self, table):
        """ create a DOM node <thead> """ 
        thead = ET.SubElement(table, "thead")
        row = ET.SubElement(thead,"row")
        self.dbh.table_cell_node(row, 'leaf', u'Tâches')
        self.dbh.table_cell_node(row, 'center', u'Date de début')
        self.dbh.table_cell_node(row, 'center', u'Date de fin')
        return thead

    def row_element(self, tbody, task, level=0):
        """ create a DOM element <row> with values in task node"""
        row = ET.SubElement(tbody, 'row')
        # indentation
        indent = u'\xA0 '*(level-1)
        # task title
        self.dbh.table_cell_node(row, 'left', indent+task.title)
        # task begin & end
        date_begin, date_end = self.projman.get_task_date_range(task)
        self.dbh.table_cell_node(row, 'center', date_begin.date, 0)
        
        self.dbh.table_cell_node(row, 'center', date_end.date, 0)
        return row

    def row_empty_element(self, tbody, task, level=0):
        """ create a DOM element <row> with values in task node"""
        row = ET.SubElement(tbody, 'row')
        # indentation
        indent = u'\xA0 '*(level-1)
        # task title
        self.dbh.table_cell_node(row, 'left', indent+task.title)
        # task begin & end
        self.dbh.table_cell_node(row)
        self.dbh.table_cell_node(row)
        return row

ALL_VIEWS = {}
for klass in (RatesSectionView,
              DurationTableView, DurationParaView, DurationSectionView,
              DateParaView,
              CostTableView, CostParaView,
              TasksListSectionView):
    ALL_VIEWS[klass.name] = klass
    

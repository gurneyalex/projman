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
from projman.lib.constants import HOURS_PER_DAY
from projman.lib._exceptions import ViewException
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET
    
# dom utilities ################################################################

DR_NS = "{http://www.logilab.org/2004/Documentor}"
LDG_NS = "{http://www.logilab.org/2005/DocGenerator}"
ET._namespace_map[DR_NS[1:-1]] = "dr"
ET._namespace_map[LDG_NS[1:-1]] = "ldg"

PUCE = u'\u203A '

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
        task_types = []
        hourly_cost = [] # used only in case of old resources type definition
        for task in self.projman.root_task.leaves():
            if task.task_type: #new resources role definition
                role = self.projman.resource_role_set.get_resource_role(task.task_type)
                if not role in task_types:
                    task_types.append(role)
        if not task_types: # old resource type definition
            for res in self.projman.get_resources():
                resource = self.projman.get_resource(res)
                if not resource.type in task_types:
                    task_types.append(resource.type)
                    hourly_cost.append(resource.hourly_rate[0])
        for i, role in enumerate(task_types):
            if isinstance(role, basestring):
                r_info = '%s : %s' %(role, format_monetary(hourly_cost[i] * HOURS_PER_DAY))
            else:
                r_info = '%s (%s) : %s' %(role.name, role.id, format_monetary(role.hourly_cost * HOURS_PER_DAY))     
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
          # find resources roles
        root = self.projman.get_task(self.config.task_root)
        resources = self.projman.get_resources()
        set_res = []
        for res in resources:
            set_res.append( self.projman.get_resource(res)) 
        root_resources = root.get_linked_resources(set_res)
        self.set_res = []
        for i in range(len(root_resources)):
            res = root_resources.pop()
            self.set_res.append(res)
        self.roles = []
        for task in self.projman.root_task.leaves():
            if task.task_type: #according to new definition of roles resources
                role_ = self.projman.resource_role_set.get_resource_role(task.task_type)
                if not role_ in self.roles:
                    self.roles.append(role_)
        if self.roles == []: # old definition of resources type
            for res in self.set_res:
                resource = self.projman.get_resource(res)
                if not resource.type in self.roles:
                    self.roles.append(resource.type)
        len_ = len(self.roles)
        specs = [u'3*']
        for i in range(len_):
            specs.append(u'1*')
        specs.append(u'1*')
        
        # create table 
        layout = self.dbh.table_layout_node(table, len_+2, colspecs=specs)
        head = self.table_head(layout, len_+2)
        # table body
        tbody = ET.SubElement(layout, "tbody")
        self.set_tbody(tbody)
        for child in self.projman.root_task.children:
            if child.TYPE == 'task' and child.level:
                self.color = 0
                self._build_task_node(tbody, child, child.level)

    def set_tbody(self, tbody):
        tbody.set(LDG_NS+"row-borders", 'false')
        tbody.set(LDG_NS+'row-backgrounds', "never")

    def set_row(self, row):
        row.set(LDG_NS+'border-top', "true")
        row.set(LDG_NS+'bold', "true")

    def table_head(self, parent, len_):
        """ create a DOM node <thead> """
        thead = ET.SubElement(parent, 'thead')
        row =  ET.SubElement(thead,'row')
        self.dbh.table_cell_node(row, 'left', u'Tâches')
        for i in range(len_ - 2):
            role = self.roles[i]
            if type(role) == str:
                self.dbh.table_cell_node(row, 'center', u'Charge "%s"' %role)
            else:
                self.dbh.table_cell_node(row, 'center', u'Charge "%s"' %role.id)
        self.dbh.table_cell_node(row, 'right', u'Coût (euros)')
        return thead

    def _build_task_node(self, tbody, task, level=1):
        """format a task in as a row in the table"""
        if not task.children:
            self.row_element(tbody, task, level)
        elif task.children and level <= self.max_level:
            self.empty_row_element(tbody, task, level)
            for child in task.children:
                if child.TYPE == 'milestone':
                    continue
                if task.level == 1:
                    self.color += 1
                self._build_task_node(tbody, child, level+1)
            self.synthesis_row_element(tbody, task, level)
        else:
            self.synthesis_row_element(tbody, task, level)

    def row_element(self, tbody, task, level=1):
        """ create a DOM element <row> with values in task node"""
        row = ET.SubElement(tbody, 'row')
        if self.color % 2:
            row.set(LDG_NS+'background', "true")
        indent = u'\xA0 '*(level-1)*2
        costs, durations = self.projman.get_task_costs(task.id, task.duration)
        # task title
        if level == 1:
            self.set_row(row)
            self.dbh.table_cell_node(row, 'left', indent+task.title)
        else:
            self.dbh.table_cell_node(row, 'left', indent+PUCE+task.title)
        # task duration
        for role in self.roles:
            if task.children:
                self.dbh.table_cell_node(row)
            else:
                duration = 0
                ### Bug: here we should group the resources that have the same
                ### role for this task into the same column... How do we know
                ### the role played by a resource into this task, well that's a
                ### problem, and solving this problem requires changing the
                ### heart of projman.
                for res in durations:
                    resource = self.projman.get_resource(res)
                    if not type(role) == str: # according to new resources definition
                        if role.id in resource.id_role:
                            duration = durations[res]                                
                            self.dbh.table_cell_node(row, 'center', "%s" %duration)
                    else: #old definition of resource type
                        if role == resource.type:
                            duration = durations[res]                                
                            self.dbh.table_cell_node(row, 'center', "%s" %duration)
                if duration == 0:
                    self.dbh.table_cell_node(row)
        # task cost by resources
        if task.children:
            self.dbh.table_cell_node(row)
        else:
            cost = 0
            for res in costs:
                cost += costs[res]
            self.dbh.table_cell_node(row,'right', u'%s' %format_monetary(cost))
        return row

    def empty_row_element(self, tbody, task, level=0):
        """ create a DOM element <row> with values in task node"""
        row =  ET.SubElement(tbody, 'row')
        if self.color % 2:
            row.set(LDG_NS+'background', "true")
        if level == 1:
            self.set_row(row)
        indent = u'\xA0 '*(level-1)*2
        # task title
        if level == 1:
            self.dbh.table_cell_node(row, 'left', indent+task.title)
        else:
            self.dbh.table_cell_node(row, 'left', indent+PUCE+task.title)
        for role in self.roles:
            self.dbh.table_cell_node(row)
        self.dbh.table_cell_node(row)
        return row

    def synthesis_row_element(self, tbody, task, level):
        durations_ = {}
        # task title
        row = ET.SubElement(tbody, 'row')
        if task.level <= self.max_level and task.children:
            row.set(LDG_NS+'italic', "true")
            string = u'Synthèse '
            if task.level == 1:
                 row.set(LDG_NS+'border-bottom', "true")
                 row.set(LDG_NS+'bold', "true")
        else:
            string = u''
        if  self.color % 2 and task.level > 1: 
            row.set(LDG_NS+'background', "true")
        indent = u'\xA0 '*(level-1)*2
        self.dbh.table_cell_node(row, 'left', indent+string+task.title)
        for res in self.set_res:
            durations_.setdefault(res,0)
        durations_ = {}
        costs_ = 0
        for child in task.children: # ?? leaves() should be better
            if child.children and child.level > self.max_level:
                raise ViewException('task %s must have no child to generate views' %child.id)
            costs, durations = self.projman.get_task_costs(child.id, child.duration)
            for children in child.children:
                costs_child, durations_child = self.projman.get_task_costs(children.id, children.duration)
                for res in durations_child:
                    if not res in durations_:
                        durations_.setdefault(res, 0)
                    durations_[res] += durations_child[res]
                    costs_ += costs_child[res]
            for res in durations:
                if not res in durations_:
                    durations_.setdefault(res, 0)
                durations_[res] += durations[res]
                costs_ += costs[res]
        for role in self.roles:
            duration = 0
            for res in durations_:
                resource = self.projman.get_resource(res)
                if not type(role) == str: # according to new resqoiurces definition
                    if role.id in resource.id_role:
                        duration = durations_[res]                                
                        self.dbh.table_cell_node(row, 'center', "%s" %duration)
                else: #old definition of resource type
                    if role == resource.type:
                        duration = durations_[res]                                
                        self.dbh.table_cell_node(row, 'center', "%s" %duration)
            if duration == 0:
                self.dbh.table_cell_node(row)
        self.dbh.table_cell_node(row,'right', u'%s' %format_monetary(costs_))
        
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
            if not child.TYPE == 'milestone':
                self._build_task_node(parent, child)

    def _build_task_node(self, parent, task):
        section = self.dbh.section(parent, task.title, id=task.id)
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
        if task.children:
            self._build_tables(task,section)
            self.add_para_total_load(section, task)
            if  self.config.display_dates:
                self.add_dates(section, task)
            # print children
            for child in task.children:
                if not  child.TYPE == 'milestone':
                    self._build_task_node(section, child)
        else:
            # task is a real task (leaf without any sub task)
            
            # add resources' info
            if task.TYPE == 'task' :
                self.resource_node(section, task)

            # add date constraints
            if self.config.display_dates:
                self.add_dates(section, task)
            if task.link:
                para = self.dbh.formalpara(section, u'Voir aussi')
                link = ET.SubElement(para, "ulink")
                link.set(u'url', '%s' %task.link)
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
        durations = {}
        costs = {}
        for leaf in task.leaves():
            if leaf.TYPE == 'milestone':
                continue
            costs_, durations_ = self.projman.get_task_costs(leaf.id, leaf.duration)
            for res in durations_:
                if not res in durations:
                    durations.setdefault(res, 0)
                    costs.setdefault(res, 0)
                durations[res] += durations_[res]
                costs[res] += costs_[res]
        for res in durations:
            resource = self.projman.get_resource(res)
            
            #if self.projman.resource_role_set.width() >1:  #use new definition of resources
                #for leaf in task.leaves(): # does not work
            #parcours des feuilles pour connaitre la liste des roles, le tps consomme
            #est donne par duration
            # on ne peut pas retrouver le role-type d'une tache a partir d'unr resource,
            # car elle peut avoir plusieurs roles. On suppose donc que les feuilles
            # auront le meme role-type
            role = None
            for leaf in task.leaves():
                if leaf.task_type or task.task_type:
                    if leaf.TYPE == 'milestone':
                        continue
                    role_ = self.projman.resource_role_set.get_resource_role(leaf.task_type)
                    role = role_.name
#            else:  # use old definition
            if not(role):
                resource = self.projman.get_resource(res)
                role = resource.type
            item = ET.SubElement(list_,'listitem')
            self.dbh.para(item, u"%s (%s) : %s jour.hommes" %(role, resource.name, durations[res]))
             
            
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
        _, duration = self.projman.get_task_costs(task.id, task.duration)
        duration_ = {}
        for res in duration:
                resource = self.projman.get_resource(res)
                if task.task_type:  # use new resources definition
                    res_role =  self.projman.resource_role_set.get_resource_role(task.task_type)
                    role = res_role.name
                else:  # use old definition of resource roles
                    role = resource.type
                item = ET.SubElement(list_,'listitem')
                self.dbh.para(item, u"%s (%s) : %s " %(role, resource.name, duration[res]))
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
            if not child.TYPE == 'milestone':
                self.row_element(child, tbody)
        # table of liverables :
        # find milestones
        milestones = []
        for child in task.children:
            if child.TYPE == 'milestone':
                milestones.append(child)
        if milestones:
            table = ET.SubElement(section,"informaltable")
            if self.config.display_dates:
                layout = self.dbh.table_layout_node(table, 2, colspecs=('2*', '1*'))
            else:
                layout = self.dbh.table_layout_node(table, 1, colspecs=('1*',))
            self.table_head_milestone(layout)
            # table body
            tbody = ET.SubElement(layout, "tbody")
        for mil_ in milestones:
            row = ET.SubElement(tbody, 'row')
            self.dbh.table_cell_node(row, 'left', u'%s' %mil_.title)
            if self.config.display_dates:
                # find end of tasks
                _, end = self.projman.get_task_date_range(mil_)
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
        self.dbh.table_cell_node(row, 'left', u'Jalons')
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
                if child.TYPE == 'milestone':
                    continue
                duration += child.duration
                if child.task_type: #use new project description
                    res_type = child.task_type
                    # get role title
                    res_role = self.projman.resource_role_set.get_resource_role(res_type)
                    role = res_role.name
                    resources.add(role)
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
    
class DurationTableView(CostTableView):
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
        # add tbody attributes
        self.set_tbody(tbody)        
        for child in self.projman.root_task.children:
            if child.TYPE == 'task':
                self.color = 0
                self._build_task_node(tbody, child, child.level)

    def synthesis_row_element(self, row, task, level):
        begin, end = self.projman.get_task_date_range(task)
        #row =  ET.SubElement(parent, 'row')
        # indentation
        indent = u'\xA0 '*(level-2)*2
        # task title
        self.dbh.table_cell_node(row, 'left', indent+u'Synthèse ' + task.title)
        # task begin & end
        date_begin, date_end = self.projman.get_task_date_range(task)
        self.dbh.table_cell_node(row, 'center', date_begin.date)
        self.dbh.table_cell_node(row, 'center', date_end.date)
        return row

    def _build_task_node(self, tbody, task, level=0):
        """format a task in as a row in the table"""
        row = ET.SubElement(tbody, 'row')
        if self.color % 2: 
            row.set(LDG_NS+'background', "true")
        if level == 1:
            self.set_row(row)
        if task.children and level < self.max_level:
            self.row_empty_element(row, task, level)
            for child in task.children:
                if child.TYPE == 'milestone':
                    continue
                if task.level == 1:
                    self.color += 1
                self._build_task_node(tbody, child, level+1)
            row = ET.SubElement(tbody, 'row')
            if self.color % 2 and level > 1:
                row.set(LDG_NS+'background', "true")
            row.set(LDG_NS+'italic', "true")
            if task.level == 1:
                row.set(LDG_NS+'border-bottom', "true")
                row.set(LDG_NS+'bold', "true")
            self.synthesis_row_element(row, task, level+1)
        else:
            #row.set(LDG_NS+'border-bottom', "true")            
            self.row_element(row, task, level)
            
    def table_head(self, table):
        """ create a DOM node <thead> """ 
        thead = ET.SubElement(table, "thead")
        row = ET.SubElement(thead,"row")
        self.dbh.table_cell_node(row, 'leaf', u'Tâches')
        self.dbh.table_cell_node(row, 'center', u'Date de début')
        self.dbh.table_cell_node(row, 'center', u'Date de fin')
        return thead

    def row_element(self, row, task, level=0):
        """ create a DOM element <row> with values in task node"""
        #row = ET.SubElement(tbody, 'row')
        # indentation
        indent = u'\xA0 '*(level-1)*2
        # task title
        if level == 1:
            self.dbh.table_cell_node(row, 'left', indent+task.title)
        else:
            self.dbh.table_cell_node(row, 'left', indent+PUCE+task.title)
        # task begin & end
        date_begin, date_end = self.projman.get_task_date_range(task)
        self.dbh.table_cell_node(row, 'center', date_begin.date)
        
        self.dbh.table_cell_node(row, 'center', date_end.date)
        return row

    def row_empty_element(self, row, task, level=0):
        """ create a DOM element <row> with values in task node"""
        #row = ET.SubElement(tbody, 'row')
        # indentation
        indent = u'\xA0 '*(level-1)*2
        # task title
        if level == 1:
            self.dbh.table_cell_node(row, 'left', indent+task.title)
        else:
            self.dbh.table_cell_node(row, 'left', indent+PUCE+task.title)
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
    

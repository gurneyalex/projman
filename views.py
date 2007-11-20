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
            task_cost = self.projman.get_task_total_cost(task.id)
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
        table = ET.SubElement(parent,"table")
        ET.SubElement(table, "title").text = self.ENTETE
        # fill column information for table
        layout = self.dbh.table_layout_node(table, 4, colspecs=('3*', '1*', '2*', '1*'))
        self.table_head( layout )
        # table body
        tbody = ET.SubElement(layout, "tbody")
        for child in self.projman.root_task.children:
            if child.TYPE == 'task' :
                self._build_task_node(tbody, child)

    def table_head(self, parent):
        """ create a DOM node <thead> """
        thead = ET.SubElement(parent, 'thead')
        row = ET.SubElement(thead,'row')
        self.dbh.table_cell_node(row)
        self.dbh.table_cell_node(row, 'left', u'Charge (jours.homme)')
        self.dbh.table_cell_node(row, 'left', u'Ressources')
        self.dbh.table_cell_node(row, 'right', u'Coût (euros)')
        return thead

    def _build_task_node(self, tbody, task, level=0):
        """format a task in as a row in the table"""
        try:
            task_cost = self.projman.tasks.get_cell_by_ids(task.id, 'cost') or 0
        except KeyError:
            task_cost = 0
        if task_cost:
            self.row_element(tbody, task, task_cost, level)
        else:
            self.empty_row_element(tbody, task, level)
        for child in task.children:
            self._build_task_node(tbody, child, level+1)

    def row_element(self, tbody, task, task_cost, level=0):
        """ create a DOM element <row> with values in task node"""
        row = ET.SubElement(tbody, 'row')
        indent = u'\xA0 '*level
        # task title
        self.dbh.table_cell_node(row, 'left', indent+task.title)
        # task duration
        duration = task.duration and unicode(task.duration) or u''
        self.dbh.table_cell_node(row, 'left', duration)
        # task cost by resources
        costs, durations = self.projman.get_task_costs(task.id)
        # FIXME = do we what number of days for each resource or monetary cost for each resource.
        r_info = ['%s(%s)' % (r_id, format_monetary(cost)) 
                  for r_id, cost in durations.items() if r_id]
        self.dbh.table_cell_node(row, 'left', ', '.join(r_info))
        # task global cost
        # FIXME hack : a (containing) task with no resources has global cost of 1!
        if durations.keys() == [u''] and task_cost == 1.:
            self.dbh.table_cell_node(row, 'right', 0)
        else:
            self.dbh.table_cell_node(row, 'right', format_monetary(task_cost))
        return row

    def empty_row_element(self, tbody, task, level=0):
        """ create a DOM element <row> with values in task node"""
        row =  ET.SubElement(tbody, 'row')
        indent = u'\xA0 '*level
        # task title
        self.dbh.table_cell_node(row, 'left', indent+task.title)
        self.dbh.table_cell_node(row)
        self.dbh.table_cell_node(row)
        self.dbh.table_cell_node(row)
        return row

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
        for child in self.projman.root_task.children:
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
        if self.config.display_dates:
            # add date-constraints
            formalpara = self.dbh.formalpara(section, u"Dates")
            date_begin, date_end = self.projman.get_task_date_range(task)
            begin = date_begin or DATE_NOT_SPECIFIED
            end = date_end or DATE_NOT_SPECIFIED
            self.dbh.para(formalpara, u"du %s au %s" % (begin.Format(EXT_DATE_FORMAT),
                                                        end.Format(EXT_DATE_FORMAT)) )
        # add resources' info
        if task.TYPE == 'task' :
            resource_dict = self.projman.get_resources_duration_per_task(task.id)
            for r_id, r_usage in resource_dict.iteritems():
                self.resource_node(section, task.id, r_id, r_usage)
        # print children
        for child in task.children:
            self._build_task_node(section, child)
        return section

    def resource_node(self, parent, task_id, r_id, usage):
        """ create a DOM node
        <formalpara id=r_id.>
          <title>resource.name</title>
          <para>usage</para>
        </formalpara>
        """
        resource = self.projman.get_resource(r_id)
        para = self.dbh.formalpara(parent, resource.name, id=task_id+'_'+r_id)
        self.dbh.para( para, get_daily_labor(usage) )
        return para


class DurationTableView(CostTableView):
    name = 'duration-table'
    ENTETE = u"Tableau récapitulatif des dates."

    def add_content_nodes(self, parent):
        """return a dr:object node for the cost table view"""
        table = ET.SubElement(parent,"table")
        ET.SubElement(table,"title").text = self.ENTETE
        # fill column information for table
        layout = self.dbh.table_layout_node(table, 4, colspecs=('3*', '2*', '2*', '1*'))
        self.table_head(layout)
        # table body
        tbody = ET.SubElement(table, "tbody")
        for child in self.projman.root_task.children:
            if child.TYPE == 'task' :
                self._build_task_node(tbody, child)

    def table_head(self, table):
        """ create a DOM node <thead> """ 
        thead = ET.SubElement(table, "thead")
        row = ET.SubElement(thead,"row")
        self.dbh.table_cell_node(row)
        self.dbh.table_cell_node(row, 'left', u'Date de début')
        self.dbh.table_cell_node(row, 'left', u'Date de fin')
        self.dbh.table_cell_node(row, 'center', u'Durée (jours)')
        return thead

    def row_element(self, tbody, task, task_cost, level=0):
        """ create a DOM element <row> with values in task node"""
        return self.empty_row_element(tbody, task, level)
    
    def empty_row_element(self, tbody, task, level=0):
        """ create a DOM element <row> with values in task node"""
        row = ET.SubElement(tbody, 'row')
        # indentation
        indent = u'\xA0 '*level
        # task title
        self.dbh.table_cell_node(row, 'left', indent+task.title)
        # task begin & end
        date_begin, date_end = self.projman.get_task_date_range(task)
        self.dbh.table_cell_node(row, 'left', date_begin.date)
        self.dbh.table_cell_node(row, 'left', date_end.date)
        # task length
        duration = date_end+1 - date_begin
        self.dbh.table_cell_node(row, 'left', str(duration.absvalues()[0]))
        return row


ALL_VIEWS = {}
for klass in (RatesSectionView,
              DurationTableView, DurationParaView, DurationSectionView,
              DateParaView,
              CostTableView, CostParaView,
              TasksListSectionView):
    ALL_VIEWS[klass.name] = klass
    

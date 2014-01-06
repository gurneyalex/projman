# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2013 LOGILAB S.A. (Paris, FRANCE).
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
from projman.lib._exceptions import ViewException, ProjmanError
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

# dom utilities ################################################################

DR_NS = "{http://www.logilab.org/2004/Documentor}"
LDG_NS = "{http://www.logilab.org/2005/DocGenerator}"
ET._namespace_map[DR_NS[1:-1]] = "dr"
ET._namespace_map[LDG_NS[1:-1]] = "ldg"

NBSP = u'\xA0'
PUCE = u'\u203A'+NBSP

def indentation(level, puce_if_level=False):
    """return unicode indentation string made of no-break-space"""
    res = NBSP*(level-1)*2
    if puce_if_level and level > 1:
        res += PUCE
    return res

def document(root=None):
    """return a DOM document node"""
    root = ET.Element(DR_NS + (root or "root") )
    return ET.ElementTree(root)

class DocbookHelper(object):
    """a helper class to generate docboock"""

    def __init__(self, lang='fr'):
        self.lang = lang

    def object_node(self, parent, task_id):
        """create a DOM node <section> with a attribute id"""
        assert isinstance(task_id, basestring)
        node = ET.SubElement(parent, DR_NS + "object", id=task_id, lang=self.lang)
        return node

    def table_layout_node(self, parent, nbcols, align='left', colsep=1, rowsep=1,
                          colspecs=None):
        layout = ET.SubElement(parent, "tgroup", cols=str(nbcols),
                               align=align, colsep=str(colsep),
                               rowsep=str(rowsep))
        if colspecs:
            assert nbcols == len(colspecs), "len(colspecs) should be equal to nbcols!"
            for i, colspec in enumerate(colspecs):
                ET.SubElement(layout, "colspec", colname="c%s"%i, colwidth=colspec)
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
            section.set("id", id)
        assert isinstance(title, unicode)
        ET.SubElement(section, 'title').text = title
        return section

    def para(self, parent, text):
        assert isinstance(text, unicode)
        ET.SubElement(parent, "para").text = text

    def formalpara(self, parent, title, id=None):
        para = ET.SubElement(parent, "formalpara")
        if id:
            para.set("id", id)
        assert isinstance(title, unicode)
        ET.SubElement(para, 'title').text = title
        return para

# other utilities and abstract classes ########################################

# XXXFIXME handle english (lang='en')

TVA = 20.0
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

class CostData(object):
    """handle global calculation: cost, duration, ressources' rate
    """

    def __init__(self, projman):
        self.projman = projman
        self.project_cost = 0.0
        self.project_duration = 0.0
        self._used_resources = set()
        self.compute(projman.root_task)

    def compute(self, project):
        """recursively compute task cost"""
        for task in project.children:
            self._compute(task)

    def _compute(self, task, level=0):
        """recursively compute task cost"""
        try:
            task_cost = self.projman.get_task_total_cost(task, task.duration)
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


class XMLView(object):
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
        view.add_content_nodes(parent)

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
        itemizedlist = ET.SubElement(parent, "itemizedlist")
        task_roles = set()
        for task in self.projman.root_task.leaves():
            if task.resources_role is not None:
                task_roles.add(task.resources_role)
        for role_id in task_roles:
            role = self.projman.get_role(role_id)
            r_info = '%s (%s) : %s' % (role.name, role.id,
                                       format_monetary(role.hourly_cost * HOURS_PER_DAY))
            item = ET.SubElement(itemizedlist, "listitem")
            self.dbh.para(item, r_info)


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
        ET.SubElement(parent, "para").text = text

class DurationParaView(XMLView):
    name = 'duration-para'

    def add_content_nodes(self, parent):
        text = TOTAL_DURATION % get_daily_labor(self.projman.root_task.maximum_duration())
        ET.SubElement(parent, "para").text = text


class RoleLoadsTableView(XMLView):
    name = 'role-loads'
    ENTETE = u"Tableau de synthèse des charges."
    COLS = [("2*", "left", u"Type de ressource"),
            ("1*", "right", u"Charge totale")]

    def add_content_nodes(self, parent):
        """return a dr:object node for the cost table view"""
        self.projman.update_caches()

        # create table
        table = ET.SubElement(parent, 'table')
        ET.SubElement(table, 'title').text = self.ENTETE
        cols = [col_def[0] for col_def in self.COLS]
        layout = self.dbh.table_layout_node(table, len(cols), colspecs=cols)

        # table head
        thead = ET.SubElement(layout, 'thead')
        row = ET.SubElement(thead, 'row')
        for col_def in self.COLS:
            self.dbh.table_cell_node(row, "center", col_def[2])

        # table body
        tbody = ET.SubElement(layout, 'tbody')
        tbody.set(LDG_NS+"row-borders", 'true')
        tbody.set(LDG_NS+'row-backgrounds', "never")
        for rid, load in self._calc_res_loads(self.projman.root_task).items():
            row = ET.SubElement(tbody, 'row')
            role = self.projman.get_role(rid)
            content = [u"%s (%s)" % (role.name, role.id), str(load)]
            for i,txt in enumerate(content):
                self.dbh.table_cell_node(row, self.COLS[i][1], txt)

    def _calc_res_loads(self, task, loads=None):
        if loads is None:
            loads = {}
        if task.duration > 0:
            loads.setdefault(task.resources_role, 0.0)
            loads[task.resources_role] += task.duration
        for child in task.children:
            self._calc_res_loads(child, loads)
        return loads

class LoadTableView(XMLView):
    name = 'load-table'
    ENTETE = u"Tableau récapitulatif des charges."
    COLS = [("3*", "left", u"Tâches"),
            ("1*", "center", u"Type"),
            ("1*", "right", u"Charge")]

    def add_content_nodes(self, parent):
        """return a dr:object node for the cost table view"""
        self.projman.update_caches()
        roles = set(self.projman.get_role(task.resources_role)
                    for task in self.projman.root_task.leaves()
                    if task.resources_role)
        self.roles = sorted(roles, key=lambda x: x.id)
        assert len(roles) == len(set(role.id for role in roles)), '%s %s' % (roles, set(role.id for role in roles))

        # create table
        table = ET.SubElement(parent, 'table')
        ET.SubElement(table, 'title').text = self.ENTETE
        cols = [col_def[0] for col_def in self.COLS]
        layout = self.dbh.table_layout_node(table, len(cols), colspecs=cols)
        self.table_head(layout)

        # table body
        tbody = ET.SubElement(layout, 'tbody')
        tbody.set(LDG_NS+"row-borders", 'false')
        tbody.set(LDG_NS+'row-backgrounds', "never")
        for child in self.projman.root_task.children:
            if child.TYPE == 'task' and child.level:
                self.color = 0
                self._build_task_node(tbody, child, child.level)

    def table_head(self, parent):
        """ create a DOM node <thead> """
        thead = ET.SubElement(parent, 'thead')
        row = ET.SubElement(thead, 'row')
        for col_def in self.COLS:
            self.dbh.table_cell_node(row, "center", col_def[2])
        return thead

    def _build_task_node(self, tbody, task, level=1):
        """format a task in as a row in the table"""
        if not task.children or level > self.max_level:
            self.row_element(tbody, task, level)
        elif task.children and level <= self.max_level:
            self.row_element(tbody, task, level, empty_row=True)
            for child in task.children:
                if child.TYPE == 'milestone':
                    continue
                if task.level == 1:
                    self.color += 1
                self._build_task_node(tbody, child, level+1)
            if self.config.display_synthesis:
                self.row_element(tbody, task, level, synthesis_row=True)

    def _calc_task_cost_and_duration(self, task):
        costs, durations = self.projman.get_task_costs(task, task.duration)
        cost = sum(costs.values())
        dur = sum(durations.values())
        for child in task.children:
            cc, dd = self._calc_task_cost_and_duration(child)
            cost+=cc
            dur+=dd
        return cost, dur

    def _get_row_content(self, task, level, empty_row, synthesis_row):
        """returns the list of the entries of the row depicting a task"""
        cost, duration = self._calc_task_cost_and_duration(task)
        title = u""
        if synthesis_row:
            title += "Totaux "
        title += task.title
        if duration == 0 or empty_row:
            return [ indentation(level, True)+title, "", ""]
        else:
            return [ indentation(level, True)+title,
                     task.resources_role,
                     str(duration) ]

    def row_element(self, tbody, task, level=1,
                    empty_row=False, synthesis_row=False):
        """ create a DOM element <row> with values in task node"""
        row = ET.SubElement(tbody, 'row')
        if self.color % 2:
            row.set(LDG_NS+'background', 'true')
        if synthesis_row:
            row.set(LDG_NS+'italic', 'true')
        contents = self._get_row_content(task, level, empty_row, synthesis_row)
        if level == 1:
            row.set(LDG_NS+'bold', 'true')
            if not synthesis_row:
                row.set(LDG_NS+'border-top', 'true')
            if synthesis_row or not task.children:
                row.set(LDG_NS+'border-bottom', 'true')
        for i in range(len(self.COLS)):
            self.dbh.table_cell_node(row, self.COLS[i][1], contents[i])
        return row


class CostTableView(LoadTableView):
    name = 'cost-table'
    ENTETE = u"Tableau récapitulatif des coûts."
    COLS = [("3*", "left", u"Tâches"),
            ("1*", "center", u"Type"),
            ("1*", "right", u"Charge"),
            ("1*", "right", u"Coût")]

    def _get_row_content(self, task, level, empty_row, synthesis_row):
        """returns the list of the entries of the row depicting a task"""
        cost, duration = self._calc_task_cost_and_duration(task)
        title = u""
        if synthesis_row:
            title += "Totaux "
        title += task.title
        if duration == 0 or empty_row:
            return [ indentation(level, True)+title, "", "", ""]
        else:
            return [ indentation(level, True)+title,
                     task.resources_role,
                     str(duration),
                     format_monetary(cost) ]

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
            if child.TYPE != 'milestone':
                self._build_task_node(parent, child)

    def _build_task_node(self, parent, task):
        section = self.dbh.section(parent, task.title, id=task.id)
        if task.description != "":
            # create xml-like string
            # encode it and create XML tree from it
            # FIXME !!!
            assert isinstance(task.description, unicode), type(task.description)
            desc = "<?xml version='1.0' encoding='UTF-8'?><para>%s</para>" \
                   % task.description.encode('utf8')
            try:
                description_doc = ET.fromstring(desc)
            except:
                print desc
                raise
            section.append(description_doc)
        if task.children:
            self._build_tables(task, section)
            self.add_para_total_load(section, task)
            if  self.config.display_dates:
                self.add_dates(section, task)
            for child in task.children:
                if child.TYPE != 'milestone':
                    self._build_task_node(section, child)
        else:
            # task is a leaf task, not a container
            if task.TYPE == 'task' :
                self.resource_node(section, task)
            if self.config.display_dates:
                self.add_dates(section, task)
            if task.link:
                para = self.dbh.formalpara(section, u'Voir aussi')
                link = ET.SubElement(para, "ulink")
                link.set(u'url', '%s' %task.link)
        return section

    def add_dates(self, parent, task):
        """print begin and end of task"""
        para = self.dbh.formalpara(parent, u'Dates')
        para = ET.SubElement(parent, "para")
        list_ = ET.SubElement(para, "itemizedlist")
        debut, fin = self.projman.get_task_date_range(task)
        item = ET.SubElement(list_, 'listitem')
        self.dbh.para(item, u"Date de début : %s" %debut.Format(EXT_DATE_FORMAT))
        item = ET.SubElement(list_, 'listitem')
        self.dbh.para(item, u"Date de fin :   %s" %fin.Format(EXT_DATE_FORMAT))

    def add_para_total_load(self, parent, task):
        """print total load (load for each resources)"""
        para = self.dbh.formalpara(parent, u'Charge totale')
        para = ET.SubElement(para, "para")
        list_ = ET.SubElement(para, "itemizedlist")
        durations = {}
        costs = {}
        for leaf in task.leaves():
            if leaf.TYPE == 'milestone':
                continue
            costs_, durations_ = self.projman.get_task_costs(leaf, leaf.duration)
            for res in durations_:
                if res not in durations:
                    durations.setdefault(res, 0)
                    costs.setdefault(res, 0)
                durations[res] += durations_[res]
                costs[res] += costs_[res]
        for res in durations:
            resource = self.projman.get_resource(res)
            role_id = resource.role_ids()[0] # XXX what if more than one role ?
            role = self.projman.get_role(role_id)
            item = ET.SubElement(list_, 'listitem')
            self.dbh.para(item, u"%s (%s) : %s" % (role.name, resource.name, get_daily_labor(durations[res])))


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
        para = self.dbh.formalpara(parent, u'Charge')
        para = ET.SubElement(parent, "para")
        list_ = ET.SubElement(para, "itemizedlist")
        _, duration = self.projman.get_task_costs(task, task.duration)
        for res in duration:
            resource = self.projman.get_resource(res)
            res_role = self.projman.get_role(task.resources_role)
            role = res_role.name
            item = ET.SubElement(list_, 'listitem')
            self.dbh.para(item, u"%s (%s) : %s" %(role, resource.name, get_daily_labor(duration[res])))
        return para

    def _build_tables(self, task, section):
        """ build tables of principal information of the task
        one for duration of subtasks and date of end of subtasks
        and another to describe deliverables"""
        # table of subtasks
        table = ET.SubElement(section, "informaltable")
        layout = self.dbh.table_layout_node(table, 2, colspecs=('2*', '1*'))
        self.table_head_task(layout)
          # table body
        tbody = ET.SubElement(layout, 'tbody')
          # lines of table
        for child in task.children:
            if child.TYPE != 'milestone':
                self.row_element(child, tbody)
        # table of deliverables :
        # find milestones
        milestones = []
        for child in task.children:
            if child.TYPE == 'milestone':
                milestones.append(child)
        if milestones:
            table = ET.SubElement(section, "informaltable")
            if self.config.display_dates:
                layout = self.dbh.table_layout_node(table, 2, colspecs=('2*', '1*'))
            else:
                layout = self.dbh.table_layout_node(table, 1, colspecs=('1*',))
            self.table_head_milestone(layout)
            # table body
            tbody = ET.SubElement(layout, 'tbody')
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
        row = ET.SubElement(thead, 'row')
        self.dbh.table_cell_node(row, 'left', u'Tâches contenues')
        self.dbh.table_cell_node(row, 'left', u'Charge')
        return thead

    def table_head_milestone(self, parent):
        """ create a DOM node <thead> for the milestone table """
        thead = ET.SubElement(parent, 'thead')
        row = ET.SubElement(thead, 'row')
        self.dbh.table_cell_node(row, 'left', u'Jalons')
        if  self.config.display_dates:
            self.dbh.table_cell_node(row, 'left', u'Date de livraison')
        return thead

    def row_element(self, task, tbody):
        """ create a DOM element <row> with values in task node"""
        def compute_duration(task):
            accumul = 0.0
            for sub_task in task.children:
                accumul += compute_duration(sub_task)
            else:
                accumul += task.duration or 0.0
            return accumul
        row = ET.SubElement(tbody, 'row')
        # task title
        self.dbh.table_cell_node(row, 'left', task.title)
        if task.children:
            duration = compute_duration(task)
            roles = set(self.projman.get_role(child.resources_role).id
                        for child in task.children if child.resources_role)
            if not roles:
                raise ProjmanError('Cant find a role for task %s' % task.id)
            role = ', '.join(sorted(roles))
        else:
            duration = task.duration and unicode(task.duration) or u''
            # get resource_role by taking possibly the parent's role
            parent = task
            while parent:
                if parent.resources_role:
                    role = self.projman.get_role(parent.resources_role).id
                    break
                parent = parent.parent
            else:
                raise ProjmanError('Cant find a role for task %s' % task.id)
        self.dbh.table_cell_node(row, 'left', u'%s : %s j.h' % (role, duration) )


class DurationTableView(LoadTableView):
    name = 'duration-table'
    ENTETE = u"Tableau récapitulatif des dates."
    COLS = [("3*", "left", u"Tâches"),
            ("1*", "center", u"Date de début"),
            ("1*", "center", u"Date de fin") ]

    def _get_row_content(self, task, level, empty_row, synthesis_row):
        """returns the list of the entries of the row depicting a task"""
        date_begin, date_end = self.projman.get_task_date_range(task)
        title = u""
        if synthesis_row:
            title += u"Récapitulatif "
        title += task.title
        if empty_row:
            return [ indentation(level, True)+title, "", ""]
        else:
            return [ indentation(level, True)+title,
                     date_begin.date,
                     date_end.date ]

ALL_VIEWS = {}
for klass in (RatesSectionView, RoleLoadsTableView,
              DurationTableView, DurationParaView, DurationSectionView,
              DateParaView, LoadTableView,
              CostTableView, CostParaView,
              TasksListSectionView):
    ALL_VIEWS[klass.name] = klass


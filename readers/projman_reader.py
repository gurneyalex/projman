# -*- coding: utf-8 -*-
# Copyright (c) 2000-2013 LOGILAB S.A. (Paris, FRANCE).
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

"""
reader generate a model from xml file (see dtd/project.dtd)
"""
from projman.readers.base_reader import AbstractXMLReader
from projman.readers.projman_checkers import ProjectChecker, ScheduleChecker, ResourcesChecker
from projman.readers.projman_checkers import TasksChecker
from projman.readers.projman_checkers import iso_date, iso_time
from os.path import dirname, abspath, isabs, join
from logilab.common.table import Table
from docutils.core import publish_string
from logilab.common.textutils import colorize_ansi
from projman.lib._exceptions import ProjectValidationError, MalformedProjectFile, MalformedId
from projman import DAY_WEEK
from projman.lib.constants import LOAD_TYPE_MAP, TASK_MILESTONE

try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET
from xml.parsers.expat import ExpatError

from logilab.doctools.rest_docbook import rest_dbk_transform
from lxml.etree import tostring as lxml_tostring

def js(txt):
    """join and split"""
    return u' '.join(txt.split())

def xml_parse(source):
    """catch xml parsing errors"""
    try:
        return ET.parse( source )
    except ExpatError, exc:
        msg = "%s : %s" % (ExpatError, exc)
        raise MalformedProjectFile(msg)

class ProjectXMLReader(AbstractXMLReader) :

    def __init__(self, src, task_root=None, skip_schedule=False):
        AbstractXMLReader.__init__(self)
        self.source = src
        self.task_root = task_root
        self.skip_schedule = skip_schedule
        self.project = self._factory.create_project()
        self.files = {'tasks': None,
                      'schedule': None,
                      'resources': None,
                      'activities': None,
                      }

    def read(self):
        if isinstance(self.source, str):
            tree = xml_parse( file(self.source) )
            filename = self.source
            base_uri = dirname(abspath(filename))
        elif isinstance(self.source, file):
            tree = xml_parse(self.source)
            filename = 'input_stream'
            base_uri = ''
        elif isinstance(self.source, ET.ElementTree):
            tree = self.source
            filename = 'input_tree'
            base_uri = ''
        else:
            raise ValueError('unknown source %s' % self.source)
        return self.fromTree(tree, filename, base_uri), self.files

    def get_file(self, tree, ftype, default=None):
        node = tree.find("import-"+ftype)
        if node is None:
            return default
        fname = node.get("file", default)
        self.files[ftype] = fname
        if not isabs(fname):
            fname = join(self._base_uris[-1], fname)
        return fname

    def fromTree(self, tree, filename="input_stream", base_uri=''):
        self._base_uris.append(base_uri)
        checker = ProjectChecker()
        if not checker.validate(tree, filename):
            raise MalformedProjectFile(str(checker))
        sched = self.get_file(tree, "schedule")
        tasks = self.get_file(tree, "tasks")
        rsrc = self.get_file(tree, "resources")
        act = self.get_file(tree, "activities")
        self.project.root_task = self.read_tasks(tasks)
        self.read_resources_file(rsrc)
        self.project.add_activities( self.read_activities(act) )
        if sched and not self.skip_schedule:
            try:
                file(sched,"r")
            except IOError, exc:
                print colorize_ansi("WARNING!", "red"),
                print (" %s. Proceeding without scheduling information." % exc)
            else:
                self.read_schedule(sched)
        return self.project

    def read_schedule(self, fname):
        schedule = xml_parse( fname )
        checker = ScheduleChecker()
        if not checker.validate(schedule, fname):
            raise MalformedProjectFile(str(checker))

        activities = Table(default_value=None,
                           col_names=['begin', 'end', 'resource', 'task',
                                      'usage', 'src'])
        tasks = Table(default_value=None,
                      col_names=['begin', 'end', 'status', 'cost', 'unit'])
        costs = Table(default_value=None,
                      col_names=['task', 'resource', 'cost', 'unit'])

        for task in schedule.findall("task"):
            t_id = task.get('id')
            tasks.create_row( t_id )
            global_cost = task.find("global-cost")
            tasks.set_cell_by_ids(t_id, 'unit', global_cost.get('unit'))
            tasks.set_cell_by_ids(t_id, 'cost', float(global_cost.text) )
            tasks.set_cell_by_ids(t_id, 'status', task.find('status').text )
            for cd in task.findall("contraint-date"):
                date = iso_date( cd.text )
                if cd.get('type') == 'begin-at-date':
                    tasks.set_cell_by_ids( t_id, 'begin', date )
                elif cd.get('type') == 'end-at-date':
                    tasks.set_cell_by_ids( t_id, 'end', date )
            for ct in task.findall("constraint-task"):
                pass
                #raise NotImplementedError("constraint-task not implemented in schedule")
            for report in task.findall("report-list/report"):
                activities.append_row( (iso_date(report.get('from')),
                                             iso_date(report.get('to')),
                                             report.get('idref'),
                                             t_id,
                                             float(report.get('usage')) ) )
            for cost in task.findall("costs_list/cost"):
                costs.append_row( (t_id, cost.attrib['idref'],float(cost.text),None) )

        for milestone in schedule.findall("milestone"):
            t_id = milestone.get('id')
            cd = milestone.find("constraint-date")
            date = iso_date( cd.text )
            self.project.milestones[t_id] = date

        self.project.add_schedule(activities)
        self.project.tasks = tasks
        self.project.costs = costs
        self.project.nb_solution = 1 # if we read a schedule from an xml file,
                                     # we obviusly have one solution

    def read_tasks(self, fname):
        tasks = xml_parse( fname )
        checker = TasksChecker()
        if not checker.validate(tasks, fname):
            raise MalformedProjectFile(str(checker))
        self.tasks_file = fname
        rt = tasks.getroot()
        if self.task_root and rt.get("id") != self.task_root:
            for t in rt.findall(".//task"):
                if t.get("id") == self.task_root:
                    rt = t
                    break
            else:
                raise RuntimeError("Task root %s not found" % self.task_root)
        return self.read_task(rt, 0)

    def read_task(self, task, niveau):
        t = self._factory.create_task( task.get("id") )
        t.level = niveau
        if task.get("resource-role"):
            t.resources_role = task.get("resource-role")
        self.task_milestone_common( t, task )
        for child in task:
            if child.tag == 'constraint-interruptible':
                if child.get('type') == 'False':
                    t.can_interrupt[0] = False
                if child.get('priority'):
                    t.can_interrupt[1] = int(child.get('priority'))
            elif child.tag == "progress":
                t.progress = float(child.text)
            elif child.tag == "priority":
                t.priority = int(child.text)
            elif child.tag == "task":
                t.append( self.read_task( child, niveau+1))
            elif child.tag == "milestone":
                t.append( self.read_milestone(child) )
        return t

    def read_milestone(self, mstone):
        m = self._factory.create_milestone( mstone.get("id") )
        self.task_milestone_common( m, mstone )
        return m

    def task_milestone_common(self, t, task):
        t.title = js(unicode(task.find("label").text))
        load_type = LOAD_TYPE_MAP[ task.get("load-type", "shared").lower() ]
        if task.tag=="milestone":
            load_type = TASK_MILESTONE
        t.load_type = load_type
        t.duration = float(task.get("load", "0"))
        for link in task.findall('link'):
            t.link = link.get('url')
        for cd in task.findall("constraint-date"):
            if cd.get("priority"):
                priority = cd.get("priority")
            else:
                priority = 1
            t.add_date_constraint( cd.get("type"), iso_date( cd.text ), priority )
        for ct in task.findall("constraint-task"):
            if ct.get("priority"):
                priority = ct.get("priority")
            else:
                priority = 1
            idref = ct.get("idref")
            if idref=="none":
                idref=None
            t.add_task_constraint( ct.get("type"), ct.get("idref"), priority)

        desc = task.find("description")
        txt_fmt = "none"
        if desc is None:
            txt = u""
            raw_txt = u""
        else:
            if desc.get("format")=="docbook":
                txt_fmt = "docbook"
            txt = desc.text and unicode(desc.text) or u""
            for n in desc:
                txt+=unicode(ET.tostring(n,"utf-8"),"utf-8")
            raw_txt = txt
            if desc.get("format")=="rest":
                txt_fmt = "rest"
                dbk_elts = rest_dbk_transform(txt)
                txt = u""
                for n in dbk_elts:
                    txt+=unicode(lxml_tostring(n, encoding="utf-8"), "utf-8")
        t.description = txt
        t.description_raw = raw_txt
        t.description_format = txt_fmt


    def read_resource_definition(self, res_node):
        res_name = u'Unknown'
        res_cal = None
        roles = []
        for n in res_node:
            if n.tag == 'label':
                res_name = unicode(n.text)
            elif n.tag == 'use-calendar':
                res_cal_id = n.get('idref')
                res_cal = self.project.calendars[res_cal_id]
            elif n.tag == 'role':
                role_id = n.get('idref')
                roles.append(self.project.resources_roles[role_id])
            else:
                print 'Tag :', n.tag, 'not supported anymore'
        res_id = res_node.get('id')
        res = self._factory.create_resource(res_id, res_name, res_cal, roles)
        return res

    def read_resource_roles(self, tree):
        root_node = tree.getroot()
        res_roles = {}
        for res_role in root_node.findall('resource-role'):
            res_id = res_role.get('id')
            res = self._factory.create_resource_role( res_id, u'')
            res.hourly_cost = float(res_role.get("hourly-cost"))
            res.unit = res_role.get("cost-unit")
            for n in res_role._children:
                if n.tag == 'label':
                    res.name = unicode(n.text)
            res_roles[res_id] = res
        return res_roles

    def read_calendar_definition(self, cal_node, parent_cal=None):
        cal = self._factory.create_calendar( cal_node.get('id') )
        cal.type_working_days = {}
        cal.type_nonworking_days = {}
        for n in cal_node:
            if n.tag == "label":
                cal.name = unicode(n.text)
            elif n.tag == "day-types":
                cal.default_day_type = n.get('default')
                for day_type in n.findall('day-type'):
                    day_id = day_type.get('id')
                    day_type_label = unicode(day_type.find('label').text)
                    intervals = []
                    for interval in day_type.findall('interval'):
                        from_time = iso_time( interval.get('start') )
                        to_time = iso_time( interval.get('end') )
                        intervals.append( (from_time, to_time) )
                    cal.day_types[day_id] = [day_type_label, intervals]
            elif n.tag == "day":
                day_type = n.get('type')
                data = n.text
                if data in DAY_WEEK:
                    cal.weekday[data] = day_type
                elif len(data) < 8:
                    cal.national_days.append(tuple([int(item) for item in data.split('-')]))
                else:
                    date = iso_date(data)
                    cal.add_timeperiod(date, date, day_type)
            elif n.tag == "timeperiod":
                from_date = iso_date( n.get('from') )
                to_date = iso_date( n.get('to') )
                type_name = n.get('type')
                cal.add_timeperiod(from_date, to_date, type_name)
            elif n.tag == 'start-on':
                cal.start_on = iso_date(n.text)
            elif n.tag == 'stop-on':
                cal.stop_on = iso_date(n.text)
            elif n.tag == 'calendar':
                subcal = self.read_calendar_definition(n, parent_cal=cal)
                cal.append(subcal)
        return cal

    def read_resources(self, tree):
        root_node = tree.getroot()
        res_set = {}
        for res_node in root_node.findall('resource'):
            res = self.read_resource_definition( res_node )
            res_set[res.id] = res
        return res_set

    def read_calendars(self, tree):
        root_node = tree.getroot()
        calendars = {}
        for cal_node in root_node.findall('calendar'):
            cal = self.read_calendar_definition( cal_node )
            calendars[cal.id] = cal
            for subcal in cal.children:
                calendars[subcal.id] = subcal
        return calendars

    def read_resources_file(self, rsrc):
        rsrc_tree = xml_parse(rsrc)
        checker = ResourcesChecker()
        if not checker.validate(rsrc_tree, rsrc):
            raise MalformedProjectFile(str(checker))
        self.project.resources_roles = self.read_resource_roles(rsrc_tree)
        self.project.calendars = self.read_calendars(rsrc_tree)
        self.project.resources = self.read_resources(rsrc_tree)

    def read_activities(self, fname):
        tree = xml_parse(fname)
        root_node = tree.getroot()
        activities = []
        for reports in root_node.findall('reports-list'):
            task_id = reports.get('task-id')
            for report in reports.findall('report'):
                res_id = report.get('idref')
                begin = iso_date( report.get('from') )
                end = iso_date( report.get('to') )
                usage = float( report.get('usage') )
                activities.append( (begin, end, res_id, task_id, usage) )
        return activities

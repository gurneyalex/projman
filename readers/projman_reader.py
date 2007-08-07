# -*- coding: utf-8 -*-
# Copyright (c) 2000-2006 LOGILAB S.A. (Paris, FRANCE).
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
from logilab.doctools.rest_docbook import FragmentWriter
from logilab.common.textutils import colorize_ansi
from projman.lib._exceptions import ProjectValidationError, MalformedProjectFile

docbook_writer = FragmentWriter()

try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

def js(txt):
    """join and split"""
    return u' '.join(txt.split())


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
            tree = ET.parse( file(self.source) )
            filename = self.source
            base_uri = dirname(abspath(filename))
        elif isinstance(self.source, file):
            tree = ET.parse( stream )
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
        fname = node.get("file",default)
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
        rsrc = self.get_file(tree, "resources")
        act = self.get_file(tree, "activities")
        tasks = self.get_file(tree, "tasks")
        self.project.root_task = self.read_tasks(tasks)
        self.project.resource_set = self.read_resources(rsrc)
        self.project.add_activities( self.read_activities(act) )
        if sched and not self.skip_schedule:
            try:
                file(sched,"r")
            except IOError:
                print colorize_ansi("WATCH OUT!", "red"), \
                      "schedule file '%s' declared in project file but is missing. " \
                      "Command completed without scheduling information."% filename
            else:
                self.read_schedule( sched )
        return self.project

    def read_schedule(self, fname):
        schedule = ET.parse( fname )
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

    def read_tasks(self, fname):
        tasks = ET.parse( fname )
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
        return self.read_task(rt)

    def read_task(self, task):
        t = self._factory.create_task( task.get("id") )
        self.task_milestone_common( t, task )
        for child in task:
            if child.tag == "duration":
                t.duration = float(child.text)
            elif child.tag == "progress":
                t.progress = float(child.text)
            elif child.tag == "priority":
                t.priority = int(child.text)
            elif child.tag == "task":
                t.append( self.read_task( child ))
            elif child.tag == "milestone":
                t.append( self.read_milestone(child) )
        return t

    def read_milestone(self, mstone):
        m = self._factory.create_milestone( mstone.get("id") )
        self.task_milestone_common( m, mstone )
        return m

    def task_milestone_common(self, t, task):
        t.title = js(unicode(task.find("label").text))
        for cd in task.findall("constraint-date"):
            t.add_date_constraint( cd.get("type"), iso_date( cd.text ) )
        for ct in task.findall("constraint-task"):
            t.add_task_constraint( ct.get("type"), ct.get("idref") )
        for cr in task.findall("constraint-resource"):
            t.add_resource_constraint( cr.get("type"), cr.get("idref"), float(cr.get("usage")) )
        desc = task.find("description")
        if desc is None:
            txt = u""
        else:
            txt = unicode(desc.text) or u""
            for n in desc:
                txt+=unicode(ET.tostring(n,"utf-8"),"utf-8")
            if desc.get("format")=="rest":
                txt = publish_string(txt,
                                     settings_overrides={'output_encoding': 'unicode'},
                                     writer=docbook_writer,
                                     source_path=self.tasks_file + "<%s>"%t.id)
        t.description = txt


    def read_resource_definition(self, res_node):
        res = self._factory.create_resource( res_node.get('id'), u'',
                                             res_node.get('type'), u'' )
        for n in res_node:
            if n.tag == 'label':
                res.name = unicode(n.text)
            elif n.tag == 'hourly-rate':
                res.hourly_rate[0] = float(n.text)
                res.hourly_rate[1] = n.get('unit','euros')
            elif n.tag == 'use-calendar':
                res.calendar = n.get('idref')
        return res


    def read_calendar_definition(self, cal_node):
        _dict_days_types = {}
        cal = self._factory.create_calendar( cal_node.get('id') )
        cal.type_working_days = {}
        cal.type_nonworking_days = {}
        for n in cal_node:
            if n.tag == "label":
                cal.name = unicode(n.text)
            elif n.tag == "day-types":
                # --------------------------
                # Read day-types
                # --------------------------
                for day_type in n.findall('day-type'):
                    day_id = day_type.get('id')
                    day_type_name = unicode(day_type.find('label').text)
                    _dict_days_types[day_id] = day_type_name
                    cal.type_nonworking_days[day_id] = day_type_name
                    intervals = [day_type_name,[]]
                    for interval in day_type.findall('interval'):
                        from_time = iso_time( interval.get('start') )
                        to_time = iso_time( interval.get('end') )
                        intervals[1].append( (from_time, to_time) )
                    if intervals[1]: # only add it if we have intervals
                        cal.type_working_days[day_id] = intervals
            elif n.tag == "default-working":
                # -----------------------------
                # Read defaults working day ids
                # -----------------------------
                # XXX: BUG? ou simple connerie? : on compare day_type[default-workin.idref]
                # avec w_type[0] (le label de day-type) au lieu de comparer juste les id ?
                _id = u''
                type_name = _dict_days_types[n.get('idref')]
                for t_id, w_type in cal.type_working_days.items():
                    if w_type[0] == type_name:
                        _id = t_id
                cal.default_working = _id
            elif n.tag == "default-nonworking":
                # -----------------------------
                # Read defaults working day ids
                # -----------------------------
                _id = u''
                type_name = _dict_days_types[n.get('idref')]
                for t_id, w_type in cal.type_nonworking_days.items():
                    if w_type == type_name:
                        _id = t_id
                cal.default_nonworking = _id
            elif n.tag == "day":
                day_type_name = _dict_days_types[ n.get('type') ]
                data = n.text
                if data in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'):
                    cal.weekday[data] = day_type_name
                elif len(data) < 8:
                    cal.national_days.append(tuple([int(item) for item in data.split('-')]))
                else:
                    date = iso_date(data)
                    cal.add_timeperiod(date, date, day_type_name)
            elif n.tag == "timeperiod":
                from_date = iso_date( n.get('from') )
                to_date = iso_date( n.get('to') )
                type_name = _dict_days_types[ n.get('type') ]
                cal.add_timeperiod( from_date, to_date, type_name )
            elif n.tag == 'start-on':
                print "TODO: Unhandled element start-on"
            elif n.tag == 'start-on':
                print "TODO: Unhandled element start-on"
            elif n.tag == 'calendar':
                subcal = self.read_calendar_definition( n )
                cal.append(subcal)
        return cal

    def read_resources(self, fname):
        tree = ET.parse(fname)
        checker = ResourcesChecker()
        if not checker.validate(tree, fname):
            raise MalformedProjectFile(str(checker))
        root_node = tree.getroot()
        res_set = self._factory.create_resourcesset('all_resources')
        for res_node in root_node.findall('resource'):
            res = self.read_resource_definition( res_node )
            res_set.append(res)
        for cal_node in root_node.findall('calendar'):
            cal = self.read_calendar_definition( cal_node )
            res_set.append(cal)
        return res_set
    
    def read_activities(self, fname):
        tree = ET.parse(fname)
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

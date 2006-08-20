# -*- coding: ISO-8859-1 -*-
# Copyright (c) 2000-2004 LOGILAB S.A. (Paris, FRANCE).
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

__revision__ = "$Id: projman_reader.py,v 1.8 2006-02-19 14:51:06 nico Exp $"

import sys
import os.path

from docutils.core import publish_string
from os.path import isabs, join
from mx.DateTime import DateTime, Time, now
from mx.DateTime.Parser import DateFromString
from logilab.common.textutils import colorize_ansi
from logilab.common.table import Table
from logilab.common.compat import set
from logilab.doctools.rest_docbook import FragmentWriter

from projman import LOG_CONF
from projman.lib._exceptions import ProjectValidationError
from projman.lib.constants import DATE_CONSTRAINTS, BEGIN_AT_DATE, END_AT_DATE
from projman.readers.base_reader import AbstractXMLReader

docbook_writer = FragmentWriter()

UNKNOWN_TAG = 'file %s line %s : Unknown tag %s'

# TaskXMLReader #############################################################

class TaskXMLReader(AbstractXMLReader) :
    """
    sax handler to process XML file and create Project and Task objects for the
    projman model
    """

    def __init__(self):
        AbstractXMLReader.__init__(self)
        self._main_project = 1
        self.inside_description = False
        self.stack.append([])

    def _start_element(self, tag, attr):
        """See SAX's ContentHandler interface.
        Calls _parsing_element or _copying_element depending on
        'self.inside_description' mode
        """
        if self.inside_description:
            self._copy_element(tag, attr)
        else:
            self._parse_element(tag, attr)
        
    def _copy_element(self, tag, attr) :
        """new element found in description: importing it as raw text
        """
        attr_desc = u""
        for attr, value in attr.items():
            attr_desc += u" %s='%s'" % (attr, value)
        self.characters(u"<%s%s>"% (tag, attr_desc))

    def _parse_element(self, tag, attr) :
        """new element found, parse it
        """
        if tag == 'description':
            self.assert_child_of(['task'])
            self.inside_description = True
            if attr.get('format') == 'rest':
                self.rest_description = True
            else:
                self.rest_description = False
        elif tag == 'import-project':
            self.assert_child_of(['task'])
            self.assert_has_attrs(['file'])
            file = attr['file']
            if not isabs(file):
                file = join(self._base_uris[-1], file)
            if not self._imported.has_key(file):
                p = ProjectXMLReader()
                proj = p.fromFile(file)
                self.stack[-1].append(proj)
                self.stack.append(proj)
                self._imported[file] = 1
        elif tag == 'task' :
            self.assert_child_of([None, 'task'])
            self.assert_has_attrs(['id'])
            t_id = self._factory.create_task(attr['id'])
            self.stack[-1].append(t_id)
            self.stack.append(t_id)
        elif tag == 'milestone' :
            self.assert_child_of(['task'])
            self.assert_has_attrs(['id'])
            m = self._factory.create_milestone(attr['id'])
            self.stack[-1].append(m)
            self.stack.append(m)                            
        elif tag == 'constraint-date':
            self.assert_child_of(['task', 'milestone'])
            self.assert_has_attrs(['type'])
            self.constraint_type = attr['type']           
        elif tag == 'constraint-task' :
            self.assert_child_of(['task', 'milestone'])
            self.assert_has_attrs(['type', 'idref'])
            type = attr['type']
            idref = attr['idref']
            if self.stack[-1].id == idref:
                raise Exception('task %s has constraint pointing to itself' % idref)
            self.stack[-1].add_task_constraint(type, idref)
        elif tag == 'constraint-resource' :
            self.assert_child_of(['task'])
            self.assert_has_attrs(['type', 'idref', 'usage'])
            usage = float(attr['usage'])
            type = attr['type']
            r_id = attr['idref']
            assert self.stack[-1].TYPE == 'task', 'Should have task, got %s' % (
                self.stack[-1].TYPE)
            self.stack[-1].add_resource_constraint(type, r_id, usage)
        elif tag == 'resource' :
            self.assert_child_of(['task'])
            self.assert_has_attrs(['idref'])
            self.stack[-1].resources.append(attr['idref'])
        elif tag == 'label':
            self.assert_child_of(['task', 'milestone'])
        elif tag == 'duration':
            self.assert_child_of(['task'])
        elif tag == 'progress':
            self.assert_child_of(['task'])
        elif tag == 'priority':
            self.assert_child_of(['task', 'milestone'])
        else :
            raise ProjectValidationError(UNKNOWN_TAG)
        
    def _end_element(self, tag) :
        """
        See SAX's ContentHandler interface
        """
        if self.inside_description: 
            self.process_not_parsed(tag)
        else:
            t = self.stack[-1]
            if tag in ('task', 'milestone'):
                self.stack.pop()
            elif tag in ('project', 'import-tasks'):
                if self._main_project:
                    self._main_project = 0
                else:
                    self.stack.pop()
            elif tag in ('label', 'duration', 'progress', 'priority', 'constraint-date'):
                chars = self.get_characters()
                if not chars:
                    raise ProjectValidationError('file %%s line %%s : %s tag not supposed to be empty %%s'%(tag))
                elif tag == 'label':
                    t.title = chars
                elif tag == 'duration':
                    t.duration = float(chars)
                elif tag == 'progress':
                    t.progress = float(chars)
                elif tag == "priority":
                    t.priority = int(chars)
                elif tag =='constraint-date':
                    date = _extract_date(chars)
                    t.add_date_constraint(self.constraint_type, date)
                    self.constraint_type = None
            else:
                if self.get_characters():
                    raise ProjectValidationError('file %%s line %%s : %s tag supposed to be empty %%s'%(tag))

    def process_not_parsed(self, tag):
        if tag == 'description':
            desc = self.get_characters(strip=False)
            if self.rest_description:
                self.stack[-1].description = publish_string(desc,
                                                            settings_overrides={'output_encoding': 'unicode'},
                                                            writer=docbook_writer)
            else:
                self.stack[-1].description = desc
            assert isinstance(self.stack[-1].description, unicode), self.stack[-1].description
            self.inside_description = False
        else:
            self.characters(u"</%s>"% tag)

    def _custom_return(self):
        return self.stack[0][0]

# ResourceXMLReader ##########################################################

class ResourcesXMLReader(AbstractXMLReader) :
    """
    sax handler to process XML file and create Resource Set object for projman model
    """
    
    def __init__(self, projman=None, activities=None):
        AbstractXMLReader.__init__(self)
        # used to link all day-type information for calendar
        self._day_type = False
        self._day_type_id = u''
        self._day_type_name = u''
        self._id_nonworking_remove = set()
        self._dict_days_types = {}

    def _start_element(self, tag, attr):
        """
        See SAX's ContentHandler interface
        """
        if tag == 'resources-list':
            self.assert_child_of([None])
            rs = self._factory.create_resourcesset('all_resources')
            self.stack.append(rs)
        elif tag == 'resource':
            self.assert_child_of(['resources-list'])
            self.assert_has_attrs(['type','id'])
            r_type = attr['type']
            r = self._factory.create_resource(attr['id'], u'', r_type, u'')
            self.stack[-1].append(r)
            self.stack.append(r)
        elif tag == 'hourly-rate':
            self.assert_child_of(['resource'])
            self.stack[-1].hourly_rate[1] = attr.get('unit', 'euros')
        elif tag == 'use-calendar':
            self.assert_child_of(['resource'])
            self.assert_has_attrs(['idref'])
            c_ref = attr['idref']
            self.stack[-1].calendar = c_ref
        elif tag == 'calendar':
            self.assert_child_of(['resources-list', 'calendar'])
            self.assert_has_attrs(['id'])
            c = self._factory.create_calendar(attr['id'])
            c.type_working_days = {}
            c.type_nonworking_days = {}
            self.stack[-1].append(c)
            self.stack.append(c)
        elif tag == 'day-types':
            self.assert_child_of(['calendar'])
        elif tag == 'day-type':
            self.assert_child_of(['day-types'])
            self.assert_has_attrs(['id'])
            self._day_type = True
            self._id = attr['id']
            self._dict_days_types[attr['id']] = u''
        elif tag == 'interval':
            self.assert_child_of(['day-type'])
            self.assert_has_attrs(['start','end'])
            from_time = _extract_time(attr['start'])
            to_time = _extract_time(attr['end'])
            c = self.stack[-1]
            self._id_nonworking_remove.add(self._day_type_id)
            if self._day_type_id not in c.type_working_days:
                c.type_working_days[self._day_type_id] = []
                type_name = self._day_type_name
                c.type_working_days[self._day_type_id].insert(0, type_name)
                interval = [(from_time, to_time)]
                c.type_working_days[self._day_type_id].insert(1, interval)
            else:
                interval = (from_time, to_time)
                c.type_working_days[self._day_type_id][1].append(interval)
        elif tag == 'day':
            self.assert_has_attrs(['type'])
            self._day_type_name = self._dict_days_types[attr['type']]
        elif tag == 'default-working':
            self.assert_child_of(['calendar'])
            self.assert_has_attrs(['idref'])
            id = u''
            type_name = self._dict_days_types[attr['idref']]
            for t_id in self.stack[-1].type_working_days:
                if self.stack[-1].type_working_days[t_id][0] == type_name:
                    id = t_id
            self.stack[-1].default_working = id
        elif tag == 'default-nonworking':
            self.assert_child_of(['calendar'])
            self.assert_has_attrs(['idref'])
            id = u''
            type_name = self._dict_days_types[attr['idref']]
            for t_id in self.stack[-1].type_nonworking_days:
                if self.stack[-1].type_nonworking_days[t_id] == type_name:
                    id = t_id
            self.stack[-1].default_nonworking = id
        elif tag == 'timeperiod':
            self.assert_child_of(['calendar'])
            self.assert_has_attrs(['from','to','type'])
            from_date = _extract_date(attr['from'])
            to_date = _extract_date(attr['to'])
            type_name = self._dict_days_types[attr['type']]
            self.stack[-1].add_timeperiod(from_date, to_date, type_name)
        elif tag == 'start-on':
	    pass
#            for id in self._id_nonworking_remove:
#                if id in self.stack[-1].type_nonworking_days:
#                    del self.stack[-1].type_nonworking_days[id]
#                else:
#                    print 'warning: day cannot be removed...', id # XXX
        elif tag == 'stop-on':
            pass
        elif tag == 'label' :
            self.assert_child_of(['resource', 'day-type', 'calendar'])
            if self._day_type:
                self._day_type = False
        else :
            raise ProjectValidationError(UNKNOWN_TAG)
        
    def _end_element(self, tag) :
        """
        See SAX's ContentHandler interface
        """
        res = self.stack[-1]
        if tag in ('resource', 'calendar'):
            self.stack.pop()
            self.current_tag = None
        elif tag in ('label', 'hourly-rate', 'start-on', 'stop-on', 'day'):
            data = self.get_characters()
            if not data:
                raise ProjectValidationError('file %%s line %%s : %s tag not supposed to be empty %%s'%(tag))
            if tag == 'label':
                if self._tags[-2] == "day-type":
                    self._day_type_name = data
                    self._dict_days_types[self._id] = data
                    self._day_type_id = len(res.type_nonworking_days)+1
                    res.type_nonworking_days[len(res.type_nonworking_days)+1] = data
                elif self._tags[-2] == "calendar":
                    res.name = data
                elif self._tags[-2] == "resource":
                    res.name = data
                else:
                    raise ProjectValidationError('%%s %%s %%s %s'%self._tags)
            elif tag == 'hourly-rate':
                res.hourly_rate[0] = float(data)
            elif tag == 'start-on':
                res.start_on = _extract_date(data)
            elif tag == 'stop-on':
                res.stop_on = _extract_date(data)
            elif tag == 'day':
                if data in ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'):
                    res.weekday[data] = self._day_type_name
                elif len(data) < 8:
                    res.national_days.append(tuple([int(item) for item in data.split('-')]))
                else:
                    date = _extract_date(data)
                    res.add_timeperiod(date, date, self._day_type_name)

    def _custom_return(self):
        return self.stack[0]


# ActivitiesXMLReader ##########################################################

class ActivitiesXMLReader(AbstractXMLReader) :
    """
    sax handler to process XML file and create Resource Set object for projman model
    """
    
    def __init__(self):
        AbstractXMLReader.__init__(self)
        self._t_id = None
        self.activities = []

    def _start_element(self, tag, attr):
        """
        See SAX's ContentHandler interface
        """
        if tag == 'activities' :
            self.assert_child_of([None])
        elif tag == 'reports-list':
            self.assert_child_of(['activities'])
            self.assert_has_attrs(['task-id'])
            self._t_id = attr['task-id']
        # set the reports activity
        elif tag == 'report':
            self.assert_child_of(['reports-list'])
            self.assert_has_attrs(['idref','from','to','usage'])
            resource_id = attr['idref']
            begin = _extract_date(attr['from'])
            end = _extract_date(attr['to'])
            usage =  float(attr['usage'])
            task_id = self._t_id
            self.activities.append((begin, end, resource_id, task_id, usage))
        else:
            raise ProjectValidationError(UNKNOWN_TAG)
         
    def _custom_return(self):
        return self.activities

# ScheduleXMLReader ##########################################################

class ScheduleXMLReader(AbstractXMLReader) :
    """
    sax handler to process XML file and create Schedule object to generate
    diagrams
    """
    
    def __init__(self):
        AbstractXMLReader.__init__(self)
        # use only to remember the resource id for task cost by resource
        self.r_id = u''
        self.task_id = None
        self.constraint_type = None
        self.activities = Table(default_value=None,
                                col_names=['begin', 'end', 'resource', 'task',
                                           'usage', 'src'])
        self.tasks = Table(default_value=None,
                           col_names=['begin', 'end', 'status', 'cost', 'unit'])
        self.costs = Table(default_value=None,
                           col_names=['task', 'resource', 'cost', 'unit'])

    def _start_element(self, tag, attr):
        """
        See SAX's ContentHandler interface
        """
        if tag == 'schedule' :
            self.assert_child_of([None])
        elif tag == 'task' :
            self.assert_child_of([None, 'schedule','task'])
            self.assert_has_attrs(['id'])
            self.task_id = attr['id']
            self.tasks.create_row(attr['id'])
            self.stack.append(attr['id'])
        elif tag == 'milestone' :
            self.assert_child_of(['task'])
            self.assert_has_attrs(['id'])
            self.stack.append(attr['id'])
        elif tag == 'status' :
            self.assert_child_of(['task'])
        elif tag == 'report-list':
            self.assert_child_of(['task'])
        elif tag == 'report':
            self.assert_child_of(['report-list'])
            self.assert_has_attrs(['idref', 'from', 'to', 'usage'])
            resource_id = attr['idref']
            begin = _extract_date(attr['from'])
            end = _extract_date(attr['to'])
            usage =  float(attr['usage'])
            self.activities.append_row((begin, end, resource_id, self.task_id, usage))
        elif tag == 'constraint-date':
            self.assert_child_of(['task'])
            self.assert_has_attrs(['type'])
            self.constraint_type = attr['type']
        elif tag == 'constraint-task':
            self.assert_child_of(['task'])
            # FIXME: raise NotImplementedError()
            pass
        elif tag == 'global-cost':
            self.assert_child_of(['task'])
            self.assert_has_attrs(['unit'])
            self.tasks.set_cell_by_ids(self.task_id, 'unit', attr['unit'])
        elif tag == 'costs_list':
            self.assert_child_of(['task'])
        elif tag == 'cost':
            self.assert_child_of(['costs_list'])
            self.assert_has_attrs(['idref'])
            self.r_id = attr['idref']
        elif tag == 'priority':
            pass # ignore for now XXX
        else:
            raise ProjectValidationError(UNKNOWN_TAG)
            
        
    def _end_element(self, tag):
        """
        See SAX's ContentHandler interface
        """
        t_id = self.task_id
        data = u''.join(self._buffer).strip()
        if tag == 'constraint-date':
            date = _extract_date(data)
            if self.constraint_type == BEGIN_AT_DATE:
                self.tasks.set_cell_by_ids(self.task_id, 'begin', date)
            elif self.constraint_type == END_AT_DATE:
                self.tasks.set_cell_by_ids(self.task_id, 'end', date)
        elif tag == 'status':
            self.tasks.set_cell_by_ids(self.task_id, 'status', data)
        elif tag == 'global-cost':
            self.tasks.set_cell_by_ids(self.task_id, 'cost', float(data))
        elif tag == 'cost':
            self.costs.append_row( (t_id, self.r_id, float(data), None) )
        elif tag == 'error':
            self.schedule.errors.append(data)
        #elif tag in ('task', 'milestone'):
        #    self.task_id = self.stack.pop()
        self._buffer = []

    def _custom_return(self):
        return self.activities, self.tasks, self.costs


# ProjectXMLReader #############################################################

class ProjectXMLReader(AbstractXMLReader) :
    """
    sax handler to process XML file and create a Project instance
    """
    
    def __init__(self):
        AbstractXMLReader.__init__(self)
        self.project = self._factory.create_project()
        self.skip_schedule = False

    def _start_element(self, tag, attr) :
        """
        See SAX's ContentHandler interface
        """
        # FIXME: remove code duplication in this method
        # schedules imported
        if tag == 'project':
            self.assert_child_of([None])
        elif tag == 'import-schedule':
            self.assert_child_of(['project'])
            self.assert_has_attrs(['file'])
            try:
                filename = attr['file']
                if not isabs(filename):
                    filename = join(self._base_uris[-1], filename)
                if not self._imported.has_key(filename):
                    p = ScheduleXMLReader()
                    activities, tasks, costs = p.fromFile(filename)
                    self.project.add_schedule(activities)
                    self.project.tasks = tasks
                    self.project.costs = costs
                    self._imported[filename] = 1
            except IOError:
                #TODO: lancer une exception au niveau le plus haut
                #qui lancerait une commande spéciale de 'recovery'
                #puis une commande de schedule puis la commande
                #initiale
                self.skip_schedule = True
                print colorize_ansi("WATCH OUT!", "red"), \
                      "schedule file '%s' declared in project file but is missing. " \
                      "Command completed without scheduling information."% filename, \
                      colorize_ansi("Please, remove reference in projman file", "red")
        # resources imported
        elif tag == 'import-resources' :
            self.assert_child_of(['project'])
            self.assert_has_attrs(['file'])
            filename = attr['file']
            if not isabs(filename):
                filename = join(self._base_uris[-1], filename)
            if not self._imported.has_key(filename):
                p = ResourcesXMLReader()
                rs = p.fromFile(filename)
                self.project.add_resource_set(rs)
                self._imported[filename] = 1
        # activities imported
        elif tag == 'import-activities' :
            self.assert_child_of(['project'])
            self.assert_has_attrs(['file'])
            filename = attr['file']
            if not isabs(filename):
                filename = join(self._base_uris[-1], filename)
            if not self._imported.has_key(filename):
                p = ActivitiesXMLReader()
                a = p.fromFile(filename)
                self.project.add_activities(a)
                self._imported[filename] = 1
        # projects imported
        elif tag == 'import-tasks' :
            self.assert_child_of(['project'])
            self.assert_has_attrs(['file'])
            filename = attr['file']
            if not isabs(filename):
                filename = join(self._base_uris[-1], filename)
            if not self._imported.has_key(filename):
                p = TaskXMLReader()
                task = p.fromFile(filename)
                self.project.root_task = task
                self._imported[filename] = 1
        elif tag == 'import-project' :
            sys.stderr.write('import-project deprecated in favor of import-tasks\n')
            raise ProjectValidationError(UNKNOWN_TAG)
        elif tag == 'projman' :
            sys.stderr.write('projman deprecated in favor of project\n')
            raise ProjectValidationError(UNKNOWN_TAG)
        else :
            raise ProjectValidationError(UNKNOWN_TAG)
        

    def _custom_return(self):
        """ custom return in path """
        return self.project
        
    def characters(self, data) :
        """
        See SAX's ContentHandler interface
        """
        if not self.skip_schedule:
            AbstractXMLReader.characters(self, data)
        else:
            print >> sys.stderr, "skip '%s'" % data
        
    def _end_element(self, tag) :
        """
        See SAX's ContentHandler interface
        """
        if tag == 'import-schedule' and self.skip_schedule:
            self.skip_schedule = False
        

# ProjectFileListReader #############################################################

class ProjectFileListReader(AbstractXMLReader) :
    """
    Initialise the list of files in an instance of ProjectStorage
    from the import-xxx elements in a projman file
    """
    
    def __init__(self, storage):
        AbstractXMLReader.__init__(self)
        self.storage = storage

    def exists(self, path):
        """check file exists after applying repo on it"""
        path = self.storage.from_repo(path)
        return os.path.exists(path)
    
    def _start_element(self, tag, attr) :
        # FIXME: cyclic import
        from projman.interface.file_manager import RESOURCES_KEY, TASKS_KEY, \
             ACTIVITIES_KEY, SCHEDULE_KEY
        if tag == 'project' :
            self.assert_child_of([None])

        elif tag == 'import-schedule':
            self.assert_child_of(['project'])
            self.assert_has_attrs(['file'])
            file_name = attr['file']
            if not self.exists(file_name):
                raise ValueError("Wrong import in '%s': file '%s' does not exist"\
                                 % (self.storage.from_projman(), file_name))
            self.storage.set_schedule(file_name)

        elif tag == 'import-resources' :
            self.assert_child_of(['project'])
            self.assert_has_attrs(['file'])
            file_name = attr['file']
            if not self.exists(file_name):
                raise ValueError("Wrong import in '%s': file '%s' does not exist"\
                                 % (self.storage.from_projman(), file_name))
            self.storage.set_resources(file_name)

        elif tag == 'import-activities' :
            self.assert_child_of(['project'])
            self.assert_has_attrs(['file'])
            file_name = attr['file']
            if not self.exists(file_name):
                raise ValueError("Wrong import in '%s': file '%s' does not exist"\
                                 % (self.storage.from_projman(), file_name))
            self.storage.set_activities(file_name)

        elif tag == 'import-tasks' :
            self.assert_child_of(['project'])
            self.assert_has_attrs(['file'])
            file_name = attr['file']
            if not self.exists(file_name):
                raise ValueError("Wrong import in '%s': file '%s' does not exist"\
                                 % (self.storage.from_projman(), file_name))
            self.storage.set_tasks(file_name)

        elif tag == 'import-project' :
            sys.stderr.write('import-project deprecated in favor of import-tasks\n')
            raise ProjectValidationError(UNKNOWN_TAG)
        elif tag == 'projman' :
            sys.stderr.write('projman deprecated in favor of project\n')
            raise ProjectValidationError(UNKNOWN_TAG)
        else:
            raise ProjectValidationError(UNKNOWN_TAG)

    def _custom_return(self):
        return self.storage

def _extract_date(date):
    """
    Extract DateTime object from string
    """
    # FIXME: use Parser.FromString()
    return DateTime(int(date[:4]), int(date[5:7]), int(date[8:]))


def _extract_time(time):
    """
    Extract DeltaTime object from string
    """
    # FIXME: use Parser.FromString()
    return Time(float(time[0:2]), float(time[2:-1]))

            
def guess_format(txt):
    """ really trivial function to determine if input string has xml in or not """
    if '<' in txt:
        return 'xml'
    else:
        return 'rest'


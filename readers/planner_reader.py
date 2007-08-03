# Copyright (c) 2004-2006 LOGILAB S.A. (Paris, FRANCE).
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
""" methods and objects to import planner files """

__revision__ = "$Id: planner_reader.py,v 1.2 2005-11-09 16:47:36 arthur Exp $"

from xml.sax import make_parser, ContentHandler

from projman.lib._exceptions import ProjectValidationError
from projman.readers.base_reader import AbstractXMLReader
from projman.lib.constants import \
     BEGIN_AFTER_END, BEGIN_AFTER_BEGIN, END_AFTER_END, END_AFTER_BEGIN, \
     BEGIN_AFTER_DATE, BEGIN_AT_DATE, BEGIN_BEFORE_DATE, \
     END_AFTER_DATE, END_AT_DATE, END_BEFORE_DATE
from projman.lib._exceptions import ProjectValidationError

UNKNOWN_TAG = 'file %s line %s : Unknown tag %s'

from mx.DateTime import DateTime, Time, now
import sys

# Planner File Reader ###########################################

class PlannerXMLReader(AbstractXMLReader) :      
    """ A sax handler to read an XML file from Planner and create 
        projman objects """

    def __init__(self):
        AbstractXMLReader.__init__(self)
        self.activities_path = []
        self.project_path = []
        self.resource_path = []
        self.day_dict = {}
        self.last_overridden = 0
        self.calendar = {}
        self.default_week = {}
        self._type_of_days = {}
        self._type_intervals = {}
        self._default_calendar = ''
        # sequence that store all the tasks that need re_evaluating
        # (generally those with fixed-work scheduling and not fixed-duration)
        self.re_evaluate = []

    def _start_element(self, tag, attr) : 
        """ See SAX's ContentHandler interface """
        # project ##
        if tag == 'project':
            p = self._factory.create_project() 
            p.title = attr['name']
            default_begin = now().date.replace('-', '')
            begin_project = attr.get('project-start', default_begin) \
                            or default_begin
            date = self._extract_date(begin_project)
            p.root_task = self._factory.create_task('p_%s'%attr['name'])
            p.root_task.add_date_constraint(BEGIN_AT_DATE, date)
            self.project_path.append(p)
            rs = self._factory.create_resourcesset('all_resources')
            self.resource_path.append(rs)

        # day type ##
        elif tag == 'day-type' :
            if 'd_'+attr['id'] not in self._type_of_days:
                self._type_of_days['d_'+attr['id']] = attr['name']

        # resource ##
        elif tag == 'resource' :
            r_type = attr.get('type', '') or self._default_type
            r_cost = attr.get('std-rate', '0.0')
            r_calendar = 'c_'+attr.get('calendar', '') or ''
            if r_calendar == 'c_':
                r_calendar = ''
            if r_calendar == 'c_':
                r_calendar = None
            r = self._factory.create_resource('r_' + attr['id'], \
                    attr['name'], r_type, r_calendar, r_cost)
            #add resource in resource set object
            self.resource_path[-1].append(r)
            self.resource_path.append(r)
            # add resource id in project resources list
            self.project_path[0].resources.append('r_' + attr['id'])

        # calendar ##
        elif tag == 'calendar' :
            tt_inherits = None
            if self.resource_path \
                   and self.resource_path[-1].TYPE == 'calendar':
                tt_inherits = self.resource_path[-1].id 
            tt = self._factory.create_calendar('c_' + attr['id'], \
                    attr['name'])
            tt.type_working_days = {}
            tt.type_nonworking_days = {}
            self.resource_path[-1].append(tt)
            self.resource_path.append(tt)

        # task ##
        elif tag == 'task':
            default_begin = now().date.replace('-', '')
            date_begin = attr.get('start', default_begin) or default_begin
            begin_date = self._extract_date(date_begin)

            default_end = (now()+1).date.replace('-', '')
            date_end = attr.get('end', default_end) or default_end
            end_date = self._extract_date(date_end)
            if attr['type'] == 'milestone':
                t = self._factory.create_milestone('t_' + attr['id'])
            elif attr['type'] == 'normal' :
                t = self._factory.create_task('t_' + attr['id'])
                # ignore lag attr['lag']
                total_hours = 8
                for id in self._type_intervals:
                    if self._type_intervals[id][0] == 'Working' \
                           and id == self._default_calendar:
                        total_hours = self._get_total_hours(self._type_intervals[id])
                        flag = 1
                # in the cas of fixed-work ##
                duration_work = attr['work']
                if attr['scheduling'] == 'fixed-work':
                    self.re_evaluate.append('t_' + attr['id'])
                    t.duration = duration_work
                elif attr['scheduling'] == 'fixed-duration':
                    t.duration = self._interval_days(begin_date, end_date)

            if attr.get('percent-complete'):
                t.progress = float(attr['percent-complete']) / 100
            t.title = attr['name']
            t.add_date_constraint(BEGIN_AT_DATE, begin_date)
            t.add_date_constraint(END_AT_DATE, end_date)
            self.project_path[-1].append(t)
            self.project_path.append(t)

        # task dependance ##
        elif tag == 'predecessor':
            pre_type = self._translate_predecessor(attr['type'])
            ct_id = str(attr['predecessor-id'])
            self.project_path[-1].add_task_constraint(pre_type, 't_' + ct_id)

        # date constraint ##
        elif tag == 'constraint':
            type = None
            if attr['type'] == 'must-start-on':
                type = BEGIN_BEFORE_DATE
            elif attr['type'] == 'start-no-earlier-than':
                type = BEGIN_AFTER_DATE
            date = self._extract_date(attr['time'])
            self.project_path[-1].add_date_constraint(type, date)


        # resource allocation ##
        elif tag == 'allocation' :
            target_task = int(attr['task-id'])
            resource = 'r_'+attr['resource-id']
            usage = int(attr['units'])
            #find type
            type = self.resource_path[0].get_resource(resource).type
            #goto find the target_task to do
            children_seq = self.project_path[0].children
            self.add_allocation(children_seq, target_task, type, resource, usage)
            # translate resource allocation in activties reports
            t_id = 't_'+str(target_task)
            task = self.project_path[0].get_node_by_id(t_id)
            t_begin = task.date_constraints[BEGIN_AT_DATE] or now()
            t_end = task.date_constraints[END_AT_DATE] or now()
            self.project_path[0].add_activity(t_begin, t_end, resource, t_id, usage)
        # internal day-type info ##
        elif tag == "overridden-day-type" :
            self.last_overridden = self.resource_path[-1].id+'_d_'+attr['id']
            if self.last_overridden not in self._type_intervals:
                self._type_intervals[self.last_overridden] = \
                            [self._type_of_days['d_'+attr['id']]]

        # internal day-type info - length ##
        elif tag == "interval" :
            start = Time(float(attr['start'][0:2]), float(attr['start'][2:-1]))
            end = Time(float(attr['end'][0:2]), float(attr['end'][2:-1]))
            self._type_intervals[self.last_overridden].append((start, end))
            if self._default_calendar == '':
                self._default_calendar = self.last_overridden

        elif tag == 'days' :
            # add day type information for each calendar
            for type_of_day in self._type_of_days:
                c = self.resource_path[-1]
                # set all type of days in working days type and nonworking days type
                if c.id+'_'+type_of_day in self._type_intervals:
                    ## in this case time intervals defines
                    c.type_working_days[len(c.type_working_days)] = \
                         [self._type_of_days[type_of_day],
                          self._type_intervals[c.id+'_'+type_of_day][1:]]
                    if self._type_of_days[type_of_day] == 'Working':
                        id = len(c.type_working_days) - 1
                        c.default_working = id

                else:
                    ## look if type_of_day contains intervals in all parents
                    ## if it is not the case add in non working days
                    child = c
                    parent = child.parent
                    nonworking = True
                    while nonworking and parent.TYPE == 'calendar':
                        if parent.id+'_'+type_of_day in self._type_intervals:
                            nonworking = False
                            c.type_working_days[len(c.type_working_days)] = \
                                [self._type_of_days[type_of_day],
                                 self._type_intervals[parent.id+'_'+type_of_day][1:]]
                            if self._type_of_days[type_of_day] == 'Working':
                                id = len(c.type_working_days) - 1
                                c.default_working = id
                        child = parent
                        parent = child.parent
                    if nonworking:
                        c.type_nonworking_days[len(c.type_nonworking_days)] = \
                                                     self._type_of_days[type_of_day]
                        if self._type_of_days[type_of_day] == 'Nonworking':
                            id = len(c.type_nonworking_days) - 1
                            c.default_nonworking = id

        # day info ##
        elif tag == "day":
            if attr['id'] in self.day_dict:
                self.calendar[self._extract_date(attr['date'])] = \
                    self.day_dict[attr['id']]
            if attr['type'] == 'day-type':
                date = self._extract_date(attr['date'])
                self.resource_path[-1].add_timeperiod(date,
                                                      date,
                                                      self._type_of_days['d_'+attr['id']])


        # default week info ##
        elif tag == 'default-week' :
            cal = self.resource_path[-1]
            if attr['mon'] != '2':
                cal.weekday['mon'] = self._type_of_days['d_'+attr['mon']]
            if attr['tue'] != '2':
                cal.weekday['tue'] = self._type_of_days['d_'+attr['tue']]
            if attr['wed'] != '2':
                cal.weekday['wed'] = self._type_of_days['d_'+attr['wed']]
            if attr['thu'] != '2':
                cal.weekday['thu'] = self._type_of_days['d_'+attr['thu']]
            if attr['fri'] != '2':
                cal.weekday['fri'] = self._type_of_days['d_'+attr['fri']]
            if attr['sat'] != '2':
                cal.weekday['sat'] = self._type_of_days['d_'+attr['sat']]
            if attr['sun'] != '2':
                cal.weekday['sun'] = self._type_of_days['d_'+attr['sun']]
        else :
            raise ProjectValidationError(UNKNOWN_TAG)

    def _custom_return(self):
        """ customize the returned value according to reader you are in"""
        projman = self._factory.create_projman()
        projman.projects = self.project_path
        projman.resource_sets = self.resource_path
        return projman


    def endElement(self, tag) :
        """
        See SAX's ContentHandler interface
        """
        if tag in ('resource', 'calendar'):
            self.resource_path.pop()
        elif tag in ('task'):
            task = self.project_path.pop()

    def endDocument(self):
        """
        See SAX's ContentHandler interface
        """
        self._re_evaluate_all(self.project_path[0].children)

    def _translate_predecessor(self, type):
        """ Translate Planner representation to projman representation
                SS: BEGIN_AFTER_BEGIN,
                SF: END_AFTER_BEGIN,
                FS: BEGIN_AFTER_BEGIN,
                FF: END_AFTER_END}
        """
        dict = {'ss':BEGIN_AFTER_BEGIN,
                'sf':END_AFTER_BEGIN,
                'fs':BEGIN_AFTER_END,
                'ff':END_AFTER_END}
        return dict[type.lower()]

    def add_allocation(self, children_seq, target_task, a_type, resource, usage):
        """ recursively adds a single allocation (resource_constraint) """
        for each in children_seq:
            #allocation only possible for tasks - loose information from
            #planner
            if each.id == 't_' + str(target_task) and each.TYPE == 'task':
                each.add_resource_constraint(a_type, resource, usage)
                return
            else : 
                self.add_allocation(each.children, target_task, \
                    a_type, resource, usage)

    def _extract_date(self, date):
        """ Extract Planner date """
        return DateTime(int(date[:4]), int(date[4:6]), int(date[6:8]))


    def _interval_length(self, start, finish):
        """ Calculates the interval length in seconds from an hour interval """
        finish_s = (int(finish[:2]) * 3600) + (int(finish[2:]) * 60)
        start_s = (int(start[:2]) * 3600) + (int(start[2:]) * 60)
        return finish_s - start_s 

    def _re_evaluate_all(self, children_seq):
        """ 
        re-evaluate all durations after parsing is finished
        so as to take into account the resources and their 
        calendars 
        """
        for each in children_seq:
            if each.TYPE != 'milestone':
                begin, end = each.get_date_range()
                if begin and end and each.id in self.re_evaluate :
                    each.duration = self._evaluate_duration(begin, end, each)
                if each.children:
                    self._re_evaluate_all(each.children)

    def _evaluate_duration(self, begin, end, task):
        """ evaluates the duration for a single task """
        days = 0
        current_date = begin
        resource_set = self.resource_path[0]
        duration_in_seconds = int(float(task.duration))
        while current_date <= end:
            for res_type, res_id, usage in task.resource_constraints:
                res = resource_set.get_resource(res_id)
                daily_duration = res.get_duration_of_work(current_date)
                if daily_duration:
                    days += 1
                    duration_in_seconds -= daily_duration * int(usage) / 100
                if duration_in_seconds <= 0:
                    break
            if duration_in_seconds <= 0:
                break
            current_date += 1
        return days


    def _interval_days(self, begin, end):
        """ Calculates the number of working days between two dates """
        days = 0
        current_date = begin
        while current_date <= end:
            if current_date.day_of_week not in (5, 6):
                days += 1
            current_date += 1
        return days

    def _get_weekday_type(self, resourcesset, cal_id, weekday, type):
        """ return the type of weekday according to inherits priority """
        cal = resourcesset.get_calendar(cal_id)
        if type == '2':
            return self._get_weekday_type(resourcesset, \
                cal.parent.id, weekday,\
                resourcesset.get_calendar(cal.parent.id).weekday[weekday])
        else:
            return type


    def _get_total_hours(self, intervals):
        """
        return the total number of hours for intervals
        """
        hours = 0
        for index in range(1, len(intervals)):
            begin = intervals[index][0]
            end = intervals[index][1]
            hours += end - begin
        hours_as_float = hours.hours + float(hours.minute)/60
        return hours_as_float


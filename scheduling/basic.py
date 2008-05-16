# Copyright (c) 2000-2005 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
base scheduling visitors
"""

__revision__ = "$Id: basic.py,v 1.2 2005-09-08 14:26:06 nico Exp $"

import sys

from logilab.common.visitor import Visitor
from logilab.common.tree import PostfixedDepthFirstIterator

from projman.lib import date_range
from projman.lib.constants import *
from mx.DateTime import now, DateTimeFromAbsDateTime
                

def add_week_days(date, days):    
    """
    adds a number of days taking into account weekends
    """
    #short circuit - taking into consideration weekends doesn't seem necessary
    return date + days
##     day_of_week = date.day_of_week
##     days_left = 4 - day_of_week
##     if days <= days_left:
##         return date+days
##     weeks = days // 5
##     days_left = days % 5
##     date += 7 * weeks
##     if days_left:
##         if date.day_of_week + days_left >= 5:
##             date += 2 + days_left
##         else:
##             date += days_left
##     return date

def sub_week_days(date, days):
    # quick and dirty since it is not used often
    weeks = days // 5
    remain = days % 5
    return date - (7 * weeks) - remain

def split_to_fit_disponibility(activity, resource, a_seq=None):
    """
    Takes an activity and returns a sequence of activities that 
    take into account the days the resource cannot work
    """
    if a_seq is None:
        a_seq = []
    begin = activity.begin
    date = begin
    end = activity.end
    while date <= end :
        if resource.is_available(date): 
            date += 1
        else: 
            if date != activity.begin:
                a_seq.append( (begin, date-1, activity.usage) )
            begin = date
            end += 1
    a_seq.append( (begin, date-1, activity.usage) )
    return a_seq

# Basic Scheduling visitor ####################################################

class BasicScheduler(Visitor):
    """
    The first step schedule visitor
    
    get the ASAP begin and end date for each task of the tree
    """
    
    def __init__(self, project):
        """
        create a BasicScheduler. Use open_visit() to start.
        """
        Visitor.__init__(self, PostfixedDepthFirstIterator)
        self._root = None
        self.errors = []
        self.project = project
        self._past_activities = Table()
        self._current_schedule = None

    def schedule(self, verbose=1, **kw):
        """
        Try to update the current_schedule using data from project
        and activities.
        
        Return project_errors
        """
        self.errors = []
        self._schedule = self.project.schedule
        return self.visit(self.project.root_task)

    # visitor API #############################################################
    
    def open_visit(self, node):
        self._root = node

    def close_visit(self, result):
        return self.errors
    
    def visit_project(self, node):
        # FIXME - is this really useful?
        if node.parent is None:
            schedule = self.project.get_schedule(node.id) 
            assert schedule is not None
            
        self.visit_task(node)
       
        if node.parent is None:
            begin, end = self.project.get_date_range(node)
            schedule.global_begin = begin
            schedule.global_end = end
    
    def visit_milestone(self, node):
        if hasattr(node, 'scheduled'):
            return
        node.scheduled = 1
        
        if node.children:
            raise ValueError , "Milestone can't have children"
        else :
            self.schedule_milestone(node)
   
    def visit_task(self, node):
        if hasattr(node, 'scheduled'):
            return
        node.scheduled = 1        
        if node.children:
            self.schedule_container(node)
        else :
            self.schedule_leaf(node)
        begin, end = self.project.calculate_date_range(node)
        self._current_schedule.tasks_timeslot[node.id] = [begin, end]
        # set also global_tasks_cost and tasks_cost_by_resource
        all_activities = self._current_schedule._merge_activities.select('task', node.id)
        #  compute the global cost of task according to time-slots and resources cost
        global_cost = 0.0
        unit = 'euros'
        for r_id in all_activities:
            r = self.project.get_resource(r_id)
            hours_per_day = r.get_default_wt_in_hours()
            list_activity = all_activities[r_id]
            hours = 0.0
            nb_days = 0.0
            for activity in list_activity:
                d = activity.begin
                loop_count = 0
                while d <= activity.end:
                    worked_hours = (r.get_duration_of_work(d) / 3600.) * activity.usage
                    # FIXME XXX infiniteloop BUG prevention
                    if loop_count == 100:
                        break
                    if worked_hours == 0 and r.is_available(d):
                        break
                    hours += worked_hours
                    d += worked_hours/hours_per_day
                    nb_days += worked_hours/hours_per_day
                    loop_count += 1
            r_hourly_rate = r.hourly_rate[0]
            unit = r.hourly_rate[1]
            global_cost += hours * r_hourly_rate
            # update cost in resource
            task_cost_by_resource = self._current_schedule.tasks_cost_by_r.setdefault(node.id, {})
            task_cost_by_resource[r_id] = task_cost_by_resource.get(r_id, 0) + nb_days
            
        # update cost in schedule
        if node.id not in self._current_schedule.tasks_global_cost:
            if global_cost != 0:
                self._current_schedule.tasks_global_cost[node.id] = [global_cost, unit]
        else:
            #FIXME need currency converter if unit != global_unit
            assert self._current_schedule.tasks_global_cost[node.id][1] == unit, \
                   "Panic: we don't support different units yet"
            self._current_schedule.tasks_global_cost[node.id][0] += global_cost

    # methods for the real job ################################################

    def schedule_container(self, node):
        """
        set begin and end for a container task according to its children tasks
        """
        # simply define begin and end
        begin, end = self.project.get_container_date_range(node, 
                                                   self._current_schedule) 
        if begin and end:
            self._current_schedule.tasks_timeslot[node.id] = [begin, end]
        else:
            sys.stderr.write('warning... unscheduled leaves!\n')
        
        
    def schedule_milestone(self, node) :
        """ 
        get node begin / end date
        set time slots according to estimated begin and end of the task
        """
        for tc_type in TASK_CONSTRAINTS:
            n_cons = self.project.get_task_constraints(node.id,
                                                        fill = TASK_CONSTRAINTS) 
            if tc_type in n_cons:
                for task_id in n_cons[tc_type]:
                    if node.get_node_by_id(task_id) is not None:
                        v = BasicScheduler(self.project)
                        v.visit(node.get_node_by_id(task_id), 
                                self._past_activities,
                                self._current_schedule)
                        self.errors += v.errors
        date, date_strict = self.get_possible_begin(node)
        self._current_schedule.tasks_timeslot[node.id] = [date, date]
        # FIXME is activity really necessary? check usage by renderer
        self._current_schedule.planned_activities.add_activity(node.id, '',
                                                               Activity(100, date, date))
    
    def schedule_leaf(self, node) :
        """ 
        get node begin / end date
        set time slots according to estimated begin and end of the task
        """
        if node.is_finished(self.project.get_activity_by_t(node.id)):
            self._current_schedule.tasks_status[node.id] = 'done'
        else:
            planned_activities = self._current_schedule.planned_activities
            # schedule all constrained task
            for tc_type in TASK_CONSTRAINTS:
                n_cons = self.project.get_task_constraints(node.id,
                                                            fill=TASK_CONSTRAINTS)
                for task_id in n_cons.get(tc_type, []):
                    task = node.get_node_by_id(task_id)
                    if task is not None:
                        v = BasicScheduler(self.project) # !?!
                        v.visit(task, self._past_activities,
                                self._current_schedule)
                        self.errors += v.errors
            # calculate edges
            begin, begin_strict = self.get_possible_begin(node)
            end, end_strict = self.get_possible_end(node)
            nb_days = node.duration
            res_seq = node.get_resources()
            # include duration of past activities in schedule
            nb_days -= self._past_activities.get_duration_worked_for_t(node.id)
            # cut up according to days worked
            date = begin
            end_limit = end_strict and end or end + 365
            # FIXME we end up having a great number of daily activities.
            while date <= end_limit:
                # calculate global disponibility at 'date'
                dispo = {}
                for resource in res_seq: 
                    dispo[resource] = min(
                        self.project.get_general_disponibility(resource, date),
                        node.get_resource_dispo(resource))
                sum_d = sum(dispo.values())
                # dispo sufficient to finish task: spread out activity among resources
                if nb_days - sum_d < -FLOAT_ZERO:
                    #FIXME TODO : if a resource available less than spread out 
                    #value... then you have more on the others (end up needing
                    #an extra day etc...)
                    used_resources = dispo.keys()
                    ideal_usage = nb_days*1./len(used_resources)
                    for resource in used_resources:
                        real_usage = min(ideal_usage, dispo[resource])
                        planned_activities.add_activity(date, date, resource, node.id, real_usage)
                        nb_days -= real_usage
                # dispo not sufficient: std option, fill in full days
                else:
                    for resource, usage in dispo.items():
                        if usage:
                            planned_activities.add_activity(date, date, resource, node.id, usage)
                            nb_days -= usage
                # task filled with activities, break
                if nb_days <= FLOAT_ZERO:
                    break
                date += 1
            # check that task has been complete (all days in duration linked to an activity)
            if nb_days > FLOAT_ZERO:
                self.errors.append('Unable to fit all days required before end date of %s (%s)' \
                                   % (node.id, nb_days))
                self._current_schedule.tasks_status[node.id] = 'problem'
                node.problem = True
           
    def get_possible_begin(self, node):
        """
        return the possible begin date of the task
        
        check for constraints inconsistency, remove broken constraints
        """
        pl_act = self._current_schedule.planned_activities 
        begin = None
        date_cs = node.get_date_constraints(fill = DATE_CONSTRAINTS)
        # set this variable to 1 if the begin date can not be later
        strict = None
        TODAY = now()

        # check begin-at / end-at date constraints
        if date_cs[BEGIN_AT_DATE] is not None:
            # remove end-at-date constraint if any
            if date_cs[END_AT_DATE] is not None:
                date_cs[END_AT_DATE] = None
            date = date_cs[BEGIN_AT_DATE]
            if begin is not None and date != begin  or date < TODAY:
                self.remove_constraint(node, BEGIN_AT_DATE,
                                       date_cs[BEGIN_AT_DATE])
                date_cs[BEGIN_AT_DATE] = None
            else:
                strict = 1
                begin = date
        elif date_cs[END_AT_DATE]:
            date = date_cs[END_AT_DATE]
            if node.TYPE == 'milestone':
                begin_est = date
            else : 
                begin_est = sub_week_days(date, \
                        node.remaining_duration()) #self.project))
            if begin is not None and not begin_est == begin or begin < TODAY:
                self.remove_constraint(node, END_AT_DATE,
                                       date_cs[END_AT_DATE])
                date_cs[END_AT_DATE] = None
            else:
                strict = 1
                begin = begin_est

        if begin is None:
            begin = TODAY
                
        # check other begin-date constraints
        if date_cs[BEGIN_AFTER_DATE] is not None:
            if begin < date_cs[BEGIN_AFTER_DATE] and strict is not None:
                self.remove_constraint(node, BEGIN_AFTER_DATE,
                                       date_cs[BEGIN_AFTER_DATE])
                date_cs[BEGIN_AFTER_DATE] = None
            else:
                begin = date_cs[BEGIN_AFTER_DATE]

        if date_cs[BEGIN_BEFORE_DATE] is not None and strict is not None:
            if begin > date_cs[BEGIN_BEFORE_DATE]:
                self.remove_constraint(node, BEGIN_BEFORE_DATE,
                                       date_cs[BEGIN_BEFORE_DATE])
                date_cs[BEGIN_BEFORE_DATE] = None
            else:
                strict = 1

        # check begin-after-end task constraints
        node_cons = self.project.get_task_constraints(node.id, fill = TASK_CONSTRAINTS)
        #self.logger.debug(" -- [%s] task constraints=%s"% (node.id, str(node_cons)))
        new = []
        for task_id in node_cons[BEGIN_AFTER_END]:
            task = node.get_node_by_id(task_id) 
            if task is not None:
                date_end = self.adjust(pl_act.get_end(task), task) or now()
                task_end = date_end
                if begin <= task_end:
                    if strict is not None:
                        self.remove_constraint(node, BEGIN_AFTER_END, task_id)
                    else:
                        new.append(task_id)
                        begin = task_end 
                else:
                    new.append(task_id)
            else:
                pass
        node_cons[BEGIN_AFTER_END] = new
        #XXX TODO:  BEGIN_BEFORE_DATE ???

        # check begin-after-begin task constraints
        new = []
        for task_id in node_cons[BEGIN_AFTER_BEGIN]:
            if node.get_node_by_id(task_id) is not None:
                task = node.get_node_by_id(task_id)
                date_begin = pl_act.get_begin(task) or now() 
                task_begin = date_begin
                if begin < task_begin:
                    if strict is not None:
                        self.remove_constraint(node, 
                                               BEGIN_AFTER_BEGIN, 
                                               task_id)
                    else:
                        new.append(task_id)
                        begin = (DateTimeFromAbsDateTime(task_begin) \
                                  + 1)
                else:
                    new.append(task_id)
            else:
                pass
        node_cons[BEGIN_AFTER_BEGIN] = new
        begin = DateTimeFromAbsDateTime(begin)
        node.scheduled = begin
        return begin, strict

    def get_possible_end(self, node):
        """
        return the estimated end of the task
        
        check for constraints inconsistency, remove broken constraints
        you must call get_possible_begin before get_possible_end
        """
        assert node.scheduled
        pl_act = self._current_schedule.planned_activities 
        date_cs = node.get_date_constraints(fill = DATE_CONSTRAINTS)
        end = node.scheduled + max(0, node.remaining_duration()) #self.project))
        # set this variable to 1 if the begin date can not be latter
        strict = None
            
        # check date constraints
        if date_cs[END_AFTER_DATE] is not None:
            if end < date_cs[END_AFTER_DATE]:
                self.remove_constraint(node, END_AFTER_DATE,
                                       date_cs[END_AFTER_DATE])
                date_cs[END_AFTER_DATE] = None
            else:
                strict = 1
                end = date_cs[END_AFTER_DATE]

        if date_cs[END_BEFORE_DATE] is not None and \
               end > date_cs[END_BEFORE_DATE]:
            self.remove_constraint(node, END_BEFORE_DATE,
                                   date_cs[END_BEFORE_DATE])
            date_cs[END_BEFORE_DATE] = None
        #XXX TODO:  END_AT_DATE ???
                    
        # check task constraints
        node_cons = self.project.get_task_constraints(node.id, 
                                            fill = TASK_CONSTRAINTS)
        new = []
        for task_id in node_cons[END_AFTER_END]:
            task = node.get_node_by_id(task_id) 
            if task is not None:
                date_end = pl_act.get_end(task) or now()
                task_end = date_end
                if end < task_end:
                    if strict is not None:
                        self.remove_constraint(node, END_AFTER_END, task_id)
                    else:
                        new.append(task_id)
                        end = task_end
                else:
                    new.append(task_id)
        node_cons[END_AFTER_END] = new
        
        new = []
        for task_id in node_cons[END_AFTER_BEGIN]:
            if node.get_node_by_id(task_id) is not None:
                date_begin = pl_act.get_begin(task) or now()
                task_begin = date_begin
                if end < task_begin:
                    if strict is not None:
                        self.remove_constraint(node, END_AFTER_BEGIN, task_id)
                    else:
                        new.append(task_id)
                        end = task_begin
                else:
                    new.append(task_id)
        node_cons[END_AFTER_BEGIN] = new
        return end, strict
            
    def remove_constraint(self, node, c_type, c_value):
        """
        notify that an unsatisfable constraint has been removed
        """
        self.errors.append('remove %s %s constraint on %s' % (
            c_type, c_value, node.id))
        self._current_schedule.tasks_status[node.id] = 'problem'
        node.problem = True
    
    def adjust(self, date, task):
        """
        checks preceding days if resources are fully used, if not 
        return previous day
        """
        # define result var in order to ease logging
        result = date or None
        # no adjusting can be done with a dependency on a milestone
        if task.TYPE != 'milestone':
            for res_id in task.get_resources():
                dispo = self.project.get_general_disponibility(res_id, date - 1)
                usage = task.get_resource_dispo(res_id)
                if dispo - usage > 0:
                    result = date - 1
        return result


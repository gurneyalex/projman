# -*- coding: utf-8 -*-
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
""" schedule project using Constraint Solving Programing """

__revision__ = "$Id: csp.py,v 1.2 2005-09-07 23:51:01 nico Exp $"

from mx.DateTime import today

from logilab.common.compat import set
from projman.lib.constants import *
from gcsp import ProjmanProblem, solve


class CSPScheduler:
    """
    schedule a project using constraint programming
    
    variables = leaf tasks of the project
    values = (timeslotsset, resource)
    """
    def __init__(self, project):
        self.project = project
        self.start_date = None
        self.calc_project_length()
        
        self.real_tasks = {}  # task_id -> (task_number,duration,list_of_resources)
        self.pseudo_tasks = [] # pseudo number -> (task_id, resource_id)
        self.constraints = {} # Constraint Type -> list of task pairs
        self.task_ranges = {} # task_id -> date range or (None,None)
        self.resources = {}   # res_id -> res_number
        for leaf in project.root_task.leaves():
            self._process_node(leaf)
           
        #self.add_priorities_as_constraints()

    def calc_project_length(self):
        """Computes start_date and max_duration (duration of the project)"""
        max_duration = self.project.root_task.maximum_duration()
        begins, ends = [], []
        for leaf in self.project.root_task.leaves():
            for c_type, date in leaf.get_date_constraints():
                if c_type in (BEGIN_AT_DATE, BEGIN_AFTER_DATE):
                    begins.append(date)
                elif c_type in (END_AT_DATE, END_BEFORE_DATE):
                    ends.append(date)
        if not self.start_date:
            # We take the earliest date constraint as a start date
            if begins:
                self.start_date = min(begins)
            elif ends:
                self.start_date = min(ends)
            else:
                self.start_date = today()
        # advance start date to the first working day
        d = self.start_date
        while True:
            print "Trying", d
            for res_id in self.project.get_resources():
                res = self.project.get_resource(res_id)
                if res.work_on( d ):
                    break
            else:
                d = d + 1
                continue
            break
        self.start_date = d
        if ends and begins:
            other_length = (max(ends) - min(begins)).days +1
        else:
            other_length = 0
        self.max_duration = max(max_duration, other_length)


    def _process_node(self, node):
        max_duration = self.max_duration
        task_num, _, task_resources = self.real_tasks.setdefault( node.id,
                                                                  (len(self.real_tasks),
                                                                   node.duration, []) )
        rnge = self.task_ranges.setdefault( node.id, [None,None] )

        # collect task constraints
        for constraint_type, task_id in node.get_task_constraints():
            for leaf in node.get_task(task_id).leaves():
                lst = self.constraints.setdefault(constraint_type, set())
                nodes = sorted( [node.id, leaf.id] )
                lst.add(tuple(nodes))
        # collect date constraints
        for c_type, date in node.get_date_constraints():
            days = (date-self.start_date).days
            if days<0:
                raaaah
            if c_type == BEGIN_AFTER_DATE :
                rnge[0] = days
                print node.id, 'begin after', days
            elif c_type == END_BEFORE_DATE :
                rnge[1] = days + 1
                print node.id, 'end before', days
        # collect resources
        for r_type, r_id, usage in node.get_resource_constraints():
            # keep usage around in case we use it one day
            print "Resource", r_type, r_id, usage
            r_num = self.resources.setdefault( r_id, len(self.resources) )
            task_resources.append( (r_num, usage) ) 
            
            
    def add_priorities_as_constraints(self):
        """
        transform priorities as BEGIN_AFTER_END constraints
        """
        return # XXXX
        lbp = {}
        for task in self.project.root_task.leaves():
            lbp.setdefault(task.priority, []).append(task)
        priorities = lbp.keys()
        priorities.sort()
        for (low, high) in zip(priorities[:-1], priorities[1:]):
            for low_leaf in lbp[low]:
                for high_leaf in lbp[high]:
                    self.constraints.add(fi.StartsAfterEnd(high_leaf.id,
                                                           low_leaf.id))
    
    def schedule(self, verbose=0):
        """
        Update the project's schedule
        Return list of errors occured during schedule
        """
        
        print "Tasks", len(self.real_tasks)
        print "Res", len(self.resources)
        print "Dur", self.max_duration
        pb = ProjmanProblem( len(self.real_tasks),
                             len(self.resources),
                             int(self.max_duration) )
        pseudo_tasks = {}
        for tid, (num, duration, resources) in self.real_tasks.items():
            pb.set_duration( num, int(duration) )
            rnge = self.task_ranges[tid]
            print "Task %2d = #%2d [%4s,%4s]" % ((num,duration)+tuple(rnge))
            if rnge[0] is not None:
                pb.set_low( num, int(rnge[0]) )
            if rnge[1] is not None:
                pb.set_high( num, int(rnge[1]) )

            if duration==0:
                continue
            for res,usage in resources:
                pid = pb.alloc(num, res)
                print "Task % 2d %12s (%2d/%2d) = %d" % (pid, tid, num, res, duration)
                lst = pseudo_tasks.setdefault( tid, [] )
                lst.append( (pid,res) )

        def _reg_csp( func, pairs ):
            """register constraint for pairs of tasks.
            effectively register the constraint for all combinations
            of pseudo tasks (task,res) couples
            """
            for t1,t2 in pairs:
                n1, _, _ = self.real_tasks[t1]
                n2, _, _ = self.real_tasks[t2]
                func( n1, n2 )
                print "%s %s(%s), %s(%s)" %(func.__name__, t1, n1, t2, n2)

        cs = self.constraints
        #print cs
        _reg_csp( pb.begin_after_end, cs.get(BEGIN_AFTER_END,[]) )
        _reg_csp( pb.end_after_end, cs.get(END_AFTER_END,[]) )
        _reg_csp( pb.begin_after_begin, cs.get(BEGIN_AFTER_BEGIN,[]) )
        _reg_csp( pb.end_after_begin, cs.get(END_AFTER_BEGIN,[]) )

        for res_id, res_num in self.resources.items():
            res = self.project.get_resource( res_id )
            print "%02d" % res_num,
            for d in range(self.max_duration):
                dt = self.start_date + d
                #print dt
                if not res.work_on( dt ):
                    pb.add_not_working_day( res_num, d )
                    print "x",
                else:
                    print ".",
            print
        
        pb.set_convexity( True )
        pb.set_time( -1 ) # 2 min max
        solve( pb )
        return []
    
        activities = []
        # FIXME: start date !
        # start_date, end_date = self.project.get_task_date_range(project.root_task)
        start_date = self.start_date
        for task_id, interval in self.solution.items():
            task_start = start_date + interval._start
            task_end = start_date + max(interval._start,interval._end-1)
            task = self.project.root_task.get_task(task_id)
            for r_type, r_id, usage in task.get_resource_constraints():
                activities.append((task_start, task_end, r_id, task_id, 1.))
            if task.TYPE=='milestone':
                for res in self.project.get_resources():
                    activities.append((task_start, task_end, res, task_id, 1.))

        self.project.add_schedule(activities)
        return []


def solution_cost(solution):
    """cost function
    
    we try to minimize the end date of the project, so the cost of a
    solution maybe represented by the end date of the last task
    """
    end_dates = [var[0].get_end() for var in solution.values()]
    return max(end_dates)



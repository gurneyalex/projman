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
""" schedule project using Constraint Solving Programing """

__revision__ = "$Id: csp.py,v 1.2 2005-09-07 23:51:01 nico Exp $"

from mx.DateTime import today

from logilab.constraint import Repository, Solver, fi
from logilab.common.compat import set

from projman.lib.constants import *

CONSTRAINT_MAP = {
    BEGIN_AFTER_END   : fi.StartsAfterEnd,
    BEGIN_AFTER_BEGIN : fi.StartsAfterStart,
    END_AFTER_END     : fi.EndsAfterEnd,
    END_AFTER_BEGIN   : fi.EndsAfterStart,
    }

class UnavailableResource(Exception):
    """Exception raised when a resource is not available"""

SchedulingDistributor = fi.FiniteIntervalDistributor
SchedulingDomain = fi.FiniteIntervalDomain

class CSPScheduler:
    """
    schedule a project using constraint programming
    
    variables = leaf tasks of the project
    values = (timeslotsset, resource)
    """
    def __init__(self, project):
        self.project = project
        self.variables = []
        self.domains = {}
        self.constraints = set()
        self.solution = None
        max_length = self.get_project_length()
        for leaf in project.root_task.leaves():
            self._process_node(leaf, max_length)
        self.add_resource_constraints()
        self.add_priorities_as_constraints()
    
    def get_project_length(self):
        max_length = self.project.root_task.maximum_duration()
        begins, ends = [today()], [today()]
        for leaf in self.project.root_task.leaves():
            for c_type, date in leaf.get_date_constraints():
                if c_type in (BEGIN_AT_DATE, BEGIN_AFTER_DATE):
                    begins.append(date)
                elif c_type in (END_AT_DATE, END_BEFORE_DATE):
                    ends.append(date)
        other_length = (max(ends) - min(begins)).days +1
        #print max_length, other_length
        return max(max_length, other_length)


    def _process_node(self, node, max_length):
        self.variables.append(node.id)
        self.domains[node.id] = SchedulingDomain(0, max_length, node.duration)
        # add task constraints
        for constraint_type, task_id in node.get_task_constraints():
            constraint_class = CONSTRAINT_MAP[constraint_type]
            for leaf in node.get_task(task_id).leaves():
                self.constraints.add(constraint_class(node.id, leaf.id))
        # add date constraints
        start_date = today()
        for c_type, date in node.get_date_constraints():
            if date < start_date :
                print 'ignore', c_type, date, start_date
                continue
            try:
                if c_type == BEGIN_AFTER_DATE :
                    self.domains[node.id].setLowestMin( (date-start_date).days )
                    print node.id, 'begin after', date
                elif c_type == END_BEFORE_DATE :
                    self.domains[node.id].setHighestMax( (date-start_date).days +1) 
                    print node.id, 'end before', date
            except fi.ConsistencyFailure, exc:
                print node.id, c_type, date, start_date, (date-start_date).days, self.domains[node.id]
                raise
            
    def add_resource_constraints(self):
        constraints = {}
        for leaf in self.project.root_task.leaves():
            for r_type, r_id, usage in leaf.get_resource_constraints():
                constraints.setdefault(r_id, set()).add(leaf.id)
        for r_id, task_ids in constraints.items():
            while task_ids:
                t1 = task_ids.pop()
                for t2 in task_ids: 
                    self.constraints.add(fi.NoOverlap(t1, t2))

    def add_priorities_as_constraints(self):
        """
        transform priorities as BEGIN_AFTER_END constraints
        """
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
        #print self.variables, self.domains, self.constraints
        #raise TypeError("zou")
        repo = Repository(self.variables, self.domains, self.constraints)
        solver = Solver(SchedulingDistributor())
        self.solution = solver.solve_one(repo, verbose=verbose)
        activities = []
        # FIXME: start date !
        # start_date, end_date = self.project.get_task_date_range(project.root_task)
        start_date = today()
        for task_id, interval in self.solution.items():
            task_start = start_date + interval._start
            task_end = start_date + max(0,interval._end-1)
            assert task_start <= task_end, "%s %s %s"%(task_id,task_start,task_end)
            task = self.project.root_task.get_task(task_id)
            for r_type, r_id, usage in task.get_resource_constraints():                
                activities.append((task_start, task_end, r_id, task_id, 1.))

        self.project.add_schedule(activities)
        return []


def solution_cost(solution):
    """cost function
    
    we try to minimize the end date of the project, so the cost of a
    solution maybe represented by the end date of the last task
    """
    end_dates = [var[0].get_end() for var in solution.values()]
    return max(end_dates)



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
""" schedule project using Constraint Solving Programing """

import itertools
from mx.DateTime import oneDay, oneHour, today
import projman.lib.constants as CST
from projman.scheduling.gcsp import (ProjmanProblem, solve,
                                     constraint_types as GCSP_CST, load_types)

GCSPMAP = {}
for t in CST.TASK_CONSTRAINTS:
    name = t.upper().replace("-","_")
    try:
        GCSPMAP[t] = getattr(GCSP_CST, name)
    except AttributeError:
        assert name == "BEGIN_AFTER_END_PREVIOUS"
_VERBOSE=1

class CSPScheduler(object):
    """
    schedule a project using constraint programming

    variables = leaf tasks of the project
    values = (timeslotsset, resource)
    """
    def __init__(self, project):
        self.project = project
        self.start_date = None
        #self.first_tasks = None
        self.constraints = {} # Constraint Type -> list of task pairs
        self.task_ranges = {} # task_id -> date range or (None,None)
        self._resources_map = {}
        self._pseudo_tasks = []
        self.calc_project_length()
        self.real_tasks = self.project.root_task.leaves()
        for leaf in self.real_tasks:
            self._process_node(leaf)
        #self.add_priorities_as_constraints()

    def calc_project_length(self):
        """Computes start_date and max_duration (duration of the project)"""
        begins, ends = [], []
        for leaf in self.project.root_task.leaves():
            for c_type, date, priority in leaf.get_date_constraints():
                if c_type in (CST.BEGIN_AT_DATE, CST.BEGIN_AFTER_DATE) and \
                            self.project.priority >= int(priority):
                    begins.append(date)
                elif c_type in (CST.END_AT_DATE, CST.END_BEFORE_DATE) and \
                            self.project.priority >= int(priority):
                    ends.append(date)
        if not self.start_date:
            # We take the earliest date constraint as a start date
            if begins:
                self.start_date = min(begins)
            elif ends:
                self.start_date = min(ends)
            else:
                self.start_date = today()
        # find the first working day
        d = self.start_date
        self.first_day = 0
        # instead of checking all resources, we should look only for resources
        # working on those task that *could* begin at the start of the project
        while not any(res.is_available(d) for res in self.project.get_resources()):
            d += 1
            self.first_day += 1
        # play it safe and add sum of loads plus time to latest date constraint
        self.max_duration = self.project.root_task.maximum_duration()
        if begins or ends:
            self.max_duration += (max(itertools.chain(begins,ends)) - self.start_date).days

    def _process_node(self, node):
        max_duration = int(self.max_duration*2)
        rnge = self.task_ranges.setdefault( node.id, [None,None] )
        tab_rnge0 = [0]
        tab_rnge1 = [max_duration]
        # collect task constraints
        for constraint_type, task_id, priority in node.get_task_constraints():
            if constraint_type not in GCSPMAP:
                assert constraint_type == 'begin-after-end-previous'
                index = self.real_tasks.index(node)
                if index == 0:
                    # apply start date
                    continue
                task_id = self.real_tasks[index - 1].id
                constraint_type = "begin-after-end"
            if self.project.priority >= int(priority):
                for leaf in node.get_task(task_id).leaves():
                    c_set = self.constraints.setdefault(constraint_type, set())
                    c_set.add( (node.id, leaf.id)  )
        for c_type, date, priority in node.get_date_constraints():
            if self.project.priority >= int(priority):
                days = (date-self.start_date).days
                if days<0:
                    raise Exception('WTF?')
                if c_type == CST.BEGIN_AFTER_DATE :
                    tab_rnge0.append(days)
                elif c_type == CST.END_BEFORE_DATE:
                    tab_rnge1.append(days+1)
        # collect date constraints
        rnge[0] = max(tab_rnge0)
        rnge[1] = min(tab_rnge1)
        if _VERBOSE>2:
            print node.id, 'range=', rnge
        # collect resources
        if node.TYPE != 'milestone':
            node.compute_resources(self.project)
            if _VERBOSE>1:
                print "Resources", node.get_resource_ids()

    def add_priorities_as_constraints(self):
        """
        transform priorities as BEGIN_AFTER_END constraints
        """
        return # XXXX FIXME
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

    def _compute_activities(self, solution, pseudo_tasks, resources_map):
        """compute the list of activities

        :rtype: List
        :returns:
            List of Tuples (begin, end, resource_id, task_id, usage, src)
        """
        factor = self.project.factor
        task_days = self.read_solution(solution)

        # list of tuples (begin, end, resource_id, task_id, usage, src)
        activities = []
        day_cost = oneHour * CST.HOURS_PER_DAY
        time_table = day_cost / factor
        for pid, days in enumerate( task_days ):
            num, task, res_id = pseudo_tasks[pid]
            tid = task.id
            for i, day in enumerate(days):
                d = day / factor
                decalage = 0
                day_resource = 0
                if i+1 < len(days)  and factor == 2 and days[i+1] != d:
                    decalage = day_cost /factor #ok
                    day_resource = 2
                elif i+1 < len(days) and factor == 4 and days[i+1] != d:
                    decalage = day_cost /(factor/3.)
                    day_resource = 4
                elif i+2 < len(days) and factor == 4 and days[i+2] != d:
                    decalage = day_cost /(factor/2.)
                    day_resource = 3
                elif i+3 < len(days) and factor == 4 and days[i+3] != d:
                    decalage = day_cost /float(factor)
                    day_resource = 2
                else:
                    day_resource = 1
                date = self.start_date + d + day_cost + decalage
                if date.hour == 0:
                    date += day_cost
                elif date.hour > 17:
                    date += day_cost
                    date += oneDay
                elif date.hour >= 12:
                    date += oneHour
                if day_resource > factor:
                    raise Exception("found non valid solution")
                already = sum(elt[4] for elt in activities if tid==elt[3])
                delta = (task.duration - already) * factor
                # duree (initiale) tache * factor - nb de jours
                #                        deja ecoules pr cette tache
                if delta > 1.0 / factor or delta <= 0:
                    usage = 1.0 / factor
                else:
                    usage = delta
                activities.append( (date, date + time_table, res_id,
                                tid, max(usage, 1./factor)) )
        return activities

    def schedule(self, verbose=0, time=60000, sol_max=4000, **kw):
        """
        Update the project's schedule
        Return list of errors occured during schedule
        """
        global _VERBOSE
        #XXX the return value should be a list of errors, but is always '[]'

        # print always the scheduling options to reminder the user of them
        sol_msg = 'all' if (sol_max==0) else 'max %d' % sol_max
        print ("\nscheduling ...\n  (searching for %s solutions, max %d msec;"
               " see projman schedule options)" % (sol_msg, time))
        _VERBOSE = verbose
        # check the tasks (duration is not 0)
        for leaf in self.project.root_task.leaves():
            leaf.check_duration()
            leaf.check_role(self.project)
        factor = self.project.factor
        max_duration = int( self.max_duration * 2 )
        if _VERBOSE>1:
            print "Nb Tasks :", len(self.real_tasks)
            print "Nb Res   :", len(self.project.resources)
            print "Duration :", self.max_duration
            print "Factor   :", factor
        pb = ProjmanProblem( int(max_duration * factor ) )
        pb.set_first_day( self.first_day * factor)

        if _VERBOSE>1:
            print "occupation"
            print "----------"

        # compute resources map
        self._resources_map = {}
        for res_id, res in self.project.resources.items():
            sched = []
            res_num = pb.add_worker( res_id )
            self._resources_map[res_id] = res_num
            #gestion calendrier jours feries et we
            for d in range(max_duration):
                if not res.is_available( self.start_date + d ):
                    for i in range(factor):
                        pb.add_not_working_day( res_num, d*factor + i )
                    sched.append("x" * factor)
                else:
                    sched.append("." * factor)
            if _VERBOSE > 1:
                print "%02d" % res_num, "".join(sched)

        self._compute_pseudo_tasks(pb)
        # register constraints
        num_tasks = dict((task.id, num) for (num, task) in enumerate(self.real_tasks))
        for type, pairs in self.constraints.items():
            for t1, t2 in pairs:
                n1 = num_tasks[t1]
                n2 = num_tasks[t2]
                pb.add_task_constraint( GCSPMAP[type], n1, n2 )
                if _VERBOSE>1:
                    print "%s %s(%s), %s(%s)" %(type, t1, n1, t2, n2)
        self._run_schedule(pb, time, sol_max)

    def _compute_pseudo_tasks(self, pb):
        factor = self.project.factor
        pseudo_tasks = self._pseudo_tasks = []
        max_duration = int( self.max_duration * 2 )
        for task in self.real_tasks:
            tid = task.id
            duration = task.duration
            _type = task.load_type
            duration_ = duration * factor
            if (duration_) % 1 > 0:
                duration_ = int(duration_) + 1
            task_num = pb.add_task( tid, _type, int(duration_),
                                    bool(task.can_interrupt[0]) )
            low, high = self.task_ranges[tid]
            if _VERBOSE>1:
                print "Task %2d = #%.2f [%4s,%4s] = '%20s'" % (task_num, duration,
                                                               low, high, tid)
            if low is None:
                low = 0
            else:
                low *= factor
            if high is None:
                high = max_duration * factor
            else:
                high *= factor
            pb.set_task_range( task_num, int(low), int(high), 0, 0 ) # XXX: cmp_type unused
            if _type == load_types.TASK_MILESTONE:
                continue
            for res_id in task.get_resource_ids():
                if _VERBOSE>2:
                    print "   ", res_id
                res_num = self._resources_map[res_id]
                pseudo_id = pb.add_resource_to_task( task_num, res_num )
                pseudo_tasks.append( (pseudo_id, task, res_id) )

    def _run_schedule(self, pb, time, sol_max):
        pb.set_convexity( True )
        pb.set_time(time)
        pb.set_verbosity( _VERBOSE )
        pb.set_max_nb_solutions(sol_max)
        solve( pb )

        self.project.nb_solution = pb.get_number_of_solutions()
        if self.project.nb_solution==0:
            return
        if (_VERBOSE>2):
            self.compare_solutions( pb )
        solution = pb.get_solution( self.project.nb_solution-1 )
        day_cost = oneHour * CST.HOURS_PER_DAY
        activities = self._compute_activities(solution, self._pseudo_tasks,
                                              self._resources_map)
        if _VERBOSE > 0:
            print "\nactivites :"
            for (db, de, res_id, tid, dur) in activities:
                print "\tdu", db,"au", de, res_id, tid, dur
        milestone = 0
        nmilestones = solution.get_nmilestones()
        factor = self.project.factor
        for task in self.real_tasks:
            tid = task.id
            if task.duration!=0:
                continue
            if milestone>=nmilestones:
                break
            d = solution.get_milestone( milestone )
            date = self.start_date + day_cost + int(d / factor)
            if (_VERBOSE>=2):
                print "MILESTONE", tid, date
            self.project.milestones[tid] = date
            milestone += 1

        self.project.add_schedule(activities)

    def read_solution( self, sol ):
        duration = sol.get_duration()
        ntasks = sol.get_ntasks()
        task_days = [ [ day for day in range(duration) if
                        sol.isworking( task, day ) ] for task in range(ntasks) ]
        return task_days

    def compare_solutions( self, pb ):
        N = pb.get_number_of_solutions()
        if N==0:
            return
        SOL0 = self.read_solution( pb.get_solution( 0 ) )
        for i in range(1,N):
            SOL1 = self.read_solution( pb.get_solution( i ) )
            for id, (task0,task1) in enumerate( zip( SOL0, SOL1 ) ):
                if task0!=task1:
                    print id, task0
                    print id, task1
            print
            SOL0 = SOL1

def solution_cost(solution):
    """cost function

    we try to minimize the end date of the project, so the cost of a
    solution maybe represented by the end date of the last task
    """
    end_dates = [var[0].get_end() for var in solution.values()]
    return max(end_dates)



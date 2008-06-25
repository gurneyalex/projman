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

from mx.DateTime import oneDay, oneHour, today
from logilab.common.compat import set
import projman.lib.constants as CST
from gcsp import ProjmanProblem, solve, constraint_types as GCSP_CST, load_types

GCSPMAP = {}
for t in CST.TASK_CONSTRAINTS:
    name = t.upper().replace("-","_")
    GCSPMAP[t] = getattr(GCSP_CST, name)

_VERBOSE=1

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
        #self.first_tasks = None
        self.real_tasks = {}  # task_id -> (task_number,duration,list_of_resources)
        self.constraints = {} # Constraint Type -> list of task pairs
        self.task_ranges = {} # task_id -> date range or (None,None)
        self.resources = set()   # res_id -> res_number
        for leaf in project.root_task.leaves():
            self._process_node(leaf)
        #self.add_priorities_as_constraints()

    def calc_project_length(self):
        """Computes start_date and max_duration (duration of the project)"""
        max_duration = self.project.root_task.maximum_duration()
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
        while True:
            # this really should be the list of resources working
            # on those task that *could* begin at the start of the project 
            for res_id in self.project.get_resources():
                res = self.project.get_resource(res_id)
                if res.is_available( d ):
                    break
            else:
                d = d + 1
                self.first_day += 1
                continue
            break
        if ends and begins:
            other_length = (max(ends) - min(begins)).days +1
        else:
            other_length = 0
        self.max_duration = max(max_duration, other_length)

    def _process_node(self, node):
        max_duration = int(self.max_duration*2)

        _, _, _, task_resources = self.real_tasks.setdefault( node.id,
                                                           [len(self.real_tasks),
                                                            node.load_type,
                                                            node.duration, []] )
        rnge = self.task_ranges.setdefault( node.id, [None,None] )

        # collect task constraints
        for constraint_type, task_id, priority in node.get_task_constraints():
            if self.project.priority >= int(priority):
                for leaf in node.get_task(task_id).leaves():
                    lst = self.constraints.setdefault(constraint_type, set())
                    lst.add( (node.id, leaf.id)  )
        # collect date constraints
        tab_rnge0 = [0]
        tab_rnge1 = [max_duration]
        for c_type, date, priority in node.get_date_constraints():
            if self.project.priority >= int(priority):
                days = (date-self.start_date).days
                if days<0:
                    raise Exception('WTF?')
                if c_type == CST.BEGIN_AFTER_DATE :
                    tab_rnge0.append(days)
                elif c_type == CST.END_BEFORE_DATE:
                    tab_rnge1.append(days+1)
        rnge[0] = max(tab_rnge0)
        rnge[1] = min(tab_rnge1)
        if _VERBOSE>2:
            print node.id, 'range=', rnge
        # collect resources
            # 
            # on utilise task.set_resources pour obtenir l ensemble des
            # resources disponibles pour une tache
            #
        # -> using new projman definition
        if node.TYPE != 'milestone' and node.get_resource_constraints()== set():
            # collect resources in root_trask
            for r_type, r_id in self.project.root_task.get_resource_constraints():
                if self.project.priority >= int(priority):
                    self.resources.add( r_id )
                    task_resources.append( r_id )
            self.project.get_resources_from_task_type(node)
            #trouver les resources correspondantes
            task_type = node.get_task_type()
            if _VERBOSE>1:
                print "Resource", r_id
        # -> using old projman definition
        else:
            for r_type, r_id in node.get_resource_constraints():
                if self.project.priority >= int(priority):
                    if _VERBOSE>1:
                        print "Resource", r_type, r_id
                    self.resources.add( r_id )
                    task_resources.append( r_id )
                    node.set_resources.append(r_id)

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

    def activity_usage_counter_by_task(self, activities, tid):
        """
        count number of days already affected to the task(tid)
        """
        usage = 0
        for element in activities:
            if tid == element[3]:
                usage = usage + element[4]
        return usage

    def schedule(self, verbose=0, time=400000, **kw):
        """
        Update the project's schedule
        Return list of errors occured during schedule
        """
        print "\nscheduling ..."
        _VERBOSE = verbose
        # check the tasks (duration is not 0)
        for leaf in self.project.root_task.leaves():
            leaf.check_duration()
        self.project.get_factor()
        factor = self.project.factor
        self.max_duration = int( self.max_duration * 2 )
        if _VERBOSE>1:
            print "Tasks", len(self.real_tasks)
            print "Res", len(self.resources)
            print "Dur", self.max_duration
            print "Factor", factor
        pb = ProjmanProblem( int(self.max_duration * factor ) )
        pb.set_first_day( self.first_day * factor) 
        real_tasks_items = self.real_tasks.items()
        real_tasks_items.sort( key = lambda x:x[1][0] )
        dt = []
        if _VERBOSE>1:
            print "occupation"
            print "----------"
        resources_map = {}
        for res_id in self.resources:
            sched = []
            res = self.project.get_resource( res_id )
            res_num = pb.add_worker( res_id )
            resources_map[res_id] = res_num
            #gestion calendrier jours feries et we
            for d in range(int(self.max_duration)):
                dt = self.start_date + d
                if not res.is_available( dt ):
                    for i in range(factor):
                        pb.add_not_working_day( res_num, d*factor + i )
                        sched.append("x")
                else:
                    for i in range(factor):
                        sched.append(".")
            if _VERBOSE > 1:
                print "%02d" % res_num, "".join(sched)
        pseudo_tasks = []
        i = 0

        for tid, (num, _type, duration, resources) in real_tasks_items:

            task = self.project.get_task(tid)
            resources = task.set_resources # set resources according to new definition
            duration_ = duration * factor
            if (duration * factor) % 1 > 0 :
                duration_ = duration * factor - ((duration * factor) % 1) + 1
                real_tasks_items[i][1][2] = duration_ / factor
            task_num = pb.add_task( tid, _type, int(duration_), bool(task.can_interrupt[0]) )
            low, high = self.task_ranges[tid]
            if _VERBOSE>1:
                print "Task %2d = #%.2f [%4s,%4s] = '%20s'" % ((task_num,duration,low,high,tid,))
            if low is None:
                low = 0
            else:
                low *= factor
            if high is None:
                high = self.max_duration * factor
            else:
                high *= factor
            pb.set_task_range( task_num, int(low), int(high), 0, 0 ) # XXX: cmp_type unused
            if _type == load_types.TASK_MILESTONE:
                continue
            for res_id in sorted(resources):
                res_num = resources_map[res_id]
                pseudo_id = pb.add_resource_to_task( task_num, res_num ) 
                pseudo_tasks.append( (pseudo_id, tid, res_id) )

        # register constraints
        for type, pairs in self.constraints.items():
            for t1, t2 in pairs:
                n1, _, _, _ = self.real_tasks[t1]
                n2, _, _, _ = self.real_tasks[t2]
                pb.add_task_constraint( GCSPMAP[type], n1, n2 )
                if _VERBOSE>1:
                    print "%s %s(%s), %s(%s)" %(type, t1, n1, t2, n2)

        pb.set_convexity( True )
        pb.set_time(time)
        pb.set_verbosity( _VERBOSE )
        pb.set_max_nb_solutions(4000)
        solve( pb )
        
        self.project.nb_solution = pb.get_number_of_solutions()
        if self.project.nb_solution==0:
            return []
        if (_VERBOSE>2):
            self.compare_solutions( pb )
        SOL = pb.get_solution( self.project.nb_solution-1 )
        duration = SOL.get_duration()
        ntasks = SOL.get_ntasks()
        tasks_days = [ [ day / factor for day in range(duration) if SOL.isworking( task, day ) ] for task in range(ntasks) ]
        #calendar gere l'utilisation d'une resource pour un jour afin
        # d'organiser les heures de travail si factorized_days > 1
        calendar = []# attention si le calendrier est fonction de chaque resources
                     # ca ne marche plus
                     # ca ne marche pas non plus si la resource n est pas utilisee
                     # sur une autre tache avant ...
        for i in range(duration/factor):
            calendar.append([])
            for j in range(len(resources_map)):
                calendar[i].append(0) 

        activities = []
        for pid, days in enumerate( tasks_days ):
            num, tid, res_id = pseudo_tasks[pid]
            time_table = oneHour * CST.HOURS_PER_DAY / factor
            for i, d in enumerate(days):
                #print "debug"
                #print "day:", d, i
                decalage = calendar[d][resources_map[res_id]]* time_table
                if decalage == 0:# and i+1 < len(days):
                    if i+1 < len(days) and days[i+1] != d and factor == 2:
                        decalage += CST.HOURS_PER_DAY * oneHour /factor #ok
                        calendar[d][resources_map[res_id]] += 2
                    elif i+1 < len(days) and factor == 4 and days[i+1] != d:
                        decalage += CST.HOURS_PER_DAY * oneHour /(factor/3.)
                        calendar[d][resources_map[res_id]] += 4
                    elif i+2 < len(days) and factor == 4 and days[i+2] != d:
                        decalage += CST.HOURS_PER_DAY * oneHour /(factor/2.)
                        calendar[d][resources_map[res_id]] += 3
                    elif i+3 < len(days) and factor == 4 and days[i+3] != d:
                        decalage += CST.HOURS_PER_DAY * oneHour /float(factor)
                        calendar[d][resources_map[res_id]] += 2
                    else:
                        calendar[d][resources_map[res_id]] += 1
                else:
                    calendar[d][resources_map[res_id]] += 1
                date = self.start_date + d + CST.HOURS_PER_DAY * oneHour + decalage
                if date.hour == 0:
                    date += CST.HOURS_PER_DAY * oneHour
                elif date.hour > 17:
                    date += CST.HOURS_PER_DAY * oneHour
                    date += oneDay
                elif date.hour >= 12:
                    date += oneHour
                if calendar[d][resources_map[res_id]]> factor:
                    raise Exception("found non valid solution")
                delta = self.real_tasks[tid][2] * factor - \
                    self.activity_usage_counter_by_task( activities, tid )* factor 
                # duree (initiale) tache * factor - nb de jours 
                #                        deja ecoules pr cette tache
                if delta > 1.0 / factor or delta <= 0:
                    usage = 1.0 / factor
                else:
                    usage = delta
                activities.append((date, date + time_table, res_id, 
                                tid, max(usage,1./factor)))
        if _VERBOSE > 0:
            print "\nactivites :"
            for (db, de, res_id, tid, dur) in activities:
                print "\tdu", db,"au", de, res_id, tid, dur
        milestone = 0
        nmilestones = SOL.get_nmilestones()
        for tid, (num, _type, duration, resources) in self.real_tasks.items():
            if duration!=0:
                continue
            if milestone>=nmilestones:
                break
            d = SOL.get_milestone( milestone )
            date = self.start_date + CST.HOURS_PER_DAY * oneHour + int(d / factor)
            if (_VERBOSE>=2):
                print "MILESTONE", tid, date
            self.project.milestones[tid] = date
            milestone += 1

        self.project.add_schedule(activities)
        return []

    def read_sol( self, SOL ):
        duration = SOL.get_duration()
        ntasks = SOL.get_ntasks()
        tasks_days = [ [ day for day in range(duration) if SOL.isworking( task, day ) ] for task in range(ntasks) ]
        return tasks_days

    def compare_solutions( self, pb ):
        N = pb.get_number_of_solutions()
        if N==0:
            return
        SOL0 = self.read_sol( pb.get_solution( 0 ) )
        for i in range(1,N):
            SOL1 = self.read_sol( pb.get_solution( i ) )
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



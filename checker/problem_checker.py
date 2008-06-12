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

from projman.scheduling import schedule
from projman.scheduling.csp import CSPScheduler

class Checker:
    
    def __init__(self, project, verbose=0, **kw):
        scheduler = CSPScheduler(project)
        self.project=project
        self.verbosity = verbose
        self.real_tasks = scheduler.real_tasks
        self.constraints = scheduler.constraints
        self.resources = scheduler.resources
        self.max_duration = scheduler.max_duration
        self.successors = {}
        self.predecessors = {}
        self.first_day = None
        self.trees = None
        self.errors = []

    def problem_checker(self):
        if self.verbosity:
            self.dump()
        self.validate()
        self.check_tasks_convexity()
        self.check_tree()
        if self.trees:
            self.check_first_days()
        if self.errors:
            print 'attention, malformed problem:'
        else:
            print 'Problem valid'
        for error in self.errors:
            print '* ', error

    def dump(self):
        """ print principal data of the probleme """
        print "\n#  Set of real tasks (no container) #"
        for task_id in self.real_tasks:
            task = self.project.get_task(task_id)
            print task.title, '(id =', task.id, '; duration = ',task.duration,')' 
        print "\n#  Avaliable resources for the project #"
        for res in self.resources:
            res = self.project.get_resource(res)
            print res.name, " (",res.id_role,")"
        print "\n#  Set of constraints #"
        for task in self.project.root_task.leaves():
            for c_type, date, priority in task.get_date_constraints():
                print task.id, c_type, date, "(priority",priority,")"
        for constraint in self.constraints:
            set_tasks = self.constraints.get(constraint)
            print constraint,":"
            for couple in set_tasks:
                print couple[0], constraint, couple[1]
        print'\n'

    def validate(self):
        """check that there is no duplicate id or null duration of leaves"""
        consistence_errors = self.project.check_consistency()
        if consistence_errors:
            for error in consistence_errors:
                self.errors.append(error)
        # check tasks duration for leaves
        for leaf in self.project.root_task.leaves():
            if leaf.duration == 0 and leaf.TYPE=='task':
                self.errors.append('Leaf %s without any duration:\n\t-> add duration, add sub tasks or write it as a milestone' %leaf.id)

    def check_tree(self):
        tasks = []
        for tid in self.real_tasks:
            tasks.append(tid)
        arcs = []
        for constraint in self.constraints:
            if constraint in ('begin-after-end', 'begin-after-begin'):
                for couple in self.constraints.get(constraint):
                    arcs.append((couple[1], couple[0]))
        for task in tasks:
            self.predecessors.setdefault(task, [])
            self.successors.setdefault(task, [])
        for couple in arcs:
            self.predecessors[couple[1]].append(couple[0])
            self.successors[couple[0]].append(couple[1])
            
        if self.verbosity > 1:
            print "arcs", arcs
            print "tasks", tasks
            print "listes des predecesseurs",self.predecessors
            print "liste des successeurs   ", self.successors
        self.trees = self.depth_first_search(tasks)

    def depth_first_search(self, tasks):
        """ applie DFS algorithm in set of tasks to detect cycle and find
            tasks order """
        if self.verbosity > 1:
            print 'ALGORITHME DEPTH FIRST SEARCH'
        if not [] in self.predecessors.values() or not [] in self.successors.values():
            self.errors.append('Cycles detected:\n\t-> change tasks constraints')
            return []
        trees = []
        set_tag = set()
        tag = None
        if self.verbosity > 2:
            print "predecessors:", self.predecessors
            print "successors:", self.successors

        for key in self.predecessors:
            # detect fisrt task
            tag = []            
            values = self.predecessors.get(key)
            if values == []:
                first = key
            else:
                continue
            Q = []
            Q.append(first)
            rounder = 0
            while Q:
                rounder += 1
                if self.verbosity > 2:
                    print "\nQ"  , Q
                    print 'tag', tag
                on_good_path = True
                v = Q[0]
                if v == first and rounder > 1:
                     self.errors.append('Cycles detected:\n\t-> change tasks constraints')
                     return []
                #check if all predecessors are allready in the path
                for pred in self.predecessors.get(v):
                    if not pred in tag and not pred in Q:
                        if pred in Q:
                            Q.remove(pred)
                        Q.insert(0, pred)
                        on_good_path = False
                if not on_good_path:
                    continue
                Q.remove(v)
                tag.append(v)
                for v_prime in self.successors.get(v):
                    if not v_prime in tag:
                        if self.verbosity > 2:
                            print '  successors:', v_prime
                        if not v_prime in Q:
                            Q.append(v_prime)                    
            trees.append(tag)
            for elt in tag:
                set_tag.add(elt)
            # check if every real task was considered
        for task in self.real_tasks:
            if not task in set_tag:
                self.errors.append('Cycles detected on task %s:\n\t-> change tasks constraints' %task)
                return []
        if self.verbosity:
            print 'tasks paths'
            print trees
        return trees

    def check_first_days(self):
        """detect unconsistant probleme due to the hypothese that
        the fist day of a project must be work """
        first = []
        for task in self.project.root_task.leaves():
            for c_type, date, priority in task.get_date_constraints():
                if c_type in ('begin-after-date', 'begin-at-date'):
                    first.append(date)
        self.first_day = min(first)
        for tree in self.trees:
            # find date constraints on first task of the tree
            task = self.project.get_task(tree[0])
            for c_type, date, priority in task.get_date_constraints():
                if date > self.first_day:
                    self.errors.append('Incoherent date constraint in task %s:\n\t-> change date constraints' % task.id)

    def check_tasks_convexity(self):
        for leaf_id in self.real_tasks:
            leaf = self.project.get_task(leaf_id)
            # compute the number of possible resources for the task
            # according to new definition of resources role
            if not leaf.can_interrupt[0] and leaf.duration >5:
                count = 0
                for res_id in self.resources:
                    resource = self.project.get_resource(res_id)
                    if leaf.task_type in resource.id_role:
                        count += 1
                duration = leaf.duration / float(count)
                if duration > 5:
                    self.errors.append('Uninterruptible task %s with duration in excess of one week:\n\t-> reduce duration or associate the task to more resources' %leaf.id)
                

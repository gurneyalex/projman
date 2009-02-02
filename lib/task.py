# -*- coding: iso-8859-1 -*-
# Copyright (c) 2004 LOGILAB S.A. (Paris, FRANCE).
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
Projman - (c)2000-2004 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projman

Manipulate a xml project description.

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

__revision__ = "$Id: task.py,v 1.4 2006-02-24 10:39:38 nico Exp $"

from logilab.common.tree import VNode 
from logilab.common.compat import set

from mx.DateTime import now
from projman.lib.constants import *


__all__ = ['MileStone', 'Task']

class TaskNode(VNode):
    """base node for Task and MileStone objects

    Attributes:
      - title
      - date_constraints
      - task_constraints
      - description
    """

    def __init__(self, node_id):
        VNode.__init__(self, node_id)
        self.title = u''
        # list of triplets ('{begin/end}-{at/before/after}-date', mxDate, priority)
        self.date_constraints = set()
        # list of triplets ('{begin/end}-after-{begin/end}', task_id, priority)
        self.task_constraints = set()
        self.description = u''
        self.description_raw = u''
        self.description_format = u'docbook'
        self._progress = None
        self._priority = None
        self.duration = 0
        self.load_type = 0
        self.task_type = None
        self.set_resources = set()
        self.can_interrupt = [True, 1] # the integer represent the priority of the constraint
        self.link = None
        self.level = 1
        
    def __repr__(self):
        return "<Task id=%s at %s>" % (self.id, id(self))
    
    def get_task(self, task_id):
        """
        return the task with id task_id
        """
        return self.get_node_by_id(task_id)

    # properties ####################################################
    
    def get_progress(self):
        """used by the 'progress' property"""
        if self.is_leaf():
            if self._progress is None:
                return 0.
            else:
                return self._progress
        else:
            done = [leaf.progress * leaf.maximum_duration()
                    for leaf in self.leaves()]
            
            if self.maximum_duration() > 1e-5:
                return sum(done) / self.maximum_duration()
            return 1.0
        
    def set_progress(self, value):
        """used by the 'progress' property"""
        if not self.is_leaf():
            raise AssertionError('Can only set progress on leaves tasks')
        if 0. <= value <= 1.:
            self._progress = value
        else:
            raise ValueError("progress is a percentage (between 0 and 1, got %s)" % value)
    
    progress = property(get_progress, set_progress,
                        doc="task progress (percentage)")

    def get_priority(self):
        """return priority (inherited from parents if None)"""
        if self._priority is None and self.parent:
            return self.parent.priority
        else:
            return self._priority

    def set_priority(self, value):
        self._priority = value

    priority = property(get_priority, set_priority)

    # Editing functions #############################################

    def add_date_constraint(self, constraint_type, date, priority=1):
        """ add a date constraint to the milestone """
        assert constraint_type in DATE_CONSTRAINTS, constraint_type
        self.date_constraints.add((constraint_type, date, priority))

    def add_task_constraint(self, constraint_type, task_id, priority=1):
        """ add a task constraint to the milestone """ 
        assert constraint_type in TASK_CONSTRAINTS, constraint_type
        self.task_constraints.add((constraint_type, task_id, priority))

    # Manipulation functions #############################################
    
    def maximum_duration(self):
        """
        returns the duration of task taking into account all the durations of 
        its children
        /!\ duration is in man-days.
        """
        if self.is_leaf():
            return self.duration
        else:
            assert not self.duration, "Only leaves should have duration ! %s" % self.id 
            return sum([node.maximum_duration() for node in self.children])
    
    def remaining_duration(self):
        """
        return an estimation of the number of days required to close this task
        /!\ duration is in man-days.
        """
        if self.is_leaf():
            if self.progress:
                return self.duration * (1 - self.progress)
            else:
                raise NotImplementedError()
        else:
            return sum([child.remaining_duration() for child in self.children])
        
    def is_ready(self):
        """
        a task is ready when all the tasks it depends on are finished
        """
        for c_type, task_id in self.task_constraints:
            if c_type == BEGIN_AFTER_END:
                task = self.get_task(task_id)
                if task.progress != 1:
                    return False
        return True
        
    def is_finished(self):
        """
        return True if task is finished
        activities is the accomplished activity related to task
        """
        if self.is_leaf():
            return self.progress == 1.
        else:
            for each in self.children:
                if not each.is_finished():
                    return False
            return True
        
    def get_task_constraints(self):
        """
        get all task constraints taking into account the constraints 
        on the parents
        """
        # FIXME: Cache result (or modify in-place)
        if self.parent:
            return self.task_constraints | self.parent.get_task_constraints()
        else:
            return self.task_constraints

    def get_date_constraints(self):
        """
        get the date constraints propagating the appropriate 
        date constraints from parent nodes
        """
        # FIXME: Cache result (or modify in-place)
        constraints = set(self.date_constraints)
        if self.parent:
            for c_type, date, priority in self.parent.get_date_constraints():
                if c_type in (BEGIN_AT_DATE, BEGIN_AFTER_DATE):
                    constraints.add((BEGIN_AFTER_DATE, date, priority))
                elif c_type in (END_AT_DATE, END_BEFORE_DATE):
                    constraints.add((END_BEFORE_DATE, date, priority))
        return constraints

    def check_duration(self):
        """check non valid duration (0)"""
        if self.TYPE != 'milestone' and self.duration == 0:
            raise Exception("non valid task duration for '%s'" %self.id)

    def check_consistency(self):
        """
        check that there are no duplicated task ids
        """
        #check non valid duration (0)
        #if self.TYPE != 'milestone' and self.duration == 0:
        #    raise Exception("non valid task duration for '%s'" %self.id)
        errors = []
        task_ids = set()
        for node in self.flatten():
            if node.id in task_ids:
                errors.append('Duplicate task id: %s' % node.id)
            else:
                task_ids.add(node.id)
        errors += self._check_consistency_date_constraints(self)
        if self.parent :
            errors += self._check_consistency_date_constraints(self.parent)
        return errors

    def _check_consistency_date_constraints(self, other):
        errors = []
        msg = 'Parent task of %s has constraint (%s, %s) which ' \
              'conflicts with its constraints (%s, %s)'
        for other_c_type, other_date, other_priority in other.get_date_constraints():
            if other_c_type in (BEGIN_AT_DATE, BEGIN_AFTER_DATE):
                for c_type, date, priority in self.date_constraints:
                    if date < other_date:
                        errors.append(msg % (self.id, other_c_type,
                                             other_date, c_type, date))
            elif c_type in (END_AT_DATE, END_BEFORE_DATE):
                for c_type, date in self.date_constraints:
                    if date > other_date:
                        errors.append(msg % (self.id, other_c_type,
                                             other_date, c_type, date))
        return errors

class Task(TaskNode):
    """a Task in the Project
    
    A Task instance is identified by its 'id' attribute. It can
    contain other tasks and/or milestone and/or imported projects,
    or it can be a leaf. If it's a leaf, the 'duration' attribute
    indicates the number of days of work needed to perform the
    task.

    Attributes:
      - priority: integer from 0 (lowest) to 9, -1 means inherits
        parent's priority
      - duration: integer estimated duration of the task
      - progress: integer progress of task (in percent)
      - resource_constraints: sequence of tuples (type, id_res),
        can be used without id_res for planning with type of
        resource
      - hide: boolean, used to render partial graphs (e.g. for a
        given resource)
        
    invariant:
        0. <= self.progress <= 1. # percentage of progress
    """ 
    
    TYPE = 'task'

    def __init__(self, t_id):
        TaskNode.__init__(self, t_id)
        self.resource_constraints = set()

    def get_task_type(self):
        if self.task_type:
                return self.task_type
        elif self.parent:
            return self.parent.get_task_type()
        else:
            return set()

    def get_resource_constraints(self):
        """
        get real resource constraints using parent resource constraints
        """
        if not self.task_type:
            if self.resource_constraints:
                return self.resource_constraints
            elif self.parent:
                return self.parent.get_resource_constraints()
            else:
                return set()
        else:
            self.get_task_type()
            return set()
        
    def get_resources(self):
        """
        return a sequence of the resources in resource_constraints
        """
        # according to old resources definition
        self.set_resources = set([id_res for type_c, id_res in
                    self.get_resource_constraints()])
        
        return self.set_resources

    def get_linked_resources(self, set_resources):
        """ return set of resources linked to a task and his children, from all
        resources of set_resources"""
        set_res = set()
        if self.TYPE == 'milestone':
            return set()
        for res in set_resources:
            for leaf in self.leaves():
                if leaf.TYPE == 'milestone':
                    continue
                if leaf.task_type: # according to new definition of resources
                    if leaf.task_type in res.id_role:
                        set_res.add(res.id)
                else: # according to old definition of resources
                    for ctype, res_id in leaf.get_resource_constraints():
                        set_res.add(res_id)
            # if task is a leaf
            if not self.children:
                if self.task_type and not self.children: # according to new definition of resources
                    if self.task_type in res.id_role:
                        set_res.add(res.id)
                else: # according to old definition of resources 
                    for ctype, res_id in self.resource_constraints:
                        set_res.add(res_id)
        return set_res

        
#    def get_resource_dispo(self, res_id):
#        """
#        get the resource disponibility required for this task
#        """
#        for type_c, id_res in self.get_resource_constraints():
#            if id_res == res_id:    
#                return usage
#        return 0

    def add_resource_constraint(self, resource_type, resource_id):
        # FIXME what about node <constraint-resource idref="toto"/>
        self.resource_constraints.add((resource_type, resource_id))


class MileStone(TaskNode):
    """A milestone in the project
    
    A milestone represents an event occuring at a specific date, but
    without any specific information about duration or timing.

    Subclasses of MileStone are Task and Project.

    """
    
    TYPE = 'milestone'

    def append(self, node):
        raise AssertionError("a milestone should always be a leaf")

    def get_progress(self):
        if self.is_ready():
            return 1.
        return 0.
    
    progress = property(get_progress, doc="milestone progress (percentage)")

    def get_resource_constraints(self):
        return set()

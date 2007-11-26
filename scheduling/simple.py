# -*- coding: iso-8859-1 -*-
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
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
schedule project without caring about resource conflicts
"""

from mx.DateTime import today
from projman.lib.constants import *

import logging
log = logging.getLogger("simple")

def cmp_tasks(task_a, task_b):
    """
    a < b return -1
    a == b return 0
    a > b return 1
    """
    # at least one task is None
    if task_a is None and task_b is None:
        return 0
    if task_a is None :
        return -1
    if task_b is None:
        return 1
    # otherwise
    res = 0
    family_a = [task.id for task in task_a.lineage()]
    family_b = [task.id for task in task_b.lineage()]
    for constraint_type, task_id in task_a.get_task_constraints():
        if constraint_type == BEGIN_AFTER_END:
            if task_id in family_b:
                res = 1
                break
    for constraint_type, task_id in task_b.get_task_constraints():
        if constraint_type == BEGIN_AFTER_END:
            if task_id in family_a:
                if res:
                    raise Exception("a after b and b after a ?!?")
                res = -1
                break
    if res == 0:
        if task_a.priority is None and task_b.priority is None:
            res = 0
        elif task_a.priority is None:
            res = 1
        elif task_b.priority is None:
            res = -1
        else:
            res = cmp(task_a.priority, task_b.priority)
    log.debug('%s %s %s'%(task_a, {-1:'<',0:'=',1:'>'}[res], task_b))
    return res

class SimpleScheduler:
    """
    schedule simple projects by ordering tasks and splitting resources
    """
    def __init__(self, project):
        self.project = project
        self.date_res = {}

    def earliest_begin(self, node):
        begin = None
        for constraint_type, task_id in node.get_task_constraints():
            if constraint_type == BEGIN_AFTER_END:
                b,e = self.project.get_task_date_range(self.project.get_task(task_id))
                begin = max(begin or e, e)
        for c_type, date in node.get_date_constraints():
            if c_type == BEGIN_AFTER_DATE :
                begin = max(begin or date, date)
        return begin
        
    def _process_node(self, node):
        # get dates
        begin = self.earliest_begin(node) or today()
        duration = max(0, node.duration-1)
        #if begin and not end:
        #    end = begin + duration
        #elif end and not begin:
        #    begin = end - duration
        # add activities
        activities = []
        resources = [(self.project.get_resource(r_id), usage/100)
                     for r_type, r_id, usage in node.get_resource_constraints()]
        if not resources:
            log.warning("task %s has no resource and will not be scheduled",node.id)
            return
        self.date_res = {}
        for res, usage in resources :
            self.date_res.setdefault(res.id, begin-1)
        load = node.duration*(1-node.progress)
        date = begin
        if load == 0 and begin == today():
            log.warning("task %s is complete but was never worked on"%node.id)
        while load > 0 and resources :
            for resource, usage in resources:
                if self.date_res[resource.id] < date and resource.is_available(date) \
                   and self.project.get_total_usage(resource.id, date) <= 1-usage :
                    activities.append( (date, date, resource.id, node.id, usage) )
                    self.date_res[resource.id] = date
                    load -= usage
                    if load <= 0:
                        break
            date += 1
        self.project.add_schedule(activities)

    def get_ordered_buckets(self):
        tasks = self.project.root_task.leaves()
        tasks.sort(cmp_tasks)
        buckets = []
        bucket = [None]
        for task in tasks:
            for other in bucket:
                if cmp_tasks(task,other) == 1:
                    bucket = [task]
                    buckets.append(bucket)
                    break
            else:
                bucket.append(task)
        return buckets

    def schedule(self, verbose=0):
        """
        Update the project's schedule
        Return list of errors occured during schedule
        """
        activities = []
        for bucket in self.get_ordered_buckets():
            for leaf in bucket:
                self._process_node(leaf)
        return []


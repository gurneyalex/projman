# -*- coding: iso-8859-1 -*-
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
"""
schedule project without caring about resource conflicts
"""

from mx.DateTime import today

from projman.lib.constants import *

class DumbScheduler(object):
    """
    schedule project without caring about resource conflicts
    nor task constraints
    """

    def __init__(self, project):
        self.project = project

    def _process_node(self, node):
        # get dates
        begin, end = None, None
        for c_type, date, priority in node.get_date_constraints():
            if c_type == BEGIN_AFTER_DATE :
                begin = date # FIXME what if more than one ?
            elif c_type == END_BEFORE_DATE :
                end = date # FIXME what if more than one ?
        if not begin and not end:
            begin = today()

        # add activities
        activities = []
        # collect resources
        if node.TYPE == "milestone":
            self.project.milestones[node.id] = begin
            return []
        node.compute_resources(self.project)
        resources = [self.project.resources[r_id] for r_id in node.get_resource_ids()]
#         if not resources:
#             print "WARNING: task %s has no resource and will not be scheduled"%node.id
        days = {}
        duration = node.duration*(1-node.progress)
        if begin:
            for resource in resources:
                days[resource] = begin
            while duration > 0 and resources:
                for resource in resources:
                    date = days[resource]
#                     while not resource.is_available(date):
#                         date += 1
#                         print date
                    # usage = 1
                    activities.append( (date, date, resource.id, node.id, 1) )
                    days[resource] = date + 1
                duration -= 1
        else:
            for resource in resources:
                days[resource] = end
            while duration > 0 and resources:
                for resource in resources:
                    date = days[resource]
#                     while not resource.is_available(date):
#                         date -= 1
#                         print date
                    # usage = 1
                    activities.append( (date, date, resource.id, node.id, 1) )
                    days[resource] = date - 1
                duration -= 1
        return activities


    def schedule(self, verbose=0, **kw):
        """
        Update the project's schedule
        Return list of errors occured during schedule
        """
        activities = []
        for leaf in self.project.root_task.leaves():
            activities.extend(self._process_node(leaf))
        self.project.add_schedule(activities)
        return []


# -*- coding: iso-8859-1 -*-
# Copyright (c) 2004-2005 LOGILAB S.A. (Paris, FRANCE).
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
Projman - (c)2000-2005 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projects/projman

Manipulate a xml project description.

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

__revision__ = "$Id: resource.py,v 1.4 2005-09-06 17:07:00 nico Exp $"

from mx.DateTime import Time
from logilab.common.deprecation import deprecated_function

from logilab.common.tree import VNode 
from projman.lib.calendar import Calendar

class Resource(VNode):
    """A Resource instance is able to perform Tasks.

    Attributes:
      - type: resource classifier (e.g. 'engineer',
        'manager', 'computer'...)
      - calendar a Calendar instance to indicating when the resource is
         (not) available
      - hourly_rate cost of one hour of work by the resource stored as
         [rate, 'unit']
     """

    TYPE = 'resource'

    def __init__(self, r_id, name, type=None, calendar=None,
                 hourly_rate=0.0, unit='euros'):
        VNode.__init__(self, r_id)
        self.name = name
        self.type = type
        self.calendar = calendar
        self.hourly_rate = [hourly_rate, unit]
        self.id_role = []

    def get_default_wt_in_hours(self):
        """return number of working hours for this resource in a default day"""
        if self.calendar:
            cal = self.get_node_by_id(self.calendar)
            return cal.get_worktime(cal.default_day_type).hours
        else:
            return 8

    def is_available(self, datetime): 
        """ 
        tell if the resource may work on a given day
        """
        if self.calendar:
            c_init = self.get_node_by_id(self.calendar)
            if c_init.availability(datetime):
                return True
            else:
                return False
        else:
            return True
    work_on = deprecated_function(is_available)
    
    def get_worktime(self, datetime):
        """
        return the number of seconds of availability on a given day
        """
        if not self.is_available(datetime):
            return Time(0)
        if self.calendar:
            cal = self.get_node_by_id(self.calendar)
            daytype = cal.get_daytype(datetime)
            return cal.get_worktime(daytype)
        else:
            # if no calendar use default value of 8 hours work
            return Time(8)

class ResourcesSet(VNode):

    TYPE = 'resourcesset'

    def __init__(self, r_id):
        VNode.__init__(self, r_id)

    add_resource = VNode.append
    get_resource = VNode.get_node_by_id
    add_calendar = VNode.append

    def get_calendar(self, tt_id):
        """
        return the time table projman object with id
        """
        calendar = self.get_node_by_id(tt_id)
        assert isinstance(calendar, Calendar)
        return calendar

    def get_resources(self):
        """
        return the list of ids of all resources available in this resources set
        """
        return [r.id for r in self.flatten() if isinstance(r, Resource)]


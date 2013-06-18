# -*- coding: iso-8859-1 -*-
# Copyright (c) 2004-2013 LOGILAB S.A. (Paris, FRANCE).
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
Manipulate a xml project description.
"""

from mx.DateTime import Time
from projman.lib.calendar import Calendar
from projman.lib.resource_role import ResourceRole

class Resource(object):
    """A Resource represents a person that can perform Tasks.

    Attributes:
      - name : A label describing the resource
      - calendar a Calendar instance to indicating when the resource is
         (not) available
      - role_ids: list of the roles that the resource can have
     """

    def __init__(self, r_id, name, calendar, roles):
        self.id = r_id
        self.name = name
        assert isinstance(calendar, Calendar)
        self.calendar = calendar
        assert isinstance(roles, (list, tuple))
        for role in roles:
            assert isinstance(role, ResourceRole)
        self.roles = roles

    def role_ids(self):
        return [role.id for role in self.roles]

    def is_available(self, datetime):
        """
        tell if the resource may work on a given day
        """
        return bool(self.calendar.availability(datetime))

    def get_worktime(self, datetime):
        """
        return the number of seconds of availability on a given day
        """
        if not self.is_available(datetime):
            return Time(0)
        daytype = self.calendar.get_daytype(datetime)
        return self.calendar.get_worktime(daytype)



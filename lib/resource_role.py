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


class ResourceRole(object):
    """A resource_role i used to decribe skills of a resource, and the
        hourly cost, depending of the skill

        attributes:
            - type : qualifiacations (engineer, ...)
            - hourly cost: cost of one hour of work by the resource associated
              to this resource_role

    """

    def __init__(self, id, name=u'', hourly_cost=0.0, unit='EUR'):
        self.id = id
        self.name = name
        self.hourly_cost = hourly_cost
        self.unit = unit


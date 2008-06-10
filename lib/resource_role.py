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


from logilab.common.tree import VNode 

class ResourceRole(VNode):
    """A resource_role i used to decribe skills of a resource, and the 
        hourly cost, depending of the skill
    
        attributes: 
            - type : qualifiacations (engineer, ...)
            - hourly cost: cost of one hour of work by the resource associated 
              to this resource_role
            
    """
    TYPE = 'resource_role'
    
    def __init__(self, id, name=u'', hourly_cost=0.0, unit='EUR'):
        VNode.__init__(self, id)
        self.id = id
        self.name = name
        self.hourly_cost = hourly_cost
        self.unit = unit

class ResourceRoleSet(VNode):

    TYPE = 'resource_role_set'

    def __init__(self, r_id):
        VNode.__init__(self, r_id)

    add_resource_role = VNode.append
    get_resource_role = VNode.get_node_by_id


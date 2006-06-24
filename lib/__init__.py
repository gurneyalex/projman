# Copyright (c) 2000-2003 LOGILAB S.A. (Paris, FRANCE).
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
""" external access point to projman base classes """

__revision__ = "$Id: __init__.py,v 1.4 2005-09-06 17:06:52 nico Exp $"

from projman.lib.task import MileStone, Task
from projman.lib.project import Project
from projman.lib.resource import Resource, ResourcesSet
from projman.lib.calendar import Calendar
from projman.lib._exceptions import *

from logilab.common.date import date_range

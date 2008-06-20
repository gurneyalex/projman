# Copyright (c) 2000-2002 LOGILAB S.A. (Paris, FRANCE).
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
""" Exceptions used in the base model
"""

__revision__ = "$Id: _exceptions.py,v 1.2 2005-06-14 15:22:25 arthur Exp $"

from logilab.common.tree import NodeNotFound


class ProjectValidationError(Exception):
    """ base class for malformed project exceptions """

class MissingRequiredAttribute(ProjectValidationError):
    """ a required attribute is missing """
EX_MISSING_RATTR = 'file %s line %s : Missing required attribute %s to element <%s>'

class MalformedProjectFile(ProjectValidationError):
    """ malformed xml project description """
EX_MALFORMED_FILE = 'file %s line %s : <%s> should not be a child of <%s>'

class MalformedId(ProjectValidationError):
    """ non ascii id attribute"""

class ScheduleCycle (ProjectValidationError):
    """ constraints cycle exception """
EX_CYCLE_DETECTED = "Schedule cycle detected for task '%s'"

class ResourceNotFound (NodeNotFound):
    """ Unable to find resources exception """
EX_RESOURCE_BY_ID_NOT_FOUND = 'Resource id="%s" not found'
EX_RESOURCE_BY_SKILLS_NOT_FOUND = 'No resource with skill(s) "%s" not found'

class DuplicatedResource(Exception):
    """ Duplicated resource id exception """
EX_DUPLICATED_RESOURCE = 'A resource with id="%s" already exists'

class DuplicatedTaskId(Exception):
    """ Duplicated task id exception """
EX_DUPLICATED_TASK = 'A resource with id="%s" already exists'

class TTException(Exception):
    """ a TimeTable exception """

class ViewException(Exception):
    """ too much sub task to generate views """

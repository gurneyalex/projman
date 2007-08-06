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
projman is a python package to schedule and transform xml project file to
gantt diagram, resource diagrams, etc.
"""

import os.path as osp
from projman import extract_extension

DATADIR = osp.abspath(osp.join(osp.dirname(__file__),'data'))

PYGANTT_PROJECT = osp.join(DATADIR, "pygantt_planif.xml")

TAR_TARED_PROJMAN = "projman.prj"
TAR_TARED_SCHEDULED_PROJMAN = "scheduled_projman.prj"
TAR_PROJMAN = "projman.xml"
TAR_TASK_FILE = "tasks.xml"
TAR_RESOURCE_FILE = "resources.xml"
TAR_ACTIVITY_FILE = "activities.xml"

XML_TARED_PROJMAN = "trivial_projman.prj"
XML_PROJMAN ="trivial_projman.xml"
XML_SCHEDULED_PROJMAN ="trivial_scheduled_projman.xml"
XML_SCHEDULED_PROJMAN_FULL ="full_scheduled_projman.xml"
XML_TASK_FILE = "three_tasked_project.xml"
XML_RESOURCE_FILE ="three_resourced_list.xml"
XML_ACTIVITY_FILE = "three_activities.xml"

# Copyright (c) 2000-2006 LOGILAB S.A. (Paris, FRANCE).
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

"""Projman - (c)2005-2006 Logilab - All rights reserved."""

__revision__ ="$Id: command_manager.py,v 1.13 2005-11-09 16:47:34 arthur Exp $"

import logging, logging.config
from xml.dom.ext import PrettyPrint
from projman import LOG_CONF, ENCODING
from projman.scheduling import schedule
from projman.readers import PlannerXMLReader, ProjectXMLReader
from projman.writers import PlannerDOMVisitor, ProjmanDOMVisitor
     #ListTasksDOMWriter, TasksDatesDOMWriter, TasksCostsDOMWriter
from projman.renderers import ResourcesRenderer, GanttRenderer, \
     GanttResourcesRenderer, PILHandler

from projman.interface import PLAN_HEAD

class AbstractCommand:
    """Base class for commands"""
    def __init__(self, option_container):
        # create logger
        try:
            logging.config.fileConfig(LOG_CONF)
        except Exception :
            logging.basicConfig()
        # set members
        self.options = option_container
        self.storage = option_container.storage
        self.project = None

    def execute(self):
        """'main' method: all commands act through this function"""
        raise NotImplementedError

class ConvertCommand(AbstractCommand):
    """to convert files from one type to another
    ex: projman -c -i pygantt -o projman input.xml output.xml
    """
    def __init__(self, option_container):
        AbstractCommand.__init__(self, option_container)
        # set up input
        if self.options.is_reading_pygantt():
            raise DeprecationWarning('pygantt format is not supported anymore')
        elif self.options.is_reading_planner():
            proj_reader = PlannerXMLReader()
        elif self.options.is_reading_projman():
            proj_reader = ProjectXMLReader()
        else:
            raise ValueError , "corrupted input %s"\
                      % str(self.options.state)
        # set up output
        if self.options.is_writing_pygantt():
            raise DeprecationWarning('pygantt format is not supported anymore')
        elif self.options.is_writing_planner():
            self.dom_visitor = PlannerDOMVisitor()
        elif self.options.is_writing_projman():
            self.dom_visitor = ProjmanDOMVisitor()
        else:
            raise ValueError , "corrupted output %s"\
                  % str(self.options.state)
        # load project
        self.project = self.storage.load(proj_reader)

    def execute(self):
        """read input, convert"""
        if not self.options.is_writing_projman():
            doms = self.dom_visitor.visit(self.project)
            # write_trees(doms, self.storage.output, writer=PrettyPrint)
            raise NotImplementedError()
        else:
            self.storage.save(self.project)
        
class ScheduleCommand(AbstractCommand):
    """to schedule project
    ex:  projman -s -I projman.xml schedule.xml
    """
    def __init__(self, option_container):
        AbstractCommand.__init__(self, option_container)
        # set up input
        self.project = self.storage.load()

    def execute(self):
        """read input, schedule"""
        #schedule
        schedule(self.project, self.options.type)
        # write result
        self.storage.save(self.project, write_schedule=True,
                          include_reference=self.options.is_including_reference())

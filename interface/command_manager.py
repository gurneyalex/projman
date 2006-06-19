#!/usr/bin/python2.2
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

"""Projman - (c)2005 Logilab - All rights reserved."""

__revision__ ="$Id: command_manager.py,v 1.13 2005-11-09 16:47:34 arthur Exp $"

import logging, logging.config
from xml.dom.ext import PrettyPrint
from projman import LOG_CONF, ENCODING
from projman.scheduling import schedule
from projman.readers import PlannerXMLReader, ProjectXMLReader
from projman.writers import PlannerDOMVisitor, ProjmanDOMVisitor, \
     ListTasksDOMWriter, TasksDatesDOMWriter, TasksCostsDOMWriter
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
        
class DiagramCommand(AbstractCommand):
    """    to generate diagrams (resources, gantt, etc.)
    ex: projman -d --diagram-type=gantt projman.xml image.png
    """
    def __init__(self, option_container):
        AbstractCommand.__init__(self, option_container)
        self.renderer = None
        # set up input
        self.project = self.storage.load()
        if not self.project._is_scheduled:
            print 'WARNING : you are generating a diagram for an unscheduled project.'
            print 
            print PLAN_HEAD
        # set diagram renderer
        """read input, draw, write result"""
        if self.options.is_image_renderer():
            handler = PILHandler(self.options.get_image_format())
            if self.options.is_resource_type():
                self.renderer = ResourcesRenderer(self.options, handler)
            elif self.options.is_gantt_type():
                self.renderer = GanttRenderer(self.options, handler)
            elif self.options.is_gantt_resource_type():
                self.renderer = GanttResourcesRenderer(self.options, handler)
            else:
                raise ValueError("corrupted image format  %s"
                                 % self.options.state)
        elif self.options.is_html_renderer:
            from projman.renderers.HTMLRenderer import ResourcesHTMLRenderer
            self.renderer = ResourcesHTMLRenderer(self.options.get_render_options())
        else:
            raise ValueError , "corrupted renderer %s"% str(self.options.state)

    def execute(self):
        """read input, draw"""
        output_f = open(self.storage.output, 'w')
        if self.options.is_image_renderer():
            self.renderer.render(self.project, output_f)
        else:
            title = 'Resources'.encode(ENCODING)
            output_f.write("""<html>
            <head><title>%s</title></head>
            <body><h1 align='center'>Resources %s</h1>
            <h3>begin on %s, possible end to %s</h3>\n"""% (
                title,
                dom_objects.schedules[0].get_view_begin().date,
                dom_objects.schedules[0].get_view_end().date))
            self.renderer.render(self.project, output_f)
            output_f.write("</body></html>")
                

class XmlCommand(AbstractCommand):
    """    to generate xml views (list, cost , date)
    ex: projman -x -v cost projman.xml view.xml
    """
    def __init__(self, option_container):
        AbstractCommand.__init__(self, option_container)
        self.visitor = None
        # set up input
        self.project = self.storage.load()
        #schedule
        # FIXME: schedule or not schedule, that is the question
        # schedule(self.project)
        # import correct visitor
        if self.options.is_list_view():
            self.visitor = ListTasksDOMWriter(self.project, self.options)
        elif self.options.is_date_view():
            self.visitor = TasksDatesDOMWriter(self.project, self.options)
        elif self.options.is_cost_view():
            self.visitor = TasksCostsDOMWriter(self.project, self.options)
        else:
            raise ValueError("corrupted view %s" % (self.options.state,))

    def execute(self):
        """read input, make view"""
        output = file(self.storage.output, 'w')
        output.write(self.visitor.as_xml_string())
        output.close()

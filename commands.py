# Copyright (c) 2006 LOGILAB S.A. (Paris, FRANCE).
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
"""provide classes for projman commands."""

import logging

from logilab.common.clcommands import BadCommandUsage, Command, \
     register_commands

from projman.__pkginfo__ import version
from projman.views import document
from projman.readers import ProjectXMLReader
from projman.writers.projman_writer import write_schedule_as_xml, indent
from projman.views import ALL_VIEWS

# verbosity to logging level mapping
LEVELS = {
    0 : logging.ERROR,
    1 : logging.WARN,
    2 : logging.INFO,
    3 : logging.DEBUG,
    }

class ProjmanCommand(Command):
    """base class providing common behaviour for projman commands"""
    def __init__(self, __doc__):
        Command.__init__(self, __doc__=__doc__, version=version)

    options = (
        ('project-file',
         {'short': 'f',
          'type' : 'string', 'metavar': '<project description file>',
          'default': 'project.xml',
          'help': 'specify the project description file to use',
          }
         ),
        ('verbose',
         {'type' : 'int', 'metavar': '<0..3>',
          'default': 0,
          'help': 'display additional information during execution of projman',
          }
         ),
        ('task-root',
         {'short': 'R',
          'type' : 'string', 'metavar': '<virtual task root>',
          'default': None,
          'help': 'identifier of a task to use as root',
          }
         ),
        ('factorized_days',
         {'type' : 'int', 'metavar' : '<1, 2 or 4>',
          'default': 1,
          'help' : 'schedule and display task in day(1), half day(2) or quarter of day(4).' 
                   'Attention: if you decide to use this option, be coherent ' 
                   'for next projman commands ! '
          }
         ),
        )

    def run(self, args):
        """run the command with its specific arguments"""
        loglevel = LEVELS.get(self.config.verbose, logging.WARN)
        logging.basicConfig(level=loglevel)
        reader = ProjectXMLReader(self.config.project_file, self.config.task_root)
        self.project, self.files = reader.read()
        self.project.factor = self.config.factorized_days
        self._run(args)

    def _run(self, args):
        raise NotImplementedError

# Concrete commands ###########################################################
class CheckCommand(ProjmanCommand):
    "check the definition of a projman problem"
    name = 'check'
    max_args = 0
    arguments = ''

    def _run(self, args):
        from projman.checker.problem_checker import Checker
        # validate xml format
        reader = ProjectXMLReader(self.config.project_file, self.config.task_root)
        # validate projman problem
        check_project = Checker(self.project, self.config.verbose)
        check_project.problem_checker()

class ScheduleCommand(ProjmanCommand):
    """schedule a project"""
    name = 'schedule'
    max_args = 0
    arguments = ''

    options = ProjmanCommand.options + (
        ('type',
         {'type' : 'choice', 'metavar': '<schedule type>',
          'choices': ('dumb', 'simple', 'csp'),
          'default': 'csp',
          'help': 'scheduling method (dumb, simple or csp)',
          }
         ),
        ('time', 
         {'type' : 'int', 'metavar': '<1...>',
          'default': 400000,
          'help': 'stop the programm after time'
          }
         ),
        )

    def _run(self, views):
        from projman.scheduling import schedule
        from projman.checker.problem_checker import Checker
        # validate projman problem
        check = Checker(self.project, self.config.verbose)
        check.problem_checker()
        if check.errors:
            return
        rounder = 0
        schedule(self.project, self.config)
        while (self.project.nb_solution == 0 and rounder < 2):
            print '\nAttention: No valid solution !'
            print "constraints with priority", self.project.priority,
            print 'are dropped ...\n'
            reader = ProjectXMLReader(self.config.project_file,
                                self.config.task_root)
            self.project, self.files = reader.read()
            self.project.factor = self.config.factorized_days
            rounder += 1
            self.project.priority -= rounder
            schedule(self.project, self.config)
            nb_solution = self.project.nb_solution
        write_schedule_as_xml(self.files['schedule'], self.project)


class ViewCommand(ProjmanCommand):
    """generate XML view(s) from a project file (usually using Documentor +
    docbook dialect)
    """
    name = 'view'
    min_args = 1
    arguments = "|".join(ALL_VIEWS.keys())

    options = ProjmanCommand.options + (
        ('output',
         {'short': 'o',
          'type' : 'string', 'metavar': '<output xml file>',
          'default': 'output.xml',
          'help': 'specific output file to use',
          }
         ),
        ('display-dates',
         {'type' : 'yn', 'metavar': '<y or n>',
          'default': True,
          'help': 'display task\'s begin and end date (tasks-list view only)',
          }
         ),
        ('level',
         {'type': 'int', 'metavar': '<1, ... >',
         'default' : 3,
         'help': 'display tasks on  1, 2, or more level in views tables',
          }
         ),
        )

    def _run(self, views):
        tree = document("root")
        if list(views) == ["all",]:
            views = ALL_VIEWS.keys()
        for viewname in views:
            try:
                viewklass = ALL_VIEWS[viewname]
            except KeyError:
                raise BadCommandUsage('unknown view %s' % viewname)
            view = viewklass(self.config)
            view.generate(tree, self.project)
        output = file(self.config.output, 'w')
        indent(tree.getroot())
        tree.write( output, encoding="UTF-8" )
        output.close()


class DiagramCommand(ProjmanCommand):
    """generate diagrams from a project file (resources, gantt, etc.)"""
    name = 'diagram'
    min_args = 1
    arguments = '<diagram name>...'

    options = ProjmanCommand.options + (
        ('output',
         {'short': 'o',
          'type' : 'string', 'metavar': '<output xml file>',
          'default': None,
          'help': 'specific output file to use when a single diagram is generated',
          }
         ),
        ('selected-resource',
         {'type' : 'string', 'metavar': '<resource identifier>',
          'default': None,
          'help': 'specifies the id of the resource to take in account for '
                  'resources diagrams',
          }
         ),
        ('format',
         {'type' : 'choice', 'metavar': '<format>',
          'choices': ('svg', 'png'), # 'html'  ## png ne marche plus
          'default': 'svg',
          'help': 'specifies the output format for diagrams',
          }
         ),
        ('depth',
         {'type' : 'int', 'metavar': '<level>',
          'default': 0,
          'help': 'specifies the depth to visualize for diagrams, default to '
                  '0 which means all the tree',
          }
         ),
        ('timestep',
         {'type' : 'string', 'metavar': '<day, week, month>',
          'default': 'day',
          'help': 'timeline increment for diagram',
          }
         ),
        ('view-begin',
         {'type' : 'date', 'metavar': '<yyyy/mm/dd>',
          'default': None,
          'help': 'begin date for diagram view',
          }
         ),
        ('view-end',
         {'type' : 'date', 'metavar': '<yyyy/mm/dd>',
          'default': None,
          'help': 'end date for diagram view',
          }
         ),
        ('del-ended',
         {'type' : 'yn', 'metavar': '<y or n>',
          'default': False,
          'help': 'do not display in resource diagram tasks wich are completed, '
                  'meaning that time of work on them equals theirs duration.',
          }
         ),
        ('del-empty',
         {'type' : 'yn', 'metavar': '<y or n>',
          'default': False,
          'help': 'do not display in resource diagram tasks wich are not '
                  'worked during given period',
          }
         ),
        )

    def _run(self, diagrams):
        #if self.config.renderer == 'html':
        #    from projman.renderers.HTMLRenderer import ResourcesHTMLRenderer
        #    renderer = ResourcesHTMLRenderer(self.options.get_render_options())
        #else:
        from projman.renderers import ResourcesRenderer, GanttRenderer, \
             GanttResourcesRenderer, HandlerFactory
        handler = HandlerFactory(self.config.format)
        known_diagrams = {
            'gantt': GanttRenderer,
            'resources': ResourcesRenderer,
            'gantt-resources': GanttResourcesRenderer,
            }
        if self.config.output and len(diagrams)>1:
            print "You specified more than one diagram with an output file name"
            print "*** only the last one will be printed ***"
        for diagram in diagrams:
            try:
                renderer = known_diagrams[diagram](self.config, handler)
            except KeyError:
                raise BadCommandUsage('unknown diagram %s' % diagram)
        if self.config.timestep:
            if not self.config.timestep in ['day', 'month', 'week']:
                raise BadCommandUsage('non valid timestep %s' %self.config.timestep) 
            
            output = self.config.output or '%s.%s' % (diagram, self.config.format)
            stream = handler.get_output(output)
            renderer.render(self.project, stream)



class DiagramCommand2(ProjmanCommand):  # a test...
    """generate diagrams from a project file (resources, gantt, etc.)"""
    name = 'diagram2'
    min_args = 1
    arguments = '<diagram name>...'

    options = ProjmanCommand.options

    def _run(self, diagrams):
        #if self.config.renderer == 'html':
        #    from projman.renderers.HTMLRenderer import ResourcesHTMLRenderer
        #    renderer = ResourcesHTMLRenderer(self.options.get_render_options())
        #else:
        from projman.renderers.gantt2 import GanttRenderer2
        gantt = GanttRenderer2(self.config, self.project)
        gantt.render("gantt2.svg")
        gantt.save()


register_commands((CheckCommand, ScheduleCommand, ViewCommand, DiagramCommand))

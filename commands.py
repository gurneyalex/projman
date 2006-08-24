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

import os, os.path as osp
from xml.dom.ext import PrettyPrint

from logilab.common.clcommands import BadCommandUsage, Command, \
     pop_arg, register_commands

from projman.__pkginfo__ import version
from projman.interface.file_manager import ProjectStorage
from projman.views import document



VIRTUAL_ROOT_OPTION = ('task-root',
                       {'short': 'R',
                        'type' : 'string', 'metavar': '<virtual task root>',
                        'default': None,
                        'help': 'identifier of a task to use as root',
                        })


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
        ('expanded',
         {'short': 'X',
          'type' : 'yn', 'metavar': '<y or n>',
          'default': True,
          'help': 'use .xml file instead of a projman file (.prj)',
          }
         ),
        ('verbose',
         {'type' : 'yn', 'metavar': '<y or n>',
          'default': False,
          'help': 'display additional information during execution of projman',
          }
         ),        
        )


## class PMViewCommand(ProjmanCommand):
##     """base class providing common behaviour for projman view commands"""
    
##     arguments = '<output file>'    

##     def run(self, args):
##         """run the command with its specific arguments"""
##         output = pop_arg(args)
##         repo_in, input = osp.split(osp.abspath(self.config.project_file))
##         self.storage = ProjectStorage(repo_in, input, output,
##                                       archive_mode=self.config.expanded,
##                                       virtual_task_root=getattr(self.config, 'task_root', None))
##         self.project = self.storage.load()
##         self._run()
    
##     def _run(self):
##         view = self._get_view()
##         root = document("dr:root")
##         view.generate(root, self.project)
##         output = file(self.storage.output, 'w')
##         PrettyPrint(root, stream=output)
##         output.close()
    
## class PMTableCommand(PMViewCommand):
##     options = PMViewCommand.options + (
##         ('format',
##          {'short': 'F',
##           'type' : 'choice', 'metavar': '<output format>',
##           'choices': ('docbook', 'html', 'csv'),
##           'default': 'docbook',
##           'help': 'identifier of a task to use as root',
##           }
##          ),
##         )

    
## class PMSectionCommand(PMViewCommand):
##     options = PMViewCommand.options + (
##         ('format',
##          {'short': 'F',
##           'type' : 'choice', 'metavar': '<output format>',
##           'choices': ('docbook', 'html'),
##           'default': 'docbook',
##           'help': 'identifier of a task to use as root',
##           }
##          ),
##         )

# Concrete commands ###########################################################


class ViewCommand(ProjmanCommand):
    """get a XML view from a project file (usually using Documentor + docbook
    dialect)
    """
    name = 'view'
    arguments = '<view name>...'    

    options = ProjmanCommand.options + (
        ('output',
         {'short': 'o',
          'type' : 'string', 'metavar': '<output xml file>',
          'default': 'output.xml',
          'help': 'specific output file to use',
          }
         ),
        #('format',
        # {'short': 'F',
        #  'type' : 'choice', 'metavar': '<output format>',
        #  'choices': ('docbook', 'html', 'csv'),
        #  'default': 'docbook',
        #  'help': 'identifier of a task to use as root',
        #  }
        # ),
        VIRTUAL_ROOT_OPTION,
        ('display-dates',
         {'type' : 'yn', 'metavar': '<y or n>',
          'default': True,
          'help': 'display task\'s begin and end date (tasks-list view only)',
          }
         ),
        
        )

    def run(self, args):
        """run the command with its specific arguments"""
        if not args:
            raise BadCommandUsage('missing argument')
        output = self.config.output
        repo_in, input = osp.split(osp.abspath(self.config.project_file))
        self.storage = ProjectStorage(repo_in, input, output,
                                      archive_mode=self.config.expanded,
                                      virtual_task_root=getattr(self.config, 'task_root', None))
        self.project = self.storage.load()
        self._run(args)
    
    def _run(self, views):
        from projman.views import ALL_VIEWS
        root = document("dr:root")
        for viewname in views:
            try:
                viewklass = ALL_VIEWS[viewname]
            except KeyError:
                raise BadCommandUsage('unknown view %s' % viewname)
            view = viewklass(self.config)
            view.generate(root, self.project)
        output = file(self.storage.output, 'w')
        PrettyPrint(root, stream=output)
        output.close()

register_commands((ViewCommand,))

## from projman.views import CostTableView, CostParaView, RatesSectionView, \
##      TasksListSectionView
    
## class RatesSectionCommand(PMSectionCommand):
##     """output a section indicating resources rates"""
##     name = 'rates-section'
##     def _get_view(self):
##         return RatesSectionView(self.config)

## class CostTableCommand(PMTableCommand):
##     """output a tasks'cost table"""
##     name = 'cost-table'
##     options = PMTableCommand.options + (
##         VIRTUAL_ROOT_OPTION,
##         )
##     def _get_view(self):
##         return CostTableView(self.config)
        
## class CostParaCommand(PMTableCommand):
##     """output a paragraph indicating the total cost of selected tasks"""
##     name = 'cost-para'
##     options = PMTableCommand.options + (
##         VIRTUAL_ROOT_OPTION,
##         )
##     def _get_view(self):
##         return CostParaView(self.config)
    
## class TasksListSectionCommand(PMSectionCommand):
##     """output a section indicating resources rates"""
##     name = 'tasks-list-section'
##     options = PMTableCommand.options + (
##         VIRTUAL_ROOT_OPTION,
##         ('display-dates',
##          {'type' : 'yn', 'metavar': '<y or n>',
##           'default': True,
##           'help': 'display task\'s begin and end date',
##           }
##          ),
##         )
##     def _get_view(self):
##         return TasksListSectionView(self.config)


## register_commands((CostTableCommand, CostParaCommand,
##                    RatesSectionCommand,
##                    TasksListSectionCommand))

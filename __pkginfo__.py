# -*- coding: iso-8859-1 -*-
# pylint: disable-msg=W0622
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""Copyright (c) 2000-2009 LOGILAB S.A. (Paris, FRANCE).
http://www.logilab.fr/ -- mailto:contact@logilab.fr  
"""

modname = 'projman'

numversion = (0, 13, 6)
version = '.'.join([str(num) for num in numversion])


license = 'GPL'
copyright = '''Copyright © 2000-2009 LOGILAB S.A. (Paris, FRANCE).
http://www.logilab.fr/ -- mailto:contact@logilab.fr'''

short_desc = "tool for project management"

long_desc = """projman is a tool for project management and diagrams creation,
as Gantt diagram and resources activities diagram.
It includes lots of functionnalties as
* scheduling of a project
* managing work-groups'actvities
* Gantt diagrams generation
* Resources'usage diagrams generation
* generation of xml doc (under docbook dtd) to list tasks, evaluate costs

All different format and output are XML files.
"""

author = "Logilab"
author_email = "devel@logilab.fr"

web = "http://www.logilab.org/projects/%s" % modname
ftp = "ftp://ftp.logilab.org/pub/%s" % modname
mailinglist = "http://lists.logilab.org/mailman/listinfo/management-projects"


scripts = ['bin/projman', ]
data_files = [['share/projman',
               ['fonts/Arial_12_72.pil',
                'fonts/Arial Bold_12_72.pil',
                'fonts/Arial Italic_12_72.pil',
                'fonts/Arial Bold Italic_12_72.pil',
                'fonts/Arial_12_72.pbm',
                'fonts/Arial Bold_12_72.pbm',
                'fonts/Arial Italic_12_72.pbm',
                'fonts/Arial Bold Italic_12_72.pbm'],
               ['share/projman/examples',
                ['scheduling/sample.cc',
                 'scheduling/projman_gecode.cc',
                 'scheduling/makefile',
                 'scheduling/projman_gecode.hh',
                 'scheduling/projman_problem.hh',
                 'scheduling/timer.hh',
                ]
               ] 
              ]
             ]

debian_name = 'projman'
debian_maintainer = 'Alexandre Fayolle ' 
debian_maintainer_email = 'alexandre.fayolle@logilab.fr'
pyversions = ["2.5"]
 
from os.path import join
include_dirs = [join('test', 'data')]

from distutils.core import Extension
ext_modules = [Extension('projman.scheduling.gcsp',
                         sources = ['scheduling/gcspmodule.cc',
                                    'scheduling/projman_gecode.cc',
                                    'scheduling/projman_problem.cc',
                         ],
                         libraries=['boost_python-mt', 'gecodeint', 'gecodeset',
                                    'gecodeminimodel', 'gecodekernel', 'gecodesearch'],
                         depends=['scheduling/projman_gecode.hh',
                                  'scheduling/projman_problem.hh',
                                  ],
                         language='c++',
                        )
             ]



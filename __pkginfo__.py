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
"""Copyright (c) 2000-2014 LOGILAB S.A. (Paris, FRANCE).
http://www.logilab.fr/ -- mailto:contact@logilab.fr
"""

modname = 'projman'

numversion = (0, 16, 1)
version = '.'.join([str(num) for num in numversion])

license = 'GPL'
copyright = '''Copyright © 2000-2014 LOGILAB S.A. (Paris, FRANCE).
http://www.logilab.fr/ -- mailto:contact@logilab.fr'''

short_desc = "project management tool"

long_desc = """projman is a tool for project management and diagrams creation,
like Gantt diagrams and resources activities diagram.

It includes many functionnalties:
* scheduling of a project,
* managing work-groups'actvities,
* Gantt diagrams generation,
* resources usage diagrams generation,
* generation of xml doc (under docbook dtd) to list tasks, evaluate costs.

Input and output files are easily parseable XML files.
"""

author = "Logilab"
author_email = "devel@logilab.fr"

web = "http://www.logilab.org/projects/%s" % modname
ftp = "ftp://ftp.logilab.org/pub/%s" % modname
mailinglist = "http://lists.logilab.org/mailman/listinfo/management-projects"

scripts = ['bin/projman', 'bin/projman-gui']
data_files = [['share/projman',
               ['fonts/Arial_12_72.pil',
                'fonts/Arial Bold_12_72.pil',
                'fonts/Arial Italic_12_72.pil',
                'fonts/Arial Bold Italic_12_72.pil',
                'fonts/Arial_12_72.pbm',
                'fonts/Arial Bold_12_72.pbm',
                'fonts/Arial Italic_12_72.pbm',
                'fonts/Arial Bold Italic_12_72.pbm',
                'data/projedit.glade'],
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
pyversions = ["2.5","2.6","2.7"]

__depends__ = {'logilab-common': '>= 0.59.0',
               'logilab-doctools': '>= 0.4.0',
               'python-gtksourceview': '>= 2.2.0',
               'python-docutils': None,
               'PIL': None,
               }

import sys
from os.path import join
include_dirs = [join('test', 'data')]

from distutils.core import Extension

def gecode_version():
    import os, subprocess
    version = [0,0,0]
    if os.path.exists('data/gecode_version.cc'):
        try:
            res=os.system("g++ -o gecode_version data/gecode_version.cc")
            p=subprocess.Popen("./gecode_version",stdout=subprocess.PIPE)
            vers = p.stdout.read()
            version = [int(c) for c in vers.strip().split('.')]
        except OSError:
            pass
    return version

def encode_version(a,b,c):
    return ((a<<16)+(b<<8)+c)

GECODE_VERSION = encode_version(*gecode_version())
PYTHON_VERSION = sys.version_info[:2]
BOOST_LIB = 'boost_python-mt-py%s%s' % PYTHON_VERSION
ext_modules = [Extension('projman.scheduling.gcsp',
                         sources = ['scheduling/gcspmodule.cc',
                                    'scheduling/projman_gecode.cc',
                                    'scheduling/projman_problem.cc',
                         ],
                         libraries=[BOOST_LIB, 'gecodeint', 'gecodeset',
                                    'gecodekernel', 'gecodesearch'],
                         depends=['scheduling/projman_gecode.hh',
                                  'scheduling/projman_problem.hh',
                                  ],
                         language='c++',
                         extra_compile_args=['-DGE_VERSION=%s' % GECODE_VERSION],
                        )
             ]

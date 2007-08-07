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
"""
Projman - (c)2005 Logilab - All rights reserved.
"""

import os.path as osp
import tempfile, shutil

from logilab.common import testlib
from projman.renderers import PILHandler, GanttRenderer, ResourcesRenderer

from projman.test import DATADIR
from projman.readers import ProjectXMLReader

CONFIG = testlib.AttrObject(del_ended=False, del_empty=False,
                            timestep=1, depth=0, selected_resource=None,
                            view_begin=None, view_end=None,
                            project_file=osp.join(DATADIR,"full_scheduled_projman.xml"),
                            task_root=None,
                            )

class RenderTest(testlib.TestCase):

    def setUp(self):
        project_file = osp.join(DATADIR,"full_scheduled_projman.xml")
        reader = ProjectXMLReader(project_file)
        self.project, files = reader.read()
        
        project_file2 = osp.join(DATADIR,"trivial_scheduled_projman.xml")
        reader = ProjectXMLReader(project_file2)
        self.project2, files = reader.read()

        self.tmpdir = tempfile.mkdtemp()
        self.file = file(osp.join(self.tmpdir, 'render_test.png'), 'w')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_gantt_diagram(self):
        handler = PILHandler('png')
        renderer = GanttRenderer(CONFIG, handler)
        renderer.render(self.project, self.file)

    def test_resource_diagram(self):
        handler = PILHandler('png')
        renderer = ResourcesRenderer(CONFIG, handler)
        renderer.render(self.project, self.file)

    def test_gantt_diagram2(self):
        handler = PILHandler('png')
        renderer = GanttRenderer(CONFIG, handler)
        renderer.render(self.project2, self.file)

    def test_resource_diagram2(self):
        handler = PILHandler('png')
        renderer = ResourcesRenderer(CONFIG, handler)
        renderer.render(self.project2, self.file)


if __name__ == '__main__':
    testlib.unittest_main()

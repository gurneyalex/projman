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

from logilab.common import testlib
from projman.renderers import PILHandler, GanttRenderer, ResourcesRenderer
from projman.storage import ProjectStorage

from projman.commands import ConfigAdapter

config = ConfigAdapter(testlib.AttrObject(del_ended=False, del_empty=False,
                                          timestep=1, depth=0, selected_resource=None,
                                          view_begin=None, view_end=None))

class RenderTest(testlib.TestCase):

    def setUp(self):
        self.project = ProjectStorage("data", "full_scheduled_projman.xml",
                                      archive_mode=False).load()
        self.project2 = ProjectStorage("data", "trivial_scheduled_projman.xml",
                                       archive_mode=False).load()
        self.file = open('generated/render_test.png', 'w')

    def test_gantt_diagram(self):
        handler = PILHandler('png')
        renderer = GanttRenderer(config, handler)
        renderer.render(self.project, self.file)

    def test_resource_diagram(self):
        handler = PILHandler('png')
        renderer = ResourcesRenderer(config, handler)
        renderer.render(self.project, self.file)

    def test_gantt_diagram2(self):
        handler = PILHandler('png')
        renderer = GanttRenderer(config, handler)
        renderer.render(self.project2, self.file)

    def test_resource_diagram2(self):
        handler = PILHandler('png')
        renderer = ResourcesRenderer(config, handler)
        renderer.render(self.project2, self.file)
    
    
if __name__ == '__main__':
    testlib.unittest_main()

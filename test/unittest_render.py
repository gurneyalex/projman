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

__revision__ ="$Id: unittest_render.py,v 1.2 2005-09-06 18:02:22 nico Exp $"

import unittest

from projman.renderers import PILHandler, GanttRenderer, ResourcesRenderer
from projman.interface.file_manager import ProjectStorage
from projman.interface.option_manager import OptionDiagram

class RenderTest(unittest.TestCase):

    def setUp(self):
        self.project = ProjectStorage("data", "full_scheduled_projman.xml",
                                      archive_mode=False).load()
        self.project2 = ProjectStorage("data", "trivial_scheduled_projman.xml",
                                       archive_mode=False).load()
        self.options = OptionDiagram([("-d", None),
                                      ("-X", None),
                                      ("--diagram-type", 'gantt'),
                                      ], ["data/full_scheduled_projman.xml"])
        self.options2 = OptionDiagram([("-d", None),
                                       ("-X", None),
                                       ], ["data/trivial_scheduled_projman.xml"])
        self.file = open('generated/render_test.png', 'w')

    def test_gantt_diagram(self):
        handler = PILHandler(self.options.get_image_format())
        renderer = GanttRenderer(self.options, handler)
        renderer.render(self.project, self.file)

    def test_resource_diagram(self):
        handler = PILHandler(self.options.get_image_format())
        renderer = ResourcesRenderer(self.options, handler)
        renderer.render(self.project, self.file)

    def test_gantt_diagram2(self):
        handler = PILHandler(self.options2.get_image_format())
        renderer = GanttRenderer(self.options2, handler)
        renderer.render(self.project, self.file)

    def test_resource_diagram2(self):
        handler = PILHandler(self.options2.get_image_format())
        renderer = ResourcesRenderer(self.options2, handler)
        renderer.render(self.project, self.file)
    
    
if __name__ == '__main__':
    unittest.main()

# Copyright (c) 2000-2004 LOGILAB S.A. (Paris, FRANCE).
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
"""Projman - (c)2004 Logilab - All rights reserved."""

__revision__ ="$Id: unittest_command_manager.py,v 1.5 2005-09-06 18:27:44 nico Exp $"

import shutil, os, tempfile
import os.path as osp

from logilab.common import testlib

from projman.interface.option_manager import OptionConvert, \
     OptionSchedule, OptionDiagram, OptionXmlView, OptionManager, \
     DEFAULT_PROJMAN_EXPORT, DEFAULT_PLANNER_EXPORT
from projman.interface.command_manager import ConvertCommand
from projman.interface.file_manager import SUFFIX, \
     RESOURCES_NAME, TASKS_NAME, ACTIVITIES_NAME, SCHEDULE_NAME, SCHEDULE_KEY
from projman.test import DATADIR
from projman.test import PLANNER_PROJECT, XML_PROJMAN, XML_SCHEDULED_PROJMAN, \
     XML_SCHEDULED_PROJMAN_FULL, TAR_PROJMAN, make_project_name

XML_FILE_NAMES =  [osp.join(DATADIR, RESOURCES_NAME),
                   osp.join(DATADIR, TASKS_NAME),
                   osp.join(DATADIR, ACTIVITIES_NAME)]

DEFAULT_PROJMAN_EXPORT = osp.join(DATADIR, DEFAULT_PROJMAN_EXPORT)
XML_PROJMAN = osp.join(DATADIR, XML_PROJMAN)
XML_SCHEDULED_PROJMAN = osp.join(DATADIR, XML_SCHEDULED_PROJMAN)
XML_SCHEDULED_PROJMAN_FULL = osp.join(DATADIR, XML_SCHEDULED_PROJMAN_FULL)
TAR_PROJMAN = osp.join(DATADIR, TAR_PROJMAN)
SCHEDULE = "out_schedule.xml"
SCHEDULE_PATH = osp.join(DATADIR, SCHEDULE)

class AbstractCommandTest(testlib.TestCase):
    """testing """
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        
class ConvertTest(AbstractCommandTest):
    """testing """
    
    def test_planner(self):
        self.planner = OptionConvert([("-c", None),
                                      ("-X", None),
                                      ("-i", 'planner')],
                                     [PLANNER_PROJECT])\
                      .get_command().execute()
        self.assert_(not osp.exists(make_project_name(DEFAULT_PROJMAN_EXPORT)))
        self.assert_(osp.exists(DEFAULT_PROJMAN_EXPORT))
        for file_name in XML_FILE_NAMES:
            self.assert_(osp.exists(file_name))
 
    
class ScheduleTest(AbstractCommandTest):
    """testing """
    
    def setUp(self):
        AbstractCommandTest.setUp(self)
        self.projman = "tmp_projman.xml"
        self.projman_path =  osp.join(DATADIR, "tmp_projman.xml")
        shutil.copyfile(XML_PROJMAN, self.projman_path)

    def test_default(self):
        # schedule xml and wrap into prj
        OptionSchedule([("-s", None), ('--type', 'csp')],
                       [self.projman_path, SCHEDULE])\
                       .get_command().execute()
        self.assert_(osp.exists(SCHEDULE_PATH))
        # schedule prj and unwrap
        OptionSchedule([("-s", None), ("-X", None), ('--type', 'csp')],
                       [make_project_name(self.projman_path), SCHEDULE]
                       ).get_command().execute()
        files = OptionManager([("-X", None)],
                              [make_project_name(self.projman_path)]).storage
        self.assertEquals(files.file_names[SCHEDULE_KEY], SCHEDULE_NAME)
        self.assert_(osp.exists(SCHEDULE_PATH))
    
    def test_include(self):
        # schedule xml and wrap into prj
        OptionSchedule([("-s", None), ("-I", None), ('--type', 'csp')],
                       [self.projman_path, SCHEDULE])\
                       .get_command().execute()
        self.assert_(not osp.exists(SCHEDULE_PATH))
        # schedule prj and unwrap
        OptionSchedule([("-s", None), ("-I", None), ("-X", None),
                        ('--type', 'csp')],
                       [make_project_name(self.projman_path), SCHEDULE]
                       ).get_command().execute()
        files = OptionManager([("-X", None)],
                              [make_project_name(self.projman_path)]).storage
        self.assertEquals(files.file_names[SCHEDULE_KEY], SCHEDULE)
        self.assert_(osp.exists(SCHEDULE_PATH))

class DiagramTest(AbstractCommandTest):
    
    def test_gantt(self):
        OptionDiagram([("-d", None),
                       ("--timestep", '7')],
                      [XML_SCHEDULED_PROJMAN])\
                       .get_command().execute()
        self.assert_(osp.exists("gantt.png"))
        OptionDiagram([("-d", None),
                       ("--diagram-type", 'gantt'),
                       ("--timestep", '7')],
                      [XML_SCHEDULED_PROJMAN,
                       osp.join(self.tmpdir, "out_gantt.png")])\
                       .get_command().execute()
        self.assert_(osp.exists(osp.join(self.tmpdir, "out_gantt.png")))
    
    def test_gantt2(self):
        OptionDiagram([("-d", None),
                       ("--timestep", '7')],
                      [XML_SCHEDULED_PROJMAN_FULL])\
                       .get_command().execute()
        self.assert_(osp.exists("gantt.png"))
        OptionDiagram([("-d", None),
                       ("--diagram-type", 'gantt'),
                       ("--timestep", '7')],
                      [XML_SCHEDULED_PROJMAN_FULL,
                       osp.join(self.tmpdir, "out_gantt.png")]
                      ).get_command().execute()
        self.assert_(osp.exists(osp.join(self.tmpdir, "out_gantt.png")))

    def test_resources(self):
        OptionDiagram([("-d", None),
                       ("--diagram-type", 'resources')],
                      [XML_SCHEDULED_PROJMAN])\
                       .get_command().execute()
        self.assert_(osp.exists("resources.png"))
        OptionDiagram([("-d", None),
                       ("--diagram-type", 'resources'),
                       ("--renderer", 'tiff')],
                      [XML_SCHEDULED_PROJMAN,
                       osp.join(self.tmpdir, "out_ress.tiff")]
                      ).get_command().execute()
        self.assert_(osp.exists(osp.join(self.tmpdir, "out_ress.tiff")))
    
    def test_gantt_resources(self):
        OptionDiagram([("-d", None),
                       ("--diagram-type", 'gantt-resources')],
                      [XML_SCHEDULED_PROJMAN])\
                       .get_command().execute()
        self.assert_(osp.exists("gantt-resources.png"))
        OptionDiagram([("-d", None),
                       ("--diagram-type", 'gantt-resources')],
                      [XML_SCHEDULED_PROJMAN,
                       osp.join(self.tmpdir, "both.png")]
                      ).get_command().execute()
        self.assert_(osp.exists(osp.join(self.tmpdir, "both.png")))

class XmlTest(AbstractCommandTest):
    
    def test_cost(self):
        OptionXmlView([("-x", None),
                       ("-v", 'cost')],
                      [XML_SCHEDULED_PROJMAN])\
                       .get_command().execute()
        self.assert_(osp.exists("cost.xml"))
        OptionXmlView([("-x", None),
                       ("-v", 'cost')],
                      [XML_SCHEDULED_PROJMAN,
                       osp.join(self.tmpdir, "out_cost.xml")]
                      ).get_command().execute()
        self.assert_(osp.exists(osp.join(self.tmpdir, "out_cost.xml")))
    
    def test_list(self):
        OptionXmlView([("-x", None),
                       ("-v", 'list')],
                      [XML_SCHEDULED_PROJMAN,
                       osp.join(self.tmpdir, "out_list.xml")]
                       ).get_command().execute()
        self.assert_(osp.exists(osp.join(self.tmpdir, "out_list.xml")))
    
    def test_date(self):
        OptionXmlView([("-x", None),
                       ("-v", 'date')],
                      [XML_SCHEDULED_PROJMAN,
                       osp.join(self.tmpdir, "out_date.xml")]
                      ).get_command().execute()
        self.assert_(osp.exists(osp.join(self.tmpdir, "out_date.xml")))

if __name__ == '__main__':
    testlib.unittest_main()

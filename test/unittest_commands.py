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

import shutil
import os, os.path

from logilab.common import testlib
from logilab.common.clcommands import cmd_run

# load commands
from projman import commands
from projman.storage import SUFFIX, \
     RESOURCES_NAME, TASKS_NAME, ACTIVITIES_NAME, SCHEDULE_NAME, SCHEDULE_KEY

#from projman.interface.option_manager import OptionConvert, \
#     OptionSchedule, OptionDiagram, OptionXmlView, OptionManager, \
#     DEFAULT_PROJMAN_EXPORT, DEFAULT_PLANNER_EXPORT
#from projman.interface.command_manager import ConvertCommand
from projman.test import TEST_DIR, REF_DIR, GENERATED_DIR, \
     PLANNER_PROJECT, XML_PROJMAN, XML_SCHEDULED_PROJMAN, \
     XML_SCHEDULED_PROJMAN_FULL, TAR_PROJMAN, make_project_name


XML_FILE_NAMES =  [os.path.join(REF_DIR, RESOURCES_NAME),
                   os.path.join(REF_DIR, TASKS_NAME),
                   os.path.join(REF_DIR, ACTIVITIES_NAME)]

DEFAULT_PROJMAN_EXPORT = os.path.join(REF_DIR, 'pmfromplanner.xml')
XML_PROJMAN = os.path.join(REF_DIR, XML_PROJMAN)
XML_SCHEDULED_PROJMAN = os.path.join(REF_DIR, XML_SCHEDULED_PROJMAN)
XML_SCHEDULED_PROJMAN_FULL = os.path.join(REF_DIR, XML_SCHEDULED_PROJMAN_FULL)
TAR_PROJMAN = os.path.join(REF_DIR, TAR_PROJMAN)
SCHEDULE = "out_schedule.xml"
SCHEDULE_PATH = os.path.join(REF_DIR, SCHEDULE)

class AbstractCommandTest(testlib.TestCase):
    """testing """
    
    def setUp(self):
        for file_name in XML_FILE_NAMES:
            if os.path.exists(file_name):
                os.remove(file_name)
    
    def tearDown(self):
        for file_name in XML_FILE_NAMES:
            if os.path.exists(file_name):
                os.remove(file_name)

class ConvertTest(AbstractCommandTest):
    """testing """
    
    def setUp(self):
        AbstractCommandTest.setUp(self)
        for file_name in [DEFAULT_PROJMAN_EXPORT, make_project_name(DEFAULT_PROJMAN_EXPORT)]:
            if os.path.exists(file_name):
                os.remove(file_name)

    def tearDown(self):
        AbstractCommandTest.tearDown(self)
        for file_name in [DEFAULT_PROJMAN_EXPORT, make_project_name(DEFAULT_PROJMAN_EXPORT)]:
            if os.path.exists(file_name):
                os.remove(file_name)

    def test_planner(self):
        cmd_run('convert', '--input-format', 'planner', '-Xy', '-f', PLANNER_PROJECT, DEFAULT_PROJMAN_EXPORT)
        self.assert_(not os.path.exists(make_project_name(DEFAULT_PROJMAN_EXPORT)))
        self.assert_(os.path.exists(DEFAULT_PROJMAN_EXPORT))
        for file_name in XML_FILE_NAMES:
            self.assert_(os.path.exists(file_name))
 
    
class ScheduleTest(AbstractCommandTest):
    """testing """
    
    def setUp(self):
        AbstractCommandTest.setUp(self)
        self.projman = "tmp_projman.xml"
        self.projman_path =  os.path.join(REF_DIR, "tmp_projman.xml")
        for file_name in [SCHEDULE_PATH, self.projman_path,
                          make_project_name(self.projman_path)]:
            if os.path.exists(file_name):
                os.remove(file_name)
        shutil.copyfile(XML_PROJMAN, self.projman_path)

    def tearDown(self):
        AbstractCommandTest.tearDown(self)
        for file_name in [SCHEDULE_PATH, self.projman_path,
                          make_project_name(self.projman_path)]:
            if os.path.exists(file_name):
                os.remove(file_name)
    
    def test_default(self):
        # schedule xml and wrap into prj
        cmd_run('schedule', '--type', 'csp', '-f', self.projman_path, '-o', SCHEDULE, '-In')
        self.assert_(os.path.exists(SCHEDULE_PATH))
        # schedule prj and unwrap
        cmd_run('schedule', '--type', 'csp', '-f', self.projman_path, '-o', SCHEDULE, '-Xy', '-In')
        #files = OptionManager([("-X", None)], [make_project_name(self.projman_path)]).storage
        #self.assertEquals(files.file_names[SCHEDULE_KEY], SCHEDULE_NAME)
        self.assert_(os.path.exists(SCHEDULE_PATH))
    
    def test_include(self):
        # schedule xml and wrap into prj
        cmd_run('schedule', '--type', 'csp', '-f', self.projman_path, '-o', SCHEDULE, '-Xn', '-Iy')
        self.assert_(not os.path.exists(SCHEDULE_PATH))
        # schedule prj and unwrap
        cmd_run('schedule', '--type', 'csp', '-f', self.projman_path, '-o', SCHEDULE, '-Xy', '-Iy')
        #files = OptionManager([("-X", None)], [make_project_name(self.projman_path)]).storage
        #self.assertEquals(files.file_names[SCHEDULE_KEY], SCHEDULE)
        self.assert_(os.path.exists(SCHEDULE_PATH))

class DiagramTest(AbstractCommandTest):
    
    def setUp(self):
        self.file_names = ["gantt.png", "generated/out_gantt.png",
                          "resources.png", "generated/out_ress.tiff",
                          "gantt-resources.png", "generated/both.png"]
        for file_name in self.file_names:
            if os.path.exists(file_name):
                os.remove(file_name)

    def tearDown(self):
        AbstractCommandTest.tearDown(self)
        for file_name in self.file_names:
            if os.path.exists(file_name):
                os.remove(file_name)
    
    def test_gantt(self):
        cmd_run('diagram', '--timestep', '7', '-f', XML_SCHEDULED_PROJMAN, 'gantt')
        self.assert_(os.path.exists("gantt.png"))
        cmd_run('diagram', '--timestep', '7', '-f', XML_SCHEDULED_PROJMAN, '-o', 'generated/out_gantt.png', 'gantt')
        
        self.assert_(os.path.exists("generated/out_gantt.png"))
    def test_gantt2(self):
        cmd_run('diagram', '--timestep', '7', '-f', XML_SCHEDULED_PROJMAN_FULL, 'gantt')
        self.assert_(os.path.exists("gantt.png"))
        cmd_run('diagram', '--timestep', '7', '-f', XML_SCHEDULED_PROJMAN_FULL, '-o', 'generated/out_gantt.png', 'gantt')
        self.assert_(os.path.exists("generated/out_gantt.png"))

    def test_resources(self):
        cmd_run('diagram', '-f', XML_SCHEDULED_PROJMAN, 'resources')
        self.assert_(os.path.exists("resources.png"))
        cmd_run('diagram', '-f', XML_SCHEDULED_PROJMAN, '--format', 'tiff', 'resources')
        self.assert_(os.path.exists("resources.tiff"))
    
    def test_gantt_resources(self):
        cmd_run('diagram', '-f', XML_SCHEDULED_PROJMAN, 'gantt-resources')
        self.assert_(os.path.exists("gantt-resources.png"))


class XmlTest(AbstractCommandTest):
    
    def setUp(self):
        self.file_names = ["cost.xml", "output.xml", "generated/out_cost.xml",
                           "generated/out_list.xml", "generated/out_duration.xml", "generated/out_duration_section.xml",
                           "generated/out_cost_para.xml", "generated/out_cost_table.xml", "generated/out_rates.xml",
                           ]
        for file_name in self.file_names:
            if os.path.exists(file_name):
                os.remove(file_name)

    def tearDown(self):
        AbstractCommandTest.tearDown(self)
        for file_name in self.file_names:
            if os.path.exists(file_name):
                os.remove(file_name)
    
    def test_all(self):
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN,
                'duration-table', 'duration-section', 'tasks-list-section',
                'cost-para', 'cost-table', 'rates-section')
        self.assert_(os.path.exists("output.xml"))
        
    def test_duration_table(self):
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', 'generated/out_duration.xml', 'duration-table')
        self.assert_(os.path.exists("generated/out_duration.xml"))
        
    def test_duration_section(self):
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', 'generated/out_duration_section.xml', 'duration-section')
        self.assert_(os.path.exists("generated/out_duration_section.xml"))
    
    def test_tasks_list_section(self):
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', 'generated/out_list.xml', 'tasks-list-section')
        self.assert_(os.path.exists("generated/out_list.xml"))

    def test_cost_para(self):
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', 'generated/out_cost_para.xml', 'cost-para')
        self.assert_(os.path.exists("generated/out_cost_para.xml"))

    def test_cost_table(self):
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', 'generated/out_cost_table.xml', 'cost-table')
        self.assert_(os.path.exists("generated/out_cost_table.xml"))

    def test_rates_section(self):
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', 'generated/out_rates.xml', 'rates-section')
        self.assert_(os.path.exists("generated/out_rates.xml"))
    
if __name__ == '__main__':
    testlib.unittest_main()

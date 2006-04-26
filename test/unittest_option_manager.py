#!/usr/bin/python2.2
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

__revision__ ="$Id: unittest_option_manager.py,v 1.8 2005-09-06 18:09:03 nico Exp $"

import unittest
import shutil
import os, os.path
from mx.DateTime import DateTime
from projman.interface.option_manager import OptionConvert, OptionSchedule ,\
     OptionDiagram, OptionXmlView, OptionManager, create_option_manager
from projman.interface.command_manager import ConvertCommand, DiagramCommand
from projman.test import REF_DIR, GENERATED_DIR, XML_PROJMAN,  \
     TAR_TARED_PROJMAN, TAR_TARED_SCHEDULED_PROJMAN

XML_PROJMAN_PATH = os.path.join(REF_DIR, XML_PROJMAN)

TAR_PROJMAN_PATH = os.path.join(REF_DIR, TAR_TARED_PROJMAN)
TAR_SCHEDULE_PATH = os.path.join(REF_DIR, TAR_TARED_SCHEDULED_PROJMAN)

class OptionManagerTest(unittest.TestCase):
    """testing """
    def setUp(self):
        self.default_options = OptionManager([("-X", None)],
                                             [XML_PROJMAN_PATH])
        self.true_options = OptionManager([("-t", None),
                                           ("-X", None),
                                           ("-p",'tasks'),
                                           ("-r", 'resources'),
                                           ("-a", 'activities')],
                                          [XML_PROJMAN_PATH])
        self.true_ext_options = OptionManager([("--interactive", None),
                                           ("--expanded", None),
                                           ("--verbose", None),
                                           ("--project",'tasks'),
                                           ("--resources", 'resources'),
                                           ("--activity", 'activities')],
                                          [XML_PROJMAN_PATH])
    
    def test_creation(self):
        """creation of OptionManager"""
        self.assertRaises(ValueError, OptionManager,  [("-h", None)], [])
        self.assertRaises(ValueError, OptionManager,  [("-V", None)], [])
        self.assertRaises(KeyError, OptionManager,  [("-c", None)], [])
        self.assertRaises(ValueError, OptionManager,  [], [])
    
    
    def test_is_verbose(self):
        """returns True if owerwrites output"""
        self.assertEquals(self.default_options.is_verbose(), False)
        self.assertEquals(self.true_options.is_verbose(), False)
        self.assertEquals(self.true_ext_options.is_verbose(), True)
    
    
    def test_is_interactive_mode(self):
        """returns True if owerwrites output"""
        self.assertEquals(self.default_options.is_interactive_mode(), False)
        self.assertEquals(self.true_options.is_interactive_mode(), True)
        self.assertEquals(self.true_ext_options.is_interactive_mode(), True)

    def test_is_archive_mode(self):
        self.assertEquals(self.default_options.is_archive_mode(), False)
        self.assertEquals(self.true_options.is_archive_mode(), False)
        self.assertEquals(self.true_ext_options.is_archive_mode(), False)
        """returns True if using archive"""
    
    def test_get_command(self):
        """delegated to appropriate child"""
        self.assertRaises(NotImplementedError, self.default_options.get_command)


class ScheduleTest(unittest.TestCase):

    def setUp(self):
        # projman paths
        self.projman_path = os.path.join(GENERATED_DIR, "tmp_projman.prj")
        self.scheduled_path = os.path.join(GENERATED_DIR, "tmp_scheduled_projman.prj")
        self.schedule = os.path.join(GENERATED_DIR, "tmp_schedule.xml")
        shutil.copyfile(TAR_PROJMAN_PATH, self.projman_path)
        shutil.copyfile(TAR_SCHEDULE_PATH, self.scheduled_path)
        # options
        self.default_options = {
            'not included': OptionSchedule([("-s", None)],
                                           [self.projman_path]),
            'included': OptionSchedule([("-s", None)],
                                       [self.scheduled_path]),
            'output': OptionSchedule([("-s", None)],
                                     [self.scheduled_path, self.schedule])}
        self.included_options = {
            'not included': OptionSchedule([("-s", None),
                                            ("-I", None)],
                                           [self.projman_path]),
            'included': OptionSchedule([("-s", None),
                                        ("-I", None)],
                                       [self.scheduled_path]),
            'output': OptionSchedule([("-s", None),
                                      ("-I", None)],
                                     [self.scheduled_path, self.schedule])}
        self.csp_options = {
            'not included': OptionSchedule([("-s", None),
                                            ("--type", 'csp')],
                                           [self.projman_path]),
            'included': OptionSchedule([("-s", None),
                                        ("--type", 'csp')],
                                       [self.scheduled_path]),
            'output': OptionSchedule([("-s", None),
                                      ("--type", 'csp')],
                                     [self.scheduled_path, self.schedule])}
        self.dict_options = [self.default_options,
                             self.included_options,
                             self.csp_options]

    def tearDown(self):
        os.remove(self.projman_path)
        os.remove(self.scheduled_path)

    def test_schedule_name(self):
        for option in [dict_option['not included']
                       for dict_option in self.dict_options]:
            self.assertEquals(option.storage.output, "schedule.xml")
            self.assertEquals(option.storage.get_schedule(),
                              "schedule.xml")
        for option in [dict_option['included']
                       for dict_option in self.dict_options]:
            self.assertEquals(option.storage.output, "out_schedule.xml")
            self.assertEquals(option.storage.get_schedule(),
                              "out_schedule.xml")
        for option in [dict_option['output']
                       for dict_option in self.dict_options]:
            self.assertEquals(option.storage.output, os.path.abspath(self.schedule))
            self.assertEquals(option.storage.to_schedule(),
                              os.path.abspath(self.schedule))
        

    def test_options(self):
        for option in self.default_options.values():
            self.assertEquals(option.is_including_reference(), False)
            self.assertNotEquals(option.type, 'csp')
        for option in self.included_options.values():
            self.assertEquals(option.is_including_reference(), True)
            self.assertNotEquals(option.type, 'csp')
        for option in self.csp_options.values():
            self.assertEquals(option.is_including_reference(), False)
            self.assertEquals(option.type, 'csp')

class ConvertTest(unittest.TestCase):

    def setUp(self):
        self.default_options = OptionConvert([("-c", None),
                                              ("-X", None)],
                                             [XML_PROJMAN_PATH])
        self.pygantt_options = create_option_manager([("-c", None),
                                                      ("-X", None),
                                                      ("-i", 'pygantt'),
                                                      ("-o", 'pygantt')],
                                                     [XML_PROJMAN_PATH])
        self.planner_options = OptionConvert([("-c", None),
                                              ("-X", None),
                                              ("-i", 'planner'),
                                              ("-o", 'planner')],
                                             [XML_PROJMAN_PATH])
        self.projman_options = OptionConvert([("-c", None),
                                              ("-X", None),
                                              ("--in-format", 'projman'),
                                              ("--out-format", 'projman')],
                                             [XML_PROJMAN_PATH])
    def test_creation(self):
        """creation of OptionManager"""
        self.assertRaises(ValueError, OptionConvert,  [("-i", 'fake')], [])
        self.assertRaises(ValueError, OptionConvert,  [("-o", 'fake')], [])
    
    def test_get_command(self):
        """delegated to appropriate child"""
        self.assert_(isinstance(self.default_options.get_command(), ConvertCommand))
        
    def test_is_reading_pygantt(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_reading_pygantt(), False)
        self.assertEquals(self.pygantt_options.is_reading_pygantt(), True)
        self.assertEquals(self.planner_options.is_reading_pygantt(), False)
        self.assertEquals(self.projman_options.is_reading_pygantt(), False)
        
    def test_is_reading_planner(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_reading_planner(), False)
        self.assertEquals(self.pygantt_options.is_reading_planner(), False)
        self.assertEquals(self.planner_options.is_reading_planner(), True)
        self.assertEquals(self.projman_options.is_reading_planner(), False)
        
    def test_is_reading_projman(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_reading_projman(), True)
        self.assertEquals(self.pygantt_options.is_reading_projman(), False)
        self.assertEquals(self.planner_options.is_reading_projman(), False)
        self.assertEquals(self.projman_options.is_reading_projman(), True)
        
    def test_is_writing_pygantt(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_writing_pygantt(), False)
        self.assertEquals(self.pygantt_options.is_writing_pygantt(), True)
        self.assertEquals(self.planner_options.is_writing_pygantt(), False)
        self.assertEquals(self.projman_options.is_writing_pygantt(), False)
        
    def test_is_writing_planner(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_writing_planner(), False)
        self.assertEquals(self.pygantt_options.is_writing_planner(), False)
        self.assertEquals(self.planner_options.is_writing_planner(),True )
        self.assertEquals(self.projman_options.is_writing_planner(), False)
        
    def test_is_writing_projman(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_writing_projman(), True)
        self.assertEquals(self.pygantt_options.is_writing_projman(), False)
        self.assertEquals(self.planner_options.is_writing_projman(), False)
        self.assertEquals(self.projman_options.is_writing_projman(), True)


class DiagramTest(unittest.TestCase):
    """testing """
    def setUp(self):
        self.default_options = OptionDiagram( [("-X", None)],
                                              [XML_PROJMAN_PATH])
        self.gantt_options = OptionDiagram([("-d", None),
                                            ("-X", None),
                                            ("--diagram-type", 'gantt'),
                                            ("--renderer", 'jpeg'),
                                            ("--selected-resource", 'select_id'),
                                            ("--depth", '2'),
                                            ("--timestep", '7'),
                                            ("--view-begin", '2004/10/29'),
                                            ("--view-end", '2004/11/11')],
                                           [XML_PROJMAN_PATH])
        self.resources_options = OptionDiagram([("-d", None),
                                                ("-X", None),
                                                ("--diagram-type", 'resources'),
                                                ("--renderer", 'tiff'),
                                                ("--del-ended", None),
                                                ("--del-empty", None)],
                                               [XML_PROJMAN_PATH])
        self.gantt_ressources_options = OptionDiagram([("-d", None),
                                                       ("-X", None),
                                                       ("-D", None),
                                                       ("--diagram-type", 'gantt-resources'),
                                                       ("--renderer", 'html'),
                                                       ],
                                                      [XML_PROJMAN_PATH])
    def test_creation(self):
        """creation of OptionManager"""
        self.assertRaises(ValueError, OptionDiagram,
                          [("--diagram-type", 'fake')], [])
        self.assertRaises(ValueError, OptionDiagram,
                          [("--renderer", 'jpg')], [])
        self.assertRaises(ValueError, OptionDiagram,
                          [("--view-begin", 'fake' )], [])
        self.assertRaises(ValueError, OptionDiagram,
                          [("--view-begin", '25/12/2004' )], [])
        self.assertRaises(ValueError, OptionDiagram,
                          [("--view-end", 'fake' )], [])
    
    def test_get_command(self):
        """delegated to appropriate child"""
        self.assert_(isinstance(self.default_options.get_command(), DiagramCommand))
        
    def test_get_render_options(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_render_options(),
                          {'timestep' : 1,
                           'detail' : 2,
                           'depth' : 0,
                           'view-begin' : None,
                           'view-end' : None,
                           'showids' : False,
                           'rappel' : False,
                           'selected-resource' : None
                           })
        self.assertEquals(self.gantt_options.get_render_options(), 
                          {'timestep' : 7,
                           'detail' : 2,
                           'depth' : 2,
                           'view-begin' : DateTime(2004, 10, 29),
                           'view-end' : DateTime(2004, 11, 11),
                           'showids' : False,
                           'rappel' : False,
                           'selected-resource' : 'select_id'
                           })
        
    def test_is_gantt_type(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_gantt_type(), True)
        self.assertEquals(self.gantt_options.is_gantt_type(), True)
        self.assertEquals(self.resources_options.is_gantt_type(), False)
        self.assertEquals(self.gantt_ressources_options.is_gantt_type(), False)
        
    def test_is_resource_type(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_resource_type(), False)
        self.assertEquals(self.gantt_options.is_resource_type(), False)
        self.assertEquals(self.resources_options.is_resource_type(), True)
        self.assertEquals(self.gantt_ressources_options.is_resource_type(), False)
        
    def test_is_gantt_resource_type(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_gantt_resource_type(), False)
        self.assertEquals(self.gantt_options.is_gantt_resource_type(), False)
        self.assertEquals(self.resources_options.is_gantt_resource_type(), False)
        self.assertEquals(self.gantt_ressources_options.is_gantt_resource_type(), True)

    def test_does_delete_empty(self):
        """returns True if using archive"""
        self.assertEquals(self.default_options.delete_empty, False)
        self.assertEquals(self.gantt_options.delete_empty, False)
        self.assertEquals(self.resources_options.delete_empty, True)
        self.assertEquals(self.gantt_ressources_options.delete_empty, True)

    def test_does_delete_ended(self):
        """returns True if using archive"""
        self.assertEquals(self.default_options.delete_ended, False)
        self.assertEquals(self.gantt_options.delete_ended, False)
        self.assertEquals(self.resources_options.delete_ended, True)
        self.assertEquals(self.gantt_ressources_options.delete_ended, True)
        
    def test_is_image_renderer(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_image_renderer(), True)
        self.assertEquals(self.gantt_options.is_image_renderer(), True)
        self.assertEquals(self.resources_options.is_image_renderer(), True)
        self.assertEquals(self.gantt_ressources_options.is_image_renderer(), False)
        
    def test_is_html_renderer(self):
        """returns file container"""
        self.assertEquals(self.default_options.is_html_renderer(), False)
        self.assertEquals(self.gantt_options.is_html_renderer(), False)
        self.assertEquals(self.resources_options.is_html_renderer(), False)
        self.assertEquals(self.gantt_ressources_options.is_html_renderer(), True)
        
    def test_get_diagram_type(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_diagram_type(), 'gantt')
        self.assertEquals(self.gantt_options.get_diagram_type(), 'gantt')
        self.assertEquals(self.resources_options.get_diagram_type(), 'resources')
        self.assertEquals(self.gantt_ressources_options.get_diagram_type(), 'gantt-resources')
        
    def test_get_image_format(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_image_format(), 'png')
        self.assertEquals(self.gantt_options.get_image_format(), 'jpeg')
        self.assertEquals(self.resources_options.get_image_format(), 'tiff')
        self.assertEquals(self.gantt_ressources_options.get_image_format(), 'html')
        
    def test_get_selected_resources(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_selected_resources(), None)
        self.assertEquals(self.gantt_options.get_selected_resources(), 'select_id')
        
    def test_get_timestep(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_timestep(), 1)
        self.assertEquals(self.gantt_options.get_timestep(), 7)
        
    def test_get_depth(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_depth(), 0)
        self.assertEquals(self.gantt_options.get_depth(), 2)
        
    def test_get_begin_date(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_begin_date(), None)
        self.assertEquals(self.gantt_options.get_begin_date(), DateTime(2004, 10, 29))
        
    def test_get_end_date(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_end_date(), None)
        self.assertEquals(self.gantt_options.get_end_date(), DateTime(2004, 11, 11))
        
    def test_get_detail(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_detail(), 2)
        self.assertEquals(self.gantt_options.get_detail(), 2)
        
    def test_get_rappel(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_rappel(), False)
        self.assertEquals(self.gantt_options.get_rappel(), False)
        
    def test_get_showids(self):
        """returns file container"""
        self.assertEquals(self.default_options.get_showids(), False)
        self.assertEquals(self.gantt_options.get_showids(), False)
    
    
if __name__ == '__main__':
    unittest.main()

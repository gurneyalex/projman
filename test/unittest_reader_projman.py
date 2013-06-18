# -*- coding: iso-8859-1 -*-
"""
unit tests for module projman.lib.projman_reader.py
Projman - (c)2000-2013 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projman
Manipulate a xml project description.

This code is released under the GNU Public Licence v2. See www.gnu.org.

"""

import os.path as osp
from mx.DateTime import Time

from logilab.common.testlib import TestCase, unittest_main

from projman.readers import ProjectXMLReader
from projman.lib._exceptions import MalformedProjectFile
from projman.test import DATADIR

class DummyConfig(object):
    def __init__(self):
        self.task_root = None

class TaskXMLReaderTest(TestCase):

    def setUp(self):
        self.reader = ProjectXMLReader(None)
        self.root = self.reader.read_tasks(osp.join(DATADIR, 'multiline_tasked_project.xml'))
        #self.reader.project.root_task = self.root

    def test_multiline_project_label(self):
        expected_title = "Simplest Project with a multiline label, gosh can you believe it"
        self.assertEqual(expected_title, self.root.title)
        self.assertEqual(len(self.root.children), 3)

    def test_multiline_task_desc(self):
        task = self.root.children[0]
        expected_desc = u"Réunions de début et de fin de tranche, réunions\n      hebdomadaires, <emphasis>comptes-rendus</emphasis>, etc."
        self.assertEqual(expected_desc, task.description)

    def test_multiline_task_duration(self):
        task = self.root.children[0]
        self.assertEqual(25, task.duration)
        task = self.root.children[1]
        self.assertEqual(10.6, task.duration)
        task = self.root.children[2]
        self.assertEqual(0, task.duration)

    def test_multiline_task_progress(self):
        task = self.root.children[0]
        self.assertEqual(0, task.progress)


class TaskXMLReaderVirtualRootTest(TestCase):
    def setUp(self):
        self.reader = ProjectXMLReader(None, task_root='t1_1')
        self.root = self.reader.read_tasks(osp.join(DATADIR, 'multiline_tasked_project.xml'))

    def test_virtual_root(self):
        task = self.root
        expected_title = "Suivi de projet"
        self.assertEqual(expected_title, task.title)
        self.assertEqual(len(task.children), 0)
        expected_desc = u"Réunions de début et de fin de tranche, réunions\n      hebdomadaires, <emphasis>comptes-rendus</emphasis>, etc."
        self.assertEqual(expected_desc, task.description)
        self.assertEqual(25, task.duration)
        self.assertEqual(0, task.progress)

class ResourcesXMLReaderTest(TestCase):
    def setUp(self):
        reader = ProjectXMLReader(None)
        three_file = osp.join(DATADIR, 'three_resourced_list.xml')
        reader.read_resources_file(three_file)
        self.project = reader.project

    def test_number_of_resources(self):
        self.assertEqual(len(self.project.resources), 3)

    def test_resource_content(self):
        res = self.project.resources['ing_1']
        self.assertEqual(res.name, "Emmanuel Breton")
        self.assertEqual(res.calendar.id, 'typic_cal')

    def test_resources_roles(self):
        roles = self.project.resources_roles
        self.assertEqual(roles.keys(), ['ing_py'])
        self.assertEqual(roles['ing_py'].hourly_cost, 80.00)
        self.assertEqual(roles['ing_py'].unit, "EUR")

    def test_calendar_content(self):
        cal = self.project.calendars.values()[0]
        self.assertEqual(cal.name, "Calendrier Francais")
        self.assertEqual(cal.weekday, {'sat': 'non_working', 'sun':'non_working'} )
        self.assertEqual(cal.national_days,
                          [(1,1), (5,1), (5,8), (7,14),
                           (8,15), (11,1), (11,11), (12,25)])
        self.assertEqual(cal.start_on, None)
        self.assertEqual(cal.stop_on, None)
        self.assertEqual(cal.day_types,
                          {'working': [u'Standard work day', [(Time(8), Time(12)),
                                                             (Time(13), Time(17,24))]],
                           'non_working': [u'Week-end day', []],
                           'holiday': [u'Day Off',[]],})
        self.assertEqual(cal.default_day_type, 'working')
        dates = [("2002-12-31","2002-12-26"),
                 ("2003-03-14","2003-03-10"),
                 ("2003-08-18","2003-08-14"),
                 ("2004-05-21","2004-05-20")]
        for (expected_end, expected_start), (start, end, working) in zip(dates, cal.timeperiods):
            start = str(start).split()[0]
            end = str(end).split()[0]
            self.assertEqual(start, expected_start)
            self.assertEqual(end, expected_end)
            self.assertEqual(working, 'holiday')



class ErrorXMLReaderTest(TestCase):
    def setUp(self):
        self.reader = ProjectXMLReader(None)

    def test_error_project(self):
        error_pr = osp.join(DATADIR, 'error_project.xml')
        self.assertRaises(MalformedProjectFile, self.reader.read_resources_file, error_pr)

    def test_error_doubletask(self):
        root = self.reader.read_tasks(osp.join(DATADIR, 'error_doubletask.xml'))
        self.assertEqual(root.check_consistency(), ['Duplicate task id: double_t1_1'])


    def test_error_dtd_project(self):
        self.assertRaises(MalformedProjectFile, self.reader.read_tasks, osp.join(DATADIR, 'error_dtd_project.xml'))
        reader = ProjectXMLReader(osp.join(DATADIR, 'error_dtd_projman.xml'))
        self.assertRaises(MalformedProjectFile, reader.read)


    def test_error_dtd_project_multi(self):
        try:
            self.reader.read_tasks(osp.join(DATADIR, 'multi_error_dtd_project.xml'))
        except MalformedProjectFile, ex:
            # more than one line of errors
            self.assertEqual(len(str(ex).split('\n')), 4)

if __name__ == '__main__':
    unittest_main()

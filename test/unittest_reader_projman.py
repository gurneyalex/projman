# -*- coding: iso-8859-1 -*-
"""
unit tests for module projman.lib.projman_reader.py
Projman - (c)2000-2006 LOGILAB <contact@logilab.fr> - All rights reserved.

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

class DummyConfig:
    def __init__(self):
        self.task_root = None

class TaskXMLReaderTest(TestCase):

    def setUp(self):
        self.reader = ProjectXMLReader(None)
        self.root = self.reader.read_tasks(osp.join(DATADIR, 'multiline_tasked_project.xml'))
        #self.reader.project.root_task = self.root

    def test_multiline_project_label(self):
        expected_title = "Simplest Project with a multiline label, gosh can you believe it"
        self.assertEquals(expected_title, self.root.title)
        self.assertEquals(len(self.root.children), 3)

    def test_multiline_task_desc(self):
        task = self.root.children[0]
        expected_desc = u"Réunions de début et de fin de tranche, réunions\n      hebdomadaires, <emphasis>comptes-rendus</emphasis>, etc."
        self.assertEquals(expected_desc, task.description)

    def test_multiline_task_duration(self):
        task = self.root.children[0]
        self.assertEquals(25, task.duration)
        task = self.root.children[1]
        self.assertEquals(10.6, task.duration)
        task = self.root.children[2]
        self.assertEquals(0, task.duration)

    def test_multiline_task_progress(self):
        task = self.root.children[0]
        self.assertEquals(0, task.progress)


class TaskXMLReaderVirtualRootTest(TestCase):
    def setUp(self):
        self.reader = ProjectXMLReader(None, task_root='t1_1')
        self.root = self.reader.read_tasks(osp.join(DATADIR, 'multiline_tasked_project.xml'))

    def test_virtual_root(self):
        task = self.root
        expected_title = "Suivi de projet"
        self.assertEquals(expected_title, task.title)
        self.assertEquals(len(task.children), 0)
        expected_desc = u"Réunions de début et de fin de tranche, réunions\n      hebdomadaires, <emphasis>comptes-rendus</emphasis>, etc."
        self.assertEquals(expected_desc, task.description)
        self.assertEquals(25, task.duration)
        self.assertEquals(0, task.progress)

class ResourcesXMLReaderTest(TestCase):
    def setUp(self):
        self.reader = ProjectXMLReader(None)
        self.resources = self.reader.read_resources(osp.join(DATADIR, 'three_resourced_list.xml'))

    def test_number_of_resources(self):
        self.assertEquals(len(self.resources.children), 4)
        for res in self.resources.children[:-1]:
            self.assertEquals(res.TYPE,'resource')
        self.assertEquals(self.resources.children[-1].TYPE, 'calendar')

    def test_resource_content(self):
        res = self.resources.children[0]
        self.assertEquals(res.name, "Emmanuel Breton")
        self.assertEquals(res.hourly_rate, [80, "euros"])
        self.assertEquals(res.calendar, 'typic_cal')

    def test_calendar_content(self):
        cal = self.resources.children[-1]
        self.assertEquals(cal.name, "Calendrier Francais")
        self.assertEquals(cal.weekday, {'sat': 'non_working', 'sun':'non_working'} )
        self.assertEquals(cal.national_days,
                          [(1,1), (5,1), (5,8), (7,14),
                           (8,15), (11,1), (11,11), (12,25)])
        self.assertEquals(cal.start_on, None)
        self.assertEquals(cal.stop_on, None)
        self.assertEquals(cal.day_types,
                          {'working': [u'Standard work day', [(Time(8), Time(12)),
                                                             (Time(13), Time(17,24))]],
                           'non_working': [u'Week-end day', []],
                           'holiday': [u'Day Off',[]],})
        self.assertEquals(cal.default_day_type, 'working')
        dates = [("2002-12-31","2002-12-26"),
                 ("2003-03-14","2003-03-10"),
                 ("2003-08-18","2003-08-14"),
                 ("2004-05-21","2004-05-20")]
        for (expected_end, expected_start), (start, end, working) in zip(dates, cal.timeperiods):
            start = str(start).split()[0]
            end = str(end).split()[0]
            self.assertEquals(start, expected_start)
            self.assertEquals(end, expected_end)
            self.assertEquals(working, 'holiday')



class ErrorXMLReaderTest(TestCase):
    def setUp(self):
        self.reader = ProjectXMLReader(None)
    
    def test_error_project(self):
        self.assertRaises(Exception, self.reader.read_resources, osp.join(DATADIR, 'error_project.xml'))

    def test_error_doubletask(self):
        root = self.reader.read_tasks(osp.join(DATADIR, 'error_doubletask.xml'))
        self.assertEquals(root.check_consistency(), ['Duplicate task id: double_t1_1'])

      
    def test_error_dtd_project(self):
        self.assertRaises(MalformedProjectFile, self.reader.read_tasks, osp.join(DATADIR, 'error_dtd_project.xml'))
        reader = ProjectXMLReader(osp.join(DATADIR, 'error_dtd_projman.xml'))
        self.assertRaises(MalformedProjectFile, reader.read)


    def test_error_dtd_project_multi(self):
        try:
            self.reader.read_tasks(osp.join(DATADIR, 'multi_error_dtd_project.xml'))
        except MalformedProjectFile, ex:
            # more than one line of errors
            self.assertEquals(len(str(ex).split('\n')), 4)

if __name__ == '__main__':
    unittest_main()

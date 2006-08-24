# -*- coding: iso-8859-1 -*-
"""
unit tests for module projman.lib.projman_reader.py
Projman - (c)2000-2006 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projman
Manipulate a xml project description.

This code is released under the GNU Public Licence v2. See www.gnu.org.

"""

from logilab.common.testlib import TestCase, unittest_main

from projman.readers import TaskXMLReader, ResourcesXMLReader, ScheduleXMLReader, ProjectFileListReader
from projman.interface.file_manager import ProjectStorage
from projman.interface.option_manager import OptionManager
from projman.lib._exceptions import DuplicatedTaskId, MalformedProjectFile
    
class AbstractXMLReaderTest:
    def setUp(self):
        self.reader = None # override to set to some useful reader

    def _init_get_character_test(self):
        self.reader.startDocument()
        self.assertEquals(self.reader._buffer, [])
        data = [u'  toto  \n', u'  titi  \n']
        for d in data:
            self.reader.characters(d)
        self.assertEquals(self.reader._buffer, data)
        
    def test_get_characters_default(self):
        self._init_get_character_test()
        self.assertEquals(self.reader.get_characters(), u'toto titi')
        self.assertEquals(self.reader._buffer, [])

    def test_get_characters_default_multiple_blanks(self):
        self._init_get_character_test()
        self.reader.characters(u'   ')
        self.reader.characters(u'\n')
        self.reader.characters(u' tata   ')
        self.assertEquals(self.reader.get_characters(), u'toto titi tata')
        self.assertEquals(self.reader._buffer, [])

    def test_get_characters_spacer(self):
        self._init_get_character_test()
        self.assertEquals(self.reader.get_characters('\t'), u'toto\ttiti')
        self.assertEquals(self.reader._buffer, [])

    def test_get_characters_unstripped(self):
        self._init_get_character_test()
        self.assertEquals(self.reader.get_characters(strip=False), u'  toto  \n  titi  \n')
        self.assertEquals(self.reader._buffer, [])

class TaskXMLReaderTest(TestCase, AbstractXMLReaderTest):

    def setUp(self):
        self.reader = TaskXMLReader()
        self.root = self.reader.fromFile('./data/multiline_tasked_project.xml')

    def test_multiline_project_label(self):
        expected_title = "Simplest Project with a multiline label, gosh can you believe it"
        self.assertEquals(expected_title, self.root.title)
        self.assertEquals(len(self.root.children), 3)

    def test_multiline_task_desc(self):
        task = self.root.children[0]
        expected_desc = u"\n    Réunions de début et de fin de tranche, réunions\n      hebdomadaires, <emphasis>comptes-rendus</emphasis>, etc."
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
        self.reader = TaskXMLReader(virtual_task_root='t1_1')
        self.root = self.reader.fromFile('./data/multiline_tasked_project.xml')

    def test_virtual_root(self):
        task = self.root
        expected_title = "Suivi de projet"
        self.assertEquals(expected_title, task.title)
        self.assertEquals(len(task.children), 0)
        expected_desc = u"\n    Réunions de début et de fin de tranche, réunions\n      hebdomadaires, <emphasis>comptes-rendus</emphasis>, etc."
        self.assertEquals(expected_desc, task.description)
        self.assertEquals(25, task.duration)
        self.assertEquals(0, task.progress)

class ResourcesXMLReaderTest(TestCase, AbstractXMLReaderTest):
    def setUp(self):
        self.reader = ResourcesXMLReader()
        self.resources = self.reader.fromFile('./data/three_resourced_list.xml')
        
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
        for day in (u'mon', u'tue', u'wed', u'thu', u'fri'):
            self.assertEquals(cal.weekday[day], u'Standard work day')
        for day in (u'sat', u'sun'):
            self.assertEquals(cal.weekday[day], u'Week-end day')
        self.assertEquals(cal.national_days,
                          [(1,1), (5,1), (5,8), (7,14),
                           (8,15), (11,1), (11,11), (12,25)])
        self.assertEquals(cal.start_on, None)
        self.assertEquals(cal.stop_on, None)
        self.assertEquals(cal.type_nonworking_days,
                          {1: u'Standard work day', 2: u'Week-end day', 3: u'Day Off'})
        
        self.assertEquals(cal.default_nonworking, 2)
        self.assertEquals(cal.default_working, 1)
        dates = [("2002-12-31","2002-12-26"),
                 ("2003-03-14","2003-03-10"),
                 ("2003-08-18","2003-08-14"),
                 ("2004-05-21","2004-05-20")]
        for (expected_end, expected_start), (start, end, working) in zip(dates, cal.timeperiods):
            start = str(start).split()[0]
            end = str(end).split()[0]
            self.assertEquals(expected_start, start)
            self.assertEquals(expected_end, end)
            self.assertEquals(u'Day Off', working)        



class ErrorXMLReaderTest(TestCase):

    def test_error_project(self):
        self.reader = ResourcesXMLReader()
        self.assertRaises(Exception, self.reader.fromFile, './data/error_project.xml')

    def test_error_doubletask(self):
        self.reader = TaskXMLReader()
        root = self.reader.fromFile('./data/error_doubletask.xml')
        self.assertEquals(root.check_consistency(), ['Duplicate task id: double_t1_1'])

      
    def test_error_dtd_project(self):
        self.reader = TaskXMLReader()
        self.assertRaises(MalformedProjectFile, self.reader.fromFile, './data/error_dtd_project.xml')
        args = [ './data/error_dtd_projman.xml']
        optmgr = OptionManager([], args)
        storage = ProjectStorage('./data', 'error_dtd_projman.xml',
                                 archive_mode=optmgr.is_archive_mode(),
                                 input_projman=optmgr.is_input_projman())
        self.assertRaises(SystemExit, storage.load)


    def test_error_dtd_project_multi(self):
        self.reader = TaskXMLReader()
        try:
            self.reader.fromFile('./data/multi_error_dtd_project.xml')
        except MalformedProjectFile, ex:
            # more than one line of errors
            self.assertEquals(len(str(ex).split('\n')), 10)

if __name__ == '__main__':
    unittest_main()

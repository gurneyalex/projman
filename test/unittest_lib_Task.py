# -*- coding: iso-8859-1 -*-
"""
unit tests for module projman.lib.Task

Projman - (c)2000-2013 LOGILAB <contact@logilab.fr> - All rights reserved.
Home: http://www.logilab.org/projman

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

from mx.DateTime import DateTime

from logilab.common.testlib import TestCase, unittest_main

from projman.lib import Task
from projman.lib.constants import *
from projman.test.unittest_lib_Project import simple_project

class TaskTC(TestCase):

    def setUp(self):
        """setup a simple project for each test"""
        project, tasks, resources, roles, stone, calendar = simple_project()
        self.project = project
        self.roles = roles
        self.resources = resources
        self.calendar = calendar
        self.parent = tasks[0]
        self.child1 = tasks[1]
        self.child2 = tasks[2]
        self.child2_1 = tasks[3]
        self.child2_2 = tasks[4]
        self.stone = stone
        #self.parent and self.child2 have no special resource role
        self.child1.resources_role = 'cdp'
        self.child2_1.resources_role = 'ingpy'
        self.child2_2.resources_role = 'ingihm'
        for task in tasks:
            task.compute_resources(project)

    def test_get_task(self):
        """check that a task finds one of its children"""
        self.assertEqual(self.parent.get_task('child1'), self.child1)
        self.assertEqual(self.parent.get_task('stone'), self.stone)
        self.assertEqual(self.parent.get_task('child2_1'), self.child2_1)
        self.assertEqual(self.parent.get_task('child2_2'), self.child2_2)

    def test_get_resources(self):
        """check that array of all resource id returned
        """
        self.assertEqual(self.parent.get_resource_ids(), set())
        self.assertEqual(self.child1.get_resource_ids(), set(['toto']))
        self.assertEqual(self.child2.get_resource_ids(), set())
        self.assertEqual(self.child2_1.get_resource_ids(), set(['toto', 'tata']))
        self.assertEqual(self.child2_2.get_resource_ids(), set(['tata']))

    def test_get_priority(self):
        """test value returned
        """
        self.assertEqual(self.parent.get_priority(), None)
        self.assertEqual(self.child1.get_priority(), None)
        self.assertEqual(self.child2.get_priority(), None)
        self.assertEqual(self.child2_1.get_priority(), None)
        self.assertEqual(self.child2_2.get_priority(), None)
        self.parent.priority = 2
        self.assertEqual(self.parent.get_priority(), 2)
        self.assertEqual(self.child1.get_priority(), 2)
        self.assertEqual(self.child2.get_priority(), 2)
        self.assertEqual(self.child2_1.get_priority(), 2)
        self.assertEqual(self.child2_2.get_priority(), 2)
        self.child2.priority = 1
        self.assertEqual(self.parent.get_priority(), 2)
        self.assertEqual(self.child1.get_priority(), 2)
        self.assertEqual(self.child2.get_priority(), 1)
        self.assertEqual(self.child2_1.get_priority(), 1)
        self.assertEqual(self.child2_2.get_priority(), 1)


    def test_is_finished(self):
        """test achievement state
        """
        #input activity is the accomplished activity related to task
        # default: progress=0, duration=10, short_activity=6
        self.assertEqual(self.parent.is_finished(), False)
        self.assertEqual(self.child1.is_finished(), False)
        self.assertEqual(self.child2.is_finished(), False)
        self.assertEqual(self.child2_1.is_finished(), False)
        self.assertEqual(self.child2_2.is_finished(), False)
        # test on progress
        self.child1.progress = 1
        self.assertEqual(self.parent.is_finished(), False)
        self.assertEqual(self.child1.is_finished(), True)
        self.assertEqual(self.child2.is_finished(), False)
        self.assertEqual(self.child2_1.is_finished(), False)
        self.assertEqual(self.child2_2.is_finished(), False)
        self.child2_2.progress = 1
        self.child2_1.progress = 1
        self.assertEqual(self.child1.is_finished(), True)
        self.assertEqual(self.child2.is_finished(), True)
        self.assertEqual(self.child2_1.is_finished(), True)
        self.assertEqual(self.child2_2.is_finished(), True)
##         # test with duration=10 long_activity=20
##         self.assertEqual(self.parent.is_finished(), True)
##         self.assertEqual(self.single_task.is_finished(), True)
##         self.assertEqual(self.child_task.is_finished(), True)


    def test_remaining_duration(self):
        """check returned number of days, and its right calculation
        according to progress
        """
        # progress=1, duration=10, short_activity=6
        self.assertRaises(AssertionError, setattr, self.parent, 'progress', 1)
        self.assertRaises(AssertionError, setattr, self.child2, 'progress', 1)
        self.child1.progress = .5
        self.child2_1.progress = .5
        self.child2_2.progress = 1.
        self.assertEqual(self.child2_2.remaining_duration(), 0)
        self.assertEqual(self.child2_1.remaining_duration(), 2.5)
        self.assertEqual(self.child2.remaining_duration(), 2.5)
        self.assertEqual(self.child1.remaining_duration(), 5)
        self.assertEqual(self.parent.remaining_duration(), 7.5)
        self.assertEqual(self.child2.progress, 14.5/17)
        self.assertEqual(self.parent.progress, 19.5/27)


    def test_maximum_duration(self):
        """test that all children are taken into account
        """
        self.assertEqual(self.parent.maximum_duration(), 27)
        self.assertEqual(self.child1.maximum_duration(), 10)
        self.assertEqual(self.child2.maximum_duration(), 17)
        self.assertEqual(self.child2_1.maximum_duration(), 5)
        self.assertEqual(self.child2_2.maximum_duration(), 12)


class ConsistencyTC(TestCase):

    def setUp(self):
        self.date1 = DateTime(2005, 01, 01)
        self.date2 = DateTime(2005, 01, 02)
        self.date3 = DateTime(2005, 01, 03)
        self.date4 = DateTime(2005, 01, 04)
        date2 = self.date2
        date3 = self.date3
        self.parent = Task('parent')
        # add a child per constraint type
        self.child_begin_at = Task('child_begin_at')
        self.child_begin_at.add_date_constraint(BEGIN_AT_DATE, date2)
        self.parent.append(self.child_begin_at)

        self.child_begin_after = Task('child_begin_after')
        self.child_begin_after.add_date_constraint(BEGIN_AFTER_DATE, date2)
        self.parent.append(self.child_begin_after)

        self.child_begin_before = Task('child_begin_before')
        self.child_begin_before.add_date_constraint(BEGIN_BEFORE_DATE, date2)
        self.parent.append(self.child_begin_before)

        self.child_end_at = Task('child_end_at')
        self.child_end_at.add_date_constraint(END_AT_DATE, date3)
        self.parent.append(self.child_end_at)

        self.child_end_after = Task('child_end_after')
        self.child_end_after.add_date_constraint(END_AFTER_DATE, date3)
        self.parent.append(self.child_end_after)

        self.child_end_before = Task('child_end_before')
        self.child_end_before.add_date_constraint(END_BEFORE_DATE, date3)
        self.parent.append(self.child_end_before)

    def test_parent_conflict(self):
        self.parent.add_date_constraint(BEGIN_AT_DATE, self.date1)
        self.assertEqual(self.parent.check_consistency(), [])
        self.parent.add_date_constraint(BEGIN_AT_DATE, self.date2)
        self.assertEqual(len(self.parent.check_consistency()), 1)

    def test_parent_begin_at2(self):
        self.parent.add_date_constraint(BEGIN_AT_DATE, self.date2)
        self.assertEqual(self.parent.check_consistency(), [])

    def test_parent_begin_at3(self):
        self.parent.add_date_constraint(BEGIN_AT_DATE, self.date3)
        self.assertEqual(self.parent.check_consistency(), [])

    def test_parent_begin_at4(self):
        self.parent.add_date_constraint(BEGIN_AT_DATE, self.date4)
        self.assertEqual(self.parent.check_consistency(), [])

    # FIXME etc.

class DateConstraintsTC(TestCase):

    def setUp(self):
        self.parent = Task('parent')
        self.child = Task('child')
        self.parent.append(self.child)

    def test_parent_begin_at(self):
        self.assertEqual(self.child.get_date_constraints(), set())
        self.parent.add_date_constraint(BEGIN_AT_DATE, DateTime(2005, 01, 01))
        constraints = self.child.get_date_constraints()
        expected = set([(BEGIN_AFTER_DATE, DateTime(2005, 01, 01), 1)])
        self.assertEqual(constraints, expected)

    def test_parent_begin_after(self):
        self.assertEqual(self.child.get_date_constraints(), set())
        self.parent.add_date_constraint(BEGIN_AFTER_DATE, DateTime(2005, 01, 01))
        constraints = self.child.get_date_constraints()
        expected = set([(BEGIN_AFTER_DATE, DateTime(2005, 01, 01), 1)])
        self.assertEqual(constraints, expected)

    def test_parent_end_at(self):
        self.assertEqual(self.child.get_date_constraints(), set())
        self.parent.add_date_constraint(END_AT_DATE, DateTime(2005, 01, 01))
        constraints = self.child.get_date_constraints()
        expected = set([(END_BEFORE_DATE, DateTime(2005, 01, 01), 1)])
        self.assertEqual(constraints, expected)

    def test_parent_end_before(self):
        self.assertEqual(self.child.get_date_constraints(), set())
        self.parent.add_date_constraint(END_BEFORE_DATE, DateTime(2005, 01, 01))
        constraints = self.child.get_date_constraints()
        expected = set([(END_BEFORE_DATE, DateTime(2005, 01, 01), 1)])
        self.assertEqual(constraints, expected)

class ProgressTC(TestCase):

    def test_get_progress(self):
        """tests progress' getter"""
        t = Task('hello')
        t.duration = 10
        self.assertEqual(t.progress, 0.)
        #activity = [100, DateTime(2005, 8, 1), DateTime(2005, 8, 4)]
        #
        #self.assertEqual(t.progress, 0.4)
        t.progress = 0.8
        self.assertEqual(t.progress, 0.8)


    def test_set_progress(self):
        t = Task('hello')
        self.assertRaises(ValueError, setattr, t, 'progress', 12)
        self.assertRaises(ValueError, setattr, t, 'progress', -1)
        t.progress = 1
        self.assertEqual(t.progress, 1.)

if __name__ == '__main__':
    unittest_main()

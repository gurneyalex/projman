# -*- coding: iso-8859-1 -*-
"""
unit tests for module projman.lib.Task

Projman - (c)2000-2002 LOGILAB <contact@logilab.fr> - All rights reserved.
Home: http://www.logilab.org/projman

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

from logilab.common import testlib
from mx.DateTime import DateTime

from logilab.common.compat import set
from logilab.common.testlib import TestCase

from projman.lib import MileStone, Task
from projman.lib.constants import *

class TaskTC(TestCase):
    
    def setUp(self):
        """called before each test from this class

        parent (inge1/1, inge2/1)
          |
          |--- child1 (inge1/1), 10
          |
          |--- child2
          |      |
          |      |--- child2_1 (inge1/0.6), 5 
          |      |
          |      `--- child2_2 (inge2/1), 12
          |
          `--- stone [milestone]
        """
        self.parent = Task('parent')
        self.child1 = Task('child1')
        self.child2 = Task('child2')
        self.child2_1 = Task('child2_1')
        self.child2_2 = Task('child2_2')
        self.stone = MileStone('stone')
        # building tree
        self.parent.append(self.child1)
        self.parent.append(self.child2)
        self.child2.append(self.child2_1)
        self.child2.append(self.child2_2)
        self.parent.append(self.stone)
        # set duration
        self.child1.duration = 10
        self.child2_1.duration = 5
        self.child2_2.duration = 12
        # set of resources constraints
        self.parent.add_resource_constraint('worker', 'inge1')
        self.parent.add_resource_constraint('worker', 'inge2')
        self.child1.add_resource_constraint('worker', 'inge1')
        self.child2_1.add_resource_constraint('worker', 'inge1')
        self.child2_2.add_resource_constraint('worker', 'inge2')
        # set of dates
        self.date_last_week = DateTime(2004, 10, 1)
        self.date_today = DateTime(2004, 10, 7)
        self.date_tomorrow = DateTime(2004, 10, 8)
        self.date_next_week = DateTime(2004, 10, 13)
        self.date_next_score = DateTime(2004, 10, 26)
        # self.short_activity = Activity(100, self.date_today, self.date_next_week)
        # self.long_activity = Activity(100, self.date_today, self.date_next_score)

    def test_get_task(self):
        """check that finds child
        """
        self.assertEquals(self.parent.get_task('child1'), self.child1)
        self.assertEquals(self.parent.get_task('stone'), self.stone)
        self.assertEquals(self.parent.get_task('child2_1'), self.child2_1)
        self.assertEquals(self.parent.get_task('child2_2'), self.child2_2)
    
    def test_get_resource_constraints(self):
        """test rsource is found, even within parents
        """
        # XXX
        # self.assertEquals(self.parent.get_resource_constraints(), [])
        self.assertEquals(self.child1.get_resource_constraints(), set([('worker', 'inge1')]))
        self.assertEquals(self.child2_1.get_resource_constraints(), set([('worker', 'inge1')]))
        self.assertEquals(self.child2_2.get_resource_constraints(), set([('worker', 'inge2')]))
        
    def test_get_resources(self):
        """check that array of all resource id returned
        """
        self.assertEquals(self.parent.get_resources(), set(['inge1', 'inge2']))
        self.assertEquals(self.child1.get_resources(), set(['inge1']))
        self.assertEquals(self.child2.get_resources(), set(['inge1', 'inge2']))
        self.assertEquals(self.child2_1.get_resources(), set(['inge1']))
        self.assertEquals(self.child2_2.get_resources(), set(['inge2']))

    
    def test_get_priority(self):
        """test value returned
        """
        self.assertEquals(self.parent.get_priority(), None)
        self.assertEquals(self.child1.get_priority(), None)
        self.assertEquals(self.child2.get_priority(), None)
        self.assertEquals(self.child2_1.get_priority(), None)
        self.assertEquals(self.child2_2.get_priority(), None)
        self.parent.priority = 2
        self.assertEquals(self.parent.get_priority(), 2)
        self.assertEquals(self.child1.get_priority(), 2)
        self.assertEquals(self.child2.get_priority(), 2)
        self.assertEquals(self.child2_1.get_priority(), 2)
        self.assertEquals(self.child2_2.get_priority(), 2)
        self.child2.priority = 1
        self.assertEquals(self.parent.get_priority(), 2)
        self.assertEquals(self.child1.get_priority(), 2)
        self.assertEquals(self.child2.get_priority(), 1)
        self.assertEquals(self.child2_1.get_priority(), 1)
        self.assertEquals(self.child2_2.get_priority(), 1)
        
        
    def test_is_finished(self):
        """test achievement state
        """
        #input activity is the accomplished activity related to task
        # default: progress=0, duration=10, short_activity=6
        self.assertEquals(self.parent.is_finished(), False)
        self.assertEquals(self.child1.is_finished(), False)
        self.assertEquals(self.child2.is_finished(), False)
        self.assertEquals(self.child2_1.is_finished(), False)
        self.assertEquals(self.child2_2.is_finished(), False)
        # test on progress
        self.child1.progress = 1
        self.assertEquals(self.parent.is_finished(), False)
        self.assertEquals(self.child1.is_finished(), True)
        self.assertEquals(self.child2.is_finished(), False)
        self.assertEquals(self.child2_1.is_finished(), False)
        self.assertEquals(self.child2_2.is_finished(), False)
        self.child2_2.progress = 1
        self.child2_1.progress = 1
        self.assertEquals(self.child1.is_finished(), True)
        self.assertEquals(self.child2.is_finished(), True)
        self.assertEquals(self.child2_1.is_finished(), True)
        self.assertEquals(self.child2_2.is_finished(), True)
##         # test with duration=10 long_activity=20
##         self.assertEquals(self.parent.is_finished(), True)
##         self.assertEquals(self.single_task.is_finished(), True)
##         self.assertEquals(self.child_task.is_finished(), True)
        
        
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
        self.assertEquals(self.child2_2.remaining_duration(), 0)
        self.assertEquals(self.child2_1.remaining_duration(), 2.5)
        self.assertEquals(self.child2.remaining_duration(), 2.5)
        self.assertEquals(self.child1.remaining_duration(), 5)
        self.assertEquals(self.parent.remaining_duration(), 7.5)
        self.assertEquals(self.child2.progress, 14.5/17)
        self.assertEquals(self.parent.progress, 19.5/27)

    
    def test_maximum_duration(self):
        """test that all children are taken into account
        """
        self.assertEquals(self.parent.maximum_duration(), 27)
        self.assertEquals(self.child1.maximum_duration(), 10)
        self.assertEquals(self.child2.maximum_duration(), 17)
        self.assertEquals(self.child2_1.maximum_duration(), 5)
        self.assertEquals(self.child2_2.maximum_duration(), 12)


class ConsistencyTC(testlib.TestCase):

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
        self.assertEquals(self.parent.check_consistency(), [])
        self.parent.add_date_constraint(BEGIN_AT_DATE, self.date2)
        self.assertEquals(len(self.parent.check_consistency()), 1)
        
    def test_parent_begin_at2(self):
        self.parent.add_date_constraint(BEGIN_AT_DATE, self.date2)
        self.assertEquals(self.parent.check_consistency(), [])

    def test_parent_begin_at3(self):
        self.parent.add_date_constraint(BEGIN_AT_DATE, self.date3)
        self.assertEquals(self.parent.check_consistency(), [])

    def test_parent_begin_at4(self):
        self.parent.add_date_constraint(BEGIN_AT_DATE, self.date4)
        self.assertEquals(self.parent.check_consistency(), [])

    # FIXME etc.
    
class DateConstraintsTC(testlib.TestCase):

    def setUp(self):
        self.parent = Task('parent')
        self.child = Task('child')
        self.parent.append(self.child)
        
    def test_parent_begin_at(self):
        self.assertEquals(self.child.get_date_constraints(), set())
        self.parent.add_date_constraint(BEGIN_AT_DATE, DateTime(2005, 01, 01))
        constraints = self.child.get_date_constraints()
        expected = set([(BEGIN_AFTER_DATE, DateTime(2005, 01, 01), 1)])
        self.assertEquals(constraints, expected)

    def test_parent_begin_after(self):
        self.assertEquals(self.child.get_date_constraints(), set())
        self.parent.add_date_constraint(BEGIN_AFTER_DATE, DateTime(2005, 01, 01))
        constraints = self.child.get_date_constraints()
        expected = set([(BEGIN_AFTER_DATE, DateTime(2005, 01, 01), 1)])
        self.assertEquals(constraints, expected)

    def test_parent_end_at(self):
        self.assertEquals(self.child.get_date_constraints(), set())
        self.parent.add_date_constraint(END_AT_DATE, DateTime(2005, 01, 01))
        constraints = self.child.get_date_constraints()
        expected = set([(END_BEFORE_DATE, DateTime(2005, 01, 01), 1)])
        self.assertEquals(constraints, expected)

    def test_parent_end_before(self):
        self.assertEquals(self.child.get_date_constraints(), set())
        self.parent.add_date_constraint(END_BEFORE_DATE, DateTime(2005, 01, 01))
        constraints = self.child.get_date_constraints()
        expected = set([(END_BEFORE_DATE, DateTime(2005, 01, 01), 1)])
        self.assertEquals(constraints, expected)

class ProgressTC(testlib.TestCase):

    def test_get_progress(self):
        """tests progress' getter"""
        t = Task('hello')
        t.duration = 10
        self.assertEquals(t.progress, 0.)
        #activity = [100, DateTime(2005, 8, 1), DateTime(2005, 8, 4)]
        # 
        #self.assertEquals(t.progress, 0.4)
        t.progress = 0.8
        self.assertEquals(t.progress, 0.8)


    def test_set_progress(self):
        t = Task('hello')
        self.assertRaises(ValueError, setattr, t, 'progress', 12)
        self.assertRaises(ValueError, setattr, t, 'progress', -1)
        t.progress = 1
        self.assertEquals(t.progress, 1.)
    
if __name__ == '__main__':
    testlib.unittest_main()

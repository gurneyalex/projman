# -*- coding: iso-8859-1 -*-
"""
unit tests for module projman.lib.Milestone

Projman - (c)2000-2002 LOGILAB <contact@logilab.fr> - All rights reserved.
Home: http://www.logilab.org/projman

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

from mx.DateTime import DateTime
from logilab.common.testlib import TestCase, unittest_main

from projman.lib import MileStone
from projman.lib.constants import BEGIN_AFTER_END, BEGIN_AFTER_BEGIN, \
     END_AFTER_END, END_AFTER_BEGIN, \
     BEGIN_AFTER_DATE, BEGIN_AT_DATE, BEGIN_BEFORE_DATE, \
     END_AFTER_DATE, END_AT_DATE, END_BEFORE_DATE

class MilestoneTest(TestCase):
    """Test all low-level function on Milestones.
    """
    def setUp(self):
        """ called before each test from this class """
        self.stone = MileStone('Test')
        self.child_stone = MileStone('Test_child')
        self.unicode_stone = MileStone(u'accentuée')
        self.unicode_stone.description = u"autre chaîne unicode non-ASCII"
        # set of dates
        self.date_today = DateTime(2004, 10, 7)
        self.date_tomorrow = DateTime(2004, 10, 8)
        self.date_yesterday = DateTime(2004, 10, 6)
        # set of date constraints
        self.at_constraints =  {BEGIN_AT_DATE: self.date_yesterday,
                                END_AT_DATE: self.date_tomorrow}
        self.before_constraints =  {BEGIN_BEFORE_DATE: self.date_today,
                                    END_BEFORE_DATE: self.date_tomorrow}
        self.after_constraints =  {BEGIN_AFTER_DATE: self.date_yesterday,
                                   END_AFTER_DATE: self.date_today}
        self.before_after_constraints =  {BEGIN_BEFORE_DATE: self.date_today,
                                          END_AFTER_DATE: self.date_yesterday}
        # set of id
        self.good_id = 'good_id'
        self.other_id = 'other_id'
        self.another_id = 'another_id'
        self.last_id = 'last_id'
        
        
    def test_add_date_constraint(self):
        """No validation over which parameter is given.
        """
        self.stone.add_date_constraint(BEGIN_AT_DATE, self.date_today)
        self.assertRaises(AssertionError,
                          self.stone.add_date_constraint, 'fake', self.date_tomorrow)
        self.assertSetEqual(self.stone.get_date_constraints(),
                            [(BEGIN_AT_DATE, self.date_today, 1)])
        
    def test_add_task_constraint(self):
        """No validation over which parameter is given.
        """
        self.stone.add_task_constraint(BEGIN_AFTER_BEGIN, self.good_id)
        self.assertRaises(AssertionError, self.stone.add_task_constraint, 'fake', 'dumb_id')
        self.assertSetEqual(self.stone.get_task_constraints(),
                          [(BEGIN_AFTER_BEGIN,self.good_id, 1)])

#     def __test_get_range_at(self):
#         """get date range after setting constraints of type 'at' with 
#         """
#         for cst, date in self.at_constraints.items():
#             self.stone.add_date_constraint(cst, date)
#         self.assertEquals(self.stone.get_date_range(),
#                           (self.date_yesterday, self.date_tomorrow))
        
#     def __test_get_range_before(self):
#         """get date range after setting constraints of type 'before' with today, tomorrow
#         """
#         for cst, date in self.before_constraints.items():
#             self.stone.add_date_constraint(cst, date)
#         self.assertEquals(self.stone.get_date_range(),
#                           (self.date_today, self.date_tomorrow))
        
#     def __test_get_range_after(self):
#         """get date range after setting constraints of type 'after' with yesterday, today
#         """
#         for cst, date in self.after_constraints.items():
#             self.stone.add_date_constraint(cst, date)
#         self.assertEquals(self.stone.get_date_range(),
#                           (self.date_yesterday, self.date_today))
        
#     def __test_get_range_before_after(self):
#         """get date range after setting constraints of type 'before, after' with today, yesterday
#         """
#         for cst, date in self.before_after_constraints.items():
#             self.stone.add_date_constraint(cst, date)
#         self.assertEquals(self.stone.get_date_range(),
#                           (self.date_today, self.date_yesterday))

#     def ___test_get_task_constraints(self):
#         """Create a child and checks inheritance of task constraints
#         """
#         # set up Milestone
#         constraints = {BEGIN_AFTER_BEGIN: [self.good_id, self.other_id],
#                        END_AFTER_END: [self.another_id]}
#         for key, values in constraints.items():
#             for value in values:
#                 self.stone.add_task_constraint(key, value)
#         # child
#         child_constraints =  {BEGIN_AFTER_END: [self.another_id],
#                               END_AFTER_END : [self.last_id]}
#         for key, values in child_constraints.items():
#             for value in values:
#                 self.child_stone.add_task_constraint(key, value)
#         # create parent
#         self.stone.append(self.child_stone)
#         # test getter
#         all_constraints = {BEGIN_AFTER_BEGIN: [self.good_id, self.other_id],
#                            END_AFTER_END: [self.another_id, self.last_id],
#                            BEGIN_AFTER_END: [self.another_id]}
#         result = self.child_stone.get_task_constraints()
#         for key in all_constraints.keys():
#             all_constraints[key].sort()
#             result[key].sort()
#             self.assertEquals(all_constraints[key], result[key])
        
#     def ___test_get_date_constraints(self):
#         """Create a child and checks inheritance of date constraints
#            BEWARE: begin-at-date & end-at-date ar inherited as
#            begin-after-date & end-before-date
#         """
#         # milestone
#         for cst, date in self.at_constraints.items():
#             self.stone.add_date_constraint(cst, date)
#         for cst, date in self.before_constraints.items():
#             self.stone.add_date_constraint(cst, date)
#         for cst, date in self.before_after_constraints.items():
#             self.child_stone.add_date_constraint(cst, date)
#         # create parent
#         self.stone.append(self.child_stone)
#         # test getter
#         all_constraints = {BEGIN_BEFORE_DATE: self.date_today,
#                            END_BEFORE_DATE: self.date_tomorrow,
#                            BEGIN_BEFORE_DATE: self.date_today,
#                            END_AFTER_DATE: self.date_yesterday}
#         result = self.child_stone.get_date_constraints()
#         for key in all_constraints.keys():
#             self.assertEquals(all_constraints[key], result[key])
#         for key in [BEGIN_AT_DATE, END_AT_DATE]:
#             self.assertRaises(KeyError, result.__getitem__, key)

if __name__ == '__main__':
    unittest_main()

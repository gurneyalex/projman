# -*- coding: iso-8859-1 -*-
"""
unit tests for module logilab.projman.lib.Resource

Projman - (c)2000-2013 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projman

Manipulate a xml project description.

This code is released under the GNU Public Licence v2. See www.gnu.org.

"""

from logilab.common.testlib import TestCase, unittest_main

from projman.lib import Resource, Calendar
from mx.DateTime import DateTime, Time
from projman.test.unittest_lib_Project import simple_project

class ResourceTest(TestCase):
    """
    Resource represents
    """
    def setUp(self):
        """ called before each test from this class """
        _, _, resources, _, _, cal = simple_project()
        # set of dates
        self.date_last_week = DateTime(2004, 10, 1)
        self.date_today = DateTime(2004, 10, 7)
        self.date_tomorrow = DateTime(2004, 10, 8)
        self.date_next_week = DateTime(2004, 10, 13)
        self.date_next_score = DateTime(2004, 10, 26)
        # set up calendar
        cal.day_types = {'working':['Working', [(Time(8), Time(12)),
                                                    (Time(13), Time(17))]],
                             'halfday':['HalfDay', [(Time(9), Time(15))]],
                             'nonworking': ['Nonworking', []],
                             }
        cal.default_day_type = 'working'
        cal.add_timeperiod(self.date_last_week, self.date_last_week,
                              'nonworking')
        cal.add_timeperiod(self.date_today, self.date_today, 'working')
        cal.add_timeperiod(self.date_tomorrow, self.date_next_week, 'halfday')
        cal.weekday['sat'] = 'nonworking'
        cal.weekday['sun'] = 'nonworking'
        # set up calendar 2
        cal_2 = Calendar('c_2', 'Special Calendar')
        cal_2.add_timeperiod(self.date_next_week, self.date_next_score,
                               'nonworking')
        # build tree
        cal.append(cal_2)
        # set up resources
        self.r1 = resources[0] # tata
        self.r2 = resources[1] # toto
        self.r2.calendar = cal_2

    def test_is_available(self):
        """
        tests if a resource is available on datetime according to its calendar
        """
        # test r_1
        self.assertEqual(self.r1.is_available(self.date_last_week), False)
        self.assertEqual(self.r1.is_available(self.date_today), True)
        self.assertEqual(self.r1.is_available(self.date_tomorrow), True)
        self.assertEqual(self.r1.is_available(self.date_next_week), True)
        # test r_2
        self.assertEqual(self.r2.is_available(self.date_last_week), False)
        self.assertEqual(self.r2.is_available(self.date_today), True)
        self.assertEqual(self.r2.is_available(self.date_tomorrow), True)
        self.assertEqual(self.r2.is_available(self.date_next_week), False)
        self.assertEqual(self.r2.is_available(self.date_next_score), False)

    def test_get_duration_of_work(self):
        """
        return the total number of seconds of work at datetime
        """
        self.assertEqual(self.r1.get_worktime(self.date_next_week).hours, 6)
        self.assertEqual(self.r2.get_worktime(self.date_next_week).hours, 0)
        self.assertEqual(self.r2.get_worktime(self.date_tomorrow).hours, 6)
        self.assertEqual(self.r2.get_worktime(self.date_today).hours, 8)

if __name__ == '__main__':
    unittest_main()

# -*- coding: iso-8859-1 -*-
"""
unit tests for module logilab.projman.lib.Resource

Projman - (c)2000-2002 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projman

Manipulate a xml project description.

This code is released under the GNU Public Licence v2. See www.gnu.org.

"""
__revision__ = "$Id: unittest_lib_Resource.py,v 1.11 2005-09-06 18:27:45 nico Exp $"

from logilab.common.testlib import TestCase, unittest_main

from projman.lib import Resource, Calendar, ResourcesSet
from mx.DateTime import DateTime, Time
    
class ResourceTest(TestCase):
    """
    Resource represents 
    """
    def setUp(self):
        """ called before each test from this class """
        # set up resources
        self.r1 = Resource('r_1', 'Resource 1')
        self.r1.calendar = 'c_1'
        self.r2 = Resource(u'où', u'là-bas')
        self.r2.calendar = 'c_2'
        # set of dates
        self.date_last_week = DateTime(2004, 10, 1)
        self.date_today = DateTime(2004, 10, 7)
        self.date_tomorrow = DateTime(2004, 10, 8)
        self.date_next_week = DateTime(2004, 10, 13)
        self.date_next_score = DateTime(2004, 10, 26)
        # set up calendar 1      
        self.c1 = Calendar('c_1', 'Defaut')
        self.c1.day_types = {'working':['Working', [(Time(8), Time(12)),
                                                    (Time(13), Time(17))]],
                             'halfday':['HalfDay', [(Time(9), Time(15))]],
                             'nonworking': ['Nonworking', []],
                             } 
        self.c1.default_day_type = 'working'
        self.c1.add_timeperiod(self.date_last_week, self.date_last_week, 'nonworking')
        self.c1.add_timeperiod(self.date_today, self.date_today, 'working')
        self.c1.add_timeperiod(self.date_tomorrow, self.date_next_week, 'halfday')
        self.c1.weekday['sat'] = 'nonworking'
        self.c1.weekday['sun'] = 'nonworking'
        # set up calendar 2        
        self.c2 = Calendar('c_2', u'Année 2')
        self.c2.add_timeperiod(self.date_next_week, self.date_next_score, 'nonworking')
        # build tree
        self.c1.append(self.c2)
        self.rss = ResourcesSet('all_resources')
        self.rss.add_resource(self.r1)
        self.rss.add_resource(self.r2)
        self.rss.add_calendar(self.c1)
        
    def test_get_default_wt_in_hours(self):
        self.assertEqual(self.r1.get_default_wt_in_hours(), 8)
        
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

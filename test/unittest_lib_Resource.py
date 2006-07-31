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
        type_working_days_c1 = {0:['Working', [(Time(8., 0.), Time(12., 0.)),
                                               (Time(13., 0.), Time(17., 0.))]],
                                1:['HalfDay', [(Time(9., 0., 0.), Time(15., 0., 0.))]]}
        type_nonworking_days_c1 = {0:'Use base',
                                   1:'Nonworking'} 
        self.c1.type_working_days = type_working_days_c1
        self.c1.type_nonworking_days = type_nonworking_days_c1
        self.c1.default_working = 0
        self.c1.default_nonworking = 1
        self.c1.add_timeperiod(self.date_last_week, self.date_last_week, 'Nonworking')
        self.c1.add_timeperiod(self.date_today, self.date_today, 'Working')
        self.c1.add_timeperiod(self.date_tomorrow, self.date_next_week, 'HalfDay')
        self.c1.weekday['mon'] = 'Working'
        self.c1.weekday['tue'] = 'Working'
        self.c1.weekday['wed'] = 'Working'
        self.c1.weekday['thu'] = 'Working'
        self.c1.weekday['fri'] = 'Working'
        self.c1.weekday['sat'] = 'Nonworking'
        self.c1.weekday['sun'] = 'Nonworking'
        # set up calendar 2        
        type_working_days_c2 = {}
        type_nonworking_days_c2 = {0:'Use base',
                                   1:'Nonworking'}
        self.c2 = Calendar('c_2', u'Année 2')
        self.c2.type_working_days = type_working_days_c2
        self.c2.type_nonworking_days = type_nonworking_days_c2
        self.c2.default_working = None
        self.c2.default_nonworking = 1
        self.c2.add_timeperiod(self.date_next_week, self.date_next_score, 'Nonworking')
        self.c2.weekday['mon'] = 'Use base'
        self.c2.weekday['tue'] = 'Use base'
        self.c2.weekday['wed'] = 'Use base'
        self.c2.weekday['thu'] = 'Use base'
        self.c2.weekday['fri'] = 'Use base'
        self.c2.weekday['sat'] = 'Use base'
        self.c2.weekday['sun'] = 'Use base'
        # build tree
        self.c1.append(self.c2)
        self.rss = ResourcesSet('all_resources')
        self.rss.add_resource(self.r1)
        self.rss.add_resource(self.r2)
        self.rss.add_calendar(self.c1)
        
    def test_get_default_wt_in_hours(self):
        self.assertEqual(self.r1.get_default_wt_in_hours(), 8)
        
    def test_work_on(self):
        """
        tests if a resource is available on datetime according to its calendar
        """
        # test r_1
        self.assertEqual(self.r1.work_on(self.date_last_week), False)
        self.assertEqual(self.r1.work_on(self.date_today), True)
        self.assertEqual(self.r1.work_on(self.date_tomorrow), True)
        self.assertEqual(self.r1.work_on(self.date_next_week), True)
        # test r_2
        self.assertEqual(self.r2.work_on(self.date_last_week), False)
        self.assertEqual(self.r2.work_on(self.date_today), True)
        self.assertEqual(self.r2.work_on(self.date_tomorrow), True)
        self.assertEqual(self.r2.work_on(self.date_next_week), False)
        self.assertEqual(self.r2.work_on(self.date_next_score), False)
        
    def test_get_duration_of_work(self):
        """
        return the total nimber of seconds of work at datetime
        """
        self.assertEqual(self.r1.get_duration_of_work(self.date_next_week), 21600)
        self.assertEqual(self.r2.get_duration_of_work(self.date_next_week), 0)
        self.assertEqual(self.r2.get_duration_of_work(self.date_tomorrow), 21600)
        self.assertEqual(self.r2.get_duration_of_work(self.date_today), 28800)

if __name__ == '__main__':
    unittest_main()

"""
Projman - (c)2000-2007 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projman

Manipulate a xml project description.

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

from mx.DateTime import DateTime, Time, Date
from logilab.common import testlib
from projman.lib import *
    
class CalendarTC(testlib.TestCase):
    """
    Calendar represents 
    """
    def setUp(self):
        """ called before each test from this class """
        self.o = Project()
        self.o.title = 'Projman'

        self.rss = ResourcesSet('all_resources')

        self.r1 = Resource('r_1', 'Resource 1')
        self.r1.calendar = 'c_1'
        self.r1.type = '1'

        self.r2 = Resource('r_2', 'Resource 2')
        self.r2.calendar = 'c_2'
        self.r2.type = '1'

        type_working_days_c1 = {0:['Working', [(Time(8, 0), Time(12, 0)),
                                               (Time(13, 0), Time(17, 0))]], 
                                1:['HalfDay', [(Time(9, 0), Time(15, 0))]]}
        type_nonworking_days_c1 = {0:'Use base', 1:'Nonworking'}
        type_working_days_c2 = {}
        type_nonworking_days_c2 = {0:'Use base', 1:'Nonworking'}
        
        self.c1 = Calendar('c_1', 'Defaut')
        self.c1.type_working_days = type_working_days_c1
        self.c1.type_nonworking_days = type_nonworking_days_c1
        self.c1.default_working = 0
        self.c1.default_nonworking = 1
        self.c1.national_days = [(1,1), (12,25), (11,11)]
	self.c1.start_on = DateTime(2004,01,06) 
	self.c1.stop_on = DateTime(2006,12,29) 
        self.c2 = Calendar('c_2', 'Calendrier 2') 
        self.c1.append(self.c2)
        self.c2.type_working_days = type_working_days_c2
        self.c2.type_nonworking_days = type_nonworking_days_c2
        self.c2.default_working = 1
        self.c2.default_nonworking = 1
        date = DateTime(2004, 05, 07)
        self.c1.add_timeperiod(date, date, 'Nonworking')
        date = DateTime(2004, 05, 05)
        self.c1.add_timeperiod(date, date, 'Working')
        date = DateTime(2004, 06, 07)
        self.c1.add_timeperiod(date, date, 'HalfDay')
        from_date = DateTime(2004, 06, 12)
        to_date = DateTime(2004, 06, 23)
        self.c2.add_timeperiod(from_date, to_date, 'Nonworking')
        self.c1.weekday['mon'] = 'Working'
        self.c1.weekday['tue'] = 'Working'
        self.c1.weekday['wed'] = 'Working'
        self.c1.weekday['thu'] = 'Working'
        self.c1.weekday['fri'] = 'Working'
        self.c1.weekday['sat'] = 'Nonworking'
        self.c1.weekday['sun'] = 'Nonworking'
        
        self.c2.weekday['mon'] = 'Use base'
        self.c2.weekday['tue'] = 'Use base'
        self.c2.weekday['wed'] = 'Use base'
        self.c2.weekday['thu'] = 'Use base'
        self.c2.weekday['fri'] = 'Use base'
        self.c2.weekday['sat'] = 'Use base'
        self.c2.weekday['sun'] = 'Use base'

        self.c1.append(self.c2)

        self.rss.add_resource(self.r1)
        self.rss.add_resource(self.r2)
        self.rss.add_calendar(self.c1)

        self.o.add_resource_set(self.rss)

    def test_within_bounds(self):
        self.assertEquals(self.c1.after_start(Date(2003,1,1)), False)
        self.assertEquals(self.c1.after_start(Date(2004,1,5)), False)
        self.assertEquals(self.c1.after_start(Date(2004,1,6)), True)
        self.assertEquals(self.c1.after_start(Date(2005,1,1)), True)
        self.assertEquals(self.c1.before_stop(Date(2003,1,1)), True)
        self.assertEquals(self.c1.before_stop(Date(2006,12,30)), False)

    def test_know_values_is_available(self):
        """
        return True if datetime is a working day for the calendar
        """
        self.assertEqual(self.c1.is_available(DateTime(2004, 01, 05)), False)
        self.assertEqual(self.c1.is_available(DateTime(2004, 01, 06)), True)
        self.assertEqual(self.c1.is_available(DateTime(2004, 05, 07)), False)
        self.assertEqual(self.c1.is_available(DateTime(2006, 12, 29)), True)
        self.assertEqual(self.c1.is_available(DateTime(2006, 12, 30)), False)
        self.assertEqual(self.c2.is_available(DateTime(2004, 05, 07)), False)

    def test_know_values_is_a_working_type(self):
        """
        return True if t_name is a working type according to inheritings properties
        """
        self.assertEqual(self.c1.is_a_working_type('Working'), True)
        self.assertEqual(self.c1.is_a_working_type('Nonworking'), False)
        self.assertEqual(self.c2.is_a_working_type('Working'), True)
        self.assertEqual(self.c2.is_a_working_type('Nonworking'), False)

    def test_known_values_get_weekday_type(self):
        """
        return of the week day associated to datetime
        """
        self.assertEqual(self.c1.get_weekday_type(DateTime(2004, 05, 07)), 'Working')
        self.assertEqual(self.c2.get_weekday_type(DateTime(2004, 03, 14)), 'Nonworking')

    def test_known_values_is_specified(self):
        """
        test if datetime is in timeperiods
        """
        self.assertEqual(self.c1.is_specified(DateTime(2004, 05, 07)), True)
        self.assertEqual(self.c2.is_specified(DateTime(2004, 05, 07)), False)
        self.assertEqual(self.c2.is_specified(DateTime(2004, 06, 15)), True)

    def test_known_values_get_type(self):
        """
        return the type associated to datetime
        """
        self.assertEqual(self.c1.get_type(DateTime(2004, 05, 07)), 'Nonworking')
        self.assertEqual(self.c2.get_type(DateTime(2004, 02, 11)), '')

    def tet_known_values_get_type_id(self):
        """
        return the id associated to t_name
        """
        self.assertEqual(self.c1.get_type_id('Working'), 0)
        self.assertEqual(self.c2.get_type_id('Working'), 0)
        self.assertEqual(self.c1.get_type_id('toto'), '')

    def test_known_values_get_intervals(self):
        """
        return tuple of DeltaTime object cooresponding to time of work at datetime
        if datetime is a nonworking day return None
        """
        self.assertEqual(self.c1.get_intervals(DateTime(2004, 05, 07)), None)
        self.assertEqual(self.c1.get_intervals(DateTime(2004, 05, 05)), [(Time(8, 0), Time(12, 0)), (Time(13, 0), Time(17, 0))])
        self.assertEqual(self.c2.get_intervals(DateTime(2004, 03, 25)), [(Time(8, 0), Time(12, 0)), (Time(13, 0), Time(17, 0))])
        self.assertEqual(self.c2.get_intervals(DateTime(2004, 06, 07)), [(Time(9), Time(15, 0))])


    def test_known_values_get_total_intervals(self):
        """
        return the number of seconds of work time for datetime
        """
        self.assertEqual(self.c1.get_total_intervals(DateTime(2004, 05, 07)), 0)
        self.assertEqual(self.c1.get_total_intervals(DateTime(2004, 05, 05)), 28800)
        self.assertEqual(self.c2.get_total_intervals(DateTime(2004, 06, 07)), 21600)

    def test_known_values_is_a_national_day(self):
        """
        tests if datetime is a national day off
        """
        self.assertEqual(self.c1.is_a_national_day(DateTime(2012, 01, 01)), True)
        self.assertEqual(self.c1.is_a_national_day(DateTime(2012, 04, 01)), False)
        self.assertEqual(self.c2.is_a_national_day(DateTime(2012, 01, 01)), True)

if __name__ == '__main__':
    testlib.unittest_main()

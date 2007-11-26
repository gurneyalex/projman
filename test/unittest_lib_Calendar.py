"""
Projman - (c)2000-2007 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projman

Manipulate a xml project description.

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

from mx.DateTime import DateTime, Time, Date
from logilab.common import testlib
from projman.lib import Project, Calendar, ResourcesSet, Resource

MORNING = (Time(8), Time(12))
AFTERNOON = (Time(13), Time(17))
HALFDAY = (Time(9), Time(15))

def mk_calendar1():
    cal = Calendar('c_1', 'Calendrier 1')
    cal.day_types = {'nonworking': ['Non working', []],
                     'working':    ['Working', [MORNING, AFTERNOON]],
                     
                         'halfday':    ['HalfDay', [HALFDAY]],
                         }
    cal.default_day_type = 'working'
    cal.national_days = [(1,1), (12,25), (11,11)]
    cal.start_on = DateTime(2004,01,06) 
    cal.stop_on = DateTime(2006,12,29)
    cal.weekday['mon'] = 'working'
    cal.weekday['tue'] = 'working'
    cal.weekday['wed'] = 'working'
    cal.weekday['thu'] = 'working'
    cal.weekday['fri'] = 'working'
    cal.weekday['sat'] = 'nonworking'
    cal.weekday['sun'] = 'nonworking'

    date = DateTime(2004, 05, 07)
    cal.add_timeperiod(date, date, 'nonworking')
    date = DateTime(2004, 05, 05)
    cal.add_timeperiod(date, date, 'working')
    date = DateTime(2004, 06, 07)
    cal.add_timeperiod(date, date, 'halfday')
    return cal

def mk_calendar2():
    cal = Calendar('c_2', 'Calendrier 2') 
    from_date = DateTime(2004, 06, 12)
    to_date = DateTime(2004, 06, 23)
    cal.add_timeperiod(from_date, to_date, 'nonworking')
    return cal

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
        self.rss.add_resource(self.r1)
        
        self.r2 = Resource('r_2', 'Resource 2')
        self.r2.calendar = 'c_2'
        self.r2.type = '1'
        self.rss.add_resource(self.r2)
        
        self.c1 = mk_calendar1()
        self.c2 = mk_calendar2()
        self.c1.append(self.c2)
        self.rss.add_calendar(self.c1)

        self.o.add_resource_set(self.rss)

    def test_within_bounds(self):
        self.assertEquals(self.c1.after_start(Date(2003,1,1)), False)
        self.assertEquals(self.c1.after_start(Date(2004,1,5)), False)
        self.assertEquals(self.c1.after_start(Date(2004,1,6)), True)
        self.assertEquals(self.c1.after_start(Date(2005,1,1)), True)
        self.assertEquals(self.c1.before_stop(Date(2003,1,1)), True)
        self.assertEquals(self.c1.before_stop(Date(2006,12,30)), False)

    def test_availability(self):
        DAY = [MORNING, AFTERNOON]
        self.assertEqual(self.c1.availability(DateTime(2004, 01, 05)), [])
        self.assertEqual(self.c1.availability(DateTime(2004, 01, 06)), DAY)
        self.assertEqual(self.c1.availability(DateTime(2004, 05, 07)), [])
        self.assertEqual(self.c1.availability(DateTime(2004, 06, 07)), [HALFDAY])
        self.assertEqual(self.c1.availability(DateTime(2006, 12, 29)), DAY)
        self.assertEqual(self.c1.availability(DateTime(2006, 12, 30)), [])
        self.assertEqual(self.c2.availability(DateTime(2004, 05, 07)), [])

    def test_get_total_intervals(self):
        self.assertEqual(self.c1.get_worktime('nonworking').hours, 0)
        self.assertEqual(self.c1.get_worktime('working').hours, 8)
        self.assertEqual(self.c2.get_worktime('halfday').hours, 6)

    def test_is_a_national_day(self):
        self.assertEqual(self.c1.is_a_national_day(DateTime(2012, 01, 01)), True)
        self.assertEqual(self.c1.is_a_national_day(DateTime(2012, 04, 01)), False)
        self.assertEqual(self.c2.is_a_national_day(DateTime(2012, 01, 01)), True)
        self.assertEqual(self.c2.is_a_national_day(DateTime(2012, 02, 02)), False)

    def test_get_daytype(self):
        self.assertEquals(self.c1.get_default_daytype(), 'working')
        self.assertEquals(self.c2.get_default_daytype(), 'working')
        
if __name__ == '__main__':
    testlib.unittest_main()

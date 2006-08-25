# -*- coding: iso-8859-1 -*-
"""
unit tests for module logilab.projman.lib.ResourceSet

Projman - (c)2000-2002 LOGILAB <contact@logilab.fr> - All rights reserved.
Home: http://www.logilab.org/projman

Manipulate a xml project description.
This code is released under the GNU Public Licence v2. See www.gnu.org.

"""

from logilab.common import testlib

from projman.lib import Resource, Calendar, ResourcesSet
from mx.DateTime import DateTime, Time
    
class ResourceTest(testlib.TestCase):
    """
    Resource represents 
    """
    def setUp(self):
        """ called before each test from this class """
        # set up resources
        self.r1 = Resource('r_1', 'Resource 1')
        self.r1.calendar = 'c_1'
        self.r2 = Resource('unicode', u'élise')
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
        self.c2 = Calendar('c_2', u'Année')
        self.c2.type_working_days = type_working_days_c2
        self.c2.type_nonworking_days = type_nonworking_days_c2
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
        
    def test_get_resource(self):
        """
        """
        self.assertEquals(self.rss.get_resource('r_1'), self.r1)
        self.assertEquals(self.rss.get_resource('unicode'), self.r2)

    def test_get_resources(self):
        """
        """
        self.assertEquals(self.rss.get_resources(), ['r_1', 'unicode'])

    def test_get_calendar(self):
        """
        """
        self.assertEquals(self.rss.get_calendar('c_1'), self.c1)
        self.assertEquals(self.rss.get_calendar('c_2'), self.c2)
    
if __name__ == '__main__':
    testlib.unittest_main()

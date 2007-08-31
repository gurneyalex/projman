# -*- coding: utf-8 -*-
# Copyright (c) 2004-2006 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

"""
Projman - (c)2000-2006 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projman

Manipulate a xml project description.

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

from logilab.common.tree import VNode 
from mx.DateTime import Time, TimeDelta

from projman import DAY_WEEK

class Calendar(VNode):
    """
    Defines which days are work days.

    All days are work days, unless told otherwise by the calendar.
    """

    TYPE = 'calendar'
    
    def __init__(self, id, name=u''):
        VNode.__init__(self, id)
        self.name = name
        self.day_types = {}
        # example:
        #  {'working': ['DefaultWorking', [(Time(8), Time(12)),
        #                                  (Time(13), Time(17))]
        #              ],
        #  'nonworking': ['DefaultNonworking', []],
        # }
        self.default_day_type = None
        # day type in a usual week
        # ex : {day_of_week:type, ...} and day_of_week
        # in {mon, tue, wed, thu, fri, sat, sun}
        self.weekday = {}
        # list of periods associated to its type 
        #ex: [(from_date, to_date, type), ...]
        # with from_date and to_date as DateTime object
        self.timeperiods = []
        # register the national day, so a relative date 
        # available each year (mm/dd)
        self.national_days = []
        self.start_on = None
        self.stop_on = None

    def add_timeperiod(self, from_datetime, to_datetime, type):
        """
        add a time period in this calendar associated to its type
        """
        new_timeperiods = []
        if self.timeperiods:
            flag = 0
            for timeperiod in self.timeperiods:
                flag2 = 0
                if (timeperiod[1]+1).date >= from_datetime.date \
                       and (timeperiod[1]).date <= to_datetime.date \
                       and timeperiod[2] == type:
                    new_timeperiods.append((timeperiod[0], to_datetime, type))
                    flag = 1
                    flag2 = 1
                elif (timeperiod[1]+1).date >= from_datetime.date \
                     and (timeperiod[1]).date <= to_datetime.date \
                     and (timeperiod[0]).date >= from_datetime.date \
                     and timeperiod[2] == type:
                    new_timeperiods.append((from_datetime, to_datetime, type))
                    flag = 1
                    flag2 = 1
                elif (timeperiod[0]-1).date <= to_datetime.date \
                         and timeperiod[1].date >= to_datetime.date \
                         and timeperiod[2] == type:
                    new_timeperiods.append((from_datetime, timeperiod[1], type))
                    flag = 1
                    flag2 = 1
                elif from_datetime.date <= timeperiod[0].date \
                     and to_datetime.date >= timeperiod[1].date \
                     and timeperiod[2] == type:
                    new_timeperiods.append((from_datetime, to_datetime, type))
                    flag = 1
                    flag2 = 1
                if flag2 == 0:
                    new_timeperiods.append(timeperiod)
            if flag == 0:
                new_timeperiods.append((from_datetime, to_datetime, type))
        else:
            new_timeperiods.append((from_datetime, to_datetime, type))
           
        self.timeperiods = new_timeperiods
        
        # check that timeperiods can merge together
        new_timeperiods = []
        merged_index = []
        for i in range(len(self.timeperiods)):
            flag = 0
            for k in range(len(self.timeperiods)):
                if k != i and k > i:
                    if self.timeperiods[i][0].date == self.timeperiods[k][1].date \
                           and self.timeperiods[i][2] == self.timeperiods[k][2]:
                        new_timeperiods.append(
                            (self.timeperiods[k][0], 
                             self.timeperiods[i][1], 
                             self.timeperiods[i][2]))
                        flag = 1
                        merged_index.append(k)
                    elif self.timeperiods[i][1].date == self.timeperiods[k][0].date \
                             and self.timeperiods[i][2] == self.timeperiods[k][2]:
                        new_timeperiods.append(
                            (self.timeperiods[i][0], 
                             self.timeperiods[k][1], 
                             self.timeperiods[i][2]))
                        flag = 1
                        merged_index.append(k)
            if flag == 0 and i not in merged_index:
                new_timeperiods.append( 
                    (self.timeperiods[i][0], 
                     self.timeperiods[i][1], 
                     self.timeperiods[i][2]))

        self.timeperiods = new_timeperiods
                    

    def availability(self, datetime):
        """
        return work intervals on that datetime.
        """
        if not self.after_start(datetime):
	    return []

	if not self.before_stop(datetime):
	    return []

        if self.is_a_national_day(datetime):
            return []

        daytype = self.get_daytype(datetime)
        return self._get_intervals(daytype)

    def is_a_national_day(self, datetime):
        """
        test if datetime is a national day off
        """
        cal = self
        while isinstance(cal, Calendar):
            if (datetime.month, datetime.day) in cal.national_days:
                return True
            cal = cal.parent
        return False
    
    def after_start(self, datetime):
        cal = self
        while isinstance(cal, Calendar):
            if cal.start_on:
	        if cal.start_on <= datetime:
		    return True
		else:
                    return False
            cal = cal.parent
        return True

    def before_stop(self, datetime):
        cal = self
        while isinstance(cal, Calendar):
            if cal.stop_on:
	        if datetime <= cal.stop_on:
		    return True
		else:
                    return False
            cal = cal.parent
        return True 
 
    def _get_intervals(self, daytype):
        cal = self
        while isinstance(cal, Calendar):
            if daytype in cal.day_types:
                return cal.day_types[daytype][1]
            cal = cal.parent
        raise ValueError('Unknown day type %s' % daytype)

    def get_daytype(self, datetime):
        """
        compute then return day type (a key in self.day_types) for date datetime.
        """
        daytype = self._get_daytype_timeperiods(datetime)
        if daytype is None:
            daytype = self._get_daytype_weekday(datetime)
        if daytype is None:
            daytype = self.get_default_daytype()
        if daytype is None:
            raise Exception('Unable to compute daytype for "%s" in calendar "%s"' 
                            % (datetime, self.name))
        return daytype
    
    def _get_daytype_timeperiods(self, datetime):
        cal = self
        while isinstance(cal, Calendar):
            for from_date, to_date, _type in cal.timeperiods:
                if from_date <= datetime <= to_date:
                    return _type
            cal = cal.parent
        return None

    def _get_daytype_weekday(self, datetime):
        """
        return the type of date acording to the day of the week
        and to the inheriting properties
        """
        day = DAY_WEEK[datetime.day_of_week]
        cal = self
        while isinstance(cal, Calendar):
            if day in cal.weekday:
                return cal.weekday[day]
            cal = cal.parent
        return None

    def get_default_daytype(self):
        cal = self
        while isinstance(cal, Calendar):
            if cal.default_day_type is not None:
                return cal.default_day_type
            cal = cal.parent
        return None

    def get_worktime(self, daytype):
        """
        return a TimeDelta representing the amount of work time on datetime.
        """
        res = TimeDelta(0)
        intervals = self._get_intervals(daytype)
        for from_time, to_time in intervals:
            res += to_time - from_time
        return res




# -*- coding: ISO-8859-1 -*-
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

__revision__ = "$Id: calendar.py,v 1.2 2005-09-06 17:06:53 nico Exp $"

from logilab.common.tree import VNode 
from mx.DateTime import Time

# FIXME: day_week probably exists in DateTime
day_week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

class Calendar(VNode):
    """
    Defines which days are work days.

    All days are work days, unless told otherwise by the calendar.
    """

    TYPE = 'calendar'
    
    def __init__(self, id, name=u''):
        VNode.__init__(self, id)
        self.name = name
        self.type_working_days = {'0':
                                  ['DefaultWorking',
                                   [(Time(8.0, 0.0, 0.0), Time(12.0, 0.0, 0.0)),
                                    (Time(13.0, 0.0, 0.0), Time(17.0, 0.0, 0.0))
                                    ]
                                   ]
                                  }
        # type of days of non work
        self.type_nonworking_days = {'0': 'DefaultNonworking'}
        # default working type
        self.default_working = u''
        # default non working type
        self.default_nonworking = u''
        # day type in a usual week
        # ex : {day_of_week:type, ...} and day_of_week 
        #in {mon, tue, wed, thu, fri, sat, sun}
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
                    
                
    def is_available(self, datetime):
        """
        return True if <datetime> is a working type of day for the calendar
        according to inheriting properties
        else return False
        """
        examined = False
        cal = self
        last = self
        c_spec = self
        day_type = u''

        if self.is_a_national_day(datetime):
            return False
        
        # case of root calendar
        if cal.is_specified(datetime):
            examined = True
            c_spec = self
            day_type = c_spec.get_type(datetime)
            
        while not examined and cal.TYPE == 'calendar' :
            examined = cal.is_specified(datetime)
            if examined:
                c_spec = cal
                day_type = cal.get_type(datetime)
                last = cal
            cal = cal.parent
        if examined:
            return c_spec.is_a_working_type(day_type)
        else:
            return last.is_a_working_type(last.get_weekday_type(datetime))

# Useful methods for calendar manipulation ##############################

    def is_a_working_type(self, t_name):
        """
        test if t_name is a working type in the calendar 
        according to inherited properties
        """
        cal = self
        while cal.TYPE == 'calendar':
            for item in cal.type_working_days.values():
                if item[0] == t_name:
                    return True
            cal = cal.parent
        return False

    def is_a_national_day(self, datetime):
        """
        test if datetime is a national day off
        """
        cal = self
        while cal.TYPE == 'calendar':
            if (datetime.month, datetime.day) in cal.national_days:
                return True
            cal = cal.parent
        return False
    

    def get_weekday_type(self, date):
        """
        return the type of date acording to the day of the week
        and to the inheriting properties
        """
        day = day_week[date.day_of_week]
        if day in self.weekday and self.weekday[day] != 'Use base':
            return self.weekday[day]
        else:
            return self.parent.get_weekday_type(date)

    def is_specified(self, date):
        """
        test if date is in timeperiods
        """
        for from_date, to_date, _type in self.timeperiods:
            if from_date <= date <= to_date:
                return True
        return False

    def get_type(self, date):
        """
        return the type associated to date in calendar, according to
        timeperiods
        if date is not in timeperiods return empty string
        """
        for from_date, to_date, _type in self.timeperiods:
            if from_date <= date <= to_date:
                return _type
        return u''

    def get_type_id(self, type):
        """
        return the tuple (type_id, cal_ref_id) associated to type name
        """
        examined = False
        cal = self
        while cal.TYPE == 'calendar':
            for t_d in cal.type_working_days:
                if cal.type_working_days[t_d][0] == type:
                    examined = True
                    return (t_d, cal.id)
            for t_d in cal.type_nonworking_days:
                if cal.type_nonworking_days[t_d] == type:
                    examined = True
                    return (t_d, cal.id)
            cal = cal.parent
        if not examined:
            raise Exception('Unknown type of days')

    def get_default_worktime(self):
        """
        return the number of seconds of work for a default day of work
        """
        cal = self
        while cal.TYPE == 'calendar':
            if cal.TYPE == 'calendar' and cal.default_working != u'':
                intervals =  cal.type_working_days[cal.default_working][1]
                return cal.get_total_seconds(intervals)
            cal = cal.parent
        raise ValueError("no default worktime found")

    def get_default_wt_in_hours(self):
        """
        return the number of hours of work for a default day of work
        """
        return  self.get_default_worktime() / 3600
        
    def get_total_intervals(self, datetime):
        """
        return the number of seconds ok work for datetime
        """
        intervals = self.get_intervals(datetime)
        if intervals:
            return self.get_total_seconds(intervals)
        return 0

    def get_total_seconds(self, intervals):
        """
        return the seconds corresponding to intervals
        """
        res = 0
        for from_time, to_time in intervals:
            res += to_time - from_time
        return (res.hours * 60 * 60) + (res.minute * 60)

    def get_intervals(self, datetime):
        """
        return the intervals of work associated to datetime
        """
        cal = self
        examined = False
        if cal.is_specified(datetime):
            examined = True
            c_spec = self
            type = c_spec.get_type(datetime)
            id_t = c_spec.get_type_id(type)[0]
            
        while not examined and cal.TYPE == 'calendar' :
            examined = cal.is_specified(datetime)
            if examined:
                c_spec = cal
                type = cal.get_type(datetime)
                id_t = cal.get_type_id(type)[0]
            cal = cal.parent
        if examined:
            if c_spec.is_a_working_type(type):
                return c_spec.type_working_days[id_t][1]
            else:
                return None
        else:
            day = day_week[datetime.day_of_week]
            cal = self
            while cal.TYPE == 'calendar':
                if day in cal.weekday and \
                       cal.is_a_working_type(cal.weekday[day]):
                    type = cal.weekday[day]
                    id_t = cal.get_type_id(type)[0]
                    cal_ref_id = cal.get_type_id(type)[1]
                    return self.get_node_by_id(cal_ref_id).type_working_days[id_t][1]
                cal = cal.parent
        return None

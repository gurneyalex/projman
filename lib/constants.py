#Copyright (c) 2000-2004 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""Projman - (c)2004 Logilab - All rights reserved."""

__revision__ = "$Id: constants.py,v 1.3 2005-06-29 23:31:21 nico Exp $"

# needed for calculation with floats
FLOAT_ZERO = 0.000001
HOURS_PER_DAY = 8.
# task constraints
BEGIN_AFTER_END = 'begin-after-end'
BEGIN_AFTER_BEGIN = 'begin-after-begin'
END_AFTER_END = 'end-after-end'
END_AFTER_BEGIN = 'end-after-begin'
TASK_CONSTRAINTS = [BEGIN_AFTER_END, BEGIN_AFTER_BEGIN,
                    END_AFTER_END, END_AFTER_BEGIN]

# date constraints
BEGIN_AFTER_DATE = 'begin-after-date'
BEGIN_AT_DATE = 'begin-at-date'
BEGIN_BEFORE_DATE = 'begin-before-date'
END_AFTER_DATE = 'end-after-date'
END_AT_DATE = 'end-at-date'
END_BEFORE_DATE = 'end-before-date'
AT_DATE = 'at-date'
DATE_CONSTRAINTS = [BEGIN_AFTER_DATE, BEGIN_AT_DATE, BEGIN_BEFORE_DATE,
                    END_AFTER_DATE, END_AT_DATE, END_BEFORE_DATE]

__all__ = ['FLOAT_ZERO', 'BEGIN_AFTER_END', 'BEGIN_AFTER_BEGIN',
           'END_AFTER_END', 'END_AFTER_BEGIN', 'TASK_CONSTRAINTS',
           'BEGIN_AFTER_DATE', 'BEGIN_AT_DATE', 'BEGIN_BEFORE_DATE',
           'END_AFTER_DATE', 'END_AT_DATE', 'END_BEFORE_DATE',
           'DATE_CONSTRAINTS', ]


try:
    from projman.scheduling.gcsp import load_types
    TASK_SHARED = load_types.TASK_SHARED
    TASK_ONEOF = load_types.TASK_ONEOF
    TASK_SAMEFORALL = load_types.TASK_SAMEFORALL
    TASK_SPREAD = load_types.TASK_SPREAD
    TASK_MILESTONE = load_types.TASK_MILESTONE
except ImportError:
    TASK_SHARED = 0
    TASK_ONEOF = 1
    TASK_SAMEFORALL = 2
    TASK_SPREAD = 3
    TASK_MILESTONE = 4
    # for now just stop since we don't handle task types out of gcsp
    #raise

LOAD_TYPE_MAP = {
    "shared" : TASK_SHARED,
    "oneof" : TASK_ONEOF,
    "sameforall" : TASK_SAMEFORALL,
    "spread" : TASK_SPREAD,
    "milestone" : TASK_MILESTONE,
}
REVERSE_LOAD_TYPE_MAP = {}
for k,v in LOAD_TYPE_MAP.items():
    REVERSE_LOAD_TYPE_MAP[v] = k

# Copyright (c) 2004-2007 LOGILAB S.A. (Paris, FRANCE).
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
projman is a python package to schedule and transform xml project file to
gantt diagram, resource diagrams, etc.
"""

__revision__ = "$Id: __init__.py,v 1.12 2005-11-10 11:34:18 arthur Exp $"

import math

ENCODING = "ISO-8859-1"
LOG_CONF = "logging.conf"

DAY_WEEK = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

# In order to format monetary numbers, we could think of standard
# package locale, but it does not include spaces when using fr_FR.
#
#  >>> import locale
#  >>> locale.setlocale(locale.LC_ALL, '')
#  fr_FR
#  >>> locale.format("%.2f", 121212.01, grouping=True)
#  121212,01
def format_monetary(str_number, nb_decimal=2, space_gap=3):
    """takes a string or number and return it formatted in a monetary way. 
    ex: 121212.01 as u'121 212,01'

    nb_decimal sets the number of decimal to display space_gap sets
    
    the gap (ie, number of numbers) between two of the spaces. It is 3
    in the previous example.
    
    raises a TypeError in case of bad format
    """
    # FIXME REFACTOR to
    # fmt = reversed(str(intval))
    # final = []
    # while fmt:
    #     final.append(fmt[:space_gap])
    #     fmt = fmt[space_gap:]
    # output = '\xA0'.join(reversed(final))
    # 
    # FIXME: decide whether or not we should call round here
    fractval, intval = math.modf(float(str_number))
    intval = int(intval)
    if nb_decimal > 0:
        fract_part = round(fractval * 100)
        if fract_part == 100:
            intval += 1
            fract_part = 0
    parts = []
    div = 10**space_gap
    if space_gap: # space_gap = 0 would mean div=1, and infinite loop
        # Build the int part's chunks
        while intval >= div:
            intval, mod = divmod(intval, div)
            parts.insert(0, '%%0%dd' % space_gap % mod)
    parts.insert(0, str(intval))
    int_part = u'\xA0'.join(parts)
    if nb_decimal:
        fmt = '%%s,%%0%dd' % nb_decimal
        return fmt % (int_part, fract_part)
    return int_part

   

def extract_extension(name):
    """returns a couple (file_name, ext) from file_name.ext"""
    # XXX is this different from os.path.basename ??
    splitted = name.split('.', 1)
    if len(splitted) == 2:
        return tuple(splitted)
    else:
        return (name, '')

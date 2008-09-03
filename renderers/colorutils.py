# Copyright (c) 2000-2008 LOGILAB S.A. (Paris, FRANCE).
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
Utility functions and constants for managing colors.
"""

COLORS = {
    'aqua':         (0x00, 0xFF, 0xFF),
    'black':        0,    
    'blue':         (0x00, 0x00, 0xFF),
    'blueviolet':   (0x8A, 0x2B, 0xE2),
    'brown':        (0xA5, 0x2A, 0x2A),
    'cadetblue':    (0x5F, 0x9E, 0xA0),
    'chartreuse':   (0x7F, 0xFF, 0x00),
    'cornsilk':     (0xFF, 0xF8, 0xDC),
    'darkblue':     (0x00, 0x00, 0x8B),
    'darkgoldenrod':(0xB8, 0x86, 0x0B),
    'darkgray':     (0xA9, 0xA9, 0xA9),
    'darkgreen':    (0x00, 0x64, 0x00),
    'darkmagenta':  (0x8B, 0x00, 0x8B),
    'darkorange':   (0xFF, 0x8C, 0x00),
    'darkseagreen': (0x8F, 0xBC, 0x8F),
    'fuchsia':      (0xFF, 0x00, 0xFF),
    'green':        (0x00, 0x80, 0x00),
    'greenyellow':  (0xAD, 0xFF, 0x2F),
    'indigo':       (0x4B, 0x00, 0x82),
    'lightpink':    (0xFF, 0xB6, 0xC1),
    'lightgrey':    (0xD3, 0xD3, 0xD3),
    'limegreen':    (0x00, 0xFF, 0x00),
    'magenta':      (0xFF, 0x00, 0xFF),
    'mediumorchid': (0xBA, 0x55, 0xD3),
    'olive':        (0x80, 0x80, 0x00),
    'orange':       (0xFF, 0xA5, 0x00),
    'purple' :      (0x80, 0x00, 0x80),
    'red':          (0xFF, 0x00, 0x00),
    'salmon':       (0xFA, 0x80, 0x72),
    'teal' :        (0x00, 0x80, 0x80),
    'violet':       (0xEE, 0x82, 0xEE),
    'wheat':        (0xF5, 0xDE, 0xB3),
    'white':        (0xFF, 0xFF, 0xFF),
    'yellow':       (0xFF, 0xFF, 0x00),
    }

def delta_color(color, x):
    """ increment or decrements color by x """
    if color == 0:
        color = (0, 0, 0)
    if color[0] == '#':
        return (eval('0x%s'% color[1:3])+x,
                eval('0x%s'% color[3:5])+x,
                eval('0x%s'% color[5:7])+x)
    if len(color) == 3 and isinstance(color[0],int):
        one, two, three = color
        return (one+x, two+x, three+x)
    one, two, three = COLORS[color]
    return (one+x, two+x, three+x)


def rgb(color):
    """ return a triplet representing a RGB color """
    if color[0] == '#':
        return (eval('0x%s'%color[1:3]),
                eval('0x%s'%color[3:5]),
                eval('0x%s'%color[5:7]))
    return COLORS[color]

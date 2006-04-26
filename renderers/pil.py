# Copyright (c) 2000-2003 LOGILAB S.A. (Paris, FRANCE).
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
a PIL handler for the Renderer
"""

import os
from os.path import exists
from cStringIO import StringIO
from PIL import Image, ImageDraw, ImageFont
import projman

__revision__ = "$ld $"

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
    if len(color) == 3 and type(color[0]) == type(0):
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

DEFAULT_FONT_DIRS = ('/usr/share/projman', \
                    os.path.join(projman.__path__[0], "fonts"))
try:
    FONT_DIR = projman.fonts_dir
except:
    for font_dir in DEFAULT_FONT_DIRS:
        if exists(font_dir):
            FONT_DIR = font_dir
            break
    else:
        FONT_DIR = None
    
FORMATS = ("ARG", "BMP", "CUR", "DCX", "EPS", "FLI", "FPX", "GBR", 
           "GIF", "ICO", "IM", "IPTC", "JPEG", "MIC", "MPEG", "MSP",
           "PCD", "PCX", "PDF", "PNG", "PPM", "PSD", "SGI", "SUN", 
           "TGA", "TIFF", "WMF", "XBM", "XPM")

def load_font(weight='', style=''):
    """ load font with the given weight and style """
    if style:
        style = ' %s' % style.capitalize()
    if weight:
        weight = ' %s' % weight.capitalize()
    font_name = 'Arial%s%s_12_72.pil' % (weight, style)
    #font_name = 'Courier Regular%s%s_12_72.pil' % (weight, style)
    #font_name = 'Times New Roman%s%s_12_72.pil' % (weight, style)
    #import sys
    #print >>sys.stderr, FONT_DIR, font_name
    return ImageFont.load(os.path.join(FONT_DIR, font_name))

class PILHandler:
    """ handler for the Python Imaging Library """
    
    def __init__(self, format):
        format = format.upper()
        assert format in FORMATS, 'Unknown format %s' % format
        self._format = format
        
    def init_drawing(self, width, height):
        """ initialize a new picture """
        #print 'diagram pixel size', width, height
        self._im = Image.new('RGB', (width, height), 0xFFFFFF)
        self._d = ImageDraw.Draw(self._im)
        self._default_font = load_font()
        
    def close_drawing(self, cropbox=None):
        """ close the current picture """
        if cropbox:
            self._im = self._im.crop(cropbox)
        # print 'diagram pixel size', width, height
    
    def get_result(self):
        """ return the current picture """
        print 'Deprecated'
        _buffer = StringIO()
        self._im.save(_buffer, self._format)
        return _buffer.getvalue()
        
    def save_result(self, stream):
        """ return the current picture """
        self._im.save(stream, self._format)

    def draw_text(self, x, y, text, **args):
        """ draw a text """
        if not args.has_key('color'):
            args['color'] = 'black'
        attrs = self._get_attrs(args)
        self._d.text((x, y-12), text.encode(projman.ENCODING), \
                     font=self._font, **attrs)
        
    def draw_line(self, x1, y1, x2, y2, **args):
        """ draw a line """
        attrs = self._get_attrs(args)
        self._d.line((x1, y1, x2, y2), **attrs)#fill=128)
        
    def draw_rect(self, x, y, width, height, **args):
        """ draw a rectangle """
        attrs = self._get_attrs(args)
        self._d.rectangle((x, y, x+width, y+height), **attrs)
        
    def draw_poly(self, point_list, **args):
        """ draw a polygon """
        attrs = self._get_attrs(args)
        self._d.polygon(point_list, **attrs)
        
    def _get_attrs(self, args):
        """ convert standard styles arguments to PIL attributes"""
        attrs = {}
        style, weight = '', ''
        for arg, value in args.items():
            if arg == 'style':
                style = value
            elif arg == 'weight':
                weight = value
            elif arg == 'fillcolor':
                attrs['fill'] = rgb(value)
            elif arg == 'color':
                attrs['fill'] = rgb(value)
            elif arg == 'delta_color':
                attrs['fill'] = delta_color(attrs['fill'], int(value))
            else:
                raise Exception('Unkwnown arguments %s'%arg)
            if style or weight:
                self._font = load_font(weight, style)
            else:
                self._font = self._default_font
        return attrs

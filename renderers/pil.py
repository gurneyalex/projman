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
a PIL handler for the Renderer
"""

import os
from os.path import exists
from cStringIO import StringIO
from PIL import Image, ImageDraw, ImageFont
import projman
from colorutils import delta_color

DEFAULT_FONT_DIRS = ('/usr/share/projman',
                     os.path.join(projman.__path__[0],
                                  "fonts"))

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
        
    def draw_poly(self, point_list, close=True, **args):
        """ draw a polygon """
        attrs = self._get_attrs(args)
        if close:
            point_list = list(point_list) + [point_list[0]]
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

    def get_output(self, fname):
        return open(fname, "w")

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
##
# SVG backend using pycairo
#
"""Projman - (c) 2004-2008 Logilab - All rights reserved."""

from math import sqrt
import cairo
import codecs
from cStringIO import StringIO

from colorutils import COLORS, delta_color as _delta_color

def _color(icol):
    """Convert (r,g,b) with range 0..255 to
    rgb range 0..1"""
    if icol in COLORS:
        icol = COLORS[icol]
    if isinstance(icol, (int,float)):
        icol = (icol,icol,icol)
    if len(icol) == 3:
        icol = icol + (255,)
    return tuple([c/255. for c in icol])

class SVGHandler:
    _linewidth = 0.5
    _weights = {"bold": cairo.FONT_WEIGHT_BOLD}
    _slants = {"italic": cairo.FONT_SLANT_ITALIC,
               "oblique": cairo.FONT_SLANT_OBLIQUE}
    _size = 8
    
    def __init__(self, format):
        pass

    def init_drawing(self, width, height):
        """ initialize a new picture """
        self._buffer = StringIO()
        self._surf = cairo.SVGSurface(self._buffer, width, height)
        self._ctx = cairo.Context(self._surf)
        self._ctx.set_line_width(self._linewidth)
        self._ctx.set_font_size(self._size)
        self.width = width
        self.height = height

    def close_drawing(self, cropbox=None):
        """ close the current picture """
        pass

    def get_result(self):
        """ return the current picture as a str buffer """
        self._surf.finish()
        return self._buffer.getvalue()
    
    def save_result(self, stream):
        """ write the current picture in stream (file-like object) """
        stream.write(self.get_result())

    def _set_style(self, x, y, **args):
        #print "new path",x,y,args
        self._ctx.save()
        self._ctx.new_path()
        self._ctx.move_to(x, y)
        if 'color' in args:
            self._ctx.set_source_rgba(*_color(args['color']))
        if 'delta_color' in args:
            self._ctx.set_source_rgba(*delta_color(args['color'], int(args['delta_color'])))
        if 'linewidth' in args:
            self._ctx.set_line_width(args['linewidth'])
        if 'fillcolor' in args:
            pattern = cairo.SolidPattern(*_color(args['fillcolor']))
            self._ctx.set_source(pattern)
        if 'weight' in args or 'style' in args:
            w = self._weights.get(args.get('weight'), cairo.FONT_WEIGHT_NORMAL)
            s = self._slants.get(args.get('style'), cairo.FONT_SLANT_NORMAL)
            face = self._ctx.select_font_face("sans-serif", s, w)
        if 'size' in args:
            self._ctx.set_font_size(args['size'])
            
    def open_link(self, url):
        # FIXME
        pass
    
    def draw_text(self, x, y, text, **args):
        """ draw a text """
        #print "draw_text", x, y, text, args
        self._set_style(x, y, **args)
        self._ctx.text_path(text)
        if args.get('border'):
            self._ctx.stroke()
        else:
            self._ctx.fill()
        self._ctx.restore()
        
    def draw_line(self, x1, y1, x2, y2, **args):
        """ draw a line """
        self._set_style(x1, y1, **args)
        self._ctx.line_to(x2, y2)
        self._ctx.stroke()
        self._ctx.restore()
        
    def draw_dot(self, x1, y1, x2, y2, n, **args):
        """ draw a dot line """
        self._set_style(x1, y1, **args)
        self._ctx.set_dash([self._linewidth, 2*self._linewidth])
        self._ctx.line_to(x2, y2)
        self._ctx.stroke()
        self._ctx.restore()

    def draw_rect(self, x, y, width, height, **args):
        """ draw a rectangle """
        #print "draw_rectangle", x, y, width, height, args
        self._set_style(x, y, **args)
        self._ctx.rectangle(x, y, width, height)
        self._ctx.fill()
        self._ctx.restore()

    def draw_poly(self, point_list, close=True, **args):
        """ draw a polygon """
        #print "draw_poly", point_list, args
        if len(point_list)>1:
            x, y = point_list[0]
            points = point_list[1:]
            self._set_style(x, y, **args)
            for x, y in points:
                self._ctx.line_to(x, y)
            if close:
                self._ctx.close_path()
                self._ctx.fill()
            self._ctx.stroke()
            self._ctx.restore()

    def get_output(self, fname):
        return  codecs.open(fname, "w", "utf-8")

    def _text_width(self, s):
        return self._ctx.text_extents(s)[2]


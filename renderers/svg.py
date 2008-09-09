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
# SVG backend using matplotlib
# DEPRECATED
#
from math import sqrt
from matplotlib.backends.backend_svg import RendererSVG
from matplotlib.font_manager import FontProperties
import codecs
from StringIO import StringIO
from xml.sax.saxutils import escape

# matplotlib bugfix
from matplotlib import rcParams
for fam in ('serif', 'sans-serif', 'monospace', 'cursive', 'fantasy'):
    param = rcParams['font.'+fam]
    if isinstance(param,str):
        rcParams['font.'+fam] = param.split(', ')

# More matplotlib hacking : monkey patch draw_text so it uses a correct font spec
from matplotlib.backends.backend_svg import rgb2hex
def draw_text(self, gc, x, y, s, prop, angle, ismath):
    if ismath:
        self._draw_mathtext(gc, x, y, s, prop, angle)
        return

    #thetext = '%s' % s
    thetext = escape(s)
    fontfamily=prop.get_family()[0]
    fontstyle=prop.get_style()
    fontsize = prop.get_size_in_points()
    fontweight = prop.get_weight()
    color = rgb2hex(gc.get_rgb())

    style = 'font-size: %f; font-family: %s; font-style: %s; font-weight: %s; fill: %s;'%(fontsize, fontfamily,fontstyle,
                                                                                          fontweight, color)
    if angle!=0:
        transform = 'transform="translate(%f,%f) rotate(%1.1f) translate(%f,%f)"' % (x,y,-angle,-x,-y) # Inkscape doesn't support rotate(angle x y)
    else: transform = ''

    svg = """\
<text style="%(style)s" x="%(x)f" y="%(y)f" %(transform)s>%(thetext)s</text>
""" % locals()
    self._svgwriter.write (svg)

RendererSVG.draw_text = draw_text



def test():
    svgwriter = codecs.open( "test.svg", "w", "utf-8")
    renderer = RendererSVG( 800, 600, svgwriter, "test" )
    gc = renderer.new_gc()
    gc.set_linewidth(4)
    renderer.draw_line(gc, 0,0,800,600)
    renderer.draw_line(gc, 0,600,800,0)
    renderer.finish()
    svgwriter.close()

from colorutils import COLORS, delta_color as _delta_color

def _color( icol ):
    """Convert (r,g,b) with range 0..255 to
    rgb range 0..1"""
    if icol in COLORS:
        icol = COLORS[icol]
    if isinstance(icol, (int,float)):
        icol = (icol,icol,icol)
    return tuple([ c/255. for c in icol])

class SVGHandler:
    def __init__(self, format):
        pass

    def get_gc( self,
                color=None,
                fillcolor=(0,0,0),
                delta_color=None,
                **args ):
        gc = self._rend.new_gc()
        col = color or fillcolor
        if not col and delta_color:
            col = _delta_color(delta_color, int(value)) # FIXME value ??
        gc.set_foreground( _color( col ) )
        return gc

    def get_prop(self,
                 style=None,
                 weight=None,
                 **args ):
        prop = FontProperties()
        prop.set_family('sans-serif')
        prop.set_size(10)
        if style:
            prop.set_style(style)
        if weight:
            prop.set_weight(weight)
        return prop

    def init_drawing(self, width, height):
        """ initialize a new picture """
        self._buffer = StringIO()
        self._rend = RendererSVG( width, height, self._buffer, "projman" )
        self.height=height

    def close_drawing(self, cropbox=None):
        """ close the current picture """
        pass

    def get_result(self):
        """ return the current picture """
        self._rend.finish()
        return self._buffer.getvalue()

    def save_result(self, stream):
        """ return the current picture """
        self._rend.finish()
        data = self._buffer.getvalue()
        stream.write( data )

    def open_link(self,url):
        """draw a link to an url"""
        self._rend._svgwriter.write('<a xlink:href=\"%s\"> ' %url)

    def close_link(self):
        self._rend._svgwriter.write('</a>')

    def draw_text(self, x, y, text, **args):
        """ draw a text """
        #print "draw_text", x, y, repr(text), args
        n=len(text)
        text=text.lstrip()
        gc = self.get_gc( **args )
        prop = self.get_prop( **args )
        if n!=len(text): # spaces are not printed so we shift left n*size(i)
            try:
                w,h,_ = self._rend.get_text_width_height_descent("i", prop, False)
            except AttributeError: # compatibility with matplotlib 0.90
                w,h = self._rend.get_text_width_height("i", prop, False)
            x+= w*(n-len(text))
        self._rend.draw_text( gc, x, y,
                              text, prop,
                              angle=0, ismath=False)
        
    def draw_line(self, x1, y1, x2, y2, **args):
        """ draw a line """
        y1 = self.height-y1
        y2 = self.height-y2
        gc = self.get_gc( **args )
        gc._linewidth /= 2.
        self._rend.draw_line(gc, x1, y1, x2, y2)

    def draw_dot(self, x1, y1, x2, y2, n, **args):
        """ draw a dot line """
        dist = sqrt((x1-x2)**2 + (y1-y2)**2)
        length = dist / n
        dx = (x1 - x2)/length
        dy = (y1 - y2)/length
        gc = self.get_gc( **args )
        gc._linewidth /= 3.
        count=0
        while dist >= 0.00001:
            x1 -= 2*dx
            y1 -= 2*dy
            dist = sqrt((x1-x2)**2 + (y1-y2)**2)
            self.draw_line(x1, y1, x1+dx, y1+dy, **args)
            count+=1
            if count>1000:
                break

    def draw_rect(self, x, y, width, height, **args):
        """ draw a rectangle """
        #print "draw_rectangle", x, y, width, height, args
        y = self.height-y-height
        gc = self.get_gc( **args )
        rgbFace = _color( args['fillcolor'] )
        self._rend.draw_rect(gc, rgbFace, x, y, width, height)

    def draw_poly(self, point_list, **args):
        """ draw a polygon """
        #print "draw_poly", point_list, args
        gc = self.get_gc( **args )
        rgbFace = gc.get_rgb()
        h=self.height
        points = [ (x, h-y) for x,y in point_list ]
        self._rend.draw_polygon(gc, rgbFace, points)

    def get_output(self, fname):
        return  codecs.open(fname, "w", "utf-8")

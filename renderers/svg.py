##
# mini demo utilisation matplotlib pour du svg:
#

from matplotlib.backends.backend_svg import RendererSVG
from matplotlib.backends.backend_svg import RendererSVG
from matplotlib.font_manager import FontProperties
import codecs
from StringIO import StringIO

def test():
    svgwriter = codecs.open( "test.svg", "w", "utf-8")
    renderer = RendererSVG( 800, 600, svgwriter, "test" )
    gc = renderer.new_gc()
    gc.set_linewidth(4)
    renderer.draw_line(gc, 0,0,800,600)
    renderer.draw_line(gc, 0,600,800,0)
    renderer.finish()
    svgwriter.close()

from pil import COLORS, delta_color as _delta_color

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
                style=None,
                fillcolor=(0,0,0),
                weight=None,
                delta_color=None,
                **args ):
        gc = self._rend.new_gc()
        col = color or fillcolor
        if not col and delta_color:
            col = _delta_color(delta_color, int(value))
        gc.set_foreground( _color( col ) )
        #gc.set_background( _color( fillcolor ) )
        if delta_color is not None:
            raise NotImplementedError("Don't know what to do with that")
        prop = FontProperties()
        if style or weight:
            print "Font style", style, weight
        return gc, prop

    def init_drawing(self, width, height):
        """ initialize a new picture """
        print 'diagram pixel size', width, height
        height=432
        width=820
        self._buffer = StringIO()
        self._rend = RendererSVG( width, height, self._buffer, "projman" )
        self._gc = self._rend.new_gc()
        self.font_prop = FontProperties()
        self.height=height
#        self._default_font = load_font()

    def close_drawing(self, cropbox=None):
        """ close the current picture """
        print "CLOSE", cropbox

    def get_result(self):
        """ return the current picture """
        self._rend.finish()
        return self._buffer.getvalue()

    def save_result(self, stream):
        """ return the current picture """
        self._rend.finish()
        data = self._buffer.getvalue()
        stream.write( data )

    def draw_text(self, x, y, text, **args):
        """ draw a text """
        print "draw_text", x, y, repr(text), args
        gc, prop = self.get_gc( **args )
        font_height = 20
        self._rend.draw_text( gc, x, y-font_height,
                              text, prop,
                              angle=0, ismath=False)

    def draw_line(self, x1, y1, x2, y2, **args):
        """ draw a line """
        print "draw_line", x1, y1, x2, y2, args
        y1 = self.height-y1
        y2 = self.height-y2
        gc, prop = self.get_gc( **args )
        self._rend.draw_line(gc, x1, y1, x2, y2)

    def draw_rect(self, x, y, width, height, **args):
        """ draw a rectangle """
        #print "draw_rectangle", x, y, width, height, args
        y = self.height-y
        gc, prop = self.get_gc( **args )
        rgbFace = _color( args['fillcolor'] )
        self._rend.draw_rectangle(gc, rgbFace, x, y, width, height)

    def draw_poly(self, point_list, **args):
        """ draw a polygon """
        print "draw_poly", point_list, args
        gc, prop = self.get_gc( **args )
        rgbFace = gc.get_rgb()
        h=self.height
        points = [ (x, h-y) for x,y in point_list ]
        self._rend.draw_polygon(gc, rgbFace, points)

    def get_output(self, fname):
        return  codecs.open(fname, "w", "utf-8")

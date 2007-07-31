##
# mini demo utilisation matplotlib pour du svg:
#

from matplotlib.backends.backend_svg import RendererSVG
import codecs
svgwriter = codecs.open( "test.svg", "w", "utf-8")
renderer = RendererSVG( 800, 600, svgwriter, "test" )
gc = renderer.new_gc()
gc.set_linewidth(4)
renderer.draw_line(gc, 0,0,800,600)
renderer.draw_line(gc, 0,600,800,0)
renderer.finish()
svgwriter.close()

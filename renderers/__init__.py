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
external access point to projman base classes
"""

from abstract import AbstractRenderer, AbstractDrawer
from gantt import GanttRenderer
from resource import ResourcesRenderer
from ganttresource import GanttResourcesRenderer

# load backends
from pil import PILHandler, FORMATS as PIL_FORMATS
#from svg import SVGHandler
from svg_cairo import SVGHandler

def HandlerFactory(format):
    format = format.upper()
    if format in PIL_FORMATS:
        return PILHandler(format)
    if format == 'SVG':
        return SVGHandler(format)
    raise NotImplementedError("Format '%s' not supported" % format )

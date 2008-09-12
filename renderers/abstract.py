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
""" Abstract classes for Abstract classes for rendering """

from mx.DateTime import now, today, oneDay
from projman import ENCODING
from projman.lib import date_range

TITLE_COLUMN_WIDTH  = 220
FIELD_COLUMN_WIDTH  = 40
TIME_COLUMN_WIDTH   = 40.
LEGEND_COLUMN_WIDTH = 80
ROW_HEIGHT          = 20

TODAY = today()

DEFAULT_COLORS = {
    'HEAD'       : 'lightgrey',
    'CONSTRAINT' : 'black',
    # for odd row
    'ODD_SET' : {'TITLE'  : 'wheat',
                 'FIELD'  : 'darkseagreen',
                 'WEEKDAY': 'wheat',
                 'WEEKEND': 'cornsilk',
                 'TODAY'  : 'salmon',
                 'RESOURCE_USED' : 'darkblue',
                 'RESOURCE_UNAVAILABLE' : 'cornsilk',
                 },
    # for even row
    'EVEN_SET' : {'TITLE'  : 'cornsilk',
                  'FIELD'  : 'teal',
                  'WEEKDAY': 'cornsilk',
                  'WEEKEND': 'wheat',
                  'TODAY'  : 'salmon',
                  'RESOURCE_USED' : 'darkblue',
                  'RESOURCE_UNAVAILABLE' : 'wheat',
                    },
    # task background according to its status
    'TASK_SET' : { 'todo'   : 'orange',   #'#7485f6',
                   'current': 'darkblue', #'#ffa703',
                  'done'   : 'darkgray', #'#818181',
                   'problem': 'red'       #'#ff0a4f',
                   }
    }

# FIXME use those colors in HTML renderer without css
def load_colors(path=None):
    """
    load the colors configuration from the given path
    if path is None, try to get the path from the PROJMAN_COLORS_FILE
    environment variable or from the ~/.projmanrc file
    """
    from os.path import expanduser, exists, join
    colors = DEFAULT_COLORS
    if path is None:
        from os import environ
        path = environ.get('PROJMAN_COLORS_FILE', None)
    if path is None:
        path = expanduser(join('~', '.projmanrc'))
    if exists(path):
        load_colors_from_stream(open(path), colors)
    return colors

def load_colors_from_stream(stream, colors=DEFAULT_COLORS):
    """
    load the colors configuration from a stream add set matching value in the
    <colors> dictionary
    """
    for line_num, line in enumerate(stream.readlines()):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        label, color = line.split('=')
        label, color = label.strip(), color.strip()
        if label[:4] == 'ODD_':
            colors_dict = colors['ODD_SET']
            key = label[4:]
        elif label[:5] == 'EVEN_':
            colors_dict = colors['EVEN_SET']
            key = label[5:]
        elif label[:5] == 'TASK_':
            colors_dict = colors['TASK_SET']
            key = label[5:].lower()
        else:
            colors_dict = colors
            key = label
        if not colors_dict.has_key(key):
            raise Exception('Unknown color identifier "%s" \
            in colors file line %s' % (label, line_num))
        colors_dict[key] = color
    return colors


class AbstractRenderer :
    """
    Implements methods common to all renderers.
    
    generates events according to the given options
    concrete renderer must implements corresponding hooks
    (see the IRender)
    """
    
    DEFAULT_OPTIONS = {'timestep' : 'day', 
                       'detail' : 2,
                       'depth' : 0,
                       'view_begin' : None,
                       'view_end' : None,
                       'showids' : False,
                       'rappel' : False
                       }
    
    def __init__(self, options) :
        """
        Initialise all fields and tools needed for rendering,
        BUT the Concrete Renderer still needs to define its drawer.
        """
        self.drawer = None
        self.options = options
        for k, v in self.DEFAULT_OPTIONS.items():
            if not hasattr( options, k ):
                setattr( options, k, v )

    def write(self, string) :
        """
        write a content part to the output buffer
        """
        self.output.write(string.encode(ENCODING))

    def render(self, project, stream) :
        """
        Method called to draw & return diagram. Must be overridden
        """
        self.output = stream
        self._render_init(project)
        self._render_body(project)
        self._render_end()
    
    def _render_init(self, project):
        """
        Method called in first place by render to set up display
        """
        # defines vars needed by _render_xxx
        self._pending_constraints = {}
        self._visible_tasks = {}
        self._i = 0 # row num
        # set borders
        begin, end = project.get_task_date_range(project.root_task)
        if self.options.view_begin:
            view_begin =  self.options.view_begin
        else:
            view_begin = begin
        if self.options.view_end:
            view_end = self.options.view_end
        else:
            view_end = end
        if not view_begin:
            view_begin = project.calculate_date_range()[0]
        if not view_end:
            view_end = project.calculate_date_range()[1]
        #open time line
        self.drawer.open_timeline(view_begin, view_end)
        #open table for display
        self.drawer.open_table(project)
            
    def _render_end(self):
        """
        Method called by render when it ends to finish display
        """
        # print table tail 
        self.drawer.open_line()
        self.drawer.main_title("Generated on %s" % (
            now().strftime("%Y/%m/%d %H:%M:%S")))
        self.drawer.draw_timeline()
        self.drawer.close_line()
        self.drawer.close_table()
        # print legend
        self.drawer.open_line()
        self.drawer.close_line()
        self.drawer.legend()
        # close
        self.drawer.close_drawing()

class AbstractDrawer :
    """
    Implements all hooks method called by the abstract renderer and do nothing
    """
    
    def __init__(self, options, handler, colors_file=None, colors_stream = None):
        """
        defines colors and initializes colors_set
        """
        # initialise colors
        self._colors = None
        if colors_stream is not None:
            self._colors = load_colors_from_stream(colors_stream)
        else:
            self._colors = load_colors(colors_file)
        self.set_color_set(0)
        # set last members
        self.options = options
        self._handler = handler
        self._timeline_days = []
        # ajust time step
        if self.options.timestep == 'day':
            self._timestep = 1
        if self.options.timestep == 'week':
            self._timestep = 7
        if self.options.timestep == 'month':
            self._timestep = 13   # maximum possible value
        # x and y coordinate for current element location
        self._x = 0
        self._y = 0        
        self._max_x = 0
        self._max_y = 0
        
    def set_color_set(self, parity):
        """
        Defines which color_set to use, EVEN or ODD form _colors
        """
        if parity % 2:
            self._color_set = self._colors['ODD_SET']
        else:
            self._color_set = self._colors['EVEN_SET']
    
    # low level methods ######################################################

    def _draw_text(self, text, **attrs):
        """
        draw a text with some alignement
        """
        self._handler.draw_text(self._x+3, self._y+ROW_HEIGHT-6, text, **attrs)
        
    def _draw_rect(self, width, height, **attrs):
        """
        draw a rectangle with some alignement
        """
        self._handler.draw_rect(self._x+1, self._y+1, width-2, height-2, **attrs)

    def open_link(self,url):
        self._handler.open_link(url)

    def close_link(self):
        self._handler.close_link()

    # generic events ##########################################################

    def close_drawing(self): 
        self._handler.close_drawing( (0,0,self._max_x,self._max_y) )

    def open_table(self, project):
        """
        open the table where the resources diagram will be located
        """
        # adjust width according to timestep
        self._daywidth = TIME_COLUMN_WIDTH // self._timestep
        self._timestepwidth = self._daywidth * self._timestep
        self._init_table()

        # estimate drawing width/height
        width, height = self._get_table_dimension(project)
        self._handler.init_drawing(width, height)

        # number of optional fields
        self._fields = 0
        
    def _init_table(self):
        """
        abstract method used for specific initialisation
        """
    
    def close_table(self): 
        """
        close the table where the diagram is located
        """
        # nothing to be done, close line does all the work

    def open_line(self):
        """
        open a new line in the table
        """
        # nothing to be done, close line does all the work
        
    def close_line(self):
        """close a table's line"""
        self._max_x = max(self._max_x, self._x)
        self._max_y = max(self._max_y, self._y)
        self._x = 0
        self._y += ROW_HEIGHT

    def draw_timeline(self):
        """
        Format time line according to time step
        """
        for day in list(date_range(self.view_begin, self.view_end)):
            # timestep == week
            if self._timestep == 7 and day.day_of_week == 0:
                date = str(day.iso_week[1])
                self._draw_text("s%s" %date)
            #timestep == month
            elif self._timestep == 13 and day.day == 1:
                date = str("%02d" %day.month)
                self._draw_text(date)
            # timestep == day
            elif self._timestep == 1:
                date = day.strftime('%m-%d')
                self._draw_text(date)
            if self._timestep == 30:
                step = float(day.days_in_month)
            else:
                step = float(self._timestep)
            self._x += self._timestepwidth / step
        
    def open_timeline(self, begin, end):
        """
        open a new time line in the table
        """
        self._timeline_days = list(date_range(begin, end, self._timestep))
        days = list(date_range(begin, end, oneDay))
        #days = [d for d in days if d.day_of_week-5 < 0]
        self._timeline_all_days = days
        self.view_begin = begin
        self.view_end = end

    def close_timeline(self):
        """
        close a table's time line
        """
        # nothing to be done
        
    # project table head/tail #################################################

    def main_title(self, title):
        """ write the main description column's title """
        self._draw_rect(TITLE_COLUMN_WIDTH,
                        ROW_HEIGHT, fillcolor=self._colors['HEAD'])
        self._draw_text(title, weight='bold')
        self._x += TITLE_COLUMN_WIDTH

    def simple_title(self, title, tail=False):
        """ write a simple description column's title """
        self._draw_rect(FIELD_COLUMN_WIDTH,
                        ROW_HEIGHT, fillcolor=self._colors['HEAD'])
        if not tail:
            self._fields += 1
            if title:
                self._draw_text(title, weight='bold')
        self._x += FIELD_COLUMN_WIDTH
        
    # standard table content ###################################################

    def simple_content(self, content):
        """ write a simple cell content  """
        self._draw_rect(FIELD_COLUMN_WIDTH, ROW_HEIGHT,
                        fillcolor=self._color_set['FIELD'])
        self._draw_text(content)
        self._x += FIELD_COLUMN_WIDTH

    def main_content(self, content, project=None,
                     depth=0, task=None):
        """ write a main cell's content """
        self._draw_rect(TITLE_COLUMN_WIDTH, ROW_HEIGHT,
                        fillcolor=self._color_set['TITLE'])
        if task is not None and task.TYPE != "milestone":
            try:
                status = project.get_task_status(task)
                color = self._colors['TASK_SET'][status]
            except KeyError, exc:
                print 'while drawing, ignoring', exc
                color = self._colors['TASK_SET']['problem']
            self._ctask = task
            self._color = color
        if depth:
            content = '%s%s'% ('  '*depth, content)
        self._draw_text(content, style='italic', weight='bold')
        self._x += TITLE_COLUMN_WIDTH

    def text_width(self, s):
        return self._handler._text_width(s)
    
    def _legend_task(self) :
        """ write the diagram's legend of tasks """
        self._draw_text('Tasks Legend', style='italic', weight='bold')
        self._x += FIELD_COLUMN_WIDTH*2 + 10
        for status, color in self._colors['TASK_SET'].items():
            self._draw_rect(FIELD_COLUMN_WIDTH+20,
                            ROW_HEIGHT,
                            fillcolor=color)
            width = self.text_width(status)
            x = self._x
            self._x += (FIELD_COLUMN_WIDTH+10 - width)/2
            self._draw_text(status, color=(100,100,100,120), weight='bold', linewidth=2, border=True)
            self._draw_text(status, color='white', weight='bold', border=False)
            self._x = x + FIELD_COLUMN_WIDTH+25



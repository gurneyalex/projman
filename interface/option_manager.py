# Copyright (c) 2000-2004 LOGILAB S.A. (Paris, FRANCE).
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
"""Projman - (c)2004 Logilab - All rights reserved."""

__revision__ ="$Id: option_manager.py,v 1.21 2005-09-09 07:47:11 alf Exp $"

# match each format with corresponding file extension
EXTENSIONS = {"docbook":"xml",
              "html":"html",
              "csv":"csv"}

DEFAULT_PROJMAN_EXPORT = 'projman_export.xml'
DEFAULT_PYGANTT_EXPORT = 'pygantt_export.xml'
DEFAULT_PLANNER_EXPORT = 'planner_export.xml'

import os, os.path
import mx.DateTime
from projman.__pkginfo__ import version
from projman.interface.file_manager import ProjectStorage
from projman.interface.command_manager import ConvertCommand, ScheduleCommand, \
     DiagramCommand, XmlCommand
from projman.interface import UsageRequested, MAIN_USAGE, CONVERT_USAGE, DIAGRAM_USAGE, \
     XML_DOC_USAGE, PLAN_USAGE, CONVERT_HEAD, PLAN_HEAD, DIAGRAM_HEAD, XML_HEAD


def create_option_manager(option_list, args):
    """seek right command through list of options and returns approriate
    OptionManager
    
    raises: KeyError if manager built with not valid options
    ValueError if mis-formatted parameter"""
    # options returned by getopt are couple (keys, value)
    # -> extract keys
    option_keys = [option[0] for option in option_list]
    # seek invoked command
    for option_state in (OptionManager, OptionConvert, OptionSchedule,
                         OptionDiagram, OptionXmlView):
        for command in option_state.COMMAND:
            if command in option_keys:
                OptionManager.option_set = option_state(option_list, args)
                return OptionManager.option_set
    # no commanf found, return generic manager
    OptionManager.option_set = OptionManager(option_list, args)
    return OptionManager.option_set
      
class OptionManager:
    """Default manager: no command found which any of implemented matches

    raises: KeyError if called with not valid options (_check_options)
            ValueError if mis-formatted parameter (_parse_options)"""

    option_set = None
    
    COMMAND = ('-V', '--version')
    OPTIONS = ('-H', '-h', '--help', "-t", "--interactive", "-X", "--expanded",
               "-p", "--project", "-r", "--resources", "-a", "--activity",
               "--verbose")
    USAGE = MAIN_USAGE
    HEAD = __doc__
    def __init__(self, option_list, argument_list):
        # set common values
        self.option_list = option_list
        self.interactive_mode = False
        self.archive_mode = True
        self.verbose = False
        # common options
        self._check_options()
        self._parse_options()
        # set members
        _repo_in, _input, output = self._parse_arguments(argument_list)
        self.storage = ProjectStorage(_repo_in, _input, output,
                                      archive_mode=self.is_archive_mode(),
                                      input_projman=self.is_input_projman())
        # parse options
        self._parse_file_options()

    def __str__(self):
        return "OptionManager"

    def _check_options(self):
        """checks that all given options are recognised by option manager

        raises KeyError if not"""
        # options returned by getopt are couple (keys, value)
        # -> extract keys
        option_keys = [option[0] for option in self.option_list]
        # check that all keys are valid
        for option in option_keys:
            if not option in self.OPTIONS + self.COMMAND:
                raise KeyError("%s unknown. Valid options are: %s"\
                               % (option, str(self.OPTIONS + self.COMMAND)))
        return True

    def _parse_arguments(self, arguments):
        """extract (input, output) from arguments"""
        # parse args
        if len(arguments) > 2:
            raise ValueError("too many arguments, see man pages or use '-h'")
        elif len(arguments) == 2:
            input_name = arguments[0]
            output_name = arguments[1]
        elif len(arguments) == 1:
            input_name = arguments[0]
            output_name = None
        else:
            raise UsageRequested(self.USAGE)
        # check validity
        if input_name != '-' and not os.path.exists(input_name):
            raise ValueError("Input %s does not exist"% input_name)
        # split repo & files
        repo_in, input_ = os.path.split(os.path.abspath(input_name))
        if output_name:
            output = os.path.abspath(output_name)
        else:
            output = None
        return repo_in, input_, output
                
    def _parse_options(self):
        """extract values from a list of options. Set up first set of
        options, which some among them are needed to create. Also
        responsible for setting output
        """
        # check all options
        for name, value in self.option_list:
            if name in ('-H', '-h', '--help') :
                raise UsageRequested(self.USAGE)
            elif name in ('-V', '--version'):
                raise UsageRequested("Projman v" + version)
            elif name in self.COMMAND:
                pass
            elif name in ("-t", "--interactive"):
                self.interactive_mode = True
            elif name in ("-X", "--expanded"):
                self.archive_mode = False
            elif name == "--verbose":
                self.verbose = True
            #else: if not valid, error raised by check_options
                
    def _parse_file_options(self):
        """extract values from a list of options. Set up first set of
        options, which some among them are needed to create. Also
        responsible for setting output
        """
        # check all options
        for name, value in self.option_list:
            if name in ('-p', '--project'):
                self.storage.plan_tasks(value)
            elif name in ('-r', '--resources'):
                self.storage.plan_resources(value)
            elif name in ('-a', '--activity'):
                self.storage.plan_activities(value)
            #else: if not valid, error raised by check_options

    # GETTERS
    def is_interactive_mode(self):
        """returns True if owerwrites output"""
        return self.interactive_mode

    def is_archive_mode(self):
        """returns True if using archive"""
        return self.archive_mode

    def is_input_projman(self):
        """returns True input is a projman file"""
        # reading projman by default. Method overriden in ConvertOption
        return True

    def is_verbose(self):
        """returns True input is a projman file"""
        return self.verbose
    
    def get_command(self):
        """delegated to appropriate child"""
        raise NotImplementedError(self.USAGE)
    
class OptionConvert(OptionManager):
    """gather all parameters/options corresponding to the conversion command.
    
    ex: projman -c -i pygantt -o projman input.xml output.xml
    """
    COMMAND = ("-c", "--convert")
    OPTIONS = OptionManager.OPTIONS \
              + ("-i", "--in-format", "-o", "--out-format")  
    USAGE = CONVERT_USAGE
    HEAD = CONVERT_HEAD
    def __init__(self, option_list, argument_list=None):
        self.input_format = 'projman'
        self.output_format = 'projman'
        OptionManager.__init__(self, option_list, argument_list)

    def __str__(self):
        return "OptionConvert (input=%s output=%s)"\
               % (self.input_format, self.output_format)

    def _parse_options(self):
        """extract values from options"""
        OptionManager._parse_options(self)
        # check all options
        for name, value in self.option_list:
            if name in ('-i', '--in-format'):
                if value not in ('planner', 'pygantt', 'projman'):
                    raise ValueError("unknown format: %s"% value)
                else:
                    self.input_format = value
            elif name in ('-o', '--out-format') :
                if value not in ('planner', 'pygantt', 'projman'):
                    raise ValueError("unknown format: %s"% value)
                else:
                    self.output_format = value
            #else: if not valid, error raised by check_options
                
    def _parse_file_options(self):
        """extract values from a list of options. Set up first set of
        options, which some among them are needed to create. Also
        responsible for setting output
        """
        # common options
        OptionManager._parse_file_options(self)
        # set up output
        if not self.storage.output:
            if self.is_writing_pygantt():
                self.storage.set_output(DEFAULT_PYGANTT_EXPORT)
            elif self.is_writing_planner():
                self.storage.set_output(DEFAULT_PLANNER_EXPORT)
            elif self.is_writing_projman():
                self.storage.set_output(DEFAULT_PROJMAN_EXPORT)
                self.storage.plan_projman(DEFAULT_PROJMAN_EXPORT)
                self.storage.plan_defaults()
            else:
                raise ValueError("corrupted format %s"% self.output_format)
        else:
            if self.is_writing_projman():
                self.storage.plan_projman(self.storage.output)
                self.storage.plan_defaults()

    # GETTERS
    def get_command(self):
        """Create command associated with this set of options"""
        return ConvertCommand(self)

    def is_input_projman(self):
        """returns True input is a projman file"""
        return self.is_reading_projman()
        
    def is_reading_pygantt(self):
        """returns True if format of the input is pygantt"""
        return self.input_format == 'pygantt'
    
    def is_reading_planner(self):
        """returns True if format of the input is planner"""
        return self.input_format == 'planner'
    
    def is_reading_projman(self):
        """returns True if format of the input is projman"""
        return self.input_format == 'projman'
    
    def is_writing_pygantt(self):
        """returns True if format of the output is pygantt"""
        return self.output_format == 'pygantt'
    
    def is_writing_planner(self):
        """returns True if format of the output is planner"""
        return self.output_format == 'planner'
    
    def is_writing_projman(self):
        """returns True if format of the output is projman"""
        return self.output_format == 'projman'
    
        
class OptionSchedule(OptionManager):
    """gather all parameters/options corresponding to the schedule command.
    
    ex:  projman -s -I projman.xml schedule.xml
    """
    COMMAND = ("-s", "--schedule", "--plan")
    OPTIONS = OptionManager.OPTIONS \
              + ("-I", "--include-references", "--type") 
    USAGE = PLAN_USAGE
    HEAD = PLAN_HEAD
    def __init__(self, option_list, argument_list=None):
        self.type = 'dumb'
        self.include_references = False
        OptionManager.__init__(self, option_list, argument_list)

    def __str__(self):
        return "OptionSchedule (type=%s include=%s)"\
               % (self.type, self.include_references)

    def _parse_options(self):
        """extract values from options"""
        OptionManager._parse_options(self)
        # check all options
        for name, value in self.option_list:
            if name in ('-I', '--include-references'):
                self.include_references = True
            elif name == '--type':
                if value in ('dumb', 'simple', 'csp'):
                   self.type = value
                else:
                    raise ValueError("unknown scheduler type: %s"% value)
                
    def _parse_file_options(self):
        """extract values from a list of options. Set up first set of
        options, which some among them are needed to create. Also
        responsible for setting output
        """
        OptionManager._parse_file_options(self)
        if self.storage.output:
            self.storage.plan_schedule(self.storage.output)
        else:
            self.storage.set_output(self.storage.get_schedule())

    # GETTERS
    def get_command(self):
        """Create command associated with this set of options"""
        return ScheduleCommand(self)
    
    def is_including_reference(self):
        """returns True if input file will be modified to include references
        to produced schedules"""
        return self.include_references
    
        
class OptionDiagram(OptionManager):
    """gather all parameters/options corresponding to the diagram command.
    
    ex: projman -d --diagram-type=gantt projman.xml image.png
    """
    COMMAND = ("-d", "--diagram")
    OPTIONS = OptionManager.OPTIONS \
              + ("--diagram-type", "--selected-resource", "--renderer",
                 "--depth", "--timestep", "--view-begin", "--view-end",
                 "-D", "--del-ended", "--del-empty") 
    USAGE = DIAGRAM_USAGE
    HEAD = DIAGRAM_HEAD
    def __init__(self, option_list, argument_list=None):
        self.delete_ended = False
        self.delete_empty = False
        self.diagram_type = 'gantt'
        self.render_ext = 'png'
        self.timestep = 1
        self.detail = 2
        self.depth = 0
        self.view_begin = None
        self.view_end = None
        self.showids = False
        self.rappel = False
        self.selected_resource = None
        self.colors_file = None
        OptionManager.__init__(self, option_list, argument_list)

    def __str__(self):
        return "OptionDiagram (type=%s render=%s step=%s detail=%s depth=%s)"\
               % (self.diagram_type, self.render_ext, self.timestep,
                  self.detail, self.depth)

    def _parse_options(self):
        """extract values from options.

        raises ValueError if one of the parameters is mis-formatted"""
        OptionManager._parse_options(self)
        # check all options
        for name, value in self.option_list:
            if name == '--diagram-type':
                self.diagram_type = value  
                if self.diagram_type not in ("gantt", "resources",
                                             "gantt-resources"):
                    raise ValueError("unknown type: %s"% self.diagram_type)
            elif name == '--renderer':
                if self.render_ext not in ('png', 'gif', 'jpeg', 'tiff', "html"):
                    raise ValueError("unknown renderer: %s"% self.render_ext)
                else:
                    self.render_ext = value
            elif name == '--selected-resource':
                self.selected_resource = value
            elif name == '--timestep':
                self.timestep = int(value)
            elif name == '--depth':
                self.depth = int(value)
            elif name == '--view-begin':
                try:
                    self.view_begin = mx.DateTime.strptime(value, "%Y/%m/%d")
                except mx.DateTime.Error :
                    raise ValueError(
                        "expected format of begin-date  is yyyy/mm/dd")
            elif name == '--view-end':
                try:
                    self.view_end = mx.DateTime.strptime(value, "%Y/%m/%d")
                except mx.DateTime.Error :
                    raise ValueError(
                        "expected format of end-date  is yyyy/mm/dd")
            elif name == "--del-ended":
                self.delete_ended = True
            elif name == "--del-empty":
                self.delete_empty = True
            elif name == "-D":
                self.delete_ended = True
                self.delete_empty = True
            #else: if not valid, error raised by check_options
                
    def _parse_file_options(self):
        """extract values from a list of options. Set up first set of
        options, which some among them are needed to create. Also
        responsible for setting output
        """
        OptionManager._parse_file_options(self)
        if not self.storage.output:
            self.storage.set_output(self.diagram_type \
                                          + '.' + self.render_ext)

    # GETTERS
    def get_render_options(self):
        """return dictionary readable by renderers & drawers"""
        return {'timestep' : self.get_timestep(),
                'detail' : self.get_detail(),
                'depth' : self.get_depth(),
                'view-begin' : self.get_begin_date(),
                'view-end' : self.get_end_date(),
                'showids' : self.get_showids(),
                'rappel' : self.get_rappel(),
                'selected-resource' : self.get_selected_resources()
                }
 
    def get_command(self):
        """Create command associated with this set of options"""
        return DiagramCommand(self)
    
    def is_gantt_type(self):
        """returns True if drawing a gantt diagram"""
        return self.diagram_type == "gantt"
    
    def is_resource_type(self):
        """returns True if drawing a resource diagram"""
        return self.diagram_type == "resources"
    
    def is_gantt_resource_type(self):
        """returns True if drawing a gantt-resource diagram"""
        return self.diagram_type == "gantt-resources"
    
    def is_image_renderer(self):
        """returns True if drawing a png diagram"""
        return self.render_ext in ('png', 'gif', 'jpeg', 'tiff')
    
    def is_html_renderer(self):
        """returns True if drawing a html diagram"""
        return self.render_ext == "html"

    def get_diagram_type(self):
        """returns extension of the image drawn"""
        return self.diagram_type

    def get_image_format(self):
        """returns extension of the image drawn"""
        return self.render_ext

    def get_selected_resources(self):
        """returns resources to take in account for resources diagrams"""
        return self.selected_resource

    def get_timestep(self):
        """returns timeline increment in days for diagram"""
        return self.timestep

    def get_depth(self):
        """returns the depth to visualisate for diagrams"""
        return self.depth

    def get_begin_date(self):
        """returns begin date for diagram view"""
        return self.view_begin

    def get_end_date(self):
        """returns end date for diagram view"""
        return self.view_end

    def get_detail(self):
        """returns the depth to visualisate for diagrams"""
        return self.detail

    def get_rappel(self):
        """returns begin date for diagram view"""
        return self.rappel

    def get_showids(self):
        """returns end date for diagram view"""
        return self.showids
    
class OptionXmlView(OptionManager):
    """gather all parameters/options corresponding to the xml-view command.
    
    ex: projman -x -v cost projman.xml view.xml
    """
    COMMAND = ("-x", "--xml-view", "--xml-doc")
    OPTIONS = OptionManager.OPTIONS \
              + ("-v", "--view", "-f", "--format", "--display-cost",
                 "--display-duration", "--display-rates") 
    USAGE = XML_DOC_USAGE
    HEAD = XML_HEAD
    def __init__(self, option_list, argument_list=None):
        self.xml_view = 'cost'
        self.xml_format = 'docbook'
        self.display_rates = False
        self.display_cost = False
        self.display_duration = False
        OptionManager.__init__(self, option_list, argument_list)

    def __str__(self):
        return "OptionXmlView (view=%s format=%s rates=%s costs=%s duration=%s)"\
               % (self.xml_view, self.xml_format, self.display_rates,
                  self.display_cost, self.display_duration)

    def _parse_options(self):
        """extract values from options"""
        OptionManager._parse_options(self)
        # check all options
        for name, value in self.option_list:
            if name in ('-v', '--view'):
                self.xml_view = value    
                if value not in ("list", "cost", "date"):
                    raise ValueError("unknown view: %s"% self.xml_view)
            elif name in ('-f', '--format'):
                self.xml_format = value    
                if self.xml_format not in ("docbook", "csv", "html"):
                    raise ValueError("unknown format: %s"% self.xml_format)
            elif name == '--display-rates':
                self.display_rates = True
            elif name == '--display-cost':
                self.display_cost = True
            elif name == '--display-duration':
                self.display_duration = True
            #else: if not valid, error raised by check_options
                
    def _parse_file_options(self):
        """extract values from a list of options. Set up first set of
        options, which some among them are needed to create. Also
        responsible for setting output
        """
        OptionManager._parse_file_options(self)
        if not self.storage.output:
            self.storage.set_output(self.xml_view + '.xml')

    # GETTERS
    def get_command(self):
        """Create command associated with this set of options"""
        return XmlCommand(self)
    
    def get_view(self):
        """returns name o fthe built view"""
        return self.xml_view
    
    def get_extension(self):
        """returns format (extension) o the built view"""
        return EXTENSIONS[self.xml_format]      
    
    def is_list_view(self):
        """returns True if building view listing all tasks"""
        return self.xml_view == "list"
    
    def is_cost_view(self):
        """returns True if building array listing all tasks
        with their load/cost"""
        return self.xml_view == "cost"
    
    def is_date_view(self):
        """returns True if building array listing all tasks
        with their duration"""
        return self.xml_view == "date"
    
    def is_displaying_rates(self):
        """return True if adding to xml view a report of all
        resources' rates"""
        return self.display_rates
    
    def is_displaying_cost(self):
        """return True if adding to xml view a section with
        global cost of project"""
        return self.display_cost
    
    def is_displaying_duration(self):
        """return True if adding to xml view a section with
        global duration of project"""
        return self.display_duration

    def is_html_format(self):
        """return True if writing wiew in html format"""
        return self.xml_format == "html"

    def is_csv_format(self):
        """return True if writing wiew in csv format"""
        return self.xml_format == "csv"

    def is_docbook_format(self):
        """return True if writing wiew in docbook format"""
        return self.xml_format == "docbook"

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
"""Projman - (c)2004 Logilab - All rights reserved."""

__revision__ = "$Id: __init__.py,v 1.9 2005-12-27 00:03:00 nico Exp $"

class UsageRequested(Exception):
    """Not really an exception, rather a way of requesting usage
    display and gracefull exit of the program"""
    pass

from projman import __pkginfo__

HEAD = "Projman %s - (c)2004 Logilab - All rights reserved." % __pkginfo__.version

LICENCE = """
This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

CONVERT_HEAD = """
  projman -c (--convert) [options] input_file [output_file]
    to convert files from one type to another
    ex: projman -c -i pygantt -o projman input.xml output.xml
"""

CONVERT = CONVERT_HEAD + """
  OPTIONS
  -------
  -i; --in-format
    specifies the format of the input.
    * planner
    * pygantt
    * [projman]

  -o; --out-format
    specifies the output format.
    * [projman]
    * planner
    * pygantt

  -p; --project
    specifies the dest file path for the description of the project

  -r; --resources
    specifies the dest file path for the description the resources

  -a; --activity
    specifies the dest file path for the description of the activities

   if --project, --resources and --activities options are omitted:
   projman generates activities_description.(i).xml,
   resources_description.(i).xml and project_description.(i).xml (i is
   the index of each element in projman object)
"""

CONVERT_USAGE = HEAD + LICENCE + CONVERT

DIAGRAM_HEAD = """
  projman -d (--diagram) [options] input_file [output_file]
    to generate diagrams (resources, gantt, etc.)
    ex: projman -d --diagram-type=resources projman.xml ress_diag.png
"""

DIAGRAM = DIAGRAM_HEAD + """
  OPTIONS
  -------
  --diagram-type
    specifies the type of diagram to generate
    * [gantt]
    * resources
    * gantt-resources (resources displayed as summary)

  --selected-resource
    specifies the id of the resource to take in account for resources diagrams
    [default=all resources]

  --renderer 
    specifies the output renderering for resources diagram 
    use only with schedule input
    * image: [png], gif, jpeg, tiff
    * html (bugs)

  --depth
    specifies the depth to visualisate for diagrams
    [default=0, this means all the tree]

  --timestep
    timeline increment in days for diagram
    [default=1]

  --view-begin
    begin date for diagram view (yyyy/mm/dd)
    [default=date begin project]

  --view-end
    end date for diagram view (yyyy/mm/dd)
    [default=date end project]

  --del-ended
    do not display in resource diagram tasks wich are completed,
    meaning that time of work on them equals theirs duration.

  --def-empty
    do not display in resource diagram tasks wich are not worked during
    given period

  -D
    add the effects of options --del-ended and --def-empty
"""

DIAGRAM_USAGE = HEAD + LICENCE + DIAGRAM

XML_HEAD = """
  projman -x (--xml-view, --xml-doc) [options] input_file [output_file]
    to generate xml views (list, cost, date)
    ex: projman -x -v list projman.xml listing_view.xml
"""

XML_DOC = XML_HEAD + """
  OPTIONS
  -------
  -v; --view
    Specify the type of view generated
    * [cost]: Table with task, load, resources, cost
    * list: List of all tasks
    * date: Table with task, begin date, end date, cost.

  -f; --format
    set output format.
    * [docbook]: respectful of format dockbook 4.2.
    * html: NOT IMPLEMENTED YET
    * csv: NOT IMPLEMENTED YET
     
  --display-cost
    Add global cost of project at the end of the view

  --display-duration
    Add global duration of project at the end of the view
    
  --display-rates
    Add daily rates for each resources working on project
"""

XML_DOC_USAGE = HEAD + LICENCE + XML_DOC

PLAN_HEAD = """
  projman -s (--schedule, --plan) [options] input_file [output_file]
    to schedule project
    ex:  projman -s -I projman.xml schedule.xml
"""

PLAN = PLAN_HEAD + """
  OPTIONS
  -------  
  -I; --include-references
    input file will be modified to include references to 
    produced schedules

  --type [dumb|simple|csp]
    chose scheduling method (defaults to dumb)
"""

PLAN_USAGE = HEAD + LICENCE + PLAN

MAIN_USAGE = HEAD + LICENCE + """
USAGES:""" + CONVERT_HEAD + PLAN_HEAD + DIAGRAM_HEAD + XML_HEAD + """
  projman -V (--version)
    display version of installed projman

  projman -h (-H, --help)
    to get more help

  Use option -t (--interactive) to preserve overwriting of output N/A
  Use option --verbose to display message during execution of projman
  Use option -X (--expanded) if you wish to use .xml file instead of
    a projman file (.prj)
"""

USAGE = HEAD + LICENCE + """
USAGE:
  projman can be used in four ways:
  * to convert types of files
  * to generate diagrams (resources diagram or gantt diagram)
  * to generate views (docbook, csv...)
  * to schedule project


convert files
=============

""" + CONVERT + """

generate diagrams
=================

""" + DIAGRAM + """

generate views
==============

""" + XML_DOC + """

schedule project
================

""" + PLAN

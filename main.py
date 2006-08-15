#!/usr/bin/python
# Copyright (c) 2000-2006 LOGILAB S.A. (Paris, FRANCE).
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

"""Projman - (c)2004-2006 Logilab - All rights reserved."""

import sys
import logging, logging.config
from logilab.common.optparser import OptionParser
from projman import LOG_CONF
from projman.interface.option_manager import create_option_manager, UsageRequested
  
# FIXME: use optparse instead of getopt
def run(args) :
    """Main function.
    """
    # create & init logger
    logger = logging.getLogger("main")
    try:
        logging.config.fileConfig(LOG_CONF)
    except Exception:
        logging.basicConfig()
    # parse command line
    import getopt
    l_opt = ['diagram-type=', 'in-format=', 'out-format=', 'project=', 
             'resources=', 'activity=', 'renderer=', 'type=',
             'timestep=', 'view-begin=', 'view-end=', 'selected-resource=', 
             'depth=', 'help', 'convert', 'schedule', 'plan', 'diagram',
             'include-references', 'xml-doc', 'xml-view', 'view=', 'format=',
             'display-rates', 'display-cost', 'display-duration', 'interactive',
             'expanded', "del-ended", "del-empty", "verbose", "version"]
    
    (opt, args) = getopt.getopt(args, 'i:o:p:r:a:g:Iv:f:cdsxVHhtXD', l_opt)
    logger.info("projman called with options %s"% str(opt))
    logger.debug("remaining args %s"% str(args))
    try:
        # creating option set
        options_set = create_option_manager(opt, args)
        if options_set.is_verbose():
            print "Launching projman with in verbose mode with options", \
                  str(options_set)
        # execute command
        options_set.get_command().execute()
    except UsageRequested, usage_exc:
        print usage_exc
        sys.exit(0)
    except (ValueError, NotImplementedError), error:
        import traceback
        traceback.print_exc()
        print 'ERROR:', error
        sys.exit(2)


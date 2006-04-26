# Copyright (c) 2000-2005 LOGILAB S.A. (Paris, FRANCE).
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
"""library that enables the scheduling of a project"""

__revision__ = "$Id: __init__.py,v 1.22 2005-09-07 23:51:01 nico Exp $"

import sys
import logging, logging.config
from projman import verbose as verboselog

# create & init logger
logger = logging.getLogger("scheduler")
try:
    logging.config.fileConfig(LOG_CONF) # LOG_CONF not defined !
except Exception :
    logging.basicConfig()
            
class ScheduleException(Exception):
    """base of scheduling exceptions"""
    
class ScheduleError(ScheduleException): 
    """scheduling error"""
    
class NoSolutionFound(ScheduleException):
    """unable to find a solution"""


def schedule(proj, type, verbose=0):
    """
    launch scheduling of a projman instance
    Uses CSPScheduler if csp is true, otherwise BasicScheduler
    """
    errors = []
    hash_value = proj.hash()
    # FIXME: deal with hash
    if 0 and hash_value == proj.schedule.hash_value:
        verboselog('Scheduling not necessary, using previous results')
    else:
        proj.reset_schedule()
        if type == 'csp':
            from projman.scheduling.csp import CSPScheduler
            scheduler = CSPScheduler(proj)
        elif type == 'dumb':
            from projman.scheduling.dumb import DumbScheduler
            scheduler = DumbScheduler(proj)
        elif type == 'simple':
            from projman.scheduling.simple import SimpleScheduler
            scheduler = SimpleScheduler(proj)
        else:
            raise ValueError('bad scheduler type %s'%value)
        global_hash = proj.hash()
        errors += scheduler.schedule(verbose=verbose)
        #print scheduler.solution
        schedule.hash_value = global_hash
    for error in errors:
        sys.stderr.write("ERROR : %s\n" % str(error))
    if errors:
        sys.stderr.write("WARNING : %s errors\n" % len(errors))

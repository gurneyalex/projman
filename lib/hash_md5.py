# -*- coding: ISO-8859-1 -*-
# Copyright (c) 2004 LOGILAB S.A. (Paris, FRANCE).
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
Projman - (c)2000-2004 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projman

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

__revision__ = "$Id: hash_md5.py,v 1.1 2005-07-06 09:45:08 alf Exp $"

import md5

class HashMixin:
    def hash(self):
        """create a HASH String to be able to compare two objects
        This is used as an optimisation in DefaultScheduler
        """
        #TODO find a better way to represent dictionnaries in hash
        #-this way will make difference if order is different.
        md5_str = md5.new(str(self)).hexdigest()
        return int(md5_str[:8], 16)

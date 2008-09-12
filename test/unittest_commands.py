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
"""Projman - (c) 2004-2008 Logilab - All rights reserved."""

import shutil, os, tempfile
import os.path as osp

from logilab.common import testlib
from logilab.common.clcommands import cmd_run

from projman import commands # load commands

from projman.test import DATADIR, XML_PROJMAN, XML_SCHEDULED_PROJMAN, \
     XML_SCHEDULED_PROJMAN_FULL, TAR_PROJMAN


XML_PROJMAN = osp.join(DATADIR, XML_PROJMAN)
XML_SCHEDULED_PROJMAN = osp.join(DATADIR, XML_SCHEDULED_PROJMAN)
XML_SCHEDULED_PROJMAN_FULL = osp.join(DATADIR, XML_SCHEDULED_PROJMAN_FULL)
TAR_PROJMAN = osp.join(DATADIR, TAR_PROJMAN)

class AbstractCommandTest(testlib.TestCase):
    """testing """
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir) 
        
class ScheduleTest(AbstractCommandTest):
    """testing """

    def setUp(self):
        AbstractCommandTest.setUp(self)
        self.projman_path =  osp.join(DATADIR, "tmp_projman.xml")
        shutil.copyfile(XML_PROJMAN, self.projman_path)
        self.sched = osp.join(DATADIR, 'schedule.xml')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        os.remove(self.projman_path)

    def test_default(self):
        """Check if a schedule file is created and can be read again"""
        self.skip("this test needs rewrite")
        try:
            os.remove(self.sched)
        except OSError, e:
            print "ERROR:", self.sched, e
            pass
        print "PROJECT FILE:", self.projman_path
        cmd_run('schedule', '--type', 'csp', '-f', self.projman_path)
        #self.assert_(osp.exists(self.sched))
        # try reschedule
        cmd_run('schedule', '--type', 'csp', '-f', self.projman_path)
        #self.assert_(osp.exists(self.sched))

class DiagramTest(AbstractCommandTest):
    
    def test_gantt(self):
        gantt = osp.join(self.tmpdir, 'out_gantt.svg')
        cmd_run('diagram', '--timestep', 'week', '-f', XML_SCHEDULED_PROJMAN, 'gantt')
        self.assert_(osp.exists('gantt.svg'))
        #os.remove('gantt.svg')
        cmd_run('diagram', '--timestep', 'week', '-f', XML_SCHEDULED_PROJMAN, '-o',
                gantt, 'gantt')
        self.assert_(osp.exists(gantt))
        
#    def test_gantt2(self):
#        gantt = osp.join(self.tmpdir, 'out_gantt.svg')
#        cmd_run('diagram', '--timestep', 'week',
#                '-f', XML_SCHEDULED_PROJMAN_FULL, 'gantt')
#        self.assert_(osp.exists("gantt.svg"))
#        os.remove('gantt.svg')
#        cmd_run('diagram', '--timestep', 'week', '-f', XML_SCHEDULED_PROJMAN_FULL,
#                '-o', gantt, 'gantt')
#        self.assert_(osp.exists(gantt))

    def test_resources(self):
        resources = osp.join(self.tmpdir, 'resources')
        cmd_run('diagram', '-f', XML_SCHEDULED_PROJMAN, 'resources',
                '-o', resources)
        self.assert_(osp.exists(resources))
        cmd_run('diagram', '-f', XML_SCHEDULED_PROJMAN, '--format', 'svg',
                'resources', '-o', resources)
        self.assert_(osp.exists(resources))
    
    def test_gantt_resources(self):
        img = osp.join(self.tmpdir, 'gantt-resources')
        cmd_run('diagram', '-f', XML_SCHEDULED_PROJMAN, 'gantt-resources',
                '-o', img,)
        self.assert_(osp.exists(img))


class XmlTest(AbstractCommandTest):
    
    def test_all(self):
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN,
                'duration-table', 'duration-section', 'tasks-list-section',
                'cost-para', 'cost-table', 'rates-section')
        self.assert_(osp.exists("output.xml"))
        
    def test_duration_table(self):
        out = osp.join(self.tmpdir, 'out_duration.xml')
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', out, 'duration-table')
        self.assert_(osp.exists(out))
        
    def test_duration_section(self):
        out = osp.join(self.tmpdir, 'out_duration.xml')
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', out, 'duration-section')
        self.assert_(osp.exists(out))
    
    def test_tasks_list_section(self):
        out = osp.join(self.tmpdir, 'out_duration.xml')
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN,
                '-o', out, 'tasks-list-section')
        self.assert_(osp.exists(out))

    def test_cost_para(self):
        out = osp.join(self.tmpdir, 'out_duration.xml')
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', out, 'cost-para')
        self.assert_(osp.exists(out))

    def test_cost_table(self):
        out = osp.join(self.tmpdir, 'out_duration.xml')
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', out, 'cost-table')
        self.assert_(osp.exists(out))

    def test_rates_section(self):
        out = osp.join(self.tmpdir, 'out_duration.xml')
        cmd_run('view', '-f', XML_SCHEDULED_PROJMAN, '-o', out, 'rates-section')
        self.assert_(osp.exists(out))

if __name__ == '__main__':
    testlib.unittest_main()

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

import os, shutil, tempfile
import os.path as osp

from logilab.common.compat import set
from logilab.common import testlib

import projman.test

from projman.interface.file_manager import *
from projman.interface.option_manager import OptionManager
from projman.test import DATADIR, make_project_name
from projman.test import XML_PROJMAN, XML_TARED_PROJMAN, XML_TASK_FILE, \
     XML_RESOURCE_FILE, XML_ACTIVITY_FILE, TAR_PROJMAN, TAR_TARED_PROJMAN, \
     TAR_TASK_FILE, TAR_RESOURCE_FILE, TAR_ACTIVITY_FILE

WRITTEN_PROJMAN = "out_projman.xml"
WRITTEN_TASK = "out_task.xml"
WRITTEN_RESOURCE = "out_resources.xml"
WRITTEN_ACTVITY = "out_activities.xml"

DEFAULT_FILES = [osp.join(DATADIR, "projman.xml"),
                 osp.join(DATADIR, "tasks.xml"),
                 osp.join(DATADIR, "resources.xml"),
                 osp.join(DATADIR, "activities.xml"),
                 osp.join(DATADIR, "schedule.xml")]

WRITTEN_FILES = [osp.join(DATADIR, WRITTEN_PROJMAN),
                 osp.join(DATADIR, WRITTEN_RESOURCE),
                 osp.join(DATADIR, WRITTEN_TASK),
                 osp.join(DATADIR, WRITTEN_ACTVITY)]
WRITTEN_TAR = osp.join(DATADIR, make_project_name(WRITTEN_PROJMAN))

FILE_OPTIONS = [("-p", WRITTEN_TASK),
                ("-r", WRITTEN_RESOURCE),
                ("-a", WRITTEN_ACTVITY)]

class FileTest(testlib.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        
    def assertTarNames(self, storage):
        self.assertDictEquals(storage.file_names,
                              {PROJECT_KEY : TAR_PROJMAN,
                               RESOURCES_KEY : TAR_RESOURCE_FILE,
                               TASKS_KEY : TAR_TASK_FILE,
                               ACTIVITIES_KEY : TAR_ACTIVITY_FILE,
                               SCHEDULE_KEY : SCHEDULE_NAME})
        
    def assertXmlNames(self, storage):
        self.assertEquals(storage.file_names,
                          {PROJECT_KEY : XML_PROJMAN,
                           RESOURCES_KEY : XML_RESOURCE_FILE,
                           TASKS_KEY : XML_TASK_FILE,
                           ACTIVITIES_KEY : XML_ACTIVITY_FILE,
                           SCHEDULE_KEY : SCHEDULE_NAME})

    def assertProject(self, storage):
        project = storage.load()
        self.assertEquals(project.root_task.id, "project2")
        self.assertEquals(project.resource_set.id, "all_resources")
        grouped = project.activities.groupby('task')
        self.assertEquals(len(grouped), 2)
        
    def test_no_repo_but_files(self):
        os.chdir(DATADIR)
        # declare
        xml_to_packed_files = OptionManager(
            FILE_OPTIONS+ [("-t", None),],
            [XML_PROJMAN]).storage
        # projman -p ... -r ... -a ... project.xml
        self.assertEquals(xml_to_packed_files.archive_mode, True)
        # repos
        self.assertEquals(xml_to_packed_files._repo_in, DATADIR)
        self.assertEquals(xml_to_packed_files.output, None)
        # file names
        self.assertEquals(xml_to_packed_files._input, XML_PROJMAN)
        self.assertXmlNames(xml_to_packed_files)
        xml_to_packed_files.plan_projman(WRITTEN_PROJMAN)
        
    def test_xml_no_repo(self):
        os.chdir(DATADIR)
        # declare
        xml_to_pack = OptionManager(
            [("-t", None)],
            [XML_PROJMAN]).storage
        xml_to_xml = OptionManager(
            [("-t", None), ("-X", None)],
            [XML_PROJMAN]).storage
        storages = [xml_to_pack, xml_to_xml]
        # projman [-X] project.xml
        self.assertEquals(xml_to_pack.archive_mode, True)
        self.assertEquals(xml_to_xml.archive_mode, False)
        for storage in storages:
            self.assertEquals(storage._repo_in, DATADIR)
            self.assertEquals(storage._input ,XML_PROJMAN)
            self.assertEquals(storage.output, None)
            self.assertXmlNames(storage)
            self.assertProject(storage)
            
    def test_prj_no_repo(self):
        os.chdir(DATADIR)
        # declare
        pack_to_pack = OptionManager(
            [("-t", None)],
            [TAR_TARED_PROJMAN]).storage
        pack_to_xml = OptionManager(
            [("-t", None), ("-X", None)],
            [TAR_TARED_PROJMAN]).storage
        storages = [pack_to_pack, pack_to_xml]
        # projman [-X] project.prj
        for storage in storages:
            self.assertEquals(storage._repo_in, DATADIR)
            self.assertEquals(pack_to_pack._input ,TAR_TARED_PROJMAN)
            self.assertEquals(storage.output, None)
            self.assertTarNames(storage)
            self.assertProject(storage)

    def test_xml_repo_in(self):
        xml_to_pack = OptionManager(
            [("-t", None)],
            [osp.join(DATADIR, XML_PROJMAN)]).storage
        xml_to_xml = OptionManager(
            [("-t", None), ("-X", None)],
            [osp.join(DATADIR, XML_PROJMAN)]).storage
        storages = [xml_to_pack, xml_to_xml]
        # projman [-X] input/project.xml
        for storage in storages:
            self.assertEquals(storage._repo_in, DATADIR)
            self.assertEquals(storage._input, XML_PROJMAN)
            self.assertEquals(storage.output, None)
            self.assertXmlNames(storage)
            self.assertProject(storage)

    def test_prj_repo_in(self):
        pack_to_pack = OptionManager(
            [("-t", None)],
            [osp.join(DATADIR, TAR_TARED_PROJMAN)]).storage
        pack_to_xml = OptionManager(
            [("-t", None), ("-X", None)],
            [osp.join(DATADIR, TAR_TARED_PROJMAN)]).storage
        storages = [pack_to_pack, pack_to_xml]
        # projman [-X] input/project.prj
        for storage in storages:
            self.assertEquals(storage._repo_in, DATADIR)
            self.assertEquals(storage._input, TAR_TARED_PROJMAN)
            self.assertEquals(storage.output, None)
            self.assertTarNames(storage)
            self.assertProject(storage)

    def test_xml_repo_out(self):
        os.chdir(DATADIR)
        xml_to_pack = OptionManager(
            [("-t", None)],
            [XML_PROJMAN, osp.join(self.tmpdir, TAR_TARED_PROJMAN)]).storage
        xml_to_xml = OptionManager(
            [("-t", None), ("-X", None)],
            [XML_PROJMAN, osp.join(self.tmpdir, TAR_TARED_PROJMAN)]).storage
        storages = [xml_to_pack, xml_to_xml]
        # projman [-X] project.xml generated/project.xml
        for storage in storages:
            self.assertEquals(storage._repo_in, DATADIR)
            self.assertEquals(storage._input, XML_PROJMAN)
            self.assertEquals(storage.output, osp.join(self.tmpdir, TAR_TARED_PROJMAN))
            self.assertXmlNames(storage)
            self.assertProject(storage)

    def test_prj_repo_both(self):
        pack_to_pack = OptionManager(
            [("-t", None)],
            [osp.join(DATADIR, TAR_TARED_PROJMAN),
             osp.join(self.tmpdir, TAR_TARED_PROJMAN)]).storage
        pack_to_xml = OptionManager(
            [("-t", None), ("-X", None)],
            [osp.join(DATADIR, TAR_TARED_PROJMAN),
             osp.join(self.tmpdir, TAR_TARED_PROJMAN)]).storage
        storages = [pack_to_pack, pack_to_xml]
        # projman [-X] data/project.prj generated/project.prj
        for storage in storages:
            self.assertEquals(storage._repo_in, DATADIR)
            self.assertEquals(storage._input, TAR_TARED_PROJMAN)
            self.assertEquals(storage.output, osp.join(self.tmpdir, TAR_TARED_PROJMAN))
            self.assertTarNames(storage)
            self.assertProject(storage)
          
class WriteTest(testlib.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def assertWrittenNames(self, storage):
        self.assertEquals(storage.to_be_written,
                          {PROJECT_KEY : WRITTEN_PROJMAN,
                           RESOURCES_KEY : WRITTEN_RESOURCE,
                           TASKS_KEY : WRITTEN_TASK,
                           ACTIVITIES_KEY : WRITTEN_ACTVITY,
                           SCHEDULE_KEY : None})
        
    def test_write_xml(self):
        xml_to_packed_files = OptionManager(
            FILE_OPTIONS,
            [osp.join(DATADIR, XML_PROJMAN)]).storage
        projman = xml_to_packed_files.load()
        xml_to_packed_files.plan_projman(WRITTEN_PROJMAN)
        self.assertWrittenNames(xml_to_packed_files)
        xml_to_packed_files.save(projman)
        self.assert_(osp.exists(WRITTEN_TAR))
        for file_name in WRITTEN_FILES:
            self.assert_(not osp.exists(file_name))
            
    def test_write_tar(self):
        xml_to_packed_files = OptionManager(
            FILE_OPTIONS + [('-X', None)],
            [osp.join(DATADIR, XML_PROJMAN)]).storage
        projman = xml_to_packed_files.load()
        xml_to_packed_files.plan_projman(WRITTEN_PROJMAN)
        self.assertWrittenNames(xml_to_packed_files)
        xml_to_packed_files.save(projman)
        self.assert_(not osp.exists(osp.join(DATADIR, "out_projman.prj")))
        for file_name in WRITTEN_FILES:
            self.assert_(osp.exists(file_name))

if __name__ == "__main__":
    unittest_main()

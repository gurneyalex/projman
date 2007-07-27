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

import os, os.path, tempfile
from os.path import abspath, join

from logilab.common.compat import set
from logilab.common import testlib

import projman.test

from projman.storage import *
from projman.test import DATADIR, XML_PROJMAN, \
     XML_TARED_PROJMAN, XML_TASK_FILE, XML_RESOURCE_FILE, XML_ACTIVITY_FILE, \
     TAR_PROJMAN, TAR_TARED_PROJMAN, TAR_TASK_FILE, TAR_RESOURCE_FILE, \
     TAR_ACTIVITY_FILE

WRITTEN_PROJMAN = "out_projman.xml"
WRITTEN_TASK = "out_task.xml"
WRITTEN_RESOURCE = "out_resources.xml"
WRITTEN_ACTVITY = "out_activities.xml"

DEFAULT_FILES = [join(DATADIR, "projman.xml"),
                 join(DATADIR, "tasks.xml"),
                 join(DATADIR, "resources.xml"),
                 join(DATADIR, "activities.xml"),
                 join(DATADIR, "schedule.xml")]

WRITTEN_FILES = [join(DATADIR, WRITTEN_PROJMAN),
                 join(DATADIR, WRITTEN_RESOURCE),
                 join(DATADIR, WRITTEN_TASK),
                 join(DATADIR, WRITTEN_ACTVITY)]
#WRITTEN_TAR = join(DATADIR, make_project_name(WRITTEN_PROJMAN))

FILE_OPTIONS = [("-p", WRITTEN_TASK),
                ("-r", WRITTEN_RESOURCE),
                ("-a", WRITTEN_ACTVITY)]

class FileTest(testlib.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def assertDictEquals(self, got, expected):
        if got != expected:
            msg = ['Dictionnaries differ:']
            missing = set(expected) - set(got)
            unexpected = set(got) - set(expected)
            common = set(expected) & set(got)
            for key in missing:
                msg.append('missing key: %s (should be %s)' % (key, expected[key]))
            for key in unexpected:
                msg.append('unexpected key: %s (with value %s)' % (key, got[key]))
            for key in common:
                got_value = got[key]
                expected_value = expected[key]
                if got_value != expected_value:
                    msg.append('diff for key "%s": got "%s" instead of "%s"' %
                               (key, got_value, expected_value))
            raise AssertionError('\n\t'.join(msg))
        
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
        
##     def test_no_repo_but_files(self):
##         os.chdir(DATADIR)
##         # declare
##         xml_to_packed_files = OptionManager(
##             FILE_OPTIONS+ [("-t", None),],
##             [XML_PROJMAN]).storage
##         # projman -p ... -r ... -a ... project.xml
##         self.assertEquals(xml_to_packed_files.archive_mode, True)
##         # repos
##         self.assertEquals(xml_to_packed_files._repo_in, self.data_path)
##         self.assertEquals(xml_to_packed_files.output, None)
##         # file names
##         self.assertEquals(xml_to_packed_files._input, XML_PROJMAN)
##         self.assertXmlNames(xml_to_packed_files)
##         xml_to_packed_files.plan_projman(WRITTEN_PROJMAN)
        
##     def test_xml_no_repo(self):
##         os.chdir(DATADIR)
##         # declare
##         xml_to_pack = OptionManager(
##             [("-t", None)],
##             [XML_PROJMAN]).storage
##         xml_to_xml = OptionManager(
##             [("-t", None), ("-X", None)],
##             [XML_PROJMAN]).storage
##         storages = [xml_to_pack, xml_to_xml]
##         # projman [-X] project.xml
##         self.assertEquals(xml_to_pack.archive_mode, True)
##         self.assertEquals(xml_to_xml.archive_mode, False)
##         for storage in storages:
##             self.assertEquals(storage._repo_in, self.data_path)
##             self.assertEquals(storage._input ,XML_PROJMAN)
##             self.assertEquals(storage.output, None)
##             self.assertXmlNames(storage)
##             self.assertProject(storage)
            
##     def test_prj_no_repo(self):
##         os.chdir(DATADIR)
##         # declare
##         pack_to_pack = OptionManager(
##             [("-t", None)],
##             [TAR_TARED_PROJMAN]).storage
##         pack_to_xml = OptionManager(
##             [("-t", None), ("-X", None)],
##             [TAR_TARED_PROJMAN]).storage
##         storages = [pack_to_pack, pack_to_xml]
##         # projman [-X] project.prj
##         for storage in storages:
##             self.assertEquals(storage._repo_in, self.data_path)
##             self.assertEquals(pack_to_pack._input ,TAR_TARED_PROJMAN)
##             self.assertEquals(storage.output, None)
##             self.assertTarNames(storage)
##             self.assertProject(storage)

##     def test_xml_repo_in(self):
##         xml_to_pack = OptionManager(
##             [("-t", None)],
##             [join(DATADIR, XML_PROJMAN)]).storage
##         xml_to_xml = OptionManager(
##             [("-t", None), ("-X", None)],
##             [join(DATADIR, XML_PROJMAN)]).storage
##         storages = [xml_to_pack, xml_to_xml]
##         # projman [-X] input/project.xml
##         for storage in storages:
##             self.assertEquals(storage._repo_in, self.data_path)
##             self.assertEquals(storage._input, XML_PROJMAN)
##             self.assertEquals(storage.output, None)
##             self.assertXmlNames(storage)
##             self.assertProject(storage)

##     def test_prj_repo_in(self):
##         pack_to_pack = OptionManager(
##             [("-t", None)],
##             [join(DATADIR, TAR_TARED_PROJMAN)]).storage
##         pack_to_xml = OptionManager(
##             [("-t", None), ("-X", None)],
##             [join(DATADIR, TAR_TARED_PROJMAN)]).storage
##         storages = [pack_to_pack, pack_to_xml]
##         # projman [-X] input/project.prj
##         for storage in storages:
##             self.assertEquals(storage._repo_in, self.data_path)
##             self.assertEquals(storage._input, TAR_TARED_PROJMAN)
##             self.assertEquals(storage.output, None)
##             self.assertTarNames(storage)
##             self.assertProject(storage)

##     def test_xml_repo_out(self):
##         os.chdir(DATADIR)
##         xml_to_pack = OptionManager(
##             [("-t", None)],
##             [XML_PROJMAN, join(self.generated_path, TAR_TARED_PROJMAN)]).storage
##         xml_to_xml = OptionManager(
##             [("-t", None), ("-X", None)],
##             [XML_PROJMAN, join(self.generated_path, TAR_TARED_PROJMAN)]).storage
##         storages = [xml_to_pack, xml_to_xml]
##         # projman [-X] project.xml generated/project.xml
##         for storage in storages:
##             self.assertEquals(storage._repo_in, self.data_path)
##             self.assertEquals(storage._input, XML_PROJMAN)
##             self.assertEquals(storage.output, join(self.generated_path, TAR_TARED_PROJMAN))
##             self.assertXmlNames(storage)
##             self.assertProject(storage)

##     def test_prj_repo_both(self):
##         pack_to_pack = OptionManager(
##             [("-t", None)],
##             [join(DATADIR, TAR_TARED_PROJMAN),
##              join(GENERATED_DIR, TAR_TARED_PROJMAN)]).storage
##         pack_to_xml = OptionManager(
##             [("-t", None), ("-X", None)],
##             [join(DATADIR, TAR_TARED_PROJMAN),
##              join(GENERATED_DIR, TAR_TARED_PROJMAN)]).storage
##         storages = [pack_to_pack, pack_to_xml]
##         # projman [-X] data/project.prj generated/project.prj
##         for storage in storages:
##             self.assertEquals(storage._repo_in, self.data_path)
##             self.assertEquals(storage._input, TAR_TARED_PROJMAN)
##             self.assertEquals(storage.output, join(self.generated_path, TAR_TARED_PROJMAN))
##             self.assertTarNames(storage)
##             self.assertProject(storage)
          
class WriteTest(testlib.TestCase):

    def setUp(self):
        for file_name in WRITTEN_FILES : #+ [WRITTEN_TAR]:
            if os.path.exists(file_name):
                os.remove(file_name)

    def tearDown(self):
        for file_name in WRITTEN_FILES + DEFAULT_FILES: # [WRITTEN_TAR]
            if os.path.exists(file_name):
                os.remove(file_name)
    
    def assertWrittenNames(self, storage):
        self.assertEquals(storage.to_be_written,
                          {PROJECT_KEY : WRITTEN_PROJMAN,
                           RESOURCES_KEY : None, #WRITTEN_RESOURCE,
                           TASKS_KEY : None, #WRITTEN_TASK,
                           ACTIVITIES_KEY : None, #WRITTEN_ACTVITY,
                           SCHEDULE_KEY : None})
        
    def test_write_xml(self):
        xml_to_packed_files = ProjectStorage(DATADIR, XML_PROJMAN)
        projman = xml_to_packed_files.load()
        xml_to_packed_files.plan_projman(WRITTEN_PROJMAN)
        self.assertWrittenNames(xml_to_packed_files)
        xml_to_packed_files.save(projman)
        #self.assert_(os.path.exists(WRITTEN_TAR))
        for file_name in WRITTEN_FILES:
            self.assert_(not os.path.exists(file_name))
            
#     def test_write_tar(self):
#         xml_to_packed_files = ProjectStorage(DATADIR, XML_PROJMAN, archive_mode=True)
#         projman = xml_to_packed_files.load()
#         xml_to_packed_files.plan_projman(WRITTEN_PROJMAN)
#         self.assertWrittenNames(xml_to_packed_files)
#         xml_to_packed_files.save(projman)
#         self.assert_(not os.path.exists(join(DATADIR, "out_projman.prj")))
#         for file_name in WRITTEN_FILES:
#             self.assert_(os.path.exists(file_name))

if __name__ == "__main__":
    testlib.unittest_main()

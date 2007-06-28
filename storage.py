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

__revision__ ="$Id: file_manager.py,v 1.16 2005-09-06 17:06:43 nico Exp $"

import sys
import tarfile
import logging, logging.config
import os, os.path as osp
from ConfigParser import ConfigParser

from logilab.common.compat import set

from projman import LOG_CONF, extract_extension
from projman.writers.projman_writer import as_xml_string, \
     write_schedule_as_xml, write_activities_as_xml

from projman.readers import ProjectXMLReader
from projman.lib._exceptions import MissingRequiredAttribute, \
     MalformedProjectFile, ScheduleCycle, ResourceNotFound,  \
     DuplicatedResource, TTException

#TODO implement interactive mode
#TODO use lists in self.file_names
#FIXME: create better default files

# conf pointing out what are the names of the files of the project
CONF_FILE = "files.conf"
CONF_SECTION = "project files"
# default file names
DEFAULT_NAMES = {
    "resources" : "resources_description.xml",
    "tasks" : "tasks_description.xml",
    "activities" : "activities_description.xml",
    "schedule" : "schedule.xml",
}
# default file content
FILE_CONTENTS = {
    "project" : """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<projman/>""",
    "resources" : """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<resources-set/>""",
    "tasks" : """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<project/>""",
    "activities" : """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<activities/>"""
    }


def default_writer(tree, file):
    file.write(as_xml_string(tree))

def _write_trees(trees, output_name, writer=default_writer):
    """write output file"""
    print "TREES", trees
    written_files = []
    print "TREE", trees
    if len(trees) > 1:
        for index, tree in enumerate(trees):
            name, extension = extract_extension(output_name)
            file_name = '%s.%s.%s' % (name, index, extension)
            file_object = open(file_name, 'w')
            writer(tree, file_object)
            written_files.append(file_name)
    elif len(trees) == 1:
        file_object = open(output_name, 'w')
        writer(trees[0], file_object)
        written_files.append(output_name)
    #else: nothing to write
    return written_files

class ProjectFiles:
    def __init__(self):
        self.repo_dir = ""
        self.project = None
        self.schedule = None
        self.resources = []
        self.activities = []
        self.tasks = []

    def copy_from_project(self, output, ofiles):
        """Create new file names from a source project and a new project destination"""
        _dir, _name = osp.split(osp.abspath(output))
        self.repo_dir = _dir
        self.project = _name
        for n in "schedule resources activities tasks".split():
            names = getattr(ofiles, n)
            typ = type(names)
            if typ!=list:
                names = [names]
            newnames = []
            for name in names:
                newnames.append(osp.basename(name))
            if not newnames:
                newnames = [DEFAULT_NAMES[n]]
            if typ!=list:
                newnames = names[0]
            setattr(self, n, newnames)

    def get_schedule(self):
        return osp.join(self.repo_dir, self.schedule)
    def get_project(self):
        return osp.join(self.repo_dir, self.project)

class ProjectStorage:
    """load and save projman project from set of file names"""
    
    def __init__(self, repo_in, input_, output=None,
                 virtual_task_root=None):
        """
         repo_in: name of directory of projman file 
         input_: name of projman file
         output: name of output file
         
         input_projman: input file under projman format
         virtual_task_root: id of a task to use as root
        """
        # create logger
        self.logger = logging.getLogger("reader")
        try:
            logging.config.fileConfig(LOG_CONF)
        except Exception :
            logging.basicConfig()
        # set options
        self.vtask_root = virtual_task_root

        # manages the file names of the input project
        self.files = ProjectFiles()
        self.files.repo_dir = repo_in
        self.files.project = input_
        self.project = None

    def __str__(self):
        return self._input

    def load(self, readerklass=None, **kwargs):
        """returns project built with reader defined in option container"""
        if readerklass is None:
            readerklass = ProjectXMLReader
        file_in = osp.join(self.files.repo_dir, self.files.project)
        # set Projman reader by default
        proj_reader = readerklass( self.files, self.vtask_root)
        # reading
        self.project = proj_reader.fromFile(file_in)

    # WRITERS
    #########
    def save(self, output=None, write_schedule=False, include_reference=False):
        """write all files of projects"""
        if output is not None:
            files = ProjectFiles()
            files.copy_from_project( output, self.files )
        else:
            files = self.files
        self._write_tasks(files)
        self._write_resources(files)
        self._write_activities(files)
        self._write_projman(files)
        if write_schedule:
            self.write_schedule(files)
            if include_reference:
                self.write_schedule_reference(files)

    def write_schedule(self, files):
        """writes schedule and include reference in projman (after
        calling load)"""
        output_name = files.get_schedule()
        write_schedule_as_xml(output_name, self.project)

    def write_schedule_reference(self, files):
        """modify projman file"""
        # XXX moyen-bof comme methode...
        file_obj = open(self.files.get_project(), 'r')
        lines = file_obj.readlines()
        file_obj.close()
        for fname in files.schedule:
            import_schedule = "\t<import-schedule file='%s'/>\n"\
                              % osp.basename(fname)
            if import_schedule not in lines:
                lines.insert(-2, import_schedule)
        file_obj = open(files.get_project(), 'w')
        file_obj.writelines(lines)
        file_obj.close()

    def _write_projman(self, files):
        """write projman, pointing out the other files"""
        output_f = open(files.get_project(), 'w')
        output_f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        output_f.write("<project>\n")
        # write tasks
        if files.tasks:
            for file_name in files.tasks:
                output_f.write("\t<import-tasks file=\'%s\'/>\n" \
                               % osp.basename(file_name))
        else:
            output_f.write("\t<import-tasks file=\'%s\'/>\n" \
                           % self.file_names[TASKS_KEY])
        # write resources
        if self.written_files[RESOURCES_KEY]:
            for file_name in self.written_files[RESOURCES_KEY]:
                output_f.write("\t<import-resources file=\'%s\'/>\n" \
                               % osp.basename(file_name))
        else:
            output_f.write("\t<import-resources file=\'%s\'/>\n" \
                           % self.file_names[RESOURCES_KEY])
        # write activities
        if self.written_files[ACTIVITIES_KEY]:
            for file_name in self.written_files[ACTIVITIES_KEY]:
                output_f.write("\t<import-activities file=\'%s\'/>\n" \
                               % osp.basename(file_name))
        else:
            output_f.write("\t<import-activities file=\'%s\'/>\n" \
                           % self.file_names[ACTIVITIES_KEY])
        output_f.write("</project>")
        output_f.close()
        self._set_written_file(PROJECT_KEY, self.to_projman())

    def _write_tasks(self, files):
        """writes tasks (after calling load)"""
        # XXX CHECK IF WRITE IS NEEDED
        output_name = osp.join(files.repo_dir, files.tasks)
        written_files = _write_trees(self.project, output_name)

    def _write_resources(self, files):
        """writes resources (after calling load)"""
        # XXX CHECK IF WRITE IS NEEDED
        output_name = osp.join(files.repo_dir, files.resources)
        written_files = _write_trees(
            self.project.resource_set,
            output_name)

    def _write_activities(self, files):
        """writes activities (after calling load)"""
        # XXX CHECK IF WRITE IS NEEDED
        output_name = osp.join(files.repo_dir, files.activities)
        write_activities_as_xml(output_name, self.project)

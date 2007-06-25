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
import os, os.path
from ConfigParser import ConfigParser

from logilab.common.compat import set

from projman import LOG_CONF, extract_extension
from projman.writers.projman_writer import as_xml_string, \
     write_schedule_as_xml, write_activities_as_xml

from projman.readers import ProjectFileListReader, ProjectXMLReader
from projman.lib._exceptions import MissingRequiredAttribute, \
     MalformedProjectFile, ScheduleCycle, ResourceNotFound,  \
     DuplicatedResource, TTException

#TODO inplement interactive mode
#TODO use lists in self.file_names
#FIXME: create better default files

SUFFIX = ".prj"
# conf pointing out what are the names of the files of the project
CONF_FILE = "files.conf"
CONF_SECTION = "project files"
# keys used to access file name and file object
PROJECT_KEY = "project"
RESOURCES_KEY = "resources"
TASKS_KEY = "tasks"
ACTIVITIES_KEY = "activities"
SCHEDULE_KEY = "schedule"
# default file names
PROJECT_NAME = "project.xml"
RESOURCES_NAME = "resources_description.xml"
TASKS_NAME = "tasks_description.xml"
ACTIVITIES_NAME = "activities_description.xml"
SCHEDULE_NAME = "schedule.xml"
# default file content
FILE_CONTENTS = {
    PROJECT_KEY : """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<projman/>""",
    RESOURCES_KEY : """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<resources-set/>""",
    TASKS_KEY : """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<project/>""",
    ACTIVITIES_KEY : """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<activities/>"""}


def default_writer(tree, file):
    file.write(as_xml_string(tree))

def write_trees(trees, output_name, writer=default_writer):
    """write output file"""
    print "TREES", trees
    written_files = []
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

class ProjectStorage:
    """load and save projman project from set of file names"""
    
    def __init__(self, repo_in, input_, output=None,
                 archive_mode=True, input_projman=True,
                 virtual_task_root=None):
        """
         repo_in: name of directory of projman file 
         input_: name of projman file
         output: name of output file
         
         archive_mode: True if using a .prj file for output
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
        self.archive_mode = archive_mode
        self.vtask_root = virtual_task_root
        # default file names
        self._repo_in = repo_in
        self._input = input_
        self.output = output
        self.file_names = {PROJECT_KEY : PROJECT_NAME,
                           RESOURCES_KEY : RESOURCES_NAME,
                           TASKS_KEY : TASKS_NAME,
                           ACTIVITIES_KEY : ACTIVITIES_NAME,
                           SCHEDULE_KEY : SCHEDULE_NAME}
        self.to_be_written = {PROJECT_KEY : None,
                              RESOURCES_KEY : None,
                              TASKS_KEY : None,
                              ACTIVITIES_KEY : None,
                              SCHEDULE_KEY : None}
        self.written_files = {PROJECT_KEY : [],
                             RESOURCES_KEY : [],
                             TASKS_KEY : [],
                             ACTIVITIES_KEY : [],
                             SCHEDULE_KEY : []}
        if input_projman:
            self._init_project()
        
    def __str__(self):
        return self._input

    def _init_project(self):
        """build up tar_name according input and options"""
        if self._input.endswith(SUFFIX):
            # read archive 
            self._init_archive(self._input)
        else:
            # read xml
            self._init_projman(self._input)

    def _init_archive(self, tar_name):
        """load file names from a .prj file
        
        @returns: None if could not find specified File, nor open it
        """
        #TODO temporary dir? pb of path in import...
        # extract & read conf file
        tar_file = tarfile.open(self.from_repo(tar_name))
        tar_file.extract(CONF_FILE, self._repo_in)
        conf_parser = ConfigParser()
        conf_file = open(self.from_repo(CONF_FILE))
        conf_parser.readfp(conf_file)
        conf_file.close()
        # extract all files
        for file_desc in conf_parser.options(CONF_SECTION):
            file_name = conf_parser.get(CONF_SECTION, file_desc)
            tar_file.extract(file_name, self._repo_in)
            self.file_names[file_desc] =  os.path.basename(file_name)
        # close archive
        tar_file.close()
        
    def _init_projman(self, file_name):
        """initialise self.file_names from a .xml file"""
        file_path = self.from_repo(file_name)
        reader = ProjectFileListReader(self)
        exceptions = (MissingRequiredAttribute, 
                      MalformedProjectFile, ScheduleCycle, ResourceNotFound,  
                      DuplicatedResource, TTException)
        try:
            self.set_projman(file_name)
            reader.fromFile(file_path)
        except exceptions, ex:
            import traceback
            traceback.print_exc()
            self.logger.info(ex)
            print ex
            sys.exit(1)
            
    def load(self, proj_reader=None):
        """returns project built with reader defined in option container"""
        exceptions = (MissingRequiredAttribute,
                      MalformedProjectFile, ScheduleCycle, ResourceNotFound,
                      DuplicatedResource, TTException)
        file_in = os.path.join(self._repo_in, self._input)
        # set Projman reader by default
        if proj_reader is None or isinstance(proj_reader, ProjectXMLReader):
            proj_reader = ProjectXMLReader(self.vtask_root)
            file_in = self.from_projman()
        # reading
        try:
            if self._input == '-':
                return proj_reader.fromStream(sys.stdin)
            else:
                return proj_reader.fromFile(file_in)
        except exceptions, ex:
            #import traceback
            #traceback.print_exc()
            #self.logger.info(ex)
            print ex
            sys.exit(1)
        
    def tar_project(self, include_reference=False):
        """build and compress archive"""
        assert self.archive_mode, "option -X set: creating .prj forbidden"
        tar_path = extract_extension(self.to_projman())[0] + SUFFIX
        tar_file = tarfile.open(tar_path, "w")
        # creating conf file which stores {filename: type of file}
        conf_parser = ConfigParser()
        conf_parser.add_section(CONF_SECTION)
        # adding all files to archive
        files_from_delete = []
        for key, file_names in self.written_files.items():
            if key == SCHEDULE_KEY and not include_reference:
                continue
            if len(file_names) == 0:
                # no written file: check initial one
                assert os.path.exists(self._from_repo_by_key(key)), \
                       "%s missing"% self._from_repo_by_key(key)
                tar_file.add(self._from_repo_by_key(key), self.file_names[key])
                conf_parser.set(CONF_SECTION, key, self.file_names[key])
                files_from_delete.append(self._from_repo_by_key(key))
                
            else:
                # file modified. forget previous one and add new ones
                for file_name in file_names:
                    base_name =  os.path.basename(file_name)
                    tar_file.add(file_name, base_name)
                    conf_parser.set(CONF_SECTION, key, base_name)
                    files_from_delete.append(file_name)
        # writing and adding conf file
        conf_file = open(self.from_repo(CONF_FILE), 'w')
        conf_parser.write(conf_file)
        conf_file.close()
        tar_file.add(conf_file.name, CONF_FILE)
        files_from_delete.append(conf_file.name)
        # close and remove files
        tar_file.close()
        for file_stored in files_from_delete:
            os.remove(file_stored)

    # WRITERS
    #########
    def save(self, projman, write_schedule=False, include_reference=False):
        """write all files of projects"""
        self._write_tasks(projman)
        self._write_resources(projman)
        self._write_activities(projman)
        self._write_projman(projman)
        if write_schedule:
            self.write_schedule(projman)
            if include_reference:
                self.write_schedule_reference(projman)
        if self.archive_mode:
            self.tar_project(include_reference)
        
    def write_schedule(self, project):
        """writes schedule and include reference in projman (after
        calling load)"""
        output_name = self.to_schedule()
        write_schedule_as_xml(output_name, project)
        self._set_written_files(SCHEDULE_KEY, [output_name])

    def write_schedule_reference(self, projman):
        """modify projman file"""
        file_obj = open(self.to_projman(), 'r')
        lines = file_obj.readlines()
        file_obj.close()
        for file_name in self.written_files[SCHEDULE_KEY]:
            import_schedule = "\t<import-schedule file='%s'/>\n"\
                              % os.path.basename(file_name)
            if import_schedule not in lines:
                lines.insert(-2, import_schedule)
            #else: already included
        file_obj = open(self.to_projman(), 'w')
        file_obj.writelines(lines)
        file_obj.close()        

    def _write_projman(self, projman):
        """write projman, pointing out the other files"""
        output_f = open(self.to_projman(), 'w')
        output_f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        output_f.write("<project>\n")
        # write tasks
        if self.written_files[TASKS_KEY]:
            for file_name in self.written_files[TASKS_KEY]:
                output_f.write("\t<import-tasks file=\'%s\'/>\n" \
                               % os.path.basename(file_name))
        else:
            output_f.write("\t<import-tasks file=\'%s\'/>\n" \
                           % self.file_names[TASKS_KEY])
        # write resources
        if self.written_files[RESOURCES_KEY]:
            for file_name in self.written_files[RESOURCES_KEY]:
                output_f.write("\t<import-resources file=\'%s\'/>\n" \
                               % os.path.basename(file_name))
        else:
            output_f.write("\t<import-resources file=\'%s\'/>\n" \
                           % self.file_names[RESOURCES_KEY])
        # write activities
        if self.written_files[ACTIVITIES_KEY]:
            for file_name in self.written_files[ACTIVITIES_KEY]:
                output_f.write("\t<import-activities file=\'%s\'/>\n" \
                               % os.path.basename(file_name))
        else:
            output_f.write("\t<import-activities file=\'%s\'/>\n" \
                           % self.file_names[ACTIVITIES_KEY])
        output_f.write("</project>")
        output_f.close()
        self._set_written_file(PROJECT_KEY, self.to_projman())

    def _write_tasks(self, project):
        """writes tasks (after calling load)"""
        if self.to_be_written[TASKS_KEY] is None:
            return
        written_files = write_trees(project,
                                    self.from_repo(self.to_be_written[TASKS_KEY]))
        self._set_written_files(TASKS_KEY, written_files)
            
    def _write_resources(self, project):
        """writes resources (after calling load)"""
        if self.to_be_written[ACTIVITIES_KEY] is None:
            return
        written_files = write_trees(
            project.resource_set,
            self.from_repo(self.to_be_written[ACTIVITIES_KEY]))
        self._set_written_files(ACTIVITIES_KEY, written_files)
            
    def _write_activities(self, project):
        """writes activities (after calling load)"""
        if self.to_be_written[RESOURCES_KEY] is None:
            return
        output_name = self.from_repo(self.to_be_written[RESOURCES_KEY])
        write_activities_as_xml(output_name, project)
        self._set_written_files(RESOURCES_KEY, [output_name])
        
    def _write_default_file(self, key, name=None):
        """write a default file except for schedule"""
        if not name:
            name = self.file_names[key]
        if key is SCHEDULE_KEY:
            # no default file for schedule
            return None
        else:
            assert not os.path.exists(name), \
                   ValueError("%s exists. can't overwrite "% name)
            default_file = open(name, "w")
            default_file.write(FILE_CONTENTS[key])
            default_file.close()
            return name
        
    def _set_written_file(self, key, name):
        """add a file object to matching key."""
        full_path = self.from_repo(os.path.basename(name))
        if full_path not in self.written_files[key]:
            self.written_files[key].append(full_path)

    def _set_written_files(self, key, names):
        """add a file object to matching key."""
        for name in names:
            self._set_written_file(key, name)
            
    # GETTERS
    #########        
    def get_schedule(self):
        if self.to_be_written[SCHEDULE_KEY]:
            return self.to_be_written[SCHEDULE_KEY]
        else:
            return self.file_names[SCHEDULE_KEY]
        
    def to_projman(self):
        if self.to_be_written[PROJECT_KEY]:
            return self.from_repo(self.to_be_written[PROJECT_KEY])
        else:
            return self.from_repo(self.file_names[PROJECT_KEY])
        
    def to_schedule(self):
        return self.from_repo(self.get_schedule())
        
    def from_projman(self):
        return self.from_repo(self.file_names[PROJECT_KEY])
        
    def from_repo(self, name=None):
        if name:
            return os.path.join(self._repo_in, name)
        else:
            return self._repo_in
        
    def _from_repo_by_key(self, key):
        return self.from_repo(self.file_names[key])

    # SETTERS
    #########
    def set_output(self, name):
        """set new value to output"""
        self.output = os.path.basename(name)

    def set_projman(self, name):
        """set projman file"""
        self.file_names[PROJECT_KEY] = os.path.basename(name)

    def set_resources(self, name):
        """set resources file"""
        self.file_names[RESOURCES_KEY] = os.path.basename(name)

    def set_tasks(self, name):
        """set tasks file"""
        self.file_names[TASKS_KEY] = os.path.basename(name)
 
    def set_activities(self, name):
        """set activities file"""
        self.file_names[ACTIVITIES_KEY] = os.path.basename(name)
 
    def set_schedule(self, name):
        """set schedule file"""
        self.file_names[SCHEDULE_KEY] =  os.path.basename(name)

    def plan_projman(self, name):
        """plan resources file"""
        self.to_be_written[PROJECT_KEY] = os.path.basename(name)

    def plan_resources(self, name):
        """plan resources file"""
        self.to_be_written[RESOURCES_KEY] = os.path.basename(name)

    def plan_tasks(self, name):
        """plan tasks file"""
        self.to_be_written[TASKS_KEY] = os.path.basename(name)
 
    def plan_activities(self, name):
        """plan activities file"""
        self.to_be_written[ACTIVITIES_KEY] = os.path.basename(name)
 
    def plan_schedule(self, name):
        """plan schedule file"""
        self.to_be_written[SCHEDULE_KEY] = os.path.basename(name)

    def plan_defaults(self):
        """ask to write all files, setting default values if necessary"""
        for key in [TASKS_KEY, ACTIVITIES_KEY, RESOURCES_KEY]:
            if self.to_be_written[key] is None:
                self.to_be_written[key] = self.file_names[key]
        

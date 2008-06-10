# Copyright (c) 2000-2002 LOGILAB S.A. (Paris, FRANCE).
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
reader generate a model from xml file (see dtd/project.dtd)
"""
__revision__ = "$Id: base_reader.py,v 1.2 2005-11-09 16:47:35 arthur Exp $"

from os.path import dirname, abspath
from xml.sax import make_parser, ContentHandler
from xml.sax.handler import feature_namespaces

from projman.lib.project import Project
from projman.lib.task import Task, MileStone
from projman.lib.resource import Resource, ResourcesSet
from projman.lib.resource_role import ResourceRole, ResourceRoleSet
from projman.lib.calendar import Calendar
from projman.lib._exceptions import ProjectValidationError, MalformedProjectFile


class ModelProjectFactory:
    """ a factory which create Projman model's objects """
    
    def create_project(self):
        """ create a new projman node """
        return Project()
        
    def create_milestone(self, m_id):
        """ create a new milestone node """
        return MileStone(m_id)
        
    def create_milestone_from_task(self, task):
        """ create a new milestone node """
        stone = self.create_milestone(task.id)
        stone.title = task.title
        stone.task_constraints = task.task_constraints
        stone.description = task.description
        return stone

    def create_task(self, t_id):
        """ create a new task node """
        return Task(t_id)

    def create_resource(self, r_id, r_name, r_type, calendar, r_hourly_rate='0.0', r_unit='euros'):
        """ create a new resource """
        try:
            float_rate = float(r_hourly_rate)
        except ValueError:
            raise AttributeError("Resource's hourly rate must be a float")
        return Resource(r_id, r_name, r_type, calendar, float_rate, r_unit)

    def create_resourcesset(self, rs_id):
        """ create a new resources set """
        return ResourcesSet(rs_id)

    def create_resource_role(self, r_id, name, cost='0.0', unit='euros'):
        """create a new resource_role"""
        return ResourceRole(r_id, name, cost, unit)

    def create_resource_role_set(self, rs_id):
        """ create a new resource_role set """
        return ResourceRoleSet(rs_id)

    def create_calendar(self, tt_id, tt_name = u''):
        """ create a new time table """
        return Calendar(tt_id, tt_name)

    def subproject_to_task(self, project):
        """ converts a subproject to a task """
        t = self.create_task(project.id)
        for task in project.children:
            t.append(task)
        return t

MODEL_FACTORY = ModelProjectFactory()

# abstract reader for xml files ###############################################

class AbstractXMLReader(ContentHandler):
    """ generic abstract reader """
    
    def __init__(self, factory=MODEL_FACTORY):
        self._factory = factory
        # default type used for resources list
        self._default_type = ""
        # path in the tree
        self.stack = []
        self._tags = []
        # base uri used for imported file resolution
        self._base_uris = []
        # file names for error report
        self._files = []
        # keep trace of yet imported files
        self._imported = {}
        # buffer for characters() callback
        self._buffer = []
        # buffer of formatting errors
        self._errors = []
       
    def fromFile(self, file):
        """ 
        import and return a project from a xml file
        """
        return self.fromStream(open(file),
                               file, dirname(abspath(file)))
        
    def fromStream(self, stream,
                   filename="input_stream", base_uri=''):
        """ 
        import and return a project from a xml stream
        """
        # create a xml parser
        p = make_parser()
        # do not perform Namespace processing 
        p.setFeature(feature_namespaces, 0)
        p.setContentHandler(self)
        p.reset()

        # parse file
        self._base_uris.append(base_uri)
        self._files.append(filename)
        p.parse(stream)
        self._base_uris.pop()
        self._files.pop()
        if self._errors:
            raise MalformedProjectFile('\n'.join(self._errors))
        return self._custom_return()

    def _custom_return(self):
        raise NotImplementedError(self.__class__)

    def startDocument(self):
        self._buffer = []

    def characters(self, data):
        self._buffer.append(data)

    def get_characters(self, joined_with=' ', strip=True):
        """return the character buffer.
        By default, strips all chunks and join them with a single space.
        If strip is false, join is performed with an empty string."""
        if strip:
            self._buffer = [a.strip() for a in self._buffer if a.strip()]
        else:
            joined_with = u''
        characters = joined_with.join(self._buffer)
        self._buffer = []
        return characters

    def startElement(self, tag, attr):
        try:
            self._attrs = attr
            self._start_element(tag, attr)
        except ProjectValidationError, error:
            try:
                msg = unicode(error)% (self._files[-1],
                                       self._locator.getLineNumber(),
                                       tag)
                self._errors.append(msg)
                self._tags.append(tag)
            except TypeError:
                raise error
        except:
            if self._errors:
                print 'WARNING: pending validation errors:'
                print '\n'.join(self._errors)
            raise
        self._tags.append(tag)

    def _start_element(self, tag, attr):
        pass
    
    def endElement(self, tag):
        try:
            self._end_element(tag)
        except ProjectValidationError, error:
            try:
                msg = unicode(error)% (self._files[-1],
                                       self._locator.getLineNumber(),
                                       tag)
                self._errors.append(msg)
            except TypeError:
                raise error
        except:
            if self._errors:
                print 'WARNING: pending validation errors:'
                print '\n'.join(self._errors)
            raise
        self._tags.pop()
        

    def _end_element(self, tag):
        pass

    def assert_child_of(self, tags):
        if not self._tags :
            if None in tags :
                return
            else:
                raise ProjectValidationError('file %s line %s : %s is not root tag')
        elif not self._tags[-1] in tags:
            raise ProjectValidationError('file %%s line %%s : %%s should be child of '
                                         '%s not %s' % (tags, self._tags[-1]))
        
    def assert_has_attrs(self, attrs):
        for attr in attrs:
            if attr not in self._attrs.keys():
                # TODO replace by MissingRequiredAttribute
                raise ProjectValidationError('file %%s line %%s : Missing required ' \
                                             'attribute %s to element <%%s>' % attr)
                #msg = unicode(error)% (self._files[-1],
                #                       self._locator.getLineNumber(),
                #                       tag)
                #self._errors.append(msg)


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
""" xml exportation utilities """

__revision__ = "$Id: tasks_list_writer.py,v 1.10 2005-09-06 17:09:29 nico Exp $"

from projman.writers.docbook_writers import AbstractTaskWriter
from projman.writers.docbook_writers import get_daily_labor
from projman.writers.docbook_writers import EXT_DATE_FORMAT
from projman.writers.docbook_writers import NO_NS
from projman import ENCODING
from xml.dom.minidom import parseString

DATE_NOT_SPECIFIED = "not specified"

class ListTasksDOMWriter(AbstractTaskWriter):   
    """
    return the dom representation of the tasks view.
    """

    def _build_task_node(self, task):
        """ create a DOM node
        <section id=task.id.>
          <title>task.title</title>
          < resource node > 
        </formalpara>
        """
        # global calculation
        AbstractTaskWriter._build_task_node(self, task)
        # create section 	 
        section = self.section_node(task.id) 	 
        root =  self.tree[-1]
        root.appendChild(section)
        self.tree.append(section)
        # fill title
        section.appendChild(self.title_node(task.title))
        # fill description
        if task.description != "":
            # create xml-like string
            # encode it and create XML tree from it
            # FIXME !!!
            assert isinstance(task.description, unicode), task.description
            desc = "<?xml version='1.0' encoding='%s'?><para>%s</para>" \
                   % (ENCODING, task.description.encode(ENCODING))
            try:
                description_doc = parseString(desc)
            except Exception, exc:
                print desc
                raise
            section.appendChild(description_doc.documentElement)
        # add date-constraints
        formal_para = self.formalpara_node()
        section.appendChild(formal_para)
        formal_para.appendChild(self.title_node(u"Dates"))
        date_begin, date_end = self.projman.get_task_date_range(task)
        begin = date_begin or DATE_NOT_SPECIFIED
        end = date_end or DATE_NOT_SPECIFIED
        para = self.para_node(u"du %s au %s" % (begin.Format(EXT_DATE_FORMAT),
                                                end.Format(EXT_DATE_FORMAT)))
        formal_para.appendChild(para)

        # add resources' info
        if task.TYPE == 'task' :
            resource_dict = self.projman.get_resources_duration_per_task(task.id)
            for r_id, r_usage in resource_dict.iteritems():
                formal_para = self.resource_node(task.id, r_id, r_usage)
                if formal_para:
                    section.appendChild(formal_para)

        # print children
        for each in task.children:
            self._build_task_node(each)
        # close section
        self.tree.pop()

    def resource_node(self, task_id, r_id, usage):
        """ create a DOM node
        <formalpara id=r_id.>
          <title>resource.name</title>
          <para>usage</para>
        </formalpara>
        """
        resource = self.projman.get_resource(r_id)
        formal_para = self.formalpara_node()
        formal_para.setAttributeNS(NO_NS, 'id', task_id+'_'+r_id)
        formal_para.appendChild(self.title_node(resource.name))
        formal_para.appendChild(self.para_node(get_daily_labor(usage)))
        return formal_para

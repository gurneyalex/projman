# -*- coding: utf-8 -*-
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

"""
Validate projman XML formats
"""

# ------------------------------------------------------------
# The following section should be generic enough to go into
# its own library something like logilab.common.xmlcheck
# ------------------------------------------------------------

import mx.DateTime
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET


def any(attrib, attr):
    return ""

def not_empty(attrib, attr):
    if not attrib[attr]:
        return "%s must not be the empty string" % attr
    return ""

def iso_date(dt):
    if len(dt) == 10:
        return mx.DateTime.strptime( dt, "%F" )
    elif len(dt) == 22:
        return mx.DateTime.strptime( dt, "%F %H:%M:%S.%S" )
    else:
        print "date = ", dt, "lg=", len(dt)
        raise RuntimeError("date non valide")

def iso_time(tm):
    date = mx.DateTime.strptime( tm, "%H%M" )
    return mx.DateTime.Time(date.hour, date.minute)

class attribute_checker(object):
    def __call__(self, attrib, attr):
        if attr not in attrib:
            assert RuntimeError("Framework should make sure the attribute is present"
                                "before calling the checker" )
        val = attrib[attr]
        return self.check(attrib, attr, val)

class convertible(attribute_checker):
    def __init__(self, cvt, msg=None):
        self.cvt = cvt
        if msg is None:
            msg = "Cannot convert %%(attr)s:%%(val)r using %s" % cvt
        self.msg = msg

    def check(self, attrib, attr, val):
        try:
            self.cvt(val)
        except:
            
            return self.msg % {'attr':attr, 'val':val}

class depends(object):
    def __init__(self, *attrs):
        self.attrs = attrs

    def __call__(self, attrib, attr):
        if attr not in attrib:
            assert RuntimeError("Framework should make sure the attribute is present"
                                "before calling the checker" )
        # check for the other attributes to be present with this one
        for a in self.attrs:
            if a not in attrib:
                return "%s must be specified along with : %s" % (attr, ", ".join(self.attrs))
        return None

class matches(attribute_checker):
    def __init__(self, txt):
        import re
        self.txt = txt
        self.re = re.compile(txt)

    def check(self, attrib, attr, val):
        if not self.re.search(val):
            return "attribute %s does not match %r" % (attr, self.txt)

class one_of(attribute_checker):
    def __init__(self, *args):
        self.values = args

    def check(self, attrib, attr, val):
        if val not in self.values:
            return "attribute %s must be one of %s (not %s)" % (attr, ",".join(self.values), repr(val))

class BaseEtreeChecker(object):
    def __init__(self):
        self._errors = []
        self._stack = []
        self._ignore_children_flag = False

    def _ignore_children(self):
        self._ignore_children_flag = True

    def check(self):
        """Generic validation methods lookup
        overide this if you have special cases
        like a 'check' node or other special chars
        """
        pos, node = self.stack[-1]
        tag = node.tag.replace("-","_")
        checker = getattr(self, "check_"+tag, None)
        self._ignore_children_flag = False
        if checker:
            checker()
        else:
            self._error("Unknown tag %s" % node.tag)
        return self._ignore_children_flag

    def _error(self, msg):
        pos = [ p for p,n in self.stack ]
        pos = [0]+pos[:-1]
        tag = [ n.tag for p,n in self.stack]
        path = "/".join( [ t+"[%s]"%p for t,p in zip(tag,pos) ] )
        self._errors.append( "%s:%s" % (path,msg) )

    def __str__(self):
        return "\n".join(self._errors)

    def validate(self, tree, filename=''):
        """Validate the source file format"""
        self.stack = [ [-1,tree.getroot()] ]
        # Do a DFS exploration so that we always have
        # the stack match the path of the element
        while self.stack:
            pos, node = self.stack[-1]
            if pos==-1: # first visit
                ignore_children = self.check()
                if ignore_children:
                    pos=len(node)

            if pos+1<len(node):
                self.stack[-1][0]+=1
                new_node = node[pos+1]
                self.stack.append( [-1, new_node] )
                continue
            # we finished all children
            self.stack.pop(-1)
        if self._errors:
            return False
        else:
            return True

    # various helpers
    def _isroot(self):
        self._is_child_of( None )

    def _noattr(self):
        pos, node = self.stack[-1]
        if node.attrib:
            self._error( "%s should not have attributes" % node.tag )

    def _is_child_of(self, *parents):
        pos, node = self.stack[-1]
        if len(self.stack)>=2 and self.stack[-2][1].tag not in parents:
            self._error( "%s must be a child of %s" % (node.tag, parents) )
        if len(self.stack)==1 and None not in parents:
            self._error( "%s must be the root node" % node.tag )


    def _attributes(self, attribs):
        pos, node = self.stack[-1]
        attrs = {}
        for name, checkers in attribs.items():
            opt = False
            if name.endswith("?"):
                name = name[:-1]
                opt = True
            attrs[name]=True
            if name not in node.attrib:
                if not opt:
                    self._error("attribute %s is missing" % name)
                continue
            if not isinstance(checkers, (list, tuple)):
                checkers = (checkers,)
            for c in checkers:
                msg = c(node.attrib, name)
                if msg:
                    self._error( msg )
        for name in node.attrib.keys():
            if name not in attrs:
                self._error("unknown attribute '%s'" % name)

    def _parent_node(self):
        if len(self.stack)<=1:
            return ET.Element("")
        return self.stack[-2][1]

    def _children(self, *types):
        pos, node = self.stack[-1]
        children = {}
        for t in types:
            if t[-1] in '?*+':
                t = t[:-1]
            children[t] = 0
        for c in node:
            if c.tag not in children:
                self._error("%s should not have child %s" % (node.tag, c.tag))
            else:
                children[c.tag]+=1
        for t in types:
            if t[-1] in '?*+':
                t0=t[:-1]
            else:
                t0=t
            n = children[t0]
            if t[-1] == '?' and n>1:
                self._error("%s should appear at most once instead of %d" % (t0, n))
            elif t[-1] == '*':
                pass
            elif t[-1] == '+' and n==0:
                self._error("%s should appear at least once instead of %d" % (t0, n))
            elif t[-1] not in '?*+' and n!=1:
                self._error("%s should appear exactly once instead of %d" % (t0, n))

    def _content(self, cvt, msg=None):
        pos, node = self.stack[-1]
        txt = node.text or ""
        if msg is None:
            msg = "%s should convert to %s" % (node.tag,cvt)
        for c in node:
            txt += c.tail or ""
        try:
            cvt(txt.strip())
        except:
            self._error(msg % {'txt':repr(txt)})
            import traceback
            traceback.print_exc()
            
    def _empty(self):
        pos, node = self.stack[-1]
        def isempty(txt):
            assert txt==""
        self._content(isempty, "should not have text : %(txt)s")

# -------------------------------------------------------------------------
# The following are checkers that check the validity of projman's project
# files
# -------------------------------------------------------------------------

class ProjectChecker(BaseEtreeChecker):
    def check_project(self):
        self._isroot()
        self._noattr()
        self._empty()
        self._children( "import-tasks",
                            "import-resources",
                            "import-schedule",
                            "import-activities", )
    def check_import_(self):
        self._is_child_of("project")
        self._attributes( { "file": not_empty } )
        self._empty()

    check_import_tasks = check_import_
    check_import_activities = check_import_
    check_import_schedule = check_import_
    check_import_resources = check_import_

DATE_CONSTRAINT = ["begin-at-date", "end-at-date",
                   "begin-after-date", "end-after-date",
                   "begin-before-date", "end-before-date",
                   ]
TASK_CONSTRAINT = ["begin-after-end", "end-after-end",
                   "begin-after-begin", "end-after-begin",
                   "synchronized",]

class ScheduleChecker(BaseEtreeChecker):
    def check_schedule(self):
        self._isroot()
        self._noattr()
        self._children( "task+", "milestone*" )

    def check_task(self):
        self._is_child_of("schedule")
        self._attributes( {"id": not_empty} )
        pos, node = self.stack[-1]
        self._children("costs_list", "report-list",
                       "global-cost", "constraint-date*",
                       "status", "constraint-task*")

    def check_constraint_date(self):
        self._is_child_of("task","milestone")
        self._children()
        if self._parent_node().tag == "milestone":
            self._attributes( {"type" : one_of("at-date") } )
        else:
            self._attributes( {"type" : one_of(*DATE_CONSTRAINT)} )
        self._content( iso_date )
        
    def check_constraint_task(self):
        self._empty()
        self._children()
        self._attributes( {"type": one_of(*TASK_CONSTRAINT),
                           "idref": not_empty} )

    def check_status(self):
        self._content( str )
        self._children()
        self._noattr()

    def check_report(self):
        self._children()
        self._empty()
        self._attributes( {"usage": convertible(float),
                           "to":  convertible(iso_date),
                           "idref": any,
                           "from": convertible(iso_date)} )
    def check_cost(self):
        self._children()
        self._content( float )
        self._attributes( {"idref" : not_empty} )
    def check_global_cost(self):
        self._children()
        self._content( float )
        self._attributes( {"unit": any} )
    def check_priority(self):
        self._error("TODO")
    def check_costs_list(self):
        self._empty()
        self._noattr()
        self._children( "cost+" )
    def check_report_list(self):
        self._empty()
        self._noattr()
        self._children( "report+" )
    def check_milestone(self):
        self._is_child_of('schedule')
        self._empty()
        self._attributes({"id": not_empty})
        self._children('constraint-date', 'constraint-task*')

class ResourcesChecker(BaseEtreeChecker):
    def check_resources_list(self):
        self._isroot()
        self._attributes( { "id?" : not_empty } )
        self._children("resource+","calendar+","resource-role*")
        self._empty()
        
    def check_resource(self):
        self._is_child_of( "resources-list" )
        self._children("label","use-calendar","hourly-rate?", "role*")
        self._empty()
        self._attributes( {"type?" : not_empty,
                           "id" : not_empty,} )

    def check_label(self):
        self._children()
        self._noattr()
        self._is_child_of("resource","resource-role","calendar","day-type")
        self._content( unicode )

    def check_role(self):
        self._children()
        self._empty()
        self._is_child_of("resource")
        self._attributes({'idref' : not_empty})

    def check_use_calendar(self):
        self._children()
        self._empty()
        self._is_child_of( "resource" )
        self._attributes( {"idref": not_empty} )

    def check_hourly_rate(self):
        self._children()
        self._content( float )
        self._is_child_of( "resource" )
        self._attributes( {"unit?": one_of("euros")} )

    def check_resource_role(self):
        self._is_child_of( "resources-list" )
        self._children("label")
        self._empty()
        self._attributes( {"id" : not_empty,
                           "hourly-cost" : convertible(float),
                           "cost-unit?" : one_of("EUR")} )

    def check_calendar(self):
        self._is_child_of( "calendar", "resources-list" )
        self._empty()
        self._attributes( {"id": not_empty} )
        self._children("calendar*", "label","day-types?","day*",
                       "timeperiod*", "start-on?", "stop-on?")

    def check_day_types(self):
        self._is_child_of("calendar")
        self._empty()
        self._children( "day-type+" )
        self._attributes( {"default": not_empty})

    def check_day_type(self):
        self._is_child_of("day-types")
        self._children( "label","interval*" )
        self._empty()
        self._attributes( {"id": not_empty} )

    def check_interval(self):
        self._is_child_of("day-type")
        self._empty()
        self._children()
        self._attributes( {"start": convertible(iso_time),
                           "end": convertible(iso_time)} )

    def check_day(self):
        self._is_child_of("calendar")
        self._content(str)
        self._children()
        self._attributes( {"type": not_empty} )

    def check_timeperiod(self):
        self._is_child_of("calendar")
        self._empty()
        self._children()
        self._attributes( {"to": convertible(iso_date),
                           "from": convertible(iso_date),
                           "type": not_empty} )

    def check_start_on(self):
        self._is_child_of("calendar")
        self._content(iso_date)
        self._children()
        self._noattr()

    def check_stop_on(self):
        self._is_child_of("calendar")
        self._content(iso_date)
        self._children()
        self._noattr()
    
class TasksChecker(BaseEtreeChecker):
    def check_task(self):
        self._is_child_of("task",None)
        self._attributes( {"id":not_empty,
                           "load-type?":(one_of("oneof","shared","sameforall","spread"),
                                         depends("load") ),
                           "load?":(convertible(float),
                                    depends("load-type")),
                           "resource-role?" : not_empty,
                           } )
        self._empty()
        pos, node = self.stack[-1]
        if node.findall("task") or node.findall("milestone"):
            # a task with sub-tasks
            self._children("label", "link?", "description?","constraint-date*",
                           "constraint-resource*","constraint-task*",
                           "task*", "milestone*")
        else:
            # a leaf task
            pos, node = self.stack[-1]
            # we don't want duration with the new load-type descriptions
            self._children("label", "link?", "description?","constraint-date*",
                           "constraint-resource*","constraint-task*",
                           "constraint-interruptible?")
            
    def check_milestone(self):
        self._is_child_of( "task" )
        self._attributes( {"id":not_empty} )
        self._empty()
        self._children("label","description?","constraint-date*",
                       "constraint-task*")

    def check_description(self):
        self._is_child_of("task","milestone")
        self._attributes( {"format?" : one_of("rest","docbook")} )
        self._content(unicode)
        self._ignore_children()

    def check_label(self):
        self._is_child_of("task","milestone")
        self._content(unicode)
        self._noattr()
        self._children()

    def check_link(self):
        self._is_child_of('task', 'milestone')
        self._empty()
        self._attributes({'url' : not_empty})
        self._children()

    def check_constraint_date(self):
        self._is_child_of("task","milestone")
        self._content(iso_date)
        self._attributes( {"type" : one_of(*DATE_CONSTRAINT),
                           "priority?": one_of('1','2','3')} )
        self._children()

    def check_constraint_task(self):
        self._is_child_of("task","milestone")
        self._empty()
        self._attributes( {"type" : one_of(*TASK_CONSTRAINT),
                          "idref" : not_empty,
                          "priority?": one_of('1','2','3') } )
        self._children()

    def check_constraint_resource(self):
        self._is_child_of("task","milestone")
        self._empty()
        self._attributes( {"idref" : not_empty,
                           "usage?" : not_empty,
                           "type?" : not_empty} )
        self._children()

    def check_constraint_interruptible(self):
        self._is_child_of("task","milestone")
        self._empty()
        self._attributes( { "type" : one_of('True', 'False'),
                            "priority" : one_of('1', '2', '3')})

class ActivitiesChecker(BaseEtreeChecker):
    def check_activities(self):
        self._isroot()
        self._empty()
        self._attributes( {"id": not_empty} )
        self._children("reports-list*")

    def check_reports_list(self):
        self._is_child_of("activities")
        self._empty()
        self._attributes( {"task-id": not_empty} )
        self._children("report+")

    def check_report(self):
        self._is_child_of("reports-list")
        self._empty()
        self._attributes({"idref":not_empty,
                          "from":convertible(iso_date),
                          "to":convertible(iso_date),
                          "usage":convertible(float)})
        self._children()

# -*- coding: iso-8859-1 -*-
"""
unit tests for module projman.lib.Project

Projman - (c)2000-2002 LOGILAB <contact@logilab.fr> - All rights reserved.
Home: http://www.logilab.org/projman

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

from mx.DateTime import now

from logilab.common import testlib

from projman.lib import MileStone, Task, Project, ResourcesSet, \
     Resource

class ProjectTC(testlib.TestCase):

    def setUp(self):
        """called before each test from this class

        parent (inge1/1, inge2/1)
          |
          |--- child1 (inge1/1), 10
          |
          |--- child2
          |      |
          |      |--- child2_1 (inge1/0.6), 5 
          |      |
          |      `--- child2_2 (inge2/1), 12
          |
          `--- stone [milestone]
        """
        self.parent = Task('parent')
        self.child1 = Task('child1')
        self.child2 = Task('child2')
        self.child2_1 = Task('child2_1')
        self.child2_2 = Task('child2_2')
        self.stone = MileStone('stone')
        # building tree
        self.parent.append(self.child1)
        self.parent.append(self.child2)
        self.child2.append(self.child2_1)
        self.child2.append(self.child2_2)
        self.parent.append(self.stone)
        # set duration
        self.child1.duration = 10
        self.child2_1.duration = 5
        self.child2_2.duration = 12
        # set of resources constraints
        self.parent.add_resource_constraint('worker', 'inge1')
        self.parent.add_resource_constraint('worker', 'inge2')
        self.child1.add_resource_constraint('worker', 'inge1')
        self.child2_1.add_resource_constraint('worker', 'inge1')
        self.child2_2.add_resource_constraint('worker', 'inge2')
        # create project
        self.project = Project()
        self.project.root_task = self.parent


    def test_project(self):
        self.assertEquals(self.project.root_task, self.parent)
        self.assertEquals(self.project.get_task('child2_2'), self.child2_2)

    def test_project_errors(self):
        """tests inconsistent projects"""
        # expliclity add duplicate node id
        self.parent.append(Task('child1'))
        self.project.root_task = self.parent
        self.assertEquals(self.project.check_consistency(), ['Duplicate task id: child1'])

    def _test_schedule(self):
        pass

    def test_resources(self):
        # build resources
        jean = Resource('inge1', 'Jean')
        paul = Resource('inge2', 'Paul')
        resource_set = ResourcesSet('rset')
        resource_set.append(jean)
        resource_set.append(paul)
        self.project.resource_set = resource_set
        # test setters & getters
        self.assertEquals(self.project.has_resource('inge1'), True)
        self.assertEquals(self.project.has_resource('Jean'), False)
        self.assertEquals(self.project.get_resource('inge1'), jean)
        self.assertEquals(self.project.get_resources(), ['inge1', 'inge2'])
    
    def test_tasks(self):
        self.assertEquals(self.project.get_task('stone'), self.stone)
        self.assertEquals(self.project.get_nb_tasks(), 6)
        self.assertEquals(self.project.is_in_allocated_time('child1', now()), False)

    def _test_activities(self):
        pass
    
    def _test_usage(self):
        pass
    
    def _test_total_usage(self):
        pass

    def _test_resources_disponibility(self):
        pass

    def _test_task_date_range(self):
        pass
    
    def _test_duration_worked_for(self):
        pass

    def _test_task_cost(self):
        pass

    

if __name__ == '__main__':
    testlib.unittest_main()


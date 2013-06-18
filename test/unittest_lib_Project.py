# -*- coding: iso-8859-1 -*-
"""
unit tests for module projman.lib.Project

Projman - (c)2000-2013 LOGILAB <contact@logilab.fr> - All rights reserved.
Home: http://www.logilab.org/projman

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

from mx.DateTime import now

from logilab.common import testlib

from projman.lib import MileStone, Task, Project, Resource
from projman.lib.resource_role import ResourceRole
from projman.lib.calendar import Calendar
from projman.lib._exceptions import ProjectValidationError

def simple_project():
    """build a simple project for testing the Project class

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
          `--- stone [milestone]"""
    # create project
    project = Project()
    # create tasks
    project.root_task = parent = Task('parent')
    child1 = Task('child1')
    child2 = Task('child2')
    child2_1 = Task('child2_1')
    child2_2 = Task('child2_2')
    stone = MileStone('stone')
    project.milestones['stone'] = stone
    # building tree
    parent.append(child1)
    parent.append(child2)
    child2.append(child2_1)
    child2.append(child2_2)
    parent.append(stone)
    # set duration
    child1.duration = 10
    child2_1.duration = 5
    child2_2.duration = 12
    # calendar
    calendar = Calendar('typic', 'Typical Calendar')
    project.calendars['typic'] = calendar
    cdp = ResourceRole('cdp', 'Chef', 100.0, 'EUR')
    ingpy = ResourceRole('ingpy', 'Python Developper', 80.0, 'EUR')
    ingihm = ResourceRole('ingihm', 'Human Interface Ingineer', 70.0, 'EUR')
    toto = Resource('toto', 'Mike', calendar, [cdp, ingpy])
    tata = Resource('tata', 'Mila', calendar, [ingpy, ingihm])
    project.resources_roles = dict(cdp=cdp, ingpy=ingpy, ingihm=ingihm)
    roles = (cdp, ingpy, ingihm)
    project.resources['toto'] = toto
    project.resources['tata'] = tata
    resources = (tata, toto)
    tasks = (parent, child1, child2, child2_1, child2_2)
    return project, tasks, resources, roles, stone, calendar


class ProjectTC(testlib.TestCase):

    def setUp(self):
        """setup a simple project for each test"""
        project, tasks, resources, roles, stone, calendar = simple_project()
        self.project = project
        self.roles = roles
        self.resources = resources
        self.calendar = calendar
        self.parent = tasks[0]
        self.child1 = tasks[1]
        self.child2 = tasks[2]
        self.child2_1 = tasks[3]
        self.child2_2 = tasks[4]
        self.stone = stone

    def test_project(self):
        self.assertEqual(self.project.root_task, self.parent)

    def test_project_errors(self):
        """tests inconsistent projects"""
        # expliclity add duplicate node id
        self.parent.append(Task('child1'))
        self.assertEqual(self.project.check_consistency(), ['Duplicate task id: child1'])

    def test_resources(self):
        """test setters & getters of resources"""
        self.assertEqual(self.project.has_resource('toto'), True)
        self.assertEqual(self.project.has_resource('Mike'), False)
        self.assertItemsEqual(self.project.get_resources(), self.resources)
        toto = self.resources[1]
        self.assertEqual(self.project.get_resource('toto'), toto)
        jean = Resource('jojo', 'Jean', self.calendar, self.roles)
        self.project.add_resource(jean)
        self.assertEqual(self.project.has_resource('jojo'), True)
        self.assertEqual(self.project.has_resource('Jean'), False)
        self.assertRaises(ProjectValidationError, self.project.add_resource, jean)

    def test_tasks(self):
        self.assertEqual(self.project.get_nb_tasks(), 6)
        self.assertEqual(self.project.is_in_allocated_time('child1', now()), False)

    def test_calendars(self):
        """test setters & getters of calendars"""
        self.assertEqual(self.project.get_calendar('typic'), self.calendar)
        cal = Calendar('atypic_be', 'Belgium Atypic Calendar')
        self.project.add_calendar(cal)
        self.assertTrue(self.project.has_calendar('atypic_be'))
        self.assertFalse(self.project.has_calendar('typic_fx'))

    def test_get_role(self):
        cdp = self.roles[0]
        self.assertEqual(cdp.id, 'cdp')
        self.assertEqual(self.project.get_role('cdp'), cdp)
        cwd = ResourceRole('cwd', 'CubicWeb Developper')
        self.project.add_role(cwd)
        self.assertEqual(self.project.get_role('cwd'), cwd)
        self.assertRaises(ProjectValidationError, self.project.add_role, cwd)

    def test_get_task(self):
        self.assertEqual(self.project.get_task('stone'), self.stone)
        self.assertEqual(self.project.get_task('parent'), self.parent)
        self.assertEqual(self.project.get_task('child2_2'), self.child2_2)


if __name__ == '__main__':
    testlib.unittest_main()

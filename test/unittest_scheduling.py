"""
Projman - (c)2000-2006 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projects/projman

This code is released under the GNU Public Licence v2. See www.gnu.org.

"""
from pprint import pprint
import sys
import os.path as osp

from logilab.common.testlib import unittest_main, TestCase
from logilab.common.compat import set
from projman.lib import *
from projman.scheduling import schedule
from projman.scheduling.simple import SimpleScheduler, cmp_tasks
from projman.scheduling.csp import *
from projman.readers import ProjectXMLReader
from mx.DateTime import DateTime,  Time

def print_solutions(solutions):
    for s in solutions:
        pprint(s)

DATADIR = osp.abspath(osp.join(osp.dirname(__file__), "data"))

class RawSchedulingTC(TestCase):

    def test_solve_simple(self):
        self.skip()
        # 2 tasks, no time -> no solution        
        variables = []
        domains = {}
        constraints = []
        for i in range(2):
            name = 't%02d' % i
            variables.append(name)
            domains[name] = SchedulingDomain(0, 2, 2)

        constraints.append(fi.NoOverlap('t00', 't01'))

        repo = Repository(variables, domains, constraints)
        solver = Solver(SchedulingDistributor())
        solutions = solver.solve(repo, verbose=0)
        #print_solutions(solutions)
        self.assertEquals(len(solutions), 0)

    def test_solve_harder(self):
        self.skip()
        variables = []
        domains = {}
        constraints = []
        for i in range(2):
            name = 't%02d' % i
            variables.append(name)
            domains[name] = SchedulingDomain(0, 4, 2)

        constraints.append(fi.NoOverlap('t00', 't01'))
        constraints.append(fi.StartsAfterEnd('t01', 't00'))

        repo = Repository(variables, domains, constraints)
        solver = Solver(SchedulingDistributor())
        solutions = solver.solve(repo, verbose=0)
        #print_solutions(solutions)
        self.assertEquals(len(solutions), 1)

    def test_solve_harder2(self):
        self.skip()
        variables = []
        domains = {}
        constraints = []
        for i in range(2):
            name = 't%02d' % i
            variables.append(name)
            domains[name] = SchedulingDomain(0, 4, 2)
        variables.append("t02")
        domains['t02'] = SchedulingDomain(0, 6, 2)
        constraints.append(fi.NoOverlap('t00', 't01'))
        constraints.append(fi.NoOverlap('t00', 't02'))
        constraints.append(fi.NoOverlap('t02', 't01'))
        constraints.append(fi.StartsAfterEnd('t02', 't00'))
        constraints.append(fi.StartsAfterEnd('t02', 't01'))

        repo = Repository(variables, domains, constraints)
        solver = Solver(SchedulingDistributor())
        solutions = solver.solve(repo, verbose=0)
        #print_solutions(solutions)
        self.assertEquals(len(solutions), 2)



class CSPSchedulerTC(TestCase):

    def skipped_setUp(self):
        filename = osp.join(DATADIR, "csp_scheduling_projman.xml")
        reader = ProjectXMLReader(filename)
        self.project, files = reader.read()

        
    def test_visit(self):
        self.skip()
        scheduler = CSPScheduler(self.project)
        scheduler.schedule()
        self.assertEquals(len(scheduler.variables), 4)
        self.assertEquals(len(scheduler.domains), 4)
        expected_constraints = set([
            fi.StartsAfterEnd(u't2_2', u't2_11'),
            fi.StartsAfterEnd(u't2_2', u't2_12'),
            fi.StartsAfterEnd(u't2_3', u't2_2'),
            fi.NoOverlap(u't2_2', u't2_12'),
            ])
        self.assertEquals(expected_constraints, scheduler.constraints)


class CmpTasksTC(TestCase):
        
    def test_cmp(self):
        self.skip()
        t0 = Task('0')
        t1 = Task('1')
        self.assertEquals( cmp_tasks(t0,None),  1)
        t1.add_task_constraint('begin-after-end', '0')
        self.assertEquals( cmp_tasks(t0,t1),  -1)

    def test_cmp2(self):
        self.skip()
        t0 = Task('0')
        t1 = Task('1')
        self.assertEquals( cmp_tasks(t0,None),  1)
        t0.priority = 2
        self.assertEquals( cmp_tasks(t0,t1),  -1)
        t1.priority = 1
        self.assertEquals( cmp_tasks(t0,t1),  1)
        t0.priority = 1
        self.assertEquals( cmp_tasks(t0,t1),  0)

        
class SimpleSchedulerTC(TestCase):

    def skipped_setUp(self):
        filename = osp.join(DATADIR, "csp_scheduling_projman.xml")
        reader = ProjectXMLReader(filename)
        self.project, files = reader.read()
        
    def test_visit1(self):
        self.skip()
        scheduler = SimpleScheduler(self.project)
        ordered_buckets = scheduler.get_ordered_buckets()
        self.assertEquals(len(ordered_buckets), 3)
        self.assertEquals(len(ordered_buckets[0]), 2)
        self.assertEquals(len(ordered_buckets[1]), 1)
        self.assertEquals(len(ordered_buckets[2]), 1)

    def skip_test_visit2(self):
        self.skip()
        scheduler = SimpleScheduler(self.project)
        scheduler.schedule()

if __name__ == '__main__':
    print "bob"
    unittest_main()
    print "is not dead"

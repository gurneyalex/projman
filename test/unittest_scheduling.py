"""
Projman - (c)2000-2005 LOGILAB <contact@logilab.fr> - All rights reserved.

Home: http://www.logilab.org/projects/projman

This code is released under the GNU Public Licence v2. See www.gnu.org.

"""
__revision__ = "$Id: unittest_scheduling.py,v 1.14 2005-09-07 23:51:01 nico Exp $"

from pprint import pprint
import unittest
import sys

from logilab.common.compat import set
from projman.lib import *
from projman.interface.file_manager import ProjectStorage
from projman.scheduling import schedule
from projman.scheduling.simple import SimpleScheduler, cmp_tasks
from projman.scheduling.csp import *
from mx.DateTime import DateTime,  Time

def print_solutions(solutions):
    for s in solutions:
        pprint(s)

class RawSchedulingTC(unittest.TestCase):

    def test_solve_simple(self):
        # 2 tasks, no time -> no solution        
        variables = []
        domains = {}
        constraints = []
        for i in range(2):
            name = 't%02d'%i
            variables.append(name)
            domains[name] = SchedulingDomain(0, 2, 2)

        constraints.append(fi.NoOverlap('t00', 't01'))

        repo = Repository(variables, domains, constraints)
        solver = Solver(SchedulingDistributor())
        solutions = solver.solve(repo, verbose=0)
        #print_solutions(solutions)
        self.assertEquals(len(solutions), 0)

    def test_solve_harder(self):
        variables = []
        domains = {}
        constraints = []
        for i in range(2):
            name = 't%02d'%i
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
        variables = []
        domains = {}
        constraints = []
        for i in range(2):
            name = 't%02d'%i
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



class CSPSchedulerTC(unittest.TestCase):

    def setUp(self):
        self.project = ProjectStorage("data", "csp_scheduling_projman.xml",
                                      archive_mode=False).load()
        
    def test_visit(self):
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


class CmpTasksTC(unittest.TestCase):
        
    def test_cmp(self):
        t0 = Task('0')
        t1 = Task('1')
        assert cmp_tasks(t0,None) == 1
        t1.add_task_constraint('begin-after-end', '0')
        assert cmp_tasks(t0,t1) == -1
        
class SimpleSchedulerTC(unittest.TestCase):

    def setUp(self):
        self.project = ProjectStorage("data", "csp_scheduling_projman.xml",
                                      archive_mode=False).load()
        
    def test_visit1(self):
        scheduler = SimpleScheduler(self.project)
        ordered_buckets = scheduler.get_ordered_buckets()
        self.assertEquals(len(ordered_buckets), 3)
        self.assertEquals(len(ordered_buckets[0]), 2)
        self.assertEquals(len(ordered_buckets[1]), 1)
        self.assertEquals(len(ordered_buckets[2]), 1)

    def test_visit2(self):
        scheduler = SimpleScheduler(self.project)
        scheduler.schedule()

if __name__ == '__main__':
    unittest.main()

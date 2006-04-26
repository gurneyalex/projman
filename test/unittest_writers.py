"""
unit tests for module projman.writers.task_costs

Projman - (c)2000-2002 LOGILAB <contact@logilab.fr> - All rights reserved.
Home: http://www.logilab.org/projman

This code is released under the GNU Public Licence v2. See www.gnu.org.
"""

__revision__ = "$Id: unittest_writers.py,v 1.3 2005-11-10 11:34:23 arthur Exp $"

from os.path import join
import unittest

from logilab.common.testlib import TestCase


from projman.interface.option_manager import create_option_manager

class WriterTestCase(TestCase):
    """
    provides utility function.
    """
    def check_result(self, input, reference, output="output.xml"):
        """executes projman and compare result with expected one

        projman processes <input> and generates <output>
        <output> will be compared to <reference>
        """
        self.assertNotEqual(input, None)
        self.assertNotEqual(output, None)
        self.assertNotEqual(reference, None)
        input = join('data', input)
        output = join('generated', output)
        reference = join('data', reference)
        option = create_option_manager(self.cmd, [input, output])
        option.get_command().execute()
        self.assertFileEqual(reference, output)


class WriterTest(WriterTestCase):
    """Test all low-level function on Milestones."""
    def setUp(self):
        self.cmd = [("-x", None),
                    ("-X", None)]
        
    def test_options(self):
        self.cmd += [("--display-cost", None), ("--display-duration", None),
                     ("--display-rates", None)]
        self.check_result(input='simplest_scheduled_projman.xml',
                          output='test_options.xml',
                          reference='out_options.xml')


## Dates #############################################################

class DatesWriterTC(WriterTestCase):
    """Test all low-level function on Milestones.
    """
    def setUp(self):
        """ called before each test from this class """
        self.cmd = [("--xml-doc", None),
                    ("-X", None),
                    ("--view", "date")]
        
    def test_simple(self):
        """check that finds child"""
        self.check_result(input='simplest_scheduled_projman.xml',
                          output='test_simplest_dates.xml',
                          reference='out_simplest_dates.xml')
        
    def test_trivial(self):
        """check that finds child"""
        self.check_result(input="trivial_scheduled_projman.xml",
                          output="test_trivial_dates.xml",
                          reference="out_trivial_dates.xml")
        
    def test_full(self):
        """check that finds child"""
        self.check_result(input="full_scheduled_projman.xml",
                          output="test_full_dates.xml",
                          reference="out_full_dates.xml")


## Listss #############################################################
    
class ListWriterTC(WriterTestCase):

    def setUp(self):
        """ called before each test from this class """
        self.cmd = [("--xml-view", None),
                    ("-X", None),
                    ("--view","list")]
        
    def test_simple(self):
        self.check_result(input="simplest_scheduled_projman.xml",
                          output="test_simplest_list.xml",
                          reference="out_simplest_list.xml")
        
    def test_trivial(self):
        self.check_result(input="trivial_scheduled_projman.xml",
                          output="test_trivial_list.xml",
                          reference="out_trivial_list.xml")
        
    def test_full(self):
        self.check_result(input="full_scheduled_projman.xml",
                          output="test_full_list.xml",
                          reference="out_full_list.xml")


## Costs #############################################################

class CostsWriterTC(WriterTestCase):
    def setUp(self):
        """ called before each test from this class """
        self.cmd = [("-x", None),
                    ("-X", None),
                    ("-v", "cost")]
        
    def test_simple(self):
        self.check_result(input="simplest_scheduled_projman.xml",
                          output="test_simplest_costs.xml",
                          reference="out_simplest_costs.xml")
        
    def test_trivial(self):
        self.check_result(input="trivial_scheduled_projman.xml",
                          output="test_trivial_costs.xml",
                          reference="out_trivial_costs.xml")
        
    def test_full(self):
        self.check_result(input="full_scheduled_projman.xml",
                          output="test_full_costs.xml",
                          reference="out_full_costs.xml")





if __name__ == '__main__':
    unittest.main()


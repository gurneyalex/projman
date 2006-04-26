__revision__ = "$Id: applicationtest.py,v 1.6 2005-09-06 18:27:44 nico Exp $"

import unittest
import sys
from xml.dom.ext import PrettyPrint
from projman.readers.base_reader import AbstractXMLReader
from projman.readers.planner_reader import PlannerXMLReader
from projman.lib.xmlutils import as_xml_string

class ApplicationTest(unittest.TestCase):
    
    def test_import_from_planner(self):
        reader = PlannerXMLReader()
        rs = reader.fromFile('data/planner_description.mrproject')
        del reader
        # resources set object associated to xml planner
        xml_rs = as_xml_string(rs[0], pretty=1).strip()
        # project object associated to xml planer
        xml_p = as_xml_string(rs[1], pretty=1).strip()
        file_r = open('data/result_res_attendu', 'w')
        file_p = open('data/result_proj_attendu', 'w')
        file_r.write(xml_rs)
        file_p.write(xml_p)
        initial_xml_resources = open('data/resources_description.xml').read().strip()
        initial_xml_project = open('data/project_description.xml').read().strip()
        if xml_p != initial_xml_project:
            f = open('data/project_description.xml.cmp', 'w')
            f.write(xml_p)
            f.close()
            self.assertEqual(0, 1, 'imported project != exported project set\n look at data/project_description.xml and data/project_description.xml.cmp')
        if xml_rs != initial_xml_resources:
            f = open('data/resources_description.xml.cmp', 'w')
            f.write(xml_rs)
            f.close()
            self.assertEqual(0, 1, 'imported resources set != exported resources set\n look at data/resources_description.xml and data/resources_description.xml.cmp')

def suite():
    """return the unitest suite"""
    loader = unittest.TestLoader()
    module = sys.modules[__name__]
    if __name__ == '__main__' and len(sys.argv) > 1:
        return loader.loadTestsFromNames(sys.argv[1:], module)
    return loader.loadTestsFromModule(module)

def Run(runner=None):
    """run tests"""
    testsuite = suite()
    if runner is None:
        runner = unittest.TextTestRunner()
        # uncomment next line to write tests results in a file
        #runner.__init__(open('tests.log','w+'))    
    return runner.run(testsuite)
        
if __name__ == '__main__':
    Run()
    #unittest.main()

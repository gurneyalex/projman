# -*- coding: iso-8859-1 -*-

import os, sys
import os.path as osp

from logilab.common.testlib import unittest_main, TestCase

def SmokeTC(TestCase):
    CMD = 'projman'

    ## RESULT_DIR contiendra tous les fichiers et images g�n�r�s lors des tests
    RESULT_DIR = 'smoke_result'

    ## FILE est l'input � utiliser pour le cas simple
    FILE = 'pygantt/ginco_planif.xml'
    #FILE = 'pygantt/pygantt_planif.xml'
    #FILE = 'pygantt/projman_planif.xml'

    ## FILE_ASSEMBLAGE est un input utlisant l'assemblage de projets
    FILE_ASSEMBLAGE = 'projman/example.xml'

    def setUp(self):
        # check that path specified might be ok
        dir = os.path.abspath(sys.argv[1])
        os.chdir(dir)
        list_dirs = os.listdir('.')
        if 'pygantt' not in list_dirs or 'projman' not in list_dirs:
            print "ERROR:"
            print "You must specify as parameter the root directory of all examples."
            print "Tipically, ~/cvs/public/soft/projman/examples"
            sys.exit()

        ## create dir for output
        if RESULT_DIR not in list_dirs:
            print "creating directory", RESULT_DIR, "for resulting files"
            os.mkdir(RESULT_DIR)

        ## change dir to output
        os.chdir(dir + '/' + RESULT_DIR)

    def ask_ok(self) :
        r = raw_input('ok [Y]/No ?')
        if r.lower() in ('n', 'no') :
            sys.exit()

    def test_conversion(self):
        "conversion pygantt / planner...",
        os.system(CMD + ' --convert -i pygantt -o planner ../'+ FILE +' toto.xml')
        os.system('planner toto.xml')
        self.ask_ok()

    def test_conversion2(self):
        "conversion pygantt / projman..."
        os.system(CMD+' --convert -i pygantt ../'+ FILE +' proj.xml')
        self.ask_ok()

    def test_gantt(self):
        "diagramme gantt..."
        os.system(CMD+' --diagram --diagram-type gantt --timestep 7 proj.xml gantt.png')
        os.system('display gantt.png')
        self.ask_ok()

    def test_ressources(self):
        "diagramme ressources..."
        os.system(CMD+' --diagram --diagram-type resources --timestep 7 proj.xml resource.png')
        os.system('display resource.png')
        self.ask_ok()

    def test_gantt_ressources(self):
        "diagramme gantt+ressources..."
        os.system(CMD+' --diagram --diagram-type gantt-resources --timestep 7 proj.xml gantt-resource.png')
        os.system('display gantt-resource.png')
        self.ask_ok()

    def test_ordonnancement(self):
        "ordonnancement..."
        os.system(CMD+' --plan --include-references proj.xml plan.xml')
        self.ask_ok()

    def test_gantt2(self):
        "diagramme gantt..."
        os.system(CMD+' --diagram --diagram-type gantt --timestep 7 proj.xml gantt.png')
        os.system('display gantt.png')
        self.ask_ok()

    def test_gantt_ressources2(self):
        "diagramme gantt+ressources..."
        os.system(CMD+' --diagram --diagram-type gantt-resources --timestep 7 proj.xml gantt-resource.png')
        os.system('display gantt-resource.png')
        self.ask_ok()

    def test_xmldoc(self):
        "xmldoc tasks-lists..."
        os.system(CMD+' --xml-doc --view=tasks-list proj.xml tasks_list.xml')
        self.ask_ok()
        os.system('mkdoc --target=pdf --stylesheet=standard tasks_list.xml')
        os.system('xpdf tasks_list.pdf')

    def test_costs(self):
        "xmldoc tasks-costs..."
        os.system(CMD+' --xml-doc --view=tasks-costs proj.xml tasks_costs.xml')
        self.ask_ok()
        os.system('mkdoc --target=pdf --stylesheet=standard tasks_costs.xml')
        os.system('xpdf tasks_costs.pdf')

    def test_dates(self):
        "xmldoc tasks-dates..."
        os.system(CMD+' --xml-doc --view=tasks-dates proj.xml tasks_dates.xml')
        self.ask_ok()
        os.system('mkdoc --target=pdf --stylesheet=standard tasks_dates.xml')
        os.system('xpdf tasks_dates.pdf')


    def test_conversion3(self):
        "conversion projman assembl�/ planner...",
        os.system(CMD + ' --convert -i projman -o planner ../'+ FILE_ASSEMBLAGE +' toto_a.xml')
        os.system('planner toto_a.0.xml')
        os.system('planner toto_a.1.xml')
        self.ask_ok()

        os.system('cp ../'+FILE_ASSEMBLAGE+' proj.xml')
        os.system('cp ../projman/sub_project.xml sub_project.xml')
        os.system('cp ../projman/example_proj.xml example_proj.xml')
        os.system('cp ../projman/example_res.xml example_res.xml')
        os.system('cp ../projman/example_act.xml example_act.xml')

    def test_gantt4(self):
        "diagramme gantt..."
        os.system(CMD+' --diagram --diagram-type gantt --timestep 7 proj.xml gantt_a.png')
        os.system('display gantt_a.png')
        self.ask_ok()

    def test_ressources3(self):
        "diagramme ressources..."
        os.system(CMD+' --diagram --diagram-type resources --timestep 7 proj.xml resource_a.png')
        os.system('display resource_a.png')
        self.ask_ok()

    def test_gantt_ressources3(self):
        "diagramme gantt+ressources..."
        os.system(CMD+' --diagram --diagram-type gantt-resources --timestep 7 proj.xml gantt-resource_a.png')
        os.system('display gantt-resource_a.png')
        self.ask_ok()

    def test_ordonnancement2(self):
        "ordonnancement..."
        os.system(CMD+' --plan --include-references proj.xml plan.xml')
        self.ask_ok()

    def test_gantt5(self):
        "diagramme gantt..."
        os.system(CMD+' --diagram --diagram-type gantt --timestep 7 proj.xml gantt.png')
        os.system('display gantt.png')
        self.ask_ok()

    def test_gantt6(self):
        "diagramme gantt+ressources..."
        os.system(CMD+' --diagram --diagram-type gantt-resources --timestep 7 proj.xml gantt-resource.png')
        os.system('display gantt-resource.png')
        self.ask_ok()



if __name__ == '__main__':
    unittest_main()

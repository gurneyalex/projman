import os, sys

## changer la commnde en fonction de l'emplacement de projman
#CMD = 'python /home/sand/cvs_work/public/soft/projman/main.py'
CMD = 'projman'

## RESULT_DIR contiendra tous les fichiers et images générés lors des tests
RESULT_DIR = 'smoke_result'

## FILE est l'input à utiliser pour le cas simple
FILE = 'pygantt/ginco_planif.xml'
#FILE = 'pygantt/pygantt_planif.xml'
#FILE = 'pygantt/projman_planif.xml'

## FILE_ASSEMBLAGE est un input utlisant l'assemblage de projets
FILE_ASSEMBLAGE = 'projman/example.xml'

## check that path specified might be ok
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

def ask_ok() :
    r = raw_input('ok [Y]/No ?')
    if r.lower() in ('n', 'no') :
        sys.exit()

# conversion pygantt / planner
print "conversion pygantt / planner...",
os.system(CMD + ' --convert -i pygantt -o planner ../'+ FILE +' toto.xml')
os.system('planner toto.xml')
ask_ok()

## Test pour projet simple
##########################

# conversion pygantt / projman
print "conversion pygantt / projman..."
os.system(CMD+' --convert -i pygantt ../'+ FILE +' proj.xml')
ask_ok()

# generation diagrammes
print "diagramme gantt..."
os.system(CMD+' --diagram --diagram-type gantt --timestep 7 proj.xml gantt.png')
os.system('display gantt.png')
ask_ok()

print "diagramme ressources..."
os.system(CMD+' --diagram --diagram-type resources --timestep 7 proj.xml resource.png')
os.system('display resource.png')
ask_ok()

print "diagramme gantt+ressources..."
os.system(CMD+' --diagram --diagram-type gantt-resources --timestep 7 proj.xml gantt-resource.png')
os.system('display gantt-resource.png')
ask_ok()

# ordonnancement automatique
print "ordonnancement..."
os.system(CMD+' --plan --include-references proj.xml plan.xml')
ask_ok()

print "diagramme gantt..."
os.system(CMD+' --diagram --diagram-type gantt --timestep 7 proj.xml gantt.png')
os.system('display gantt.png')
ask_ok()

print "diagramme gantt+ressources..."
os.system(CMD+' --diagram --diagram-type gantt-resources --timestep 7 proj.xml gantt-resource.png')
os.system('display gantt-resource.png')
ask_ok()

# xmldoc
print "xmldoc tasks-lists..."
os.system(CMD+' --xml-doc --view=tasks-list proj.xml tasks_list.xml')
ask_ok()
os.system('mkdoc --target=pdf --stylesheet=standard tasks_list.xml')
os.system('xpdf tasks_list.pdf')

print "xmldoc tasks-costs..."
os.system(CMD+' --xml-doc --view=tasks-costs proj.xml tasks_costs.xml')
ask_ok()
os.system('mkdoc --target=pdf --stylesheet=standard tasks_costs.xml')
os.system('xpdf tasks_costs.pdf')

print "xmldoc tasks-dates..."
os.system(CMD+' --xml-doc --view=tasks-dates proj.xml tasks_dates.xml')
ask_ok()
os.system('mkdoc --target=pdf --stylesheet=standard tasks_dates.xml')
os.system('xpdf tasks_dates.pdf')


## Test pour assemblage de projets
##################################

# conversion projman assemblé / planner
print "conversion projman assemblé/ planner...",
os.system(CMD + ' --convert -i projman -o planner ../'+ FILE_ASSEMBLAGE +' toto_a.xml')
os.system('planner toto_a.0.xml')
os.system('planner toto_a.1.xml')
ask_ok()

os.system('cp ../'+FILE_ASSEMBLAGE+' proj.xml')
os.system('cp ../projman/sub_project.xml sub_project.xml')
os.system('cp ../projman/example_proj.xml example_proj.xml')
os.system('cp ../projman/example_res.xml example_res.xml')
os.system('cp ../projman/example_act.xml example_act.xml')
                                                                                
# generation diagrammes
print "diagramme gantt..."
os.system(CMD+' --diagram --diagram-type gantt --timestep 7 proj.xml gantt_a.png')
os.system('display gantt_a.png')
ask_ok()

print "diagramme ressources..."
os.system(CMD+' --diagram --diagram-type resources --timestep 7 proj.xml resource_a.png')
os.system('display resource_a.png')
ask_ok()

print "diagramme gantt+ressources..."
os.system(CMD+' --diagram --diagram-type gantt-resources --timestep 7 proj.xml gantt-resource_a.png')
os.system('display gantt-resource_a.png')
ask_ok()

# ordonnancement automatique
print "ordonnancement..."
os.system(CMD+' --plan --include-references proj.xml plan.xml')
ask_ok()

print "diagramme gantt..."
os.system(CMD+' --diagram --diagram-type gantt --timestep 7 proj.xml gantt.png')
os.system('display gantt.png')
ask_ok()

print "diagramme gantt+ressources..."
os.system(CMD+' --diagram --diagram-type gantt-resources --timestep 7 proj.xml gantt-resource.png')
os.system('display gantt-resource.png')
ask_ok()




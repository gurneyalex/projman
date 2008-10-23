import sys
from xml.etree import ElementTree as ET

def dict_by(element, key):
    return dict((node.attrib[key], node) 
                for node in element.getiterator()
                if key in node.attrib)

project_resources = ET.parse(sys.argv[1])
pr_by_id = dict_by(project_resources, 'id')
pr_by_idref = dict_by(project_resources, 'idref')
project_tasks = ET.parse(sys.argv[2])
print '''<?xml version='1.0' encoding='UTF-8'?>
<schedule>
'''
for task in project_tasks.getiterator('task'):
    if 'load' not in task.attrib:
        continue
    role = pr_by_id[task.attrib['resource-role']]
    #resource = pr_by_idref[role.attrib['id']].parent
    load = float(task.attrib['load'])
    cost = load * float(role.attrib['hourly-cost']) * 8
    txt = '''<task id='%(id)s'>
    <constraint-date type='begin-at-date'>2000-09-07</constraint-date>
    <constraint-date type='end-at-date'>2000-09-07</constraint-date>
    <status>todo</status>
    <global-cost unit='XXX'>%(globalcost)s</global-cost>
    <costs_list>
      <cost idref='%(res_id)s'>%(cost)s</cost>
    </costs_list>
    <report-list>
      <report usage='%(load)s' to='2000-09-07' idref='%(res_id)s' from='2000-09-07'/>
    </report-list>
    </task>
    ''' % {'id': task.attrib['id'],
           'load': load,
           'globalcost': cost,
           'cost': cost,
           'res_id': 'ing_1', #resource.attrib['id']
           }
    if '-d' in sys.argv:
        print dir(task)
    else:
        print txt

print '''
</schedule>
'''

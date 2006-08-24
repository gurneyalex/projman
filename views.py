# -*- coding: ISO-8859-1 -*-

from xml.dom.minidom import DOMImplementation, parseString
from logilab.common.compat import set

from projman import format_monetary

# dom utilities ################################################################

DOMIMPL = DOMImplementation()
NO_NS = None

def document(root=None):
    """return a DOM document node"""
    return DOMIMPL.createDocument("http://www.logilab.org/2004/Documentor",
                                  root, None)

class DocbookHelper:
    """a helper class to generate docboock"""

    def __init__(self, doc, lang='fr'):
        self._doc = doc
        self.lang = lang
    
    def object_node(self, task_id): 	 
        """create a DOM node <section> with a attribute id"""
        assert isinstance(task_id, basestring)
        node = self._doc.createElementNS(NO_NS, 'dr:object')
        node.setAttributeNS(NO_NS, 'id', task_id)
        node.setAttributeNS(NO_NS, 'lang', self.lang) 
        return node 	 

    def section_node(self, task_id=None): 	 
        """create a DOM node <section> with a attribute id""" 	 
        node = self._doc.createElementNS(NO_NS, 'section')
        if task_id:
            assert isinstance(task_id, basestring)
            node.setAttributeNS(NO_NS, 'id', task_id)
        return node 	 

    def title_node(self, title):
        """create a DOM node <title> title </title> node"""
        assert type(title) is unicode
        node = self._doc.createElementNS(NO_NS, 'title')
        node.appendChild(self._doc.createTextNode(title))
        return node

    def para_node(self, text):
        """create a DOM node <para> text </para> node"""
        assert type(text) is unicode
        node = self._doc.createElementNS(NO_NS, 'para')
        node.appendChild(self._doc.createTextNode(text))
        return node

    def formalpara_node(self):
        """ create a DOM node <formalpara>"""
        return self._doc.createElementNS(NO_NS, 'formalpara')

    def table_node(self):
        """ create a DOM node <table> """
        return self._doc.createElementNS(NO_NS, 'table')

    def table_layout_node(self, nbcols, align='left', colsep=1, rowsep=1,
                          colspecs=None):
        layout = self._doc.createElementNS(NO_NS, 'tgroup')
        layout.setAttributeNS(NO_NS, 'cols', str(nbcols))
        layout.setAttributeNS(NO_NS, 'align', align)
        layout.setAttributeNS(NO_NS, 'colsep', str(colsep))
        layout.setAttributeNS(NO_NS, 'rowsep', str(rowsep))
        if colspecs:
            for i, colspec in enumerate(colspecs):
                layout.appendChild(self.table_colspec_node("c%s"%i, colspec))
        return layout

    def table_colspec_node(self, colname, colwidth):
        """ create a DOM node <colspec> """
        colspec = self._doc.createElementNS(NO_NS, 'colspec')
        colspec.setAttributeNS(NO_NS, 'colname', colname)
        colspec.setAttributeNS(NO_NS, 'colwidth', colwidth)
        return colspec
    
    def table_head_node(self):
        """ create a DOM node <tbody>"""
        return self._doc.createElementNS(NO_NS, 'thead')

    def table_body_node(self):
        """ create a DOM node <tbody>"""
        return self._doc.createElementNS(NO_NS, 'tbody')

    def table_cell_node(self, align='', value=u''):
        """ create a DOM node <entry> """
        entry = self._doc.createElementNS(NO_NS, 'entry')
        if align and value:
            entry.setAttributeNS(NO_NS, 'align', align)
            entry.appendChild(self._doc.createTextNode(value))
        return entry
    
    def list_node(self):
        """ create a DOM node <itemizedlist>"""
        return self._doc.createElementNS(NO_NS, 'itemizedlist')
    
    def list_item_node(self):
        """ create a DOM node <listitem>"""
        return self._doc.createElementNS(NO_NS, 'listitem')

    def custom_node(self, tag, ns=NO_NS):
        return self._doc.createElementNS(ns, tag)

# other utilities and abstract classes ########################################

# FIXME handle english

TVA = 19.6
EXT_DATE_FORMAT = u'%Y-%m-%d'
DATE_NOT_SPECIFIED = "non spécifié"
TOTAL_DATE = u"L'ensemble du projet se déroule entre le %s et le %s."
TOTAL_DURATION = u"La charge totale du projet se chiffre à %s."
TOTAL_DURATION_UNIT = u"1 jour.homme"
TOTAL_DURATION_UNITS_ROUND = u"%i jours.homme"
TOTAL_DURATION_UNITS = u"%.1f jours.homme"

def get_daily_labor(number):
    """return a string with unit jour(s).homme"""
    if number == 1.: # float not int...
        return TOTAL_DURATION_UNIT
    elif int(number) == number:
        return TOTAL_DURATION_UNITS_ROUND % number
    else:
        return TOTAL_DURATION_UNITS % number

        
class CostData:
    """handle global calculation: cost, duration, ressources' rate
    """

    def __init__(self, projman):
        self.projman = projman
        self.project_cost = 0.0
        self.project_duration = 0.0
        self._used_resources = set()
        self.compute(projman.root_task)
        
    def compute(self, project):
        for task in project.children:
            self._compute(task)
            
    def _compute(self, task, level=0):
        try:
            task_cost = self.projman.get_task_total_cost(task.id)
        except KeyError:
            task_cost = 0
        self.project_cost += task_cost
        # compute global duration
        self.project_duration += task.duration
        # set used_resources for legend
        grouped = self.projman.costs.groupby('task', 'resource')
        # grouped[task.id] is a dictionnary (res_id/rows)
        self._used_resources |= set(grouped.get(task.id, []))
        for each in task.children:
            self._compute(each, level+1)

    def used_resources(self):
        return [self.projman.get_resource(rid) for rid in self._used_resources]

    
class XMLView:
    def __init__(self, config):
        self.config = config

    def unique_id(self, nid):
        # use getattr since not all commands support task-root option
        vtask_root = getattr(self.config, 'task_root', None)
        if vtask_root:
            return '%s-%s' % (vtask_root, nid)
        return nid

    def generate(self, root, projman):
        """return a dr:object node for the rate section view"""
        self._init(root, projman)
        n = self.dbh.object_node(self.unique_id(self.name))
        root.documentElement.appendChild(n)
        for content in self.content_nodes():
            n.appendChild(content)
        return n
    
    def _init(self, root, projman):
        self.projman = projman
        self.dbh = DocbookHelper(root)
        self.cdata = CostData(projman)
        


# actual views ################################################################

class RatesSectionView(XMLView):
    name = 'rates-section'
    
    def content_nodes(self):
        section = self.dbh.section_node(self.unique_id('rate-section'))
        resources = self.cdata.used_resources()
        section.appendChild(self.dbh.title_node(u"Tarifs journaliers"))
        section.appendChild(self.dbh.para_node(u"Coût pour une journée type de travail:"))
        section.appendChild(self.resources_rates(resources))
        return section,

    def resources_rates(self, resources):
        """ create a DOM node <itemizedlist> containing the legend of table"""
        list_items = self.dbh.list_node()
        for resource in resources:
            item = self.dbh.list_item_node()
            r_calendar = resource.get_node_by_id(resource.calendar)
            nb_hours_per_day = float(r_calendar.get_default_worktime() / 3600)
            cost_per_day = resource.hourly_rate[0] * nb_hours_per_day
            r_info = resource.id+' : '+resource.name+' ('+\
                     format_monetary(cost_per_day)+' '\
                     +resource.hourly_rate[1]+')'
            para = self.dbh.para_node(r_info)
            item.appendChild(para)
            list_items.appendChild(item)
        return list_items


class DurationSectionView(XMLView):
    name = 'duration-section'
    
    def content_nodes(self):
        section = self.dbh.section_node(self.unique_id(u"duration-section"))
        section.appendChild(self.dbh.title_node(u"Durée totale"))
        # XXX
        date_begin, date_end = self.projman.get_task_date_range(self.projman.root_task)
        section.appendChild(self.dbh.para_node(
            TOTAL_DATE % (date_begin.strftime(FULL_DATE_FORMAT),
                          date_end.strftime(FULL_DATE_FORMAT))))
        section.appendChild(self.dbh.para_node(
            TOTAL_DURATION %  get_daily_labor(self.project.maximum_duration())))
        return section,

    
class CostTableView(XMLView):
    name = 'cost-table'
    ENTETE = u"Tableau récapitulatif des coûts."
    
    def content_nodes(self):
        """return a dr:object node for the cost table view"""
        table = self.dbh.table_node()
        # fill title
        table.appendChild(self.dbh.title_node(self.ENTETE))
        # fill column information for table
        layout = self.dbh.table_layout_node(4, colspecs=('3*', '1*', '2*', '1*'))
        # table head
        layout.appendChild(self.table_head())
        table.appendChild(layout)
        # table body
        tbody = self.dbh.table_body_node()
        layout.appendChild(tbody)
        for child in self.projman.root_task.children:
            self._build_task_node(tbody, child)
        return table,
    
    def table_head(self):
        """ create a DOM node <thead> """ 
        thead = self.dbh.table_head_node()
        row = self.dbh.custom_node('row')
        row.appendChild(self.dbh.table_cell_node())
        row.appendChild(self.dbh.table_cell_node('left', u'Charge (jours.homme)'))
        row.appendChild(self.dbh.table_cell_node('left', u'Ressources'))
        row.appendChild(self.dbh.table_cell_node('right', u'Coût (euros)'))
        thead.appendChild(row)
        return thead
    
    def _build_task_node(self, tbody, task, level=0):
        """format a task in as a row in the table"""
        try:
            task_cost = self.projman.tasks.get_cell_by_ids(task.id, 'cost') or 0
        except KeyError:
            task_cost = 0
        if task_cost:
            row = self.row_element(task, task_cost, level)
        else:
            row = self.empty_row_element(task, level)
        # add row
        tbody.appendChild(row)
        # print children
        for child in task.children:
            self._build_task_node(tbody, child, level+1)

    def row_element(self, task, task_cost, level=0):
        """ create a DOM element <row> with values in task node"""
        row = self.dbh.custom_node('row')
        indent = u'\xA0 '*level
        # task title
        entry = self.dbh.table_cell_node('left', indent+task.title)
        row.appendChild(entry)
        # task duration
        duration = task.duration and unicode(task.duration) or u''
        entry = self.dbh.table_cell_node('left', duration)
        row.appendChild(entry)
        # task cost by resources
        costs, durations = self.projman.get_task_costs(task.id)
        # FIXME = do we what number of days for each resource or monetary cost for each resource.
        r_info = ['%s(%s)' % (r_id, format_monetary(cost)) 
                  for r_id, cost in durations.items() if r_id]
        entry = self.dbh.table_cell_node('left', ', '.join(r_info))
        row.appendChild(entry)
        # task global cost
        # FIXME hack : a (containing) task with no resources has global cost of 1!
        if durations.keys() == [u''] and task_cost == 1.:
            entry = self.dbh.table_cell_node('right', 0)
        else:
            entry = self.dbh.table_cell_node('right', format_monetary(task_cost))
        row.appendChild(entry)
        return row
    
    def empty_row_element(self, task, level=0):
        """ create a DOM element <row> with values in task node"""
        row = self.dbh.custom_node('row')
        indent = u'\xA0 '*level
        # task title
        entry = self.dbh.table_cell_node('left', indent+task.title)
        row.appendChild(entry)
        row.appendChild(self.dbh.table_cell_node())
        row.appendChild(self.dbh.table_cell_node())
        row.appendChild(self.dbh.table_cell_node())
        return row



class CostParaView(XMLView):
    name = 'cost-para'
    TOTAL_COST = u"Le coût total se chiffre à %s euros HT, soit %s euros TTC."
        
    def content_nodes(self):
        """return a dr:object node for the cost paragraph view"""
        cost = self.cdata.project_cost
        text = self.TOTAL_COST % (format_monetary(cost),
                                  format_monetary(cost * (1+TVA/100)))
        return self.dbh.para_node(text),



class TasksListSectionView(XMLView):
    name = 'tasks-list-section'
    
    def content_nodes(self):
        """return a dr:object node for the tasks list section view"""
        for child in self.projman.root_task.children:
            yield self._build_task_node(child)
        
    def _build_task_node(self, task):
        section = self.dbh.section_node(task.id)
        # fill title
        section.appendChild(self.dbh.title_node(task.title))
        # fill description
        if task.description != "":
            # create xml-like string
            # encode it and create XML tree from it
            # FIXME !!!
            assert isinstance(task.description, unicode), task.description
            desc = "<?xml version='1.0' encoding='UTF-8'?><para>%s</para>" \
                   % task.description.encode('utf8')
            try:
                description_doc = parseString(desc)
            except Exception, exc:
                print desc
                raise
            section.appendChild(description_doc.documentElement)
        if self.config.display_dates:
            # add date-constraints
            formal_para = self.dbh.formalpara_node()
            section.appendChild(formal_para)
            formal_para.appendChild(self.dbh.title_node(u"Dates"))
            date_begin, date_end = self.projman.get_task_date_range(task)
            begin = date_begin or DATE_NOT_SPECIFIED
            end = date_end or DATE_NOT_SPECIFIED
            para = self.dbh.para_node(u"du %s au %s" % (begin.Format(EXT_DATE_FORMAT),
                                                        end.Format(EXT_DATE_FORMAT)))
            formal_para.appendChild(para)
        # add resources' info
        if task.TYPE == 'task' :
            resource_dict = self.projman.get_resources_duration_per_task(task.id)
            for r_id, r_usage in resource_dict.iteritems():
                section.appendChild(self.resource_node(task.id, r_id, r_usage))
        # print children
        for child in task.children:
            section.appendChild(self._build_task_node(child))
        return section
    
    def resource_node(self, task_id, r_id, usage):
        """ create a DOM node
        <formalpara id=r_id.>
          <title>resource.name</title>
          <para>usage</para>
        </formalpara>
        """
        resource = self.projman.get_resource(r_id)
        para = self.dbh.formalpara_node()
        para.setAttributeNS(NO_NS, 'id', task_id+'_'+r_id)
        para.appendChild(self.dbh.title_node(resource.name))
        para.appendChild(self.dbh.para_node(get_daily_labor(usage)))
        return para

    
class DurationTableView(CostTableView):
    name = 'duration-table'
    ENTETE = u"Tableau récapitulatif des dates."
    
    def content_nodes(self):
        """return a dr:object node for the cost table view"""
        table = self.dbh.table_node()
        # fill title
        table.appendChild(self.dbh.title_node(self.ENTETE))
        # fill column information for table
        layout = self.dbh.table_layout_node(4, colspecs=('3*', '2*', '2*', '1*'))
        # table head
        layout.appendChild(self.table_head())
        table.appendChild(layout)
        # table body
        tbody = self.dbh.table_body_node()
        layout.appendChild(tbody)
        for child in self.projman.root_task.children:
            self._build_task_node(tbody, child)
        return table,
    
    def table_head(self):
        """ create a DOM node <thead> """ 
        thead = self.dbh.table_head_node()
        row = self.dbh.custom_node('row')
        row.appendChild(self.dbh.table_cell_node())
        row.appendChild(self.dbh.table_cell_node('left', u'Date de début'))
        row.appendChild(self.dbh.table_cell_node('left', u'Date de fin'))
        row.appendChild(self.dbh.table_cell_node('center', u'Durée (jours)'))
        thead.appendChild(row)
        return thead
    
    def row_element(self, task, task_cost, level=0):
        """ create a DOM element <row> with values in task node"""
        return self.empty_row_element(task, level)
    
    def empty_row_element(self, task, level=0):
        """ create a DOM element <row> with values in task node"""
        row = self.dbh.custom_node('row')
        # indentation
        indent = u'\xA0 '*level
        # task title
        row.appendChild(self.dbh.table_cell_node('left', indent+task.title))
        # task begin & end
        date_begin, date_end = self.projman.get_task_date_range(task)
        row.appendChild(self.dbh.table_cell_node('left', date_begin.date))
        row.appendChild(self.dbh.table_cell_node('left', date_end.date))
        # task length
        duration = date_end+1 - date_begin
        row.appendChild(self.dbh.table_cell_node('left', str(duration.absvalues()[0])))
        return row


ALL_VIEWS = {}
for klass in (RatesSectionView, DurationSectionView, CostTableView,
              CostParaView, TasksListSectionView, DurationTableView):
    ALL_VIEWS[klass.name] = klass
    

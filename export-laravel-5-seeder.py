# -*- coding: utf-8 -*-
# MySQL Workbench module
# A MySQL Workbench plugin which exports a Model to Laravel 5 seeds
# Written in MySQL Workbench 6.2.5.0

import re
import cStringIO

import grt
import mforms
import datetime

from grt.modules import Workbench
from wb import DefineModule, wbinputs
from workbench.ui import WizardForm, WizardPage
from mforms import newButton, newCodeEditor, FileChooser

ModuleInfo = DefineModule(name='GenerateLaravel5seed', author='Pedro Soares', version='0.0.1')
seeds = {}
seed_tables = []
pure_seeds = " "

seedBegginingTemplate = '''
<?php

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class {tableNameCamelCase}Seeder extends Seeder {{

    /**
     * Run the {tableName} seeds.
     *
     * @return void
     */
    public function run() {{
'''

insertTemplate = '''
        DB::table('{tableName}')->insert(
            [{columns}]
        );
'''

columnsTemplate = '''"{nome}" => "{valor}"'''



seedEndingTemplate = '''
    }}
}}
'''

def insertToColumn(table):
    inserts = table.inserts()
    if inserts:

        # lines = inserts.splitlines()
        lines = inserts.replace('\n', '').split(';')

        tableName = ""

        tableTmp = ""

        global pure_seeds

        for line in lines:
            #print line

            peaces = line.split('(')

            if len(peaces) == 0 or not peaces[0]:
                continue

            tableName = getTableName(peaces[0])

            seed_tables.append(tableName)

            tableColumnsName = getColumnsName(peaces[1])
            tableColumnsValue = getColumnValues(peaces[2])

            columnsTmp = ""

            for index in range(len(tableColumnsName)):
                columnsTmp += columnsTemplate.format(
                    nome = tableColumnsName[index],
                    valor = tableColumnsValue[index]
                )
                if index+1 < len(tableColumnsName):
                    columnsTmp += ","

            tableTmp += insertTemplate.format(
                tableName = tableName,
                columns = columnsTmp
            )

        templateTmp = seedBegginingTemplate.format(
            tableNameCamelCase = tableName.replace('.', ''),
            tableName = tableName
        )

        templateTmp += tableTmp + "\n"

        templateTmp += seedEndingTemplate.format()
            
        seeds[tableName] = templateTmp

        pure_seeds += templateTmp + "\n\n"

def getTableName(insert):
    return insert.replace("INSERT INTO ", "").replace("`", "").strip()

def getColumnsName(insert):
    result = []

    columns = insert.replace(") VALUES ", "").replace("`", "").split(',')
    for column in columns:
        result.append( column.strip() )

    return result

def getColumnValues(insert):
    result = []

    regex = r"(\'[^\']*\'|(([^\',]+)))"
    matches = re.finditer(regex, insert.replace(")", ""))

    for matchNum, match in enumerate(matches):
        columnValueRegex = match.group().strip()


        if len(columnValueRegex) > 0 and columnValueRegex[0] == '\'':
            columnValueRegex = columnValueRegex.replace(columnValueRegex[:1], '').strip()

        if len(columnValueRegex) > 0 and columnValueRegex[:-1] == '\'':
            columnValueRegex = columnValueRegex.replace(columnValueRegex[:-1], '').strip()


        if len(columnValueRegex) == 0:
            continue

        result.append( columnValueRegex )

    

    #inserts = insert.replace(")", "").split(', \'')
    #for insert in inserts:
        #result.append( insert.strip().replace("'", "") )

    return result
    
 

class GenerateLaravel5SeederWizard_PreviewPage(WizardPage):
    def __init__(self, owner, sql_text):
        WizardPage.__init__(self, owner, 'Review Generated Seeder(s)')

        self.save_button = mforms.newButton()
        self.save_button.enable_internal_padding(True)
        self.save_button.set_text('Save Seeder(s) to Folder...')
        self.save_button.set_tooltip('Select the folder to save your seeder(s) to.')
        self.save_button.add_clicked_callback(self.save_clicked)

        self.sql_text = mforms.newCodeEditor()
        self.sql_text.set_language(mforms.LanguageMySQL)
        self.sql_text.set_text(sql_text)

    def go_cancel(self):
        self.main.finish()

    def create_ui(self):
        button_box = mforms.newBox(True)
        button_box.set_padding(8)

        button_box.add(self.save_button, False, True)

        self.content.add_end(button_box, False, False)
        self.content.add_end(self.sql_text, True, True)

    def save_clicked(self):
        file_chooser = mforms.newFileChooser(self.main, mforms.OpenDirectory)

        if file_chooser.run_modal() == mforms.ResultOk:
            path = file_chooser.get_path()
            text = self.sql_text.get_text(False)

            i = 0
            now = datetime.datetime.now()
            for mkey in sorted(seeds):
                print mkey
                try:
                    with open(path + '/%s_%s_%s_%s_seeder_%s_table.php' % (
                            now.strftime('%Y'), now.strftime('%m'), now.strftime('%d'), str(i).zfill(6), mkey),
                              'w+') as f:
                        f.write(''.join(seeds[mkey]))
                        i += 1
                except IOError as e:
                    mforms.Utilities.show_error(
                        'Save to File',
                        'Could not save to file "%s": %s' % (path, str(e)),
                        'OK'
                    )
    

@ModuleInfo.plugin('wb.util.generateLaravel5Seeder',
                   caption='Export Laravel 5 Seeder',
                   input=[wbinputs.currentCatalog()],
                   groups=['Catalog/Utilities', 'Menu/Catalog']
                   )
@ModuleInfo.export(grt.INT, grt.classes.db_Catalog)
def generateLaravel5Seeder(cat):
    
    Laravel5Seeder()

class GenerateLaravel5SeederWizard(WizardForm):
    def __init__(self, sql_text):
        WizardForm.__init__(self, None)

        self.set_name('generate_laravel_5_seeder_wizard')
        self.set_title('Generate Laravel 5 Seeder Wizard')

        self.preview_page = GenerateLaravel5SeederWizard_PreviewPage(self, sql_text)
        self.add_page(self.preview_page)

def Laravel5Seeder():
    global pure_seeds

    for model in grt.root.wb.doc.physicalModels:
        for schema in model.catalog.schemata:
            for table in schema.tables:
                insertToColumn(table) 


    wizard = GenerateLaravel5SeederWizard(pure_seeds)
    wizard.run()

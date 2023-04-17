#!/usr/bin/env python3
# coding: utf-8
#
# makeBomCmd.py
#
# Parses the Assembly 4 Model tree and creates a list of parts

import os
import json
import re

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4
import infoPartCmd
import infoKeys

crea = infoPartCmd.infoPartUI.makePartInfo
fill = infoPartCmd.infoPartUI.infoDefault

ConfUserDir = os.path.join(App.getUserAppDataDir(),'Templates')
ConfUserFilename = "Asm4_infoPartConf.json"
ConfUserFilejson = os.path.join(ConfUserDir, ConfUserFilename)

'''
# Check if the configuration file exists
try:
    file = open(ConfUserFilejson, 'r')
    file.close()
except:
    partInfoDef = dict()
    for prop in InfoKeys.partInfo:
        partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': True})
    for prop in InfoKeys.partInfo_Invisible:
        partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': False})
    try:
        os.mkdir(ConfUserDir)
    except:
        pass
    file = open(ConfUserFilejson, 'x')
    json.dump(partInfoDef, file)
    file.close()

# Load user's config file
file = open(ConfUserFilejson, 'r')
infoKeysUser = json.load(file).copy()
file.close()
'''


class makeBOM:

    def __init__(self, follow_subassemblies=True):
        super(makeBOM, self).__init__()
        self.follow_subassemblies = follow_subassemblies
        '''
        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()
        '''

    def GetResources(self):

        if self.follow_subassemblies == True:
            menutext = "Bill of Materials"
            tooltip  = "Create the Bill of Materials of the Assembly including sub-assemblies"
            iconFile = os.path.join( Asm4.iconPath, 'Asm4_PartsList_Subassemblies.svg' )
        else:
            menutext = "Local Bill of Materials"
            tooltip  = "Create the Bill of Materials of the Assembly"
            iconFile = os.path.join( Asm4.iconPath, 'Asm4_PartsList.svg' )

        return {
            "MenuText": menutext,
            "ToolTip": tooltip,
            "Pixmap": iconFile
        }

    def IsActive(self):
        if Asm4.getAssembly() is None:
            return False
        else:
            return True

    def Activated(self):
        self.UI = QtGui.QDialog()
        self.modelDoc = App.ActiveDocument
        # open user part info template
        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()

        try:
            self.model = self.modelDoc.Assembly
            print("ASM4> BOM of the Assembly 4 Model")
        except:
            try:
                self.model = self.modelDoc.Model
                print("ASM4> BOM of the legacy Assembly 4 Model")
            except:
                print("ASM4> BOM might not work with this file")

        self.drawUI()
        self.UI.show()
        self.BOM.clear()
        self.Verbose = str()
        self.PartsList = {}

        if self.follow_subassemblies == True:
            print("ASM4> BOM following sub-assemblies")
        else:
            print("ASM4> BOM local parts only")

        self.listParts(self.model)
        self.inSpreadsheet()
        self.BOM.setPlainText(self.Verbose)

    def indent(self, level, tag="|"):
        spaces = (level + 1) * "  "
        return "[{level}]{spaces}{tag} ".format(level=str(level), tag=tag, spaces=spaces)

    def listParts(self, obj, level=0, parent=None):

        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()

        max_level = 100
        if self.follow_subassemblies == False:
            max_level = 2;

        if obj == None:
            return

        if self.PartsList == None:
            self.PartsList = {}

        #=======================
        # VISIBLE APP LINK
        #=======================

        if obj.TypeId == 'App::Link':
            if obj.Visibility == True:
                print("ASM4> {level}{obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level), obj_label=obj.Label, obj_name=obj.FullName, obj_typeid=obj.TypeId))

                # self.Verbose += "> {level} | {type}: {label}, {fullname}".format(level=obj.Label, type="APP_LINK", label=obj.Label, fullname=obj.FullName)
                # try:
                #     self.Verbose += "- linked: {linked_obj}\n".format(linked_obj=obj.LinkedObject.Name)
                # except:
                #     self.Verbose += "- linked: {linked_obj}\n".format(linked_obj=obj.Name)
                # self.Verbose += '- not included\n\n'

                # Navigate on objects inside a App:Links (Groups of Fasteners)
                if obj.ElementCount > 0:
                    for i in range(obj.ElementCount):
                        self.listParts(obj.LinkedObject, level, parent=obj)
                else:
                    self.listParts(obj.LinkedObject, level + 1, parent=obj)

        #==================================
        # MODEL_PART aka ASM4 SUB-ASSEMBLY
        #==================================
        elif obj.TypeId == 'App::Part' and Asm4.isAsm4Model(obj):
            if level > 0 and level <= max_level and self.follow_subassemblies == False:
                # Recover the record, if any
                try:
                    if self.infoKeysUser.get("Doc_Label").get('active'):
                        try:
                            doc_name = getattr(obj, self.infoKeysUser.get("Doc_Label").get('userData'))
                        except AttributeError:
                            doc_name = obj.Document.Name
                except:
                    doc_name = obj.Document.Name

                # Recover the record, if any
                if self.infoKeysUser.get("Part_Label").get('active'):
                    try:
                        obj_label = getattr(obj, self.infoKeysUser.get("Part_Label").get('userData'))
                    except AttributeError:
                        obj_label = obj.Label

                # The name cannot be Model otherwise it will sum all other 'Model' names together
                if obj_label == "Model":
                   obj_label = obj.Document.Name

                if obj_label in self.PartsList:
                    if self.PartsList[obj_label]['Doc_Label'] == doc_name:
                        qtd = self.PartsList[obj_label]['Qty.'] + 1

                        print("ASM4> {level}| {qtd}x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj_label, obj_name=obj.FullName, obj_typeid=obj.TypeId, qtd=qtd))

                        self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj_label, type="ASM4_PART", label=obj_label, fullname=obj.FullName)
                        self.Verbose += "- object already added (" + str(qtd) + ")\n\n"
                        self.PartsList[obj_label]['Qty.'] = qtd

                else:
                    print("ASM4> {level}| 1x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj_label, obj_name=obj.FullName, obj_typeid=obj.TypeId))

                    self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj_label, type="ASM4_PART", label=obj_label, fullname=obj.FullName)
                    self.Verbose += "- adding object (1)\n"

                    self.PartsList[obj_label] = dict()
                    for prop in self.infoKeysUser:

                        if self.infoKeysUser.get(prop).get('active'):
                            try: # to get partInfo
                                getattr(obj, self.infoKeysUser.get(prop).get('userData'))
                                info = "(predefined)"
                            except AttributeError:
                                crea(self,obj)
                                fill(obj)
                                info = "(extracted)"

                            if self.infoKeysUser.get(prop).get('visible'):
                                data = getattr(obj, self.infoKeysUser.get(prop).get('userData'))
                            else:
                                data = "-"

                            if data == "":
                                data = "-"

                            if prop == "Part_Label":
                                data = obj_label

                            if data != "-":
                                self.Verbose += "- " + prop + ": " + data + " " + info + "\n"

                            self.PartsList[obj_label][self.infoKeysUser.get(prop).get('userData')] = data

                    self.PartsList[obj_label]['Qty.'] = 1
                    self.Verbose += '\n'


        #============================
        # STANDALONE MODEL_PART
        #============================

        elif obj.TypeId == 'App::Part' and not Asm4.isAsm4Model(obj):
            if level > 0 and level <= max_level:
                # Recover the record, if any
                try:
                    if self.infoKeysUser.get("Doc_Label").get('active'):
                        try:
                            doc_name = getattr(obj, self.infoKeysUser.get("Doc_Label").get('userData'))
                        except AttributeError:
                            doc_name = obj.Document.Name
                except:
                    doc_name = obj.Document.Name

                # Recover the record, if any

                try:
                    if self.infoKeysUser.get("Part_Label").get('active'):
                        try:
                            obj_label = getattr(obj, self.infoKeysUser.get("Part_Label").get('userData'))
                        except AttributeError:
                            obj_label = obj.Label
                except:
                    doc_name = obj.Label

                # The name cannot be model otherwise it will sum all other 'Model' names together
                if obj_label == "Model":
                   obj_label = obj.Document.Name

                if obj_label in self.PartsList:
                    if self.PartsList[obj_label]['Doc_Label'] == doc_name:
                        qtd = self.PartsList[obj_label]['Qty.'] + 1
                        print("ASM4> {level}| {qtd}x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj_label, obj_name=obj.FullName, obj_typeid=obj.TypeId, qtd=qtd))
                        self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj_label, type="PART", label=obj_label, fullname=obj.FullName)
                        self.Verbose += "- object already added (" + str(qtd) + ")\n\n"
                        self.PartsList[obj_label]['Qty.'] = qtd

                else:
                    print("ASM4> {level}| 1x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj_label, obj_name=obj.FullName, obj_typeid=obj.TypeId))
                    self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj_label, type="PART", label=obj_label, fullname=obj.FullName)
                    self.Verbose += "- adding object (1)\n"
                    self.PartsList[obj_label] = dict()
                    for prop in self.infoKeysUser:
                        if self.infoKeysUser.get(prop).get('active'):
                            try: # to get partInfo
                                getattr(obj, self.infoKeysUser.get(prop).get('userData'))
                                info = "(predefined)"
                            except AttributeError:
                                crea(self,obj)
                                fill(obj)
                                info = "(extracted)"

                            if self.infoKeysUser.get(prop).get('visible'):
                                data = getattr(obj, self.infoKeysUser.get(prop).get('userData'))
                            else:
                                data = "-"

                            if data == "":
                                data = "-"

                            if prop == "Part_Label":
                                data = obj_label

                            if data != "-":
                                self.Verbose += "- " + prop + ": " + data + " " + info + "\n"

                            self.PartsList[obj_label][self.infoKeysUser.get(prop).get('userData')] = data

                    self.PartsList[obj_label]['Qty.'] = 1
                    self.Verbose += '\n'

        #============================
        # STANDALONE MODEL_PARTDESIGN
        #============================

        elif obj.TypeId == 'PartDesign::Body':

            # if level > 0 and level <= max_level and Asm4.isAsm4Model(parent):
            if level > 0 and level <= max_level :

                # Recover the record, if any
                try:
                    if self.infoKeysUser.get("Doc_Label").get('active'):
                        try:
                            doc_name = getattr(obj, self.infoKeysUser.get("Doc_Label").get('userData'))
                        except AttributeError:
                            doc_name = obj.Document.Name
                except:
                    doc_name = obj.Document.Name

                if obj.Label in self.PartsList:
                    if self.PartsList[obj.Label]['Doc_Label'] == doc_name:
                        qtd = self.PartsList[obj.Label]['Qty.'] + 1
                        print("ASM4> {level}{qtd}x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj.Label, obj_name=obj.FullName, obj_typeid=obj.TypeId, qtd=qtd))
                        self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj.Label, type="PART", label=obj.Label, fullname=obj.FullName)
                        self.Verbose += "- object already added (" + str(qtd) + ")\n\n"
                        self.PartsList[obj.Label]['Qty.'] = qtd

                else:
                    print("ASM4> {level}1x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj.Label, obj_name=obj.FullName, obj_typeid=obj.TypeId))
                    self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj.Label, type="PARTDESIGN", label=obj.Label, fullname=obj.FullName)
                    self.Verbose += "- adding object (1)\n"
                    self.PartsList[obj.Label] = dict()
                    for prop in self.infoKeysUser:
                        self.Verbose +=  "- " + prop + ': '
                        if prop == 'Doc_Label':
                            data = obj.Document.Label
                        elif prop == 'Part_Label':
                            data = obj.Label
                        else:
                            data = "-"

                        if data != "-":
                            self.Verbose += data + '\n'

                        self.PartsList[obj.Label][self.infoKeysUser.get(prop).get('userData')] = data

                    self.PartsList[obj.Label]['Qty.'] = 1
                    self.Verbose += '\n'


        #============================
        # FATENERS
        #============================

        elif obj.TypeId == 'Part::FeaturePython' and (obj.Content.find("FastenersCmd") or (obj.Content.find("PCBStandoff")) > -1):
            if level > 0 and level <= max_level:
                doc_name = os.path.splitext(os.path.basename(obj.Document.FileName))[0]
                obj_label = re.sub(r'[0-9]+$', '', obj.Label)

                if obj_label in self.PartsList:
                    if self.PartsList[obj_label]['Doc_Label'] == doc_name:
                        qtd = self.PartsList[obj_label]['Qty.'] + 1
                        print("ASM4> {level}| {qtd}x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj_label, obj_name=obj.FullName, obj_typeid=obj.TypeId, qtd=qtd))
                        self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj_label, type="FASTENER", label=obj_label, fullname=obj.FullName)
                        self.Verbose += "- object already added (" + str(qtd) + ")\n\n"
                        self.PartsList[obj_label]['Qty.'] = qtd

                else: # if the part is a was not added already

                    print("ASM4> {level}| 1x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj_label, obj_name=obj.FullName, obj_typeid=obj.TypeId))

                    self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj_label, type="FASTENER", label=obj_label, fullname=obj.FullName)
                    self.Verbose += "- adding object (1)\n"

                    self.PartsList[obj_label] = dict()
                    for prop in self.infoKeysUser:
                        if prop == 'Doc_Label':
                            data = doc_name
                        elif prop == 'Part_Label':
                            data = obj_label
                        elif prop == "Fastener_Diameter":
                            data = obj.diameter
                        elif prop == "Fastener_Type":
                            data = obj.type
                        elif prop == "Fastener_Lenght":
                            try:
                                data = str(obj.length).strip("mm")
                            except:
                                data = ""
                        else:
                            data = "-"

                        if data != "-":
                            self.Verbose += "- " + prop + ': ' + data + '\n'

                        self.PartsList[obj_label][self.infoKeysUser.get(prop).get('userData')] = data

                    self.PartsList[obj_label]['Qty.'] = 1
                    self.Verbose += '\n'


        # else:
            # print("@", obj.TypeId)

        #===================================
        # Continue walking inside the groups
        #===================================

        # Navigate on objects inide a folders
        if obj.TypeId == 'App::DocumentObjectGroup':
            for objname in obj.getSubObjects():
                subobj = obj.Document.getObject(objname[0:-1])
                self.listParts(subobj, level, parent=obj)

        # Navigate on objects inide a ASM4 Part (Links and Folders)
        if obj.TypeId == 'App::Part':
            for objname in obj.getSubObjects():
                subobj = obj.Document.getObject(objname[0:-1])
                # if subobj.TypeId == 'App::Link' or subobj.TypeId == 'App::DocumentObjectGroup':
                self.listParts(subobj, level+1, parent=obj)

        return

        self.Verbose += '\nBOM creation is done\n'

    # Copy Parts list to Spreadsheet
    def inSpreadsheet(self):
        document = App.ActiveDocument
        plist = self.PartsList

        if len(plist) == 0:
            return

        if self.follow_subassemblies:
            if not hasattr(document, 'BOM'):
                spreadsheet = document.addObject('Spreadsheet::Sheet', 'BOM')
            else:
                spreadsheet = document.BOM
            spreadsheet.Label = "BOM"
        else:
            if not hasattr(document, 'BOM_Local'):
                spreadsheet = document.addObject('Spreadsheet::Sheet', 'BOM_Local')
            else:
                spreadsheet = document.BOM_Local
            spreadsheet.Label = "BOM_Local"

        spreadsheet.clearAll()


        # Write rows in the spreadsheet
        def wrow(drow: [str], row: int):
            for i, d in enumerate(drow):
                if row == 0:
                    spreadsheet.set(str(chr(ord('a') + i)).upper() + str(row + 1), infoPartCmd.decodeXml(str(d)))
                else:
                    spreadsheet.set(str(chr(ord('a') + i)).upper() + str(row + 1), str(d))

        data = list(plist.values()) # present data in the order it is in the Object tree

        wrow(data[0].keys(), 0)
        for i, _ in enumerate(data):
            wrow(data[i].values(), i + 1)

        document.recompute()

        self.Verbose += "\n" + spreadsheet.Label + ' spreadsheet was created.\n'


    def onOK(self):
        document = App.ActiveDocument
        if self.follow_subassemblies:
            Gui.Selection.addSelection(document.Name, 'BOM')
        else:
            Gui.Selection.addSelection(document.Name, 'BOM_Local')
        self.UI.close()

    # Define the UI (static elements, only)
    def drawUI(self):
        # Main Window (QDialog)
        self.UI.setWindowTitle('Parts List (BOM)')
        self.UI.setWindowIcon(QtGui.QIcon(os.path.join(Asm4.iconPath , 'FreeCad.svg')))
        self.UI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.UI.setModal(False)
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        # Help and Log
        self.LabelBOML1 = QtGui.QLabel()
        self.LabelBOML1.setText('BOM generates bill of materials.\n\nIt uses the Parts\' info to generate entries on BOM, unless autofill is set.\n')
        self.LabelBOML2 = QtGui.QLabel()
        self.LabelBOML2.setText("Check <a href='https://github.com/Zolko-123/FreeCAD_Assembly4/tree/master/Examples/ConfigBOM/README.md'>BOM tutorial</a>")
        self.LabelBOML2.setOpenExternalLinks(True)
        self.LabelBOML3 = QtGui.QLabel()
        self.LabelBOML3.setText('\n\nReport:')

        self.mainLayout.addWidget(self.LabelBOML1)
        self.mainLayout.addWidget(self.LabelBOML2)
        self.mainLayout.addWidget(self.LabelBOML3)

        # The Log view is a plain text field
        self.BOM = QtGui.QPlainTextEdit()
        self.BOM.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        self.mainLayout.addWidget(self.BOM)

        # the button row definition
        self.buttonLayout = QtGui.QHBoxLayout()

        # OK button
        self.OkButton = QtGui.QPushButton('OK')
        self.OkButton.setDefault(True)
        self.buttonLayout.addWidget(self.OkButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.OkButton.clicked.connect(self.onOK)


# Add the command in the workbench
Gui.addCommand('Asm4_makeLocalBOM', makeBOM(follow_subassemblies=False))
Gui.addCommand('Asm4_makeBOM', makeBOM(follow_subassemblies=True))

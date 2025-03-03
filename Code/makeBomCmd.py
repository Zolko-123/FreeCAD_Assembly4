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
from Asm4_Translate import _atr, QT_TRANSLATE_NOOP, translate

import Asm4_libs as Asm4
import infoPartCmd
#import infoKeys
#All infor from infoKeys is process by infoPartCmd shouldn't need to


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
        #super().__init__()
        self.follow_subassemblies = follow_subassemblies
        '''
        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()
        '''

    def GetResources(self):

        if self.follow_subassemblies == True:
            menutext = translate("Asm4_makeBOM", "Bill of Materials")
            tooltip  = translate("Asm4_makeBOM", "Create the Bill of Materials of the Assembly including sub-assemblies")
            iconFile = os.path.join( Asm4.iconPath, 'Asm4_PartsList_Subassemblies.svg' )
        else:
            menutext = translate("Asm4_makeBOM", "Local Bill of Materials")
            tooltip  = translate("Asm4_makeBOM", "Create the Bill of Materials of the Assembly")
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
            print(translate("Asm4_makeBOM", "ASM4> BOM of the Assembly 4 Model"))
        except:
            try:
                self.model = self.modelDoc.Model
                print(translate("Asm4_makeBOM", "ASM4> BOM of the legacy Assembly 4 Model"))
            except:
                print(translate("Asm4_makeBOM", "ASM4> BOM might not work with this file"))

        self.drawUI()
        self.UI.show()
        self.BOM.clear()
        self.Verbose = str()
        self.BomKeyList = {}
        self.BomKeyForAutoFillList = {}

        if self.follow_subassemblies == True:
            print(translate("Asm4_makeBOM", "ASM4> BOM following sub-assemblies"))
        else:
            print(translate("Asm4_makeBOM", "ASM4> BOM local parts only"))

        # This recursive routine goes through the Bom to find parts making up the
        # Assembly it then runs the Autofill to make sure that values than can be automatically applied are
        # There is mimimum functionality hardcoded into inPartCmd.py for a generic use case
        # if you a modding and your use case is not "universal" please consider placing these mods in InfoKeys.py
        # so we're not tripping over each other.
        # todo, there should be some type of toggle, to optionally fire this.
        self.RecursivelyAutoFillPartInfoInBom(self.model)


        self.listParts(self.model)
        self.inSpreadsheet()
        self.BOM.setPlainText(self.Verbose)

    def indent(self, level, tag="|"):
        spaces = (level + 1) * "  "
        return "[{level}]{spaces}{tag} ".format(level=str(level), tag=tag, spaces=spaces)



    #This routine uses basically looks for parts and assemblies called out for the first time and applies
    # infoPartCmd.infoDefaul to auto populate the Part_info fields where such logic exists
    #
    def RecursivelyAutoFillPartInfoInBom(self, obj, level=0, parent=None):
        max_level = 100
        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()

        if obj == None:
            return
        print (f"TypeID = {obj.TypeId} Level = {level}  Parent = {str(parent)}  Obj.Fullname ={obj.FullName}")
        if self.BomKeyForAutoFillList == None:
            self.BomKeyForAutoFillList = {}
        if obj.TypeId == 'App::Link':
            if obj.ElementCount > 0:
                for i in range(obj.ElementCount):
                    self.RecursivelyAutoFillPartInfoInBom(obj.LinkedObject, level, parent=obj)
            else:
                self.RecursivelyAutoFillPartInfoInBom(obj.LinkedObject, level + 1, parent=obj)
        elif obj.TypeId == 'App::Part':
            BomKeyAF = obj.FullName
            print ("------------")
            print (f"Level = {level}  Parent = {str(parent)}  BomKeyAF={BomKeyAF}")
            if level <= max_level:
                if  BomKeyAF in self.BomKeyForAutoFillList: # we don't need to add info because we did it already
                # would like to keep score though
                    if self.BomKeyForAutoFillList[BomKeyAF]['BomKeyAF'] == BomKeyAF:
                        qtd = self.BomKeyForAutoFillList[BomKeyAF]['Qty.'] + 1
                        #self.BomKeyForAutoFillList[BomKeyAF]['Qty.'] = qtd
                        self.BomKeyForAutoFillList[BomKeyAF] = {'BomKeyAF': BomKeyAF, 'Qty.': qtd}
                else:
                    #This is the first time a Part or assembly has been called.
                    #We need to apply the magic

                    infoPartCmd.infoPartUI.infoDefault(obj)
                    self.BomKeyForAutoFillList[BomKeyAF] = {'BomKeyAF': BomKeyAF, 'Qty.': 1}





        #============================
        # FASTENERS AND ARRAYS
        #============================
        elif obj.TypeId == 'Part::FeaturePython' and (obj.Content.find("FastenersCmd") or (obj.Content.find("PCBStandoff")) > -1):
            pass #This should be fine

        else:
            print (translate("Asm4_makeBOM", "Nothing Applied"))
        #===================================
        # Continue walking inside the groups
        #=====  ==============================

        # Navigate on objects inide a folders
        if obj.TypeId == 'App::DocumentObjectGroup':
            for objname in obj.getSubObjects():
                subobj = obj.Document.getObject(objname[0:-1])
                self.RecursivelyAutoFillPartInfoInBom(subobj, level, parent=obj)

        # Navigate on objects inide a ASM4 Part (Links and Folders)
        if obj.TypeId == 'App::Part':
            for objname in obj.getSubObjects():
                subobj = obj.Document.getObject(objname[0:-1])
                # if subobj.TypeId == 'App::Link' or subobj.TypeId == 'App::DocumentObjectGroup':
                self.RecursivelyAutoFillPartInfoInBom(subobj, level+1, parent=obj)

        return



    def listParts(self, obj, level=0, parent=None):

        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()

        max_level = 100
        if self.follow_subassemblies == False:
            max_level = 2;

        if obj == None:
            return

        if self.BomKeyList == None:
            self.BomKeyList = {}


        print (translate("Asm4_makeBOM", "-------------------------------------------------- remove after debugging"))
        print (obj.TypeId)
        print (obj.Label)
        #=======================
        # VISIBLE APP LINK
        #=======================

        if obj.TypeId == 'App::Link':
            if obj.Visibility == True:


                print("ASM4> {level}{obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level), obj_label=obj.Label, obj_name=obj.FullName, obj_typeid=obj.TypeId))

                #'-----------------------------------------------------------------------'
                #'--- Test to see if we have an Linked Part in the assembly if we do  ---'
                #'-----------------------------------------------------------------------'

                # self.Verbose += "> {level} | {type}: {label}, {fullname}".format(level=obj.Label, type="APP_LINK", label=obj.Label, fullname=obj.FullName)
                # try:
                #     self.Verbose += "- linked: {linked_obj}\n".format(linked_obj=obj.LinkedObject.Name)
                # except:
                #     self.Verbose += "- linked: {linked_obj}\n".format(linked_obj=obj.Name)
                # self.Verbose += '- not included\n\n'

                # Navigate on objects inside a App:Links
                if obj.ElementCount > 0:
                    for i in range(obj.ElementCount):
                        self.listParts(obj.LinkedObject, level, parent=obj)
                else:
                    self.listParts(obj.LinkedObject, level + 1, parent=obj)

        #==================================
        # TRY TREATING ALL PARTS (AND ASSEMBLY) THE SAME =
        #==================================
        #Not sure if this is going to work,It just seems that we have some endless complexity.
        #at the end of the day we have parts and standard hardware
        #Parts should have a drawing number associated with them
        #Some Drawings can have multiple parts.
        #The Goal (I think is to pull out how many times we have a Part called out
        #If we have standard nuts and bolts we want howmany times those are called out.

        elif obj.TypeId == 'App::Part':
            if level <= max_level:

                #the BomKey is the unique identifier.
                #if its a flat part list, it's Drawing-Part Id for non hardware
                #if it's a multi-level bom it would be Someline line 001.001.001 representing which item level a part is on the bom.
                BomKey = obj.FullName

                obj_fullname = obj.FullName

                # Split the string based on the "#" delimiter
                parts = obj_fullname.split("#")

                # Extract the Document and PartName from the parts list
                if len(parts) == 2:
                    Document = parts[0]
                    #PartName = parts[1]
                else:
                    # Handle the case where there is no "#" delimiter in the string
                    # or there are more than one "#" delimiters (not in the format we expect)
                    Document = ""
                    #PartName = ""
                PartName = obj.Label

                if BomKey in self.BomKeyList:
                    if self.BomKeyList[BomKey]['BomKey'] == BomKey:
                        qtd = self.BomKeyList[BomKey]['Qty.'] + 1
                        print("ASM4> {level}{qtd}x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj.Label, obj_name=obj.FullName, obj_typeid=obj.TypeId, qtd=qtd))
                        self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj.Label, type="PART", label=obj.Label, fullname=obj.FullName)
                        self.Verbose += "- object already added (" + str(qtd) + ")\n\n"
                        self.BomKeyList[BomKey]['Qty.'] = qtd

                else:
                    print("ASM4> {level}1x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj.Label, obj_name=obj.FullName, obj_typeid=obj.TypeId))
                    self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj.Label, type="PARTDESIGN", label=obj.Label, fullname=obj.FullName)
                    self.Verbose += "- adding object (1)\n"
                    self.BomKeyList[BomKey] = dict()

                    for prop in self.infoKeysUser:
                        self.Verbose +=  "- " + prop + ': '
                        # JT putting the exception message in data should be removed once we figure out what's going on
                        data = ""

                        # With the  exception of the BomKey the info in the try needs to be refactored

                        try:
                            if prop == 'BomKey':
                                data = BomKey
                            else:
                                data = getattr(obj,prop,"-")

                        except Exception as e:
                            data = "todo Remove after debug" + str(e)

                        if data != "-":
                            self.Verbose += data + '\n'

                        self.BomKeyList[BomKey][self.infoKeysUser.get(prop).get('userData')] = data
                    self.BomKeyList[BomKey]['Qty.'] = 1

                    self.Verbose += '\n'

        #============================
        # FASTENERS AND ARRAYS
        #============================

        elif obj.TypeId == 'Part::FeaturePython' and (obj.Content.find("FastenersCmd") or (obj.Content.find("PCBStandoff")) > -1):
            if level > 0 and level <= max_level:
                doc_name = os.path.splitext(os.path.basename(obj.Document.FileName))[0]

                obj_label = f"{re.sub(r'[0-9]+$', '', obj.Label)}({obj.type})"
                BomKey = obj_label
                print (f"Bomkey: {BomKey}")
                # if array
                if obj.Content.find("Orthogonal array")>-1:
                  # count up the objects in the array
                  x_count = obj.NumberX
                  y_count = obj.NumberY
                  z_count = obj.NumberZ
                  total = x_count * y_count * z_count
                  # identify the linked object
                  subobj = obj.Base.LinkedObject
                  # count each instance of linked object
                  for i in range(0, total):
                    print("    ", i, "...")
                    self.listParts(subobj, level, parent=obj)

                elif obj_label in self.BomKeyList:
                    if self.BomKeyList[BomKey]['BomKey'] == BomKey:
                        qtd = self.BomKeyList[BomKey]['Qty.'] + 1
                        print("ASM4> {level}| {qtd}x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj_label, obj_name=obj.FullName, obj_typeid=obj.TypeId, qtd=qtd))
                        self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj_label, type="FASTENER", label=obj_label, fullname=obj.FullName)
                        self.Verbose += "- object already added (" + str(qtd) + ")\n\n"
                        self.BomKeyList[BomKey]['Qty.'] = qtd

                else: # if the part is a was not added already
                    print("ASM4> {level}| 1x | {obj_typeid} | {obj_name} | {obj_label}".format(level=self.indent(level, tag=" "), obj_label=obj_label, obj_name=obj.FullName, obj_typeid=obj.TypeId))

                    self.Verbose += "> {level} | {type}: {label}, {fullname}\n".format(level=obj_label, type="FASTENER", label=obj_label, fullname=obj.FullName)
                    self.Verbose += "- adding object (1)\n"

                    self.BomKeyList[obj_label] = dict()
                    for prop in self.infoKeysUser:
                        print ("prop="+prop)
                        if prop =='BomKey':
                            data = BomKey
                        elif prop == "DrawingName":
                            #we may want to build in more smarts here.
                            #For a flat bom, ireally just want to know how many nuts and bolts I have total regardless of sub assembly.'
                            data = "All"
                            #if we had an identented bill of material we would want to know all.
                            #data = doc_name
                        elif prop == 'PartID':
                            data = obj_label
                        elif prop == "FastenerDiameter":
                            data = obj.diameter
                        elif prop == "FastenerType":
                            data = obj.type
                        elif prop == "FastenerLength":
                            try:
                                data = str(obj.length).strip("mm")
                            except:
                                data = ""
                        else:
                            data = "-"

                        if data != "-":
                            self.Verbose += "- " + prop + ': ' + data + '\n'

                        self.BomKeyList[BomKey][self.infoKeysUser.get(prop).get('userData')] = data

                    self.BomKeyList[BomKey]['Qty.'] = 1
                    self.Verbose += '\n'
        else:
            print (translate("Asm4_makeBOM", "Nothing Applied"))

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

        self.Verbose += translate("Asm4_makeBOM", '\nBOM creation is done\n')

    # Copy Parts list to Spreadsheet
    def inSpreadsheet(self):
        document = App.ActiveDocument
        plist = self.BomKeyList

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

        self.Verbose += "\n" + spreadsheet.Label + translate("Asm4_makeBOM", ' spreadsheet was created.\n')


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
        self.UI.setWindowTitle(translate("Asm4_makeBOM", 'Parts List (BOM)'))
        self.UI.setWindowIcon(QtGui.QIcon(os.path.join(Asm4.iconPath , 'FreeCad.svg')))
        self.UI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.UI.setModal(False)
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        # Help and Log
        self.LabelBOML1 = QtGui.QLabel()
        self.LabelBOML1.setText(translate("Asm4_makeBOM", 'BOM generates bill of materials.\n\nIt uses the Parts\' info to generate entries on BOM, unless autofill is set.\n'))
        self.LabelBOML2 = QtGui.QLabel()
        self.LabelBOML2.setText(translate("Asm4_makeBOM", "Check <a href='https://github.com/Zolko-123/FreeCAD_Assembly4/tree/master/Examples/ConfigBOM/README.md'>BOM tutorial</a>"))
        self.LabelBOML2.setOpenExternalLinks(True)
        self.LabelBOML3 = QtGui.QLabel()
        self.LabelBOML3.setText(translate("Asm4_makeBOM", '\n\nReport:'))

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
        self.OkButton = QtGui.QPushButton(translate("Asm4_makeBOM", 'OK'))
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

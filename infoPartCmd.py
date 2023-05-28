#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# infoPartCmd.py

import os, json

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4
import infoKeys

# file_version = infoKeys.file_version
part_info = infoKeys.part_info
part_info_tooltip = infoKeys.part_info_tooltip
fastener_info = infoKeys.fastener_info

"""
    +-----------------------------------------------+
    |                  Helper Tools                 |
    +-----------------------------------------------+
"""

config_dir_path = os.path.join(App.getUserAppDataDir(), 'Templates')
config_filename = "Asm4_infoPartConf.json"
config_file_path = os.path.join(config_dir_path, config_filename)


def writeXml(text):
    text = text.encode('unicode_escape').decode().replace('\\', '_x_m_l_')
    return text


def decodeXml(text):
    text = text.replace('_x_m_l_', '\\').encode().decode('unicode_escape')
    return text


def versiontuple(v):
   filled = []
   for point in v.split("."):
      filled.append(point.zfill(8))
   return tuple(filled)


def load_config_file():

    parts_plist = dict() # part properties list

    # If config file exists compare its version
    # and if its version is older, delete it so it will be recreated
    if os.path.isfile(config_file_path):

        with open(config_file_path, 'r') as f:
            try:
                p = json.load(f).copy()
                if not "file_version" in p:
                    os.remove(config_file_path)
                else:
                    if versiontuple(file_version) > versiontuple(p["file_version"]["userData"]):
                        pass
                        # os.remove(config_file_path)
            except:
                # Malformed file, delete it so it will be recreated
                os.remove(config_file_path)

    # (Re)Create the config file if it does not exist
    if not os.path.isfile(config_file_path):

        # Add file version
        # parts_plist.setdefault("file_version", file_version)

        # Add the default settings
        for prop in part_info:
            parts_plist.setdefault(prop, {"userData": prop, "active": True, "visible": True})

        # Add hidden settings for fastners only
        for prop in fastener_info:
            parts_plist.setdefault(prop, {"userData": prop, "active": True, "visible": False})

        if not os.path.exists(config_dir_path):
            os.mkdir(config_dir_path)

        with open(config_file_path, 'x') as f:
            json.dump(parts_plist, f, indent=4, separators=(", ", ": "))


    with open(config_file_path, 'r') as f:
        parts_plist = json.load(f).copy()

    return parts_plist


"""
    +-----------------------------------------------+
    |                Info Part Command              |
    +-----------------------------------------------+
"""

class infoPartCmd():

    def __init__(self):
        super(infoPartCmd, self).__init__()


    def GetResources(self):
        tooltip  = "<p>Edit Part information</p>"
        tooltip += "<p>User-supplied information can be added to a part</p>"
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_PartInfo.svg')

        return {
            "MenuText": "Edit Part Information",
            "ToolTip": tooltip,
            "Pixmap": iconFile}


    def IsActive(self):
        if App.ActiveDocument and Asm4.getSelectedContainer():
            return True
        return False


    def Activated(self):
        Gui.Control.showDialog(infoPartUI())


"""
    +-----------------------------------------------+
    |       UI and functions in the Task panel      |
    +-----------------------------------------------+
"""

class infoPartUI():

    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_PartInfo.svg')
        self.form.setWindowIcon(QtGui.QIcon(iconFile))
        self.form.setWindowTitle("Edit Part Information")
        self.infoKeysUser = load_config_file()
        self.part = Asm4.getSelectedContainer()
        self.create_partinfo_fields(self.part)
        self.infoTable = []
        self.getPartInfo()
        self.drawUI()


    # Create PartInfo fields (Part|Body|Fastener)
    def create_partinfo_fields(self, obj):
        for user_prop in self.infoKeysUser:
            if self.infoKeysUser.get(user_prop).get('active') and self.infoKeysUser.get(user_prop).get('visible'):
                if hasattr(obj, "part"):
                    if not hasattr(obj.part, self.infoKeysUser.get(user_prop).get('userData')):
                        obj.part.addProperty('App::PropertyString', self.infoKeysUser.get(user_prop).get('userData'), 'PartInfo')
                else:
                    if obj.TypeId == "App::Part" or obj.TypeId == "PartDesign::Body" or obj.TypeId == 'Part::FeaturePython' and ((obj.Content.find("FastenersCmd") > -1) or (obj.Content.find("PCBStandoff") > -1)):
                        if not hasattr(obj, self.infoKeysUser.get(user_prop).get('userData')):
                            obj.addProperty('App::PropertyString', self.infoKeysUser.get(user_prop).get('userData'), 'PartInfo')


    def getPartInfo(self):
        self.infoTable.clear()
        for user_prop in self.infoKeysUser:
            for part_prop in self.part.PropertiesList:
                if self.part.getGroupOfProperty(part_prop) == 'PartInfo':
                    if self.part.getTypeIdOfProperty(part_prop) == 'App::PropertyString':
                        if self.infoKeysUser.get(user_prop).get('userData') == part_prop:
                            if self.infoKeysUser.get(user_prop).get('active') and self.infoKeysUser.get(user_prop).get('visible'):
                                value = self.part.getPropertyByName(part_prop)
                                self.infoTable.append([part_prop, value])


    def addNew(self):
        for i, part_prop in enumerate(self.infoTable):
            if hasattr(self.part, part_prop[0]):
                if self.part.getGroupOfProperty(part_prop[0]) == 'PartInfo':
                    if self.part.getTypeIdOfProperty(part_prop[0]) == 'App::PropertyString':
                        for user_prop in self.infoKeysUser:
                            if self.infoKeysUser.get(user_prop).get('userData') == part_prop[0]:
                                if self.infoKeysUser.get(user_prop).get('active') and self.infoKeysUser.get(user_prop).get('visible'):
                                    text = self.infos[i].text()
                                    setattr(self.part, part_prop[0], str(text))


    def editKeys(self):
        Gui.Control.closeDialog()
        Gui.Control.showDialog(infoPartConfUI())


    # Reset the list of properties
    def on_reinit_part(self):

        part_props = self.part.PropertiesList
        part_info_props = []

        for part_prop in part_props:
            if self.part.getGroupOfProperty(part_prop) == 'PartInfo':
                part_info_props.append(part_prop)

        for suppr in part_info_props: # delete all PartInfo properties
            self.part.removeProperty(suppr)

        self.infoKeysUser = load_config_file()
        self.create_partinfo_fields(self.part)
        # self.set_partinfo_data()

        # Asm4.warningBox("The Part Info fields have been cleared")
        # self.finish()


    def set_partinfo_data(self):

        # if not hasattr(self, "infoKeysUser"):
            # self.infoKeysUser = load_config_file()
        # elif not self.infoKeysUser:
            # self.infoKeysUser = load_config_file()

        # infoKeysUser = load_config_file()

        try:
            self.TypeId
            part = self
        except AttributeError:
            part = self.part

        print("-----------------------------")

        doc = part.Document

        for i, obj1 in enumerate(part.Group):
            if obj1.TypeId == 'PartDesign::Body':
                body = obj1
                for j, obj2 in enumerate(body.Group):
                    if obj2.TypeId == 'PartDesign::Pad':
                        pad = obj2
                        try:
                            sketch = pad.Profile[0]
                        except NameError :
                            print('Sketch: {}, Pad {} does not have Sketch'.format(part.FullName, sketch))
                            pass

            try:
                self.LabelDoc(self, part, doc)
            except:
                print('LabelDoc: {} does not have Doc_Label'.format(part.FullName))
                pass
            try:
                self.LabelType(self, part)
            except:
                print('LabelType: {} does not have TypeId'.format(part.FullName))
                pass
            try:
                self.LabelPart(self, part)
            except:
                print('LabelPart: Part does not exist')
                pass
            try:
                self.PadLength(self, part, pad)
            except:
                print('PadLenght: {} does not have a Pad feature'.format(part.FullName))
                pass
            try:
                self.ShapeLength(self, part, sketch)
            except:
                print('ShapeLength: {} does not have a Sketch'.format(part.FullName))
                pass
            try:
                self.ShapeVolume(self, part, body)
            except:
                print('ShapeVolume: {} does not have a Shape'.format(part.FullName))
                pass


    def LabelDoc(self, part, doc):

        # Recover doc_name from parts_dict
        try:
            if infoKeysUser.get("Doc_Label").get('active'):
                try:
                    doc_name = getattr(obj, infoKeysUser.get("Doc_Label").get('userData'))
                except AttributeError:
                    doc_name = obj.Document.Label
            else:
                doc_name = obj.Document.Label
        except:
            doc_name = obj.Document.Label

        field_name = infoKeysUser.get("Doc_Label").get('userData')
        field_data = doc_name

        try:
            self.TypeId
            setattr(part, field_name, field_data)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == field_name:
                        self.infos[i].setText(field_data)
            except AttributeError:
                self.infos[i].setText("-")


    def LabelType(self, part):

        field_name = infoKeysUser.get('Type_Label').get('userData')

        # field_data = part.TypeId
        if Asm4.isAssembly(part):
            field_data = "Subassembly"
        elif part.TypeId == "App::Part":
            field_data = "Part"
        elif part.TypeId == "PartDesign::Body":
            field_data = "Body"
        else:
            field_data = "Fastener"

        try:
            self.TypeId
            setattr(part, field_name, field_data)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == field_name:
                        self.infos[i].setText(field_data)
            except AttributeError:
                self.infos[i].setText("-")


    def LabelPart(self, part):
        field_name = infoKeysUser.get('Part_Label').get('userData')
        field_data = part.Label

        try:
            self.TypeId
            setattr(part, field_name, field_data)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == field_name:
                        self.infos[i].setText(field_data)
            except AttributeError:
                self.infos[i].setText("-")


    def PadLength(self, part, pad):
        field_name = infoKeysUser.get('Pad_Length').get('userData')
        try:
            field_data = str(pad.Length).replace('mm','')
        except AttributeError:
            return
        try:
            self.TypeId
            setattr(part, field_name, field_data)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == field_name:
                        self.infos[i].setText(field_data)
            except AttributeError:
                self.infos[i].setText("-")


    def ShapeLength(self, part, sketch):
        field_name = infoKeysUser.get('Shape_Length').get('userData')
        try:
            field_data = str(sketch.Shape.Length)
        except AttributeError:
            return
        try:
            self.TypeId
            setattr(part, field_name, field_data)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == field_name:
                        self.infos[i].setText(field_data)
            except AttributeError:
                self.infos[i].setText("-")


    def ShapeVolume(self, part, body):
        field_name = infoKeysUser.get('Shape_Volume').get('userData')
        bbc = body.Shape.BoundBox
        field_data = str(str(round(bbc.ZLength, 3)) + str(' mm x ') + str(round(bbc.YLength, 3)) + str(' mm x ') + str(round(bbc.XLength, 3)) + str(' mm'))
        try:
            self.TypeId
            setattr(part, field_name, field_data)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == field_name:
                        self.infos[i].setText(field_data)
            except AttributeError:
                self.infos[i].setText("-")



    def finish(self):
        Gui.Control.closeDialog()

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)

    def reject(self):
        self.finish()

    def accept(self):
        self.addNew()
        self.finish()

    # Define the UI (static elements, only)
    def drawUI(self):
        # Place the widgets with layouts
        self.mainLayout = QtGui.QVBoxLayout(self.form)
        self.formLayout = QtGui.QFormLayout()
        self.infos = []
        for i, prop in enumerate(self.infoTable):
            for propuser in self.infoKeysUser:
                if self.infoKeysUser.get(propuser).get('userData') == prop[0]:
                    if self.infoKeysUser.get(propuser).get('active'): #and self.infoKeysUser.get(propuser).get('visible'):
                        checkLayout = QtGui.QHBoxLayout()
                        propValue = QtGui.QLineEdit()
                        propValue.setText(prop[1])
                        checkLayout.addWidget(propValue)
                        self.formLayout.addRow(QtGui.QLabel(decodeXml(prop[0])), checkLayout)
                        self.infos.append(propValue)

        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(QtGui.QLabel())

        # Buttons
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.confFields = QtGui.QPushButton('Configure fields')
        self.confFields.setToolTip('Edit fields')
        self.reinit = QtGui.QPushButton('Reset fields')
        self.reinit.setToolTip('Reset fields')
        self.autoFill = QtGui.QPushButton('Autofill data')
        self.autoFill.setToolTip('Autofill fields')
        self.buttonsLayout.addWidget(self.confFields)
        self.buttonsLayout.addWidget(self.reinit)
        self.buttonsLayout.addWidget(self.autoFill)

        self.mainLayout.addLayout(self.buttonsLayout)

        # Actions
        self.confFields.clicked.connect(self.editKeys)
        self.reinit.clicked.connect(self.on_reinit_part)
        self.autoFill.clicked.connect(self.set_partinfo_data)

        '''
        test = False
        try:
            if self.infoTable[0][1] == '':
                test = True
        except IndexError:set_partinfo_data
            test = True
        if test:
            self.set_partinfo_data()
            self.addNew()
        '''



class infoPartConfUI():

    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_PartInfo.svg')
        self.form.setWindowIcon(QtGui.QIcon(iconFile))
        self.form.setWindowTitle("Edit Part Information")

        self.infoKeysDefault = infoKeys.part_info.copy()
        self.part_info_tooltip = infoKeys.part_info_tooltip.copy()

        # file = open(config_file_path, 'r')
        # self.infoKeysUser = json.load(file).copy()
        # file.close()
        self.infoKeysUser = load_config_file()

        self.confTemplate = dict()
        self.confTemplate = self.infoKeysUser.copy()

        self.drawConfUI()


    def finish(self):
        Gui.Control.closeDialog()


    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)


    def reject(self):
        self.finish()


    def accept(self):
        i = 0
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('visible'):
                if self.infos[i].text() == '':
                    '''
                    mb = QtGui.QMessageBox()
                    mb.setWindowTitle("BOM Configuration")
                    mb.setText("Fields Name cannot be blank\nYou must disable or delete it")
                    mb.exec_()
                    '''
                    Asm4.warningBox("Name of the field cannot be blank. You must disable or delete it")
                    return
                i += 1

        # Restore file and appen new config
        partInfoDef = dict()
        for prop in infoKeys.part_info:
            partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': True})
        for prop in infoKeys.fastener_info:
            partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': False})

        i = 0
        # config = dict()
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('visible'):
                uData = writeXml(self.infos[i].text())
                partInfoDef.setdefault(prop, {'userData': uData.replace(" ", "_"), 'active': self.checker[i].isChecked(), 'visible': True})
                i += 1

        # file = open(config_file_path, 'w')
        # json.dump(partInfoDef, file, indent=4, separators=(", ", ": "))
        # file.close()
        # file = open(config_file_path, 'r')
        # self.infoKeysUser = json.load(file).copy()
        # file.close()
        self.infoKeysUser = load_config_file()

        '''
        mb = QtGui.QMessageBox()
        mb.setWindowTitle("BOM Configuration")
        mb.setText("The configuration\nhas been saved")
        mb.exec_()
        '''

        self.finish()


    def addNewManField(self):
        """
        Create a new field
        """
        baseName = "Field"
        fieldLabel = self.newOne.text()
        indexref = 1
        fieldName = baseName + "_" + str(indexref)
        while fieldName in self.confTemplate:
            indexref += 1
            fieldName = baseName + "_" + str(indexref)
        self.newOne.setText('')
        self.addNewField(fieldName, fieldLabel)


    def addNewField(self, newRef, newField):
        """
        Write the new field in configuration template
        """
        self.confTemplate.setdefault(newRef, {'userData': newField, 'active': True, 'visible': True})

        # Label
        newLab = QtGui.QLabel(newRef)
        self.gridLayout.addWidget(newLab, self.i, 0)
        self.label.append(newLab)

        # Input field
        newOne = QtGui.QLineEdit()
        newOne.setText(newField)
        self.gridLayout.addWidget(newOne, self.i, 1)
        self.infos.append(newOne)

        # Checkbox
        checkLayout = QtGui.QVBoxLayout()
        checked = QtGui.QCheckBox()
        checked.setChecked(self.confTemplate.get(newRef).get('active'))
        self.gridLayout.addWidget(checked, self.i, 2)
        self.checker.append(checked)

        # Suppcombo
        self.suppCombo.addItem(newRef + " - " + newField)

        self.i += 1


    def deleteField(self):
        """
        Delete custom fields
        """
        delField = writeXml(self.suppCombo.currentText())
        fieldRef = delField.split("-")[0].strip(" ")
        fieldData = delField.split("-")[1].strip(" ")
        i = 0
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('visible'):
                if str(prop) == fieldRef and self.confTemplate.get(prop).get('userData') == fieldData:
                    self.label[i].deleteLater()
                    self.label.remove(self.label[i])
                    self.infos[i].deleteLater()
                    self.infos.remove(self.infos[i])
                    self.checker[i].deleteLater()
                    self.checker.remove(self.checker[i])
                    self.suppCombo.removeItem(i - len(self.infoKeysDefault))
                    self.refField = str(prop)
                i += 1

        self.confTemplate.pop(self.refField)

        return


    def updateAutoFieldlist(self):
        listUser = []
        for li in self.infoKeysUser:
            listUser.append(li)

        listDefault = self.infoKeysDefault.copy()
        for li in listUser:
            try:
                listDefault.remove(li)
            except:
                pass

        if listDefault == []:
            return None
        else:
            return listDefault


    def updateAutoField(self):
        """
        Update auto field (used when new default keys are added to the infoKeys.py)
        """
        upField = self.upCombo.currentText()
        self.upCombo.removeItem(self.upCombo.currentIndex())
        self.addNewField(upField, upField)


    # Define the UI
    # TODO : make it static
    def drawConfUI(self):
        self.label = []
        self.infos = []
        self.checker = []
        self.combo = []
        self.upcombo = []

        # Place the widgets with layouts
        self.mainLayout = QtGui.QVBoxLayout(self.form)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayoutButtons = QtGui.QGridLayout()
        self.gridLayoutUpdate = QtGui.QGridLayout()

        # 1st column holds the field names
        default = QtGui.QLabel('Field')
        self.gridLayout.addWidget(default, 0, 0)

        i = 1
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('visible'):
                default = QtGui.QLabel(prop)
                default.setToolTip(self.part_info_tooltip.get(prop))
                self.gridLayout.addWidget(default, i, 0)
                self.label.append(default)
                i += 1

        self.addnewLab = QtGui.QLabel('Field')
        self.gridLayoutButtons.addWidget(self.addnewLab, 0, 0)

        self.suppLab = QtGui.QLabel('Field')
        self.gridLayoutButtons.addWidget(self.suppLab, 1, 0)

        # 2nd column holds the data
        user = QtGui.QLabel('Name')
        self.gridLayout.addWidget(user, 0, 1)

        i = 1
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('visible'):
                propValue = QtGui.QLineEdit()
                propValue.setText(decodeXml(self.confTemplate.get(prop).get('userData')))
                self.gridLayout.addWidget(propValue, i, 1)
                self.infos.append(propValue)
                i += 1

        self.newOne = QtGui.QLineEdit()
        self.i = i
        self.gridLayoutButtons.addWidget(self.newOne, 0, 1)

        self.suppCombo =  QtGui.QComboBox()
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('visible'):
                if prop[0:6] == 'Field_':
                    fieldRef = prop
                    fieldData = decodeXml(self.confTemplate.get(prop).get('userData'))
                    self.suppCombo.addItem(fieldRef + " - " + fieldData)

        self.gridLayoutButtons.addWidget(self.suppCombo, 1, 1)

        # 3rd column has the Active checkbox
        active = QtGui.QLabel('Active')
        self.gridLayout.addWidget(active, 0, 2)

        i = 1
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('visible'):
                checkLayout = QtGui.QVBoxLayout()
                checked = QtGui.QCheckBox()
                checked.setChecked(self.confTemplate.get(prop).get('active'))
                self.gridLayout.addWidget(checked, i, 2)
                self.checker.append(checked)
                i += 1

        self.addnew = QtGui.QPushButton('Add')
        self.gridLayoutButtons.addWidget(self.addnew, 0, 2)
        self.suppBut = QtGui.QPushButton('Delete')
        self.gridLayoutButtons.addWidget(self.suppBut, 1, 2)

        # Actions
        self.addnew.clicked.connect(self.addNewManField)
        self.suppBut.clicked.connect(self.deleteField)

        # Insert layout in mainlayout
        self.mainLayout.addLayout(self.gridLayout)
        self.mainLayout.addLayout(self.gridLayoutButtons)

        # Show the update if any
        if self.updateAutoFieldlist() != None:
            updateLab = QtGui.QLabel('Update automatic input field')
            self.gridLayoutUpdate.addWidget(updateLab, 0, 0)
            self.upCombo = QtGui.QComboBox()
            self.gridLayoutUpdate.addWidget(self.upCombo, 1, 0)

            for prop in self.updateAutoFieldlist():
                self.upCombo.addItem(prop)
            self.upBut = QtGui.QPushButton('Update')
            self.gridLayoutUpdate.addWidget(self.upBut, 1, 1)

            # Actions
            self.upBut.clicked.connect(self.updateAutoField)

            # Insert layout in mainlayout
            self.mainLayout.addLayout(self.gridLayoutUpdate)


# Add the command in the workbench
Gui.addCommand('Asm4_infoPart', infoPartCmd())

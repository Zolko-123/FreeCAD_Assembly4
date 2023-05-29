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
hidden_part_info = infoKeys.hidden_part_info

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


def load_config_file_data():

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
        for prop in hidden_part_info:
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
        # has been checked before
        self.part = Asm4.getSelectedContainer()
        # Check and load if the configuration file exists
        try:
            file = open(config_file_path, 'r')
            self.infoKeysUser = json.load(file).copy()
            file.close()
        except:
            self.infoKeysUser = dict()

            for prop in infoKeys.partInfo:
                self.infoKeysUser.setdefault(prop, {'userData': prop, 'active': True, 'visible': True})

            for prop in infoKeys.partInfo_Invisible:
                self.infoKeysUser.setdefault(prop, {'userData': prop, 'active': True, 'visible': False})

        self.makePartInfo(self, self.part)
        self.infoTable = []
        self.getPartInfo()
        self.drawUI()


    def getPartInfo(self):
        self.infoTable.clear()
        for propuser in self.infoKeysUser:
            for prop in self.part.PropertiesList:
                if self.part.getGroupOfProperty(prop) == 'PartInfo':
                    if self.part.getTypeIdOfProperty(prop) == 'App::PropertyString':
                        if self.infoKeysUser.get(propuser).get('userData') == prop:
                            if self.infoKeysUser.get(propuser).get('active') and self.infoKeysUser.get(propuser).get('visible'):
                                value = self.part.getPropertyByName(prop)
                                self.infoTable.append([prop, value])


    # Add the default part information
    def makePartInfo(self, object, reset=False):
        for propuser in self.infoKeysUser:
            if self.infoKeysUser.get(propuser).get('active') and self.infoKeysUser.get(propuser).get('visible'):
                try:
                    object.part
                    if not hasattr(object.part, self.infoKeysUser.get(propuser).get('userData')):
                        object.part.addProperty('App::PropertyString', self.infoKeysUser.get(propuser).get('userData'), 'PartInfo')
                except AttributeError:
                    if object.TypeId == 'App::Part':
                        if not hasattr(object,self.infoKeysUser.get(propuser).get('userData')):
                            object.addProperty('App::PropertyString', self.infoKeysUser.get(propuser).get('userData'), 'PartInfo')
        return


    def addNew(self):
        for i, prop in enumerate(self.infoTable):
            if self.part.getGroupOfProperty(prop[0]) == 'PartInfo':
                if self.part.getTypeIdOfProperty(prop[0]) == 'App::PropertyString':
                    for propuser in self.infoKeysUser:
                        if self.infoKeysUser.get(propuser).get('userData') == prop[0]:
                            if self.infoKeysUser.get(propuser).get('active') and self.infoKeysUser.get(propuser).get('visible'):
                                text = self.infos[i].text()
                                setattr(self.part, prop[0], str(text))


    def editKeys(self):
        Gui.Control.closeDialog()
        Gui.Control.showDialog(infoPartConfUI())


    # Reset the list of properties
    def reInit(self):

        load_config_file_data()

        # List = self.part.PropertiesList
        # listpi = []
        # for prop in List:
        #     if self.part.getGroupOfProperty(prop) == 'PartInfo':
        #         listpi.append(prop)
        # for suppr in listpi: # delete all PartInfo properties
        #     self.part.removeProperty(suppr)

        # # Recover initial json file since fateners keys are being lost
        # partInfoDef = dict()
        # for prop in infoKeys.partInfo:
        #     partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': True})
        # for prop in infoKeys.partInfo_Invisible:
        #     partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': False})
        # try:
        #     os.mkdir(config_dir_path)
        # except:
        #     pass
        # file = open(config_file_path, 'w')
        # json.dump(partInfoDef, file)
        # file.close()


        '''
        mb = QtGui.QMessageBox()
        mb.setWindowTitle("Clear fileds")
        mb.setText("The Part Info field\nhas been cleared")
        mb.exec_()
        '''
        Asm4.warningBox("The Part Info field has been cleared")
        self.finish()


    def infoDefault(self):
        # infoKeys.infoDefault(self)
        # file = open(config_file_path, 'r')
        # infoKeysUser = json.load(file).copy()
        # file.close()
        infoKeysUser = load_config_file_data()
        try:
            self.TypeId
            part = self
        except AttributeError:
            part = self.part
        doc = part.Document
        for i in range(len(part.Group)):
            if part.Group[i].TypeId == 'PartDesign::Body':
                body = part.Group[i]
                for i in range(len(body.Group)):
                    if body.Group[i].TypeId == 'PartDesign::Pad':
                        pad = body.Group[i]
                        try:
                            sketch = pad.Profile[0]
                        except NameError :
                            # print('There is no Sketch on a Pad of the Part', part.FullName)
                            pass
            try:
                self.LabelDoc(self, part, doc)
            except:
                # print('LabelDoc: there is no Document on the Part ', part.FullName)
                pass
            try:
                self.LabelPart(self, part)
            except:
                # print('LabelPart: Part does not exist')
                pass
            try:
                self.PadLength(self, part, pad)
            except:
                # print('PadLenght: there is no Pad in the Part ', part.FullName)
                pass
            try:
                self.ShapeLength(self, part, sketch)
            except:
                # print('ShapeLength: there is no Sketch in the Part ', part.FullName)
                pass
            try:
                self.ShapeVolume(self, part, body)
            except:
                # print('ShapeVolume: there is no Shape in the Part ', part.FullName)
                pass


    def LabelDoc(self, part, doc):

        # Recover doc_name from parts_dict
        try:
            if infoKeysUser.get("Doc_Label").get('active'):
                try:
                    doc_name = getattr(obj, infoKeysUser.get("Doc_Label").get('userData'))
                except AttributeError:
                    doc_name = obj.Document.Name
        except:
            doc_name = obj.Document.Name

        auto_info_field = infoKeysUser.get("Doc_Label").get('userData')
        auto_info_fill = doc_name
        try:
            self.TypeId
            setattr(part, auto_info_field, auto_info_fill)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == auto_info_field:
                        self.infos[i].setText(auto_info_fill)
            except AttributeError:
                self.infos[i].setText("-")


    def LabelPart(self, part):
        auto_info_field = infoKeysUser.get('Part_Label').get('userData')
        auto_info_fill = part.Label
        try:
            self.TypeId
            setattr(part, auto_info_field, auto_info_fill)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == auto_info_field:
                        self.infos[i].setText(auto_info_fill)
            except AttributeError:
                self.infos[i].setText("-")


    def PadLength(self, part, pad):
        auto_info_field = infoKeysUser.get('Pad_Length').get('userData')
        try:
            auto_info_fill = str(pad.Length).replace('mm','')
        except AttributeError:
            return
        try:
            self.TypeId
            setattr(part, auto_info_field, auto_info_fill)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == auto_info_field:
                        self.infos[i].setText(auto_info_fill)
            except AttributeError:
                self.infos[i].setText("-")


    def ShapeLength(self, part, sketch):
        auto_info_field = infoKeysUser.get('Shape_Length').get('userData')
        try:
            auto_info_fill = str(sketch.Shape.Length)
        except AttributeError:
            return
        try:
            self.TypeId
            setattr(part, auto_info_field, auto_info_fill)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == auto_info_field:
                        self.infos[i].setText(auto_info_fill)
            except AttributeError:
                self.infos[i].setText("-")


    def ShapeVolume(self, part, body):
        auto_info_field = infoKeysUser.get('Shape_Volume').get('userData')
        bbc = body.Shape.BoundBox
        auto_info_fill = str(str(round(bbc.ZLength, 3)) + str(' mm x ') + str(round(bbc.YLength, 3)) + str(' mm x ') + str(round(bbc.XLength, 3)) + str(' mm'))
        try:
            self.TypeId
            setattr(part, auto_info_field, auto_info_fill)
        except AttributeError:
            try:
                for i in range(len(self.infoTable)):
                    if self.infoTable[i][0] == auto_info_field:
                        self.infos[i].setText(auto_info_fill)
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
        self.reinit.clicked.connect(self.reInit)
        self.autoFill.clicked.connect(self.infoDefault)

        '''
        test = False
        try:
            if self.infoTable[0][1] == '':
                test = True
        except IndexError:
            test = True
        if test:
            self.infoDefault()
            self.addNew()
        '''



class infoPartConfUI():

    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_PartInfo.svg')
        self.form.setWindowIcon(QtGui.QIcon(iconFile))
        self.form.setWindowTitle("Edit Part Information")

        self.infoKeysDefault = infoKeys.partInfo.copy()
        self.infoToolTip = infoKeys.infoToolTip.copy()
        file = open(config_file_path, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()

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
                    Asm4.warningBox("Fields Name cannot be blank. You must disable or delete it")
                    return
                i += 1

        # Restore file and appen new config
        partInfoDef = dict()
        for prop in infoKeys.partInfo:
            partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': True})
        for prop in infoKeys.partInfo_Invisible:
            partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': False})

        i = 0
        # config = dict()
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('visible'):
                uData = writeXml(self.infos[i].text())
                partInfoDef.setdefault(prop, {'userData': uData.replace(" ", "_"), 'active': self.checker[i].isChecked(), 'visible': True})
                i += 1

        file = open(config_file_path, 'w')
        json.dump(partInfoDef, file)
        file.close()

        file = open(config_file_path, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()

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
                default.setToolTip(self.infoToolTip.get(prop))
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

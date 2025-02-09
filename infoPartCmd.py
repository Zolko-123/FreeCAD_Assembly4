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
from Asm4_Translate import _atr, QT_TRANSLATE_NOOP, translate
import infoKeys

#This is partcoded part information.
partInfo = [
    'BomKey',
    'DrawingName',
    'DrawingRevision',
    'PartID',
    'PartDescription']



infoToolTip = {
    'BomKey': translate("Asm4_InfoPart", 'BomKey'),
    'DrawingName':     translate("Asm4_InfoPart", 'Document or File name'),
    'DrawingRevision': translate("Asm4_InfoPart", 'Document Revision'),
    'PartID':     translate("Asm4_InfoPart", 'Part ID'),
    'PartDescription': translate("Asm4_InfoPart", 'Part Description')}

# Remaining fields that can be customized
try:
    import infoKeys
    partInfo += infoKeys.partInfoUserAdded
    infoToolTip.update(infoKeys.infoToolTipUserAdded)
except ImportError:
    pass




partInfo_Invisible = [
    'FastenerDiameter',
    'FastenerLength',
    'FastenerType']

infoToolTip_Invisible = {
    'FastenerDiameter': translate("Asm4_InfoPart", 'Fastener diameter'),
    'FastenerLength':   translate("Asm4_InfoPart", 'Fastener length'),
    'FastenerType':     translate("Asm4_InfoPart", 'Fastener type')}

ConfUserDir = os.path.join(App.getUserAppDataDir(),'Templates')
ConfUserFilename = "Asm4_infoPartConf.json"
ConfUserFilejson = os.path.join(ConfUserDir, ConfUserFilename)



# Check if the configuration file exists
try:
    file = open(ConfUserFilejson, 'r')
    file.close()
except:
    partInfoDef = dict()
    for prop in partInfo:
        partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': True})
    for prop in partInfo_Invisible:
        partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': False})
    try:
        os.mkdir(ConfUserDir)
    except:
        pass
    file = open(ConfUserFilejson, 'x')
    json.dump(partInfoDef, file)
    file.close()


"""
    +-----------------------------------------------+
    |                  Helper Tools                 |
    +-----------------------------------------------+
"""
def writeXml(text):
    text = text.encode('unicode_escape').decode().replace('\\', '_x_m_l_')
    return text

def decodeXml(text):
    text = text.replace('_x_m_l_', '\\').encode().decode('unicode_escape')
    return text

def infoDefault(part):
    # infoKeys.infoDefault(self)

    #Values are being populated through the back door
    #if the diaglog control is open and you click on autofill
    #the dialog needs to be closed otherwise
    #backdoor values will be overwritten when you press ok..



    file = open(ConfUserFilejson, 'r')
    infoKeysUser = json.load(file).copy()
    file.close()

    #trying to understand this. Not positive that I'm correct here.
    #This routine attempts to autopopulate the fields that are defined in infoKeys.py and also appear in the json file
    #it appears that these fields are inserted into self or self.part by infoPartCmd.infoPartUI.makePartInfo

    doc = part.Document
    print (len(part.Group))
    part.Type
    if part.Type =="Assembly" and part.TypeId == 'App::Part':

        print (translate("Asm4_InfoPart", "We have an assembly"))
        try:
            infoKeys.AssignCustomerValuesIntoUserFieldsForPartWithSingleBody(part, doc, None)
        except NotImplementedError as e:
            AssignValuesForAutofile(part, doc,None)

    elif part.Type !='Assembly' and part.TypeId == 'App::Part':
        #We are looking at the standard instance where we have a ASM4 which has a single
        #PartDesign:: Body given that use case
        try:
            ObjSingleBody = check_single_body(part)
        except Exception as e:
            print (str(e))
            raise NotImplementedError(f"Logic only implement for Part with single body this exception was thrown: {str(e)}")
        # 'body' contains the single PartDesign::Body object
        print(f"Part contains a single PartDesign::Body: {ObjSingleBody.Name}")
        #in JT use case The Fcstd file name contains the Part_id (a portion of it if it is a mult-level part
        #Since this is not how everyone will want to do this.
        #Also file name contains a revision
        #Probably should be looking at a separate .py file that is customized to the users business rules.
        try:
            infoKeys.AssignCustomerValuesIntoUserFieldsForPartWithSingleBody(part, doc, ObjSingleBody)
        except NotImplementedError as e:
            print (str (e))
            AssignValuesForAutofile(part, doc,ObjSingleBody)

    else:
        # There is no PartDesign::Body or more than one found in the 'part'
        raise NotImplementedError("Need to develop logic for something that is neither a part or an assembly")
        print(translate("Asm4_InfoPart", "Part does not contain a single PartDesign::Body."))

    '''
        # This needs to be moved up into the for look
        try:
            self.LabelDoc(self, part, doc)
        except NameError:
            #print('LabelDoc: there is no Document on the Part ', part.FullName)
            pass
        except Exception as e:
            print ("Exception"+e)

    try:
        self.GetPartName(part)
        #info_cmd = infoPartCmd()  # Create an instance of infoPartCmd
        #info_cmd.GetPartName(part)  # Call GetPartName from infoPartCmd instance
    except NameError:
        # print('LabelPart: Part does not exist')
        pass


        try:
            self.PadLength(self, part, pad)
        except NameError:
            # print('PadLenght: there is no Pad in the Part ', part.FullName)
            pass
        try:
            self.ShapeLength(self, part, sketch)
        except NameError:
            # print('ShapeLength: there is no Sketch in the Part ', part.FullName)
            pass
        try:
            self.ShapeVolume(self, part, body)
        except NameError:
            # print('ShapeVolume: there is no Shape in the Part ', part.FullName)
            pass
        '''

def check_single_body(part):
    num_bodies = 0
    objBody = None

    for obj in part.Group:
        if obj.TypeId == 'PartDesign::Body':
            num_bodies += 1
            objBody = obj

    if num_bodies == 0:
        # No PartDesign::Body found in the group
        return None
    elif num_bodies == 1:
        # Only one PartDesign::Body found in the group
        return objBody
    else:
        # More than one PartDesign::Body found in the group
        return None

def AssignValuesForAutofile(part, doc, singleBodyOfPart):
    #todo if part is not
    try:

        infoKeys.AssignCustomerValuesIntoUserFieldsForPartWithSingleBody(part, doc, singleBodyOfPart)
    except Exception as e:
        print (f"Customization failed or is not setup : {str(e)}  Attempting to insert default values")
        try:
            try:
                part.DrawingName
            except Exception as e:
                # if we're here it means that there was no cust
                #JT not sure at the moment if we should fix it here or just add logic upstream to prevent this from happening
                raise Exception(f"{part.FullName} in {doc.FileName} is missing Part information fields. It needs to be reset in Edit Part Information- Configure fields .")


            part.DrawingName =os.path.basename(doc.FileName)
            part.PartID = doc.Label
            if singleBodyOfPart != None:
                part.PartDescription = singleBodyOfPart.Label
        except Exception as e:
            raise e



"""
    +-----------------------------------------------+
    |                Info Part Command              |
    +-----------------------------------------------+
"""
class infoPartCmd():

    def __init__(self):
        super(infoPartCmd, self).__init__()

    def GetResources(self):
        tooltip  = translate("Asm4_InfoPart", "<p>Edit Part information</p>" + \
        "<p>User-supplied information can be added to a part</p>")
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_PartInfo.svg')
        return {"MenuText": translate("Asm4_InfoPart", "Edit Part Information"), "ToolTip": tooltip, "Pixmap": iconFile}

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
        self.form.setWindowTitle(translate("Asm4_InfoPart", "Edit Part Information"))
        # has been checked before
        self.part = Asm4.getSelectedContainer()
        # Check and load if the configuration file exists
        try:
            file = open(ConfUserFilejson, 'r')
            self.infoKeysUser = json.load(file).copy()
            file.close()
        except:
            self.infoKeysUser = dict()
            for prop in partInfo:
                self.infoKeysUser.setdefault(prop, {'userData': prop, 'active': True, 'visible': True})
            for prop in partInfo_Invisible:
                self.infoKeysUser.setdefault(prop, {'userData': prop, 'active': True, 'visible': False})
        '''
            try:
                os.mkdir(ConfUserDir)
            except:
                pass
            file = open(ConfUserFilejson, 'x')
            json.dump(partInfoDef, file)
            file.close()

        # should be safe now
        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()
        '''
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
                    #if object.part doesn't exist at the object Typeid is App::Part through it in there?
                    #need to think on that one.
                    object.part
                    if not hasattr(object.part, self.infoKeysUser.get(propuser).get('userData')):
                        object.part.addProperty('App::PropertyString', self.infoKeysUser.get(propuser).get('userData'), 'PartInfo')
                except AttributeError:
                    if object.TypeId == 'App::Part':
                        if not hasattr(object,self.infoKeysUser.get(propuser).get('userData')):
                            object.addProperty('App::PropertyString', self.infoKeysUser.get(propuser).get('userData'), 'PartInfo')



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
        List = self.part.PropertiesList
        listpi = []
        for prop in List:
            if self.part.getGroupOfProperty(prop) == 'PartInfo':
                listpi.append(prop)
        for suppr in listpi: # delete all PartInfo properties
            self.part.removeProperty(suppr)

        # Recover initial json file since fasteners keys are being lost
        # JT Not sure about above being an accurate statement.
        partInfoDef = dict()
        for prop in partInfo:
            partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': True})
        for prop in partInfo_Invisible:
            partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': False})
        try:
            os.mkdir(ConfUserDir)
        except:
            pass
        file = open(ConfUserFilejson, 'w')
        json.dump(partInfoDef, file)
        file.close()

        '''
        mb = QtGui.QMessageBox()
        mb.setWindowTitle("Clear fileds")
        mb.setText("The Part Info field\nhas been cleared")
        mb.exec_()
        '''
        Asm4.warningBox(translate("Asm4_InfoPart", "The Part Info field has been cleared"))
        self.finish()


    def infoDefault(self):
        # infoKeys.infoDefault(self)

        #Values are being populated through the back door
        #if the diaglog control is open and you click on autofill
        #the dialog needs to be closed otherwise
        #backdoor values will be overwritten when you press ok..
        Gui.Control.closeDialog()

        try:
            self.TypeId
            part = self
        except AttributeError:
            part = self.part
        infoDefault(part)


    def SetPartInfoValue(self,fieldName, fieldvalue):


        auto_info_field = self.infoKeysUser.get(fieldName).get('userData')
        try:
            #This sets the value behind the curtain
            self.infoKeysUser[auto_info_field][1]= fieldvalue
            #if the Edit part information window is open and you press ok what ever is in that textbox will overwrite



        except Exception as e:
            #print (f" This expection was thrown: {str(e)})
            # Re throw the exception
            raise e



    def GetPartName(self, part):
        auto_info_field = infoKeysUser.get('PartName').get('userData')
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

    '''
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
    '''


    def finish(self):
        Gui.Control.closeDialog()

    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok

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
        self.confFields = QtGui.QPushButton(translate("Asm4_InfoPart", 'Configure fields'))
        self.confFields.setToolTip(translate("Asm4_InfoPart", 'Edit fields'))
        self.reinit = QtGui.QPushButton(translate("Asm4_InfoPart", 'Reset fields'))
        self.reinit.setToolTip(translate("Asm4_InfoPart", 'Reset fields'))
        self.autoFill = QtGui.QPushButton(translate("Asm4_InfoPart", 'Autofill data'))
        self.autoFill.setToolTip(translate("Asm4_InfoPart", 'Autofill fields'))
        self.buttonsLayout.addWidget(self.confFields)
        self.buttonsLayout.addWidget(self.reinit)
        self.buttonsLayout.addWidget(self.autoFill)

        self.mainLayout.addLayout(self.buttonsLayout)

        # Actions
        self.confFields.clicked.connect(self.editKeys)
        self.reinit.clicked.connect(self.reInit)
        self.autoFill.clicked.connect(self.infoDefault)

'''
#JT This seems to be creating some issue Lets disable for the moment.'
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
        self.form.setWindowTitle(translate("Asm4_InfoPart", "Edit Part Information"))

        self.infoKeysDefault = partInfo.copy()
        self.infoToolTip = infoToolTip.copy()
        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()

        self.confTemplate = dict()
        self.confTemplate = self.infoKeysUser.copy()

        self.drawConfUI()

    def finish(self):
        Gui.Control.closeDialog()

    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok

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
                    Asm4.warningBox(translate("Asm4_InfoPart", "Fields Name cannot be blank. You must disable or delete it"))
                    return
                i += 1

        # Restore file and appen new config
        partInfoDef = dict()
        for prop in infoPartCmd.partInfo:
            partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': True})
        for prop in infoPartCmd.partInfo_Invisible:
            partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': False})

        i = 0
        # config = dict()
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('visible'):
                uData = writeXml(self.infos[i].text())
                partInfoDef.setdefault(prop, {'userData': uData.replace(" ", "_"), 'active': self.checker[i].isChecked(), 'visible': True})
                i += 1

        file = open(ConfUserFilejson, 'w')
        json.dump(partInfoDef, file)
        file.close()

        file = open(ConfUserFilejson, 'r')
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
        default = QtGui.QLabel(translate("Asm4_InfoPart", 'Field'))
        self.gridLayout.addWidget(default, 0, 0)

        i = 1
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('visible'):
                default = QtGui.QLabel(prop)
                default.setToolTip(self.infoToolTip.get(prop))
                self.gridLayout.addWidget(default, i, 0)
                self.label.append(default)
                i += 1

        self.addnewLab = QtGui.QLabel(translate("Asm4_InfoPart", 'Field'))
        self.gridLayoutButtons.addWidget(self.addnewLab, 0, 0)

        self.suppLab = QtGui.QLabel(translate("Asm4_InfoPart", 'Field'))
        self.gridLayoutButtons.addWidget(self.suppLab, 1, 0)

        # 2nd column holds the data
        user = QtGui.QLabel(translate("Asm4_InfoPart", 'Name'))
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
        active = QtGui.QLabel(translate("Asm4_InfoPart", 'Active'))
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

        self.addnew = QtGui.QPushButton(translate("Asm4_InfoPart", 'Add'))
        self.gridLayoutButtons.addWidget(self.addnew, 0, 2)
        self.suppBut = QtGui.QPushButton(translate("Asm4_InfoPart", 'Delete'))
        self.gridLayoutButtons.addWidget(self.suppBut, 1, 2)

        # Actions
        self.addnew.clicked.connect(self.addNewManField)
        self.suppBut.clicked.connect(self.deleteField)

        # Insert layout in mainlayout
        self.mainLayout.addLayout(self.gridLayout)
        self.mainLayout.addLayout(self.gridLayoutButtons)

        # Show the update if any
        if self.updateAutoFieldlist() != None:
            updateLab = QtGui.QLabel(translate("Asm4_InfoPart", 'Update automatic input field'))
            self.gridLayoutUpdate.addWidget(updateLab, 0, 0)
            self.upCombo = QtGui.QComboBox()
            self.gridLayoutUpdate.addWidget(self.upCombo, 1, 0)

            for prop in self.updateAutoFieldlist():
                self.upCombo.addItem(prop)
            self.upBut = QtGui.QPushButton(translate("Asm4_InfoPart", 'Update'))
            self.gridLayoutUpdate.addWidget(self.upBut, 1, 1)

            # Actions
            self.upBut.clicked.connect(self.updateAutoField)

            # Insert layout in mainlayout
            self.mainLayout.addLayout(self.gridLayoutUpdate)


# Add the command in the workbench
Gui.addCommand('Asm4_infoPart', infoPartCmd())

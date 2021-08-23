#!/usr/bin/env python3
# coding: utf-8
#
# configurationEngine.py
#
# The code to save and restore configurations, using spreadsheets


import os, re

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4

ASM4_CONFIG_TYPE        = 'Asm4::ConfigurationTable'
HEADER_CELL             = 'A1'
DESCRIPTION_CELL        = 'A2'
OBJECTS_START_ROW       = '5'
OBJECT_NAME_COL         = 'A'
OBJECT_VISIBLE_COL      = 'B'
OBJECT_ASM_TYPE_COL     = 'C'
OFFSET_POS_X_COL        = 'D'
OFFSET_POS_Y_COL        = 'E'
OFFSET_POS_Z_COL        = 'F'
OFFSET_ROT_YAW_COL      = 'G'
OFFSET_ROT_PITCH_COL    = 'H'
OFFSET_ROT_ROLL_COL     = 'I'



"""
    +-----------------------------------------------+
    |     create a new empty configuration table    |
    +-----------------------------------------------+
"""
def createConfig(name, description):
    group = getConfGroup()
    if not group:
        # create a group Configurations to store various config tables
        assy = Asm4.getAssembly()
        if assy:
            group = assy.newObject('App::DocumentObjectGroup','Configurations')
        else:
            FCC.PrintWarnin('No assembly container here, quitting\n')
            return
    # Create the document
    conf = group.newObject('Spreadsheet::Sheet', name)
    headerRow = str(int(OBJECTS_START_ROW)-1)
    #conf.set(HEADER_CELL,           'Assembly4 configuration table')
    conf.set(HEADER_CELL,           ASM4_CONFIG_TYPE)
    conf.set(DESCRIPTION_CELL,      str(description))
    conf.set(OBJECT_NAME_COL      + headerRow, 'ObjectName')
    conf.set(OBJECT_VISIBLE_COL   + headerRow, 'Visible')
    conf.set(OBJECT_ASM_TYPE_COL  + headerRow, 'Assembly Type')
    conf.set(OFFSET_POS_X_COL     + headerRow, 'Pos. X')
    conf.set(OFFSET_POS_Y_COL     + headerRow, 'Pos. Y')
    conf.set(OFFSET_POS_Z_COL     + headerRow, 'Pos. Z')
    conf.set(OFFSET_ROT_YAW_COL   + headerRow, 'Rot. Yaw')
    conf.set(OFFSET_ROT_PITCH_COL + headerRow, 'Rot. Pitch')
    conf.set(OFFSET_ROT_ROLL_COL  + headerRow, 'Rot. Roll')
    return conf


"""
    +-----------------------------------------------+
    |           Apply configuration command         |
    +-----------------------------------------------+
"""
class applyConfigurationCmd:
    def __init__(self):
        super(applyConfigurationCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Apply configuration",
                "ToolTip": "Applies selected configuration\nConfigurations allow to set visibilities and offsets of parts",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_applyConfig.svg')
                }

    def IsActive(self):
        # if a spreadsheet in a Group called "Configuration" is selected
        if Asm4.getAssembly() and len(Gui.Selection.getSelection()) == 1:
            config = Gui.Selection.getSelection()[0]
            if getConfGroup() and isAsm4Config(config):
                return True
        return False

    def Activated(self):
        config = Gui.Selection.getSelection()[0]        
        restoreConfiguration(config.Name)
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection( Asm4.getAssembly() )
        
        
        
"""
    +-----------------------------------------------+
    |         General configuration Task UI         |
    +-----------------------------------------------+
"""
class openConfigurationsCmd:
    def __init__(self):
        super(openConfigurationsCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Open configurations panel",
                "ToolTip": "Configurations allow to set visibilities and offsets of parts",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_Configurations.svg')
                }

    def IsActive(self):
        # Will handle LCSs only for the Assembly4 model
        #if Asm4.getSelectedLink() or Asm4.getModelSelected():
        if Asm4.getSelectedLink() or Asm4.getAssembly():
            return True
        return False

    def Activated(self):
        ui = openConfigurationsUI()
        Gui.Control.showDialog(ui)



class openConfigurationsUI():
    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base
        iconFile = os.path.join( Asm4.iconPath , 'Asm4_Variables.svg')
        self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle('Assembly Configurations')

        # draw the GUI, objects are defined later down
        self.drawUI()
        self.initUI()

    # standard FreeCAD Task panel buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Ok)

    # OK = apply and close
    def accept(self):
        if len(self.configList.selectedItems()) == 1:
            self.Restore()
        Gui.Control.closeDialog()
        
    # Apply without closing, so user can cycle through configurations
    def clicked(self, button):
        if button == QtGui.QDialogButtonBox.Apply:
            if len(self.configList.selectedItems()) == 1:
                self.Restore()

    # create a new config is done in a separate window
    def onNewConfig(self):
        Gui.runCommand( 'Asm4_newConfiguration' )
        Gui.Control.closeDialog()

    # restore existing configuration
    def Restore(self):
        selectedItems = self.configList.selectedItems()
        if len(selectedItems) != 1:
            Asm4.warningBox('Please select a configuration in the list')
            return
        confName = self.configList.currentItem().name
        restoreConfiguration(confName)

    # delete selected configuration
    def onDelete(self):
        selectedItems = self.configList.selectedItems()
        if len(selectedItems) == 1:
            confName = self.configList.currentItem().name
            conf = getConfig(confName)
            if isAsm4Config(conf):
                confirm = Asm4.confirmBox('This will delete configuration "' + confName + '"?')
                if confirm:
                    App.ActiveDocument.removeObject(confName)
                else:
                    FCC.PrintMessage('Configuration "' + confName + '" not touched\n')
            else:
                FCC.PrintMessage('Object "' + confName + '" is not a valid Assembly4 configuration, leaving untouched\n')
            # rescan configuration list
            self.initUI()


    # overwrite existing configuration
    def onOverwrite(self):
        selectedItems = self.configList.selectedItems()
        if len(selectedItems) == 1:
            confName = self.configList.currentItem().name
            conf = getConfig(confName)
            confDescr = getConfigDescription(conf)
            # confirmation is asked in that function
            SaveConfiguration( confName, confDescr )


    # Cancel
    def reject(self):
        Gui.Control.closeDialog()

    # fill description
    def onConfClicked(self):
        selectedItems = self.configList.selectedItems()
        if len(selectedItems) == 1:
            confName = self.configList.currentItem().name
            #FCC.PrintMessage('confName = '+confName+'\n')
            #FCC.PrintMessage('confText = '+self.configList.currentItem().text()+'\n')
            conf = getConfig(confName)
            #FCC.PrintMessage('conf.Name = '+conf.Name+'\n')            
            description = getConfigDescription(conf)
            self.configDescription.clear()
            self.configDescription.setPlainText(description)


    # initialise UI
    def initUI(self):
        self.configDescription.clear()
        self.configList.clear()
        # Fill the configurations list
        confGroup = getConfGroup()
        if confGroup:
            for obj in confGroup.OutList:
                #if obj.TypeId == 'Spreadsheet::Sheet':
                if isAsm4Config(obj):
                    #self.addListEntry(obj.Label, getConfigDescription(obj))
                    newItem = ListEntry(obj.Name)
                    newItem.setText(obj.Label)
                    self.configList.addItem(newItem)


    # defines the UI, only static elements
    def drawUI(self):
        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self.form)

        # List of configurations
        self.mainLayout.addWidget(QtGui.QLabel("Available configurations:"))
        self.configList = QtGui.QListWidget()
        self.configList.setMinimumHeight(100)
        self.mainLayout.addWidget(self.configList)
        # Descriptions
        self.mainLayout.addWidget(QtGui.QLabel("Description:"))
        self.configDescription = QtGui.QTextEdit()
        self.configDescription.setMinimumHeight(100)
        self.configDescription.setReadOnly(True)
        self.mainLayout.addWidget(self.configDescription)
        # Buttons
        self.buttonLayout = QtGui.QHBoxLayout()
        self.newButton = QtGui.QPushButton('New')
        self.deleteButton = QtGui.QPushButton('Delete')
        self.overwriteButton = QtGui.QPushButton('Overwrite')
        # the button layout
        self.buttonLayout.addWidget(self.newButton)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.deleteButton)
        self.buttonLayout.addWidget(self.overwriteButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # apply the layout to the main window
        self.form.setLayout(self.mainLayout)

        # Actions
        self.configList.itemClicked.connect( self.onConfClicked )
        self.newButton.clicked.connect(self.onNewConfig)
        self.deleteButton.clicked.connect(self.onDelete)
        self.overwriteButton.clicked.connect(self.onOverwrite)


"""
    +-----------------------------------------------+
    |        Create new configuration Button        |
    +-----------------------------------------------+
"""
class newConfigurationCmd:
    def __init__(self):
        super(newConfigurationCmd,self).__init__()
        self.UI = QtGui.QDialog()
        self.drawUI()

    def GetResources(self):
        return {"MenuText": "New configuration",
                "ToolTip": "Create a new configuration of the assembly",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_applyConfig.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if Asm4.getAssembly():
            return True
        return False 


    def Activated(self):
        # Now we can draw the UI
        self.UI.show()
        self.configName.clear()
        self.configDescription.clear()
        # Fill the configurations list
        self.configList.clear()
        confGroup = getConfGroup()
        if confGroup:
            for obj in confGroup.OutList:
                #if obj.TypeId == 'Spreadsheet::Sheet':
                if isAsm4Config(obj):
                    #self.addListEntry(obj.Label, getConfigDescription(obj))
                    newItem = ListEntry(obj.Name)
                    newItem.setText(obj.Label)
                    self.configList.addItem(newItem)


    def onOK(self):
        confName = self.configName.text().strip()
        confDescr = self.configDescription.toPlainText().strip()
        if confName == '':
            Asm4.warningBox('Please specify configuration name!')
            self.configName.setFocus()
            return
        # if no description provided, set the name as description
        if confDescr == '':
            confDescr = ' '
        SaveConfiguration( confName, confDescr )
        self.UI.close()


    def onCancel(self):
        self.UI.close()
        
        
    # Verify and handle bad names similar to the spreadsheet workbench
    def onNameEdited(self):
        pattern = re.compile("^[A-Za-z][_A-Za-z0-9]*$")
        if pattern.match(self.configName.text()):
            self.configName.setStyleSheet("color: black;")
            self.OkButton.setEnabled(True)
        else:
            self.configName.setStyleSheet("color: red;")
            self.OkButton.setEnabled(False)


    # defines the UI, only static elements
    def drawUI(self):
        # Our main window will be a QDialog
        self.UI.setWindowTitle('Create a new assembly configuration')
        self.UI.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.UI.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.UI.setMinimumWidth(400)
        self.UI.setModal(False)
        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        # Configuration name
        self.mainLayout.addWidget(QtGui.QLabel("Enter configuration name:"))
        self.configName = QtGui.QLineEdit()
        self.mainLayout.addWidget(self.configName)
        # Configuration description
        self.mainLayout.addWidget(QtGui.QLabel("Description (optional):"))
        self.configDescription = QtGui.QTextEdit()
        self.configDescription.setMinimumHeight(100)
        self.mainLayout.addWidget(self.configDescription)
        # List of configurations
        self.mainLayout.addWidget(QtGui.QLabel("Existing configurations:"))
        self.configList = QtGui.QListWidget()
        self.configList.setMinimumHeight(100)
        self.mainLayout.addWidget(self.configList)
        
        # Buttons
        self.buttonLayout = QtGui.QHBoxLayout()
        # Cancel button
        self.CancelButton = QtGui.QPushButton('Cancel')
        # OK button
        self.OkButton = QtGui.QPushButton('OK')
        self.OkButton.setDefault(True)
        # the button layout
        self.buttonLayout.addWidget(self.CancelButton)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.OkButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.OkButton.clicked.connect(self.onOK)
        self.CancelButton.clicked.connect(self.onCancel)
        self.configName.textEdited.connect(self.onNameEdited)




"""
    +-----------------------------------------------+
    |         Save configuration functions          |
    +-----------------------------------------------+
"""


def SaveConfiguration(confName, description):
    FCC.PrintMessage('Saving configuration to "' + confName + '"\n')
    #conf = getConfig(confName, 'Configurations')
    conf = getConfig(confName)
    if conf and isAsm4Config(conf):
        confirm = Asm4.confirmBox('This will overwrite existing configuration "' + confName + '"')
        if not confirm:
            FCC.PrintMessage('Cancel save of configuration "' + confName + '"\n')
            return
        else:
            setConfigDescription(conf, description)
    else:
        conf = createConfig(confName, description)

    assy = Asm4.getAssembly()
    link  = Asm4.getSelectedLink()
    if link:
        SaveObject(conf, link)
    else:
        SaveSubObjects(conf, assy)            
    conf.recompute(True)


def SaveSubObjects(conf, container):
    for objName in container.getSubObjects():
        obj = container.getSubObject(objName, 1)
        # only save properties of objects that are derived from Part::Feature
        if obj.isDerivedFrom('Part::Feature'):
            SaveObject(conf, obj)


def SaveObject(conf, obj):
    # parse App::Part containers, and only those
    if obj.TypeId == 'App::Part':
        SaveSubObjects(conf, obj)

    parentObj, objFullName = obj.Parents[0]
    #objName = App.ActiveDocument.Name + '.' + parentObj.Name + '.' + objFullName
    objName = parentObj.Name + '.' + objFullName[0:-1]

    row = GetObjectRow(conf, objName)
    if row is None:
        conf.insertRows(OBJECTS_START_ROW, 1)
        row = OBJECTS_START_ROW

    conf.set( OBJECT_NAME_COL       + row,  objName )
    conf.setAlias(OBJECT_NAME_COL   + row,  GetValidAlias(objName) )
    # always store visibility info
    conf.set( OBJECT_VISIBLE_COL    + row,  str(obj.ViewObject.Visibility) )
    # check how this object is assembled
    asmType = '-'
    if hasattr(obj,'AssemblyType'):
        asmType = obj.AssemblyType
    conf.set( OBJECT_ASM_TYPE_COL       + row,  str(asmType) )
    if asmType == 'Asm4EE':
        offset = obj.AttachmentOffset
        conf.set( OFFSET_POS_X_COL      + row,  str(offset.Base.x) )
        conf.set( OFFSET_POS_Y_COL      + row,  str(offset.Base.y) )
        conf.set( OFFSET_POS_Z_COL      + row,  str(offset.Base.z) )
        conf.set( OFFSET_ROT_YAW_COL    + row,  str(offset.Rotation.toEuler()[0]) )
        conf.set( OFFSET_ROT_PITCH_COL  + row,  str(offset.Rotation.toEuler()[1]) )
        conf.set( OFFSET_ROT_ROLL_COL   + row,  str(offset.Rotation.toEuler()[2]) )





"""
    +-----------------------------------------------+
    |         Restore configuration functions       |
    +-----------------------------------------------+
"""
def restoreConfiguration(confName):
    FCC.PrintMessage('Restoring configuration "' + confName + '"\n')
    #doc = getConfig(confName, 'Configurations')
    conf = getConfig(confName)
    assy = Asm4.getAssembly()
    link = Asm4.getSelectedLink()
    if link:
        restoreObject(conf, link)
    else:
        restoreSubObjects(conf, assy)
    App.ActiveDocument.recompute()

# parse container
def restoreSubObjects(conf, container):
    for objName in container.getSubObjects():
        obj = container.getSubObject(objName, 1)
        restoreObject(conf, obj)

def restoreObject(conf, obj):
    # parse App::Part containers, and only those
    if obj.TypeId == 'App::Part':
        restoreSubObjects(conf, obj)

    parentObj, objFullName = obj.Parents[0]
    #objName = App.ActiveDocument.Name + '.' + parentObj.Name + '.' + objFullName
    objName = parentObj.Name + '.' + objFullName

    row = GetObjectRow(conf, objName)
    if row is None:
        FCC.PrintMessage('No data for object "' + objName + '" in configuration "' + conf.Name + '"\n')
        return

    vis   = conf.get( OBJECT_VISIBLE_COL   + row )
    obj.ViewObject.Visibility = (vis=='True')
    asm   = str(conf.get( OBJECT_ASM_TYPE_COL  + row ))
    if asm == 'Asm4EE':
        x     = conf.get( OFFSET_POS_X_COL     + row )
        y     = conf.get( OFFSET_POS_Y_COL     + row )
        z     = conf.get( OFFSET_POS_Z_COL     + row )
        yaw   = conf.get( OFFSET_ROT_YAW_COL   + row )
        pitch = conf.get( OFFSET_ROT_PITCH_COL + row )
        roll  = conf.get( OFFSET_ROT_ROLL_COL  + row )
        position = App.Vector(x, y, z)
        rotation = App.Rotation(yaw, pitch, roll)
        offset = App.Placement(position, rotation)
        obj.AttachmentOffset = offset


"""
    +-----------------------------------------------+
    |                 Helper Functions              |
    +-----------------------------------------------+
"""
def isAsm4Config(sheet):
    if sheet and sheet.TypeId=='Spreadsheet::Sheet' and sheet.get(HEADER_CELL)==ASM4_CONFIG_TYPE:
        return True
    else:
        return False

def getConfGroup():
    confGroup = App.ActiveDocument.getObject('Configurations')
    if confGroup and confGroup.TypeId == 'App::DocumentObjectGroup':
        return confGroup
    else:
        return None

def getConfig(name, groupName='Configurations'):
    retval = None
    # Get the needed configuration table
    # group = getGroup(groupName)
    group = getConfGroup()
    if group:
        retval = group.getObject(name)
    return retval


def setConfigDescription(conf, description):
    conf.set(DESCRIPTION_CELL, str(description))


def getConfigDescription(conf):
    return str(conf.get(DESCRIPTION_CELL)).strip()


def GetValidAlias(str):
    # Spreadsheed doesn't like many characters in the alias, specifically the '.' that we need to separate sub-sub-links
    # For now we will just remove all those characters in hope that there will be no duplication
    badChars = '`~!@#$%^&*()-+=|\;:\'".,'
    ret = ''
    for char in str:
        if char not in badChars:
            ret = ret + char
    # Should not have '_' at the beginning of the string...
    ret = ret.strip('_')
    return ret


def GetObjectRow(conf, name):
    cell = conf.getCellFromAlias(GetValidAlias(name))
    if cell:
        # leave only numbers in the cell string
        row = ''.join(i for i in cell if i.isdigit())
        return row
    return None


def GetObjectData(conf, name, col):
    row = GetObjectRow(conf, name)
    return conf.get(str(col) + str(row))


class ListEntry(QtGui.QListWidgetItem):
    name = ''
    description = ''
    def __init__(self, name, description=''):
        self.name = name
        self.description = description
        super(ListEntry, self).__init__()


#def getGroup(groupName, create=True):
'''
def getGroup(groupName):
    # Look for the specified group, or ActiveDocument if not specified
    group = None
    if groupName != '':
        group = App.ActiveDocument.getObject(groupName)
    return group
'''


"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
#Gui.addCommand( 'Asm4_saveConfiguration',    saveConfigurationCmd()  )
#Gui.addCommand( 'Asm4_restoreConfiguration', restoreConfigurationCmd() )
Gui.addCommand( 'Asm4_applyConfiguration',   applyConfigurationCmd() )
Gui.addCommand( 'Asm4_openConfigurations',   openConfigurationsCmd() )
Gui.addCommand( 'Asm4_newConfiguration',     newConfigurationCmd()   )

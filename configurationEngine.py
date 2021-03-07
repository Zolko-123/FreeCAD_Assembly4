#!/usr/bin/env python3
# coding: utf-8
#
# configurationEngine.py
#
# The code to save and restore configurations, using spreadsheets

import math
from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import libAsm4 as Asm4

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
    |           Save configuration Button           |
    +-----------------------------------------------+
"""
class saveConfigurationCmd:
    def __init__(self):
        super(saveConfigurationCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Save configuration",
                "ToolTip": "Save configuration of the selected object",
                #"Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_showLCS.svg')
                }

    def IsActive(self):
        # Will handle LCSs only for the Assembly4 model
        #if Asm4.getSelectedLink() or Asm4.getModelSelected():
        if Asm4.getSelectedLink() or Asm4.checkModel():
            return True
        return False

    def Activated(self):
        ui = saveConfigurationUI()
        '''
        # Fill the configurations list
        confGroup = GetGroup('Configurations')
        if confGroup:
            for obj in confGroup.OutList:
                if obj.TypeId == 'Spreadsheet::Sheet':
                    ui.addListEntry(obj.Label, getConfigDescription(obj))
        '''
        Gui.Control.showDialog(ui)


"""
    +-----------------------------------------------+
    |            Save configuration UI              |
    +-----------------------------------------------+
"""
class saveConfigurationUI():
    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base
        #iconFile = os.path.join( Asm4.iconPath , 'Place_Link.svg')
        #self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle('Save configuration')
        # draw the GUI, objects are defined later down
        self.drawUI()
        # Fill the configurations list
        confGroup = GetGroup('Configurations')
        if confGroup:
            for obj in confGroup.OutList:
                if obj.TypeId == 'Spreadsheet::Sheet':
                    self.addListEntry(obj.Label, getConfigDescription(obj))

    # standard FreeCAD Task panel buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)

    # OK
    def accept(self):
        confName = self.configurationName.text().strip()
        confDescr = self.configurationDescription.text().strip()
        if confName == '':
            Asm4.warningBox('Please specify configuration name!')
            self.configurationName.setFocus()
            return
        # if no description provided, set the name as description
        if confDescr == '':
            confDescr = ' '
        
        self.SaveConfiguration( confName, confDescr )
        Gui.Control.closeDialog()


    # Cancel
    def reject(self):
        Gui.Control.closeDialog()


    # Free insert
    def clicked(self, button):
        pass


    def SaveConfiguration(self, confName, description):
        FCC.PrintMessage('Saving configuration to "' + confName + '"\n')
        conf = getConfig(confName, 'Configurations')
        if conf:
            confirm = Asm4.confirmBox('Override configuration in "' + confName + '"?')
            if not confirm:
                FCC.PrintMessage('Cancel save...\n')
                return
            else:
                setConfigDescription(conf, description)
        else:
            conf = self.createConfig(confName, description, 'Configurations')

        model = App.ActiveDocument.getObject('Model')
        link  = Asm4.getSelectedLink()
        if link:
            self.SaveObject(conf, link)
        else:
            self.SaveSubObjects(conf, model)            
        conf.recompute(True)
    

    def SaveSubObjects(self, conf, container):
        for objName in container.getSubObjects():
            obj = container.getSubObject(objName, 1)
            #if obj.TypeId == 'App::Link':
            self.SaveObject(conf, obj)


    def SaveObject(self, conf, obj):
        # parse App::Part containers, and only those
        if obj.TypeId == 'App::Part':
            self.SaveSubObjects(conf, obj)

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


    def createConfig(self, name, description, groupName=''):
        group = GetGroup(groupName)
        if not group:
            # create a group Configurations to store various config tables
            group = App.ActiveDocument.getObject('Model').newObject('App::DocumentObjectGroup','Configurations')
        # Create the document
        conf = group.newObject('Spreadsheet::Sheet', name)
        headerRow = str(int(OBJECTS_START_ROW)-1)
        conf.set(HEADER_CELL,           'Assembly4 configuration table')
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


    def onListChange(self):
        # Get selected entry
        selectedItems = self.configurationList.selectedItems()
        if len(selectedItems) != 1:
            return

        item = selectedItems[0]
        item.__class__ = ListEntry
        self.configurationName.setText(item.name)
        self.configurationDescription.setText(item.description)


    def addListEntry(self, name, description):
        newItem = ListEntry(name, description)
        str = name
        if description != '':
            str = str + ' (' + description + ')'
        newItem.setText(str)
        self.configurationList.addItem(newItem)


    # defines the UI, only static elements
    def drawUI(self):
        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self.form)

        # Configuration name
        self.mainLayout.addWidget(QtGui.QLabel("Name:"))
        self.configurationName = QtGui.QLineEdit()
        self.mainLayout.addWidget(self.configurationName)
        # Configuration description
        self.mainLayout.addWidget(QtGui.QLabel("Description:"))
        self.configurationDescription = QtGui.QLineEdit()
        self.mainLayout.addWidget(self.configurationDescription)
        # List of configurations
        self.mainLayout.addWidget(QtGui.QLabel("Override configuration:"))
        self.configurationList = QtGui.QListWidget()
        self.configurationList.setMinimumHeight(100)
        self.mainLayout.addWidget(self.configurationList)
        # apply the layout to the main window
        self.form.setLayout(self.mainLayout)

        # actions
        self.configurationList.itemSelectionChanged.connect(self.onListChange)



"""
    +-----------------------------------------------+
    |            Restore Configuration              |
    +-----------------------------------------------+
"""
class restoreConfigurationCmd:
    def __init__(self):
        super(restoreConfigurationCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Restore configuration",
                "ToolTip": "Restore configuration of the selected object",
                #"Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_showLCS.svg')
                }

    def IsActive(self):
        # Will handle LCSs only for the Assembly4 model
        if Asm4.checkModel() and GetGroup('Configurations'):
            return True
        return False

    def Activated(self):
        # if a configuration is selected, pre-select it in the list
        if Gui.Selection.getSelection():
            selection = Gui.Selection.getSelection()[0]
            if selection.getParentGroup() and selection.getParentGroup().Name == 'Configurations':
                #FCC.PrintMessage('Restoring configuration '+selection.Name+'\n')
                RestoreConfiguration(selection.Name)
                return
        ui = restoreConfigurationUI()
        '''
        # Fill the configurations list
        confGroup = GetGroup('Configurations')
        if confGroup:
            for obj in confGroup.OutList:
                if obj.TypeId == 'Spreadsheet::Sheet':
                    ui.addListEntry(obj.Label, getConfigDescription(obj))
        '''
        Gui.Control.showDialog(ui)


"""
    +-----------------------------------------------+
    |         Restore configuration Task UI         |
    +-----------------------------------------------+
"""
class restoreConfigurationUI():
    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base
        #iconFile = os.path.join( Asm4.iconPath , 'Place_Link.svg')
        #self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle('Restore configuration')

        # draw the GUI, objects are defined later down
        self.drawUI()
        # Fill the configurations list
        confGroup = GetGroup('Configurations')
        if confGroup:
            for obj in confGroup.OutList:
                if obj.TypeId == 'Spreadsheet::Sheet':
                    self.addListEntry(obj.Label, getConfigDescription(obj))


    # standard FreeCAD Task panel buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)


    # OK
    def accept(self):
        selectedItems = self.configurationList.selectedItems()
        if len(selectedItems) == 0:
            Asm4.warningBox('Please select a configuration in the list')
            return
        config = selectedItems[0]
        RestoreConfiguration(config.name)
        Gui.Control.closeDialog()


    # Cancel
    def reject(self):
        Gui.Control.closeDialog()


    # Free insert
    def clicked(self, button):
        pass

    
    def addListEntry(self, name, description):
        newItem = ListEntry(name)
        str = name
        if description != '':
            str = str + ' (' + description + ')'
        newItem.setText(str)
        self.configurationList.addItem(newItem)


    # defines the UI, only static elements
    def drawUI(self):
        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self.form)

        # List of configurations
        self.mainLayout.addWidget(QtGui.QLabel("Select configuration:"))
        self.configurationList = QtGui.QListWidget()
        self.configurationList.setMinimumHeight(100)
        self.mainLayout.addWidget(self.configurationList)

        # apply the layout to the main window
        self.form.setLayout(self.mainLayout)




"""
    +-----------------------------------------------+
    |                 Helper Functions              |
    +-----------------------------------------------+
"""
def getConfig(name, groupName=''):
    retval = None
    # Get the needed configuration table
    group = GetGroup(groupName)
    if group:
        retval = group.getObject(name)
    return retval

#def GetGroup(groupName, create=True):
def GetGroup(groupName):
    # Look for the specified group, or ActiveDocument if not specified
    group = None
    if groupName != '':
        group = App.ActiveDocument.getObject(groupName)
    return group


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


def RestoreConfiguration(docName):
    FCC.PrintMessage('Restoring configuration "' + docName + '"\n')
    doc = getConfig(docName, 'Configurations')
    model = Asm4.checkModel()
    link = Asm4.getSelectedLink()
    if link:
        RestoreObject(doc, link)
    else:
        RestoreSubObjects(doc, model)
    App.ActiveDocument.recompute()


def RestoreSubObjects(doc, container):
    for objName in container.getSubObjects():
        obj = container.getSubObject(objName, 1)
        #if obj.TypeId == 'App::Link':
        RestoreObject(doc, obj)


def RestoreObject(doc, obj):
    # parse App::Part containers, and only those
    if obj.TypeId == 'App::Part':
        SaveSubObjects(conf, obj)

    parentObj, objFullName = obj.Parents[0]
    #objName = App.ActiveDocument.Name + '.' + parentObj.Name + '.' + objFullName
    objName = parentObj.Name + '.' + objFullName

    row = GetObjectRow(doc, objName)
    if row is None:
        FCC.PrintMessage('No data for object "' + objName + '" in configuration "' + doc.Name + '"\n')
        return

    vis   = doc.get( OBJECT_VISIBLE_COL   + row )
    obj.ViewObject.Visibility = vis
    asm   = str(doc.get( OBJECT_ASM_TYPE_COL  + row ))
    if asm == 'Asm4EE':
        x     = doc.get( OFFSET_POS_X_COL     + row )
        y     = doc.get( OFFSET_POS_Y_COL     + row )
        z     = doc.get( OFFSET_POS_Z_COL     + row )
        yaw   = doc.get( OFFSET_ROT_YAW_COL   + row )
        pitch = doc.get( OFFSET_ROT_PITCH_COL + row )
        roll  = doc.get( OFFSET_ROT_ROLL_COL  + row )
        position = App.Vector(x, y, z)
        rotation = App.Rotation(yaw, pitch, roll)
        offset = App.Placement(position, rotation)
        obj.AttachmentOffset = offset


"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_saveConfiguration',    saveConfigurationCmd() )
Gui.addCommand( 'Asm4_restoreConfiguration', restoreConfigurationCmd() )


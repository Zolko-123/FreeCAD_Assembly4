#!/usr/bin/env python3
# coding: utf-8
#
# configurationEngine.py
#
# The code to save and restore configurations, using spreadsheets

import FreeCADGui as Gui
import FreeCAD as App
import libAsm4 as Asm4

HEADER_CELL             = 'A1'
NAME_CELL               = 'A2'
OBJECTS_START_ROW       = '5'
OBJECT_NAME_COL         = 'A'
ATTACHMENT_POS_X_COL    = 'B'
ATTACHMENT_POS_Y_COL    = 'C'
ATTACHMENT_POS_Z_COL    = 'D'
ATTACHMENT_AXIS_X_COL   = 'E'
ATTACHMENT_AXIS_Y_COL   = 'F'
ATTACHMENT_AXIS_Z_COL   = 'G'
ATTACHMENT_ANGLE_COL    = 'H'


"""
    +-----------------------------------------------+
    |                  main class                   |
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
        if Asm4.getSelection() or Asm4.getModelSelected():
            return True
        return False

    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        #TODO: Ask for configuration name
        doc = GetDocument('test')

        model = Asm4.getModelSelected()
        if model:
            for objName in model.getSubObjects():
                SaveObject(doc, model.getSubObject(objName, 1))
        else:
            SaveObject(doc, Asm4.getSelection())


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
        if Asm4.getSelection() or Asm4.getModelSelected():
            return True
        return False

    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        #TODO: Ask for configuration name
        doc = GetDocument('test')

        model = Asm4.getModelSelected()
        if model:
            for objName in model.getSubObjects():
                RestoreObject(doc, model.getSubObject(objName, 1))
        else:
            RestoreObject(doc, Asm4.getSelection())


"""
    +-----------------------------------------------+
    |                  storage engine               |
    +-----------------------------------------------+
"""
def GetDocument(name):
    # Get Configurations group where the spreadsheets will be saved
    conf = App.ActiveDocument.getObject('Configurations')
    if conf is None:
        conf = App.ActiveDocument.addObject('App::DocumentObjectGroup', 'Configurations')

    # Get the needed document, create if not exist
    doc = conf.getObject(name)
    if doc is None:
        doc = conf.newObject('Spreadsheet::Sheet', name)
        PrepareDocument(doc, name)

    return doc


def PrepareDocument(doc, name):
    print('Preparing: ' + name)
    doc.clearAll()
    doc.set(HEADER_CELL, 'This is an Assembly4 configuration file. Manual changes or deleletion of that file might break your assembly completely!')
    doc.set(NAME_CELL, name)
    headerRow = str(int(OBJECTS_START_ROW)-1)
    doc.set(OBJECT_NAME_COL + headerRow, 'ObjectName')
    doc.set(ATTACHMENT_POS_X_COL + headerRow, 'Position_X')
    doc.set(ATTACHMENT_POS_Y_COL + headerRow, 'Position_Y')
    doc.set(ATTACHMENT_POS_Z_COL + headerRow, 'Position_Z')
    doc.set(ATTACHMENT_AXIS_X_COL + headerRow, 'Axis_X')
    doc.set(ATTACHMENT_AXIS_Y_COL + headerRow, 'Axis_Y')
    doc.set(ATTACHMENT_AXIS_Z_COL + headerRow, 'Axis_Z')
    doc.set(ATTACHMENT_ANGLE_COL + headerRow, 'Angle')

def GetObjectRow(doc, name):
    cell = doc.getCellFromAlias(name)
    if cell:
        # leave only numbers in the cell string
        row = ''.join(i for i in cell if i.isdigit())
        return row
    return None


def GetObjectData(doc, name, col):
    row = GetObjectRow(doc, name)
    return doc.get(str(col) + str(row))


def SaveObject(doc, obj):
    row = GetObjectRow(doc, obj.Name)
    if row is None:
        doc.insertRows(OBJECTS_START_ROW, 1)
        row = OBJECTS_START_ROW

    linkedObjName = Asm4.getLinkedObjectName(App.ActiveDocument.Name, App.ActiveDocument.Model.Name, obj.Name)
    doc.set(OBJECT_NAME_COL + row, linkedObjName)
    attachment = obj.AttachmentOffset
    doc.set(ATTACHMENT_POS_X_COL + row, str(attachment.Base.x))
    doc.set(ATTACHMENT_POS_Y_COL + row, str(attachment.Base.y))
    doc.set(ATTACHMENT_POS_Z_COL + row, str(attachment.Base.z))
    doc.set(ATTACHMENT_AXIS_X_COL + row, str(attachment.Rotation.Axis.x))
    doc.set(ATTACHMENT_AXIS_Y_COL + row, str(attachment.Rotation.Axis.y))
    doc.set(ATTACHMENT_AXIS_Z_COL + row, str(attachment.Rotation.Axis.z))
    doc.set(ATTACHMENT_ANGLE_COL + row, str(attachment.Rotation.Angle))


def RestoreObject(doc, obj):
    #TODO
    todo = 1




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_saveConfiguration', saveConfigurationCmd() )
Gui.addCommand( 'Asm4_restoreConfiguration', restoreConfigurationCmd() )


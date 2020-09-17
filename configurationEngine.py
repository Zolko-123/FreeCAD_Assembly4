#!/usr/bin/env python3
# coding: utf-8
#
# configurationEngine.py
#
# The code to save and restore configurations, using spreadsheets

import FreeCADGui as Gui
import FreeCAD as App
import libAsm4 as Asm4
import math

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
        doc = GetDocument('test', 'Configurations')

        model = Asm4.getModelSelected()
        if model:
            SaveSubObjects(doc, model)
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
        doc = GetDocument('test', 'Configurations')

        model = Asm4.getModelSelected()
        if model:
            RestoreSubObjects(doc, model)
        else:
            RestoreObject(doc, Asm4.getSelection())


"""
    +-----------------------------------------------+
    |                  storage engine               |
    +-----------------------------------------------+
"""
def GetDocument(name, groupName = ''):
    # Look for the specified group, or ActiveDocument if not specified
    if groupName != '':
        group = App.ActiveDocument.getObject(groupName)
        if group is None:
            group = App.ActiveDocument.addObject('App::DocumentObjectGroup', groupName)
    else:
        group = App.ActiveDocument

    # Get the needed document, create if not exist
    doc = group.getObject(name)
    if doc is None:
        doc = group.newObject('Spreadsheet::Sheet', name)
        PrepareDocument(doc, name)

    return doc


def PrepareDocument(doc, name):
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


def GetObjectRow(doc, name):
    cell = doc.getCellFromAlias(GetValidAlias(name))
    if cell:
        # leave only numbers in the cell string
        row = ''.join(i for i in cell if i.isdigit())
        return row
    return None


def GetObjectData(doc, name, col):
    row = GetObjectRow(doc, name)
    return doc.get(str(col) + str(row))


def SaveSubObjects(doc, container, namePrefix=''):
    print("Container: " + container.Name)
    print("Prefix: " + namePrefix)
    for objName in container.getSubObjects():
        obj = container.getSubObject(objName, 1)
        if obj.TypeId == 'App::Link':
            SaveObject(doc, obj, namePrefix)


def SaveObject(doc, obj, namePrefix=''):
    linkedObjName = namePrefix + obj.Name + '.';

    SaveSubObjects(doc, obj, linkedObjName)
    print("Saving " + linkedObjName + " to " + doc.Name)
    row = GetObjectRow(doc, linkedObjName)
    if row is None:
        doc.insertRows(OBJECTS_START_ROW, 1)
        row = OBJECTS_START_ROW

    doc.set(OBJECT_NAME_COL + row, linkedObjName)
    doc.setAlias(OBJECT_NAME_COL + row, GetValidAlias(linkedObjName))
    attachment = obj.AttachmentOffset
    doc.set(ATTACHMENT_POS_X_COL + row, str(attachment.Base.x))
    doc.set(ATTACHMENT_POS_Y_COL + row, str(attachment.Base.y))
    doc.set(ATTACHMENT_POS_Z_COL + row, str(attachment.Base.z))
    doc.set(ATTACHMENT_AXIS_X_COL + row, str(attachment.Rotation.Axis.x))
    doc.set(ATTACHMENT_AXIS_Y_COL + row, str(attachment.Rotation.Axis.y))
    doc.set(ATTACHMENT_AXIS_Z_COL + row, str(attachment.Rotation.Axis.z))
    doc.set(ATTACHMENT_ANGLE_COL + row, str(math.degrees(attachment.Rotation.Angle)))
    doc.recompute(True)


def RestoreSubObjects(doc, container, namePrefix=''):
    for objName in container.getSubObjects():
        obj = container.getSubObject(objName, 1)
        if obj.TypeId == 'App::Link':
            RestoreObject(doc, obj, namePrefix)


def RestoreObject(doc, obj, namePrefix=''):
    linkedObjName = namePrefix + obj.Name + '.';

    RestoreSubObjects(doc, obj, namePrefix + obj.Name + '.')

    print("Restoring " + linkedObjName + " from " + doc.Name)
    row = GetObjectRow(doc, linkedObjName)
    if row is None:
        print('No data for object "' + linkedObjName + '." in configuration "' + doc.Name + '"')
        return

    x = doc.get(ATTACHMENT_POS_X_COL + row)
    y = doc.get(ATTACHMENT_POS_Y_COL + row)
    z = doc.get(ATTACHMENT_POS_Z_COL + row)
    v1 = App.Vector(x, y, z)
    print(v1)
    x = doc.get(ATTACHMENT_AXIS_X_COL + row)
    y = doc.get(ATTACHMENT_AXIS_Y_COL + row)
    z = doc.get(ATTACHMENT_AXIS_Z_COL + row)
    angle = doc.get(ATTACHMENT_ANGLE_COL + row)
    v2 = App.Vector(x, y, z)
    rotation = App.Rotation(v2, angle)
    print(rotation)
    placement = App.Placement(v1, rotation)
    print(placement)
    obj.AttachmentOffset = placement
    obj.recompute()


"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_saveConfiguration', saveConfigurationCmd() )
Gui.addCommand( 'Asm4_restoreConfiguration', restoreConfigurationCmd() )


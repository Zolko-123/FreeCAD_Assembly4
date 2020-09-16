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
    headerRow = str(OBJECTS_START_ROW-1)
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
        doc.insertRow(OBJECTS_START_ROW, 1)
        row = OBJECTS_START_ROW

    doc.set(OBJECT_NAME_COL + row, obj.Name)
    attachment = obj.AttachmentOffset
    doc.set(ATTACHMENT_POS_X_COL + row, attachment.Base.x)
    doc.set(ATTACHMENT_POS_Y_COL + row, attachment.Base.y)
    doc.set(ATTACHMENT_POS_Z_COL + row, attachment.Base.z)
    doc.set(ATTACHMENT_AXIS_X_COL + row, attachment.Rotation.Axis.x)
    doc.set(ATTACHMENT_AXIS_Y_COL + row, attachment.Rotation.Axis.y)
    doc.set(ATTACHMENT_AXIS_Z_COL + row, attachment.Rotation.Axis.z)
    doc.set(ATTACHMENT_ANGLE_COL + row, attachment.Rotation.Angle)



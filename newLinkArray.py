#!/usr/bin/env python3
# coding: utf-8
#
# newLinkArray.py

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Draft

from libAsm4 import *


class newLinkArray():
    """Creating a link array from Draft Workbench"""

    def GetResources(self):
        return {"MenuText": "New Link Array",
                "ToolTip": "Create a new orthogonal or polar array from links",
                "Pixmap": os.path.join(iconPath, 'Asm4_LinkArray.svg')
                }

    def IsActive(self):
        if App.ActiveDocument:
            # Only active when a App::Link is selected
            selectObj = self.checkPart()
            if selectObj:
                return (True)
        else:
            return (False)

    def Activated(self):
        # get the current active document
        partChecked = self.checkPart()
        if partChecked:
            selectObject = self.checkPart()
            if selectObject:
                # Now is time to create the array
                arrayName = 'array'
                text, ok = QtGui.QInputDialog.getText(None, 'Create new Link Array', 'Enter new Link Array name: ',
                                                      text=arrayName)
                if ok and text:
                    Draft.makeArray(App.ActiveDocument.getObject(selectObject.Name), App.Vector(1, 0, 0),
                                    App.Vector(0, 1, 0), 2, 2, useLink=True)

    def checkPart(self):
        # if something is selected
        if Gui.Selection.getSelection():
            selectedObj = Gui.Selection.getSelection()[0]
            # Only create arrays of links
            if selectedObj.TypeId == 'App::Link':
                return selectedObj
            else:
                return False


# add the command to the workbench
Gui.addCommand('Asm4_newLinkArray', newLinkArray())

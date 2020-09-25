#!/usr/bin/env python3
# coding: utf-8
#
# treeSelectionOverride.py
#
# The code tracks the selections made

import os
from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import libAsm4 as Asm4

"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class treeSelectionOverrideCmd( QtGui.QDialog):
    def __init__(self):
        super(treeSelectionOverrideCmd,self).__init__()


    def GetResources(self):
        return {"MenuText": "Enable/Disable 3D View selection mode",
                "ToolTip": "Enable/Disable 3D View selection mode\n\n"    + \
                "Allows to select a Link object in the 3D view\n" + \
                "window instead of the Model tree",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_enableLinkSelection.svg')
                }


    def IsActive(self):
        return True


    def Activated(self):
        global observer
        # This function is executed when the command is activated
        if observer is None:
            self.Enable()
        else:
            self.Disable()


    def Enable(self):
        global observer
        observer = Asm4.selObserver3DView();
        # add the listener, 0 forces to resolve the links
        Gui.Selection.addObserver(observer, 0)
        #print("3D view link selection mode is now enabled")
        FCC.PrintMessage("3D view link selection mode is now enabled\n")


    def Disable(self):
        global observer
        Gui.Selection.removeObserver(observer) 
        observer = None
        #print("3D view link selection mode is now disabled")
        FCC.PrintMessage("3D view link selection mode is now disabled\n")
    



"""
    +-----------------------------------------------+
    |               observer class                  |
    +-----------------------------------------------+

class asm4SelObserver:
    def addSelection(self,doc,obj,sub,pnt):               # Selection object
        # Since both 3D view clicks and manual tree selection gets into the same callback
        # we will determine by clicked coordinates, for manual tree selections the coordinates are (0,0,0)
        if pnt != (0,0,0):
            # 3D view click
            # Get linked object name that handles sub-sub-assembly
            subObjName = Asm4.getLinkedObjectName(doc, obj, sub)
            if subObjName != '':
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(doc, obj, subObjName)
"""

observer = None

def Deactivate():
    global observer
    Gui.Selection.removeObserver(observer) 
    observer = None
    #print("3D view link selection mode is now disabled")
    FCC.PrintMessage("3D view link selection mode is now disabled\n")



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_treeSelectionOverrideCmd', treeSelectionOverrideCmd() )



#!/usr/bin/env python3
# coding: utf-8
#
# showHideLcsCmd.py

import math, re, os

import FreeCADGui as Gui
import FreeCAD as App

import libAsm4 as Asm4



"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class showLcsCmd:
    def __init__(self):
        super(showLcsCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Show LCS",
                "ToolTip": "Show LCS of selected part and its children",
#                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_CoordinateSystem.svg')
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
        model = Asm4.getModelSelected()
        if model:
            for objName in model.getSubObjects():
                ShowChildLCSs(model.getSubObject(objName, 1), True)
        else:
            ShowChildLCSs(Asm4.getSelection(), True)


class hideLcsCmd:
    def __init__(self):
        super(hideLcsCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Hide LCS",
                "ToolTip": "Hide LCS of selected part and its children",
#                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_CoordinateSystem.svg')
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
        model = Asm4.getModelSelected()
        if model:
            for objName in model.getSubObjects():
                ShowChildLCSs(model.getSubObject(objName, 1), False)
        else:
            ShowChildLCSs(Asm4.getSelection(), False)



# Show/Hide the LCSs in the provided object and all linked children
def ShowChildLCSs(obj, show):
    lcsTypes = ["PartDesign::CoordinateSystem", "PartDesign::Line", "PartDesign::Point", "PartDesign::Plane"]

    if obj.TypeId == 'App::Link':
        for linkObj in obj.LinkedObject.Document.Objects:
            ShowChildLCSs(linkObj, show)
    else:
        for subObjName in obj.getSubObjects():
            subObj = obj.getSubObject(subObjName, 1)    # 1 for returning the real object
            if subObj != None:
                if subObj.TypeId in lcsTypes:
                    subObj.Visibility = show

"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_showLcs', showLcsCmd() )
Gui.addCommand( 'Asm4_hideLcs', hideLcsCmd() )


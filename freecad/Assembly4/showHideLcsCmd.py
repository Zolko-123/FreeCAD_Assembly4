#!/usr/bin/env python3
# coding: utf-8
#
# showHideLcsCmd.py

import os

import FreeCADGui as Gui
import FreeCAD as App

from . import Asm4_libs as Asm4
from .Asm4_Translate import translate




"""
    +-----------------------------------------------+
    |                    Show                       |
    +-----------------------------------------------+
"""
class showLcsCmd:

    def __init__(self):
        super(showLcsCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": translate("Asm4_showLcs", "Show LCS"),
                "ToolTip": translate("Asm4_showLcs", "Show LCS and Datums of selected part and its children"),
                "Pixmap": os.path.join(Asm4.iconPath, 'Asm4_showLCS.svg')
                }

    def IsActive(self):
        # if something is selected or an Asm4 assembly present
        if Gui.Selection.hasSelection() or Asm4.getAssembly():
            return True
        return False

    def Activated(self):
        # show
        showHide(True)



"""
    +-----------------------------------------------+
    |                      Hide                     |
    +-----------------------------------------------+
"""
class hideLcsCmd:
    def __init__(self):
        super(hideLcsCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": translate("Asm4_hideLcs", "Hide LCS"),
                "ToolTip": translate("Asm4_hideLcs", "Hide LCS and Datums of selected part and its children"),
                "Pixmap": os.path.join(Asm4.iconPath, 'Asm4_hideLCS.svg')
                }

    def IsActive(self):
        # if something is selected or an Asm4 assembly present
        if Gui.Selection.hasSelection() or Asm4.getAssembly():
            return True
        return False

    def Activated(self):
        # hide
        showHide(False)


"""
    +-----------------------------------------------+
    |              Show/Hide the LCSs in            |
    |   the provided object and all its children    |
    +-----------------------------------------------+
"""
def showHide( show ):
    # reset processed links cache
    processedLinks = []
    # if something is selected
    if Gui.Selection.hasSelection():
        for sel in Gui.Selection.getSelection():
            if sel.isDerivedFrom('App::Link'):
                showChildLCSs(sel, show, processedLinks)
            elif sel.TypeId in Asm4.containerTypes:
                for objName in sel.getSubObjects(1):
                    showChildLCSs(sel.getSubObject(objName, 1), show, processedLinks)
    # if not, apply it to the assembly
    elif Asm4.getAssembly():
        asm = Asm4.getAssembly()
        for objName in asm.getSubObjects(1):
            showChildLCSs(asm.getSubObject(objName, 1), show, processedLinks)

def showChildLCSs(obj, show, processedLinks):
    #global processedLinks
    # if its a datum apply the visibility
    if obj.TypeId in Asm4.datumTypes:
        obj.Visibility = show
    # if it's a link, look for subObjects
    elif obj.TypeId == 'App::Link' and obj.Name not in processedLinks:
        processedLinks.append(obj.Name)
        for objName in obj.LinkedObject.getSubObjects(1):
            linkedObj = obj.LinkedObject.Document.getObject(objName[0:-1])
            showChildLCSs(linkedObj, show, processedLinks)
    # if it's a container or a group
    elif obj.TypeId in Asm4.containerTypes or obj.TypeId=='App::DocumentObjectGroup':
        for subObjName in obj.getSubObjects(1):
            subObj = obj.getSubObject(subObjName, 1)    # 1 for returning the real object
            if subObj != None:
                showChildLCSs(subObj, show, processedLinks)




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_showLcs', showLcsCmd() )
Gui.addCommand( 'Asm4_hideLcs', hideLcsCmd() )


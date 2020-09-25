#!/usr/bin/env python3
# coding: utf-8
#
# showHideLcsCmd.py

import math, re, os

import FreeCADGui as Gui
import FreeCAD as App

import libAsm4 as Asm4


# Already processed links cache, no need to process the same part if its linked multiple times
processedLinks = []


"""
    +-----------------------------------------------+
    |                    Show                       |
    +-----------------------------------------------+
"""
class showLcsCmd:
    def __init__(self):
        super(showLcsCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Show LCS",
                "ToolTip": "Show LCS of selected part and its children",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_showLCS.svg')
                }

    def IsActive(self):
        # Will handle LCSs only for the Assembly4 model
        if Asm4.getSelection() or Asm4.getModelSelected():
        # treats all container types : Body and Part
        #if Asm4.getSelectedContainer() or Asm4.checkModel() or Asm4.getSelectedLink():
            return True
        return False

    def Activated(self):
        global processedLinks
        # reset processed links cache
        processedLinks = []

        model = Asm4.getModelSelected()
        if model:
            for objName in model.getSubObjects():
                ShowChildLCSs(model.getSubObject(objName, 1), True)
        else:
            ShowChildLCSs(Asm4.getSelection(), True)


"""
    +-----------------------------------------------+
    |                      Hide                     |
    +-----------------------------------------------+
"""
class hideLcsCmd:
    def __init__(self):
        super(hideLcsCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Hide LCS",
                "ToolTip": "Hide LCS of selected part and its children",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_hideLCS.svg')
                }

    def IsActive(self):
        # Will handle LCSs only for the Assembly4 model
        if Asm4.getSelection() or Asm4.getModelSelected():
            return True
        return False

    def Activated(self):
        global processedLinks
        # reset processed links cache
        processedLinks = []

        model = Asm4.getModelSelected()
        if model:
            for objName in model.getSubObjects():
                ShowChildLCSs(model.getSubObject(objName, 1), False)
        else:
            ShowChildLCSs(Asm4.getSelection(), False)



"""
    +-----------------------------------------------+
    |              Show/Hide the LCSs in            |
    |  the provided object and all linked children  |
    +-----------------------------------------------+
"""
def ShowChildLCSs(obj, show):
    global processedLinks

    # if its a datum apply the visibility
    if obj.TypeId in Asm4.datumTypes:
        obj.Visibility = show
    # if it's a link, look for subObjects
    elif obj.TypeId == 'App::Link' and obj.Name not in processedLinks:
        processedLinks.append(obj.Name)
        for objName in obj.LinkedObject.getSubObjects():
            linkObj = obj.LinkedObject.Document.getObject(objName[0:-1])
            ShowChildLCSs(linkObj, show)
    # if it's a container
    else:
        if obj.TypeId in Asm4.containerTypes:
            for subObjName in obj.getSubObjects():
                subObj = obj.getSubObject(subObjName, 1)    # 1 for returning the real object
                if subObj != None:
                    if subObj.TypeId in Asm4.datumTypes:
                        subObj.Visibility = show



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_showLcs', showLcsCmd() )
Gui.addCommand( 'Asm4_hideLcs', hideLcsCmd() )


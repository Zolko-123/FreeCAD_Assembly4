#!/usr/bin/env python3
# coding: utf-8
#
# showHideLcsCmd.py

import math, re, os

import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4
from Asm4_Translate import QT_TRANSLATE_NOOP as Qtranslate




"""
    +-----------------------------------------------+
    |                    Show                       |
    +-----------------------------------------------+
"""
class showLcsCmd:

    def __init__(self):
        super(showLcsCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": Qtranslate("Asm4_showLcs", "Show LCS"),
                "ToolTip": Qtranslate("Asm4_showLcs", "Show LCS and Datums of selected part and its children"),
                "Pixmap": os.path.join(Asm4.iconPath, 'Asm4_showLCS.svg')
                }

    def IsActive(self):
        # treats all container types : Body and Part
        if Asm4.getSelectedContainer() or Asm4.getAssembly() or Asm4.getSelectedLink():
            return True
        return False

    def Activated(self):
        #global processedLinks
        # reset processed links cache
        processedLinks = []

        #model = Asm4.getModelSelected()
        container = Asm4.getSelectedContainer()
        if not container:
            container = Asm4.getAssembly()
        link = Asm4.getSelectedLink()
        if link:
            showChildLCSs(link, True, processedLinks)
        elif container:
            for objName in container.getSubObjects(1):
                showChildLCSs(container.getSubObject(objName, 1), True, processedLinks)


"""
    +-----------------------------------------------+
    |                      Hide                     |
    +-----------------------------------------------+
"""
class hideLcsCmd:
    def __init__(self):
        super(hideLcsCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": Qtranslate("Asm4_hideLcs", "Hide LCS"),
                "ToolTip": Qtranslate("Asm4_hideLcs", "Hide LCS and Datums of selected part and its children"),
                "Pixmap": os.path.join(Asm4.iconPath, 'Asm4_hideLCS.svg')
                }

    def IsActive(self):
        # Will handle LCSs only for the Assembly4 model
        if Asm4.getSelectedContainer() or Asm4.getAssembly() or Asm4.getSelectedLink():
            return True
        return False

    def Activated(self):
        #global processedLinks
        # reset processed links cache
        processedLinks = []

        container = Asm4.getSelectedContainer()
        if not container:
            container = Asm4.getAssembly()
        link = Asm4.getSelectedLink()
        if link:
            showChildLCSs(link, False, processedLinks)
        elif container:
            for objName in container.getSubObjects(1):
                showChildLCSs(container.getSubObject(objName, 1), False, processedLinks)



"""
    +-----------------------------------------------+
    |              Show/Hide the LCSs in            |
    |   the provided object and all its children    |
    +-----------------------------------------------+
"""
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
    # if it's a container
    else:
        if obj.TypeId in Asm4.containerTypes:
            for subObjName in obj.getSubObjects(1):
                subObj = obj.getSubObject(subObjName, 1)    # 1 for returning the real object
                if subObj != None:
                    if subObj.TypeId in Asm4.datumTypes:
                        #subObj.Visibility = show
                        # Apparently obj.Visibility API is very slow
                        # Using the ViewObject.show() and ViewObject.hide() API runs at least twice faster
                        if show:
                            subObj.ViewObject.show()
                        else:
                            subObj.ViewObject.hide()




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_showLcs', showLcsCmd() )
Gui.addCommand( 'Asm4_hideLcs', hideLcsCmd() )


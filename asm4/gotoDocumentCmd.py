#!/usr/bin/env python3
# coding: utf-8
#
# gotoDocumentCmd.py

import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import Asm4_libs as Asm4
from Asm4_Translate import QT_TRANSLATE_NOOP as Qtranslate



"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class gotoDocumentCmd:

    def __init__(self):
        super(gotoDocumentCmd,self).__init__()
        self.selectedLink = []


    def GetResources(self):
        return {"MenuText": Qtranslate("Asm4_gotoDocument", "Open Document"),
                "ToolTip": Qtranslate("Asm4_gotoDocument", "Activates the document of the selected linked part"),
                "Pixmap": os.path.join(Asm4.iconPath, 'Asm4_openDocument.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if App.ActiveDocument and self.checkSelection() is not None:
            return True
        else:
            return False 


    def checkSelection(self):
        selectedLink = None
        # check that 1 object is selected
        if len(Gui.Selection.getSelection())==1:
            selObj = Gui.Selection.getSelection()[0]
            # check that the selected object is a link ...
            if  selObj.TypeId=='App::Link':
                # ... to something in a Document ...
                if hasattr(selObj.LinkedObject,'Document'):
                    # ... that is not the current Document
                    if selObj.LinkedObject.Document != App.ActiveDocument:
                        selectedLink = selObj
        # now we should be safe
        return selectedLink
    

    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # check what we have selected
        selectedLink = self.checkSelection()
        if not selectedLink:
            return
        linkedObj = selectedLink.LinkedObject

        # in case linking to a sub-object
        if isinstance(linkedObj, tuple):
            linkedObj = linkedObj[0].getSubObject(linkedObj[1], retType=1)
        
        # the non-magical command
        App.setActiveDocument(linkedObj.Document.Name)
        Gui.activateView('Gui::View3DInventor', True)



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_gotoDocument', gotoDocumentCmd() )

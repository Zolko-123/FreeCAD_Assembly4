#!/usr/bin/env python3
# coding: utf-8
#
# gotoDocumentCmd.py

import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

from Asm4_translate import QT_TRANSLATE_NOOP

import libAsm4 as Asm4



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
        return {"MenuText": QT_TRANSLATE_NOOP("Asm4_gotoDocument", "Open Document"),
                "ToolTip": QT_TRANSLATE_NOOP("Asm4_gotoDocument", "Activates the document of the selected linked part"),
                "Pixmap": os.path.join(Asm4.iconPath, 'Asm4_openDocument.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if App.ActiveDocument:
            # is something selected ?
            selObj = self.checkSelection()
            if selObj != None:
                return True
        return False 


    def checkSelection(self):
        selectedLink = None
        # check that there is an App::Part called 'Model'
        # a standard App::Part would also do, but then more error checks are necessary
        if App.ActiveDocument.getObject('Model') and App.ActiveDocument.getObject('Model').TypeId=='App::Part' :
        # check that something is selected
            if Gui.Selection.getSelection():
            # set the (first) selected object as global variable
                selection = Gui.Selection.getSelection()[0]
                selectedType = selection.TypeId
                # check that the selected object is a Datum CS or Point type
                if  selectedType=='App::Link':
                    selectedLink = selection
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
        elif not selectedLink.TypeId=='App::Link':
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

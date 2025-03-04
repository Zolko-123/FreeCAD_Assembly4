#!/usr/bin/env python3
# coding: utf-8
#
# releaseAttachmentCmd.py
#
# LGPL
# Copyright HUBERT Zoltán


import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part
from Asm4_Translate import _atr, QT_TRANSLATE_NOOP, translate

from . import Asm4_libs as Asm4



"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class releaseAttachment:

    def __init__(self):
        super(releaseAttachment,self).__init__()
        self.selectedObj = []


    def GetResources(self):
        return {"MenuText": translate("Asm4_releaseAttachment", "Release from Attachment"),
                "ToolTip": translate("Asm4_releaseAttachment", "Release an object from all attachments to any geometry"),
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_releaseAttachment.svg')
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
        selectedObj = None
        # check that there is an Assembly
        if Asm4.getAssembly() and len(Gui.Selection.getSelection())==1:
            # set the (first) selected object as global variable
            selection = Gui.Selection.getSelection()[0]
            if Asm4.isAsm4EE(selection) and selection.SolverId != '':
                selectedObj = selection
        # now we should be safe
        return selectedObj
    

    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):

        # check what we have selected
        selectedObj = self.checkSelection()
        if not selectedObj:
            return
        objName  = selectedObj.Name
        objLabel = selectedObj.Label
        objType  = selectedObj.TypeId

        # ask for confirmation before resetting everything
        confirmText = translate("Asm4_releaseAttachment", 'This command will release all attachments on ')+Asm4.labelName(selectedObj) + translate("Asm4_releaseAttachment", ' and set it to manual positioning in its current location.')
        if not Asm4.confirmBox(confirmText):
            # don't do anything
            return

        # the root Assembly
        model = Asm4.getAssembly()

        # handle object types differently
        # an App::Link
        if objType == 'App::Link':
            # unset the ExpressionEngine for the Placement
            selectedObj.setExpression('Placement', None)
            # reset Asm4 properties
            Asm4.makeAsmProperties( selectedObj, reset=True )
        # a datum object
        else:
            # reset Asm4 properties
            Asm4.makeAsmProperties( selectedObj, reset=True )
            # unset both Placements (who knows what confusion the user has done)
            selectedObj.setExpression( 'Placement', None )
            selectedObj.setExpression( 'AttachmentOffset', None )
            # if it's a datum object
            if objType=='PartDesign::CoordinateSystem' or objType=='PartDesign::Plane' or objType=='PartDesign::Line' or objType=='PartDesign::Point' :
                # unset the MapMode; this actually keeps the MapMode parameters intact, 
                # so it's easy for the user to re-enable it
                selectedObj.MapMode = 'Deactivated'

        # recompute the assembly model
        model.recompute(True)



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_releaseAttachment', releaseAttachment() )

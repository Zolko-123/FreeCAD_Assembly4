#!/usr/bin/env python3
# coding: utf-8
#
# releaseAttachmentCmd.py

import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import libAsm4 as Asm4



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
        return {"MenuText": "Release from Attachment",
                "ToolTip": "Release an object from all attachments to any geometry",
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
        # check that there is an App::Part called 'Model'
        # a standard App::Part would also do, but then more error checks are necessary
        if App.ActiveDocument.getObject('Model') and App.ActiveDocument.getObject('Model').TypeId=='App::Part' :
        # check that something is selected
            if Gui.Selection.getSelection():
            # set the (first) selected object as global variable
                selection = Gui.Selection.getSelection()[0]
                selectedType = selection.TypeId
                # check that the selected object is a Datum CS or Point type
                if  selectedType=='App::Link' or selectedType=='PartDesign::CoordinateSystem' or selectedType=='PartDesign::Plane' or selectedType=='PartDesign::Line' or selectedType=='PartDesign::Point' :
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
        if objName==objLabel:
            objText = objLabel
        else:
            objText = objLabel+' ('+objName+')'
        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle('FreeCAD Warning')
        msgBox.setIcon(QtGui.QMessageBox.Warning)
        msgBox.setText('This command will release all attachments on '+objText+' and set it to manual positioning in its current location.')
        msgBox.setInformativeText('Are you sure you want to proceed ?')
        msgBox.setStandardButtons(QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ok)
        msgBox.setEscapeButton(QtGui.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
        retval = msgBox.exec_()
        # Cancel = 4194304
        # Ok = 1024
        if retval == 4194304:
            # don't do anything
            return

        # the root Assembly4 Model
        model = App.ActiveDocument.getObject('Model')

        # handle oject types differently
        # an App::Link
        if objType == 'App::Link':
            # unset the ExpressionEngine for the Placement
            selectedObj.setExpression('Placement', None)
            # property AssemblyType
            if hasattr(selectedObj,'AssemblyType'):
                selectedObj.AssemblyType = ''
            else:
                selectedObj.addProperty( 'App::PropertyString', 'AssemblyType', 'Attachment' ).AssemblyType = ''
            # property AttachedBy
            if hasattr(selectedObj,'AttachedBy'):
                selectedObj.AttachedBy = ''
            else:
                selectedObj.addProperty( 'App::PropertyString', 'AttachedBy', 'Attachment' ).AttachedBy = ''
            # property AttachedTo
            if hasattr(selectedObj,'AttachedTo'):
                selectedObj.AttachedTo = ''
            else:
                selectedObj.addProperty( 'App::PropertyString', 'AttachedTo', 'Attachment' ).AttachedTo = ''
            # property AttachmentOffset
            if hasattr(selectedObj,'AttachmentOffset'):
                selectedObj.AttachmentOffset = App.Placement()
            else:
                selectedObj.addProperty( 'App::PropertyPlacement', 'AttachmentOffset', 'Attachment' ).AttachedTo = App.Placement()
        # a datum object
        elif objType=='PartDesign::CoordinateSystem' or objType=='PartDesign::Plane' or objType=='PartDesign::Line' or objType=='PartDesign::Point' :
            # unset the MapMode; this actually keeps the MapMode parameters intact, 
            # so it's easy for the user to re-enable it
            selectedObj.MapMode = 'Deactivated'
            # unset both Placements (who knows what confusion the user has done)
            selectedObj.setExpression( 'Placement', None )
            selectedObj.setExpression( 'AttachmentOffset', None )

        # recompute the assembly model
        App.ActiveDocument.getObject('Model').recompute(True)



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_releaseAttachment', releaseAttachment() )

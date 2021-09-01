#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# importDatumCmd.py 


import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4




"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class importDatumCmd():
    def __init__(self):
        super(importDatumCmd,self).__init__()

    def GetResources(self):
        tooltip  = "Imports the selected Datum object from a sub-part into the root assembly.\n"
        tooltip += "This creates a new datum of the same type, and with the same global placement\n\n"
        tooltip += "This command can also be used to override the placement of an existing datum :\n"
        tooltip += "select a second datum in the same root container as the first selected datum"
        iconFile = os.path.join( Asm4.iconPath , 'Import_Datum.svg')
        return {"MenuText": "Import Datum object",
                "ToolTip" : tooltip,
                "Pixmap"  : iconFile }

    def IsActive(self):
        if App.ActiveDocument and self.getSelectedDatums():
            return True
        else:
            return False

    def getSelectedDatums(self):
        retval = None
        selection = Gui.Selection.getSelection()
        if len(selection)==1:
            selObj = Gui.Selection.getSelection()[0]
            if selObj.TypeId in Asm4.datumTypes:
                retval = selection
        elif len(selection)==2:
            selObj1 = Gui.Selection.getSelection()[0]
            selObj2 = Gui.Selection.getSelection()[1]
            if selObj1.TypeId in Asm4.datumTypes and selObj2.TypeId in Asm4.datumTypes:
                retval = selection
        return retval

    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        ( selDatum, selTree ) = Asm4.getSelectionTree()
        # the selected datum is not deep enough
        if not selTree or len(selTree)<3:
            message = selDatum.Name + ' is already at the top-level and cannot be imported'
            Asm4.warningBox(message)
            return
        # the root parent container is the first in the selection tree
        rootContainer = App.ActiveDocument.getObject(selTree[0])
        
        # build the Placement expression
        # the first [0] object is at the document root and its Placement is ignored
        # the second [1] object gets a special treatment, it is always in the current document
        expression = selTree[1]+'.Placement'
        obj1 = App.ActiveDocument.getObject(selTree[1])
        # the document where an object is
        if obj1.isDerivedFrom('App::Link') and obj1.LinkedObject.Document != App.ActiveDocument:
            doc = obj1.LinkedObject.Document
        else:
            doc = App.ActiveDocument
        # parse the tree
        for objName in selTree[2:]:
            #FCC.PrintMessage('treating '+objName+'\n')
            obj = doc.getObject(objName)
            # the *previous* object was a link to doc
            if doc == App.ActiveDocument:
                expression += ' * '+objName+'.Placement'
            else:
                expression += ' * '+doc.Name+'#'+objName+'.Placement'
            # check whether *this* object is a link to an *external* doc
            if obj.isDerivedFrom('App::Link') and obj.LinkedObject.Document != App.ActiveDocument:
                doc = obj.LinkedObject.Document
            # else, keep the same document
            else:
                pass
        #FCC.PrintMessage('expression = '+expression+'\n')
        
        confirm = False
        selection = self.getSelectedDatums()
        # if a single datum object is selected
        if len(selection)==1:
            # create a new datum object
            proposedName = selTree[-2]+'_'+selDatum.Label
            message = 'Create a new '+selDatum.TypeId+' in '+Asm4.labelName(rootContainer)+' \nsuperimposed on:\n\n'
            for objName in selTree[1:]:
                message += '> '+objName+'\n'
            message += '\nEnter name for this datum :'+' '*40
            text,ok = QtGui.QInputDialog.getText(None,'Import Datum',
                    message, text = proposedName)
            if ok and text:
                targetDatum = rootContainer.newObject( selDatum.TypeId, text )
                targetDatum.Label = text
                # apply existing view properties if applicable
                if hasattr(selDatum,'ResizeMode') and selDatum.ResizeMode == 'Manual':
                    targetDatum.ResizeMode = 'Manual'
                    if hasattr(selDatum,'Length'):
                        targetDatum.Length = selDatum.Length
                    if hasattr(selDatum,'Width'):
                        targetDatum.Width = selDatum.Width
                targetDatum.ViewObject.ShapeColor   = selDatum.ViewObject.ShapeColor
                targetDatum.ViewObject.Transparency = selDatum.ViewObject.Transparency
                # signal for later down that everything went fine
                confirm = True
        # two datum objects are selected
        # the second is superimposed on the first
        # Can be of different types, doesn't matter
        elif len(selection)==2:
            targetDatum = selection[1]
            # we can only import a datum to another datum at the root of the same container
            if targetDatum.getParentGeoFeatureGroup() != rootContainer:
                message = Asm4.labelName(targetDatum)+'is not in the root container '+Asm4.labelName(rootContainer)
                Asm4.messageBox(message)
                return
            # target datum is free
            if targetDatum.MapMode == 'Deactivated':
                message = 'This will superimpose '+Asm4.labelName(targetDatum)+' in '+Asm4.labelName(rootContainer)+' on:\n\n'
                for objName in selTree[1:-1]:
                    message += '> '+objName+'\n'
                message += '> '+Asm4.labelName(selDatum)
                Asm4.messageBox(message)
                confirm = True
            # target datum is attached
            else:
                message = Asm4.labelName(targetDatum)+' in '+Asm4.labelName(rootContainer)+' is already attached to some geometry. '
                message += 'This will superimpose its Placement on:\n\n'
                for objName in selTree[1:-1]:
                    message += '> '+objName+'\n'
                message += '> '+Asm4.labelName(selDatum)
                confirm = Asm4.confirmBox(message)
        # if everything went according to plan
        if confirm:
            # unset Attachment
            targetDatum.MapMode = 'Deactivated'
            targetDatum.Support = None
            # Set Asm4 properties
            Asm4.makeAsmProperties( targetDatum, reset=True )
            targetDatum.AttachedBy = 'Origin'
            targetDatum.SolverId   = 'Placement::ExpressionEngine'
            # set the Placement's ExpressionEngine
            targetDatum.setExpression( 'Placement', expression )
            # hide initial datum
            selDatum.Visibility    = False
            targetDatum.Visibility = True
            # select the newly created datum
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( App.ActiveDocument.Name, rootContainer.Name, targetDatum.Name+'.' )
            # recompute the object to apply the placement:
            targetDatum.recompute()
            # recompute assembly
            rootContainer.recompute(True)

       




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_importDatum', importDatumCmd() )

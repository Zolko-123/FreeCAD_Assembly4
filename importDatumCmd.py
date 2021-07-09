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
        tooltip += "This command can also be used to override the placement of an existing datum"
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
        # the first object gets a special treatment
        # it is always in the current document
        expression = selTree[1]+'.Placement'
        obj1 = App.ActiveDocument.getObject(selTree[1])
        # the document where an object is
        if obj1.isDerivedFrom('App::Link') and obj1.LinkedObject.Document != App.ActiveDocument:
            doc = obj1.LinkedObject.Document
        else:
            doc = App.ActiveDocument
        # parse the tree
        for objName in selTree[2:]:
            FCC.PrintMessage('treating '+objName+'\n')
            obj = doc.getObject(objName)
            # the *previous* object was a link to 
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
        selection = Gui.Selection.getSelection()
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
                createdDatum = rootContainer.newObject( selDatum.TypeId, text )
                createdDatum.Label = text
                targetDatum = createdDatum
                confirm = True
        # two datum objects are selected
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
                Asm4.warningBox(message)
                confirm = True
            # target datum is attached
            else:
                message = Asm4.labelName(targetDatum)+' in '+Asm4.labelName(rootContainer)+' is already attached to some geometry. '
                message += 'This will superimpose its Placement on:\n\n'
                for objName in selTree[1:-1]:
                    message += '> '+objName+'\n'
                message += '> '+Asm4.labelName(selDatum)
                confirm = Asm4.confirmBox(message)

        if confirm:
            # unset Attachment
            targetDatum.Support = None
            targetDatum.MapMode = 'Deactivated'
            # set the Placement's ExpressionEngine
            targetDatum.setExpression( 'Placement', expression )
            # hide initial datum
            selDatum.Visibility=False
            # select the newly created datum
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( App.ActiveDocument.Name, rootContainer.Name, targetDatum.Name+'.' )
            # recompute the object to apply the placement:
            targetDatum.recompute()
            # recompute assembly
            rootContainer.recompute(True)

       


"""
    +-----------------------------------------------+
    |    The UI and functions in the Task panel     |
    +-----------------------------------------------+

class importDatumUI():
    def __init__(self):
        ( link, datum ) = Asm4.getLinkAndDatum()
        if link :
            self.targetDatum = datum
            self.targetLink  = link
            
            self.base = QtGui.QWidget()
            self.form = self.base        
            self.form.setWindowIcon(QtGui.QIcon( iconFile ))
            self.form.setWindowTitle('Import a Datum object into the Assembly')

            # get the current active document to avoid errors if user changes tab
            self.activeDoc = App.ActiveDocument
            self.parentAssembly = self.activeDoc.Model

            # make and initialize UI
            self.drawUI()
            self.initUI()
        else:
            Asm4.warningBox( 'The selected datum object cannot be imported into this assembly' )


    # this is the end ...
    def finish(self):
        Gui.Control.closeDialog()

    # standard FreeCAD Task panel buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel
                   | QtGui.QDialogButtonBox.Ok)

    # OK
    def accept(self):
        self.onApply()
        self.finish()

    # Cancel
    def reject(self):
        self.finish()


    def onApply(self):
        # get the name of the part where the datum to be copied is:
        #linkedPartName = self.childrenList.currentText()

        linkName   = self.targetLink.Name
        linkedPart = self.targetLink.LinkedObject.Name
        linkedDoc  = self.targetLink.LinkedObject.Document.Name
        datum = self.targetDatum

        # the name of the datum in the assembly, as per the dialog box
        setDatumName = self.datumName.text()
        
        # check that all of them have something in
        if not (linkName and linkedPart and datum and setDatumName):
            self.datumName.setText( 'Problem in selections' )
        else:
            # create the Datum
            createdDatum = App.activeDocument().getObject('Model').newObject( datum.TypeId, setDatumName )
            self.datumName.setText( '=> ' +createdDatum.Name )
            # build the expression for the ExpressionEngine
            # if the linked part is in the same docmument as the assembly
            if self.activeDoc == self.targetLink.LinkedObject.Document:
                expr = linkName +'.Placement * '+ datum.Name +'.Placement * AttachmentOffset'
            # if the linked part is in another document
            else:
                # it's the App.Document, not the App::Part that must be set before the #
                # expr = linkName +'.Placement * '+ linkedPart +'#'+ datum.Name +'.Placement'
                expr = linkName +'.Placement * '+ linkedDoc +'#'+ datum.Name +'.Placement * AttachmentOffset'
            # load the built expression into the Expression field of the datum created in the assembly
            self.activeDoc.getObject( createdDatum.Name ).setExpression( 'Placement', expr )
            # recompute the object to apply the placement:
            createdDatum.recompute()
        # recompute assembly
        self.parentAssembly.recompute(True)
        return


    def initUI(self):
        docName = self.targetLink.LinkedObject.Document.Name+'#'
        self.datumOrig.setText( Asm4.nameLabel(self.targetDatum) )
        self.datumType.setText( self.targetDatum.TypeId )
        self.linkName.setText(  Asm4.nameLabel(self.targetLink) )
        self.partName.setText(  docName + Asm4.nameLabel(self.targetLink.LinkedObject))
        self.datumName.setText( self.targetDatum.Label )


    
    # defines the UI, only static elements
    def drawUI(self):
        # Our main layoyt will be vertical
        self.mainLayout = QtGui.QVBoxLayout(self.form)

        # Define the fields for the form ( label + widget )
        self.formLayout = QtGui.QFormLayout()
        # Datum Type
        self.datumType = QtGui.QLineEdit()
        self.datumType.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Datum Type'),self.datumType)
        # Datum Object
        self.datumOrig = QtGui.QLineEdit()
        self.datumOrig.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Orig. Datum'),self.datumOrig)
        # Link instance
        self.linkName = QtGui.QLineEdit()
        self.linkName.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Orig. Instance'),self.linkName)
        # Orig Part
        self.partName = QtGui.QLineEdit()
        self.partName.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Orig. Doc#Part'),self.partName)
        # apply the layout
        self.mainLayout.addLayout(self.formLayout)
        
        # empty line
        self.mainLayout.addWidget(QtGui.QLabel())
        # the name as seen in the tree of the selected link
        self.datumName = QtGui.QLineEdit()
        self.mainLayout.addWidget(QtGui.QLabel("Enter the imported Datum's name :"))
        self.mainLayout.addWidget(self.datumName)

        # set main window widgets
        self.form.setLayout(self.mainLayout)
"""




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_importDatum', importDatumCmd() )

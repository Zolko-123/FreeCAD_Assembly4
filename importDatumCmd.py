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

import libAsm4 as Asm4




"""
    +-----------------------------------------------+
    |               Helper functions                |
    +-----------------------------------------------+
"""
def getSelection():
    # check that there is an App::Part called 'Model'
    if Asm4.checkModel is None:
        return None
    # if something is selected ...
    if len(Gui.Selection.getSelection())==1:
        selectedObj = Gui.Selection.getSelection()[0]
        # if it's a datum object we return it
        if selectedObj.TypeId in datumTypes:
            return selectedObj            
    return None


# Types of objects to import
datumTypes = [  'PartDesign::CoordinateSystem', \
                'PartDesign::Plane',            \
                'PartDesign::Line',             \
                'PartDesign::Point']


# icon to show in the Menu, toolbar and widget window
iconFile = os.path.join( Asm4.iconPath , 'Import_Datum.svg')


    
"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class importDatumCmd():
    def __init__(self):
        super(importDatumCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Import Datum object",
                "ToolTip": "Imports the selected Datum object from a linked Part into the assembly.\nOnly datum objects at the root of the linked part can be imported",
                "Pixmap" : iconFile
                }

    def IsActive(self):
        if App.ActiveDocument and getSelection():
            return True
        return False

    def Activated(self):
        Gui.Control.showDialog( importDatumUI() )
        # Before calling the UI, we make some checks:
        # We get all the App::Link parts in the assembly 
        '''
        parentAssembly = App.ActiveDocument.Model
        childrenTable = []
        for objStr in parentAssembly.getSubObjects():
            # the string ends with a . that must be removed
            obj = App.ActiveDocument.getObject( objStr[0:-1] )
            if obj.TypeId == 'App::Link' and hasattr(obj.LinkedObject,'isDerivedFrom'):
                if  obj.LinkedObject.isDerivedFrom('App::Part') or obj.LinkedObject.isDerivedFrom('PartDesign::Body'):
                    # add it to our tree table if it's a link to an App::Part ...
                    childrenTable.append( obj )

        targetDatum = getSelection()
        # this returns the selection hierarchy in the form 'linkName.datumName.'
        selectionTree = Gui.Selection.getSelectionEx("", 0)[0].SubElementNames[0]
        (targetLinkName, sel, dot) = selectionTree.partition('.'+targetDatum.Name)
        targetLink = App.ActiveDocument.getObject( targetLinkName )
        # If the selected datum is at the root of the link. Else we don't consider it
        if dot =='.' and targetLink in childrenTable:
            Gui.Control.showDialog( importDatumUI() )
        else:
            # see whether the datum is in a group, some people like to do that
            (targetLinkName, dot, groupName) = targetLink.partition('.')
            targetLink = App.ActiveDocument.getObject( targetLinkName )
            group = App.ActiveDocument.getObject( groupName )
            if targetLink in childrenTable and group.TypeId=='App::DocumentObjectGroup':
                Gui.Control.showDialog( importDatumUI() )
            else:
                # something fishy, abort
                FCC.PrintWarning('The selected datum object cannot be imported into this assembly\n')
                return
        '''


"""
    +-----------------------------------------------+
    |    The UI and functions in the Task panel     |
    +-----------------------------------------------+
"""
class importDatumUI():
    def __init__(self):
        ( link, datum ) = Asm4.getLinkAndDatum()
        if not link is None:
            self.targetDatum = datum
            self.targetLink  = link
            
            self.base = QtGui.QWidget()
            self.form = self.base        
            self.form.setWindowIcon(QtGui.QIcon( iconFile ))
            self.form.setWindowTitle('Import a Datum object into the Assembly')

            # get the current active document to avoid errors if user changes tab
            self.activeDoc = App.ActiveDocument
            self.parentAssembly = self.activeDoc.Model

            '''
            # this has been checked before calling
            self.targetDatum = getSelection()
            selectionTree = Gui.Selection.getSelectionEx("", 0)[0].SubElementNames[0]
            (targetLinkName, sel, dot) = selectionTree.partition('.'+self.targetDatum.Name)
            self.targetLink = self.activeDoc.getObject( targetLinkName )
            '''

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



    """
    +-----------------------------------------------+
    | check that all necessary things are selected, |
    |   populate the expression with the selected   |
    |    elements, put them into the constraint     |
    |   and trigger the recomputation of the part   |
    +-----------------------------------------------+
    """
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
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_importDatum', importDatumCmd() )

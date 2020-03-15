#!/usr/bin/env python3
# coding: utf-8
# 
# placeDatumCmd.py 


import os

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
class importDatum( QtGui.QDialog ):

    def __init__(self):
        super(importDatum,self).__init__()
        self.drawUI()
        self.datumTypes = ['PartDesign::CoordinateSystem',
                           'PartDesign::Plane',
                           'PartDesign::Line',
                           'PartDesign::Point']


    def GetResources(self):
        return {"MenuText": "Import Datum object",
                "ToolTip": "Imports the selected Datum object from a linked Part into the assembly.\nOnly datum objects at the root of the linked part can be imported",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Import_Datum.svg')
                }
    

    def IsActive(self):
        if App.ActiveDocument:
            if self.getSelection():
                return True
        return False


    def getSelection(self):
        # check that there is an App::Part called 'Model'
        if not App.ActiveDocument.getObject('Model'):
            return None
        # if something is selected ...
        if len(Gui.Selection.getSelection())==1:
            selectedObj = Gui.Selection.getSelection()[0]
            # if it's a datum object we return it
            if selectedObj.TypeId in self.datumTypes:
                return selectedObj
        return None
    
    

    """  
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        
        # get the current active document to avoid errors if user changes tab
        self.activeDoc = App.ActiveDocument
        self.parentAssembly = self.activeDoc.Model

        # initialize 
        self.initUI()
        self.datumTable = [ ]
        self.selectedChild = None
        self.childrenTable = []
 
        # We get all the App::Link parts in the assembly 
        # find all the child linked parts in the assembly
        for objStr in self.parentAssembly.getSubObjects():
            # the string ends with a . that must be removed
            obj = self.activeDoc.getObject( objStr[0:-1] )
            if obj.TypeId == 'App::Link' and obj.LinkedObject.isDerivedFrom('App::Part'):
                # add it to our tree table if it's a link to an App::Part ...
                self.childrenTable.append( obj )

        # check whether a Datum is already selected:
        self.targetDatum = self.getSelection()
        # this returns the selection hierarchy in the form 'linkName.datumName.'
        selectionTree = Gui.Selection.getSelectionEx("", 0)[0].SubElementNames[0]
        (targetLinkName, sel, dot) = selectionTree.partition('.'+self.targetDatum.Name)
        self.targetLink = self.activeDoc.getObject( targetLinkName )
        # If the selected datum is at the root of the link. Else we don't consider it
        if dot =='.' and self.targetLink in self.childrenTable:
            self.datumType.setText( self.targetDatum.TypeId )
            docName = self.targetLink.LinkedObject.Document.Name+'#'
            #self.datumOrig.setText( self.labelName(self.targetDatum) )
            #self.linkName.setText(  self.labelName(self.targetLink) )
            #self.partName.setText(  docName + self.labelName(self.targetLink.LinkedObject))
            self.datumOrig.setText( Asm4.nameLabel(self.targetDatum) )
            self.linkName.setText(  Asm4.nameLabel(self.targetLink) )
            self.partName.setText(  docName + Asm4.nameLabel(self.targetLink.LinkedObject))
            self.datumName.setText( self.targetDatum.Label )
        else:
            # something fishy, abort
            msgBox = QtGui.QMessageBox()
            msgBox.setWindowTitle('FreeCAD Warning')
            msgBox.setIcon(QtGui.QMessageBox.Warning)
            msgBox.setText("The selected datum object cannot be imported into this assembly")
            msgBox.exec_()
            # Cancel = 4194304
            # Ok = 1024
            return

        # Now we can show the UI
        self.show()




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


    """
    +-----------------------------------------------+
    |                     Cancel                    |
    +-----------------------------------------------+
    """
    def onCancel(self):
        self.close()


    """
    +-----------------------------------------------+
    |                      OK                       |
    |               accept and close                |
    +-----------------------------------------------+
    """
    def onOK(self):
        self.onApply()
        self.close()


    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def initUI(self):
        self.datumOrig.clear()
        self.datumType.clear()
        self.linkName.clear()
        self.partName.clear()
        self.datumName.clear()
    
    
    
    def drawUI(self):
        # Our main window will be a QDialog
        self.setWindowTitle('Import a Datum object')
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumWidth(470)
        self.setModal(False)
        self.mainLayout = QtGui.QVBoxLayout(self)

        # Define the fields for the form ( label + widget )
        self.formLayout = QtGui.QFormLayout(self)
        # Datum Type
        self.datumType = QtGui.QLineEdit(self)
        self.datumType.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Datum Type'),self.datumType)
        # Datum Object
        self.datumOrig = QtGui.QLineEdit(self)
        self.datumOrig.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Orig. Datum'),self.datumOrig)
        # Link instance
        self.linkName = QtGui.QLineEdit(self)
        self.linkName.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Orig. Instance'),self.linkName)
        # Orig Part
        self.partName = QtGui.QLineEdit(self)
        self.partName.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Orig. Doc#Part'),self.partName)
        # apply the layout
        self.mainLayout.addLayout(self.formLayout)
        
        # empty line
        self.mainLayout.addWidget(QtGui.QLabel(' '))
        # the name as seen in the tree of the selected link
        self.datumName = QtGui.QLineEdit(self)
        self.mainLayout.addWidget(QtGui.QLabel("Enter the imported Datum's name :"))
        self.mainLayout.addWidget(self.datumName)

        # Cancel button
        self.CancelButton = QtGui.QPushButton('Cancel', self)
        # Import button
        self.ImportButton = QtGui.QPushButton('Import', self)
        self.ImportButton.setDefault(True)
        # the button row definition
        self.buttonLayout = QtGui.QHBoxLayout(self)
        self.buttonLayout.addWidget(self.CancelButton)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.ImportButton)
        self.mainLayout.addStretch()
        self.mainLayout.addLayout(self.buttonLayout)

        # set main window widgets
        self.setLayout(self.mainLayout)

        # Actions
        self.CancelButton.clicked.connect(self.onCancel)
        self.ImportButton.clicked.connect(self.onOK)



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_importDatum', importDatum() )

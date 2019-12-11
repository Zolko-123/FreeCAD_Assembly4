#!/usr/bin/env python3
# coding: utf-8
# 
# placeDatumCmd.py 


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, math, re

from libAsm4 import *



"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class importDatum( QtGui.QDialog ):

    def __init__(self):
        super(importDatum,self).__init__()
        self.datumTypes = ['PartDesign::CoordinateSystem',
                           'PartDesign::Plane',
                           'PartDesign::Line',
                           'PartDesign::Point']


    def GetResources(self):
        return {"MenuText": "Import Datum object",
                "ToolTip": "Imports the selected Datum object from a linked Part into the assembly.\nOnly datum objects at the root of the linked part can be imported",
                "Pixmap" : os.path.join( iconPath , 'Import_Datum.svg')
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
    
    
    def labelName( self, obj ):
        if obj.Name==obj.Label:
            return(obj.Label)
        else:
            return(obj.Label+' ('+obj.Name+')')


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
        self.datumTable = [ ]
        self.selectedChild = None

        # Now we can draw the UI
        self.drawUI()

        # We get all the App::Link parts in the assembly 
        self.childrenTable = []
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
            self.datumList.setText( self.labelName(self.targetDatum) )
            self.datumType.setText( self.targetDatum.TypeId )
            self.linkName.setText(  self.labelName(self.targetLink) )
            docName = self.targetLink.LinkedObject.Document.Name+'#'
            self.partName.setText(  docName + self.labelName(self.targetLink.LinkedObject))
            self.datumName.setText(  self.targetDatum.Label )
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
                expr = linkName +'.Placement * '+ datum.Name +'.Placement'
            # if the linked part is in another document
            else:
                # it's the App.Document, not the App::Part that must be set before the #
                # expr = linkName +'.Placement * '+ linkedPart +'#'+ datum.Name +'.Placement'
                expr = linkName +'.Placement * '+ linkedDoc +'#'+ datum.Name +'.Placement'
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
    def drawUI(self):
        # Our main window will be a QDialog
        self.setWindowTitle('Import a Datum object')
        self.setWindowIcon( QtGui.QIcon( os.path.join( iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumSize(450, 470)
        self.resize(450,470)
        self.setModal(False)
        # make this dialog stay above the others, always visible
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

        # Datum Object
        self.labelRight = QtGui.QLabel(self)
        self.labelRight.setText("Datum object to import :")
        self.labelRight.move(10,20)
        self.datumList = QtGui.QLineEdit(self)
        self.datumList.setReadOnly(True)
        self.datumList.move(40,50)
        self.datumList.setMinimumSize(400, 1)

        # Datum Type
        self.labelType = QtGui.QLabel(self)
        self.labelType.setText("Datum type :")
        self.labelType.move(10,100)
        self.datumType = QtGui.QLineEdit(self)
        self.datumType.setReadOnly(True)
        self.datumType.move(40,130)
        self.datumType.setMinimumSize(400, 1)

        # Link instance
        self.linkLabel = QtGui.QLabel(self)
        self.linkLabel.setText("Link instance's name:")
        self.linkLabel.move(10,180)
        self.linkName = QtGui.QLineEdit(self)
        self.linkName.setReadOnly(True)
        self.linkName.setMinimumSize(400, 1)
        self.linkName.move(40,210)

        # Orig Part
        self.partLabel = QtGui.QLabel(self)
        self.partLabel.setText("Linked Part's origin:")
        self.partLabel.move(10,260)
        self.partName = QtGui.QLineEdit(self)
        self.partName.setReadOnly(True)
        self.partName.move(40,290)
        self.partName.setMinimumSize(400, 1)
        
        # imported Link name
        self.datumLabel = QtGui.QLabel(self)
        self.datumLabel.setText("Enter the new Datum objects's name:")
        self.datumLabel.move(10,350)
        # the name as seen in the tree of the selected link
        self.datumName = QtGui.QLineEdit(self)
        self.datumName.setMinimumSize(430, 1)
        self.datumName.move(10,380)

        # Buttons
        #
        # Cancel button
        self.CancelButton = QtGui.QPushButton('Cancel', self)
        self.CancelButton.setAutoDefault(False)
        self.CancelButton.move(10, 430)
        # Import button
        self.ImportButton = QtGui.QPushButton('Import', self)
        self.ImportButton.setAutoDefault(False)
        self.ImportButton.move(360, 430)
        self.ImportButton.setDefault(True)
        # OK button
        #self.OKButton = QtGui.QPushButton('OK', self)
        #self.OKButton.setAutoDefault(False)
        #self.OKButton.move(310, 450)
        #self.OKButton.setDefault(True)

        # Actions
        self.CancelButton.clicked.connect(self.onCancel)
        self.ImportButton.clicked.connect(self.onOK)
        #self.OKButton.clicked.connect(self.onOK)
        #self.childrenList.currentIndexChanged.connect( self.onParentList )
        #self.datumList.itemClicked.connect( self.onDatumClicked )



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_importDatum', importDatum() )

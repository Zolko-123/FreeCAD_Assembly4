#!/usr/bin/env python3
# coding: utf-8
# 
# insertLinkCmd.py




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
class insertLink( QtGui.QDialog ):
    "My tool object"

    def __init__(self):
        super(insertLink,self).__init__()
        # the GUI objects are defined later down
        self.drawUI()


    def GetResources(self):
        return {"MenuText": "Link an external Part",
                "Accel": "Ctrl+L",
                "ToolTip": "Insert a link to external Part from another open document",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Link_Part.svg')
                }


    def IsActive(self):
            # We only insert a link into an Asm4  Model
        if App.ActiveDocument and self.getSelection():
            return True
        return False


    def getSelection(self):
        selectedObj = None
        # check that there is an App::Part called 'Model'
        if App.ActiveDocument.getObject('Model'):
            selectedObj = App.ActiveDocument.getObject('Model')
        else:
            return None
        # if an App::Link is selected, return that (we'll duplicate it)
        if Gui.Selection.getSelection():
            selObj = Gui.Selection.getSelection()[0]
            # it's an App::Link
            if selObj.isDerivedFrom('App::Link'):
                selectedObj = selObj
        return selectedObj



    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # This function is executed when the command is activated

        # initialise stuff
        self.partList.clear()
        self.linkNameInput.clear()
        self.allParts = []
        self.partsDoc = []
        
        # get the current active document to avoid errors if user changes tab
        self.activeDoc = App.ActiveDocument

        # get the 'Model' object of the current document
        # it has been checked that it exists before
        # this is where the App::Link will be placed, even if there are other plain App::Parts
        self.asmModel = self.activeDoc.getObject('Model')
        
        # if an App::Link is selected, we'll ducplicate it
        selObj = self.getSelection()
        if selObj.isDerivedFrom('App::Link'):
            self.origLink = selObj
        else:
            self.origLink = None
        
        # Search for all App::Parts in all open documents
        # Also store the document of the part
        for doc in App.listDocuments().values():
            # there might be more than 1 App::Part per document
            for obj in doc.findObjects("App::Part"):
                # we don't want to link to itself to the 'Model' object
                # other App::Part in the same document are OK 
                # (even though I don't see the use-case)
                if obj != self.asmModel:
                    self.allParts.append( obj )
                    self.partsDoc.append( doc )

        # build the list
        for part in self.allParts:
            newItem = QtGui.QListWidgetItem()
            if part.Name == part.Label:
                partText = part.Name 
            else:
                partText = part.Label + ' (' +part.Name+ ')' 
            newItem.setText( part.Document.Name +"#"+ partText )
            newItem.setIcon(part.ViewObject.Icon)
            self.partList.addItem(newItem)

        # if an existing App::Link was selected
        if self.origLink:
            origPart = self.origLink.LinkedObject
            # try to find the original part of the selected link
            # MatchExactly, MatchContains, MatchEndsWith, MatchStartsWith ...
            origPartText = origPart.Document.Name +"#"+ origPart.Label
            partFound = self.partList.findItems( origPartText, QtCore.Qt.MatchStartsWith )
            if partFound:
                self.partList.setCurrentItem(partFound[0])
                # set the proposed name to a duplicate of the original link name
                origName = self.origLink.Label
                # if the last character is a number, we increment this number
                lastChar = origName[-1]
                if lastChar.isnumeric():
                    origInstanceNum = int(lastChar)
                    proposedLinkName = origName[:-1]+str(origInstanceNum+1)
                # else we append a _2 to the original name (Label)
                else:
                    proposedLinkName = origName+'_2'
                self.linkNameInput.setText( proposedLinkName )


        # show the UI
        self.show()



    """
    +-----------------------------------------------+
    |         the real stuff happens here           |
    +-----------------------------------------------+
    """
    def onCreateLink(self):
        # parse the selected items 
        # TODO : there should only be 1
        selectedPart = []
        for selected in self.partList.selectedIndexes():
            # get the selected part
            selectedPart = self.allParts[ selected.row() ]

        # get the name of the link (as it should appear in the tree)
        linkName = self.linkNameInput.text()
        # only create link if there is a Part object and a name
        if self.asmModel and selectedPart and linkName:
            # create the App::Link with the user-provided name
            createdLink = self.activeDoc.getObject('Model').newObject( 'App::Link', linkName )
            # assigne the user-selected selectedPart to it
            createdLink.LinkedObject = selectedPart
            # update the link
            createdLink.recompute()
            
            # close the dialog UI...
            self.close()

            # ... and launch the placement of the inserted part
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.activeDoc.Name, 'Model', createdLink.Name+'.' )
            Gui.runCommand( 'Asm4_placeLink' )

        # if still open, close the dialog UI
        self.close()



    def onItemClicked( self, item ):
        for selected in self.partList.selectedIndexes():
            # get the selected part
            part = self.allParts[ selected.row() ]
            doc  = self.partsDoc[ selected.row() ]

            # if the App::Part has been renamed by the user, we suppose it's important
            # thus we append the Label to the link's name
            # this might happen if there are multiple App::Parts in a document
            if doc == self.activeDoc:
                proposedLinkName = part.Label
            else:
                if part.Name == 'Model':
                    proposedLinkName = part.Document.Name
                else:
                    proposedLinkName = part.Document.Name+'_'+part.Label
            self.linkNameInput.setText( proposedLinkName )




    """
    +-----------------------------------------------+
    |                 some functions                |
    +-----------------------------------------------+
    """


    def onCancel(self):
        self.close()



    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):

        # Our main window is a QDialog
        # make this dialog stay above the others, always visible
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.setModal(False)
        self.setWindowTitle('Insert a Part')
        self.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumSize(400, 500)
        self.resize(400,500)

        # Define the individual widgets
        # The part list is a QListWidget
        self.partList = QtGui.QListWidget(self)
        # Create a line that will contain the name of the link (in the tree)
        self.linkNameInput = QtGui.QLineEdit(self)
        # Cancel button
        self.cancelButton = QtGui.QPushButton('Cancel', self)
        # Insert Link button
        self.insertButton = QtGui.QPushButton('Insert', self)
        self.insertButton.setDefault(True)

        # Place the widgets with layouts
        self.mainLayout = QtGui.QVBoxLayout(self)
        self.mainLayout.addWidget(QtGui.QLabel("Select Part to be inserted :"))
        self.mainLayout.addWidget(self.partList)
        self.mainLayout.addWidget(QtGui.QLabel("Enter a Name for the link :\n(Must be unique in the Model tree)"))
        self.mainLayout.addWidget(self.linkNameInput)
        self.mainLayout.addWidget(QtGui.QLabel(' '))
        self.buttonsLayout = QtGui.QHBoxLayout(self)
        self.buttonsLayout.addWidget(self.cancelButton)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.insertButton)
        self.mainLayout.addLayout(self.buttonsLayout)
        self.setLayout(self.mainLayout)

        # Actions
        self.cancelButton.clicked.connect(self.onCancel)
        self.insertButton.clicked.connect(self.onCreateLink)
        self.partList.itemClicked.connect( self.onItemClicked)


"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_insertLink', insertLink() )


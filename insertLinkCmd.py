#!/usr/bin/env python3
# coding: utf-8
# 
# insertLinkCmd.py



import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
#from FreeCAD import Console as FCC


import libAsm4 as Asm4



"""
    +-----------------------------------------------+
    |               Helper functions                |
    +-----------------------------------------------+
"""
def getSelection():
    selectedObj = None
    # check that there is an App::Part called 'Model'
    if App.ActiveDocument.getObject('Model') and App.ActiveDocument.Model.TypeId == 'App::Part':
        selectedObj = App.ActiveDocument.Model
    else:
        return None
    # if an App::Link is selected, return that (we'll duplicate it)
    if len(Gui.Selection.getSelection())==1:
        selObj = Gui.Selection.getSelection()[0]
        # it's an App::Link
        if selObj.isDerivedFrom('App::Link'):
            selectedObj = selObj
    return selectedObj


# allowed types to link-to
linkTypes = [ 'App::Part', 'PartDesign::Body']

# global success state variable
success = False

"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class insertLinkCmd():
    def __init__(self):
        super(insertLinkCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Insert Part",
                "Accel": "Ctrl+L",
                "ToolTip": "Insert a Part into the Assembly",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Link_Part.svg')
                }

    def IsActive(self):
        # We only insert a link into an Asm4  Model
        if App.ActiveDocument and getSelection():
            return True
        return False

    def Activated(self):
        Gui.Control.showDialog( insertLinkUI() )
        # Gui.runCommand( 'Asm4_placeLink' )



"""
    +-----------------------------------------------+
    |    The UI and functions in the Task panel     |
    +-----------------------------------------------+
"""
class insertLinkUI():

    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base        
        iconFile = os.path.join( Asm4.iconPath , 'Link_Part.svg')
        self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle('Insert a Part into the Assembly')

        # the GUI objects are defined later down
        self.drawUI()
        
        # hey-ho, let's go
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
        selObj = getSelection()
        self.origLink = None
        if selObj.isDerivedFrom('App::Link'):
            selType = selObj.LinkedObject.TypeId
            if selType in linkTypes:
                self.origLink = selObj
        
        # Search for all App::Parts and PartDesign::Body in all open documents
        # Also store the document of the part
        for doc in App.listDocuments().values():
            for linkType in linkTypes:
                for obj in doc.findObjects( linkType ):
                    # we don't want to link to itself to the 'Model' object
                    # other App::Part in the same document are OK 
                    # but only those at top level (not nested inside other containers)
                    if obj != self.asmModel and obj.getParentGeoFeatureGroup()==None:
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
            # if Label!=Name then the string still starts with Label
            partFound = self.partList.findItems( origPartText, QtCore.Qt.MatchStartsWith )
            if partFound:
                self.partList.setCurrentItem(partFound[0])
                # set the proposed name to a duplicate of the original link name
                origName = self.origLink.Label
                # if the last character is a number, we increment this number
                lastChar = origName[-1]
                if lastChar.isnumeric():
                    rootName = origName[:-1]
                    instanceNum = int(lastChar)
                    while App.ActiveDocument.getObject( rootName+str(instanceNum) ):
                        instanceNum += 1
                    proposedLinkName = rootName+str(instanceNum)
                # else we append a _2 to the original name (Label)
                else:
                    proposedLinkName = origName+'_2'
                self.linkNameInput.setText( proposedLinkName )


    # close
    def finish(self):
        Gui.Control.closeDialog()


    # standard panel UI buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)

    # Cancel
    def reject(self):
        self.finish()


    # OK: we insert the selected part
    def accept(self):
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
            # assign the user-selected selectedPart to it
            createdLink.LinkedObject = selectedPart
            # If the name was already chosen, and a UID was generated:
            if createdLink.Name != linkName:
                # we try to set the label to the chosen name
                createdLink.Label = linkName
            # update the link
            createdLink.recompute()
            # ... and launch the placement of the inserted part
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.activeDoc.Name, 'Model', createdLink.Name+'.' )
            # close the dialog UI...
            self.finish()

        # close the dialog UI...
        self.finish()


    # a part in the parts list has been clicked, we propose a name for the link
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


    # Define the iUI, only static elements
    def drawUI(self):
        # The part list is a QListWidget
        self.partList = QtGui.QListWidget(self.form)
        self.partList.setMinimumHeight(300)
        # Create a line that will contain the name of the link (in the tree)
        self.linkNameInput = QtGui.QLineEdit(self.form)

        # Place the widgets with layouts
        self.mainLayout = QtGui.QVBoxLayout(self.form)
        self.mainLayout.addWidget(QtGui.QLabel("Select Part to be inserted :"))
        self.mainLayout.addWidget(self.partList)
        self.mainLayout.addWidget(QtGui.QLabel("Enter a Name for the link :\n(Must be unique in the Model tree)"))
        self.mainLayout.addWidget(self.linkNameInput)
        #self.mainLayout.addLayout(self.buttonsLayout)
        self.form.setLayout(self.mainLayout)

        # Actions
        self.partList.itemClicked.connect( self.onItemClicked)





"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_insertLink', insertLinkCmd() )


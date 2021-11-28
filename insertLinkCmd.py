#!/usr/bin/env python3
# coding: utf-8
# 
# insertLinkCmd.py




import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4



"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class insertLink():
    "My tool object"

    def __init__(self):
        super(insertLink,self).__init__()
        # the GUI objects are defined later down
        # self.UI = QtGui.QDialog()
        # self.drawUI()


    def GetResources(self):
        tooltip  = "Insert a link to a Part. This will create a dynamic link to the part\n"
        tooltip += "The part to be linked must be open in the current session\n"
        tooltip += "This command also enables to repair broken/missing links"
        iconFile = 'Link_Part.svg'
        return {"MenuText" : "Insert Link to a Part", 
                "ToolTip"  : tooltip, 
                "Pixmap"   : os.path.join( Asm4.iconPath , iconFile )
                }


    def IsActive(self):
        # if an App::Link is selected, even a broken one
        if Gui.Selection.getSelection() and Gui.Selection.getSelection()[0].isDerivedFrom('App::Link'):
            return True
        # there is an assembly or a root App::Part is selected
        elif Asm4.getAssembly() or Asm4.getSelectedRootPart():
            return True
        return False


    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # This function is executed when the command is activated
        self.UI = QtGui.QDialog()
        self.drawUI()

        # initialise stuff
        self.activeDoc    = App.ActiveDocument
        self.rootAssembly = None
        self.origLink     = None
        self.brokenLink   = False
        #self.allParts = []
        #self.partsDoc = []
        self.filterPartList.clear()
        #self.partList.clear()
        self.linkNameInput.clear()

        # if an Asm4 Assembly is present, that's where we put the link
        if Asm4.getAssembly():
            self.rootAssembly  = Asm4.getAssembly()
        # an App::Part at the root of the document is selected, we insert the link there
        elif Asm4.getSelectedRootPart():
            self.rootAssembly = Asm4.getSelectedRootPart()
        # if a link is selected, we see if we can duplicate it
        if Asm4.getSelectedLink():
            selObj = Asm4.getSelectedLink()
            parent = selObj.getParentGeoFeatureGroup()
            # if the selected link is in a root App::Part
            if parent is not None and parent.TypeId == 'App::Part' and parent.getParentGeoFeatureGroup() is None:
                self.rootAssembly = parent
                self.origLink = selObj
        # if a broken link is selected
        elif len(Gui.Selection.getSelection())==1 :
            selObj = Gui.Selection.getSelection()[0]
            if selObj.isDerivedFrom('App::Link') and selObj.LinkedObject is None:
                parent = selObj.getParentGeoFeatureGroup()
                # if the selected (broken) link is in a root App::Part
                if parent.TypeId == 'App::Part' and parent.getParentGeoFeatureGroup() is None:
                    self.brokenLink = True
                    self.rootAssembly = parent
                    self.origLink = selObj
                    self.UI.setWindowTitle('Re-link broken link')
                    self.insertButton.setText('Replace')
                    self.linkNameInput.setText(Asm4.labelName(selObj))
                    self.linkNameInput.setEnabled(False)

        if self.rootAssembly is None:
            Asm4.warningBox( 'Please create an Assembly' )
            return

        # build the list of available parts
        self.lookForParts()

        '''
        # Search for all App::Parts and PartDesign::Body in all open documents
        # Also store the document of the part
        for doc in App.listDocuments().values():
            # don't consider temporary documents
            if not doc.Temporary:
                for obj in doc.findObjects("App::Part"):
                    # we don't want to link to itself to the 'Model' object
                    # other App::Part in the same document are OK 
                    # but only those at top level (not nested inside other containers)
                    if obj != self.rootAssembly and obj.getParentGeoFeatureGroup() is None:
                        self.allParts.append( obj )
                        self.partsDoc.append( doc )
                for obj in doc.findObjects("PartDesign::Body"):
                    # but only those at top level (not nested inside other containers)
                    if obj.getParentGeoFeatureGroup() is None:
                        self.allParts.append( obj )
                        self.partsDoc.append( doc )

        # build the list
        for part in self.allParts:
            newItem = QtGui.QListWidgetItem()
            newItem.setText( part.Document.Name +"#"+ Asm4.labelName(part) )
            newItem.setIcon(part.ViewObject.Icon)
            self.partList.addItem(newItem)
        '''

        # if an existing valid App::Link was selected
        if self.origLink and not self.brokenLink:
            origPart = self.origLink.LinkedObject
            # try to find the original part of the selected link
            origPartText = origPart.Document.Name +"#"+ Asm4.labelName(origPart)
            # MatchExactly, MatchContains, MatchEndsWith, MatchStartsWith ...
            partFound = self.partList.findItems( origPartText, QtCore.Qt.MatchExactly )
            if partFound:
                self.partList.setCurrentItem(partFound[0])
                # self.onItemClicked(partFound[0])
                # if the last character is a number, we increment this number
                origName = self.origLink.Label
                lastChar = origName[-1]
                if lastChar.isnumeric():
                    (rootName,sep,num) = origName.rpartition('_')
                    proposedLinkName = Asm4.nextInstance(rootName,startAtOne=True)
                # else we take the next instance
                else:
                    proposedLinkName = Asm4.nextInstance(origName)
                # set the proposed name in the entry field
                self.linkNameInput.setText( proposedLinkName )

        # show the UI
        self.UI.show()

    # Search for all App::Parts and PartDesign::Body in all open documents
    # Also store the document of the part
    def lookForParts( self, doc=None ):
        self.allParts = []
        self.partsDoc = []
        self.partList.clear()
        if doc is None:
            docList = App.listDocuments().values()
        else:
            docList = [doc]
        for doc in docList:
            # don't consider temporary documents
            if not doc.Temporary:
                for obj in doc.findObjects("App::Part"):
                    # we don't want to link to itself to the 'Model' object
                    # other App::Part in the same document are OK 
                    # but only those at top level (not nested inside other containers)
                    if obj != self.rootAssembly and obj.getParentGeoFeatureGroup() is None:
                        self.allParts.append( obj )
                        self.partsDoc.append( doc )
                for obj in doc.findObjects("PartDesign::Body"):
                    # but only those at top level (not nested inside other containers)
                    if obj.getParentGeoFeatureGroup() is None:
                        self.allParts.append( obj )
                        self.partsDoc.append( doc )
        # build the list
        for part in self.allParts:
            newItem = QtGui.QListWidgetItem()
            newItem.setText( part.Document.Name +"#"+ Asm4.labelName(part) )
            newItem.setIcon(part.ViewObject.Icon)
            self.partList.addItem(newItem)


    # from A2+
    def openFile(self):
        filename = None
        importDoc = None
        importDocIsOpen = False
        dialog = QtGui.QFileDialog( QtGui.QApplication.activeWindow(),
                                    "Select FreeCAD document to import part from" )
        # set option "DontUseNativeDialog"=True, as native Filedialog shows
        # misbehavior on Unbuntu 18.04 LTS. It works case sensitively, what is not wanted...
        '''
        if a2plib.getNativeFileManagerUsage():
            dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog, False)
        else:
            dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog, True)
        '''
        dialog.setNameFilter("Supported Formats *.FCStd *.fcstd (*.FCStd *.fcstd);;All files (*.*)")
        if dialog.exec_():
            filename = str(dialog.selectedFiles()[0])
            # look only for filenames, not paths, as there are problems on WIN10 (Address-translation??)
            requestedFile = os.path.split(filename)[1]
            # see whether the file is already open
            for d in App.listDocuments().values():
                recentFile = os.path.split(d.FileName)[1]
                if requestedFile == recentFile:
                    importDoc = d # file is already open...
                    importDocIsOpen = True
                    break
            # if not, open it
            if not importDocIsOpen:
                if filename.lower().endswith('.fcstd'):
                    importDoc = App.openDocument(filename)
                    App.setActiveDocument( self.activeDoc.Name )
                    # update the part list
                    self.lookForParts(importDoc)
        return


    """
    +-----------------------------------------------+
    |         the real stuff happens here           |
    +-----------------------------------------------+
    """
    def onCreateLink(self):
        # parse the selected items 
        selectedPart = []
        for selected in self.partList.selectedIndexes():
            # get the selected part
            selectedPart = self.allParts[ selected.row() ]

        # get the name of the link (as it should appear in the tree)
        linkName = self.linkNameInput.text()
        # repair broken link
        if self.brokenLink and selectedPart:
            self.origLink.LinkedObject = selectedPart
            self.origLink.recompute()
            self.UI.close()
            # ... and launch the placement of the inserted part
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.activeDoc.Name, self.rootAssembly.Name, self.origLink.Name+'.' )
            # ... but only if we're in an Asm4 Model
            if self.rootAssembly == Asm4.getAssembly():
                Gui.runCommand( 'Asm4_placeLink' )
        # only create link if there is a Part object and a name
        elif self.rootAssembly and selectedPart and linkName:
            # check that the current document had been saved
            # or that it's the same document as that of the selected part
            if App.ActiveDocument.FileName!='' or App.ActiveDocument==selectedPart.Document:
                # create the App::Link with the user-provided name
                #createdLink = self.activeDoc.getObject('Model').newObject( 'App::Link', linkName )
                createdLink = self.rootAssembly.newObject( 'App::Link', linkName )
                # assign the user-selected selectedPart to it
                createdLink.LinkedObject = selectedPart
                # If the name was already chosen, and a UID was generated:
                if createdLink.Name != linkName:
                    # we try to set the label to the chosen name
                    createdLink.Label = linkName
                # add the Asm4 properties
                Asm4.makeAsmProperties(createdLink)
                # update the link
                createdLink.recompute()
                # close the dialog UI...
                self.UI.close()
                # ... and launch the placement of the inserted part
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection( self.activeDoc.Name, self.rootAssembly.Name, createdLink.Name+'.' )
                # ... but only if we're in an Asm4 Model
                if self.rootAssembly == Asm4.getAssembly():
                    Gui.runCommand( 'Asm4_placeLink' )
            else:
                Asm4.warningBox('The current document must be saved before inserting an external part')
                return


        # if still open, close the dialog UI
        self.UI.close()


    def onItemClicked( self, item ):
        for selected in self.partList.selectedIndexes():
            # get the selected part
            part = self.allParts[ selected.row() ]
            doc  = self.partsDoc[ selected.row() ]
            # by default, the link shall have the same name as the original part
            proposedLinkName = part.Label
            # if it's a sub-assembly
            if part.Name == 'Model' or part.Name == 'Assembly':
                # if it has been renamed, we take the name given by the user
                if part.Name == part.Label:
                    proposedLinkName = part.Document.Name
            # set the proposed name into the text field, unless it's a broken link
            if not self.brokenLink:
                self.linkNameInput.setText( proposedLinkName )


    def onFilterChange(self):
        filterStr = self.filterPartList.text().strip()

        for x in range(self.partList.count()):
            item = self.partList.item(x)
            # check it items's text match the filter
            if filterStr:
                if filterStr in item.text():
                    item.setHidden(False)
                else:
                    item.setHidden(True)
            else:
                item.setHidden(False)


    def onCancel(self):
        self.UI.close()



    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window is a QDialog
        # make this dialog stay above the others, always visible
        self.UI.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.UI.setModal(False)
        self.UI.setWindowTitle('Insert a Part')
        self.UI.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.UI.setMinimumSize(400, 500)
        self.UI.resize(400,500)

        # Define the individual widgets
        # Create a line for filtering the parts list
        self.filterPartList = QtGui.QLineEdit(self.UI)
        # The part list is a QListWidget
        self.partList = QtGui.QListWidget(self.UI)
        # Create a line that will contain the name of the link (in the tree)
        self.linkNameInput = QtGui.QLineEdit(self.UI)
        # Cancel button
        self.cancelButton = QtGui.QPushButton('Cancel', self.UI)
        # Cancel button
        self.openFileButton = QtGui.QPushButton('Open file', self.UI)
        # Insert Link button
        self.insertButton = QtGui.QPushButton('Insert', self.UI)
        self.insertButton.setDefault(True)

        # Place the widgets with layouts
        self.mainLayout = QtGui.QVBoxLayout(self.UI)
        self.mainLayout.addWidget(QtGui.QLabel("Filter :"))
        self.mainLayout.addWidget(self.filterPartList)
        self.mainLayout.addWidget(QtGui.QLabel("Select Part to be inserted :"))
        self.mainLayout.addWidget(self.partList)
        self.mainLayout.addWidget(QtGui.QLabel("Name for the link :"))
        self.mainLayout.addWidget(self.linkNameInput)
        self.mainLayout.addWidget(QtGui.QLabel(' '))
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.buttonsLayout.addWidget(self.cancelButton)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.openFileButton)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.insertButton)
        self.mainLayout.addLayout(self.buttonsLayout)
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.cancelButton.clicked.connect(self.onCancel)
        self.openFileButton.clicked.connect(self.openFile)
        self.insertButton.clicked.connect(self.onCreateLink)
        self.partList.itemClicked.connect( self.onItemClicked)
        self.filterPartList.textChanged.connect(self.onFilterChange)


"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_insertLink', insertLink() )


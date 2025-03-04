#!/usr/bin/env python3
# coding: utf-8
#
# variantLinkCmd.py
#
# LGPL
# Copyright HUBERT Zoltán


import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

from . import Asm4_libs as Asm4
from .Asm4_objects import VariantLink, ViewProviderVariant




"""
    +-----------------------------------------------+
    |        create a variant link to a part        |
    +-----------------------------------------------+

var = App.ActiveDocument.addObject("Part::FeaturePython", 'varLink', VariantLink(),None,True)

"""
class makeVariantLink():
    def __init__(self):
        super(makeVariantLink,self).__init__()
        #pass

    def GetResources(self):
        tooltip  = "EXPERIMENTAL !!!\n"
        tooltip += "Create a variant link to a part\n"
        tooltip += "Select a part containing a \"Variables\" property container"
        iconFile = 'Variant_Link.svg'
        return {"MenuText" : "Create a variant Part", 
                "ToolTip"  :  tooltip, 
                "Pixmap"   :  os.path.join( Asm4.iconPath, iconFile ) 
                }

    def IsActive(self):
        # we only insert variant links into assemblies and root parts 
        if Asm4.getAssembly() or Asm4.getSelectedRootPart():
            return True
        # if an existing variant link is selected, we duplicate it
        if Asm4.getSelectedVarLink():
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
        self.allParts = []
        self.partsDoc = []
        self.filterPartList.clear()
        self.partList.clear()
        self.linkNameInput.clear()

        # if an Asm4 Assembly is present, that's where we put the variant link
        if Asm4.getAssembly():
            self.rootAssembly  = Asm4.getAssembly()
        # an App::Part at the root of the document is selected, we insert the link there
        elif Asm4.getSelectedRootPart():
            self.rootAssembly = Asm4.getSelectedRootPart()

        # if a variant link is selected, we see if we can duplicate it
        if Asm4.getSelectedVarLink():
            selObj = Asm4.getSelectedVarLink()
            parent = selObj.getParentGeoFeatureGroup()
            # if the selected link is in a root App::Part
            if parent.TypeId == 'App::Part' and parent.getParentGeoFeatureGroup() is None:
                self.rootAssembly = parent
                self.origLink = selObj
                self.origPart = selObj.SourceObject
        '''
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
        '''

        if self.rootAssembly is None:
            Asm4.warningBox( 'Please create an Assembly' )
            return

        # Search for all App::Parts having a "Variables" property container in all open documents
        # Also store the document of the part
        for doc in App.listDocuments().values():
            # don't consider temporary documents
            if not doc.Temporary:
                for obj in doc.findObjects("App::Part"):
                    # we don't want to link to itself to the 'Model' object
                    # other App::Part in the same document are OK 
                    # but only those at top level (not nested inside other containers)
                    if obj != self.rootAssembly and obj.getParentGeoFeatureGroup() is None:
                        # and only those that have a Variables property container
                        variables = obj.getObject('Variables')
                        if hasattr(variables,'Type') and variables.Type=='App::PropertyContainer':
                            self.allParts.append( obj )
                            self.partsDoc.append( doc )

        # build the list
        for part in self.allParts:
            newItem = QtGui.QListWidgetItem()
            newItem.setText( part.Document.Name +"#"+ Asm4.labelName(part) )
            newItem.setIcon(part.ViewObject.Icon)
            self.partList.addItem(newItem)

        # if an existing valid App::Link was selected
        if self.origLink and not self.brokenLink:
            origPart = self.origLink.SourceObject
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
                if not self.brokenLink:
                    self.linkNameInput.setText( proposedLinkName )

        # show the UI
        self.UI.show()



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
            # not yet implemented for variant links
            pass
            '''
            self.origLink.LinkedObject = selectedPart
            self.origLink.recompute()
            self.UI.close()
            # ... and launch the placement of the inserted part
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.activeDoc.Name, self.rootAssembly.Name, self.origLink.Name+'.' )
            # ... but only if we're in an Asm4 Model
            if self.rootAssembly == Asm4.getAssembly():
                Gui.runCommand( 'Asm4_placeLink' )
            '''
        # only create link if there is a Part object and a name
        elif self.rootAssembly and selectedPart and linkName:
            # check that the current document had been saved
            # or that it's the same document as that of the selected part
            if App.ActiveDocument.FileName!='' or App.ActiveDocument==selectedPart.Document:
                # create the variant link with the user-provided name
                # variantLink = self.rootAssembly.newObject( 'App::Link', linkName )
                variantLink = App.ActiveDocument.addObject("Part::FeaturePython", linkName, VariantLink(), None, True )
                self.rootAssembly.addObject(variantLink)
                # assign the user-selected selectedPart to it
                variantLink.SourceObject = selectedPart
                # add the Asm4 properties
                Asm4.makeAsmProperties(variantLink)
                variantLink.Type = 'Asm4::VariantLink'
                # apply the ViewProvider
                ViewProviderVariant(variantLink.ViewObject)
                # update the link to actually make all things inside
                variantLink.recompute()
                # If the name was already chosen, and a UID was generated:
                if variantLink.Name != linkName:
                    # we try to set the label to the chosen name
                    variantLink.Label = linkName
                # update
                variantLink.recompute()
                # close the dialog UI...
                self.UI.close()
                # select/highlight the newly created link
                Gui.Selection.clearSelection()
                doc = self.activeDoc.Name
                asm = self.rootAssembly.Name
                lnk = variantLink.Name+'.'
                # FCC.PrintMessage('*'+doc+'*'+asm+'*'+lnk+'*\n')
                Gui.Selection.addSelection( doc, asm, lnk )
                # launch the placement of the inserted part
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
            proposedLinkName = part.Label+'_var'
            # if it's a sub-assembly
            if part.Name == 'Model' or part.Name == 'Assembly':
                # if it has been renamed, we take the name given by the user
                if part.Name == part.Label:
                    proposedLinkName = part.Document.Name+'_var'
                # if not, we take the document
                else:
                    proposedLinkName = part.Label+'_var'
            # set the proposed name into the text field, unless it's a broken link
            if not self.brokenLink:
                # if the last character is a number, we increment this number
                lastChar = proposedLinkName[-1]
                if lastChar.isnumeric():
                    (rootName,sep,num) = proposedLinkName.rpartition('_')
                    proposedLinkName = Asm4.nextInstance(rootName)
                # if that name is already taken
                if self.activeDoc.getObject(proposedLinkName):
                    proposedLinkName = Asm4.nextInstance(proposedLinkName)
                self.linkNameInput.setText( proposedLinkName )

    # filter to display only parts that match this filter
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
        self.UI.setWindowTitle('Insert a variant of a Part')
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
        self.buttonsLayout.addWidget(self.insertButton)
        self.mainLayout.addLayout(self.buttonsLayout)
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.cancelButton.clicked.connect(self.onCancel)
        self.insertButton.clicked.connect(self.onCreateLink)
        self.partList.itemClicked.connect( self.onItemClicked)
        self.filterPartList.textChanged.connect(self.onFilterChange)











"""
    +-----------------------------------------------+
    |                 test functions                |
    +-----------------------------------------------+
    
see:
    https://forum.freecadweb.org/viewtopic.php?f=10&t=38970&start=50#p343116
    https://forum.freecadweb.org/viewtopic.php?f=22&t=42331

asmDoc = App.ActiveDocument
tmpDoc = App.newDocument('TmpDoc', hidden=True, temp=True)
App.setActiveDocument(asmDoc.Name)
beamCopy = tmpDoc.copyObject( asmDoc.getObject( 'Beam'), 'True' )
asmDoc.getObject('Beam_2').LinkedObject = beamCopy
asmDoc.getObject('Beam_3').LinkedObject = beamCopy
asmDoc.getObject('Beam_4').LinkedObject = beamCopy
copyVars = beamCopy.getObject('Variables')
copyVars.Length=50
copyVars.Size=50
asmDoc.recompute()

from .Asm4_objects import VariantLink
var = App.ActiveDocument.addObject("Part::FeaturePython", 'varLink', VariantLink(),None,True)
tmpDoc = App.newDocument( 'TmpDoc', hidden=True, temp=True )
tmpDoc.addObject('App::Part

"""



# add the command to the workbench
Gui.addCommand('Asm4_variantLink', makeVariantLink())

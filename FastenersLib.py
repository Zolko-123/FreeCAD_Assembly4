#!/usr/bin/env python3
# coding: utf-8
#
# FastenersLib.py




import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part
from FastenerBase import FSBaseObject

import libAsm4 as Asm4




"""
    +-----------------------------------------------+
    |        a class to create all fasteners        |
    |       from the Fasteners WB (ScrewMaker)      |
    +-----------------------------------------------+
    
    import ScrewMaker
    sm = ScrewMaker.Instance()
    screwObj = sm.createFastener('ISO7046', 'M6', '20', 'simple', shapeOnly=False)
"""

class insertFastener:
    "My tool object"
    def __init__(self, fastenerType):
        self.fastenerType = fastenerType
        # Screw:
        if self.fastenerType=='Screw':
            self.menutext = "Insert Screw"
            self.tooltip = "Insert a Screw in the Assembly"
            self.icon = os.path.join( Asm4.iconPath , 'Asm4_Screw.svg')
            self.fastenerName = 'Screw'
        # Nut:
        elif self.fastenerType=='Nut':
            self.menutext = "Insert Nut"
            self.tooltip = "Insert a Nut in the Assembly"
            self.icon = os.path.join( Asm4.iconPath , 'Asm4_Nut.svg')
            self.fastenerName = 'Nut'
        # Washer:
        elif self.fastenerType=='Washer':
            self.menutext = "Insert Washer"
            self.tooltip = "Insert a Washer in the Assembly"
            self.icon = os.path.join( Asm4.iconPath , 'Asm4_Washer.svg')
            self.fastenerName = 'Washer'


    def GetResources(self):
        return {"MenuText": self.menutext,
                "ToolTip": self.tooltip,
                "Pixmap" : self.icon }


    def IsActive(self):
        if App.ActiveDocument:
            # if there is a Model object in the active document:
            if App.ActiveDocument.getObject('Model'):
                return(True)
        # if there is no reason to be active:
        return(False)


    def Activated(self):
        # check that we have somewhere to put our stuff
        self.asmDoc = App.ActiveDocument
        modelObj = self.checkModel()
        fastenerName = self.fastenerName+'_1'
        if modelObj:
            # this is a pre-made document in the Asm4 library, containing base Fastener objects
            fastenerDoc = self.getFastenersDoc()
            newFastener = modelObj.addObject(self.asmDoc.copyObject( fastenerDoc.getObject(self.fastenerType), True ))[0]

            # update the link ...
            newFastener.recompute()

            # ... and launch the placement of the inserted part
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.asmDoc.Name, 'Model', newFastener.Name+'.' )
            Gui.runCommand( 'Asm4_placeFastener' )



    def checkModel(self):
        # of nothing is selected ...
        if App.ActiveDocument.getObject('Model'):
            # ... but there is a Model:
            return App.ActiveDocument.getObject('Model')
        else:
            return(False)


    def getFastenersDoc(self):
        # list of all open documents in the sessions
        docList = App.listDocuments()
        for doc in docList:
            # if the Fastener's document is already open
            if doc == 'Fasteners':
                fastenersDoc = App.getDocument('Fasteners')
                return fastenersDoc
        # if the Fastner document isn't yet open:
        fastenersDocPath = os.path.join( Asm4.libPath , 'Fasteners.FCStd')
        # The document is opened in the background:
        fastenersDoc = App.openDocument( fastenersDocPath, hidden='True')
        # and we reset the original document as active:
        App.setActiveDocument( self.asmDoc.Name )
        return fastenersDoc



"""
    +-----------------------------------------------+
    |                  placeFastener                |
    +-----------------------------------------------+
"""
class placeFastener( QtGui.QDialog ):

    def __init__(self):
        super(placeFastener,self).__init__()
        self.drawUI()



    def GetResources(self):
        return {"MenuText": "Edit Attachment of a Fastener",
                "ToolTip": "Edit Attachment of a Fastener",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_mvFastener.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if App.ActiveDocument:
            # is something selected ?
            selObj = self.GetSelection()
            if selObj != None:
                return True
        else:
            return False 


    def GetSelection(self):
        # check that there is an App::Part called 'Model'
        screwObj = None
        if not App.ActiveDocument.getObject('Model'):
            return screwObj
        for selObj in Gui.Selection.getSelectionEx():
            obj = selObj.Object
            if (hasattr(obj,'Proxy') and isinstance(obj.Proxy, FSBaseObject)):
                screwObj = obj
        return screwObj


    def msgNotAsm4(self):
        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle('Warning')
        msgBox.setIcon(QtGui.QMessageBox.Critical)
        msgBox.setText("This doesn't seem to be an Assembly4 Fastener")
        msgBox.exec_()
        return(False)


    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):

        # get the current active document to avoid errors if user changes tab
        self.activeDoc = App.activeDocument()
        # the parent (top-level) assembly is the App::Part called Model (hard-coded)
        self.parentAssembly = self.activeDoc.Model

        # check that we have selected a PartDesign::CoordinateSystem
        self.selectedFastener = []
        selection = self.GetSelection()
        if selection == None:
            self.close()
        else:
            self.selectedFastener = selection

        # check that the fastener is an Asm4 fastener
        if not hasattr(self.selectedFastener,'AssemblyType'):
            Asm4.makeAsmProperties(self.selectedFastener)
        asmType = self.selectedFastener.AssemblyType
        # we only deal with Asm4 or empty types
        if asmType!='Asm4EE' and asmType!='':
            Asm4.warningBox("This doesn't seem to be an Assembly4 Fastener")
            return(False)

        # check where the fastener was attached to
        (self.old_Parent, separator, self.old_parentLCS) = self.selectedFastener.AttachedTo.partition('#')

        # get and store the current expression engine:
        self.old_EE = ''
        old_EE = self.selectedFastener.ExpressionEngine
        if old_EE:
            for ( key, expr ) in old_EE:
                #( key, expr ) = ee
                if key=='Placement':
                    self.old_EE = expr

        # Now we can draw the UI
        self.initUI()
        self.show()

        # decode the old ExpressionEngine
        # if the decode is unsuccessful, old_Expression is set to False
        # and old_attPart and old_attLCS are set to 'None'
        old_Parent = ''
        old_parentPart = ''
        old_parentLCS = ''
        if  self.old_EE and self.old_Parent:
            ( old_Parent, old_parentPart, old_parentLCS ) = self.splitExpressionFastener( self.old_EE, self.old_Parent )
        #self.expression.setText( 'old_Parent = '+ old_Parent )

        # We get all the App::Link parts in the assembly 
        self.asmParts = []
        # the first item is "Select linked Part" therefore we add an empty object
        self.asmParts.append( [] )
        # We alse add the parent assembly
        self.asmParts.append( self.parentAssembly )
        # Add it as first element to the drop-down combo-box
        parentIcon = self.parentAssembly.ViewObject.Icon
        self.parentList.addItem( parentIcon, 'Parent Assembly', self.parentAssembly )
        # find all the linked parts in the assembly
        for obj in self.activeDoc.findObjects("App::Link"):
            if obj.LinkedObject.isDerivedFrom('App::Part'):
                # add it to our tree table if it's a link to an App::Part ...
                self.asmParts.append( obj )
                # ... and add to the drop-down combo box with the assembly tree's parts
                objIcon = obj.LinkedObject.ViewObject.Icon
                self.parentList.addItem( objIcon, obj.Name, obj)

        # find the oldPart in the part list...
        parent_index = 1
        if old_Parent == 'Parent Assembly':
            parent_found = True
        else:
            parent_found = False
            for item in self.asmParts[1:]:
                if item.Name == old_Parent:
                    parent_found = True
                    break
                else:
                    parent_index = parent_index +1
        if not parent_found:
            parent_index = 0
        self.parentList.setCurrentIndex( parent_index )
        # this should have triggered self.getPartLCS() to fill the LCS list


        # find the oldLCS in the list of LCS of the linked part...
        lcs_found = []
        lcs_found = self.attLCSlist.findItems( old_parentLCS, QtCore.Qt.MatchExactly )
        if lcs_found:
            # ... and select it
            self.attLCSlist.setCurrentItem( lcs_found[0] )
        else:
            # may-be it was renamed, see if we can find it as (name)
            lcs_found = self.attLCSlist.findItems( '('+old_parentLCS+')', QtCore.Qt.MatchContains )
            if lcs_found:
                self.attLCSlist.setCurrentItem( lcs_found[0] )



    """
    +-----------------------------------------------+
    | check that all necessary things are selected, |
    |   populate the expression with the selected   |
    |    elements, put them into the constraint     |
    |   and trigger the recomputation of the part   |
    +-----------------------------------------------+
    """
    def onApply(self):
        # get the name of the part to attach to:
        # it's either the top level part name ('Model')
        # or the provided link's name.

        if self.parentList.currentText() == 'Parent Assembly':
            a_Link = 'Parent Assembly'
            a_Part = None
        elif self.parentList.currentIndex() > 1:
            parent = self.asmParts[ self.parentList.currentIndex() ]
            a_Link = parent.Name
            a_Part = parent.LinkedObject.Document.Name
        else:
            a_Link = None
            a_Part = None

        # the attachment LCS's name in the parent
        # check that something is selected in the QlistWidget
        if self.attLCSlist.selectedItems():
            a_LCS = self.attLCStable[ self.attLCSlist.currentRow() ].Name
        else:
            a_LCS = None

        # check that all of them have something in
        if a_Link and a_LCS :
            # <<LinkName>>.Placement.multiply( <<LinkName>>.<<LCS.>>.Placement )
            # expr = '<<'+ a_Part +'>>.Placement.multiply( <<'+ a_Part +'>>.<<'+ a_LCS +'.>>.Placement )'
            expr = self.makeExpressionFastener( a_Link, a_Part, a_LCS )
            # this can be skipped when this method becomes stable
            self.expression.setText( expr )
            # indicate the this fastener has been placed with the Assembly4 workbench
            if not hasattr(self.selectedFastener,'AssemblyType'):
                Asm4.makeAsmProperties(self.selectedFastener)
            self.selectedFastener.AssemblyType = 'Asm4EE'
            # the fastener is attached by its Origin, no extra LCS
            self.selectedFastener.AttachedBy = 'Origin'
            # store the part where we're attached to in the constraints object
            self.selectedFastener.AttachedTo = a_Link+'#'+a_LCS
            # load the built expression into the Expression field of the constraint
            self.selectedFastener.setExpression( 'Placement', expr )
            # check the Invert and Offset values
            self.selectedFastener.invert = self.Invert.isChecked()
            self.selectedFastener.offset = self.Offset.value()
            # recompute the object to apply the placement:
            self.selectedFastener.recompute()
            self.parentAssembly.recompute()
            self.activeDoc.recompute()
            # highlight the selected fastener in its new position
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedFastener.Name +'.')
        else:
            self.expression.setText( 'Problem in selections' )
        return



    """
    +-----------------------------------------------+
    |         populate the ExpressionEngine         |
    |               for a Datum object              |
    |       linked to an LCS in a sister part       |
    +-----------------------------------------------+
    """
    def makeExpressionFastener( self, attLink, attPart, attLCS ):
        # check that everything is defined
        if attLink and attLCS:
            # expr = Link.Placement * LinkedPart#LCS.Placement
            expr = attLCS +'.Placement * AttachmentOffset'
            if attPart:
                expr = attLink+'.Placement * '+attPart+'#'+expr
        else:
            expr = False
        return expr



    """
    +-----------------------------------------------+
    |           split the ExpressionEngine          |
    |        of a linked Datum object to find       |
    |         the old attachment Part and LCS       |
    +-----------------------------------------------+
    """
    def splitExpressionFastener(self, expr, parent ):
        # default return value
        retval = ( '', 'None', 'None' )
        if parent == 'Parent Assembly':
            # we're attached to an LCS in the parent assembly
            # expr = LCS_in_the_assembly.Placement * AttachmentOffset
            ( attLCS, separator, rest1 ) = expr.partition('.Placement * AttachmentOff')
            restFinal = rest1[0:3]
            attLink = parent
            attPart = 'None'
            #self.expression.setText( 'parentAsm ***'+restFinal+'***'+attLink+'***'+attLCS+'***' )
            #return ( restFinal, 'None', 'None', 'None', 'None', 'None')
        else:
            parentObj = self.parentAssembly.getObject(parent)
            if parentObj and parentObj.TypeId == 'App::Link':
                parentDoc = parentObj.LinkedObject.Document
                # if the link points to a Part in the same document
                if parentDoc == self.activeDoc:
                    # we're attached to an LCS in a part in the same document
                    # expr = ParentLink.Placement * LCS_parent.Placement * AttachmentOffset
                    ( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
                    ( attLCS,     separator, rest2 ) = rest1.partition('.Placement * AttachmentOff')
                    restFinal = rest2[0:3]
                    attPart = 'None'
                    #self.expression.setText( 'sameDoc ***'+restFinal+'***'+attLink+'***'+attLCS+'***' )
                else:
                    # we're attached to an LCS in a sister part in an external document
                    # expr = ParentLink.Placement * ParentPart#LCS.Placement * AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
                    ( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
                    ( attPart,    separator, rest2 ) = rest1.partition('#')
                    ( attLCS,     separator, rest3 ) = rest2.partition('.Placement * AttachmentOff')
                    restFinal = rest3[0:3]
                    #self.expression.setText( 'extDoc ***'+restFinal+'***'+attLink+'***'+attLCS+'***' )
                    #return ( restFinal, 'None', 'None', 'None', 'None', 'None')
        if restFinal=='set' and attLink==parent :
            # wow, everything went according to plan
            retval = ( attLink, attPart, attLCS )
        #self.expression.setText( attPart +'***'+ attLCS )
        else:
            # rats ! But still, if the decode is unsuccessful, put some text for debugging
            retval = ( '', restFinal, attLink )
        #self.expression.setText( '***'+restFinal+'***'+attLink+'***'+attLCS+'***' )
        return retval
    


    """
    +-----------------------------------------------+
    |           get all the LCS in a part           |
    +-----------------------------------------------+
    """
    def getPartLCS( self, part ):
        partLCS = [ ]
        # parse all objects in the part (they return strings)
        for objName in part.getSubObjects():
            # get the proper objects
            # all object names end with a "." , this needs to be removed
            obj = part.getObject( objName[0:-1] )
            if obj.TypeId == 'PartDesign::CoordinateSystem' or obj.TypeId == 'PartDesign::Point':
                partLCS.append( obj )
        return partLCS



    """
    +------------------------------------------------+
    |   fill the LCS list when changing the parent   |
    +------------------------------------------------+
    """
    def onParentList(self):
        # clear the LCS list
        self.attLCSlist.clear()
        self.attLCStable = []
        # clear the selection in the GUI window
        Gui.Selection.clearSelection()
        # keep the fastener selected
        Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedFastener.Name+'.')
        # the current text in the combo-box is the link's name...
        # parentName = self.attLCStable[ self.parentList.currentRow() ].Name
        # parentName = self.parentList.currentText()
        # ... or it's 'Parent Assembly' then the parent is the 'Model' root App::Part		
        if self.parentList.currentText() == 'Parent Assembly':
            parentName = 'Parent Assembly'
            parentPart = self.activeDoc.getObject( 'Model' )
            # we get the LCS directly in the root App::Part 'Model'
            self.attLCStable = self.getPartLCS( parentPart )
        # if something is selected
        elif self.parentList.currentIndex() > 1:
            parentName = self.asmParts[ self.parentList.currentIndex() ].Name
            parentPart = self.activeDoc.getObject( parentName )
            if parentPart:
                # we get the LCS from the linked part
                self.attLCStable = self.getPartLCS( parentPart.LinkedObject )
                # highlight the selected part:
                Gui.Selection.addSelection( parentPart.Document.Name, 'Model', parentPart.Name+'.' )
        # something wrong
        else:
            return
        
        # build the list
        for lcs in self.attLCStable:
            newItem = QtGui.QListWidgetItem()
            if lcs.Name == lcs.Label:
                newItem.setText( lcs.Name )
            else:
                newItem.setText( lcs.Label + ' (' +lcs.Name+ ')' )
            newItem.setIcon( lcs.ViewObject.Icon )
            self.attLCSlist.addItem( newItem )
            #self.attLCStable.append(lcs)
        return


    """
    +-----------------------------------------------+
    |  An LCS has been clicked in 1 of the 2 lists  |
    |              We highlight both LCS            |
    +-----------------------------------------------+
    """
    def onDatumClicked( self ):
        # clear the selection in the GUI window
        Gui.Selection.clearSelection()
        # keep the fastener selected
        Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedFastener.Name+'.')
        # LCS in the parent
        if self.attLCSlist.selectedItems():
            #a_LCS = self.attLCSlist.selectedItems()[0].text()
            a_LCS = self.attLCStable[ self.attLCSlist.currentRow() ].Name
            # get the part where the selected LCS is
            a_Part = self.parentList.currentText()
            # parent assembly and sister part need a different treatment
            if a_Part == 'Parent Assembly':
                linkDot = ''
            else:
                linkDot = a_Part+'.'
            Gui.Selection.addSelection( self.activeDoc.Name, 'Model', linkDot+a_LCS+'.')
        # show the resulting placement
        self.onApply()


    """
    +-----------------------------------------------+
    |    insert instance free of any attachment     |
    +-----------------------------------------------+
    """
    def freeInsert(self):
        # ask for confirmation before resetting everything
        fName  = self.selectedFastener.Name
        fLabel = self.selectedFastener.Label
        if fName==fName:
            fText = fName
        else:
            fText = fName+' ('+fName+')'
        # see whether the ExpressionEngine field is filled
        if self.old_EE :
            # if yes, then ask for confirmation
            confirmed = Asm4.confirmBox('This command will release all attachments on '+fText+' and set it to manual positioning in its current location.')
            # if not, then it's useless to bother the user
        else:
            confirmed = True
        if confirmed:
            # unset the ExpressionEngine for the Placement
            # self.selectedFastener.setExpression( 'Placement', expr )
            self.selectedFastener.setExpression('Placement', None)
            # reset the assembly properties
            Asm4.makeAsmProperties(self.selectedFastener)
            # finish
            self.close()
        else:
            return


    """
    +-----------------------------------------------+
    |                     Cancel                    |
    |           restores the previous values        |
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



    def initUI(self):
        # fill it in the GUI
        self.fastenerName.setText( self.selectedFastener.Label )
        self.parentList.clear()
        self.parentList.addItem( 'Select parent Part' )
        self.attLCSlist.clear()
        self.expression.clear()
        self.Invert.setChecked( self.selectedFastener.invert )
        self.Offset.setValue( self.selectedFastener.offset )



    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        # make this dialog stay above the others, always visible
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.setWindowTitle('Attach a Fastener')
        self.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumSize(470, 570)
        self.resize(470,570)
        self.setModal(False)

        # the name as seen in the tree of the selected link
        self.fastenerName = QtGui.QLineEdit(self)
        self.fastenerName.setReadOnly(True)
        # combobox showing all available App::Link
        self.parentList = QtGui.QComboBox(self)
        # The list of all attachment LCS in the assembly is a QListWidget
        # it is populated only when the parent combo-box is activated
        self.attLCSlist = QtGui.QListWidget(self)
        # Expression Engine
        self.expression = QtGui.QLineEdit(self)
        # Invert ?
        self.Invert = QtGui.QCheckBox(self)
        # Offset value
        self.Offset = QtGui.QDoubleSpinBox(self)
        self.Offset.setMinimum(-100.00)
        self.Offset.setMaximum(100.00)
        # Cancel button
        self.CancelButton = QtGui.QPushButton('Close', self)
        # Free Insert button
        self.FreeButton = QtGui.QPushButton('Free Insert', self)
        self.FreeButton.setToolTip("Insert the fastener into the assembly with manual placement. \nTo move it right-click on its name in the tree and select \"Transform\"")
        # OK button
        self.OkButton = QtGui.QPushButton('OK', self)
        self.OkButton.setDefault(True)

        # Build the window layout
        self.mainLayout = QtGui.QVBoxLayout(self)
        self.formLayout = QtGui.QFormLayout(self)
        self.formLayout.addRow(QtGui.QLabel('Fastener :'),self.fastenerName)
        self.formLayout.addRow(QtGui.QLabel('Attached to :'),self.parentList)
        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(QtGui.QLabel("Select attachment LCS in parent Part :"))
        self.mainLayout.addWidget(self.attLCSlist)
        self.mainLayout.addWidget(QtGui.QLabel("Expression Engine :"))
        self.mainLayout.addWidget(self.expression)
        self.InvertOffset = QtGui.QHBoxLayout(self)
        self.InvertOffset.addWidget(QtGui.QLabel('Invert'))
        self.InvertOffset.addWidget(self.Invert)
        self.InvertOffset.addStretch()
        self.InvertOffset.addWidget(QtGui.QLabel('Offset'))
        self.InvertOffset.addWidget(self.Offset)
        self.mainLayout.addLayout(self.InvertOffset)
        self.buttonsLayout = QtGui.QHBoxLayout(self)
        self.buttonsLayout.addWidget(self.CancelButton)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.FreeButton)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.OkButton)
        self.mainLayout.addWidget(QtGui.QLabel(' '))
        self.mainLayout.addLayout(self.buttonsLayout)

        # Actions
        #self.Invert.stateChanged.connect(self.onInvert)
        self.CancelButton.clicked.connect(self.onCancel)
        self.OkButton.clicked.connect(self.onOK)
        self.parentList.currentIndexChanged.connect( self.onParentList )
        self.attLCSlist.itemClicked.connect( self.onDatumClicked )
        self.Invert.clicked.connect(self.onApply)
        self.Offset.valueChanged.connect(self.onApply)
        self.FreeButton.clicked.connect(self.freeInsert)




"""
    +-----------------------------------------------+
    |       add the commands to the workbench       |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_insertScrew', insertFastener('Screw') )
Gui.addCommand( 'Asm4_insertNut',  insertFastener('Nut') )
Gui.addCommand( 'Asm4_insertWasher', insertFastener('Washer') )

Gui.addCommand( 'Asm4_placeFastener', placeFastener() )

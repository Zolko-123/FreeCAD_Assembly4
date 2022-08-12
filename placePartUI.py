#!/usr/bin/env python3
# coding: utf-8
#
# placePartUI.py


import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4





"""
    +-----------------------------------------------+
    |    The UI and functions in the Task panel     |
    +-----------------------------------------------+
"""
class placePartUI():
    
    def __init__(self):
        self.form = QtGui.QWidget()
        iconFile = os.path.join( Asm4.iconPath , 'Place_Link.svg')
        self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle('Place a Part in the assembly')

        # get the current active document to avoid errors if user changes tab
        self.activeDoc = App.activeDocument()
        # the parent (top-level) assembly is the App::Part called Model (hard-coded)
        self.rootAssembly = Asm4.getAssembly()
        # has been checked before calling
        try:
            self.selectedObj = Gui.Selection.getSelection()[0]
            assert self.selectedObj.getTypeIdOfProperty('Placement')=='App::PropertyPlacement'
        except:
            Asm4.warningBox('Please select ab object with a Placement property')

        # check where the fastener was attached to
        (self.old_Parent, separator, self.old_parentLCS) = self.selectedObj.AttachedTo.partition('#')
        # get and store the Placement's current ExpressionEngine:
        self.old_EE = Asm4.placementEE( self.selectedObj.ExpressionEngine )
        if hasattr(self.selectedObj,'AttachmentOffset'):
            self.old_AO = self.selectedObj.AttachmentOffset
        else:
            self.old_AO = None

        # Now we can draw the UI
        self.drawUI()
        self.initUI()
        # now self.parentList and self.parentTable are available

        # find all the linked parts in the assembly
        for obj in self.activeDoc.findObjects("App::Link"):
            if self.rootAssembly.getObject(obj.Name) is not None and hasattr(obj.LinkedObject,'isDerivedFrom'):
                linkedObj = obj.LinkedObject
                if linkedObj.isDerivedFrom('App::Part') or linkedObj.isDerivedFrom('PartDesign::Body'):
                    # add to the object table holding the objects ...
                    self.parentTable.append( obj )
                    # ... and add to the drop-down combo box with the assembly tree's parts
                    objIcon = linkedObj.ViewObject.Icon
                    objText = Asm4.labelName(obj)
                    self.parentList.addItem( objIcon, objText, obj)

        # decode the old ExpressionEngine
        # if the decode is unsuccessful, old_Expression is set to False
        # and old_attPart and old_attLCS are set to 'None'
        old_Parent = ''
        old_parentPart = ''
        old_parentLCS = ''
        if  self.old_EE and self.old_Parent:
            ( old_Parent, old_parentPart, old_parentLCS ) = self.splitExpression( self.old_EE, self.old_Parent )

        # find the oldPart in the part list...
        parent_index = 1
        if old_Parent == 'Parent Assembly':
            parent_found = True
        else:
            parent_found = False
            for item in self.parentTable[1:]:
                if item.Name == old_Parent:
                    parent_found = True
                    break
                else:
                    parent_index += 1
        if not parent_found:
            parent_index = 0
        self.parentList.setCurrentIndex( parent_index )
        # this should have triggered self.getPartLCS() to fill the LCS list

        # find the oldLCS in the list of LCS of the linked part...
        lcs_found = []
        lcs_found = self.attLCSlist.findItems( old_parentLCS, QtCore.Qt.MatchExactly )
        # may-be it was renamed, see if we can find it as (name)
        if not lcs_found:
            lcs_found = self.attLCSlist.findItems( '('+old_parentLCS+')', QtCore.Qt.MatchContains )
        if lcs_found:
            # ... and select it
            self.attLCSlist.setCurrentItem( lcs_found[0] )

        Gui.Selection.addObserver(self, 0)


    # this is the end ...
    def finish(self):
        # remove the  observer
        Gui.Selection.removeObserver(self)
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
        # restore previous values if they existed
        if self.old_AO is not None:
            self.selectedObj.AttachmentOffset = self.old_AO
        if self.old_EE is not None:
            self.selectedObj.setExpression('Placement', self.old_EE )
        self.selectedObj.recompute()
        # highlight the selected LCS in its new position
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection( self.activeDoc.Name, self.rootAssembly.Name, self.selectedObj.Name +'.')
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
        # get the name of the part to attach to:
        # it's either the top level part name ('Model')
        # or the provided link's name.
        if self.parentList.currentText() == 'Parent Assembly':
            a_Link = 'Parent Assembly'
            a_Part = None
        elif self.parentList.currentIndex() > 1:
            parent = self.parentTable[ self.parentList.currentIndex() ]
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
            # add Asm4 properties if necessary
            Asm4.makeAsmProperties( self.selectedObj, reset=True )
            # hide "offset" and "invert" properties to avoid confusion as they are not used in Asm4
            if hasattr( self.selectedObj, 'offset' ):
                self.selectedObj.setPropertyStatus('offset', 'Hidden')
            if hasattr( self.selectedObj, 'invert' ):
                self.selectedObj.setPropertyStatus('invert', 'Hidden')

            # <<LinkName>>.Placement.multiply( <<LinkName>>.<<LCS.>>.Placement )
            # expr = '<<'+ a_Part +'>>.Placement.multiply( <<'+ a_Part +'>>.<<'+ a_LCS +'.>>.Placement )'
            
            Asm4.placeObjectToLCS(self.selectedObj, a_Link, a_Part, a_LCS)
            
            # highlight the selected fastener in its new position
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.activeDoc.Name, self.rootAssembly.Name, self.selectedObj.Name +'.')
        else:
            FCC.PrintWarning("Problem in selections\n")
        return



    """
    +-----------------------------------------------+
    |           split the ExpressionEngine          |
    |        of a linked Datum object to find       |
    |         the old attachment Part and LCS       |
    +-----------------------------------------------+
    """
    def splitExpression(self, expr, parent ):
        # default return value
        retval = ( expr, 'None', 'None' )
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
            parentObj = self.rootAssembly.getObject(parent)
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


    # fill the LCS list when changing the parent
    def onParentList(self):
        # clear the LCS list
        self.attLCSlist.clear()
        self.attLCStable = []
        # clear the selection in the GUI window
        Gui.Selection.clearSelection()
        # keep the fastener selected
        Gui.Selection.addSelection( self.activeDoc.Name, self.rootAssembly.Name, self.selectedObj.Name+'.')
        # the current text in the combo-box is the link's name...
        # ... or it's 'Parent Assembly' then the parent is the 'Model' root App::Part		
        if self.parentList.currentText() == 'Parent Assembly':
            parentName = 'Parent Assembly'
            # parentPart = self.activeDoc.getObject( 'Model' )
            parentPart = self.rootAssembly
            # we get the LCS directly in the root App::Part 
            self.attLCStable = Asm4.getPartLCS( parentPart )
            self.parentDoc.setText( parentPart.Document.Name+'#'+Asm4.labelName(parentPart) )
        # if something is selected
        elif self.parentList.currentIndex() > 1:
            parentName = self.parentTable[ self.parentList.currentIndex() ].Name
            parentPart = self.activeDoc.getObject( parentName )
            if parentPart:
                # we get the LCS from the linked part
                self.attLCStable = Asm4.getPartLCS( parentPart.LinkedObject )
                # linked part & doc
                dText = parentPart.LinkedObject.Document.Name +'#'
                # if the linked part has been renamed by the user
                pText = Asm4.labelName( parentPart.LinkedObject )
                self.parentDoc.setText( dText + pText )
                # highlight the selected part:
                Gui.Selection.addSelection( \
                        parentPart.Document.Name, self.rootAssembly.Name, parentPart.Name+'.' )
                QtCore.QTimer.singleShot(1500, lambda:Gui.Selection.removeSelection( \
                        parentPart.Document.Name, self.rootAssembly.Name, parentPart.Name+'.' ) )

        # something wrong
        else:
            return
        
        # build the list
        self.attLCSlist.clear()
        for lcs in self.attLCStable:
            newItem = QtGui.QListWidgetItem()
            newItem.setText(Asm4.labelName(lcs))
            newItem.setIcon( lcs.ViewObject.Icon )
            self.attLCSlist.addItem( newItem )
            #self.attLCStable.append(lcs)
        return


    # An LCS has been clicked in 1 of the 2 lists, we highlight both LCS            |
    def onDatumClicked( self ):
        # clear the selection in the GUI window
        Gui.Selection.clearSelection()
        # keep the fastener selected
        Gui.Selection.addSelection( self.activeDoc.Name, self.rootAssembly.Name, self.selectedObj.Name+'.')
        # LCS in the parent
        if self.attLCSlist.selectedItems():
            #a_LCS = self.attLCSlist.selectedItems()[0].text()
            a_LCS = self.attLCStable[ self.attLCSlist.currentRow() ].Name
            # get the part where the selected LCS is
            #a_Part = self.parentList.currentText()
            a_Part = self.parentTable[ self.parentList.currentIndex() ]
            # parent assembly and sister part need a different treatment
            if a_Part == 'Parent Assembly':
                linkDot = ''
            else:
                linkDot = a_Part+'.'
            Gui.Selection.addSelection( self.activeDoc.Name, self.rootAssembly.Name, linkDot+a_LCS+'.')
            FCC.PrintMessage("selection: "+ linkDot+a_LCS+'.' +"\n")
        # show the resulting placement
        self.onApply()
    
    
    # selection observer
    def addSelection(self, doc, obj, sub, pnt):
        selPath = Asm4.getSelectionPath(doc, obj, sub)
        selObj = Gui.Selection.getSelection()[0]
        if selObj and len(selPath) > 2:
            selLinkName = selPath[2]
            selLink = App.ActiveDocument.getObject(selLinkName)
            idx = self.parentList.findText(Asm4.labelName(selLink), QtCore.Qt.MatchExactly)
            # if selLink is in the child list
            if idx >= 0:
                self.parentList.setCurrentIndex(idx)
            # else it might be an LCS in the root assembly
            elif selLink.TypeId in Asm4.datumTypes:
                self.parentList.setCurrentIndex(1)
            # this has triggered to fill the LCS list
            found = self.attLCSlist.findItems(Asm4.labelName(selObj), QtCore.Qt.MatchExactly)
            if len(found) > 0:
                self.attLCSlist.clearSelection()
                found[0].setSelected(True)
                self.attLCSlist.scrollToItem(found[0])
                self.attLCSlist.setCurrentRow(self.attLCSlist.row(found[0]))
                self.onApply()


    # Rotations
    def rotAxis( self, placement ):
        # placement is of TypeId 'Placement'
        # we only add the rotation, not the position
        addRotation = placement.Rotation
        oldRotation  = self.selectedObj.AttachmentOffset.Rotation
        newRotation  = oldRotation.multiply( addRotation )
        self.selectedObj.AttachmentOffset.Rotation = newRotation
        self.selectedObj.recompute()

    def onRotX(self):
        # return is a Placement extract the Rotation of it
        self.rotAxis(Asm4.rotX)

    def onRotY(self):
        self.rotAxis(Asm4.rotY)

    def onRotZ(self):
        self.rotAxis(Asm4.rotZ)

    # Translations
    def movePart( self ):
        x = self.XtranslSpinBox.value()
        y = self.YtranslSpinBox.value()
        z = self.ZtranslSpinBox.value()
        self.selectedObj.AttachmentOffset.Base = App.Vector(x,y,z)
        self.selectedObj.recompute()

    # fill in the GUI
    def initUI(self):
        self.selectedObject.setText( self.selectedObj.Label )
        self.attLCSlist.clear()
        # Initialize the assembly tree with the Parent Assembly as first element
        # clear the available parents combo box
        self.parentTable = []
        self.parentList.clear()
        self.parentTable.append( [] )
        self.parentList.addItem('Please select')
        self.parentTable.append( self.rootAssembly )
        parentIcon = self.rootAssembly.ViewObject.Icon
        self.parentList.addItem( parentIcon, 'Parent Assembly', self.rootAssembly )
        # set the old position values
        self.XtranslSpinBox.setValue( self.selectedObj.AttachmentOffset.Base.x )
        self.YtranslSpinBox.setValue( self.selectedObj.AttachmentOffset.Base.y )
        self.ZtranslSpinBox.setValue( self.selectedObj.AttachmentOffset.Base.z )


    # defines the UI, only static elements
    def drawUI(self):
        # Build the window layout
        self.mainLayout = QtGui.QVBoxLayout()

        # the name as seen in the tree of the selected link
        self.formLayout = QtGui.QFormLayout()
        self.selectedObject = QtGui.QLineEdit()
        self.selectedObject.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Selected Object :'),self.selectedObject)
        # combobox showing all available App::Link
        self.parentList = QtGui.QComboBox()
        self.parentList.setMaximumWidth(300)
        self.formLayout.addRow(QtGui.QLabel('Attach to :'),self.parentList)
        self.mainLayout.addLayout(self.formLayout)

        # the document containing the linked object
        self.parentDoc = QtGui.QLineEdit()
        self.parentDoc.setReadOnly(True)
        self.mainLayout.addWidget(self.parentDoc)

        # The list of all attachment LCS in the assembly is a QListWidget
        # it is populated only when the parent combo-box is activated
        self.mainLayout.addWidget(QtGui.QLabel("Select attachment LCS in parent Part :"))
        self.attLCSlist = QtGui.QListWidget()
        self.mainLayout.addWidget(self.attLCSlist)

        # X Translation Value
        self.XoffsetLayout = QtGui.QHBoxLayout()
        self.XtranslSpinBoxLabel = self.XoffsetLayout.addWidget(QtGui.QLabel("X Translation :"))
        self.XtranslSpinBox = Asm4.QUnitSpinBox()
        self.XtranslSpinBox.setRange(-999999.00, 999999.00)
        self.XtranslSpinBox.setDecimals(App.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt('Decimals'))
        self.XtranslSpinBox.setToolTip("Translation along X axis")
        self.RotXButton = QtGui.QPushButton('Rotate X +90°')
        self.RotXButton.setToolTip("Rotate 90 deg around X axis")
        # add the QLDoubleSpinBox
        self.XoffsetLayout.addWidget(self.XtranslSpinBox)
        self.XoffsetLayout.addStretch()
        self.XoffsetLayout.addWidget(self.RotXButton)
        self.mainLayout.addLayout(self.XoffsetLayout)

        # Y Translation Value
        self.YoffsetLayout = QtGui.QHBoxLayout()
        self.YtranslSpinBoxLabel = self.YoffsetLayout.addWidget(QtGui.QLabel("Y Translation :"))
        self.YtranslSpinBox = Asm4.QUnitSpinBox()
        self.YtranslSpinBox.setRange(-999999.00, 999999.00)
        self.YtranslSpinBox.setDecimals(App.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt('Decimals'))
        self.YtranslSpinBox.setToolTip("Translation along Y")
        self.RotYButton = QtGui.QPushButton('Rotate Y +90°')
        self.RotYButton.setToolTip("Rotate 90 deg around Y axis")
        # add the QLDoubleSpinBox
        self.YoffsetLayout.addWidget(self.YtranslSpinBox)
        self.YoffsetLayout.addStretch()
        self.YoffsetLayout.addWidget(self.RotYButton)
        self.mainLayout.addLayout(self.YoffsetLayout)

        # Z Translation Value
        self.ZoffsetLayout = QtGui.QHBoxLayout()
        self.ZtranslSpinBoxLabel = self.ZoffsetLayout.addWidget(QtGui.QLabel("Z Translation :"))
        self.ZtranslSpinBox = Asm4.QUnitSpinBox()
        self.ZtranslSpinBox.setRange(-999999.00, 999999.00)
        self.ZtranslSpinBox.setDecimals(App.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt('Decimals'))
        self.ZtranslSpinBox.setToolTip("Translation along Z:")
        self.RotZButton = QtGui.QPushButton('Rotate Z +90°')
        self.RotZButton.setToolTip("Rotate 90 deg around Z axis")
        # add to the layout
        self.ZoffsetLayout.addWidget(self.ZtranslSpinBox)
        self.ZoffsetLayout.addStretch()
        self.ZoffsetLayout.addWidget(self.RotZButton)
        self.mainLayout.addLayout(self.ZoffsetLayout)

        # apply the layout to the main window
        self.form.setLayout(self.mainLayout)

        # Actions
        self.parentList.currentIndexChanged.connect( self.onParentList )
        self.parentList.activated.connect( self.onParentList )
        ##self.attLCSlist.itemClicked.connect( self.onDatumClicked )
        self.attLCSlist.itemClicked.connect( self.onApply )
        self.RotXButton.clicked.connect( self.onRotX )
        self.RotYButton.clicked.connect( self.onRotY )
        self.RotZButton.clicked.connect( self.onRotZ)
        self.XtranslSpinBox.valueChanged.connect(self.movePart)
        self.YtranslSpinBox.valueChanged.connect(self.movePart)
        self.ZtranslSpinBox.valueChanged.connect(self.movePart)


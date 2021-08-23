#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# placeDatumCmd.py

import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4




"""
    +-----------------------------------------------+
    |               Helper functions                |
    +-----------------------------------------------+
"""


# icon to show in the Menu, toolbar and widget window
iconFile = os.path.join( Asm4.iconPath , 'Place_Datum.svg')



"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class placeDatumCmd():
    def __init__(self):
        super(placeDatumCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Edit Placement of a Datum object",
                "ToolTip": "Attach a Datum object in the assembly to a Datum in a linked Part",
                "Pixmap" : iconFile
                }

    def IsActive(self):
        if App.ActiveDocument and Asm4.getSelectedDatum():
            return True
        return False

    def Activated(self):
        selectedDatum = Asm4.getSelectedDatum()
        # check if the datum object is already mapped to something
        if selectedDatum.MapMode == 'Deactivated' and Asm4.checkModel():
            Gui.Control.showDialog( placeDatumUI() )
        else:
            Gui.runCommand('Part_EditAttachment')
            '''
            message = 'This datum object \"'+selectedDatum.Label+'\" is mapped to some geometry. Attaching-it with Assembly4 will loose this mapping.'
            if Asm4.confirmBox(message):
                # unset MappingMode
                selectedDatum.Support = None
                selectedDatum.MapMode = 'Deactivated'
                Gui.Control.showDialog( placeDatumUI() )
            else:
                # don't do anything and ...
                return
            '''



"""
    +-----------------------------------------------+
    |    The UI and functions in the Task panel     |
    +-----------------------------------------------+
"""
class placeDatumUI():
    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base        
        self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle('Place a Datum object in the assembly')

        # get the current active document to avoid errors if user changes tab
        self.activeDoc = App.activeDocument()
        # the parent (top-level) assembly is the App::Part called Model (hard-coded)
        self.parentAssembly = self.activeDoc.Model

        # check that we have selected a PartDesign::CoordinateSystem
        self.selectedDatum = Asm4.getSelectedDatum()
  
        # Now we can draw the UI
        self.drawUI()
        self.initUI()
        # now self.parentList and self.parentTable are available

        # find all the linked parts in the assembly
        for objName in self.parentAssembly.getSubObjects():
            # remove the trailing .
            obj = self.activeDoc.getObject(objName[0:-1])
            if obj.TypeId=='App::Link':
                # add it to our list if it's a link to an App::Part ...
                if hasattr(obj.LinkedObject,'isDerivedFrom'):
                    linkedObj = obj.LinkedObject
                    if linkedObj.isDerivedFrom('App::Part') or linkedObj.isDerivedFrom('PartDesign::Body'):
                        # add to the object table holding the objects ...
                        self.parentTable.append( obj )
                        # ... and add to the drop-down combo box with the assembly tree's parts
                        objIcon = obj.LinkedObject.ViewObject.Icon
                        objText = Asm4.nameLabel(obj)
                        self.parentList.addItem( objIcon, objText, obj)

        self.old_EE = ' '
        # get and store the Placement's current ExpressionEngine:
        self.old_EE = Asm4.placementEE(self.selectedDatum.ExpressionEngine)

        # decode the old ExpressionEngine
        # if the decode is unsuccessful, old_Expression is set to False
        # and old_attPart and old_attLCS are set to 'None'
        old_Parent = ''
        old_ParentPart = ''
        old_attLCS = ''
        ( old_Parent, old_ParentPart, old_attLCS ) = self.splitExpressionDatum( self.old_EE )

        # find the oldPart in the current part list...
        oldPart = self.parentList.findText( old_Parent )
        # if not found
        if oldPart == -1:
            # set to initial "Select linked Part" entry
            self.parentList.setCurrentIndex( 0 )
        else:
            self.parentList.setCurrentIndex( oldPart )

        parent_found = False
        parent_index = 1
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


        # find the old attachment Datum in the list of the Datums in the linked part...
        # lcs_found = []
        lcs_found = self.attLCSlist.findItems( old_attLCS, QtCore.Qt.MatchExactly )
        if not lcs_found:
            lcs_found = self.attLCSlist.findItems( old_attLCS+' (', QtCore.Qt.MatchContains )
        if lcs_found:
            # ... and select it
            self.attLCSlist.setCurrentItem( lcs_found[0] )


    # this is the end ...
    def finish(self):
        Gui.Control.closeDialog()

    # standard FreeCAD Task panel buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel
                   | QtGui.QDialogButtonBox.Ok
                   | QtGui.QDialogButtonBox.Ignore)

    # Ignore
    def clicked(self, bt):
        if bt == QtGui.QDialogButtonBox.Ignore:
            # ask for confirmation before resetting everything
            msgName = Asm4.nameLabel(self.selectedDatum)
            # see whether the ExpressionEngine field is filled
            if self.selectedDatum.ExpressionEngine :
                # if yes, then ask for confirmation
                confirmed = Asm4.confirmBox('This command will release all attachments on '+msgName+' and set it to manual positioning in its current location.')
                # if not, then it's useless to bother the user
            else:
                confirmed = True
            if confirmed:
                self.selectedDatum.setExpression('Placement', None)
            self.finish()

    # OK
    def accept(self):
        if self.onApply():
            if self.selectedDatum:
                self.selectedDatum.ViewObject.ShowLabel = False
            self.finish()
        else:
            FCC.PrintWarning("Problem in selections\n")

    # Cancel
    def reject(self):
        # restore previous expression if it existed
        if self.old_EE != None:
            self.selectedDatum.setExpression('Placement', self.old_EE )
        if self.selectedDatum and self.selectedDatum.TypeId=='PartDesign::CoordinateSystem':
            self.selectedDatum.ViewObject.ShowLabel = False
        self.selectedDatum.recompute()
        # highlight the selected LCS in its new position
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedDatum.Name +'.')
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
        if self.parentList.currentIndex() > 0:
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
        # constrName has been checked at the beginning
        '''
        if not a_Part :
            FCC.PrintWarning("Problem in selections (no a_Part)\n")
        elif not a_LCS :
            FCC.PrintWarning("Problem in selections (no a_LCS)\n")
        else:
        '''
        retval = False
        if a_Part and a_LCS:
            # don't forget the last '.' !!!
            # <<LinkName>>.Placement.multiply( <<LinkName>>.<<LCS.>>.Placement )
            # expr = '<<'+ a_Part +'>>.Placement.multiply( <<'+ a_Part +'>>.<<'+ a_LCS +'.>>.Placement )'
            expr = Asm4.makeExpressionDatum( a_Link, a_Part, a_LCS )
            # load the built expression into the Expression field of the constraint
            self.activeDoc.getObject( self.selectedDatum.Name ).setExpression( 'Placement', expr )
            # recompute the object to apply the placement:
            self.selectedDatum.ViewObject.ShowLabel = True
            self.selectedDatum.ViewObject.FontSize = 20
            self.selectedDatum.recompute()
            # highlight the selected LCS in its new position
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedDatum.Name +'.')
            retval = True
        return retval


    # fill the LCS list when changing the parent
    def onParentSelected(self):
        # clear the selection in the GUI window
        Gui.Selection.clearSelection()
        # build the LCS table
        self.attLCStable = []
        # the current text in the combo-box is the link's name...
        if self.parentList.currentIndex() > 0:
            parentName = self.parentTable[ self.parentList.currentIndex() ].Name
            parentPart = self.activeDoc.getObject( parentName )
            if parentPart:
                # we get the LCS from the linked part
                self.attLCStable = Asm4.getPartLCS( parentPart.LinkedObject )
                # linked part & doc
                dText = parentPart.LinkedObject.Document.Name +'#'
                # if the linked part has been renamed by the user
                pText = Asm4.nameLabel( parentPart.LinkedObject )
                self.parentDoc.setText( dText + pText )
                # highlight the selected part:
                Gui.Selection.addSelection( parentPart.Document.Name, 'Model', parentPart.Name+'.' )
        # something wrong
        else:
            return
        
        # build the list
        self.attLCSlist.clear()
        for lcs in self.attLCStable:
            newItem = QtGui.QListWidgetItem()
            newItem.setText(Asm4.nameLabel(lcs))
            newItem.setIcon( lcs.ViewObject.Icon )
            self.attLCSlist.addItem( newItem )
            #self.attLCStable.append(lcs)
        return



    # A target Datum has been clicked in the list
    def onDatumSelected( self ):
        # clear the selection in the GUI window
        Gui.Selection.clearSelection()
        # check that something is selected
        if self.attLCSlist.selectedItems():
            # get the linked part where the selected LCS is
            a_Link = self.parentTable[ self.parentList.currentIndex() ].Name
            # LCS in the linked part
            a_LCS = self.attLCStable[ self.attLCSlist.currentRow() ].Name
            Gui.Selection.addSelection( self.activeDoc.Name, 'Model', a_Link+'.'+a_LCS+'.')
        success = self.onApply()
        return


    # Rotations
    def rotAxis( self, addRotation ):
        self.selectedDatum.AttachmentOffset = self.selectedDatum.AttachmentOffset.multiply(addRotation) 
        self.selectedDatum.recompute()

    def onRotX(self):
        self.rotAxis(Asm4.rotX)

    def onRotY(self):
        self.rotAxis(Asm4.rotY)

    def onRotZ(self):
        self.rotAxis(Asm4.rotZ)

    """
        +-----------------------------------------------+
        |           split the ExpressionEngine          |
        |        of a linked Datum object to find       |
        |         the old attachment Part and LCS       |
        +-----------------------------------------------+
    """
    def splitExpressionDatum( self, expr ):
        retval = ( expr, 'None', 'None' )
        # expr is empty
        if not expr:
            return retval
        restFinal = ''
        attLink = ''
        if expr:
            # Look for a # to see whether the linked part is in the same document
            # expr = Link.Placement * LinkedPart#LCS.Placement * AttachmentOffset
            # expr = Link.Placement * LCS.Placement * AttachmentOffset
            if '#' in expr:
                # the linked part is in another document
                # expr = Link.Placement * LinkedPart#LCS.Placement * AttachmentOffset
                ( attLink, separator, rest1 ) = expr.partition('.Placement * ')
                ( attPart, separator, rest2 ) = rest1.partition('#')
                ( attLCS,  separator, rest3 ) = rest2.partition('.Placement * ')
                restFinal = rest3[0:16]
            else:
                # the linked part is in the same document
                # expr = Link.Placement * LCS.Placement * AttachmentOffset
                ( attLink, separator, rest1 ) =  expr.partition('.Placement * ')
                ( attLCS,  separator, rest2 ) = rest1.partition('.Placement * ')
                restFinal = rest2[0:16]
                attPart = 'unimportant'
            if restFinal=='AttachmentOffset':
                # wow, everything went according to plan
                retval = ( attLink, attPart, attLCS )
                #self.expression.setText( attPart +'***'+ attLCS )
            else:
                # rats ! But still, if the decode is unsuccessful, put some text
                retval = ( restFinal, 'None', 'None' )
        return retval



    """
        +-----------------------------------------------+
        |                    the UI                     |
        +-----------------------------------------------+
    """
    # Initialises the UI once the widget has started
    def initUI(self):
        self.lscName.setText( Asm4.nameLabel(self.selectedDatum) )
        self.parentDoc.clear()
        self.attLCSlist.clear()
        # list and table containing the available parents in the assembly to choose from
        self.parentList.clear()
        self.parentTable = []
        self.parentList.addItem( 'Please select' )
        self.parentTable.append( [] )


    # defines the UI, only static elements
    def drawUI(self):
        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self.form)
        
        # Selected Datum
        self.mainLayout.addWidget(QtGui.QLabel('Selected Datum :'))
        self.lscName = QtGui.QLineEdit()
        self.lscName.setReadOnly(True)
        self.mainLayout.addWidget(self.lscName)

        # combobox showing all available App::Link
        self.mainLayout.addWidget(QtGui.QLabel('Attach to :'))
        self.parentList = QtGui.QComboBox()
        self.mainLayout.addWidget(self.parentList)
        # the document containing the linked object
        self.parentDoc = QtGui.QLineEdit()
        self.parentDoc.setReadOnly(True)
        self.mainLayout.addWidget(self.parentDoc)

        # The list of all attachment LCS in the assembly is a QListWidget
        # it is populated only when the parent combo-box is activated
        self.mainLayout.addWidget(QtGui.QLabel('Select LCS in Parent :'))
        self.attLCSlist = QtGui.QListWidget()
        self.mainLayout.addWidget(self.attLCSlist)

        # Rot Buttons
        self.rotButtonsLayout = QtGui.QHBoxLayout()
        # RotX button
        self.RotXButton = QtGui.QPushButton('Rot X')
        self.RotXButton.setToolTip("Rotate the Datum around the X axis by 90deg")
        # RotY button
        self.RotYButton = QtGui.QPushButton('Rot Y')
        self.RotYButton.setToolTip("Rotate the Datum around the Y axis by 90deg")
        # RotZ button
        self.RotZButton = QtGui.QPushButton('Rot Z')
        self.RotZButton.setToolTip("Rotate the Datum around the Z axis by 90deg")
        # add the buttons
        self.rotButtonsLayout.addStretch()
        self.rotButtonsLayout.addWidget(self.RotXButton)
        self.rotButtonsLayout.addWidget(self.RotYButton)
        self.rotButtonsLayout.addWidget(self.RotZButton)
        self.rotButtonsLayout.addStretch()
        self.mainLayout.addLayout(self.rotButtonsLayout)

        # apply the layout to the main window
        self.form.setLayout(self.mainLayout)

        # Actions
        self.parentList.currentIndexChanged.connect( self.onParentSelected )
        self.attLCSlist.currentItemChanged.connect( self.onDatumSelected )
        self.attLCSlist.itemClicked.connect( self.onDatumSelected )
        self.RotXButton.clicked.connect( self.onRotX )
        self.RotYButton.clicked.connect( self.onRotY )
        self.RotZButton.clicked.connect( self.onRotZ)




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_placeDatum', placeDatumCmd() )

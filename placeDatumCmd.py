#!/usr/bin/env python3
# coding: utf-8
#
# placeDatumCmd.py

import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import libAsm4 as Asm4



"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class placeDatum( QtGui.QDialog ):
    "My tool object"


    def __init__(self):
        super(placeDatum,self).__init__()
        self.drawUI()


    def GetResources(self):
        return {"MenuText": "Edit Attachment of a Datum object",
                "ToolTip": "Attach a Datum object in the assembly to a Datum in a linked Part",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Place_Datum.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if App.ActiveDocument:
            # is something selected ?
            selObj = self.checkSelectionDatum()
            if selObj != None:
                return True
        return False 


    def checkSelectionDatum(self):
        selectedObj = None
        # check that there is an App::Part called 'Model'
        # a standard App::Part would also do, but then more error checks are necessary
        if App.ActiveDocument.getObject('Model') and App.ActiveDocument.getObject('Model').TypeId=='App::Part' :
        # check that something is selected
            if Gui.Selection.getSelection():
            # set the (first) selected object as global variable
                selection = Gui.Selection.getSelection()[0]
                selectedType = selection.TypeId
                # check that the selected object is a Datum CS or Point type
                if selectedType=='PartDesign::CoordinateSystem' or selectedType=='PartDesign::Plane' or selectedType=='PartDesign::Line' or selectedType=='PartDesign::Point' :
                    selectedObj = selection
        # now we should be safe
        return selectedObj
    


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
        self.selectedDatum = []
        selection = self.checkSelectionDatum()
        if not selection:
            self.close()
        else:
            self.selectedDatum = selection

        # check if the datum object is already mapped to something
        if self.selectedDatum.MapMode != 'Deactivated':
            message = 'This datum object \"'+self.selectedDatum.Label+'\" is mapped to some geometry. Attaching-it with Assembly4 will loose this mapping.'
            if Asm4.confirmBox(message):
                # unset MappingMode
                self.selectedDatum.MapMode = 'Deactivated'
            else:
                # don't do anything and ...
                return

        # Now we can draw the UI
        self.initUI()
        # now self.parentList and self.parentTable are available

        # find all the linked parts in the assembly
        """
        for obj in self.activeDoc.findObjects("App::Link"):
            if obj.LinkedObject.isDerivedFrom('App::Part'):
                # add it to our tree table if it's a link to an App::Part ...
                self.parentTable.append( obj )
                # ... and add to the drop-down combo box with the assembly tree's parts
                objIcon = obj.LinkedObject.ViewObject.Icon
                self.parentList.addItem( objIcon, obj.Name, obj)
        """
        for objName in self.parentAssembly.getSubObjects():
            # remove the trailing .
            obj = self.activeDoc.getObject(objName[0:-1])
            if obj.TypeId=='App::Link':
                # add it to our list if it's a link to an App::Part ...
                if hasattr(obj.LinkedObject,'isDerivedFrom') and obj.LinkedObject.isDerivedFrom('App::Part'):
                    self.parentTable.append( obj )
                    # add to the drop-down combo box with the assembly tree's parts
                    objIcon = obj.LinkedObject.ViewObject.Icon
                    objText = obj.Label
                    if obj.Name != obj.Label:
                        objText += ' ('+obj.Name+')'
                    self.parentList.addItem( objIcon, objText, obj)

        # get and store the current expression engine:
        self.old_EE = ''
        old_EE = self.selectedDatum.ExpressionEngine
        if old_EE:
            ( pla, self.old_EE ) = old_EE[0]

        # decode the old ExpressionEngine
        # if the decode is unsuccessful, old_Expression is set to False
        # and old_attPart and old_attLCS are set to 'None'
        old_Parent = ''
        old_ParentPart = ''
        old_attLCS = ''
        ( old_Parent, old_ParentPart, old_attLCS ) = Asm4.splitExpressionDatum( self.old_EE )
        #self.expression.setText( 'old_Parent = '+ old_Parent )


        # find the oldPart in the current part list...
        """
        oldPart = self.parentList.findText( old_Parent )
        # if not found
        if oldPart == -1:
            # set to initial "Select linked Part" entry
            self.parentList.setCurrentIndex( 0 )
        else:
            self.parentList.setCurrentIndex( oldPart )
        """
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
        lcs_found = []
        lcs_found = self.attLCSlist.findItems( old_attLCS, QtCore.Qt.MatchExactly )
        if lcs_found:
            # ... and select it
            self.attLCSlist.setCurrentItem( lcs_found[0] )
        else:
            # may-be it was renamed, see if we can find it as (name)
            lcs_found = self.attLCSlist.findItems( '('+old_attLCS+')', QtCore.Qt.MatchContains )
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
        if not a_Part :
            self.expression.setText( 'Problem in selections (no a_Part)' )
        elif not a_LCS :
            self.expression.setText( 'Problem in selections (no a_LCS)' )
        else:
            # don't forget the last '.' !!!
            # <<LinkName>>.Placement.multiply( <<LinkName>>.<<LCS.>>.Placement )
            # expr = '<<'+ a_Part +'>>.Placement.multiply( <<'+ a_Part +'>>.<<'+ a_LCS +'.>>.Placement )'
            expr = Asm4.makeExpressionDatum( a_Link, a_Part, a_LCS )
            # this can be skipped when this method becomes stable
            self.expression.setText( expr )
            # load the built expression into the Expression field of the constraint
            self.activeDoc.getObject( self.selectedDatum.Name ).setExpression( 'Placement', expr )
            # recompute the object to apply the placement:
            self.selectedDatum.ViewObject.ShowLabel = True
            self.selectedDatum.ViewObject.FontSize = 20
            self.selectedDatum.recompute()
            # highlight the selected LCS in its new position
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedDatum.Name +'.')
        return




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
    def onParentSelected(self):
        # clear the LCS list
        self.attLCSlist.clear()
        self.attLCStable = []
        # clear the selection in the GUI window
        Gui.Selection.clearSelection()
        # the current selection in the combo-box list gives the index 
        # of the currently selected link, whoose name is in the table
        #parentName = self.parentList.currentText()
        #parentLink = self.activeDoc.getObject( parentName )
        # if something is selected
        if self.parentList.currentIndex() > 0:
            parentName = self.parentTable[ self.parentList.currentIndex() ].Name
            parentLink = self.activeDoc.getObject( parentName )
            if parentLink:
                # we get the LCS from the linked part
                self.attLCStable = self.getPartLCS( parentLink.LinkedObject )
                # linked part & doc
                dText = ''
                if parentLink.LinkedObject.Document != self.activeDoc :
                    dText = parentLink.LinkedObject.Document.Name +'#'
                # if the linked part has been renamed by the user, keep the label and add (.Name)
                pText = parentLink.LinkedObject.Label
                if parentLink.LinkedObject.Name != parentLink.LinkedObject.Label:
                    pText = pText+' ('+parentLink.LinkedObject.Name+')'
                self.parentDoc.setText( dText + pText )
                # highlight the selected part:
                Gui.Selection.addSelection( parentLink.Document.Name, 'Model', parentLink.Name+'.' )
        # something wrong
        else:
            return
        """
        if parentLink:
            # we get the LCS from the linked part
            self.attLCStable = self.getPartLCS( parentLink.LinkedObject )
            self.parentDoc.setText( parentLink.LinkedObject.Document.Name )
            # highlight the selected part:
            Gui.Selection.addSelection( parentLink.Document.Name, 'Model', parentLink.Name+'.' )
        """
        # build the list
        for lcs in self.attLCStable:
            newItem = QtGui.QListWidgetItem()
            # if the LCS has been renamed, we show both the label and the (name)
            if lcs.Name == lcs.Label:
                newItem.setText( lcs.Name )
            else:
                newItem.setText( lcs.Label + ' (' +lcs.Name+ ')' )
            newItem.setIcon( lcs.ViewObject.Icon )
            self.attLCSlist.addItem( newItem )
        self.onApply()
        return



    """
    +-----------------------------------------------+
    |  A target Datum has been clicked in the list  |
    +-----------------------------------------------+
    """
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
        self.onApply()
        return



    """
    +-----------------------------------------------+
    |                  Rotations                    |
    +-----------------------------------------------+
    """
    def rotAxis( self, addRotation ):
        self.selectedDatum.AttachmentOffset = addRotation.multiply( self.selectedDatum.AttachmentOffset )
        self.selectedDatum.recompute()

    def onRotX(self):
        self.rotAxis(Asm4.rotX)

    def onRotY(self):
        self.rotAxis(Asm4.rotY)

    def onRotZ(self):
        self.rotAxis(Asm4.rotZ)


    """
    +-----------------------------------------------+
    |                     Cancel                    |
    |           restores the previous values        |
    +-----------------------------------------------+
    """
    def onCancel(self):
        # restore previous expression if it existed
        if self.old_EE:
            self.selectedDatum.setExpression('Placement', self.old_EE )
        self.selectedDatum.ViewObject.ShowLabel = False
        self.selectedDatum.recompute()
        # highlight the selected LCS in its new position
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedDatum.Name +'.')
        self.close()



    """
    +-----------------------------------------------+
    |                      OK                       |
    |               accept and close                |
    +-----------------------------------------------+
    """
    def onOK(self):
        self.onApply()
        self.selectedDatum.ViewObject.ShowLabel = False
        self.close()




    """
    +-----------------------------------------------+
    | nitialises the UI once the widget has stared  |
    +-----------------------------------------------+
    """
    def initUI(self):
        self.lscName.setText( self.selectedDatum.Name )
        self.parentDoc.clear()
        self.attLCSlist.clear()
        self.expression.clear()
        self.show()
        # list and table containing the available parents in the assembly to choose from
        self.parentList.clear()
        self.parentList.addItem( 'Please choose' )
        self.parentTable = []
        self.parentTable.append( [] )


    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        self.setWindowTitle('Attach a Coordinate System')
        self.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.setMinimumSize(370, 570)
        self.setModal(False)

        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self)

        # Selected Datum
        self.formLayout = QtGui.QFormLayout(self)
        self.lscName = QtGui.QLineEdit(self)
        self.lscName.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Selected Datum :'),self.lscName)
        self.mainLayout.addLayout(self.formLayout)

        # combobox showing all available App::Link
        self.mainLayout.addWidget(QtGui.QLabel('Selected Parent :'))
        self.parentList = QtGui.QComboBox(self)
        self.mainLayout.addWidget(self.parentList)

        # the document containing the linked object
        self.mainLayout.addWidget(QtGui.QLabel('Parent Part (Doc#Part) :'))
        self.parentDoc = QtGui.QLineEdit(self)
        self.parentDoc.setReadOnly(True)
        self.mainLayout.addWidget(self.parentDoc)


        # The list of all attachment LCS in the assembly is a QListWidget
        # it is populated only when the parent combo-box is activated
        self.mainLayout.addWidget(QtGui.QLabel('Select LCS in Parent :'))
        self.attLCSlist = QtGui.QListWidget(self)
        self.mainLayout.addWidget(self.attLCSlist)

        # Expression
        # Create a line that will contain full expression for the expression engine
        self.mainLayout.addWidget(QtGui.QLabel('Expression Engine :'))
        self.expression = QtGui.QLineEdit(self)
        self.mainLayout.addWidget(self.expression)


        # Rot Buttons
        self.rotButtonsLayout = QtGui.QHBoxLayout(self)
        # RotX button
        self.RotXButton = QtGui.QPushButton('Rot X', self)
        self.RotXButton.setToolTip("Rotate the Datum around the X axis by 90deg")
        # RotY button
        self.RotYButton = QtGui.QPushButton('Rot Y', self)
        self.RotYButton.setToolTip("Rotate the Datum around the Y axis by 90deg")
        # RotZ button
        self.RotZButton = QtGui.QPushButton('Rot Z', self)
        self.RotZButton.setToolTip("Rotate the Datum around the Z axis by 90deg")
        # add the buttons
        self.rotButtonsLayout.addStretch()
        self.rotButtonsLayout.addWidget(self.RotXButton)
        self.rotButtonsLayout.addWidget(self.RotYButton)
        self.rotButtonsLayout.addWidget(self.RotZButton)
        self.rotButtonsLayout.addStretch()
        self.mainLayout.addLayout(self.rotButtonsLayout)

        # OK Buttons
        self.OkButtonsLayout = QtGui.QHBoxLayout(self)
        #
        # Cancel button
        self.CancelButton = QtGui.QPushButton('Cancel', self)
        self.CancelButton.setToolTip("Restore initial parameters and close dialog")
        # OK button
        self.OkButton = QtGui.QPushButton('OK', self)
        self.OkButton.setToolTip("Apply current parameters and close dialog")
        self.OkButton.setDefault(True)
        # position the buttons
        self.OkButtonsLayout.addWidget(self.CancelButton)
        self.OkButtonsLayout.addStretch()
        self.OkButtonsLayout.addWidget(self.OkButton)
        self.mainLayout.addWidget(QtGui.QLabel(' '))
        self.mainLayout.addLayout(self.OkButtonsLayout)

        # Actions
        self.parentList.currentIndexChanged.connect( self.onParentSelected )
        self.attLCSlist.currentItemChanged.connect( self.onDatumSelected )
        self.attLCSlist.itemClicked.connect( self.onDatumSelected )
        self.CancelButton.clicked.connect(self.onCancel)
        self.OkButton.clicked.connect(self.onOK)
        self.RotXButton.clicked.connect( self.onRotX )
        self.RotYButton.clicked.connect( self.onRotY )
        self.RotZButton.clicked.connect( self.onRotZ)

        # apply the layout to the main window
        self.setLayout(self.mainLayout)



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_placeDatum', placeDatum() )

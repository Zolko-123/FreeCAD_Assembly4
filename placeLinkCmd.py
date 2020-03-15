#!/usr/bin/env python3
# coding: utf-8
#
# placeLinkCmd.py


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
class placeLink( QtGui.QDialog ):
    "My tool object"


    def __init__(self):
        super(placeLink,self).__init__()
        # draw the GUI, objects are defined later down
        self.drawUI()



    def GetResources(self):
        return {"MenuText": "Edit Placement of a Part",
                "ToolTip": "Move/Attach a Part in the assembly",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Place_Link.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if App.ActiveDocument:
            # is something selected ?
            selObj = self.GetSelection()
            if selObj != None:
                return True
        return False


    def GetSelection(self):
        # check that there is an App::Part called 'Model'
        selectedObj = None
        if not App.ActiveDocument.getObject('Model'):
            return None
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
        # get the current active document to avoid errors if user changes tab
        self.activeDoc = App.activeDocument()
        # the parent (top-level) assembly is the App::Part called Model (hard-coded)
        self.parentAssembly = self.activeDoc.Model

        self.attLCStable = []

        # check that we have selected an App::Link object
        self.selectedLink = []
        selection = self.GetSelection()
        if not selection:
            self.close()
        else:
            self.selectedLink = selection

        # check that the link is an Asm4 link:
        self.isAsm4EE = False
        if hasattr(self.selectedLink,'AssemblyType'):
            if self.selectedLink.AssemblyType == 'Asm4EE' or self.selectedLink.AssemblyType == '' :
                self.isAsm4EE = True
            else:
                Asm4.warningBox("This Link's assembly type doesn't correspond to this WorkBench")
                return

        # initialize the UI with the current data
        self.initUI()
        # now self.parentList and self.parentTable are available

        # find all the linked parts in the assembly
        # for obj in self.activeDoc.findObjects("App::Link"):
        for objName in self.parentAssembly.getSubObjects():
            # remove the trailing .
            obj = self.activeDoc.getObject(objName[0:-1])
            if obj.TypeId=='App::Link':
                # add it to our list if it's a link to an App::Part ...
                if hasattr(obj.LinkedObject,'isDerivedFrom') and obj.LinkedObject.isDerivedFrom('App::Part'):
                    # ... except if it's the selected link itself
                    if obj != self.selectedLink:
                        self.parentTable.append( obj )
                        # add to the drop-down combo box with the assembly tree's parts
                        objIcon = obj.LinkedObject.ViewObject.Icon
                        objText = Asm4.nameLabel(obj)
                        self.parentList.addItem( objIcon, objText, obj)


        # find all the LCS in the selected link
        self.partLCStable = self.getPartLCS( self.selectedLink.LinkedObject )
        # build the list
        self.partLCSlist.clear()
        for lcs in self.partLCStable:
            newItem = QtGui.QListWidgetItem()
            newItem.setText(Asm4.nameLabel(lcs))
            newItem.setIcon( lcs.ViewObject.Icon )
            self.partLCSlist.addItem(newItem)


        # get the old values
        if self.isAsm4EE:
            self.old_AO = self.selectedLink.AttachmentOffset
            self.old_linkLCS = self.selectedLink.AttachedBy[1:]
            (self.old_Parent, separator, self.old_parentLCS) = self.selectedLink.AttachedTo.partition('#')
        else:
            self.old_AO = []
            self.old_Parent = ''


        self.old_EE = ''
        # get and store the current expression engine:
        self.old_EE = Asm4.placementEE(self.selectedLink.ExpressionEngine)
        # for debugging, use this field to print text
        #self.expression.setText( self.old_EE )

        # decode the old ExpressionEngine
        old_Parent = ''
        old_ParentPart = ''
        old_attLCS = ''
        constrName = ''
        linkedDoc = ''
        old_linkLCS = ''
        # if the decode is unsuccessful, old_Expression is set to False and the other things are set to 'None'
        ( old_Parent, old_attLCS, old_linkLCS ) = Asm4.splitExpressionLink( self.old_EE, self.old_Parent )
        #self.expression.setText( old_Parent +'***'+ self.old_Parent )


        # find the old LCS in the list of LCS of the linked part...
        # MatchExactly, MatchContains, MatchEndsWith ...
        lcs_found = self.partLCSlist.findItems( old_linkLCS, QtCore.Qt.MatchExactly )
        if not lcs_found:
            lcs_found = self.partLCSlist.findItems( old_linkLCS+' (', QtCore.Qt.MatchStartsWith )
        if lcs_found:
            # ... and select it
            self.partLCSlist.setCurrentItem( lcs_found[0] )


        # find the oldPart in the part list...
        if old_Parent == 'Parent Assembly':
            parent_found = True
            parent_index = 1
        else:
            parent_found = False
            parent_index = 1
            for item in self.parentTable[1:]:
                if item.Name == old_Parent:
                    parent_found = True
                    break
                else:
                    parent_index = parent_index +1
        if not parent_found:
            parent_index = 0
        self.parentList.setCurrentIndex( parent_index )
        # this should have triggered self.getPartLCS() to fill the LCS list

        # find the old attachment Datum in the list of the Datums in the linked part...
        lcs_found = self.attLCSlist.findItems( old_attLCS, QtCore.Qt.MatchExactly )
        if not lcs_found:
            lcs_found = self.attLCSlist.findItems( old_attLCS+' (', QtCore.Qt.MatchStartsWith )
        if lcs_found:
            # ... and select it
            self.attLCSlist.setCurrentItem( lcs_found[0] )



        # the widget is shown and not executed to allow it to stay on top
        self.show()



    """
    +-----------------------------------------------+
    | check that all necessary things are selected, |
    |   populate the expression with the selected   |
    |    elements, put them into the constraint     |
    |   and trigger the recomputation of the part   |
    +-----------------------------------------------+
    """
    def Apply( self ):
        # get the instance to attach to:
        # it's either the top level assembly or a sister App::Link
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

        # the linked App::Part's name
        l_Part = self.selectedLink.LinkedObject.Document.Name

        # the LCS's name in the linked part to be used for its attachment
        # check that something is selected in the QlistWidget
        if self.partLCSlist.selectedItems():
            #l_LCS = self.partLCSlist.selectedItems()[0].text()
            l_LCS = self.partLCStable[ self.partLCSlist.currentRow() ].Name
        else:
            l_LCS = None
        #self.expression.setText( '***'+ l_LCS +'***' )

        # check that all of them have something in
        # constrName has been checked at the beginning
        if not ( a_Link and a_LCS and l_Part and l_LCS ):
            self.expression.setText( 'Problem in selections' )
        else:
            # this is where all the magic is, see:
            # 
            # https://forum.freecadweb.org/viewtopic.php?p=278124#p278124
            #
            # as of FreeCAD v0.19 the syntax is different:
            # https://forum.freecadweb.org/viewtopic.php?f=17&t=38974&p=337784#p337784
            #
            # expr = ParentLink.Placement * ParentPart#LCS.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
            # expr = LCS_in_the_assembly.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
            expr = Asm4.makeExpressionPart( a_Link, a_Part, a_LCS, l_Part, l_LCS )
            # this can be skipped when this method becomes stable
            self.expression.setText( expr )
            # add the Asm4 properties if it's a pure App::Link
            Asm4.makeAsmProperties(self.selectedLink)
            # store the part where we're attached to in the constraints object
            self.selectedLink.AssemblyType = 'Asm4EE'
            self.selectedLink.AttachedBy = '#'+l_LCS
            self.selectedLink.AttachedTo = a_Link+'#'+a_LCS
            # load the expression into the link's Expression Engine
            self.selectedLink.setExpression('Placement', expr )
            # recompute the object to apply the placement:
            self.selectedLink.recompute()
            self.parentAssembly.recompute(True)
        return


    """
    +-----------------------------------------------+
    |    insert instance free of any attachment     |
    +-----------------------------------------------+
    """
    def freeInsert(self):
        # ask for confirmation before resetting everything
        linkName  = self.selectedLink.Name
        linkLabel = self.selectedLink.Label
        if linkName==linkName:
            linkText = linkName
        else:
            linkText = linkName+' ('+linkName+')'
        # see whether the ExpressionEngine field is filled
        if self.selectedLink.ExpressionEngine :
            # if yes, then ask for confirmation
            confirmed = Asm4.confirmBox('This command will release all attachments on '+linkText+' and set it to manual positioning in its current location.')
            # if not, then it's useless to bother the user
        else:
            confirmed = True
        if confirmed:
            # unset the ExpressionEngine for the Placement
            self.selectedLink.setExpression('Placement', None)
            # reset the assembly properties
            Asm4.makeAsmProperties( self.selectedLink, reset=True )
            """
            # property AssemblyType
            if hasattr(self.selectedLink,'AssemblyType'):
                self.selectedLink.AssemblyType = ''
            else:
                self.selectedLink.addProperty( 'App::PropertyString', 'AssemblyType', 'Attachment' ).AssemblyType = ''
            # property AttachedBy
            if hasattr(self.selectedLink,'AttachedBy'):
                self.selectedLink.AttachedBy = ''
            else:
                self.selectedLink.addProperty( 'App::PropertyString', 'AttachedBy', 'Attachment' ).AttachedBy = ''
            # property AttachedTo
            if hasattr(self.selectedLink,'AttachedTo'):
                self.selectedLink.AttachedTo = ''
            else:
                self.selectedLink.addProperty( 'App::PropertyString', 'AttachedTo', 'Attachment' ).AttachedTo = ''
            # property AttachmentOffset
            if hasattr(self.selectedLink,'AttachmentOffset'):
                self.selectedLink.AttachmentOffset = App.Placement()
            else:
                self.selectedLink.addProperty( 'App::PropertyPlacement', 'AttachmentOffset', 'Attachment' ).AttachmentOffset = App.Placement()
            """
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedLink.Name+'.' )
            # finish
            self.close()
        else:
            return




    """
    +-----------------------------------------------+
    |   find all the linked parts in the assembly   |
    +-----------------------------------------------+
    """
    def getAllLinkedParts(self):
        allLinkedParts = []
        for obj in self.activeDoc.findObjects("App::Link"):
            # add it to our list if it's a link to an App::Part ...
            if obj.LinkedObject.isDerivedFrom('App::Part'):
                # ... except if it's the selected link itself, because
                # we don't want to place the new link relative to itself !
                if obj != self.selectedLink:
                    allLinkedParts.append( obj )
        return allLinkedParts



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
            if obj.TypeId == 'PartDesign::CoordinateSystem':
                partLCS.append( obj )
        return partLCS



    """
    +------------------------------------------------+
    |   fill the LCS list when changing the parent   |
    +------------------------------------------------+
    """
    def onParentSelected(self):
        # clear the selection in the GUI window
        Gui.Selection.clearSelection()
        # build the LCS table
        self.attLCStable = []
        # the current text in the combo-box is the link's name...
        # ... or it's 'Parent Assembly' then the parent is the 'Model' root App::Part
        if self.parentList.currentText() == 'Parent Assembly':
            parentName = 'Parent Assembly'
            parentPart = self.parentAssembly
            # we get the LCS directly in the root App::Part 'Model'
            self.attLCStable = self.getPartLCS( parentPart )
            self.parentDoc.setText( parentPart.Document.Name+'#'+Asm4.nameLabel(parentPart) )
        # if something is selected
        elif self.parentList.currentIndex() > 1:
            parentName = self.parentTable[ self.parentList.currentIndex() ].Name
            parentPart = self.activeDoc.getObject( parentName )
            if parentPart:
                # we get the LCS from the linked part
                self.attLCStable = self.getPartLCS( parentPart.LinkedObject )
                # linked part & doc
                dText = ''
                if parentPart.LinkedObject.Document != self.activeDoc :
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






    """
    +-----------------------------------------------+
    |                  Rotations                    |
    +-----------------------------------------------+
    """
    def rotAxis( self, plaRotAxis ):
        constrAO = self.selectedLink.AttachmentOffset
        self.selectedLink.AttachmentOffset = plaRotAxis.multiply( constrAO )
        self.selectedLink.recompute()

    def onRotX(self):
        self.rotAxis(Asm4.rotX)

    def onRotY(self):
        self.rotAxis(Asm4.rotY)

    def onRotZ(self):
        self.rotAxis(Asm4.rotZ)

    def onReset( self ):
        newPlacement = App.Placement( App.Vector(0,0,0), App.Rotation( App.Vector(0,0,1), 0.0 ) )
        self.selectedLink.AttachmentOffset = newPlacement
        self.selectedLink.recompute()



    """
    +-----------------------------------------------+
    |                      OK                       |
    |               accept and close                |
    +-----------------------------------------------+
    """
    def onOK(self):
        self.Apply()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedLink.Name+'.' )
        self.close()


    def onCancel(self):
        # restore previous values
        if self.old_AO:
            self.selectedLink.AttachmentOffset = self.old_AO
        if self.old_EE:
            self.selectedLink.setExpression( 'Placement', self.old_EE )
        self.selectedLink.recompute()
        Gui.Selection.clearSelection()
        self.close()


    """
    +-----------------------------------------------+
    |     initialize the UI for the selected link   |
    +-----------------------------------------------+
    """
    def initUI(self):
        # clear the parent name (if any)
        self.parentDoc.clear()
        self.expression.clear()
        self.partLCSlist.clear()
        self.attLCSlist.clear()
        # the selected link's name 
        self.linkName.setText( Asm4.nameLabel(self.selectedLink) )
        # linked part & doc
        dText = ''
        if self.selectedLink.LinkedObject.Document != self.activeDoc :
            dText = self.selectedLink.LinkedObject.Document.Name +'#'
        # if the linked part has been renamed by the user, keep the label and add (.Name)
        pText = Asm4.nameLabel(self.selectedLink.LinkedObject)
        self.linkedDoc.setText( dText + pText )
        # Initialize the assembly tree with the Parrent Assembly as first element
        # clear the available parents combo box
        self.parentList.clear()
        self.parentList.addItem('Please choose')
        parentIcon = self.parentAssembly.ViewObject.Icon
        self.parentList.addItem( parentIcon, 'Parent Assembly', self.parentAssembly )
        # all the parts in the assembly
        self.parentTable = []
        self.parentTable.append( [] )
        self.parentTable.append( self.parentAssembly )



    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        self.setWindowTitle('Place linked Part')
        self.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumSize(550, 640)
        self.resize(550,640)
        self.setModal(False)
        # make this dialog stay above the others, always visible
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self)
        # with 2 columns
        self.columnsLayout = QtGui.QHBoxLayout(self)
        self.leftLayout = QtGui.QVBoxLayout(self)
        self.rightLayout = QtGui.QVBoxLayout(self)
        
        # Part, left side
        #
        # Selected Link (the name as seen in the tree of the selected link)
        self.leftLayout.addWidget(QtGui.QLabel("Selected Link :"))
        self.linkName = QtGui.QLineEdit(self)
        self.linkName.setReadOnly(True)
        self.linkName.setMinimumSize(200, 1)
        self.leftLayout.addWidget(self.linkName)

        # the document containing the linked part
        # if the linked part is in the same document as the assembly Model
        self.leftLayout.addWidget(QtGui.QLabel("Linked Part :"))
        self.linkedDoc = QtGui.QLineEdit(self)
        self.linkedDoc.setReadOnly(True)
        self.linkedDoc.setMinimumSize(200, 1)
        self.leftLayout.addWidget(self.linkedDoc)

        # The list of all LCS in the part is a QListWidget
        self.leftLayout.addWidget(QtGui.QLabel("Select LCS in Part :"))
        self.partLCSlist = QtGui.QListWidget(self)
        self.partLCSlist.setMinimumSize(100, 250)
        self.partLCSlist.setToolTip('Select a coordinate system from the list')
        self.leftLayout.addWidget(self.partLCSlist)

        # Assembly, Right side
        #
        # combobox showing all available App::Link
        self.rightLayout.addWidget(QtGui.QLabel("Select Parent to attach to :"))
        self.parentList = QtGui.QComboBox(self)
        self.parentList.setMinimumSize(250, 10)
        self.parentList.setToolTip('Choose the part in which the attachment\ncoordinate system is to be found')
        # the parent assembly is hardcoded, and made the first real element
        self.rightLayout.addWidget(self.parentList)

        # the document containing the linked object
        self.rightLayout.addWidget(QtGui.QLabel("Parent Part :"))
        self.parentDoc = QtGui.QLineEdit(self)
        self.parentDoc.setReadOnly(True)
        self.parentDoc.setMinimumSize(200, 1)
        self.rightLayout.addWidget(self.parentDoc)
        # The list of all attachment LCS in the assembly is a QListWidget
        # it is populated only when the parent combo-box is activated
        self.rightLayout.addWidget(QtGui.QLabel("Select LCS in Parent :"))
        self.attLCSlist = QtGui.QListWidget(self)
        self.attLCSlist.setMinimumSize(250, 250)
        self.attLCSlist.setToolTip('Select a coordinate system from the list')
        self.rightLayout.addWidget(self.attLCSlist)

        # add the 2 columns
        self.columnsLayout.addLayout(self.leftLayout)
        self.columnsLayout.addLayout(self.rightLayout)
        self.mainLayout.addLayout(self.columnsLayout)

        # Create a line that will contain full expression for the expression engine
        self.expression = QtGui.QLineEdit(self)
        self.expression.setMinimumSize(530, 0)
        self.mainLayout.addWidget(QtGui.QLabel("Expression Engine :"))
        self.mainLayout.addWidget(self.expression)

        # Rot Buttons
        self.rotButtonsLayout = QtGui.QHBoxLayout(self)
        #
        # Reset button
        # self.ResetButton = QtGui.QPushButton('Reset', self)
        # self.ResetButton.setToolTip("Reset the AttachmentOffset of this Link")
        # RotX button
        self.RotXButton = QtGui.QPushButton('Rot X', self)
        self.RotXButton.setToolTip("Rotate the instance around the X axis by 90deg")
        # RotY button
        self.RotYButton = QtGui.QPushButton('Rot Y', self)
        self.RotYButton.setToolTip("Rotate the instance around the Y axis by 90deg")
        # RotZ button
        self.RotZButton = QtGui.QPushButton('Rot Z', self)
        self.RotZButton.setToolTip("Rotate the instance around the Z axis by 90deg")
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
        # Free Insert button
        self.FreeButton = QtGui.QPushButton('Free Insert', self)
        self.FreeButton.setToolTip("Insert the linked part into the assembly with manual placement. \nTo move the part right-click on its name and select \"Transform\"")
        # OK button
        self.OkButton = QtGui.QPushButton('OK', self)
        self.OkButton.setToolTip("Apply current parameters and close dialog")
        self.OkButton.setDefault(True)
        # position the buttons
        self.OkButtonsLayout.addWidget(self.CancelButton)
        self.OkButtonsLayout.addStretch()
        self.OkButtonsLayout.addWidget(self.FreeButton)
        self.OkButtonsLayout.addStretch()
        self.OkButtonsLayout.addWidget(self.OkButton)
        self.mainLayout.addWidget(QtGui.QLabel(' '))
        self.mainLayout.addLayout(self.OkButtonsLayout)

        # Actions
        self.parentList.currentIndexChanged.connect( self.onParentSelected )
        self.attLCSlist.itemClicked.connect( self.Apply )
        #self.attLCSlist.currentItemChanged.connect( self.Apply )
        self.partLCSlist.itemClicked.connect( self.Apply )
        #self.partLCSlist.currentItemChanged.connect( self.Apply )
        #self.ResetButton.clicked.connect( self.onReset )
        self.RotXButton.clicked.connect( self.onRotX )
        self.RotYButton.clicked.connect( self.onRotY )
        self.RotZButton.clicked.connect( self.onRotZ)
        self.CancelButton.clicked.connect(self.onCancel)
        self.FreeButton.clicked.connect(self.freeInsert)
        self.OkButton.clicked.connect(self.onOK)

        # apply the layout to the main window
        self.setLayout(self.mainLayout)


"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_placeLink', placeLink() )

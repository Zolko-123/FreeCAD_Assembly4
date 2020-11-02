#!/usr/bin/env python3
# coding: utf-8
#
# FastenersLib.py




import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC
from FastenerBase import FSBaseObject
import FastenersCmd as FS

import libAsm4 as Asm4




"""
    +-----------------------------------------------+
    |               Helper functions                |
    +-----------------------------------------------+
"""
def getSelectionFS():    
    selectedObj = None
    # check that something is selected
    if len(Gui.Selection.getSelection())==1:
        obj = Gui.Selection.getSelection()[0]
        if isFastener(obj):
            selectedObj = obj
        else:
            for selObj in Gui.Selection.getSelectionEx():
                obj = selObj.Object
                if isFastener(obj):
                    selectedObj = obj
    # now we should be safe
    return selectedObj


# icon to show in the Menu, toolbar and widget window
iconFile = os.path.join( Asm4.iconPath , 'Asm4_mvFastener.svg')



def isFastener( obj):
    if not obj:
        return False
    if (hasattr(obj,'Proxy') and isinstance(obj.Proxy, FSBaseObject)):
        return True
    return False
    
    


"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class placeFastenerCmd():

    def __init__(self):
        super(placeFastenerCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Edit Placement of a Fastener",
                "ToolTip": "Edit Placement of a Fastener",
                "Pixmap" : iconFile
                }

    def IsActive(self):
        if Asm4.checkModel() and getSelectionFS():
            return True
        return False

    def Activated(self):
        # check that we have selected a Fastener from the Fastener WB
        selection = getSelectionFS()
        if selection == None:
            return
        # check that the fastener is an Asm4 fastener
        if not hasattr(selection,'AssemblyType'):
            Asm4.makeAsmProperties(selection)
        # we only deal with Asm4 or empty types
        asmType = selection.AssemblyType
        if asmType=='Asm4EE' or asmType=='':
            # now we should be safe, call the UI
            Gui.Control.showDialog( placeFastenerUI() )
        else:
            convert = Asm4.confirmBox("This doesn't seem to be an Assembly4 Fastener")
            if convert:
                Asm4.makeAsmProperties( selection, reset=True )
                selection.AssemblyType = 'Asm4EE'
                Gui.Control.showDialog( placeFastenerUI() )
            return



"""
    +-----------------------------------------------+
    |    The UI and functions in the Task panel     |
    +-----------------------------------------------+
"""
class placeFastenerUI():
    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base        
        self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle('Attach a Fastener in the assembly')

        # get the current active document to avoid errors if user changes tab
        self.activeDoc = App.activeDocument()
        # the parent (top-level) assembly is the App::Part called Model (hard-coded)
        self.parentAssembly = self.activeDoc.Model
        # has been checked before calling
        self.selectedFastener = getSelectionFS()

        # Now we can draw the UI
        self.drawUI()
        self.initUI()
        # now self.parentList and self.parentTable are available

        # find all the linked parts in the assembly
        for objName in self.parentAssembly.getSubObjects():
            # remove the trailing .
            obj = self.activeDoc.getObject(objName[0:-1])
            if obj.TypeId=='App::Link' and hasattr(obj.LinkedObject,'isDerivedFrom'):
                linkedObj = obj.LinkedObject
                if linkedObj.isDerivedFrom('App::Part') or linkedObj.isDerivedFrom('PartDesign::Body'):
                    # add to the object table holding the objects ...
                    self.parentTable.append( obj )
                    # ... and add to the drop-down combo box with the assembly tree's parts
                    objIcon = obj.LinkedObject.ViewObject.Icon
                    objText = Asm4.nameLabel(obj)
                    self.parentList.addItem( objIcon, objText, obj)

        # check where the fastener was attached to
        (self.old_Parent, separator, self.old_parentLCS) = self.selectedFastener.AttachedTo.partition('#')
        # get and store the Placement's current ExpressionEngine:
        self.old_EE = Asm4.placementEE( self.selectedFastener.ExpressionEngine )

        # decode the old ExpressionEngine
        # if the decode is unsuccessful, old_Expression is set to False
        # and old_attPart and old_attLCS are set to 'None'
        old_Parent = ''
        old_parentPart = ''
        old_parentLCS = ''
        if  self.old_EE and self.old_Parent:
            ( old_Parent, old_parentPart, old_parentLCS ) = self.splitExpressionFastener( self.old_EE, self.old_Parent )

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
        if lcs_found:
            # ... and select it
            self.attLCSlist.setCurrentItem( lcs_found[0] )
        else:
            # may-be it was renamed, see if we can find it as (name)
            lcs_found = self.attLCSlist.findItems( '('+old_parentLCS+')', QtCore.Qt.MatchContains )
            if lcs_found:
                self.attLCSlist.setCurrentItem( lcs_found[0] )



    # this is the end ...
    def finish(self):
        Gui.Control.closeDialog()


    # standard FreeCAD Task panel buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel
                   | QtGui.QDialogButtonBox.Ok
                   | QtGui.QDialogButtonBox.Ignore)


    # Ignore = Free Insert
    def clicked(self, bt):
        if bt == QtGui.QDialogButtonBox.Ignore:
            # ask for confirmation before resetting everything
            msgName = Asm4.nameLabel(self.selectedFastener)
            # see whether the ExpressionEngine field is filled
            if self.old_EE :
                # if yes, then ask for confirmation
                confirmed = Asm4.confirmBox('This command will release all attachments on '+msgName+' and set it to manual positioning in its current location.')
            else:
                # if not, then it's useless to bother the user
                confirmed = True
            if confirmed:
                # unset the ExpressionEngine in the Placement
                self.selectedFastener.setExpression('Placement', None)
                # reset Asm4 properties
                Asm4.makeAsmProperties( self.selectedFastener, reset=True )
            self.finish()


    # OK
    def accept(self):
        self.onApply()
        self.finish()


    # Cancel
    def reject(self):
        # restore previous expression if it existed
        if self.old_EE != None:
            self.selectedFastener.setExpression('Placement', self.old_EE )
        self.selectedFastener.recompute()
        # highlight the selected LCS in its new position
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedFastener.Name +'.')
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
            # <<LinkName>>.Placement.multiply( <<LinkName>>.<<LCS.>>.Placement )
            # expr = '<<'+ a_Part +'>>.Placement.multiply( <<'+ a_Part +'>>.<<'+ a_LCS +'.>>.Placement )'
            expr = self.makeExpressionFastener( a_Link, a_Part, a_LCS )
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
            # recompute the object to apply the placement:
            self.selectedFastener.recompute()
            self.parentAssembly.recompute()
            self.activeDoc.recompute()
            # highlight the selected fastener in its new position
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedFastener.Name +'.')
        else:
            FCC.PrintWarning("Problem in selections\n")
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


    # fill the LCS list when changing the parent
    def onParentList(self):
        # clear the LCS list
        self.attLCSlist.clear()
        self.attLCStable = []
        # clear the selection in the GUI window
        Gui.Selection.clearSelection()
        # keep the fastener selected
        Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedFastener.Name+'.')
        # the current text in the combo-box is the link's name...
        # ... or it's 'Parent Assembly' then the parent is the 'Model' root App::Part		
        if self.parentList.currentText() == 'Parent Assembly':
            parentName = 'Parent Assembly'
            parentPart = self.activeDoc.getObject( 'Model' )
            # we get the LCS directly in the root App::Part 'Model'
            self.attLCStable = Asm4.getPartLCS( parentPart )
            self.parentDoc.setText( parentPart.Document.Name+'#'+Asm4.nameLabel(parentPart) )
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


    # An LCS has been clicked in 1 of the 2 lists, we highlight both LCS            |
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
            #a_Part = self.parentList.currentText()
            a_Part = self.parentTable[ self.parentList.currentIndex() ]
            # parent assembly and sister part need a different treatment
            if a_Part == 'Parent Assembly':
                linkDot = ''
            else:
                linkDot = a_Part+'.'
            Gui.Selection.addSelection( self.activeDoc.Name, 'Model', linkDot+a_LCS+'.')
            FCC.PrintMessage("selection: "+ linkDot+a_LCS+'.' +"\n")
        # show the resulting placement
        self.onApply()


    # Rotations
    def rotAxis( self, placement ):
        # placement is of TypeId 'Placement'
        # we only add the rotation, not the postion
        addRotation = placement.Rotation
        oldRotation  = self.selectedFastener.AttachmentOffset.Rotation
        newRotation  = oldRotation.multiply( addRotation )
        self.selectedFastener.AttachmentOffset.Rotation = newRotation
        self.selectedFastener.recompute()

    def onRotX(self):
        # return is a Placement extract the Rotation of it
        self.rotAxis(Asm4.rotX)

    def onRotY(self):
        self.rotAxis(Asm4.rotY)

    def onRotZ(self):
        self.rotAxis(Asm4.rotZ)


    # fill in the GUI
    def initUI(self):
        self.FStype.setText( self.selectedFastener.Label )
        self.attLCSlist.clear()
        # Initialize the assembly tree with the Parent Assembly as first element
        # clear the available parents combo box
        self.parentTable = []
        self.parentList.clear()
        self.parentTable.append( [] )
        self.parentList.addItem('Please select')
        self.parentTable.append( self.parentAssembly )
        parentIcon = self.parentAssembly.ViewObject.Icon
        self.parentList.addItem( parentIcon, 'Parent Assembly', self.parentAssembly )


    # defines the UI, only static elements
    def drawUI(self):
        # Build the window layout
        self.mainLayout = QtGui.QVBoxLayout()

        # the name as seen in the tree of the selected link
        self.formLayout = QtGui.QFormLayout()
        self.FStype = QtGui.QLineEdit()
        self.FStype.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Fastener :'),self.FStype)
        # combobox showing all available App::Link
        self.parentList = QtGui.QComboBox()
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

        # Rotation Buttons
        self.rotButtonsLayout = QtGui.QHBoxLayout()
        self.RotXButton = QtGui.QPushButton('Rot X')
        self.RotXButton.setToolTip("Rotate the instance around the X axis by 90deg")
        self.RotYButton = QtGui.QPushButton('Rot Y')
        self.RotYButton.setToolTip("Rotate the instance around the Y axis by 90deg")
        self.RotZButton = QtGui.QPushButton('Rot Z')
        self.RotZButton.setToolTip("Rotate the instance around the Z axis by 90deg")
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
        self.parentList.currentIndexChanged.connect( self.onParentList )
        ##self.attLCSlist.itemClicked.connect( self.onDatumClicked )
        self.attLCSlist.itemClicked.connect( self.onApply )
        self.RotXButton.clicked.connect( self.onRotX )
        self.RotYButton.clicked.connect( self.onRotY )
        self.RotZButton.clicked.connect( self.onRotZ)



"""
    +-----------------------------------------------+
    |        a class to create all fasteners        |
    |       from the Fasteners WB (ScrewMaker)      |
    +-----------------------------------------------+

Gui.activateWorkbench('FastenersWorkbench')
Gui.activateWorkbench('Assembly4Workbench')
import FastenersCmd as FS
fs = App.ActiveDocument.addObject("Part::FeaturePython",'Screw')
FS.FSScrewObject( fs, 'ISO4762', None )
fs.Label = fs.Proxy.itemText
FS.FSViewProviderTree(fs.ViewObject)
fs.ViewObject.ShapeColor = (0.3, 0.6, 0.7)
# (0.85, 0.3, 0.5)
# (1.0, 0.75, 0)
fs.recompute()
Gui.Selection.addSelection(fs)
Gui.runCommand('FSChangeParams')
    
"""

class insertFastener:
    "My tool object"
    def __init__(self, fastenerType):
        self.FStype = fastenerType
        # Screw:
        if  self.FStype      == 'Screw':
            self.menutext     = "Insert Screw"
            self.tooltip      = "Insert a Screw in the Assembly"
            self.icon         = os.path.join( Asm4.iconPath , 'Asm4_Screw.svg')
            self.FScolor      = (0.3, 0.6, 0.7)
        # Nut:
        elif self.FStype     == 'Nut':
            self.menutext     = "Insert Nut"
            self.tooltip      = "Insert a Nut in the Assembly"
            self.icon         = os.path.join( Asm4.iconPath , 'Asm4_Nut.svg')
            self.FScolor      = (0.85, 0.3, 0.5)
        # Washer:
        elif self.FStype     == 'Washer':
            self.menutext     = "Insert Washer"
            self.tooltip      = "Insert a Washer in the Assembly"
            self.icon         = os.path.join( Asm4.iconPath , 'Asm4_Washer.svg')
            self.FScolor      = (1.0, 0.75, 0.0)
        # Washer:
        elif self.FStype     == 'ThreadedRod':
            self.menutext     = "Insert threaded rod"
            self.tooltip      = "Insert threaded rod"
            self.icon         = os.path.join( Asm4.iconPath , 'Asm4_Rod.svg')
            self.FScolor      = (0.3, 0.5, 0.75)


    def GetResources(self):
        return {"MenuText": self.menutext,
                "ToolTip": self.tooltip,
                "Pixmap" : self.icon }

    def IsActive(self):
        if App.ActiveDocument and  self.getPart():
                return True
        return(None)

    def getPart(self):
        # check where to put our fastener
        if Gui.Selection.getSelection():
            selectedObj = Gui.Selection.getSelection()[0]
            # first-choice: it's an App::Part
            if selectedObj.TypeId=='App::Part':
                return( selectedObj )
            # if a previous fastener is selected, we return its parent container
            if isFastener(selectedObj):
                parent = selectedObj.getParentGeoFeatureGroup()
                if parent and parent.TypeId == 'App::Part':
                    return( parent )
        # or of nothing is selected but there is a Part called Model:
        elif App.ActiveDocument.getObject('Model') and App.ActiveDocument.Model.TypeId=='App::Part':
            return App.ActiveDocument.getObject('Model')
        # if there is no reason to be active:
        return(None)


    def Activated(self):
        # check that the Fasteners WB has been loaded before:
        if not 'FSChangeParams' in Gui.listCommands():
            Gui.activateWorkbench('FastenersWorkbench')
            Gui.activateWorkbench('Assembly4Workbench')
        # check that we have somewhere to put our stuff
        self.asmDoc = App.ActiveDocument
        part = self.getPart()
        if part :
            newFastener = App.ActiveDocument.addObject("Part::FeaturePython",self.FStype)
            newFastener.ViewObject.ShapeColor = self.FScolor
            if self.FStype == 'Screw':
                FS.FSScrewObject( newFastener, 'ISO4762', None )
            elif self.FStype == 'Nut':
                FS.FSScrewObject( newFastener, 'ISO4032', None )
            elif self.FStype == 'Washer':
                FS.FSScrewObject( newFastener, 'ISO7089', None )
            elif self.FStype == 'ThreadedRod':
                FS.FSThreadedRodObject( newFastener, None )
            # make the Proxy and stuff
            newFastener.Label = newFastener.Proxy.itemText
            FS.FSViewProviderTree(newFastener.ViewObject)
            # add Asm4 properties if necessary
            Asm4.makeAsmProperties( newFastener, reset=True )
            # add it to the Part 
            part.addObject( newFastener )
            # hide "offset" and "invert" properties to avoid confusion as they are not used in Asm4
            if hasattr( newFastener, 'offset' ):
                newFastener.setPropertyStatus('offset', 'Hidden')
            if hasattr( newFastener, 'invert' ):
                newFastener.setPropertyStatus('invert', 'Hidden')
            newFastener.recompute()
            # ... and select it
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( newFastener )
            Gui.runCommand('FSChangeParams')
            #Gui.runCommand( 'Asm4_placeFastener' )




"""
    +-----------------------------------------------+
    |         wrapper for FSChangeParams            |
    +-----------------------------------------------+
"""
class changeFSparametersCmd():

    def __init__(self):
        super(changeFSparametersCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Change Fastener parameters",
                "ToolTip": "Change Fastener parameters",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_FSparams.svg')
                }

    def IsActive(self):
        if App.ActiveDocument and getSelectionFS():
            return True
        return False

    def Activated(self):
        # check that the Fasteners WB has been loaded before:
        if not 'FSChangeParams' in Gui.listCommands():
            Gui.activateWorkbench('FastenersWorkbench')
            Gui.activateWorkbench('Assembly4Workbench')
        # check that we have selected a Fastener from the Fastener WB
        selection = getSelectionFS()
        if selection == None:
            return
        Gui.runCommand('FSChangeParams')



"""
    +-----------------------------------------------+
    |       add the commands to the workbench       |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_insertScrew',    insertFastener('Screw')  )
Gui.addCommand( 'Asm4_insertNut',      insertFastener('Nut')    )
Gui.addCommand( 'Asm4_insertWasher',   insertFastener('Washer') )
Gui.addCommand( 'Asm4_insertRod',      insertFastener('ThreadedRod') )
Gui.addCommand( 'Asm4_placeFastener',  placeFastenerCmd()       )
Gui.addCommand( 'Asm4_FSparameters',   changeFSparametersCmd()  )

# defines the drop-down button for Fasteners:
FastenersCmdList = [    'Asm4_insertScrew', 
                        'Asm4_insertNut', 
                        'Asm4_insertWasher', 
                        'Asm4_insertRod', 
                        'Asm4_FSparameters'] 
Gui.addCommand( 'Asm4_Fasteners', Asm4.dropDownCmd( FastenersCmdList, 'Fasteners'))

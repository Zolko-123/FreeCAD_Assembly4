#!/usr/bin/env python3
# coding: utf-8
#
# placeLinkCmd.py


import os, time

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import libAsm4 as Asm4




"""
    +-----------------------------------------------+
    |                Global variables               |
    +-----------------------------------------------+
"""
global taskUI

# selection view properties overrides
DrawStyle = 'Solid'
LineWidth = 3.0
DiffuseColor = (1.0, 1.0, 1.0, 0.0)
Transparency = 0.50



"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class placeLinkCmd():
    def __init__(self):
        super(placeLinkCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Edit Placement of a Part",
                "ToolTip": "Move/Attach a Part in the assembly",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Place_Link.svg')
                }

    def IsActive(self):
        # We only insert a link into an Asm4  Model
        if (App.ActiveDocument and (Asm4.getSelection() or (all(Asm4.getLinkAndDatum2())))):
            return True
        return False

    def Activated(self):
        # enable the local link selection observer
        global linkObserver
        linkObserver = linkSelObserver();
        # add the listener, 0 forces to resolve the links
        Gui.Selection.addObserver(linkObserver, 0)
        # launch the UI in the task panel
        Gui.Control.showDialog(placeLinkUI())




"""
    +-----------------------------------------------+
    |    The UI and functions in the Task panel     |
    +-----------------------------------------------+
"""
class placeLinkUI():

    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base        
        iconFile = os.path.join( Asm4.iconPath , 'Place_Link.svg')
        self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle('Place linked Part')

        # check that we have selected two LCS or an App::Link object
        self.selectedLink = []
        self.selectedLCSA = None
        self.selectedLinkB = None
        self.selectedLCSB = None
        selection = Asm4.getSelection()
        selectedLCSPair = Asm4.getLinkAndDatum2()
        self.Xtranslation = 0.00
        self.Ytranslation = 0.00
        self.Ztranslation = 0.00
        self.XrotationAngle = 0.00
        self.YrotationAngle = 0.00
        self.ZrotationAngle = 0.00

        # draw the GUI, objects are defined later down
        self.drawUI()
        global taskUI
        taskUI = self
      
        if not all(selectedLCSPair):
            #Handle single selected App::Link
            if not selection :
                # This shouldn't happen
                FCC.PrintWarning("This is not an error message you are supposed to see, something went wrong\n")
                Gui.Control.closeDialog()
            else:
                self.selectedLink = selection

            #save original AttachmentOffset of linked part
            self.old_LinkAttachmentOffset = self.selectedLink.AttachmentOffset
            self.old_LinkRotation = self.selectedLink.AttachmentOffset.Rotation
            self.old_LinkPosition = self.selectedLink.AttachmentOffset.Base
            # default values correspond to original AttachmentOffset of linked part
            self.Xtranslation = self.old_LinkPosition[0]
            self.Ytranslation = self.old_LinkPosition[1]
            self.Ztranslation = self.old_LinkPosition[2]
            self.XrotationAngle = self.old_LinkRotation.toEuler()[0]
            self.YrotationAngle = self.old_LinkRotation.toEuler()[1]
            self.ZrotationAngle = self.old_LinkRotation.toEuler()[2]
            self.XrotAngleSpinBox.setValue(self.XrotationAngle)
            self.YrotAngleSpinBox.setValue(self.YrotationAngle)
            self.ZrotAngleSpinBox.setValue(self.ZrotationAngle)
            self.XtranslSpinBox.setValue(self.old_LinkPosition[0])
            self.YtranslSpinBox.setValue(self.old_LinkPosition[1])
            self.ZtranslSpinBox.setValue(self.old_LinkPosition[2])
            
            # save previous view properties
            self.old_OverrideMaterial = self.selectedLink.ViewObject.OverrideMaterial
            self.old_DrawStyle = self.selectedLink.ViewObject.DrawStyle
            self.old_LineWidth = self.selectedLink.ViewObject.LineWidth
            self.old_DiffuseColor = self.selectedLink.ViewObject.ShapeMaterial.DiffuseColor
            self.old_Transparency = self.selectedLink.ViewObject.ShapeMaterial.Transparency
            # set new view properties
            self.selectedLink.ViewObject.OverrideMaterial = True
            self.selectedLink.ViewObject.DrawStyle = DrawStyle
            self.selectedLink.ViewObject.LineWidth = LineWidth
            self.selectedLink.ViewObject.ShapeMaterial.DiffuseColor = DiffuseColor
            self.selectedLink.ViewObject.ShapeMaterial.Transparency = Transparency

            # get the current active document to avoid errors if user changes tab
            self.activeDoc = App.activeDocument()
            # the parent (top-level) assembly is the App::Part called Model (hard-coded)
            self.parentAssembly = self.activeDoc.Model

            # check that the link is an Asm4 link:
            self.isAsm4EE = False
            if hasattr(self.selectedLink,'AssemblyType'):
                if self.selectedLink.AssemblyType == 'Asm4EE' or self.selectedLink.AssemblyType == '' :
                    self.isAsm4EE = True
                else:
                    Asm4.warningBox("This Link's assembly type doesn't correspond to this WorkBench")
                    return

            # initialize the UI with the current data
            self.attLCStable = []
            self.initUI()
            # now self.parentList and self.parentTable are available

            # find all the linked parts in the assembly
            for objName in self.parentAssembly.getSubObjects():
                # remove the trailing .
                obj = self.activeDoc.getObject(objName[0:-1])
                if obj.TypeId=='App::Link' and hasattr(obj.LinkedObject,'isDerivedFrom'):
                    if obj.LinkedObject.isDerivedFrom('App::Part') or obj.LinkedObject.isDerivedFrom('PartDesign::Body'):
                    # ... except if it's the selected link itself
                        if obj != self.selectedLink:
                            self.parentTable.append( obj )
                            # add to the drop-down combo box with the assembly tree's parts
                            objIcon = obj.LinkedObject.ViewObject.Icon
                            objText = Asm4.nameLabel(obj)
                            self.parentList.addItem( objIcon, objText, obj)

            # find all the LCS in the selected link
            self.partLCStable = Asm4.getPartLCS( self.selectedLink.LinkedObject )
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

            # decode the old ExpressionEngine
            old_Parent = ''
            old_ParentPart = ''
            old_attLCS = ''
            constrName = ''
            linkedDoc = ''
            old_linkLCS = ''
            # if the decode is unsuccessful, old_Expression is set to False and the other things are set to 'None'
            ( old_Parent, old_attLCS, old_linkLCS ) = Asm4.splitExpressionLink( self.old_EE, self.old_Parent )

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

                
        else:
            #Handle pair of selected LCS
            self.selectedLink = selectedLCSPair[0]
            self.selectedLCSA = selectedLCSPair[1]
            self.selectedLinkB = selectedLCSPair[2]
            self.selectedLCSB = selectedLCSPair[3]

            #save original AttachmentOffset of linked part
            self.old_LinkAttachmentOffset = self.selectedLink.AttachmentOffset
            self.old_LinkRotation = self.selectedLink.AttachmentOffset.Rotation
            self.old_LinkPosition = self.selectedLink.AttachmentOffset.Base
            # default values correspond to original AttachmentOffset of linked part
            self.Xtranslation = self.old_LinkPosition[0]
            self.Ytranslation = self.old_LinkPosition[1]
            self.Ztranslation = self.old_LinkPosition[2]
            self.XrotationAngle = self.old_LinkRotation.toEuler()[0]
            self.YrotationAngle = self.old_LinkRotation.toEuler()[1]
            self.ZrotationAngle = self.old_LinkRotation.toEuler()[2]
            self.XrotAngleSpinBox.setValue(self.XrotationAngle)
            self.YrotAngleSpinBox.setValue(self.YrotationAngle)
            self.ZrotAngleSpinBox.setValue(self.ZrotationAngle)
            self.XtranslSpinBox.setValue(self.old_LinkPosition[0])
            self.YtranslSpinBox.setValue(self.old_LinkPosition[1])
            self.ZtranslSpinBox.setValue(self.old_LinkPosition[2])
            
            # save previous view properties
            self.old_OverrideMaterial = self.selectedLink.ViewObject.OverrideMaterial
            self.old_OverrideMaterialB = self.selectedLinkB.ViewObject.OverrideMaterial
            self.old_DrawStyle = self.selectedLink.ViewObject.DrawStyle
            self.old_DrawStyleB = self.selectedLinkB.ViewObject.DrawStyle
            self.old_LineWidth = self.selectedLink.ViewObject.LineWidth
            self.old_LineWidthB = self.selectedLinkB.ViewObject.LineWidth
            self.old_DiffuseColor = self.selectedLink.ViewObject.ShapeMaterial.DiffuseColor
            self.old_DiffuseColorB = self.selectedLinkB.ViewObject.ShapeMaterial.DiffuseColor
            self.old_Transparency = self.selectedLink.ViewObject.ShapeMaterial.Transparency
            self.old_TransparencyB = self.selectedLinkB.ViewObject.ShapeMaterial.Transparency
            # set new view properties
            self.selectedLink.ViewObject.OverrideMaterial = True
            self.selectedLinkB.ViewObject.OverrideMaterial = True
            self.selectedLink.ViewObject.DrawStyle = DrawStyle
            self.selectedLinkB.ViewObject.DrawStyle = DrawStyle
            self.selectedLink.ViewObject.LineWidth = LineWidth
            self.selectedLinkB.ViewObject.LineWidth = LineWidth
            self.selectedLink.ViewObject.ShapeMaterial.DiffuseColor = DiffuseColor
            self.selectedLinkB.ViewObject.ShapeMaterial.DiffuseColor = DiffuseColor
            self.selectedLink.ViewObject.ShapeMaterial.Transparency = Transparency
            self.selectedLinkB.ViewObject.ShapeMaterial.Transparency = Transparency

            # get the current active document to avoid errors if user changes tab
            self.activeDoc = App.activeDocument()
            # the parent (top-level) assembly is the App::Part called Model (hard-coded)
            self.parentAssembly = self.activeDoc.Model

            # check that the link is an Asm4 link:
            self.isAsm4EE = False
            if ((hasattr(self.selectedLink,'AssemblyType')) and (hasattr(self.selectedLinkB,'AssemblyType'))):
                if ((self.selectedLink.AssemblyType == 'Asm4EE' or self.selectedLink.AssemblyType == '') and (self.selectedLinkB.AssemblyType == 'Asm4EE' or self.selectedLinkB.AssemblyType == '')) :
                    self.isAsm4EE = True
                else:
                    Asm4.warningBox("This Link's assembly type doesn't correspond to this WorkBench")
                    return

            # initialize the UI with the current data
            self.attLCStable = []
            self.initUI()
            # now self.parentList and self.parentTable are available

            # find all the linked parts in the assembly
            for objName in self.parentAssembly.getSubObjects():
                # remove the trailing .
                obj = self.activeDoc.getObject(objName[0:-1])
                if obj.TypeId=='App::Link' and hasattr(obj.LinkedObject,'isDerivedFrom'):
                    if obj.LinkedObject.isDerivedFrom('App::Part') or obj.LinkedObject.isDerivedFrom('PartDesign::Body'):
                    # ... except if it's the selected link itself
                        if obj != self.selectedLink:
                            self.parentTable.append( obj )
                            # add to the drop-down combo box with the assembly tree's parts
                            objIcon = obj.LinkedObject.ViewObject.Icon
                            objText = Asm4.nameLabel(obj)
                            self.parentList.addItem( objIcon, objText, obj)

            # find all the LCS in the selected link A
            self.partLCStable = Asm4.getPartLCS( self.selectedLink.LinkedObject )
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

            # decode the old ExpressionEngine
            old_Parent = ''
            old_ParentPart = ''
            old_attLCS = ''
            constrName = ''
            linkedDoc = ''
            old_linkLCS = ''
            # if the decode is unsuccessful, old_Expression is set to False and the other things are set to 'None'
            ( old_Parent, old_attLCS, old_linkLCS ) = Asm4.splitExpressionLink( self.old_EE, self.old_Parent )
            # select LCS in the list of LCS in the linked part according to selectedLCSPair[1]
            lcs_found = self.partLCSlist.findItems( self.selectedLCSA.Label, QtCore.Qt.MatchExactly )
            if not lcs_found:
                # find the old LCS in the list of LCS of the linked part...
                # MatchExactly, MatchContains, MatchEndsWith ...
                lcs_found = self.partLCSlist.findItems( old_linkLCS, QtCore.Qt.MatchExactly )
                if not lcs_found:
                    lcs_found = self.partLCSlist.findItems( old_linkLCS+' (', QtCore.Qt.MatchStartsWith )
            if lcs_found:
                # ... and select it
                self.partLCSlist.setCurrentItem( lcs_found[0] )


            # find the oldPart in the part list...
            if self.selectedLCSB is not None:
                parent_found = False
                parent_index = 1
                for item in self.parentTable[1:]:
                    if item.Name == self.selectedLinkB.Name:
                        parent_found = True
                        break
                    else:
                        parent_index = parent_index + 1
            elif old_Parent == 'Parent Assembly':
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
                        parent_index = parent_index + 1
            if not parent_found:
                parent_index = 0
            self.parentList.setCurrentIndex( parent_index )
            # this should have triggered self.getPartLCS() to fill the LCS list

            # select attachment LCS in the list of Datums in the linked part according to second selected LCS
            lcs_found = self.attLCSlist.findItems( Asm4.nameLabel(self.selectedLCSB), QtCore.Qt.MatchExactly )

            # else find the old attachment Datum in the list of the Datums in the linked part...
            if not lcs_found:
                lcs_found = self.attLCSlist.findItems( old_attLCS, QtCore.Qt.MatchExactly )
                if not lcs_found:
                    lcs_found = self.attLCSlist.findItems( old_attLCS+' (', QtCore.Qt.MatchStartsWith )
            if lcs_found:
                # ... and select it
                self.attLCSlist.setCurrentItem( lcs_found[0] )

    # Close
    def finish(self):
        # remove the  observer
        global linkObserver
        Gui.Selection.removeObserver(linkObserver) 

        self.restoreView()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedLink.Name+'.' )
        Gui.Control.closeDialog()


    # restore initial view properties
    def restoreView(self, normal=True):
        self.selectedLink.ViewObject.OverrideMaterial = False
        self.selectedLink.ViewObject.DrawStyle    = self.old_DrawStyle
        self.selectedLink.ViewObject.LineWidth    = self.old_LineWidth
        self.selectedLink.ViewObject.ShapeMaterial.DiffuseColor = self.old_DiffuseColor
        self.selectedLink.ViewObject.ShapeMaterial.Transparency = self.old_Transparency
        if self.selectedLinkB:
            self.selectedLinkB.ViewObject.OverrideMaterial = False
            self.selectedLinkB.ViewObject.DrawStyle    = self.old_DrawStyleB
            self.selectedLinkB.ViewObject.LineWidth    = self.old_LineWidthB
            self.selectedLinkB.ViewObject.ShapeMaterial.DiffuseColor = self.old_DiffuseColorB
            self.selectedLinkB.ViewObject.ShapeMaterial.Transparency = self.old_TransparencyB

    # standard FreeCAD Task panel buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel
                   | QtGui.QDialogButtonBox.Ok
                   | QtGui.QDialogButtonBox.Ignore)


    # OK
    def accept(self):
        if self.Apply():
            # highlight in the 3D window the object we placed
            self.finish()
        else:
            FCC.PrintWarning("Problem in selections\n")
            return


    # Cancel, restore previous values if available
    def reject(self):
        if self.old_AO:
            self.selectedLink.AttachmentOffset = self.old_AO
        if self.old_EE:
            self.selectedLink.setExpression( 'Placement', self.old_EE )
        self.selectedLink.recompute()
        # highlight in the 3D window the object we placed
        self.finish()


    # Free insert
    def clicked(self, button):
        if button == QtGui.QDialogButtonBox.Ignore:
            # ask for confirmation before resetting everything
            msgName = Asm4.nameLabel(self.selectedLink)
            # see whether the ExpressionEngine field is filled
            if self.selectedLink.ExpressionEngine :
                # if yes, then ask for confirmation
                confirmed = Asm4.confirmBox('This command will release all attachments on '+msgName+' and set it to manual positioning in its current location.')
                # if not, then it's useless to bother the user
            else:
                confirmed = True
            if confirmed:
                # unset the ExpressionEngine for the Placement
                self.selectedLink.setExpression('Placement', None)
                # reset the assembly properties
                Asm4.makeAsmProperties( self.selectedLink, reset=True )
                # finish
                FCC.PrintWarning("Part is now manually placed\n")
                self.finish()
            else:
                FCC.PrintWarning("Part untouched\n")
                self.finish()






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

        # check that all of them have something in
        # constrName has been checked at the beginning
        if a_Link and a_LCS and l_Part and l_LCS :
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
            return True
        else:
            #FCC.PrintWarning("Problem in selections\n")
            return False

    '''
    # get all the LCS in a part
    def getPartLCS( self, part ):
        partLCS = [ ]
        # parse all objects in the part (they return strings)
        for objName in part.getSubObjects(1):
            # get the proper objects
            # all object names end with a "." , this needs to be removed
            obj = part.getObject( objName[0:-1] )
            if obj.TypeId == 'PartDesign::CoordinateSystem':
                partLCS.append( obj )
        return partLCS
    '''

    # fill the LCS list when changing the parent
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




    # Reorientation
    def reorientLink( self ):
        moveXYZ = App.Placement( App.Vector(self.Xtranslation,self.Ytranslation,self.Ztranslation), self.old_LinkRotation )
        # New AttachmentOffset rotation of the link is difference between set rotation angles and original AttachmentOffset rotation of the link
        rotationX = App.Placement( App.Vector(0.00, 0.00, 0.00), App.Rotation( App.Vector(1,0,0), self.XrotationAngle - self.old_LinkRotation.toEuler()[0] ))
        rotationY = App.Placement( App.Vector(0.00, 0.00, 0.00), App.Rotation( App.Vector(0,1,0), self.YrotationAngle - self.old_LinkRotation.toEuler()[1] ))
        rotationZ = App.Placement( App.Vector(0.00, 0.00, 0.00), App.Rotation( App.Vector(0,0,1), self.ZrotationAngle - self.old_LinkRotation.toEuler()[2] ))

        self.selectedLink.AttachmentOffset = moveXYZ * rotationX * rotationY * rotationZ
        self.selectedLink.recompute()

    def onXRotValChanged(self):
        self.XrotationAngle = self.XrotAngleSpinBox.value()
        self.reorientLink()

    def onYRotValChanged(self):
        self.YrotationAngle = self.YrotAngleSpinBox.value()
        self.reorientLink()
        
    def onZRotValChanged(self):
        self.ZrotationAngle = self.ZrotAngleSpinBox.value()
        self.reorientLink()
        
    def onXTranslValChanged(self):
        self.Xtranslation = self.XtranslSpinBox.value()
        self.reorientLink()
        
    def onYTranslValChanged(self):
        self.Ytranslation = self.YtranslSpinBox.value()
        self.reorientLink()
        
    def onZTranslValChanged(self):
        self.Ztranslation = self.ZtranslSpinBox.value()
        self.reorientLink()
        
    # Rotations
    def onRotX(self):
        if self.XrotationAngle > 270.0: 
            self.XrotAngleSpinBox.setValue(self.XrotationAngle - 270.0)
        else:
            self.XrotAngleSpinBox.setValue(self.XrotationAngle + 90.0)

    def onRotY(self):
        if self.YrotationAngle > 270.0: 
            self.YrotAngleSpinBox.setValue(self.YrotationAngle - 270.0)
        else:
            self.YrotAngleSpinBox.setValue(self.YrotationAngle + 90.0)

    def onRotZ(self):
        if self.ZrotationAngle > 270.0: 
            self.ZrotAngleSpinBox.setValue(self.ZrotationAngle - 270.0)
        else:
            self.ZrotAngleSpinBox.setValue(self.ZrotationAngle + 90.0)

    # initialize the UI for the selected link
    def initUI(self):
        # clear the parent name (if any)
        self.parentDoc.clear()
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
        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self.form)
        
        # Define the fields for the form ( label + widget )
        self.formLayout = QtGui.QFormLayout()
        # Selected Link (the name as seen in the tree of the selected link)
        self.linkName = QtGui.QLineEdit()
        self.linkName.setReadOnly(True)
        self.formLayout.addRow(QtGui.QLabel('Selected Link :'),self.linkName)

        # combobox showing all available App::Link
        self.parentList = QtGui.QComboBox()
        self.parentList.setToolTip('Choose the part in which the attachment\ncoordinate system is to be found')
        # the parent assembly is hardcoded, and made the first real element
        self.formLayout.addRow(QtGui.QLabel('Attach to :'),self.parentList)
        self.mainLayout.addLayout(self.formLayout)

        # with 2 columns
        self.columnsLayout = QtGui.QHBoxLayout()
        self.leftLayout = QtGui.QVBoxLayout()
        self.rightLayout = QtGui.QVBoxLayout()
        # Part, left side
        #
        # the document containing the linked part
        self.leftLayout.addWidget(QtGui.QLabel("Linked Part :"))
        self.linkedDoc = QtGui.QLineEdit()
        self.linkedDoc.setReadOnly(True)
        self.leftLayout.addWidget(self.linkedDoc)

        # The list of all LCS in the part is a QListWidget
        self.leftLayout.addWidget(QtGui.QLabel("Select LCS in Part :"))
        self.partLCSlist = QtGui.QListWidget()
        self.partLCSlist.setMinimumHeight(200)
        self.partLCSlist.setToolTip('Select a coordinate system from the list')
        self.leftLayout.addWidget(self.partLCSlist)

        # Assembly, Right side
        #
        # the document containing the linked object
        self.rightLayout.addWidget(QtGui.QLabel("Parent Part :"))
        self.parentDoc = QtGui.QLineEdit()
        self.parentDoc.setReadOnly(True)
        self.rightLayout.addWidget(self.parentDoc)
        # The list of all attachment LCS in the assembly is a QListWidget
        # it is populated only when the parent combo-box is activated
        self.rightLayout.addWidget(QtGui.QLabel("Select LCS in Parent :"))
        self.attLCSlist = QtGui.QListWidget()
        self.attLCSlist.setMinimumHeight(200)
        self.attLCSlist.setToolTip('Select a coordinate system from the list')
        self.rightLayout.addWidget(self.attLCSlist)

        # add the 2 columns
        self.columnsLayout.addLayout(self.leftLayout)
        self.columnsLayout.addLayout(self.rightLayout)
        self.mainLayout.addLayout(self.columnsLayout)

        # X Translation Value
        self.XtranslSpinBoxLayout = QtGui.QHBoxLayout()
        self.XtranslSpinBox = QtGui.QDoubleSpinBox()
        self.XtranslSpinBox.setRange(-999999.00, 999999.00)
        self.XtranslSpinBox.setValue(self.Xtranslation)
        self.XtranslSpinBox.setToolTip("X translation in mm")
        # add the QLDoubleSpinBox
        self.XtranslSpinBoxLayout.addStretch()
        self.XtranslSpinBoxLabel = self.XtranslSpinBoxLayout.addWidget(QtGui.QLabel("X translation in mm: "))
        self.XtranslSpinBoxLayout.addWidget(self.XtranslSpinBox)
        self.mainLayout.addLayout(self.XtranslSpinBoxLayout)
        
        # Y Translation Value
        self.YtranslSpinBoxLayout = QtGui.QHBoxLayout()
        self.YtranslSpinBox = QtGui.QDoubleSpinBox()
        self.YtranslSpinBox.setRange(-999999.00, 999999.00)
        self.YtranslSpinBox.setValue(self.Ytranslation)
        self.YtranslSpinBox.setToolTip("Y translation in mm")
        # add the QLDoubleSpinBox
        self.YtranslSpinBoxLayout.addStretch()
        self.YtranslSpinBoxLabel = self.YtranslSpinBoxLayout.addWidget(QtGui.QLabel("Y translation in mm: "))
        self.YtranslSpinBoxLayout.addWidget(self.YtranslSpinBox)
        self.mainLayout.addLayout(self.YtranslSpinBoxLayout)

        # Z Translation Value
        self.ZtranslSpinBoxLayout = QtGui.QHBoxLayout()
        self.ZtranslSpinBox = QtGui.QDoubleSpinBox()
        self.ZtranslSpinBox.setRange(-999999.00, 999999.00)
        self.ZtranslSpinBox.setValue(self.Ztranslation)
        self.ZtranslSpinBox.setToolTip("Z translation in mm")
        # add the QLDoubleSpinBox
        self.ZtranslSpinBoxLayout.addStretch()
        self.ZtranslSpinBoxLabel = self.ZtranslSpinBoxLayout.addWidget(QtGui.QLabel("Z translation in mm: "))
        self.ZtranslSpinBoxLayout.addWidget(self.ZtranslSpinBox)
        self.mainLayout.addLayout(self.ZtranslSpinBoxLayout)

        # X Rotation Value
        self.XrotAngleSpinBoxLayout = QtGui.QHBoxLayout()
        self.XrotAngleSpinBox = QtGui.QDoubleSpinBox()
        self.XrotAngleSpinBox.setRange(-360.00, 360.00)
        self.XrotAngleSpinBox.setValue(self.XrotationAngle)
        self.XrotAngleSpinBox.setToolTip("Rotation around x-axis in deg.")
        self.RotXButton = QtGui.QPushButton('Rot X + 90°')
        self.RotXButton.setToolTip("Rotate 90 deg around X axis")
        # add the QLDoubleSpinBox
        self.XrotAngleSpinBoxLayout.addStretch()
        self.XrotAngleSpinBoxLabel = self.XrotAngleSpinBoxLayout.addWidget(QtGui.QLabel("Rotation around x-axis in deg.: "))
        self.XrotAngleSpinBoxLayout.addWidget(self.XrotAngleSpinBox)
        self.XrotAngleSpinBoxLayout.addWidget(self.RotXButton)
        self.mainLayout.addLayout(self.XrotAngleSpinBoxLayout)

        # Y Rotation Value
        self.YrotAngleSpinBoxLayout = QtGui.QHBoxLayout()
        self.YrotAngleSpinBox = QtGui.QDoubleSpinBox()
        self.YrotAngleSpinBox.setRange(-360.00, 360.00)
        self.YrotAngleSpinBox.setValue(self.YrotationAngle)
        self.YrotAngleSpinBox.setToolTip("Rotation around y-axis in deg.")
        self.RotYButton = QtGui.QPushButton('Rot Y + 90°')
        self.RotYButton.setToolTip("Rotate 90 deg around Y axis")
        # add the QLDoubleSpinBox
        self.YrotAngleSpinBoxLayout.addStretch()
        self.YrotAngleSpinBoxLabel = self.YrotAngleSpinBoxLayout.addWidget(QtGui.QLabel("Rotation around y-axis in deg.: "))
        self.YrotAngleSpinBoxLayout.addWidget(self.YrotAngleSpinBox)
        self.YrotAngleSpinBoxLayout.addWidget(self.RotYButton)
        self.mainLayout.addLayout(self.YrotAngleSpinBoxLayout)

        # Z Rotation Value
        self.ZrotAngleSpinBoxLayout = QtGui.QHBoxLayout()
        self.ZrotAngleSpinBox = QtGui.QDoubleSpinBox()
        self.ZrotAngleSpinBox.setRange(-360.00, 360.00)
        self.ZrotAngleSpinBox.setValue(self.ZrotationAngle)
        self.ZrotAngleSpinBox.setToolTip("Rotation around z-axis in deg.")
        self.RotZButton = QtGui.QPushButton('Rot Z + 90°')
        self.RotZButton.setToolTip("Rotate 90 deg around Z axis")
        # add the QLDoubleSpinBox and button
        self.ZrotAngleSpinBoxLayout.addStretch()
        self.ZrotAngleSpinBoxLabel = self.ZrotAngleSpinBoxLayout.addWidget(QtGui.QLabel("Rotation around z-axis in deg.: "))
        self.ZrotAngleSpinBoxLayout.addWidget(self.ZrotAngleSpinBox)
        self.ZrotAngleSpinBoxLayout.addWidget(self.RotZButton)
        self.mainLayout.addLayout(self.ZrotAngleSpinBoxLayout)

        # apply the layout to the main window
        self.form.setLayout(self.mainLayout)

        # Actions
        self.parentList.currentIndexChanged.connect( self.onParentSelected )
        self.attLCSlist.itemClicked.connect( self.Apply )
        self.partLCSlist.itemClicked.connect( self.Apply )
        self.RotXButton.clicked.connect( self.onRotX )
        self.RotYButton.clicked.connect( self.onRotY )
        self.RotZButton.clicked.connect( self.onRotZ )
        self.XrotAngleSpinBox.valueChanged.connect(self.onXRotValChanged)
        self.YrotAngleSpinBox.valueChanged.connect(self.onYRotValChanged)
        self.ZrotAngleSpinBox.valueChanged.connect(self.onZRotValChanged)
        self.XtranslSpinBox.valueChanged.connect(self.onXTranslValChanged)
        self.YtranslSpinBox.valueChanged.connect(self.onYTranslValChanged)
        self.ZtranslSpinBox.valueChanged.connect(self.onZTranslValChanged)



"""
    +-----------------------------------------------+
    |            selection observer                 |
    +-----------------------------------------------+
"""
class linkSelObserver:
    def addSelection(self,doc,obj,sub,pnt):               # Selection object
        # Since both 3D view clicks and manual tree selection gets into the same callback
        # we will determine by clicked coordinates, for manual tree selections the coordinates are (0,0,0)
        if pnt != (0,0,0):
            # 3D view click
            # Get linked object name that handles sub-sub-assembly
            #subObjName = Asm4.getLinkedObjectName(doc, obj, sub)
            objList = App.getDocument(doc).getObject(obj).getSubObjectList(sub)
            # Build the name of the selected sub-object for multiple sub-assembly levels
            subObjName = ''
            for subObj in objList:
                if subObj.TypeId == 'App::Link':
                    subObjName = subObjName + subObj.Name + '.'

            if subObjName != '':
                # set the selection to the selected object
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(doc, obj, subObjName)
                # set the selected object drop-down to this object
                global taskUI
                link = App.ActiveDocument.getObject(subObjName[0:-1])
                #FCC.PrintMessage('LinkedObject = '+link.LinkedObject.Name+'\n')
                # try to find this link in the parents 
                parent_found = False
                parent_index = 1
                for item in taskUI.parentTable[1:]:
                    if item.Name == link.Name:
                        parent_found = True
                        break
                    else:
                        parent_index = parent_index +1
                if not parent_found:
                    parent_index = 0
                taskUI.parentList.setCurrentIndex( parent_index )
            # select the Parent Assembly
            else:
                taskUI.parentList.setCurrentIndex( 1 )




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_placeLink', placeLinkCmd() )

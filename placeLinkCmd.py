#!/usr/bin/env python3
# coding: utf-8
#
# placeLinkCmd.py


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, math, re

from libAsm4 import *



"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class placeLink( QtGui.QDialog ):
	"My tool object"


	def __init__(self):
		super(placeLink,self).__init__()
		self.selectedLink = []
		self.attLCStable = []


	def GetResources(self):
		return {"MenuText": "Edit Placement of a Part",
				"ToolTip": "Move/Attach a Part in the assembly",
				"Pixmap" : os.path.join( iconPath , 'Place_Link.svg')
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

		# check that we have selected an App::Link object
		selection = self.GetSelection()
		if not selection:
			self.close()
		else:
			self.selectedLink = selection

		# check that the link is an Asm4 link:
		self.isAsm4EE = False
		if hasattr(self.selectedLink,'AssemblyType'):
			if self.selectedLink.AssemblyType == 'Asm4EE':
				self.isAsm4EE = True
			else:
				msgBox = QtGui.QMessageBox()
				msgBox.setWindowTitle('Warning')
				msgBox.setIcon(QtGui.QMessageBox.Critical)
				msgBox.setText("This Link's Assembly Type doesn't correspond to this WorkBench")
				msgBox.exec_()
				return


		# draw the GUI, objects are defined later down
		self.drawUI()

		# the parent (top-level) assembly is the App::Part called Model (hard-coded)
		# What would happen if there are 2 App::Part ?
		self.parentAssembly = self.activeDoc.Model
		# Initialize the assembly tree with the Parrent Assembly as first element
		# all the parts in the assembly, except the selected link
		self.asmParts = []
		# the first item is "Select attachment Parent" therefore we add an empty object
		self.asmParts.append( [] )
		self.asmParts.append( self.parentAssembly )
		# Add it as first element to the drop-down combo-box
		parentIcon = self.parentAssembly.ViewObject.Icon
		self.parentList.addItem( parentIcon, 'Parent Assembly', self.parentAssembly )

		# find all the linked parts in the assembly
		for obj in self.activeDoc.findObjects("App::Link"):
			# add it to our list if it's a link to an App::Part ...
			if obj.LinkedObject.isDerivedFrom('App::Part'):
				# ... except if it's the selected link itself
				if obj != self.selectedLink:
					self.asmParts.append( obj )
					# add to the drop-down combo box with the assembly tree's parts
					objIcon = obj.LinkedObject.ViewObject.Icon
					if obj.Name == obj.Label:
						objText = obj.Name
					else:
						objText = obj.Label+' ('+obj.Name+')'
					self.parentList.addItem( objIcon, objText, obj)


		# find all the LCS in the selected link
		self.partLCStable = self.getPartLCS( self.selectedLink.LinkedObject )
		# build the list
		for lcs in self.partLCStable:
			newItem = QtGui.QListWidgetItem()
			if lcs.Name == lcs.Label:
				newItem.setText( lcs.Name )
			else:
				newItem.setText( lcs.Label + ' (' +lcs.Name+ ')' )
			#newItem.setIcon( lcs.ViewObject.Icon )
			#self.lcsIcon = lcs.ViewObject.Icon
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
		old_EE = self.selectedLink.ExpressionEngine
		if old_EE:
			( pla, self.old_EE ) = old_EE[0]

		# for debugging, use this field to print text
		#self.expression.setText( self.old_attPart )


		# decode the old ExpressionEngine
		old_Parent = ''
		old_ParentPart = ''
		old_attLCS = ''
		constrName = ''
		linkedPart = ''
		old_linkLCS = ''
		# if the linked part is in the same document as the assembly:
		if self.parentAssembly.Document.Name == self.selectedLink.LinkedObject.Document.Name:
			( old_Parent, old_attLCS, old_linkLCS ) = self.splitExpressionDoc( self.old_EE, self.old_Parent )
		# if the linked part comes from another document:
		else:
		# if the decode is unsuccessful, old_Expression is set to False and the other things are set to 'None'
			( old_Parent, old_attLCS, old_linkLCS ) = self.splitExpressionLink( self.old_EE, self.old_Parent )
		#self.expression.setText( old_Parent +'***'+ self.old_Parent )


		# find the old LCS in the list of LCS of the linked part...
		# MatchExactly, MatchContains, MatchEndsWith ...
		lcs_found = []
		lcs_found = self.partLCSlist.findItems( old_linkLCS, QtCore.Qt.MatchExactly )
		if lcs_found:
			# ... and select it
			self.partLCSlist.setCurrentItem( lcs_found[0] )
		else:
			# may-be it was renamed, see if we can find it as (name)
			lcs_found = self.partLCSlist.findItems( '('+old_linkLCS+')', QtCore.Qt.MatchContains )
			if lcs_found:
				self.partLCSlist.setCurrentItem( lcs_found[0] )


		# find the oldPart in the part list...
		if old_Parent == 'Parent Assembly':
			parent_found = True
			parent_index = 1
		else:
			parent_found = False
			parent_index = 1
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


		# find the oldLCS in the old parent Part (actually the App::Link)...
		#self.oldLCS = self.attLCSlist.findItems( self.old_attLCS, QtCore.Qt.CaseSensitive )
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


		# the widget is shown and not executed to allow it to stay on top
		self.show()




	"""
    +-----------------------------------------------+
    |         populate the ExpressionEngine         |
    |             for a linked App::Part            |
    +-----------------------------------------------+
	"""
	def makeExpressionPart( self, attLink, attPart, attLCS, linkedPart, linkLCS ):
		# if everything is defined
		if attLink and attLCS and linkedPart and linkLCS:
			# this is where all the magic is, see:
			# 
			# https://forum.freecadweb.org/viewtopic.php?p=278124#p278124
			#
			# as of FreeCAD v0.19 the syntax is different:
			# https://forum.freecadweb.org/viewtopic.php?f=17&t=38974&p=337784#p337784
			# expr = ParentLink.Placement * ParentPart#LCS.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1
			# expr = LCS_in_the_assembly.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1
			# the AttachmentOffset is now a property of the App::Link
			# expr = LCS_in_the_assembly.Placement * AttachmentOffset * LinkedPart#LCS.Placement ^ -1
			expr = attLCS+'.Placement * AttachmentOffset * '+linkedPart+'#'+linkLCS+'.Placement ^ -1'
			# if we're attached to another sister part (and not the Parent Assembly)
			# we need to take into account the Placement of that Part.
			if attPart:
				expr = attLink+'.Placement * '+attPart+'#'+expr
		else:
			expr = False
		return expr




	"""
    +-----------------------------------------------+
    |  split the ExpressionEngine of a linked part  |
    |          to find the old attachment LCS       |
    |   (in the parent assembly or a sister part)   |
    |   and the old target LCS in the linked Part   |
    +-----------------------------------------------+
	"""
	# this is the case for a link to a part coming from another document
	def splitExpressionLink( self, expr, parent ):
		# expr = ParentLink.Placement * ParentPart#LCS.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
		bad_EE = ( '', 'None', 'None' )
		if not expr:
			return bad_EE
		if parent == 'Parent Assembly':
			# we're attached to an LCS in the parent assembly
			# expr = LCS_in_the_assembly.Placement * AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
			( attLCS, separator, rest1 ) = expr.partition('.Placement * AttachmentOffset * ')
			( linkedPart, separator, rest2 ) = rest1.partition('#')
			( linkLCS, separator, rest3 ) = rest2.partition('.Placement ^ ')
			restFinal = rest3[0:2]
			attLink = parent
			attPart = 'None'
			#return ( restFinal, 'None', 'None', 'None', 'None', 'None')
		else:
			# we're attached to an LCS in a sister part
			# expr = ParentLink.Placement * ParentPart#LCS.Placement * AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
			( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
			( attPart,    separator, rest2 ) = rest1.partition('#')
			( attLCS,     separator, rest3 ) = rest2.partition('.Placement * AttachmentOffset * ')
			( linkedPart, separator, rest4 ) = rest3.partition('#')
			( linkLCS,    separator, rest5 ) = rest4.partition('.Placement ^ ')
			restFinal = rest5[0:2]
			#return ( restFinal, 'None', 'None', 'None', 'None', 'None')
		if restFinal=='-1' and attLink==parent :
			# wow, everything went according to plan
			# retval = ( expr, attPart, attLCS, constrLink, partLCS )
			retval = ( attLink, attLCS, linkLCS )
		else:
			# rats ! Didn't succeed in decoding the ExpressionEngine.
			# But still, if the decode is unsuccessful, put some text
			retval = bad_EE
		return retval


	# this is the case for a link to a part coming from the same document as the assembly
	def splitExpressionDoc( self, expr, parent ):
		# expr = ParentLink.Placement * LCS_parent.Placement * constr_linkName.AttachmentOffset * LCS_linkedPart.Placement ^ -1
		# expr = LCS_model.Placement * constr_linkName.AttachmentOffset * LCS_linkedPart.Placement ^ -1
		bad_EE = ( '', 'None', 'None' )
		if not expr:
			return bad_EE
		if parent == 'Parent Assembly':
			# we're attached to an LCS in the parent assembly
			# expr = LCS_in_the_assembly.Placement * constr_linkName.AttachmentOffset * LCS_linkedPart.Placement ^ -1
			( attLCS, separator, rest1 ) = expr.partition('.Placement * AttachmentOffset * ')
			( linkLCS, separator, rest2 ) = rest1.partition('.Placement ^ ')
			restFinal = rest2[0:2]
			attLink = parent
			attPart = 'None'
			#return ( restFinal, 'None', 'None', 'None', 'None', 'None')
		else:
			# we're attached to an LCS in a sister part
			# expr = ParentLink.Placement * LCS_parent.Placement * constr_linkName.AttachmentOffset * LCS_linkedPart.Placement ^ -1
			( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
			( attLCS,     separator, rest2 ) = rest1.partition('.Placement * AttachmentOffset * ')
			( linkLCS,    separator, rest3 ) = rest2.partition('.Placement ^ ')
			restFinal = rest3[0:2]
			#return ( restFinal, 'None', 'None', 'None', 'None', 'None')
		if restFinal=='-1' and attLink==parent :
			# wow, everything went according to plan
			# retval = ( expr, attPart, attLCS, constrLink, partLCS )
			retval = ( attLink, attLCS, linkLCS )
		else:
			# rats ! Didn't succeed in decoding the ExpressionEngine.
			# But still, if the decode is unsuccessful, put some text
			retval = bad_EE
		return retval

	"""
    +-----------------------------------------------+
    |           create the constr_LinkName          |
    |            for the App::Link object           |
    +-----------------------------------------------+
	"""
	def makeAsm4Properties( self ):
		if not hasattr(self.selectedLink,'AssemblyType'):
			self.selectedLink.addProperty( 'App::PropertyString', 'AssemblyType', 'Attachment' ).AssemblyType = 'Asm4EE'
			self.selectedLink.addProperty( 'App::PropertyString', 'AttachedBy', 'Attachment' )
			self.selectedLink.addProperty( 'App::PropertyString', 'AttachedTo', 'Attachment' )
			self.selectedLink.addProperty( 'App::PropertyPlacement', 'AttachmentOffset', 'Attachment' )
		return



	"""
    +-----------------------------------------------+
    | check that all necessary things are selected, |
    |   populate the expression with the selected   |
    |    elements, put them into the constraint     |
    |   and trigger the recomputation of the part   |
    +-----------------------------------------------+
	"""
	def onApply( self ):
		# get the instance to attach to:
		# it's either the top level assembly or a sister App::Link
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
			#a_LCS = self.attLCSlist.selectedItems()[0].text()
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
			expr = self.makeExpressionPart( a_Link, a_Part, a_LCS, l_Part, l_LCS )
			# this can be skipped when this method becomes stable
			self.expression.setText( expr )
			# add the Asm4 properties if it's a pure App::Link
			self.makeAsm4Properties()
			# store the part where we're attached to in the constraints object
			self.selectedLink.AttachedBy = '#'+l_LCS
			self.selectedLink.AttachedTo = a_Link+'#'+a_LCS
			# load the expression into the link's Expression Engine
			self.selectedLink.setExpression('Placement', expr )
			# recompute the object to apply the placement:
			self.selectedLink.recompute()
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
	def onParentList(self):
		# clear the LCS list
		self.attLCSlist.clear()
		self.attLCStable = []
		# clear the selection in the GUI window
		Gui.Selection.clearSelection()
		# the current text in the combo-box is the link's name...
		# parentName = self.attLCStable[ self.parentList.currentRow() ].Name
		# parentName = self.parentList.currentText()
		# ... or it's 'Parent Assembly' then the parent is the 'Model' root App::Part		
		if self.parentList.currentText() == 'Parent Assembly':
			parentName = 'Parent Assembly'
			parentPart = self.activeDoc.getObject( 'Model' )
			# we get the LCS directly in the root App::Part 'Model'
			self.attLCStable = self.getPartLCS( parentPart )
			self.parentDoc.setText( parentPart.Document.Name )
		# if something is selected
		elif self.parentList.currentIndex() > 1:
			parentName = self.asmParts[ self.parentList.currentIndex() ].Name
			parentPart = self.activeDoc.getObject( parentName )
			if parentPart:
				# we get the LCS from the linked part
				self.attLCStable = self.getPartLCS( parentPart.LinkedObject )
				self.parentDoc.setText( parentPart.LinkedObject.Document.Name )
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
	def onLCSclicked( self ):
		# clear the selection in the GUI window
		Gui.Selection.clearSelection()
		# LCS of the linked part
		if self.partLCSlist.selectedItems():
			#p_LCS = self.partLCSlist.selectedItems()[0].text()
			p_LCS = self.partLCStable[ self.partLCSlist.currentRow() ].Name
			Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedLink.Name+'.'+p_LCS+'.')
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
		return



	"""
    +-----------------------------------------------+
    |                     Cancel                    |
    |           restores the previous values        |
    +-----------------------------------------------+
	"""
	def onCancel(self):
		# restore previous values
		if self.old_AO:
			self.selectedLink.AttachmentOffset = self.old_AO
		if self.old_EE:
			self.selectedLink.setExpression( 'Placement', self.old_EE )
		self.selectedLink.recompute()
		self.close()



	"""
    +-----------------------------------------------+
    |                  Rotations                    |
    +-----------------------------------------------+
	"""
	def rotAxis( self, plaRotAxis ):
		constrAO = self.selectedLink.AttachmentOffset
		self.selectedLink.AttachmentOffset = plaRotAxis.multiply( constrAO )
		self.selectedLink.recompute()
		return

	def onRotX(self):
		rotX = App.Placement( App.Vector(0,0,0), App.Rotation( App.Vector(1,0,0), 90. ) )
		self.rotAxis(rotX)
		return

	def onRotY(self):
		rotY = App.Placement( App.Vector(0,0,0), App.Rotation( App.Vector(0,1,0), 90. ) )
		self.rotAxis(rotY)
		return

	def onRotZ(self):
		rotZ = App.Placement( App.Vector(0,0,0), App.Rotation( App.Vector(0,0,1), 90. ) )
		self.rotAxis(rotZ)
		return

	def onReset( self ):
		newPlacement = App.Placement( App.Vector(0,0,0), App.Rotation( App.Vector(0,0,1), 0.0 ) )
		self.selectedLink.AttachmentOffset = newPlacement
		self.selectedLink.recompute()
		return


	"""
    +-----------------------------------------------+
    |                      OK                       |
    |               accept and close                |
    +-----------------------------------------------+
	"""
	def onOK(self):
		self.onApply()
		self.close()



	"""
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
	"""
	def drawUI(self):
		# Our main window will be a QDialog
		self.setWindowTitle('Place linked Part')
		self.setWindowIcon( QtGui.QIcon( os.path.join( iconPath , 'FreeCad.svg' ) ) )
		self.setMinimumSize(550, 640)
		self.resize(550,640)
		self.setModal(False)
		# make this dialog stay above the others, always visible
		self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

		# Part, Left side
		#
		# Selected Link label
		self.linkLabel = QtGui.QLabel(self)
		self.linkLabel.setText("Selected Link :")
		self.linkLabel.move(10,20)
		# the name as seen in the tree of the selected link
		self.linkName = QtGui.QLineEdit(self)
		self.linkName.setReadOnly(True)
		self.linkName.setText( self.selectedLink.Name )
		self.linkName.setMinimumSize(200, 1)
		self.linkName.move(35,50)

		# label
		self.linkedLabel = QtGui.QLabel(self)
		self.linkedLabel.setText("Linked Document :")
		self.linkedLabel.move(10,90)
		# the document containing the linked object
		self.linkedDoc = QtGui.QLineEdit(self)
		self.linkedDoc.setReadOnly(True)
		self.linkedDoc.setText( self.selectedLink.LinkedObject.Document.Name )
		self.linkedDoc.setMinimumSize(200, 1)
		self.linkedDoc.move(35,120)

		# label
		self.labelLeft = QtGui.QLabel(self)
		self.labelLeft.setText("Select LCS in Part :")
		self.labelLeft.move(10,160)
		# The list of all LCS in the part is a QListWidget
		self.partLCSlist = QtGui.QListWidget(self)
		self.partLCSlist.move(10,190)
		self.partLCSlist.setMinimumSize(100, 250)
		self.partLCSlist.setToolTip('Select a coordinate system from the list')

		# Assembly, Right side
		#
		# label
		self.slectedLabel = QtGui.QLabel(self)
		self.slectedLabel.setText("Select Part to attach to:")
		self.slectedLabel.move(280,20)
		# combobox showing all available App::Link
		self.parentList = QtGui.QComboBox(self)
		self.parentList.move(280,50)
		self.parentList.setMinimumSize(250, 10)
		self.parentList.setMaximumSize(250, 50)
		self.parentList.setToolTip('Choose the part in which the attachment\ncoordinate system is to be found')
		# the parent assembly is hardcoded, and made the first real element
		self.parentList.addItem('Select attachment Parent')

		# label
		self.parentLabel = QtGui.QLabel(self)
		self.parentLabel.setText("Parent Document :")
		self.parentLabel.move(280,90)
		# the document containing the linked object
		self.parentDoc = QtGui.QLineEdit(self)
		self.parentDoc.setReadOnly(True)
		self.parentDoc.setMinimumSize(200, 1)
		self.parentDoc.move(305,120)
		# label
		self.labelRight = QtGui.QLabel(self)
		self.labelRight.setText("Select LCS in Parent :")
		self.labelRight.move(280,160)
		# The list of all attachment LCS in the assembly is a QListWidget
		# it is populated only when the parent combo-box is activated
		self.attLCSlist = QtGui.QListWidget(self)
		self.attLCSlist.move(280,190)
		self.attLCSlist.setMinimumSize(250, 250)
		self.attLCSlist.setToolTip('Select a coordinate system from the list')

		# Expression
		#
		# expression label
		self.labelExpression = QtGui.QLabel(self)
		self.labelExpression.setText("Expression Engine :")
		self.labelExpression.move(10,450)
		# Create a line that will contain full expression for the expression engine
		self.expression = QtGui.QLineEdit(self)
		self.expression.setMinimumSize(530, 0)
		self.expression.move(10, 480)

		# Buttons
		#
		# Reset button
		self.ResetButton = QtGui.QPushButton('Reset', self)
		self.ResetButton.setToolTip("Reset the AttachmentOffset of this Link")
		self.ResetButton.setAutoDefault(False)
		self.ResetButton.move(50, 530)
		# RotX button
		self.RotXButton = QtGui.QPushButton('Rot X', self)
		self.RotXButton.setToolTip("Rotate the instance around the X axis by 90deg")
		self.RotXButton.setAutoDefault(False)
		self.RotXButton.move(200, 530)
		# RotY button
		self.RotYButton = QtGui.QPushButton('Rot Y', self)
		self.RotYButton.setToolTip("Rotate the instance around the Y axis by 90deg")
		self.RotYButton.setAutoDefault(False)
		self.RotYButton.move(300, 530)
		# RotZ button
		self.RotZButton = QtGui.QPushButton('Rot Z', self)
		self.RotZButton.setToolTip("Rotate the instance around the Z axis by 90deg")
		self.RotZButton.setAutoDefault(False)
		self.RotZButton.move(400, 530)

		# Cancel button
		self.CancelButton = QtGui.QPushButton('Cancel', self)
		self.CancelButton.setToolTip("Restore initial parameters and close dialog")
		self.CancelButton.setAutoDefault(False)
		self.CancelButton.move(10, 600)
		# Apply button
		self.ApplyButton = QtGui.QPushButton('Show', self)
		self.ApplyButton.setToolTip("Previsualise the instance's placement \nwith the chosen parameters")
		self.ApplyButton.setAutoDefault(False)
		self.ApplyButton.move(230, 600)
		self.ApplyButton.setDefault(True)
		# OK button
		self.OKButton = QtGui.QPushButton('OK', self)
		self.OKButton.setToolTip("Apply current parameters and close dialog")
		self.OKButton.setAutoDefault(False)
		self.OKButton.move(460, 600)

		# Actions
		self.parentList.currentIndexChanged.connect( self.onParentList )
		#self.attLCSlist.itemClicked.connect( self.onLCSclicked )
		#self.partLCSlist.itemClicked.connect( self.onLCSclicked )
		self.ResetButton.clicked.connect( self.onReset )
		self.RotXButton.clicked.connect( self.onRotX )
		self.RotYButton.clicked.connect( self.onRotY )
		self.RotZButton.clicked.connect( self.onRotZ)
		self.CancelButton.clicked.connect(self.onCancel)
		self.ApplyButton.clicked.connect(self.onApply)
		self.OKButton.clicked.connect(self.onOK)



	"""
    +-----------------------------------------------+
    |                 initial check                 |
    +-----------------------------------------------+
	"""




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_placeLink', placeLink() )

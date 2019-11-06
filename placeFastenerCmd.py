#!/usr/bin/env python3
# coding: utf-8
#
# placeDatumCmd.py


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, math, re

from libAsm4 import *
from FastenerBase import FSBaseObject



"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class placeFastener( QtGui.QDialog ):
	"My tool object"


	def __init__(self):
		super(placeFastener,self).__init__()
		self.selectedFastener = []


	def GetResources(self):
		return {"MenuText": "Edit Attachment of a Fastener",
				"ToolTip": "Attach a Fastener to an external Part",
				"Pixmap" : os.path.join( iconPath , 'Asm4_mvFastener.svg')
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
		selection = self.GetSelection()
		if selection == None:
			self.close()
		else:
			self.selectedFastener = selection

		# check that the fastener is an Asm4 fastener
		if not hasattr(self.selectedFastener,'AssemblyType'):
			self.msgNotAsm4()
			return(False)
		if hasattr(self.selectedFastener,'AssemblyType'):
			if not self.selectedFastener.AssemblyType=='Asm4EE':
				self.msgNotAsm4()
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
		self.drawUI()
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
		# constrName has been checked at the beginning
		if not a_Link or not a_LCS :
			self.expression.setText( 'Problem in selections' )
		else:
			# don't forget the last '.' !!!
			# <<LinkName>>.Placement.multiply( <<LinkName>>.<<LCS.>>.Placement )
			# expr = '<<'+ a_Part +'>>.Placement.multiply( <<'+ a_Part +'>>.<<'+ a_LCS +'.>>.Placement )'
			expr = self.makeExpressionFastener( a_Link, a_Part, a_LCS )
			# this can be skipped when this method becomes stable
			self.expression.setText( expr )
			# store the part where we're attached to in the constraints object
			self.selectedFastener.AttachedTo = a_Link+'#'+a_LCS
			# load the built expression into the Expression field of the constraint
			self.selectedFastener.setExpression( 'Placement', expr )
			# recompute the object to apply the placement:
			self.selectedFastener.recompute()
			# highlight the selected LCS in its new position
			Gui.Selection.clearSelection()
			Gui.Selection.addSelection( self.activeDoc.Name, 'Model', self.selectedFastener.Name +'.')
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




	"""
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
	"""
	def drawUI(self):
		# Our main window will be a QDialog
		self.setWindowTitle('Attach a Fastener')
		self.setWindowIcon( QtGui.QIcon( os.path.join( iconPath , 'FreeCad.svg' ) ) )
		self.setMinimumSize(370, 690)
		self.resize(370,700)
		self.setModal(False)
		# make this dialog stay above the others, always visible
		self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

		# Part, Left side
		#
		# Selected Link label
		self.lcsLabel = QtGui.QLabel(self)
		self.lcsLabel.setText("Fastener :")
		self.lcsLabel.move(10,20)
		# the name as seen in the tree of the selected link
		self.lscName = QtGui.QLineEdit(self)
		self.lscName.setReadOnly(True)
		self.lscName.setText( self.selectedFastener.Label )
		self.lscName.setMinimumSize(240, 1)
		self.lscName.move(120,18)

		# label
		self.parentLabel = QtGui.QLabel(self)
		self.parentLabel.setText("Linked Part :")
		self.parentLabel.move(10,80)
		# combobox showing all available App::Link
		self.parentList = QtGui.QComboBox(self)
		self.parentList.move(10,120)
		self.parentList.setMinimumSize(350, 1)
		# initialize with an explanation
		self.parentList.addItem( 'Select linked Part' )

		# label
		self.labelRight = QtGui.QLabel(self)
		self.labelRight.setText("Select LCS in linked Part :")
		self.labelRight.move(10,180)
		# The list of all attachment LCS in the assembly is a QListWidget
		# it is populated only when the parent combo-box is activated
		self.attLCSlist = QtGui.QListWidget(self)
		self.attLCSlist.move(10,220)
		self.attLCSlist.setMinimumSize(350, 250)

		# Expression
		#
		# expression label
		self.labelExpression = QtGui.QLabel(self)
		self.labelExpression.setText("Expression Engine :")
		self.labelExpression.move(10,500)
		# Create a line that will contain full expression for the expression engine
		self.expression = QtGui.QLineEdit(self)
		self.expression.setMinimumSize(350, 0)
		self.expression.move(10, 540)

		# Buttons
		#
		# Cancel button
		self.CancelButton = QtGui.QPushButton('Cancel', self)
		self.CancelButton.setAutoDefault(False)
		self.CancelButton.move(10, 650)

		# Apply button
		self.ApplyButton = QtGui.QPushButton('Apply', self)
		self.ApplyButton.setAutoDefault(False)
		self.ApplyButton.move(150, 650)
		self.ApplyButton.setDefault(True)

		# OK button
		self.OKButton = QtGui.QPushButton('OK', self)
		self.OKButton.setAutoDefault(False)
		self.OKButton.move(280, 650)
		self.OKButton.setDefault(True)

		# Actions
		self.CancelButton.clicked.connect(self.onCancel)
		self.ApplyButton.clicked.connect(self.onApply)
		self.OKButton.clicked.connect(self.onOK)
		self.parentList.currentIndexChanged.connect( self.onParentList )
		self.attLCSlist.itemClicked.connect( self.onDatumClicked )


	"""
    +-----------------------------------------------+
    |                 initial check                 |
    +-----------------------------------------------+
	"""
	def checkSelectionLCS(self):
		# check that something is selected
		if not Gui.Selection.getSelection():
			msgBox = QtGui.QMessageBox()
			msgBox.setWindowTitle('Warning')
			msgBox.setIcon(QtGui.QMessageBox.Critical)
			msgBox.setText("Please select a linked part.")
			msgBox.exec_()
			return(False)
		# set the (first) selected object as global variable
		selectedObj = Gui.Selection.getSelection()[0]
		selectedType = selectedObj.TypeId
		# check that the selected object is a Datum CS or Point type
		if not (selectedType == 'PartDesign::CoordinateSystem' or selectedType == 'PartDesign::Point'):
			msgBox = QtGui.QMessageBox()
			msgBox.setWindowTitle('Warning')
			msgBox.setIcon(QtGui.QMessageBox.Critical)
			msgBox.setText("Please select a Datum Point or Coordinate System.")
			msgBox.exec_()
			return(False)
		# now we should be safe
		return( selectedObj )



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_placeFastener', placeFastener() )

#!/usr/bin/env python3
# coding: utf-8
#
# placeDatumCmd.py

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
class placeDatum( QtGui.QDialog ):
	"My tool object"


	def __init__(self):
		super(placeDatum,self).__init__()
		self.selectedDatum = []


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

		# check that we have selected a PartDesign::CoordinateSystem
		selection = self.checkSelectionDatum()
		if not selection:
			self.close()
		else:
			self.selectedDatum = selection


		# check if the datum object is already mapped to something
		# TODO : make a warning and confirmation dialog with "Cancel" and "OK" buttons
		# TODO : see confirmBox below
		if self.selectedDatum.MapMode != 'Deactivated':
			msgBox = QtGui.QMessageBox()
			msgBox.setWindowTitle('FreeCAD Warning')
			msgBox.setIcon(QtGui.QMessageBox.Warning)
			msgBox.setText("This Datum object is mapped to some geometry.")
			msgBox.setInformativeText("Attaching-it with Assembly4 will loose this mapping. Are you sure you want to proceed ?")
			msgBox.setStandardButtons(QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ok)
			msgBox.setEscapeButton(QtGui.QMessageBox.Cancel)
			msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
			retval = msgBox.exec_()
			# Cancel = 4194304
			# Ok = 1024
			if retval == 4194304:
				return


		# Now we can draw the UI
		self.drawUI()
		self.show()

		# We get all the App::Link parts in the assembly 
		self.asmParts = []
		# the first item is "Select linked Part" therefore we add an empty object
		self.asmParts.append( [] )
		# find all the linked parts in the assembly
		for obj in self.activeDoc.findObjects("App::Link"):
			if obj.LinkedObject.isDerivedFrom('App::Part'):
				# add it to our tree table if it's a link to an App::Part ...
				self.asmParts.append( obj )
				# ... and add to the drop-down combo box with the assembly tree's parts
				objIcon = obj.LinkedObject.ViewObject.Icon
				self.parentList.addItem( objIcon, obj.Name, obj)


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


		# find the oldPart in the part list...
		oldPart = self.parentList.findText( old_Parent )
		# if not found
		if oldPart == -1:
			self.parentList.setCurrentIndex( 0 )
		else:
			self.parentList.setCurrentIndex( oldPart )
			# this should have triggered self.getPartLCS() to fill the LCS list


		# find the oldLCS in the list of LCS of the linked part...
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
		if not a_Part or not a_LCS :
			self.expression.setText( 'Problem in selections' )
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
	def onParentList(self):
		# clear the LCS list
		self.attLCSlist.clear()
		self.attLCStable = []
		# clear the selection in the GUI window
		Gui.Selection.clearSelection()
		# the current text in the combo-box is the link's name...
		parentName = self.parentList.currentText()
		parentPart = self.activeDoc.getObject( parentName )
		if parentPart:
			# we get the LCS from the linked part
			self.attLCStable = self.getPartLCS( parentPart.LinkedObject )
			self.parentDoc.setText( parentPart.LinkedObject.Document.Name )
			# highlight the selected part:
			Gui.Selection.addSelection( parentPart.Document.Name, 'Model', parentPart.Name+'.' )
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
		# check that something is selected
		if self.attLCSlist.selectedItems():
			# get the linked part where the selected LCS is
			a_Part = self.parentList.currentText()
			# LCS in the linked part
			a_LCS = self.attLCStable[ self.attLCSlist.currentRow() ].Name
			# Gui.Selection.addSelection('asm_Test','Model','Lego_3001.LCS_h2x1.')
			# Gui.Selection.addSelection('asm_Test','Model','LCS_0.')
			Gui.Selection.addSelection( self.activeDoc.Name, 'Model', a_Part+'.'+a_LCS+'.')
		return



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
		self.close()


	"""
    +-----------------------------------------------+
    |            Cancel the confirmation            |
    +-----------------------------------------------+
	"""
	def onCancelConfirm(self):
		return(False)

	"""
    +-----------------------------------------------+
    |                   OK confirm                  |
    +-----------------------------------------------+
	"""
	def onOKConfirm(self):
		return(True)


	"""
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
	"""
	def drawUI(self):
		# Our main window will be a QDialog
		self.setWindowTitle('Attach a Coordinate System')
		self.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
		self.setMinimumSize(370, 570)
		self.resize(370,570)
		self.setModal(False)
		# make this dialog stay above the others, always visible
		self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

		# Part, Left side
		#
		# Selected Link label
		self.lcsLabel = QtGui.QLabel(self)
		self.lcsLabel.setText("Selected Datum :")
		self.lcsLabel.move(10,20)
		# the name as seen in the tree of the selected link
		self.lscName = QtGui.QLineEdit(self)
		self.lscName.setReadOnly(True)
		self.lscName.setText( self.selectedDatum.Name )
		self.lscName.setMinimumSize(150, 1)
		self.lscName.move(170,18)

		# combobox showing all available App::Link
		self.parentList = QtGui.QComboBox(self)
		self.parentList.move(10,80)
		self.parentList.setMinimumSize(350, 1)
		# initialize with an explanation
		self.parentList.addItem( 'Select linked Part' )

		# label
		self.parentLabel = QtGui.QLabel(self)
		self.parentLabel.setText("Linked Part :")
		self.parentLabel.move(10,120)
		# the document containing the linked object
		self.parentDoc = QtGui.QLineEdit(self)
		self.parentDoc.setReadOnly(True)
		self.parentDoc.setMinimumSize(300, 1)
		self.parentDoc.move(30,150)
		# label
		self.labelRight = QtGui.QLabel(self)
		self.labelRight.setText("Select LCS in linked Part :")
		self.labelRight.move(10,200)
		# The list of all attachment LCS in the assembly is a QListWidget
		# it is populated only when the parent combo-box is activated
		self.attLCSlist = QtGui.QListWidget(self)
		self.attLCSlist.move(10,240)
		self.attLCSlist.setMinimumSize(350, 200)

		# Expression
		#
		# expression label
		self.labelExpression = QtGui.QLabel(self)
		self.labelExpression.setText("Expression Engine :")
		self.labelExpression.move(10,450)
		# Create a line that will contain full expression for the expression engine
		self.expression = QtGui.QLineEdit(self)
		self.expression.setMinimumSize(350, 0)
		self.expression.move(10, 480)

		# Buttons
		#
		# Cancel button
		self.CancelButton = QtGui.QPushButton('Cancel', self)
		self.CancelButton.setAutoDefault(False)
		self.CancelButton.move(10, 530)

		# Apply button
		self.ApplyButton = QtGui.QPushButton('Apply', self)
		self.ApplyButton.setAutoDefault(False)
		self.ApplyButton.move(150, 530)
		self.ApplyButton.setDefault(True)

		# OK button
		self.OKButton = QtGui.QPushButton('OK', self)
		self.OKButton.setAutoDefault(False)
		self.OKButton.move(280, 530)
		self.OKButton.setDefault(True)

		# Actions
		self.CancelButton.clicked.connect(self.onCancel)
		self.ApplyButton.clicked.connect(self.onApply)
		self.OKButton.clicked.connect(self.onOK)
		self.parentList.currentIndexChanged.connect( self.onParentList )
		self.attLCSlist.itemClicked.connect( self.onDatumClicked )




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_placeDatum', placeDatum() )

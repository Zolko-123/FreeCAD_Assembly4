#!/usr/bin/env python3
# coding: utf-8
# 
# placeDatumCmd.py 


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
class importDatum( QtGui.QDialog ):
	"My tool object"


	def __init__(self):
		super(importDatum,self).__init__()
		self.datumTable = [ ]


	def GetResources(self):
		return {"MenuText": "Import Datum object",
				"ToolTip": "Import a Datum object from a linked Part",
				"Pixmap" : os.path.join( iconPath , 'Import_Datum.svg')
				}

	def IsActive(self):
		if App.ActiveDocument:
			# We only insert a link into an Asm4  Model
			if App.ActiveDocument.getObject('Model'):
				return(True)
			else:
				return(False)
		else:
			return(False) 


	"""  
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
	"""
	def Activated(self):
		
		# get the current active document to avoid errors if user changes tab
		self.activeDoc = App.activeDocument()

		# Now we can draw the UI
		self.drawUI()

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
		# Set the list to the first element
		self.parentList.setCurrentIndex( 0 )

		# check whether a Datum is already selected:
		targetDatum = self.getSelection()


		# Now we can show the UI
		self.show()



	"""
    +-----------------------------------------------+
    | check that all necessary things are selected, |
    |   populate the expression with the selected   |
    |    elements, put them into the constraint     |
    |   and trigger the recomputation of the part   |
    +-----------------------------------------------+
	"""
	def onApply(self):
		# get the name of the part where the datum to be copied is:
		#linkedPartName = self.parentList.currentText()

		# get the name of the part to attach to:
		# it's either the top level part name ('Model')
		# or the provided link's name.
		if self.parentList.currentIndex() > 0:
			parent = self.asmParts[ self.parentList.currentIndex() ]
			linkName = parent.Name
			linkedPart = parent.LinkedObject.Document.Name
		else:
			linkName = None
			linkedPart = None

		# check that something is selected in the datum list
		if self.datumList.selectedItems():
			datum = self.datumTable[ self.datumList.currentRow() ]
		else:
			datum = None

		# the name of the datum in the assembly, as per the dialog box
		setDatumName = self.datumName.text()
		
		# check that all of them have something in
		if not (linkName and linkedPart and datum and setDatumName):
			self.datumName.setText( 'Please select a Datum object' )
		else:
			# create the Datum
			if datum.TypeId == 'PartDesign::CoordinateSystem' or datum.TypeId == 'PartDesign::Point':
				#createdLink = self.activeDoc.getObject('Model').newObject( 'App::Link', linkName )
				createdDatum = App.activeDocument().getObject('Model').newObject( datum.TypeId, setDatumName )
				self.datumName.setText( '=> ' +createdDatum.Name )
			else:
				self.datumName.setText( 'unsupported Datum::Type' )
				return
			# build the expression to the linked datum (not the datumName in the assembly !)
			expr = makeExpressionDatum( linkName, linkedPart, datum.Name )
			# load the built expression into the Expression field of the datum created in the assembly
			self.activeDoc.getObject( createdDatum.Name ).setExpression( 'Placement', expr )
			# recompute the object to apply the placement:
			createdDatum.recompute()
			# clear the selection in the datum list
			self.datumList.setCurrentRow( -1 )
		return



	"""
    +-----------------------------------------------+
    |  check if there is already a datum selected   |
    +-----------------------------------------------+
	"""
	def getSelection(self):
		# if something is selected ...
		if Gui.Selection.getSelection():
			selectedObj = Gui.Selection.getSelection()[0]
			st = selectedObj.TypeId
			# ... and it's an App::Part:
			if st=='PartDesign::CoordinateSystem' or st=='PartDesign::Plane' or st=='PartDesign::Line' or st=='PartDesign::Point':
				return(selectedObj)
			else:
				return([])


	"""
    +-----------------------------------------------+
    |           get all the Datums in a Link        |
    +-----------------------------------------------+
	"""
	def getLinkDatums( self, link ):
		linkDatums = [ ]
		# parse all objects in the part (they return strings)
		for objName in link.getSubObjects():
			# get the proper objects
			# all object names end with a "." , this needs to be removed
			obj = link.getObject( objName[0:-1] )
			if obj.TypeId == 'PartDesign::CoordinateSystem' or obj.TypeId == 'PartDesign::Point':
				linkDatums.append( obj )
		return linkDatums



	"""
    +------------------------------------------------+
    |   fill the LCS list when changing the parent   |
    +------------------------------------------------+
	"""
	def onParentList(self):
		# clear the LCS list
		self.datumList.clear()
		self.datumName.setText( '' )
		# clear the selection in the GUI window
		Gui.Selection.clearSelection()
		# if something is selected in the linked parts list
		if self.parentList.currentIndex() > 0:
			parent = self.asmParts[ self.parentList.currentIndex() ]
			# we get all the datum objects from the linked part
			self.datumTable = self.getLinkDatums( parent.LinkedObject )
			self.parentDoc.setText( parent.LinkedObject.Document.Name )
			# highlight the selected part:
			Gui.Selection.addSelection( parent.Document.Name, 'Model', parent.Name+'.' )
		# build the datum objects names list
			for datum in self.datumTable:
				newItem = QtGui.QListWidgetItem()
				if datum.Name == datum.Label:
					newItem.setText( datum.Name )
				else:
					newItem.setText( datum.Label + ' (' +datum.Name+ ')' )
				newItem.setIcon( datum.ViewObject.Icon )
				self.datumList.addItem( newItem )
		return




	"""
    +-----------------------------------------------+
    |            An LCS has been clicked            |
    |     We pre-fill the datum's name text-box     |
    +-----------------------------------------------+
	"""
	def onDatumClicked( self ):
		# LCS in the parent
		datum = self.datumTable[ self.datumList.currentRow() ]
		#a_LCS = self.datumList.selectedItems()[0].text()
		# pre-fill the Datum name with the Label of the selected Datum
		self.datumName.setText( datum.Label )
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
		self.setWindowTitle('Import a Datum object')
		self.setWindowIcon( QtGui.QIcon( os.path.join( iconPath , 'FreeCad.svg' ) ) )
		self.setMinimumSize(400, 590)
		self.resize(400,590)
		self.setModal(False)
		# make this dialog stay above the others, always visible
		self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

		# label
		self.linkLabel = QtGui.QLabel(self)
		self.linkLabel.setText("Select a linked Part:")
		self.linkLabel.move(10,20)
		# combobox showing all available App::Link 
		self.parentList = QtGui.QComboBox(self)
		self.parentList.move(10,55)
		self.parentList.setMinimumSize(380, 1)
		# initialize with an explanation
		self.parentList.addItem( 'Please select ...' )

		# label
		self.parentLabel = QtGui.QLabel(self)
		self.parentLabel.setText("Parent Document (for info):")
		self.parentLabel.move(10,100)
		# the document containing the linked object
		self.parentDoc = QtGui.QLineEdit(self)
		self.parentDoc.setReadOnly(True)
		self.parentDoc.setMinimumSize(330, 1)
		self.parentDoc.move(30,130)
		# label
		self.labelRight = QtGui.QLabel(self)
		self.labelRight.setText("Select Datum object to import :")
		self.labelRight.move(10,180)
		# The list of all attachment LCS in the assembly is a QListWidget
		# it is populated only when the parent combo-box is activated
		self.datumList = QtGui.QListWidget(self)
		self.datumList.move(10,220)
		self.datumList.setMinimumSize(380, 220)

		# imported Link name
		self.datumLabel = QtGui.QLabel(self)
		self.datumLabel.setText("The imported Datum objects's name:")
		self.datumLabel.move(10,460)
		# the name as seen in the tree of the selected link
		self.datumName = QtGui.QLineEdit(self)
		self.datumName.setMinimumSize(380, 1)
		self.datumName.move(10,495)

		# Buttons
		#
		# Cancel button
		self.CancelButton = QtGui.QPushButton('Close', self)
		self.CancelButton.setAutoDefault(False)
		self.CancelButton.move(10, 550)

		# Apply button
		self.ApplyButton = QtGui.QPushButton('Import', self)
		self.ApplyButton.setAutoDefault(False)
		self.ApplyButton.move(310, 550)
		self.ApplyButton.setDefault(True)

		# OK button
		#self.OKButton = QtGui.QPushButton('OK', self)
		#self.OKButton.setAutoDefault(False)
		#self.OKButton.move(310, 550)
		#self.OKButton.setDefault(True)

		# Actions
		self.CancelButton.clicked.connect(self.onCancel)
		self.ApplyButton.clicked.connect(self.onApply)
		#self.OKButton.clicked.connect(self.onOK)
		self.parentList.currentIndexChanged.connect( self.onParentList )
		self.datumList.itemClicked.connect( self.onDatumClicked )



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_importDatum', importDatum() )

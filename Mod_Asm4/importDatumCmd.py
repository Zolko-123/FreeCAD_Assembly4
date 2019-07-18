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
		return {"MenuText": "Import Datum Point or Coordinate System",
				"ToolTip": "Import a Datum Point or Coordinate System from a linked Part",
				"Pixmap" : os.path.join( iconPath , 'ImportDatum.svg')
				}

	def IsActive(self):
		if App.ActiveDocument:
			# only activate if nothing is selected
			if Gui.Selection.getSelection():
				return False
			else:
				return True
		else:
			return False 


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
		self.show()

		# Search for all App::Links in the current document
		allLinkedParts = self.getAllLinkedParts()
		# Now populate the list with the (linked) sister parts
		for part in allLinkedParts:
			itemIcon = part.LinkedObject.ViewObject.Icon
			itemText = part.Name
			itemObj = part
			# fill the parent selection combo-box
			self.parentList.addItem( itemIcon, itemText, itemObj)
		# Set the list to the first element
		self.parentList.setCurrentIndex( 0 )



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
		linkedPartName = self.parentList.currentText()

		# check that something is selected in the datum list
		if self.datumList.selectedItems():
			# this is in the QWidgetList...
			listDatumName = self.datumList.currentItem().text()
			# ... and this is the table with the actual datum objects
			datumType = self.datumTable[ self.datumList.currentRow() ].TypeId
		else:
			listDatumName = None

		# the name of the datum in the assembly, as per the dialog box
		datumAsmName = self.datumName.text()
		
		# check that all of them have something in
		if not linkedPartName or not listDatumName or not datumType or not datumAsmName:
			self.datumName.setText( 'Please select a Datum object' )
		else:
			# create the Datum
			if datumType == 'PartDesign::CoordinateSystem':
				#createdLink = self.activeDoc.getObject('Model').newObject( 'App::Link', linkName )
				createdDatum = App.activeDocument().getObject('Model').newObject( 'PartDesign::CoordinateSystem', datumAsmName )
				self.datumName.setText( '=> ' +createdDatum.Name )
			elif datumType == 'PartDesign::Point':
				createdDatum = App.activeDocument().getObject('Model').newObject( 'PartDesign::Point', datumAsmName )
				self.datumName.setText( '=> ' +createdDatum.Name )
			else:
				self.datumName.setText( 'unsupported Datum::Type' )
				return
			# build the expression to the linked datum (not the datumName in the assembly !)
			expr = makeExpressionDatum( linkedPartName, listDatumName )
			# load the built expression into the Expression field of the datum created in the assembly
			self.activeDoc.getObject( createdDatum.Name ).setExpression( 'Placement', expr )
			# recompute the object to apply the placement:
			createdDatum.recompute()
			# highlight the selected LCS in its new position
			Gui.Selection.clearSelection()
			Gui.Selection.addSelection( self.activeDoc.Name, 'Model', createdDatum.Name +'.')
			# clear the selection in the datum list
			self.datumList.setCurrentRow( -1, QtGui.QItemSelectionModel.Clear )
		return



	"""
    +-----------------------------------------------+
    |   find all the linked parts in the assembly   |
    +-----------------------------------------------+
	"""
	def getAllLinkedParts(self):
		allLinkedParts = [ ]
		for obj in self.activeDoc.findObjects("App::Link"):
			# add it to our list if it's a link to an App::Part
			if obj.LinkedObject.isDerivedFrom('App::Part'):
				allLinkedParts.append( obj )
		return allLinkedParts


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
    +-----------------------------------------------+
    |   fill the LCS list when chaning the parent   |
    +-----------------------------------------------+
	"""
	def onParentList(self):
		# clear the LCS list
		self.datumList.clear()
		self.datumTable = [ ]
		self.datumName.setText( '' )
		# clear the selection in the GUI window
		Gui.Selection.clearSelection()
		# the current text in the combo-box is the link's name...
		parentName = self.parentList.currentText()
		# ... or it's 'Parent Assembly' then the parent is the 'Model' root App::Part
		if parentName =='Parent Assembly':
			Parent = self.activeDoc.getObject( 'Model' )
			# we get the LCS directly in the root App::Part 'Model'
			partDatums = self.getLinkDatums( Parent )
			self.parentDoc.setText( Parent.Document.Name )
		# a sister object is an App::Link
		# the .LinkedObject is an App::Part
		else:
			Parent = self.activeDoc.getObject( parentName )
			# we get the LCS from the linked part
			partDatums = self.getLinkDatums( Parent.LinkedObject )
			self.parentDoc.setText( Parent.LinkedObject.Document.Name )
			# highlight the selected part:
			Gui.Selection.addSelection( Parent.Document.Name, 'Model', Parent.Name+'.' )
		# build the list
		for datum in partDatums:
			newItem = QtGui.QListWidgetItem()
			newItem.setText( datum.Name )
			newItem.setIcon( datum.ViewObject.Icon )
			self.datumList.addItem( newItem )
			self.datumTable.append(datum)
		return


	"""
    +-----------------------------------------------+
    |  An LCS has been clicked in 1 of the 2 lists  |
    |              We higlight both LCS             |
    +-----------------------------------------------+
	"""
	def onDatumClicked( self ):
		# clear the selection in the GUI window
		Gui.Selection.clearSelection()
		# get the part where the selected LCS is
		a_Part = self.parentList.currentText()
		# LCS in the parent
		a_LCS = self.datumList.selectedItems()[0].text()
		# pre-fill the Datum name with the one selected
		self.datumName.setText( a_LCS )
		# parent assembly and sister part need a different treatment
		if a_Part == 'Parent Assembly':
			linkDot = ''
		else:
			linkDot = a_Part+'.'
		# Highlight the selected datum object
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
		self.setWindowTitle('Import a Datum object')
		self.setWindowIcon( QtGui.QIcon( os.path.join( iconPath , 'FreeCad.svg' ) ) )
		self.setMinimumSize(400, 600)
		self.resize(400,600)
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
		self.labelRight.setText("Select Datum in Link :")
		self.labelRight.move(10,180)
		# The list of all attachment LCS in the assembly is a QListWidget
		# it is populated only when the parent combo-box is activated
		self.datumList = QtGui.QListWidget(self)
		self.datumList.move(10,220)
		self.datumList.setMinimumSize(380, 220)

		# imported Link name
		self.datumLabel = QtGui.QLabel(self)
		self.datumLabel.setText("Enter the imported Datum's name:")
		self.datumLabel.move(10,460)
		# the name as seen in the tree of the selected link
		self.datumName = QtGui.QLineEdit(self)
		self.datumName.setMinimumSize(380, 1)
		self.datumName.move(10,495)

		# Buttons
		#
		# Cancel button
		self.CancelButton = QtGui.QPushButton('Cancel', self)
		self.CancelButton.setAutoDefault(False)
		self.CancelButton.move(10, 550)

		# Apply button
		self.ApplyButton = QtGui.QPushButton('Apply', self)
		self.ApplyButton.setAutoDefault(False)
		self.ApplyButton.move(164, 550)
		self.ApplyButton.setDefault(True)

		# OK button
		self.OKButton = QtGui.QPushButton('OK', self)
		self.OKButton.setAutoDefault(False)
		self.OKButton.move(310, 550)
		self.OKButton.setDefault(True)

		# Actions
		self.CancelButton.clicked.connect(self.onCancel)
		self.ApplyButton.clicked.connect(self.onApply)
		self.OKButton.clicked.connect(self.onOK)
		self.parentList.currentIndexChanged.connect( self.onParentList )
		self.datumList.itemClicked.connect( self.onDatumClicked )



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'importDatumCmd', importDatum() )

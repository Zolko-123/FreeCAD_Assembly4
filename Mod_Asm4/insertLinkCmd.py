#!/usr/bin/env python3
# coding: utf-8
# 
# Command template 

from PySide import QtGui, QtCore
from libAsm4 import *
import FreeCADGui as Gui
import FreeCAD as App
import Part, os, math, re


__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'icons' )



"""
    ╔═══════════════════════════════════════════════╗
    ║                  main class                   ║
    ╚═══════════════════════════════════════════════╝
"""
class insertLink( QtGui.QDialog ):
	"My tool object"

	def __init__(self):
		super(insertLink,self).__init__()

        
	def GetResources(self):
		return {"MenuText": "Insert an external Part",
				"Accel": "Ctrl+L",
				"ToolTip": "Insert an external Part from another open document",
				"Pixmap" : os.path.join( iconPath , 'LinkModel.svg')
				}


	def IsActive(self):
		if App.ActiveDocument == None:
			return False
		else:
			return True


	def Activated(self):
		# This function is executed when the command is activated
		
		# get the current active document to avoid errors if user changes tab
		self.activeDoc = App.activeDocument()
		
		# the GUI objects are defined later down
		self.drawUI()
		
		# Search for all App::Parts in all open documents
		self.getAllParts()
		
		# build the list
		for part in self.allParts:
			newItem = QtGui.QListWidgetItem()
			newItem.setText( part.Document.Name +" -> "+ part.Name )
			newItem.setIcon(part.ViewObject.Icon)
			self.partList.addItem(newItem)



	"""
    ╔═══════════════════════════════════════════════╗
    ║         the real stuff happens here           ║
    ╚═══════════════════════════════════════════════╝
	"""
	def onCreateLink(self):
		# parse the selected items 
		# TODO : there should only be 1
		model = []
		for selected in self.partList.selectedIndexes():
			# get the selected part
			model = self.allParts[ selected.row() ]
		# get the name of the link (as it should appear in the tree)
		linkName = self.linkNameInput.text()
		# only create link if there is a model and a name
		if model and linkName:
			# create the App::Link to the previously selected model
			createdLink = self.activeDoc.getObject('Model').newObject( 'App::Link', linkName )
			createdLink.LinkedObject = model
			# because of the unique naming principle of FreeCAD, 
			# the created object might been assigned a different name
			linkName = createdLink.Name
		
			# create an App::FeaturePython for that object in the Constraints group
			constrName = constraintPrefix + linkName
			# if it exists, delete it
			# TODO : a bit aggressive, no ?
			if self.activeDoc.getObject('Constraints').getObject( constrName ):
				self.activeDoc.removeObject( constrName )
			# create the constraints feature
			constrFeature = self.activeDoc.getObject('Constraints').newObject( 'App::FeaturePython', constrName )
			# get the App::FeaturePython itself
			# constrFeature = self.activeDoc.getObject( constrName )
			# store the name of the linked document (only for information)
			constrFeature.addProperty( 'App::PropertyString', 'LinkedFile' )
			constrFeature.LinkedFile = model.Document.Name
			# store the name of the App::Link this cosntraint refers-to
			constrFeature.addProperty( 'App::PropertyString', 'LinkName' )
			constrFeature.LinkName = linkName

			# Store the type of the constraint
			constrFeature.addProperty( 'App::PropertyString', 'ConstraintType' )
			constrFeature.ConstraintType = 'AttachmentByLCS'

			# the constraint and how the part is attached with it 
			# TODO : hard-coded, should do proper error checking
			attPart = 'Parent Assembly'
			attLCS  = 'LCS_0'
			linkLCS = 'LCS_0'

			# populate the App::Link's Expression Engine with this info
			expr = makeExpressionPart( attPart, attLCS, constrName, linkLCS )
			# put this expression into the Expression Engine of the link:
			createdLink.setExpression( 'Placement', expr )

			# add an App::Placement that will be the osffset between attachment and link LCS
			# the last 'Placement' means that the property will be placed in that group
			constrFeature.addProperty( 'App::PropertyPlacement', 'AttachmentOffset', 'Attachment' )
			# store the name of the part where the link is attached to
			constrFeature.addProperty( 'App::PropertyString', 'AttachedTo', 'Attachment' )
			constrFeature.AttachedTo = attPart
			# store the name of the LCS in the assembly where the link is attached to
			constrFeature.addProperty( 'App::PropertyString', 'AttachmentLCS', 'Attachment' )
			constrFeature.AttachmentLCS = attLCS
			# store the name of the LCS in the assembly where the link is attached to
			constrFeature.addProperty( 'App::PropertyString', 'LinkedPartLCS', 'Attachment' )
			constrFeature.LinkedPartLCS = linkLCS

			# update the link
			createdLink.recompute()
			
			# close the dialog UI...
			self.close()

			# ... and launch the placement of the inserted part
			Gui.Selection.clearSelection()
			Gui.Selection.addSelection( self.activeDoc.Name, 'Model', createdLink.Name+'.' )
			Gui.runCommand( 'placeLinkCmd' )

		# if still open, close the dialog UI
		self.close()



	"""
    ╔═══════════════════════════════════════════════╗
    ║                 some fonctions                ║
    ╚═══════════════════════════════════════════════╝
	"""
	def getAllParts(self):
		# get all App::Part from all open documents
		self.allParts = []
		for doc in App.listDocuments().values():
			if doc != self.activeDoc:
				parts = doc.findObjects("App::Part")
				# there might be more than 1 App::Part per document
				for obj in parts:
					self.allParts.append( obj )


	def onItemClicked( self, item ):
		for selected in self.partList.selectedIndexes():
			# get the selected part
			model = self.allParts[ selected.row() ]
            # set the text of the link to be made to the document where the part is in
			self.linkNameInput.setText(model.Document.Name)


	def onCancel(self):
		self.close()



	"""
    ╔═══════════════════════════════════════════════╗
    ║     defines the UI, only static elements      ║
    ╚═══════════════════════════════════════════════╝
	"""
	def drawUI(self):

		# Our main window is a QDialog
		self.setModal(False)
		# make this dialog stay above the others, always visible
		self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
		self.setWindowTitle('Insert a Model')
		self.setWindowIcon( QtGui.QIcon( os.path.join( iconPath , 'FreeCad.svg' ) ) )
		self.setMinimumSize(400, 500)
		self.resize(400,500)
		#self.Layout.addWidget(self.GUIwindow)

		# label
		self.labelMain = QtGui.QLabel(self)
		self.labelMain.setText("Select Part to be inserted :")
		self.labelMain.move(10,20)
		#self.Layout.addWidget(self.labelMain)
		
		# label
		self.labelLink = QtGui.QLabel(self)
		self.labelLink.setText("Enter a Name for the link :\n(Must be unique in the Model tree)")
		self.labelLink.move(10,350)

		# Create a line that will contain the name of the link (in the tree)
		self.linkNameInput = QtGui.QLineEdit(self)
		self.linkNameInput.setMinimumSize(380, 0)
		self.linkNameInput.move(10, 400)
	
		# The part list is a QListWidget
		self.partList = QtGui.QListWidget(self)
		self.partList.move(10,50)
		self.partList.setMinimumSize(380, 280)

		# Cancel button
		self.CancelButton = QtGui.QPushButton('Cancel', self)
		self.CancelButton.setAutoDefault(False)
		self.CancelButton.move(10, 460)

		# create Link button
		self.createLinkButton = QtGui.QPushButton('Insert part', self)
		self.createLinkButton.move(285, 460)
		self.createLinkButton.setDefault(True)

		# Actions
		self.CancelButton.clicked.connect(self.onCancel)
		self.createLinkButton.clicked.connect(self.onCreateLink)
		self.partList.itemClicked.connect( self.onItemClicked)

		# show the UI
		self.show()



# add the command to the workbench
Gui.addCommand( 'insertLinkCmd', insertLink() )


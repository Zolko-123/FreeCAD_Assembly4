#!/usr/bin/env python3
# coding: utf-8
# 
# newPointCmd.py 


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, math, re

from libAsm4 import *
from FastenerBase import FSBaseObject



"""
    +-----------------------------------------------+
    |        a class to create all fasteners        |
    |       from the Fasteners WB (ScrewMaker)      |
    +-----------------------------------------------+
    
	import ScrewMaker
	sm = ScrewMaker.Instance()
	screwObj = sm.createFastener('ISO7046', 'M6', '20', 'simple', shapeOnly=False)
"""

class insertFastener:
	"My tool object"
	def __init__(self, fastenerType):
		self.fastenerType = fastenerType
		# Screw:
		if self.fastenerType=='Screw':
			self.menutext = "Insert Screw"
			self.tooltip = "Insert a Screw in the Assembly"
			self.icon = os.path.join( iconPath , 'Asm4_Screw.svg')
			self.fastenerName = 'Screw'
		# Nut:
		elif self.fastenerType=='Nut':
			self.menutext = "Insert Nut"
			self.tooltip = "Insert a Nut in the Assembly"
			self.icon = os.path.join( iconPath , 'Asm4_Nut.svg')
			self.fastenerName = 'Nut'
		# Washer:
		elif self.fastenerType=='Washer':
			self.menutext = "Insert Washer"
			self.tooltip = "Insert a Washer in the Assembly"
			self.icon = os.path.join( iconPath , 'Asm4_Washer.svg')
			self.fastenerName = 'Washer'


	def GetResources(self):
		return {"MenuText": self.menutext,
				"ToolTip": self.tooltip,
				"Pixmap" : self.icon }


	def IsActive(self):
		if App.ActiveDocument:
			# if there is a Model object in the active document:
			if App.ActiveDocument.getObject('Model'):
				return(True)
		# if there is no reason to be active:
		return(False)


	def Activated(self):
		# check that we have somewhere to put our stuff
		self.asmDoc = App.ActiveDocument
		modelObj = self.checkModel()
		fastenerName = self.fastenerName+'_1'
		if modelObj:
			# this is a pre-made document in the Asm4 library, containing base Fastener objects
			fastenerDoc = self.getFastenersDoc()
			newFastener = modelObj.addObject(self.asmDoc.copyObject( fastenerDoc.getObject(self.fastenerType), True ))[0]

			# update the link ...
			newFastener.recompute()

			# ... and launch the placement of the inserted part
			Gui.Selection.clearSelection()
			Gui.Selection.addSelection( self.asmDoc.Name, 'Model', newFastener.Name+'.' )
			Gui.runCommand( 'Asm4_placeFastener' )



	def checkModel(self):
		# of nothing is selected ...
		if App.ActiveDocument.getObject('Model'):
			# ... but there is a Model:
			return App.ActiveDocument.getObject('Model')
		else:
			return(False)


	def getFastenersDoc(self):
		# list of all open documents in the sessions
		docList = App.listDocuments()
		for doc in docList:
			# if the Fastener's document is already open
			if doc == 'Fasteners':
				fastenersDoc = App.getDocument('Fasteners')
				return fastenersDoc
		# if the Fastsner document isn't yet open:
		fastenersDocPath = os.path.join( libPath , 'Fasteners.FCStd')
		# The document is opened in the background:
		fastenersDoc = App.openDocument( fastenersDocPath, hidden='True')
		# and we reset the original document as active:
		App.setActiveDocument( self.asmDoc.Name )
		return fastenersDoc




"""
    +-----------------------------------------------+
    |          a class to place fasteners           |
    |       from the Fasteners WB (ScrewMaker)      |
    +-----------------------------------------------+
"""
class moveFastener:
	def GetResources(self):
		icon = os.path.join( iconPath , 'Asm4_mvFastener.svg')
		return {'Pixmap'  : icon , # the name of a svg file available in the resources
				'MenuText': "Move fastner" ,
				'ToolTip' : "Move fastner to a new location"}
 
	def Activated(self):
		selObj = self.GetSelection()
		if selObj[0] == None:
			return
		selObj[0].baseObject = selObj[1]
		App.ActiveDocument.recompute()
		return
   
	def IsActive(self):
		selObj = self.GetSelection()
		if selObj[0] != None:
			return True
		return False

	def GetSelection(self):
		screwObj = None
		edgeObj = None
		for selObj in Gui.Selection.getSelectionEx():
			obj = selObj.Object
			if (hasattr(obj, 'Proxy') and isinstance(obj.Proxy, FSBaseObject)):
				screwObj = obj
			elif (len(selObj.SubObjects) == 1 and isinstance(selObj.SubObjects[0],Part.Edge)):
				edgeObj = (obj, [selObj.SubElementNames[0]])
		return (screwObj, edgeObj)
        
        
Gui.addCommand('Asm4_moveFastener', moveFastener())


"""
    +-----------------------------------------------+
    |       add the commands to the workbench       |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_insertScrew', insertFastener('Screw') )
Gui.addCommand( 'Asm4_insertNut',  insertFastener('Nut') )
Gui.addCommand( 'Asm4_insertWasher', insertFastener('Washer') )


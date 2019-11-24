#!/usr/bin/env python3
# coding: utf-8
# 
# newModelCmd.py 


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, math, re

from libAsm4 import *



class updateAssembly:
	"My tool object"

	def GetResources(self):
		return {"MenuText": "Solve and Update Assembly",
				"ToolTip": "Update Assembly",
				"Pixmap" : os.path.join( iconPath , 'Asm4_Update.svg')
				}

	def IsActive(self):
		if App.ActiveDocument:
			if App.ActiveDocument.getObject('Model'):
				return(True)
		return(False)



	"""
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
	"""
	def Activated(self):
		
		# get the current active document to avoid errors if user changes tab
		self.activeDoc = App.activeDocument()
		# find every objects in the assembly...
		for obj in self.activeDoc.Model.getSubObjects():
			# ... and update it
			objName = obj[0:-1]
			self.activeDoc.Model.getObject(objName).recompute()
		# finally uodate the entire document
		self.activeDoc.Model.recompute()
		self.activeDoc.recompute()


# add the command to the workbench
Gui.addCommand( 'Asm4_updateAssembly', updateAssembly() )

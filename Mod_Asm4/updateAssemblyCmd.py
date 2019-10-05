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
				"ToolTip": "Solve all constraints and update Assembly",
				"Pixmap" : os.path.join( iconPath , 'Solver.svg')
				}

	def IsActive(self):
		if App.ActiveDocument:
			return(True)
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

		# find all the linked parts in the assembly...
		for obj in self.activeDoc.findObjects():
			# ... and update it
			obj.recompute()
		# finally uodate the parent assembly
		self.activeDoc.Model.recompute()


# add the command to the workbench
Gui.addCommand( 'updateAssemblyCmd', updateAssembly() )

#!/usr/bin/env python3
# coding: utf-8
# 
# newBodyCmd.py 


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, math, re

from libAsm4 import *



class newBody:
	"My tool object"

	def GetResources(self):
		return {"MenuText": "Create a new Body",
				"Accel": "Ctrl+B",
				"ToolTip": "Create a new Body in the Model",
				"Pixmap" : os.path.join( iconPath , 'PartDesign_Body.svg')
				}

	def IsActive(self):
		if App.ActiveDocument:
			# is something selected ?
			if Gui.Selection.getSelection():
				return(False)
			else:
				return(True)
		else:
			return(False)

	def Activated(self):
		# do something here...
		bodyName = 'Body'
		text,ok = QtGui.QInputDialog.getText(None,'Create new Body in Model','Enter new Body name :                                        ', text = bodyName)
		if ok and text:
			App.activeDocument().getObject('Model').newObject( 'PartDesign::Body', text )


# add the command to the workbench
Gui.addCommand( 'newBodyCmd', newBody() )

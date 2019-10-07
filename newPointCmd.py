#!/usr/bin/env python3
# coding: utf-8
# 
# newPointCmd.py 


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, math, re

from libAsm4 import *



class newPoint:
	"My tool object"

	def GetResources(self):
		return {"MenuText": "Create a new Point",
				"ToolTip": "Create a new Datum Point in the Model",
				"Pixmap" : os.path.join( iconPath , 'Point.svg')
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
		# input dialog to ask the user the name of the LCS:
		pointName = 'Point_1'
		text,ok = QtGui.QInputDialog.getText(None,'Create new Datum Point','Enter Datum Point name :                              ', text = pointName)
		# if everything went well:
		if ok and text:
			App.activeDocument().getObject('Model').newObject( 'PartDesign::Point', text )


# add the command to the workbench
Gui.addCommand( 'newPointCmd', newPoint() )

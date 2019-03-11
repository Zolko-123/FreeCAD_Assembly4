#!/usr/bin/env python3
# coding: utf-8
# 
# Command template 

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, os, math, re

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Resources', 'icons' )


class newSketch:
	"My tool object"

	def GetResources(self):
		return {"MenuText": "Create a new Sketch",
				"ToolTip": "Create a new Sketch in the Model",
				"Pixmap" : os.path.join( iconPath , 'Model_NewSketch.svg')
				}

	def IsActive(self):
		if App.ActiveDocument == None:
			return False
		else:
			return True

	def Activated(self):
		# input dialog to ask the user the name of the Sketch:
		sketchName = 'Sketch_1'
		text,ok = QtGui.QInputDialog.getText(None,'Create new Sketch in Model','Enter Sketch name :                                        ', text = sketchName)
		if ok and text:
			App.activeDocument().getObject('Model').newObject( 'Sketcher::SketchObject', text )


# add the command to the workbench
Gui.addCommand( 'newSketchCmd', newSketch() )


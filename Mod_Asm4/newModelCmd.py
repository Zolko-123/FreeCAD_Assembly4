#!/usr/bin/env python3
# coding: utf-8
# 
# Command template 

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, os, math, re

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'icons' )


class newModel:
	"My tool object"

	def GetResources(self):
		return {"MenuText": "Create a new Model",
				"Accel": "Ctrl+M",
				"ToolTip": "Create a new Model App::Part",
				"Pixmap" : os.path.join( iconPath , 'Model.svg')
				}

	def IsActive(self):
		if App.ActiveDocument == None:
			return False
		else:
			return True

	def Activated(self):
		# create a new App::Part called 'Model'
		App.activeDocument().Tip = App.activeDocument().addObject('App::Part','Model')
		App.activeDocument().getObject('Model').newObject('App::DocumentObjectGroup','Constraints')
		App.activeDocument().getObject('Model').newObject('PartDesign::CoordinateSystem','LCS_0')


# add the command to the workbench
Gui.addCommand( 'newModelCmd', newModel() )

#!/usr/bin/env python3
# coding: utf-8
# 
# newModelCmd.py 


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, math, re

from libAsm4 import *



class newModel:
	"My tool object"

	def GetResources(self):
		return {"MenuText": "New Model",
				"Accel": "Ctrl+M",
				"ToolTip": "Create a new Assembly4 Model",
				"Pixmap" : os.path.join( iconPath , 'Asm4_Model.svg')
				}


	def IsActive(self):
		if App.ActiveDocument:
			return(True)
		else:
			return(False)


	def Activated(self):
		# get the current active document to avoid errors if user changes tab
		self.activeDoc = App.activeDocument()
		# check whether there is already Model in the document
		if not self.checkModel():
			# create a new App::Part called 'Model'
			model = self.activeDoc.addObject('App::Part','Model')
			model.newObject( 'App::DocumentObjectGroup', 'Constraints' )
			# model.newObject( 'App::FeaturePython', 'Variables' )
			lcs0 = model.newObject('PartDesign::CoordinateSystem','LCS_0')
			lcs0.Support = [(model.getObject('X_Axis'),'')]
			lcs0.MapMode = 'ObjectXY'
			lcs0.MapReversed = False
			model.recompute()
			self.activeDoc.recompute()


	def checkModel(self):
		# check wheter there is already a Model in the document
		# we don't check whether it's an App::Part or not
		# Returns True if there is an object called 'Model'
		if self.activeDoc.getObject('Model'):
			msgBox = QtGui.QMessageBox()
			msgBox.setWindowTitle('Warning')
			msgBox.setIcon(QtGui.QMessageBox.Critical)
			msgBox.setText("There is already a Model in this assembly.")
			msgBox.exec_()
			return(True)
		else:
			return(False)


# add the command to the workbench
Gui.addCommand( 'newModelCmd', newModel() )

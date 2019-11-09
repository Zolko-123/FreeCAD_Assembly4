#!/usr/bin/env python3
# coding: utf-8
# 
# newPartCmd.py 


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, math, re

from libAsm4 import *



class newPart:
	"My tool object"

	def GetResources(self):
		return {"MenuText": "New Part",
				"Accel": "Ctrl+P",
				"ToolTip": "Create a new Part in the document",
				"Pixmap" : os.path.join( iconPath , 'Asm4_Part.svg')
				}


	def IsActive(self):
		if App.ActiveDocument:
			return(True)
		else:
			return(False)


	def Activated(self):
		partName = 'Part'
		text,ok = QtGui.QInputDialog.getText(None,'Create new Part','Enter new Part name :                                        ', text = partName)
		if ok and text:
			# create Part
			part = App.ActiveDocument.addObject('App::Part',text)
			# If the 'Part' group exists, move it there:
			if App.ActiveDocument.getObject('Parts'):
				App.ActiveDocument.getObject('Parts').addObject(part)
			# add an LCS at the root of the Part, and attach it to the 'Origin'
			# this one starts with 1, because the LCS_0 is for the Model
			lcs1 = part.newObject('PartDesign::CoordinateSystem','LCS_1')
			lcs1.Support = [(part.Origin.OriginFeatures[0],'')]
			lcs1.MapMode = 'ObjectXY'
			lcs1.MapReversed = False
			# recompute
			part.recompute()
			App.ActiveDocument.recompute()



# add the command to the workbench
Gui.addCommand( 'Asm4_newPart', newPart() )

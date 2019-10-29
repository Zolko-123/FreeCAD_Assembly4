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
			part = App.ActiveDocument.addObject('App::Part',text)
			lcs0 = part.newObject('PartDesign::CoordinateSystem','LCS_0')
			lcs0.Support = [(part.Origin.OriginFeatures[0],'')]
			lcs0.MapMode = 'ObjectXY'
			lcs0.MapReversed = False
			part.recompute()
			App.ActiveDocument.recompute()



# add the command to the workbench
Gui.addCommand( 'newPartCmd', newPart() )

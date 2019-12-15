#!/usr/bin/env python3
# coding: utf-8
#
# FastenersDummy.py



import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part
#from FastenerBase import FSBaseObject

import libAsm4 as asm4




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
			self.icon = os.path.join( asm4.iconPath , 'Asm4_Screw.svg')
		# Nut:
		elif self.fastenerType=='Nut':
			self.menutext = "Insert Nut"
			self.icon = os.path.join( asm4.iconPath , 'Asm4_Nut.svg')
		# Washer:
		elif self.fastenerType=='Washer':
			self.menutext = "Insert Washer"
			self.icon = os.path.join( asm4.iconPath , 'Asm4_Washer.svg')


	def GetResources(self):
		return {"MenuText": self.menutext,
				"ToolTip": 'FastenersWorkbench is not installed.\n \nYou can install it with the FreeCAD AddonsManager:\nMenu Tools > Addon Manager > fasteners',
				"Pixmap" : self.icon }


	def IsActive(self):
		# it's the dummy, always inactive
		return False


	def Activated(self):
		return




"""
    +-----------------------------------------------+
    |             dummy  placeFastener              |
    +-----------------------------------------------+
"""
class placeFastener( QtGui.QDialog ):
	"My tool object"


	def __init__(self):
		super(placeFastener,self).__init__()


	def GetResources(self):
		return {"MenuText": "Edit Attachment of a Fastener",
				"ToolTip": 'FastenersWorkbench is not installed.\n \nYou can install it with the FreeCAD AddonsManager:\nMenu Tools > Addon Manager > fasteners',
				"Pixmap" : os.path.join( asm4.iconPath , 'Asm4_mvFastener.svg')
				}


	def IsActive(self):
		# it's a dummy, always inactive
		return False 


	def Activated(self):
		return



"""
    +-----------------------------------------------+
    |       add the commands to the workbench       |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_insertScrew', insertFastener('Screw') )
Gui.addCommand( 'Asm4_insertNut',  insertFastener('Nut') )
Gui.addCommand( 'Asm4_insertWasher', insertFastener('Washer') )

Gui.addCommand( 'Asm4_placeFastener', placeFastener() )

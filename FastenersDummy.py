#!/usr/bin/env python3
# coding: utf-8
#
# FastenersDummy.py



import os

import FreeCADGui as Gui
import FreeCAD as App

from BaseCommand import BaseCommand
from Asm4_Translate import translate
#from FastenerBase import FSBaseObject

import Asm4_libs as Asm4
from Asm4_Translate import translate




"""
    +-----------------------------------------------+
    |        a class to create all fasteners        |
    |       from the Fasteners WB (ScrewMaker)      |
    +-----------------------------------------------+

    import ScrewMaker
    sm = ScrewMaker.Instance()
    screwObj = sm.createFastener('ISO7046', 'M6', '20', 'simple', shapeOnly=False)
"""

class insertFastener(BaseCommand):
    "My tool object"
    def __init__(self, fastenerType):
        self.fastenerType = fastenerType
        self.tooltip = translate("Fasteners",
            "FastenersWorkbench is not installed.\n \n"
            "You can install it with the FreeCAD AddonsManager:\n"
            "Menu Tools > Addon Manager > fasteners")
        # Screw:
        if self.fastenerType=='Screw':
            self.menutext = translate("Fasteners", "Insert Screw")
            self.icon = os.path.join( Asm4.iconPath , 'Asm4_Screw.svg')
        # Nut:
        elif self.fastenerType=='Nut':
            self.menutext = translate("Fasteners", "Insert Nut")
            self.icon = os.path.join( Asm4.iconPath , 'Asm4_Nut.svg')
        # Washer:
        elif self.fastenerType=='Washer':
            self.menutext = translate("Fasteners", "Insert Washer")
            self.icon = os.path.join( Asm4.iconPath , 'Asm4_Washer.svg')
        # threaded rod:
        elif self.fastenerType=='ThreadedRod':
            self.menutext = translate("Fasteners", "Insert threaded rod")
            self.icon = os.path.join( Asm4.iconPath , 'Asm4_Rod.svg')


    def GetResources(self):
        return {"MenuText": self.menutext,
                "ToolTip": translate("Fasteners", "FastenersWorkbench is not installed.\n \nYou can install it with the FreeCAD AddonsManager:\nMenu Tools > Addon Manager > fasteners"),
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
class placeFastenerCmd(BaseCommand):
    "My tool object"

    def __init__(self):
        super(placeFastenerCmd,self).__init__()
        self.icon = os.path.join( Asm4.iconPath , 'Asm4_mvFastener.svg')
        self.menutext = translate("Fasteners", "Edit Attachment of a Fastener")
        self.tooltip = translate("Fasteners",
            "FastenersWorkbench is not installed.\n \n"
            "You can install it with the FreeCAD AddonsManager:\n"
            "Menu Tools > Addon Manager > fasteners")

    def IsActive(self):
        # it's a dummy, always inactive
        return False 

    def Activated(self):
        return
    
    
"""
    +-----------------------------------------------+
    |                dummy parameters               |
    +-----------------------------------------------+
"""
class changeFSparametersCmd(BaseCommand):
    def __init__(self):
        super(changeFSparametersCmd,self).__init__()
        self.icon = os.path.join( Asm4.iconPath , 'Asm4_FSparams.svg')
        self.menutext = translate("Fasteners", "Change Fastener parameters")
        self.tooltip = translate("Fasteners",
            "Change Fastener parameters")

    def IsActive(self):
        # it's a dummy, always inactive
        return False 

    def Activated(self):
        return



class cloneFastenersToAxesCmd(BaseCommand):
    def __init__(self):
        super(cloneFastenersToAxesCmd,self).__init__()
        self.pixmap

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
Gui.addCommand( 'Asm4_insertScrew',    insertFastener('Screw') )
Gui.addCommand( 'Asm4_insertNut',      insertFastener('Nut') )
Gui.addCommand( 'Asm4_insertWasher',   insertFastener('Washer') )
Gui.addCommand( 'Asm4_insertRod',      insertFastener('ThreadedRod') )
Gui.addCommand( 'Asm4_placeFastener',  placeFastenerCmd() )
Gui.addCommand( 'Asm4_cloneFastenersToAxes',  cloneFastenersToAxesCmd() )
Gui.addCommand( 'Asm4_FSparameters',   changeFSparametersCmd()  )

#!/usr/bin/env python3
# coding: utf-8
#
# FastenersDummy.py


import os

import FreeCADGui as Gui
import FreeCAD as App


import Asm4_libs as Asm4

QT_TRANSLATE_NOOP = App.Qt.QT_TRANSLATE_NOOP
translate = App.Qt.translate


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
        self.tooltip = translate(
            "Fasteners",
            "Fasteners Workbench is not installed.\n\n"
            "You can install it with the FreeCAD AddonsManager:\n"
            "Menu Tools > Addon Manager > fasteners",
        )
        # Screw:
        if self.fastenerType == "Screw":
            self.menutext = QT_TRANSLATE_NOOP("Asm4_insertScrew", "Insert Screw")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Screw.svg")
        # Nut:
        elif self.fastenerType == "Nut":
            self.menutext = QT_TRANSLATE_NOOP("Asm4_insertNut", "Insert Nut")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Nut.svg")
        # Washer:
        elif self.fastenerType == "Washer":
            self.menutext = QT_TRANSLATE_NOOP("Asm4_insertWasher", "Insert Washer")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Washer.svg")
        # threaded rod:
        elif self.fastenerType == "ThreadedRod":
            self.menutext = QT_TRANSLATE_NOOP("Asm4_insertRod", "Insert threaded rod")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Rod.svg")

    def GetResources(self):
        return {
            "MenuText": self.menutext,
            "ToolTip": self.tooltip,
            "Pixmap": self.icon,
        }

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


class placeFastenerCmd:
    "My tool object"

    def __init__(self):
        super(placeFastenerCmd, self).__init__()

    def GetResources(self):
        return {
            "MenuText": QT_TRANSLATE_NOOP("Asm4_placeFastener", "Edit Attachment of a Fastener"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "Asm4_placeFastener",
                "FastenersWorkbench is not installed.\n \n"
                "You can install it with the FreeCAD AddonsManager:\n"
                "Menu Tools > Addon Manager > fasteners",
            ),
            "Pixmap": os.path.join(Asm4.iconPath, "Asm4_mvFastener.svg"),
        }

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


class changeFSparametersCmd:
    def __init__(self):
        super(changeFSparametersCmd, self).__init__()

    def GetResources(self):
        return {
            "MenuText": QT_TRANSLATE_NOOP("Asm4_FSparameters", "Change Fastener parameters"),
            "ToolTip": QT_TRANSLATE_NOOP("Asm4_FSparameters", "Change Fastener parameters"),
            "Pixmap": os.path.join(Asm4.iconPath, "Asm4_FSparams.svg"),
        }

    def IsActive(self):
        # it's a dummy, always inactive
        return False

    def Activated(self):
        return


class cloneFastenersToAxesCmd:
    def __init__(self):
        super(cloneFastenersToAxesCmd, self).__init__()

    def GetResources(self):
        return {
            "MenuText": QT_TRANSLATE_NOOP("Asm4_cloneFastenersToAxes", "Clone Fastener to Axes"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "Asm4_cloneFastenersToAxes",
                "FastenersWorkbench is not installed.\n \n"
                "Youcan install it with the FreeCAD AddonsManager:\n"
                "Menu Tools > Addon Manager > fasteners",
            ),
            "Pixmap": os.path.join(Asm4.iconPath, "Asm4_cloneFasteners.svg"),
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
Gui.addCommand( 'Asm4_insertScrew',    insertFastener('Screw') )
Gui.addCommand( 'Asm4_insertNut',      insertFastener('Nut') )
Gui.addCommand( 'Asm4_insertWasher',   insertFastener('Washer') )
Gui.addCommand( 'Asm4_insertRod',      insertFastener('ThreadedRod') )
Gui.addCommand( 'Asm4_placeFastener',  placeFastenerCmd() )
Gui.addCommand( 'Asm4_cloneFastenersToAxes',  cloneFastenersToAxesCmd() )
Gui.addCommand( 'Asm4_FSparameters',   changeFSparametersCmd()  )

#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# HelpCmd.py

import os, webbrowser

import FreeCADGui as Gui

from . import Asm4_libs as Asm4
from .Asm4_Translate import translate


"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class Asm4Help():

    def GetResources(self):
        return {"MenuText": translate("Asm4_Help", "Help for Assembly4"),
                "ToolTip": translate("Asm4_Help", "Show basic usage for FreeCAD and Assembly4"),
                "Pixmap": os.path.join(Asm4.iconPath, 'Asm4_Help.svg')
                }

    def IsActive(self):
        return True


    def Activated(self):
        webbrowser.open('https://github.com/Zolko-123/FreeCAD_Assembly4/blob/master/INSTRUCTIONS.md')

"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_Help', Asm4Help() )

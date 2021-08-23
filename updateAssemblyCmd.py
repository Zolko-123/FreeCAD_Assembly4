#!/usr/bin/env python3
# coding: utf-8
# 
# updateAssembly.py 


import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import Asm4_libs as Asm4



class updateAssembly:

    def GetResources(self):
        return {"MenuText": "Solve and Update Assembly",
                "ToolTip": "Update Assembly",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_Solver.svg')
                }


    def IsActive(self):
        if App.ActiveDocument:
            return(True)
        return(False)


    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # find every Part in the document ...
        for obj in App.ActiveDocument.Objects:
            # ... and update it
            if obj.TypeId == 'App::Part':
                obj.recompute('True')
        #App.ActiveDocument.recompute()


# add the command to the workbench
Gui.addCommand( 'Asm4_updateAssembly', updateAssembly() )

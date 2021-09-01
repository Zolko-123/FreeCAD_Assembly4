#!/usr/bin/env python3
# coding: utf-8
#
# makeBinderCmd.py
# creates a SubShapeBinder at the root of the assembly


import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4




"""
    +-----------------------------------------------+
    |    a circular link array class and command    |
    +-----------------------------------------------+
"""
class makeShapeBinder():
    def __init__(self):
        pass

    def GetResources(self):
        tooltip  = "Create a reference to an external shape\n"
        tooltip += "This creates a SubShapeBinder of the selected shapes\n"
        tooltip += "(face, edge, point) in the root assembly\n"
        tooltip += "Only shapes belonging to the same part can be imported in a single step"
        iconFile = os.path.join( Asm4.iconPath, 'Asm4_shapeBinder.svg' )
        return {"MenuText": "Create a shape binder", "ToolTip":  tooltip, "Pixmap": iconFile }

    def IsActive(self):
        # only od this for assembly objects and all selected shapes must be in the same part
        if Asm4.getAssembly() and len(Gui.Selection.getSelection())==1:
            return True
        else:
            return False

    def Activated(self):
        rootAssembly = Asm4.getAssembly()
        # get the selected objects
        selEx = Gui.Selection.getSelectionEx("", 0)[0].SubElementNames
        (objName,dot,shape) = selEx[0].partition('.')
        # the first element should be the name of a child in the assembly
        if objName+'.' in rootAssembly.getSubObjects():
            # get the object where the selected shapes are
            obj = App.ActiveDocument.getObject(objName)
            # this is a double-check, should always be true at this point
            if obj:
                shape = (shape,)
                # we must remove the first name in each selEx element
                if len(selEx)>1:
                    # the first one (shape) has already been done
                    for sel in selEx[1:]:
                        (objName,dot,shp) = sel.partition('.')
                        shape += (shp,)
                # now create the SubShapeBinder
                binder  = rootAssembly.newObject('PartDesign::SubShapeBinder', 'ShapeBinder')
                binder.Support = [(obj, shape)]
                binder.MakeFace = False
                binder.ViewObject.LineColor = (0.,1.,0.)
                binder.recompute()                   



"""
    +-----------------------------------------------+
    |                 test functions                |
    +-----------------------------------------------+

binder = App.ActiveDocument.Model.newObject('PartDesign::SubShapeBinder', 'ShapeBinder')
support = [ (sel.Object, sel.SubElementNames) for sel in Gui.Selection.getSelectionEx('', 1) ]

"""




# add the command to the workbench
Gui.addCommand('Asm4_shapeBinder', makeShapeBinder())

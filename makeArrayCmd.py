#!/usr/bin/env python3
# coding: utf-8
#
# makeArrayCmd.py


import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4
from Asm4_objects import (
    PolarArray,
    ViewProviderArray,
    ExpressionArray,
    LinearArray,
    checkArraySelection,
)


'''
    +-----------------------------------------------+
    |    an expression link array class and command    |
    +-----------------------------------------------+
'''

class makeExpressionArray:
    '''Create a array of the selected object where the placement of each element
       is calculated using expressions and an ElementIndex property'
       Select an object to array and optionally an Axis that transformation will be related to.
       Without axis the transformations relates to the objects origin Z axis'''
    def __init__(self):
        pass

    def GetResources(self):
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_ExpressionArray.svg')
        return {
            'MenuText': 'Create a expression Array',
            'ToolTip': self.__doc__,
            'Pixmap': iconFile,
        }

    def IsActive(self):
        self.precheck = checkArraySelection()
        return self.precheck[0] is not None

    def _Activated(self, arrayClass):
        array = arrayClass.createFromSelection(*self.precheck)
        if array:
            objParent = self.precheck[1]
            array.recompute()
            objParent.recompute()
            App.ActiveDocument.recompute()

            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(
                objParent.Document.Name, objParent.Name, array.Name + '.'
            )

    def Activated(self):
        self._Activated(ExpressionArray)


'''
    +-----------------------------------------------+
    |    a circular link array class and command    |
    +-----------------------------------------------+
'''

class makeCircularArray(makeExpressionArray):
    '''Create a circular (polar) array of the selected object
       Select first an object and then the axis
       The axis can be either a datum Axis, an Origin axis or the axis of an LCS
       but it must be in the same container as the selected object'''
    def __init__(self):
        pass

    def GetResources(self):
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_PolarArray.svg')
        return {
            'MenuText': 'Create a circular Array',
            'ToolTip': self.__doc__,
            'Pixmap': iconFile,
        }

    def IsActive(self):
        self.precheck = checkArraySelection()
        return self.precheck[2] is not None

    def Activated(self):
        self._Activated(PolarArray)


'''
    +-----------------------------------------------+
    |    a linear link array class and command    |
    +-----------------------------------------------+
'''

class makeLinearArray(makeExpressionArray):
    '''Create a linear array of the selected object
        Select first an object and then an axis for the direction
        The axis can be either a datum Axis, an Origin axis or the axis of an LCS
        but it must be in the same container as the selected object'''
    def __init__(self):
        pass

    def GetResources(self):
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_LinkArray.svg')
        return {
            'MenuText': 'Create a linear Array',
            'ToolTip': self.__doc__,
            'Pixmap': iconFile,
        }

    def IsActive(self):
        self.precheck = checkArraySelection()
        return self.precheck[2] is not None

    def Activated(self):
        self._Activated(LinearArray)


'''
    +-----------------------------------------------+
    |                 test functions                |
    +-----------------------------------------------+
    
import makeArrayCmd
array = makeArrayCmd.makeMyLink(obj)
pls = []
for i in range(10):
    rot_i = App.Rotation(App.Vector(0,0,1), i*20)
    pla_i = App.Placement(App.Vector(0,0,0), rot_i)
    plaElmt = axePla * pla_i * axePla.inverse() * ballPla
    pls.append(plaElmt)

array.setPropertyStatus('PlacementList', '-Immutable')
array.PlacementList = pls


import makeArrayCmd
array = makeArrayCmd.makeCircularArray(obj,20)

'''


def makeMyLink(obj):
    # addObject() API is extended to accept extra parameters in order to
    # let the python object override the type of C++ view provider
    link = obj.Document.addObject(
        'App::FeaturePython', 'LinkArray', LinkArray(), None, True
    )
    # ViewProviderArray(link.ViewObject)
    link.setLink(obj)
    return link


def makeArray(obj, count):
    array = obj.Document.addObject(
        'App::FeaturePython', 'LinkArray', LinkArray(), None, True
    )
    ViewProviderArray(array.ViewObject)
    array.setLink(obj)
    array.ElementCount = count
    return array


# add the command to the workbench
Gui.addCommand('Asm4_linearArray', makeLinearArray())
Gui.addCommand('Asm4_circularArray', makeCircularArray())
Gui.addCommand('Asm4_expressionArray', makeExpressionArray())

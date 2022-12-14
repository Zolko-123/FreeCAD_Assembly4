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
    ViewProviderArray,
    ExpressionArray,
    CircularArray,
)


"""
    +-----------------------------------------------+
    |   an expression link array class and command  |
    +-----------------------------------------------+
"""


class makeExpressionArray:

    iconFileName = 'Asm4_ExpressionArray.svg'
    menuText = 'Create an expression driven Array'
    arrayType = 'Expression Array'
    namePrefix = 'XArray_'
    tooltip = """Create an array of the selected object where the placement of each element is calculated using expressions and an Index property.<br>
        Select a source object to array and optionally an Axis that transformation will be related to.<br>
        Without axis the transformations relates to the source objects origin.<br>
        <br>
        <b>Index</b> : Hidden but useful to reference in expressions on Element Placement. Increments for each element from <code>0</code> to <code>Count-1</code> during recompute. <br>
        <br>
        <b>Element Placement :</b> Set an expression for the entire placement or its sub-properties.<br>
           By opening Element Placement property in Tasks panel it is possible to set expressions for euler angles too.<br>
        <br>
        <b>Expressions examples</b><br>
        on Angle: <code>Index%2==0?30:-30</code><br>
        on Position.X: <code>Index*30</code>"""

    def GetResources(self):
        # print('self.iconFileName',self.iconFileName)
        iconFile = os.path.join(Asm4.iconPath, self.iconFileName)
        return {
            'MenuText': self.menuText,
            'ToolTip': self.tooltip,
            'Pixmap': iconFile,
        }

    def _getSelectionInfo(self):
        """Check axis and returns an Expression that calculates the axis placement.
           Fails if it contains more than two objects."""
        sourceObj = None
        objParent = None
        axisObj = None
        # Use the Z axis of Axis Object as default
        # Works well with datum axis and more
        xyz = 'Z'
        selection = Gui.Selection.getSelectionEx()
        # check that it's an Assembly4 'Model'
        if len(selection) in (1, 2):
            sourceObj = selection[0].Object
            objParent = sourceObj.getParentGeoFeatureGroup()
            if objParent.TypeId == 'PartDesign::Body':
                # Don't go there
                objParent = sourceObj = None
            elif len(selection) == 2:
                axisSel = selection[1]
                # both objects need to be in the same container or
                # the Placements will get screwed
                if objParent == axisSel.Object.getParentGeoFeatureGroup():
                    axisObj = axisSel.Object
                    # Origin axis goes along its placements X-axis ...
                    if axisSel.TypeName == 'App::Line':
                        xyz = 'X'
                    # Check if a sub element of a LCS is selected
                    elif axisSel.TypeName == 'PartDesign::CoordinateSystem':
                        if len(axisSel.SubElementNames) == 1:
                            xyz = axisSel.SubElementNames[0]
        # return what we have found
        self.selectionInfo = sourceObj, objParent, axisObj, xyz

    def IsActive(self):
        self._getSelectionInfo()
        return self.selectionInfo[0] is not None

    # Special property setup for this array type.
    def _setupProperties(self, obj):
        pass

    def Activated(self):
        srcObj, objParent, axisObj, xyz = self.selectionInfo
        if srcObj and objParent:
            obj = srcObj.Document.addObject(
                'Part::FeaturePython',
                self.namePrefix + srcObj.Name,
                ExpressionArray(),
                None,
                True,
            )
            obj.ArrayType = self.arrayType
            obj.setPropertyStatus('ArrayType', 'ReadOnly')
            obj.Label = self.namePrefix + srcObj.Label
            obj.Axis = axisObj
            obj.AxisXYZ = xyz
            # set the viewprovider
            ViewProviderArray(obj.ViewObject)
            # move array into common parent (if any)
            objParent.addObject(obj)
            # hide original object
            srcObj.Visibility = False
            # set array parameters
            obj.setLink(srcObj)
            # setup class specific properties
            self._setupProperties(obj)

            obj.recompute()
            objParent = self.selectionInfo[1]
            objParent.recompute()
            App.ActiveDocument.recompute()
            # select the new array
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj)



"""
    +-----------------------------------------------+
    |    a circular link array class and command    |
    +-----------------------------------------------+
"""

class makeCircularArray(makeExpressionArray):

    iconFileName = 'Asm4_PolarArray.svg'
    menuText = 'Create a circular array'
    arrayType = 'Circular Array'
    namePrefix = 'Circular_'
    tooltip = """Create a circular (polar) array of the selected object.<br>
       Select first an object and then the axis.<br>
       The axis can be any object with a Placement in the same container as the selected object.<br>
       It's alo possible to select a sub axis of a LCS.<br>
       <br>
       <b>Iterval Angle</b> : The angle between two subsequent elements.<br>
       To place the last element at for example 180°, set the expression to <code>180/(Count-1)</code>"""

    def IsActive(self):
        # print('IsActive XC')
        self._getSelectionInfo()
        return self.selectionInfo[2] is not None


    # Special property setup for this array type.
    def _setupProperties(self, obj):
        obj.Count = 6
        obj.addProperty('App::PropertyAngle',     'IntervalAngle',    'Array',
                        'Default is an expression to spread elements equal over the full angle')
        obj.setExpression('IntervalAngle',                    '360/Count')
        obj.setExpression('.ElementPlacement.Rotation.Angle', 'IntervalAngle * Index')
        obj.setPropertyStatus('ElementPlacement', 'Hidden')


"""
    +-----------------------------------------------+
    |    a linear link array class and command    |
    +-----------------------------------------------+
"""

class makeLinearArray(makeExpressionArray):

    iconFileName = 'Asm4_LinearArray.svg'
    menuText = 'Create a linear array'
    arrayType = 'Linear Array'
    namePrefix = 'Linear_'
    tooltip = """Create a linear array of the selected object<br>
       Select first an object and then an axis for the direction<br>
       The axis can be any object with a Placement in the same container as the selected object<br>
       It's alo possible to select a sub axis of a LCS<br>
       <br>
       <b>Linear Step</b> : The angle between two subsequent elements.<br>
       To place the last element 100 mm from first element, set the expression to <code>100mm/(Count-1)</code>"""


    def IsActive(self):
        # print('IsActive XL')
        self._getSelectionInfo()
        return self.selectionInfo[2] is not None


    # Special property setup for this array type.
    def _setupProperties(self, obj):
        obj.Count = 6
        obj.addProperty('App::PropertyDistance',  'LinearStep',       'Array',
                        'Distance between elements along Axis')
        obj.LinearStep = 10.0
        obj.setExpression('.ElementPlacement.Base.z',         'LinearStep * Index')
        obj.setPropertyStatus('ElementPlacement', 'Hidden')

"""
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


def makeMyLink(obj):
    # addObject() API is extended to accept extra parameters in order to 
    # let the python object override the type of C++ view provider
    link = obj.Document.addObject("App::FeaturePython",'LinkArray',LinkArray(),None,True)
    #ViewProviderArray(link.ViewObject)
    link.setLink(obj)
    return link


def makeArray(obj,count):
    array = obj.Document.addObject("App::FeaturePython",'LinkArray',LinkArray(),None,True)
    ViewProviderArray(array.ViewObject)
    array.setLink(obj)
    array.Count = count
    return array
    
"""


# add the command to the workbench
Gui.addCommand('Asm4_linearArray', makeLinearArray())
Gui.addCommand('Asm4_circularArray', makeCircularArray())
Gui.addCommand('Asm4_expressionArray', makeExpressionArray())

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
    findAxisPlacement,
)


"""
    +-----------------------------------------------+
    |   an expression link array class and command  |
    +-----------------------------------------------+
"""


class makeExpressionArray:

    iconFileName = 'Asm4_ExpressionArray.svg'
    menuText = App.Qt.translate("Asm4_makeArray", 'Create an expression driven Array')
    arrayType = 'Expression Array'
    namePrefix = 'XArray_'
    tooltip = App.Qt.translate("Asm4_makeArray", """Create an array of the selected object where the placement of each element is calculated using expressions and an Index property.<br>
        Select a source object to array and optionally an Axis that transformation will be related to.<br>
        Without axis the transformations relates to the source object internal Z axis.<br>
        <br>
        <b>Count :</b> The amount of elements in the array.<br>
        <b>Index :</b> Hidden but Placer use it in expressions to calculating the Placements. Increments for each element starting with 0.<br>
        <b>Placer :</b> Set an expression for the entire placement or its sub-properties.<br>
           By opening Placer property in Tasks panel it is possible to set expressions for euler angles too.<br>
        Also see tooltips in Property view
        """)

    def GetResources(self):
        iconFile = os.path.join(Asm4.iconPath, self.iconFileName)
        return {
            'MenuText': self.menuText,
            'ToolTip': self.tooltip,
            'Pixmap': iconFile,
        }

    def _cacheSelectionInfo(self):
        """Check axis and caches useful data for selected items.
           Selection must contain one or two objects."""
        sourceObj = None
        objParent = None
        axisObj = None
        sub = None
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
                    if findAxisPlacement(axisSel.Object, axisSel.SubElementNames):
                        axisObj = axisSel.Object
                        sub = axisSel.SubElementNames[0:1]
        # store what we have found
        self._selectionInfo = sourceObj, objParent, axisObj, sub

    def IsActive(self):
        self._cacheSelectionInfo()
        return self._selectionInfo[0] is not None

    # Special property setup for this array type.
    def _setupProperties(self, obj):
        pass

    def Activated(self):
        srcObj, objParent, axisObj, sub = self._selectionInfo
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
            if axisObj:
                obj.Axis = axisObj, sub
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
            # recompute
            obj.enforceRecompute()
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
    menuText = App.Qt.translate("Asm4_makeArray", 'Create a circular array')
    arrayType = 'Circular Array'
    namePrefix = 'Circular_'
    tooltip = App.Qt.translate("Asm4_makeArray", """<p>Create a circular (polar) array around an axis.
                Supported axis objects are axis or plane from an origin, datum line, LCS axes, straight line segments, arcs and circles</p>
                <p><b>Usage</b>: Select an object and the axis (hold CTRL key to select second object)</p>""")
 
    def IsActive(self):
        self._cacheSelectionInfo()
        return self._selectionInfo[2] is not None

    # Special property setup for this array type.
    def _setupProperties(self, obj):
        obj.Count = 6
        obj.addProperty('App::PropertyAngle', 'AngleStep', 'Array',
                        App.Qt.translate("Asm4_makeArray", 'The angle between two subsequent elements.\n'
                        'Expression to place the last element at 180°: <code>180/(Count-1)</code>'))
        obj.setExpression('AngleStep',              '360/Count')
        obj.setExpression('.Placer.Rotation.Angle', 'AngleStep * Index')
        obj.setPropertyStatus('Placer', 'Hidden')
        obj.setPropertyStatus('Scaler', 'Hidden')


"""
    +-----------------------------------------------+
    |    a linear link array class and command    |
    +-----------------------------------------------+
"""

class makeLinearArray(makeExpressionArray):

    iconFileName = 'Asm4_LinearArray.svg'
    menuText = App.Qt.translate("Asm4_makeArray", 'Create a linear array')
    arrayType = 'Linear Array'
    namePrefix = 'Linear_'
    tooltip = App.Qt.translate("Asm4_makeArray", """<p>Create a linear array along an axis.
                Supported axis objects are axis or plane from an origin, datum line, LCS axes, straight line segments, arcs and circles</p>
                <p><b>Usage</b>: Select an object and an axis for the direction (hold CTRL key to select second object)</p>""")

    def IsActive(self):
        self._cacheSelectionInfo()
        return self._selectionInfo[2] is not None

    # Special property setup for this array type.
    def _setupProperties(self, obj):
        obj.Count = 6
        obj.addProperty('App::PropertyDistance', 'LinearStep', 'Array',
                        App.Qt.translate("Asm4_makeArray", 'The length between two subsequent elements.\n'
                        'Expression to place the last element at 100 mm: 100mm/(Count-1)'))
        obj.LinearStep = 10.0
        obj.setExpression('.Placer.Base.z', 'LinearStep * Index')
        obj.setPropertyStatus('Placer', 'Hidden')
        obj.setPropertyStatus('Scaler', 'Hidden')


"""
    +-----------------------------------------------+
    |     a mirror link array class and command     |
    +-----------------------------------------------+
"""
class makeMirrorArray(makeExpressionArray):

    iconFileName = 'Asm4_Mirror.svg'
    menuText = App.Qt.translate("Asm4_makeArray", 'Create mirror')
    arrayType = 'Mirror Array'
    namePrefix = 'Mirror_'
    tooltip = App.Qt.translate("Asm4_makeArray", """<p>Create a mirror of a part.
                Supported axis objects are axis or plane from an origin, datum line, LCS axes, straight line segments, arcs and circles</p>
                <p><b>Usage</b>: Select a source object and a mirror plane or a normal to a plane (hold CTRL key to select second object)</p>""")

    def IsActive(self):
        self._cacheSelectionInfo()
        return self._selectionInfo[2] is not None

    # Special property setup for this array type.
    def _setupProperties(self, obj):
        obj.Count = 2
        obj.setExpression('Scaler', '1 - 2 * (Index % 2)')
        obj.setExpression('.Placer.Base', '.Placer.Rotation * minvert(.AxisPlacement) * .SourceObject.Placement.Base * -2 * (Index % 2)')
        obj.setExpression('.Placer.Rotation.Angle', '180 * (Index % 2)')
        obj.setPropertyStatus('Placer', 'Hidden')
        obj.setPropertyStatus('Scaler', 'Hidden')
        # https://github.com/Zolko-123/FreeCAD_Assembly4/issues/474
        Asm4.makeAsmProperties(obj)

        # Count property could be hidden but predefined Link properties goes back to
        # visible again after reopening document


# add the commands to the workbench
Gui.addCommand('Asm4_mirrorArray', makeMirrorArray())
Gui.addCommand('Asm4_linearArray', makeLinearArray())
Gui.addCommand('Asm4_circularArray', makeCircularArray())
Gui.addCommand('Asm4_expressionArray', makeExpressionArray())

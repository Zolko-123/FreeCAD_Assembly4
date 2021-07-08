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
from Asm4_objects import CircularArray, ViewProviderLink




"""
    +-----------------------------------------------+
    |    a circular link array class and command    |
    +-----------------------------------------------+
"""
class makeCircularArray():
    def __init__(self):
        pass

    def GetResources(self):
        return {"MenuText": "Create a circular Array",
                "ToolTip":  "Create a circular (polar) array of the selected object\n"+
                            "Select an object and a datum axis",
                "Pixmap": os.path.join( Asm4.iconPath, 'Asm4_PolarArray.svg' )
                }

    def IsActive(self):
        if App.ActiveDocument:
            # check correct selections
            selObj,selAxis = self.checkObjAndAxis()
            if selAxis:
                return (True)
        else:
            return (False)

    def Activated(self):
        # get the selected object
        selObj,selAxis = self.checkObjAndAxis()
        #FCC.PrintMessage('Selected '+selObj.Name+' of '+selObj.TypeId+' TypeId' )
        # check that object and axis belong to the same parent
        objParent  =  selObj.getParentGeoFeatureGroup()
        axisParent = selAxis.getParentGeoFeatureGroup()
        if not objParent==axisParent:
            msg = 'Please select an object and an axis belonging to the same part'
            Asm4.warningBox( msg)
        # if something valid has been returned:
        else:
            # create the array            
            array = selObj.Document.addObject(  "Part::FeaturePython",
                                                'Array_'+selObj.Name,
                                                CircularArray(),None,True)
            # move array into common parent (if any)
            if objParent:
                objParent.addObject(array)
            # set array parameters
            array.setLink(selObj)
            array.Label = 'Array_'+selObj.Label
            array.Axis = selAxis
            array.ArraySteps = "Full Circle"
            array.ElementCount = 5
            # hide original object
            #array.SourceObject.ViewObject.hide()
            selObj.Visibility = False
            # set the viewprovider
            ViewProviderLink( array.ViewObject )
            # update
            array.recompute()
            array.ElementCount = 7
            objParent.recompute()
            App.ActiveDocument.recompute()
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(objParent.Document.Name,objParent.Name,array.Name+'.')


    # check that 1 object (any) and 1 datum axis are selected
    def checkObjAndAxis(self):
        selObj  = None
        selAxis = None
        # check that it's an Assembly4 'Model'
        if len(Gui.Selection.getSelection())==2:
            obj1 = Gui.Selection.getSelection()[0]
            obj2 = Gui.Selection.getSelection()[1]
            # Only create arrays with a datum axis
            # TODO : extend it to cylinders and circles
            if obj2.TypeId == 'PartDesign::Line':
                selObj  = obj1
                selAxis = obj2
        # return what we have found
        return selObj,selAxis








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

"""

def makeMyLink(obj):
    # addObject() API is extended to accept extra parameters in order to 
    # let the python object override the type of C++ view provider
    link = obj.Document.addObject("App::FeaturePython",'LinkArray',LinkArray(),None,True)
    #ViewProviderLink(link.ViewObject)
    link.setLink(obj)
    return link


def makeArray(obj,count):
    array = obj.Document.addObject("App::FeaturePython",'LinkArray',LinkArray(),None,True)
    ViewProviderArray(array.ViewObject)
    array.setLink(obj)
    array.ElementCount = count
    return array



# add the command to the workbench
Gui.addCommand('Asm4_circularArray', makeCircularArray())

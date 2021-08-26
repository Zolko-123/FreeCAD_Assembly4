#!/usr/bin/env python3
# coding: utf-8
#
# Asm4_objects.py


import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4



"""
    +-----------------------------------------------+
    |           a general link array class          |
    +-----------------------------------------------+
    see: 
    https://github.com/realthunder/FreeCAD_assembly3/wiki/Link#app-namespace
"""
class LinkArray( object ):
    def __init__(self):
        self.Object = None
    
    def __getstate__(self):
        return

    def __setstate__(self,_state):
        return
    
    # new Python API called when the object is newly created
    def attach(self,obj):
        # the actual link property with a customized name
        obj.addProperty("App::PropertyLink","SourceObject",   " Link",'')
        # the placement with the default name
        #obj.addProperty("App::PropertyPlacement","Placement", " Link",'')
        # the following two properties are required to support link array
        obj.addProperty("App::PropertyBool",   "ShowElement", "Array",'')
        obj.addProperty("App::PropertyInteger","ElementCount","Array",
                        'Number of elements in the array (including the original)')
        # install the actual extension
        obj.addExtension('App::LinkExtensionPython')
        # initiate the extension
        self.linkSetup(obj)

    # helper function for both initialization (attach()) and restore (onDocumentRestored())
    def linkSetup(self,obj):
        assert getattr(obj,'Proxy',None)==self
        self.Object = obj
        # Tell LinkExtension which additional properties are available.
        # This information is not persistent, so the following function must 
        # be called by at both attach(), and restore()
        obj.configLinkProperty('ShowElement','ElementCount','Placement', LinkedObject='SourceObject')

    # new Python API for overriding C++ view provider of the binding object
    def getViewProviderName(self,_obj):
        return 'Gui::ViewProviderLinkPython'

    # Python API called on document restore
    def onDocumentRestored(self, obj):
        self.linkSetup(obj)

    # Execute when a property changes.
    def onChanged(self, obj, prop):
        # this allows to move individual elements by the user
        if prop == 'ShowElement':
            # set the PlacementList for user to change
            if hasattr(obj, 'PlacementList'):
                if obj.ShowElement:
                    obj.setPropertyStatus('PlacementList','-Immutable')
                else:
                    obj.setPropertyStatus('PlacementList', 'Immutable')
                    
            


"""
    +-----------------------------------------------+
    |                   ViewProvider                |
    +-----------------------------------------------+
"""
class ViewProviderLink(object):
    def __init__( self, vobj ):
        vobj.Proxy = self
        self.attach(vobj)

    def attach(self,vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    # Return objects that will be placed under it in the tree view.
    def claimChildren(self):
        if hasattr(self.Object, "ShowElement") and self.Object.ShowElement:
            return self.Object.ElementList
        elif hasattr(self.Object, "SourceObject"):
            return [self.Object.SourceObject]

    # return an icon corresponding to the array type
    def getIcon(self):
        iconFile = None
        if hasattr(self.Object,"ArrayType"):
            tp = self.Object.ArrayType
            if tp=='Circular Array':
                iconFile = os.path.join( Asm4.iconPath, 'Asm4_PolarArray.svg')
            if tp=='Linear Array':
                iconFile = os.path.join( Asm4.iconPath, 'Asm4_LinkArray.svg')
        if iconFile:
            return iconFile
                
    def __getstate__(self):
        return None

    def __setstate__(self, _state):
        return None
    


"""
    +-----------------------------------------------+
    |          a circular link array class          |
    +-----------------------------------------------+
"""
class CircularArray(LinkArray):

    #Set up the properties when the object is attached.
    def attach(self, obj):
        obj.addProperty("App::PropertyEnumeration", "ArraySteps",   "Array", '')
        obj.ArraySteps=['Full Circle','Interval']
        obj.addProperty("App::PropertyString",      "ArrayType",    "Array", '')
        obj.ArrayType = 'Circular Array'
        obj.setPropertyStatus('ArrayType', 'ReadOnly')
        obj.addProperty("App::PropertyString" ,     "Axis",         "Array", '')
        obj.addProperty("App::PropertyAngle",       "FullAngle",    "Array", '')
        # obj.FullAngle.setRange(-3600, 3600)
        obj.addProperty("App::PropertyAngle",       "IntervalAngle","Array", '')
        tooltip = 'Steps perpandicular to the array plane to form a spiral'
        obj.addProperty("App::PropertyFloat",       "LinearSteps",  "Array", tooltip)
        # do the attach of the LinkArray class
        super().attach(obj)

    # do the calculation of the elements' Placements
    def execute(self, obj):
        #FCC.PrintMessage('Triggered execute() ...')
        if not obj.SourceObject or not obj.Axis:
            return
        # Source Object
        sObj = obj.SourceObject
        parent = sObj.getParentGeoFeatureGroup()
        if not parent:
            return
        # get the datum axis 
        axisObj = parent.getObject(obj.Axis)
        if axisObj:
            axisPlacement = axisObj.Placement
        # if it's not, it might be the axis of an LCS, like 'LCS.Z'
        else:
            (lcs,dot,axis) = obj.Axis.partition('.')
            lcsObj = parent.getObject(lcs)
            # if lcs and axis are not empty
            if lcs and lcsObj and axis :
                if axis =='X':
                    axisPlacement = Asm4.rotY * lcsObj.Placement
                elif axis == 'Y':
                    axisPlacement = Asm4.rotX * lcsObj.Placement
                else:
                    axisPlacement = lcsObj.Placement
            else:
                FCC.PrintMessage('Axis not found\n')
                return    
        # calculate the number of instances
        if obj.ArraySteps=='Interval':
            fullAngle = (obj.ElementCount-1) * obj.IntervalAngle
            obj.setExpression("FullAngle","ElementCount * IntervalAngle")
        elif  obj.ArraySteps=='Full Circle':
            obj.setExpression("FullAngle",None)
            obj.FullAngle = 360
            obj.IntervalAngle = obj.FullAngle/obj.ElementCount
        plaList = []
        for i in range(obj.ElementCount):
            # calculate placement of element i
            rot_i = App.Rotation( App.Vector(0,0,1), i*obj.IntervalAngle)
            lin_i = App.Vector(0,0,i*obj.LinearSteps)
            pla_i = App.Placement( lin_i, rot_i )
            plaElmt = axisPlacement * pla_i * axisPlacement.inverse() * sObj.Placement
            plaList.append(plaElmt)
        if not getattr(obj, 'ShowElement', True) or obj.ElementCount != len(plaList):
            obj.setPropertyStatus('PlacementList', '-Immutable')
            obj.PlacementList = plaList
            obj.setPropertyStatus('PlacementList', 'Immutable')
        return False     # to call LinkExtension::execute()   <= is this rally needed ?

    #Execute when a property is changed.
    def onChanged(self, obj, prop):
        super().onChanged(obj, prop)
        # you cannot have less than 1 elements in an array
        if prop == 'ElementCount':
            if obj.ElementCount < 1:
                obj.ElementCount=1




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
    #ViewProviderLink(link.ViewObject)
    link.setLink(obj)
    return link


def makeArray(obj,count):
    array = obj.Document.addObject("App::FeaturePython",'LinkArray',LinkArray(),None,True)
    ViewProviderArray(array.ViewObject)
    array.setLink(obj)
    array.ElementCount = count
    return array

"""


#!/usr/bin/env python3
# coding: utf-8
#
# makeArray.py


import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import libAsm4 as Asm4



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
        obj.addProperty("App::PropertyPlacement","Placement", " Link",'')
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
    def __init__( self, vobj, iconfile=None ):
        self.Object = vobj.Object
        vobj.Proxy = self
        self.attach(vobj)
        self.customIcon = iconfile

    def attach(self,vobj):
        self.ViewObject = vobj

    # Return objects that will be placed under it in the tree view.
    def claimChildren(self):
        if hasattr(self.Object, "ShowElement") and self.Object.ShowElement:
            return self.Object.ElementList
        elif hasattr(self.Object, "SourceObject"):
            return [self.Object.SourceObject]

    def getIcon(self):
        return self.customIcon

    def __getstate__(self):
        return None

    def __setstate__(self, _state):
        return None
    


"""
    +-----------------------------------------------+
    |    a circular link array class and command    |
    +-----------------------------------------------+
"""
class CircularArray(LinkArray):

    #Set up the properties when the object is attached.
    def attach(self, obj):
        obj.addProperty("App::PropertyEnumeration", "ArraySteps",   "Array", '')
        obj.addProperty("App::PropertyLink" ,       "Axis",         "Array", '')
        obj.addProperty("App::PropertyAngle",       "FullAngle",    "Array", '')
        obj.addProperty("App::PropertyAngle",       "IntervalAngle","Array", '')
        obj.ArraySteps=['Full Circle','Interval']
        # do the attach of the LinkArray class
        super().attach(obj)

    # do the calculation of the elements' Placements
    def execute(self, obj):
        #FCC.PrintMessage('Triggered execute() ...')
        if not obj.SourceObject or not obj.Axis:
            return
        if obj.ArraySteps=='Interval':
            obj.FullAngle = (obj.ElementCount-1) * obj.IntervalAngle
        elif  obj.ArraySteps=='Full Circle':
            obj.FullAngle = 360
            obj.IntervalAngle = obj.FullAngle/obj.ElementCount
        # Source Object
        sobj = obj.SourceObject
        plaList = []
        for i in range(obj.ElementCount):
            # calculate placement of element i
            rot_i = App.Rotation( App.Vector(0,0,1), i*obj.IntervalAngle)
            pla_i = App.Placement(App.Vector(0,0,0), rot_i)
            plaElmt = obj.Axis.Placement * pla_i * obj.Axis.Placement.inverse() * sobj.Placement
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
        # you cannot have less than 1 elements in an array
        if prop == 'SourceObject':
            obj.Label = 'Array_'+obj.SourceObject.Label


class makeCircularArray():
    def __init__(self):
        self.iconFile = os.path.join( Asm4.iconPath, 'Asm4_PolarArray.svg' )

    def GetResources(self):
        return {"MenuText": "Create a circular Array",
                "ToolTip":  "Create a circular (polar) array of the selected object\n"+
                            "Select an object and a datum axis",
                "Pixmap": self.iconFile
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
            array = selObj.Document.addObject("App::FeaturePython",
                                              'Array_'+selObj.Label,
                                              CircularArray(),None,True)
            # set array parameters
            array.setLink(selObj)
            array.Axis = selAxis
            array.ArraySteps = "Full Circle"
            array.ElementCount = 5
            # set the viewprovider
            ViewProviderLink( array.ViewObject, self.iconFile )
            # move array into common parent (if any)
            if objParent:
                objParent.addObject(array)
            # hide original object
            #array.SourceObject.ViewObject.hide()
            selObj.Visibility = False
            # update
            array.recompute()
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

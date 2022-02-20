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
    |              a variant link class             |
    +-----------------------------------------------+

see:
    https://forum.freecadweb.org/viewtopic.php?f=10&t=38970&start=50#p343116
    https://forum.freecadweb.org/viewtopic.php?f=22&t=42331

asmDoc = App.ActiveDocument
tmpDoc = App.newDocument('TmpDoc', hidden=True, temp=True)
App.setActiveDocument(asmDoc.Name)
beamCopy = tmpDoc.copyObject( asmDoc.getObject( 'Beam'), 'True' )
asmDoc.getObject('Beam_2').LinkedObject = beamCopy
asmDoc.getObject('Beam_3').LinkedObject = beamCopy
asmDoc.getObject('Beam_4').LinkedObject = beamCopy
copyVars = beamCopy.getObject('Variables')
copyVars.Length=50
copyVars.Size=50
asmDoc.recompute()

from Asm4_objects import VariantLink
var = App.ActiveDocument.addObject("Part::FeaturePython", 'varLink', VariantLink(),None,True)
tmpDoc = App.newDocument( 'TmpDoc', hidden=True, temp=True )
tmpDoc.addObject('App::Part
"""
class VariantLink( object ):
    def __init__(self):
        FCC.PrintMessage('Initialising ...\n')
        self.Object = None
    
    def __getstate__(self):
        return

    def __setstate__(self,_state):
        return
    
    # new Python API for overriding C++ view provider of the binding object
    def getViewProviderName(self,_obj):
        return 'Gui::ViewProviderLinkPython'

    # returns True only of the object has been successfully restored
    def isLoaded(self,obj):
        if hasattr(obj,'SourceObject') and obj.SourceObject is not None:
            return obj.SourceObject.isValid()
        return False

    # triggered in recompute(), update variant parameters
    def execute(self, obj):
        # should be a copy of the one of the SourceObject
        if obj.LinkedObject is not None and obj.LinkedObject.isValid():
            # get the Variables container of the LinkedObject
            variantVariables = obj.LinkedObject.getObject('Variables')
            if variantVariables is not None:
                # parse all variant variables and apply them to the linked object
                variantProps = obj.PropertiesList
                sourceProps = variantVariables.PropertiesList
                for prop in variantProps:
                    if prop in sourceProps and obj.getGroupOfProperty(prop) == 'VariantVariables':
                        setattr( variantVariables, prop, getattr( obj, prop ))
                variantVariables.recompute()
                obj.LinkedObject.recompute()
                obj.LinkedObject.Document.recompute()
        elif obj.SourceObject is not None and obj.SourceObject.isValid():
            self.makeVarLink(obj)
            self.fillVarProperties(obj)

    # do the actual variant: this creates a new hidden temporary document
    # deep-copies the source object there, and re-links the copy
    def makeVarLink(self, obj):
        # create a new, empty, hidden, temporary document
        tmpDocName = 'varTmpDoc_'
        i = 1
        while i<100 and tmpDocName+str(i) in App.listDocuments():
            i += 1
        if i<100:
            tmpDocName = 'varTmpDoc_'+str(i)
            tmpDoc = App.newDocument( tmpDocName, hidden=True, temp=True )
            # deep-copy the source object and link it back
            obj.LinkedObject = tmpDoc.copyObject( obj.SourceObject, True )
        else:
            FCC.PrintWarning('100 temporary variant documents are already in use, not creating a new one.\n')
        return

    # Python API called after the document is restored
    def onDocumentRestored(self, obj):
        # this sets up the link infrastructure
        self.linkSetup(obj)
        # restore the variant
        if obj.SourceObject is not None and obj.SourceObject.isValid():
            obj.LinkedObject = obj.SourceObject
            # update obj
            self.makeVarLink(obj)
            self.fillVarProperties(obj)
            self.restorePlacementEE(obj)
            self.execute(obj)
            obj.Type='Asm4::VariantLink'
            obj.recompute()

    # make the Asm4EE according to the properties stored in the varLink object
    # this is necessary because the placement refers to the LinkedObject's document *name*,
    # which is a temporary document, and this document may be different on restore
    def restorePlacementEE( self, obj ):
        # only attempt this on fully restored objects
        if self.isLoaded(obj) and obj.LinkedObject.isValid():
            # if it's indeed an Asm4 object
            # LCS_Origin.Placement * AttachmentOffset * varTmpDoc_3#LCS_Origin.Placement ^ -1
            if Asm4.isAsm4EE(obj) and ( obj.SolverId=='Asm4EE' or obj.SolverId=='Placement::ExpressionEngine' ):
                # retrieve the info from the object's properties
                (a_Link,sep,a_LCS) = obj.AttachedTo.partition('#')
                if a_Link=='Parent Assembly':
                    a_Part = None
                else:
                    a_Part = obj.Document.getObject(a_Link).LinkedObject.Document.Name
                l_Part = obj.LinkedObject.Document.Name
                l_LCS = obj.AttachedBy[1:]
                # build the expression
                expr = Asm4.makeExpressionPart( a_Link, a_Part, a_LCS, l_Part, l_LCS )
                # set the expression
                obj.setExpression('Placement', expr )

    # find all 'Variables' in the original part, 
    # and create corresponding properties in the variant
    def fillVarProperties(self,obj):
        variables = obj.SourceObject.getObject('Variables')
        if variables is None:
            FCC.PrintVarning('No \"Variables\" container in source object\n')
        else: 
            for prop in variables.PropertiesList:
                # fetch all properties in the Variables group
                if variables.getGroupOfProperty(prop) == 'Variables':
                    # if the corresponding variables doesn't yet exist
                    if not hasattr(obj,prop):
                        # create a same property with same value in the variant
                        propType = variables.getTypeIdOfProperty(prop)
                        obj.addProperty(propType,prop,'VariantVariables')
                        setattr( obj, prop, getattr( variables, prop ))

    # new Python API called when the object is newly created
    def attach(self,obj):
        FCC.PrintMessage('Attaching VariantLink ...\n')
        # the source object for the variant object
        obj.addProperty("App::PropertyXLink","SourceObject"," Link",
                        'Original object from which this variant is derived')
        # the actual linked object property with a customized name
        obj.addProperty("App::PropertyXLink","LinkedObject"," Link",
                        'Link to the modified object')
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
        obj.configLinkProperty( 'Placement', LinkedObject='LinkedObject')
        # hide the scale properties
        if hasattr( obj, 'Scale' ):
            obj.setPropertyStatus('Scale', 'Hidden')
        if hasattr( obj, 'ScaleList' ):
            obj.setPropertyStatus('ScaleList', 'Hidden')
        return

    # Execute when a property changes.
    def onChanged(self, obj, prop):
        # check that the SourceObject is valid, this should ensure
        # that the object has been successfully loaded
        if self.isLoaded(obj):
            # this changes the available variant parameters
            if prop == 'SourceObject':
                pass
                '''
                if obj.LinkedObject is None:
                    FCC.PrintMessage('Creating new variant ...\n')
                    self.makeVarLink(obj)
                    self.fillVarProperties(obj)
                elif hasattr(obj.LinkedObject,'Document'):
                    FCC.PrintMessage('Updating variant ...\n')
                    oldVarDoc = obj.LinkedObject.Document
                # setting the LinkedObject to the SourceObject temporarily
                # obj.LinkedObject = obj.SourceObject
                # self.makeVariant(obj)
                '''

    # this is never actually called
    def onLostLinkToObject(self, obj):
        FCC.PrintMessage('Triggered onLostLinkToObject() in VariantLink\n')
        obj.LinkedObject = obj.SourceObject
        return

    # this is never actually called
    def setupObject(self, obj):
        FCC.PrintMessage('Triggered by setupObject() in VariantLink\n')
        obj.LinkedObject = obj.SourceObject





"""
    +-----------------------------------------------+
    |           a general link array class          |
    +-----------------------------------------------+
    see: 
    https://github.com/realthunder/FreeCAD_assembly3/wiki/Link#app-namespace

from Asm4_objects import LinkArray
la = App.ActiveDocument.addObject("Part::FeaturePython", 'linkArray', LinkArray(),None,True)
"""
class LinkArray( object ):
    def __init__(self):
        self.Object = None
    
    def __getstate__(self):
        return

    def __setstate__(self,_state):
        return
    
    # new Python API for overriding C++ view provider of the binding object
    def getViewProviderName(self,_obj):
        return 'Gui::ViewProviderLinkPython'

    # Python API called on document restore
    def onDocumentRestored(self, obj):
        self.linkSetup(obj)

    # new Python API called when the object is newly created
    def attach(self,obj):
        # the actual link property with a customized name
        obj.addProperty("App::PropertyLink", "SourceObject", " Link",'')
        # the following two properties are required to support link array
        obj.addProperty("App::PropertyBool", "ShowElement", "Array",
                        'Shows each individual element')
        obj.addProperty("App::PropertyInteger","ElementCount","Array",
                        'Number of elements in the array (including the original)')
        obj.ElementCount=1
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
        # hide the scale properties
        if hasattr( obj, 'Scale' ):
            obj.setPropertyStatus('Scale', 'Hidden')
        if hasattr( obj, 'ScaleList' ):
            obj.setPropertyStatus('ScaleList', 'Hidden')

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
        # you cannot have less than 1 elements in an array
        elif prop == 'ElementCount':
            if obj.ElementCount < 1:
                obj.ElementCount=1




"""
    +-----------------------------------------------+
    |                   ViewProvider                |
    +-----------------------------------------------+
"""
class ViewProviderArray(object):
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
        tooltip = 'Steps perpendicular to the array plane to form a spiral'
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

    '''
    #Execute when a property is changed.
    def onChanged(self, obj, prop):
        super().onChanged(obj, prop)
        # you cannot have less than 1 elements in an array
        if prop == 'ElementCount':
            if obj.ElementCount < 1:
                obj.ElementCount=1
    '''



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
    link.setLink(obj)
    return link


def makeArray(obj,count):
    array = obj.Document.addObject("App::FeaturePython",'LinkArray',LinkArray(),None,True)
    ViewProviderArray(array.ViewObject)
    array.setLink(obj)
    array.ElementCount = count
    return array

"""


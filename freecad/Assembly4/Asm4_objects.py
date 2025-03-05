#!/usr/bin/env python3
# coding: utf-8
#
# Asm4_objects.py
# 
# LGPL
# Copyright HUBERT Zoltán



import os
from math import radians
import re

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

from . import Asm4_libs as Asm4



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

from .Asm4_objects import VariantLink
var = App.ActiveDocument.addObject("Part::FeaturePython", 'varLink', VariantLink(),None,True)
tmpDoc = App.newDocument( 'TmpDoc', hidden=True, temp=True )
tmpDoc.addObject('App::Part
"""
class VariantLink( object ):
    def __init__(self):
        FCC.PrintMessage('Initialising variantLink ...\n')
        self.Object = None
    # for Python version ≤3.10
    def __getstate__(self):
        return

    def __setstate__(self,_state):
        return
    # for Python version ≥3.11
    def dumps(self):
        return

    def loads(self,_state):
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
            obj.Type='Asm4::VariantLink'
            self.restorePlacementEE(obj)
            self.execute(obj)
            ViewProviderVariant(obj.ViewObject)
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
        # the actual linked object property with a customized name
        obj.addProperty("App::PropertyString","Type")

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

    # this is never actually called
    # see https://forum.freecadweb.org/viewtopic.php?f=10&t=72728&p=634441#p634361
    def onSettingDocument(self, obj):
        FCC.PrintMessage('Triggered onSettingDocument() in VariantLink\n')
        obj.LinkedObject = obj.SourceObject
        return

    # this is never actually called
    def onLostLinkToObject(self, obj):
        FCC.PrintMessage('Triggered onLostLinkToObject() in VariantLink\n')
        obj.LinkedObject = obj.SourceObject
        return

    # this is never actually called
    def setupObject(self, obj):
        FCC.PrintMessage('Triggered by setupObject() in VariantLink\n')
        obj.LinkedObject = obj.SourceObject


# variantLink viewprovider
class ViewProviderVariant(object):
    def __init__( self, vobj ):
        vobj.Proxy = self
        self.attach(vobj)

    def attach(self,vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    # return an icon corresponding to the variant link type
    def getIcon(self):
        iconPath = os.path.join( Asm4.iconPath, 'Variant_Link.svg' )
        if hasattr( self.Object.Type, 'Type' ) and self.Object.Type == 'Asm4::VariantLink':
            iconPath = os.path.join( Asm4.iconPath, 'Variant_Link.svg' )
        return iconPath
                
    def __getstate__(self):
        return None

    def __setstate__(self, _state):
        return None

    def dumps(self):
        return None

    def loads(self, _state):
        return None




"""
    +-----------------------------------------------+
    |           a general link array class          |
    +-----------------------------------------------+
    see: 
    https://github.com/realthunder/FreeCAD_assembly3/wiki/Link#app-namespace

from .Asm4_objects import LinkArray
la = App.ActiveDocument.addObject("Part::FeaturePython", 'linkArray', LinkArray(),None,True)
"""
class LinkArray( object ):
    def __init__(self):
        self.Object = None
    
    def __getstate__(self):
        return

    def __setstate__(self,_state):
        return

    def dumps(self):
        return

    def loads(self,_state):
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
        obj.addProperty("App::PropertyLink",   "SourceObject", "Array", 'The object to array')
        # the following two properties are required to support link array
        obj.addProperty("App::PropertyBool",   "ShowElement",  "Array", '')
        obj.addProperty("App::PropertyInteger","Count",        "Array",
                        'Total number of elements in the array')
        obj.Count=1
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
        obj.configLinkProperty("ShowElement", 'Placement', ElementCount='Count', LinkedObject='SourceObject')
        # hide the scale properties
        if hasattr( obj, 'Scale' ):
            obj.setPropertyStatus('Scale', 'Hidden')
        if hasattr( obj, 'ScaleList' ):
            obj.setPropertyStatus('ScaleList', 'Hidden')


    # Execute when a property changes.
    def onChanged(self, obj, prop):
        # this allows to move individual elements by the user
        if prop == 'ShowElement': # set the PlacementList for user to change
            if hasattr(obj, 'PlacementList'):
                if obj.ShowElement:
                    obj.setPropertyStatus('PlacementList','-ReadOnly')
                else:
                    obj.setPropertyStatus('PlacementList', 'ReadOnly')
        # you cannot have less than 1 elements in an array
        elif prop == 'Count':
            if obj.Count < 1:
                obj.Count=1



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
            elif tp=='Linear Array':
                iconFile = os.path.join( Asm4.iconPath, 'Asm4_LinearArray.svg')
            elif tp=='Mirror Array':
                iconFile = os.path.join( Asm4.iconPath, 'Asm4_Mirror.svg')
            elif tp=='Expression Array':
                iconFile = os.path.join( Asm4.iconPath, 'Asm4_ExpressionArray.svg')
        if iconFile:
            return iconFile
                
    def __getstate__(self):
        return None

    def __setstate__(self, _state):
        return None

    def dumps(self):
        return None

    def loads(self, _state):
        return None


"""
    +-----------------------------------------------+
    |          a circular link array class          |
    +-----------------------------------------------+
class CircularArray(LinkArray):

    def onDocumentRestored(self, obj):
        # for backwards compability
        if not hasattr(obj, "Count"):
            obj.addProperty("App::PropertyInteger","Count","Array","")
            obj.Count = obj.ElementCount
        if hasattr(obj, "ElementCount"):
            obj.setPropertyStatus('ElementCount', 'Hidden')
        super().onDocumentRestored(obj)


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
            fullAngle = (obj.Count-1) * obj.IntervalAngle
            obj.setExpression("FullAngle","Count * IntervalAngle")
        elif  obj.ArraySteps=='Full Circle':
            obj.setExpression("FullAngle",None)
            obj.FullAngle = 360
            obj.IntervalAngle = obj.FullAngle/obj.Count
        plaList = []
        for i in range(obj.Count):
            # calculate placement of element i
            rot_i = App.Rotation(Asm4.VEC_Z, i*obj.IntervalAngle)
            lin_i = App.Vector(0,0,i*obj.LinearSteps)
            pla_i = App.Placement( lin_i, rot_i )
            plaElmt = axisPlacement * pla_i * axisPlacement.inverse() * sObj.Placement
            plaList.append(plaElmt)
        if not getattr(obj, 'ShowElement', True) or obj.Count != len(plaList):
            obj.setPropertyStatus('PlacementList', '-Immutable')
            obj.PlacementList = plaList
            obj.setPropertyStatus('PlacementList', 'Immutable')
        return False     # to call LinkExtension::execute()   <= is this rally needed ?
"""


"""
    +-----------------------------------------------+
    |        an expression link array class         |
    +-----------------------------------------------+
# Axial spiral
array.setExpression('.Placer.Base.z', 'Index * 10')
array.setExpression('.Placer.Rotation.Angle', 'Index * 40')
# Mirrored flat spiral
array.setExpression('.Placer.Base', '.Placer.Rotation * (minvert(.AxisPlacement) * .SourceObject.Placement.Base * -2 * (Index % 2) + create(<<vector>>; floor(Index / 2) * 15; 0; 0) * (Index % 2 * -2 + 1))')
array.setExpression('.Placer.Rotation.Angle', '180 * (Index % 2) + floor(Index / 2) * 40')
array.setExpression('Scaler', '1 - 2 * (Index % 2)')'
"""

class ExpressionArray(LinkArray):

    def raiseError(self, obj, message):
        App.Console.PrintError(f'{type(self).__name__} {obj.Label}: {message}\n')
        raise RuntimeError

    def onDocumentRestored(self, obj):
        # for backwards compability
        if obj.getTypeIdOfProperty('Axis') == 'App::PropertyLink':
            axisObj = obj.Axis
            obj.removeProperty('Axis')
            obj.addProperty("App::PropertyLinkSub","Axis","Array","")
            if hasattr(obj, "AxisXYZ"):
                subnameList = [obj.AxisXYZ]
                obj.removeProperty('AxisXYZ')
            else:
                subnameList = []
            obj.Axis = (axisObj, subnameList)
        if not hasattr(obj, "Scaler"):
            obj.addProperty('App::PropertyFloat',     'Scaler',        'Array','')
            obj.Scaler = 1.0
        if not hasattr(obj, "AxisPlacement"):
            obj.addProperty('App::PropertyPlacement', 'AxisPlacement', 'Array','')
        if not hasattr(obj, "Placer"):
            obj.addProperty('App::PropertyPlacement', 'Placer',         'Array','')
            if hasattr(obj, "ElementPlacement"):
                obj.Placer = obj.ElementPlacement
                def pnrepl(s): return s.replace('ElementPlacement','Placer')
                for k, ex in obj.ExpressionEngine:
                    obj.setExpression(pnrepl(k), pnrepl(ex))
                    if 'ElementPlacement' in k:
                        obj.setExpression(k, None)
                obj.removeProperty('ElementPlacement')
        if not hasattr(obj, "AngleStep") and hasattr(obj, "IntervalAngle"):
            obj.addProperty('App::PropertyAngle', 'AngleStep', 'Array','')
            obj.AngleStep = obj.IntervalAngle
            for k, ex in obj.ExpressionEngine:
                obj.setExpression(k, ex.replace('IntervalAngle','AngleStep'))
            obj.setExpression('IntervalAngle', None)
            obj.removeProperty('IntervalAngle')
        obj.setPropertyStatus('Index',         '-Immutable')
        obj.setPropertyStatus('PlacementList', '-Immutable')
        obj.setPropertyStatus('ScaleList',     '-Immutable')

        super().onDocumentRestored(obj)

    # Set up the properties when the object is attached.
    def attach(self, obj):
        super().attach(obj)
        obj.addProperty('App::PropertyString',      'ArrayType',        'Array', '')
        obj.addProperty('App::PropertyPlacement',   'Placer',           'Array', 
                        'Calculates element placements in relation to the Axis.\n'
                        'Each element is assigned an Index starting from 0\n'
                        'The Index can be used in expressions calculating this Placement or its sub-properties\n'
                        'Expression examples:\n'
                        'on Angle: Index%2==0?30:-30\n'
                        'on Position.X: Index*30')
        obj.addProperty('App::PropertyInteger',     'Index',            'Array', '')
        obj.addProperty('App::PropertyLinkSub',     'Axis',             'Array',
                        'The axis, direction or plane the Placer relates to')
        obj.addProperty('App::PropertyPlacement',   'AxisPlacement',     'Array','')
        obj.addProperty('App::PropertyFloat',       'Scaler',            'Array','')
        obj.Scaler = 1.0
        obj.Index = 1
        obj.setPropertyStatus('Index',         'Hidden')
        obj.setPropertyStatus('AxisPlacement', 'Hidden')
        obj.setPropertyStatus('AxisPlacement', 'ReadOnly')
        obj.setPropertyStatus('Index',         'ReadOnly')
        obj.setPropertyStatus('PlacementList', 'ReadOnly')
        obj.setPropertyStatus('ScaleList',     'ReadOnly')
        obj.ShowElement = False

    # do the calculation of the elements Placements
    def execute(self, obj):
        """ The placement is calculated relative to the axis placement
        Without Axis the Array is relative to the internal Z axis of the SourceObject."""

        # Source Object
        if not obj.SourceObject:
            self.raiseError(obj, "Missing Source Object")
        sObj = obj.SourceObject
        # we only deal with objects that are in a parent container because we'll put the array there
        parent = sObj.getParentGeoFeatureGroup()
        if not parent:
            self.raiseError(obj, "Source Object must reside inside a Part")
        # find placement of axis
        if obj.Axis:
            if parent != obj.Axis[0].getParentGeoFeatureGroup():
                self.raiseError(obj, 'Source Object and Axis must have the same parent Part')
            obj.AxisPlacement = findAxisPlacement(*obj.Axis)
            if obj.AxisPlacement is None:
                self.raiseError(obj, 'The type of the selected axis is not supported')
        else:
            obj.AxisPlacement = obj.SourceObject.Placement
        # preparing calculations
        pmt1 = obj.AxisPlacement.inverse() * sObj.Placement
        placementList = []
        scaleList = []
        expDict = dict(obj.ExpressionEngine)
        evalList = _evalOrder(expDict)
        # calculate placement of each element
        for i in range(obj.Count):
            obj.Index = i
            for pn in evalList:
                ps = 'obj.'+pn.lstrip('.')
                nv = type(eval(ps))(obj.evalExpression(expDict[pn]))
                o,a = ps.rsplit('.',1)
                if a == 'Angle' and type(eval(o)) == App.Rotation:
                    nv = radians(nv)
                # must set entire rotation axis at once.
                # Related discussion: https://forum.freecad.org/viewtopic.php?t=73898
                if o.endswith('.Axis') and a in 'xyz':
                    axv = eval(o.replace('.Axis','.RawAxis'))
                    setattr(axv, a, nv)
                    exec(o + ' = axv')
                    continue
                exec(ps + ' = nv')
            placementList.append(obj.AxisPlacement * obj.Placer * pmt1)
            s = obj.Scaler
            scaleList.append(App.Vector(s, s, s))
        # Resetting Index to 1 because we get more useful preview results 
        # in the expression editor
        obj.Index = 1
        if obj.ShowElement:
            for i in range(obj.Count):
                el = obj.ElementList[i]
                el.NoTouch = True
                el.Placement = placementList[i]
                el.ScaleVector = scaleList[i]
                el.setPropertyStatus('Placement',   'ReadOnly')
                el.setPropertyStatus('ScaleVector', 'ReadOnly')
                el.setPropertyStatus('Scale',       'ReadOnly')
                el.NoTouch = False
        else:
            obj.PlacementList = placementList
            obj.ScaleList = scaleList
        return

def findAxisPlacement(axisObj, subnameList):
    if subnameList:
        if len(subnameList) != 1:
            return None
        subname = subnameList[0]
        sub = axisObj.getSubObject(subname)
        if sub:
            if Asm4.isSegment(sub):
                b = sub.Vertexes[0].Point
                d = sub.Vertexes[1].Point - b
                return App.Placement(b, App.Rotation(Asm4.VEC_Z, d))
            # for a Circle it's the circle's center and axis
            if Asm4.isCircle(sub):
                return App.Placement(sub.Curve.Center, App.Rotation(Asm4.VEC_Z, sub.Curve.Axis))
        # This is for LCS and works for other objects too
        if subname == 'X':
            return axisObj.Placement * App.Rotation(Asm4.VEC_T, 120)
        if subname == 'Y':
            return axisObj.Placement * App.Rotation(Asm4.VEC_T, 240)
        if subname == 'Z':
            return axisObj.Placement
        return None
    # on origin axes we want the X axis
    if axisObj.TypeId == 'App::Line' and hasattr(axisObj,'Role'):
        return axisObj.Placement * App.Rotation(Asm4.VEC_T, 120)
    if axisObj.TypeId == 'App::Plane' and hasattr(axisObj,'Role'):
        return axisObj.Placement
    if axisObj.TypeId in ('PartDesign::CoordinateSystem', 'PartDesign::Plane'):
        return axisObj.Placement        
    # Arbitary object as axis is rejected for now
    return None

# To find evaluation order of expressions. The builtin can't handle a placement internal properties
def _findParam(p_name, expression):
    if p_name in expression:
        if p_name[0] == '.':
            exp = expression.replace(p_name,'a'+p_name)
            a = "\\b{}\\b(?![.])".format('a'+p_name.replace('.',r'\.'))
        else:
            exp = expression
            a = "\\b{}\\b(?![.])".format(p_name)
        return bool(re.search(a, exp))
    return False

_placerProps = [
    '.Placer.Rotation',
    '.Placer.Rotation.Axis',
    '.Placer.Rotation.Axis.x',
    '.Placer.Rotation.Axis.y',
    '.Placer.Rotation.Axis.z',
    '.Placer.Rotation.Angle',
    '.Placer.Rotation.Yaw',
    '.Placer.Rotation.Pitch',
    '.Placer.Rotation.Roll',
    '.Placer.Base',
    '.Placer.Base.x',
    '.Placer.Base.y',
    '.Placer.Base.z',
]
def _expandEdge(edge):
    if edge.startswith('.Placer.'):
        ie = []
        for s in _placerProps:
            if s.startswith(edge):
                ie.append(s)
        while True:
            edge = edge.rsplit('.',1)[0]
            if edge == '.Placer':
                break
            ie.append(edge)
        return ie
    return [edge]

def _evalOrder(exDict):
    unresolved = []
    resolved = []
    def dep_resolve(node, resolved, unresolved):
        unresolved.append(node)
        nodes = _expandEdge(node)
        for edge in exDict.keys():
            for n in nodes:
                if edge == n: continue
                if _findParam(n, exDict[edge]):
                    if edge not in resolved:
                        if edge in unresolved:
                            raise RuntimeError('Circular reference detected: {} -> {}'.format(n, edge))
                        dep_resolve(edge, resolved, unresolved)
        resolved.append(node)
        unresolved.remove(node)
    dep_resolve('Index', resolved, unresolved)
    resolved.pop()
    return list(reversed(resolved))


#!/usr/bin/env python3
# coding: utf-8
#
# libraries for FreeCAD's Assembly 4 workbench
#
# LGPL
# Copyright HUBERT Zoltán



"""
    +-----------------------------------------------+
    |          shouldn't these be DEFINE's ?        |
    +-----------------------------------------------+
"""

import os
wbPath   = os.path.dirname(__file__)
iconPath = os.path.join( wbPath, 'Resources/icons' )
libPath  = os.path.join( wbPath, 'Resources/library' )

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC



# Types of datum objects
datumTypes = [  'PartDesign::CoordinateSystem', \
                'PartDesign::Plane',            \
                'PartDesign::Line',             \
                'PartDesign::Point']


partInfo =[     'PartID',                       \
                'PartName',                     \
                'PartDescription',              \
                'PartSupplier']

containerTypes = [  'App::Part', 'PartDesign::Body' ]


VEC_0 = App.Vector(0, 0, 0)
VEC_X = App.Vector(1, 0, 0)
VEC_Y = App.Vector(0, 1, 0)
VEC_Z = App.Vector(0, 0, 1)
VEC_T = App.Vector(1, 1, 1)


rotX = App.Placement( VEC_0, App.Rotation( VEC_X, 90) )
rotY = App.Placement( VEC_0, App.Rotation( VEC_Y, 90) )
rotZ = App.Placement( VEC_0, App.Rotation( VEC_Z, 90) )



def findObjectLink(obj, doc = App.ActiveDocument):
    for o in doc.Objects:
        if hasattr(o, 'LinkedObject'):
            if o.LinkedObject == obj:
                return o
    return(None)


def getSelectionPath(docName, objName, subObjName):
        val = []
        if (docName is None) or (docName == ''):
            docName = App.ActiveDocument.Name
        val.append(docName)
        if objName and (objName != ''):
            val.append(objName)
            if subObjName and (subObjName != ''):
                for son in subObjName.split('.'):
                    if son and (son != ''):
                        val.append(son)

        return val


"""
    +-----------------------------------------------+
    |           Object helper functions             |
    +-----------------------------------------------+
"""

def cloneObject(obj):
    container = obj.getParentGeoFeatureGroup()
    result = None
    if obj.Document and container:
        #result = obj.Document.copyObject(obj, False)
        result = obj.Document.addObject('App::Link', obj.Name)
        result.LinkedObject = obj
        result.Label = obj.Label
        container.addObject(result)
        result.recompute()
        #container = result.getParentGeoFeatureGroup()
        #if container:
        container.recompute()
        #if result.Document:
        result.Document.recompute()
    return result

def newLCS(parent, objType, objName, attSupport):
    result = parent.newObject(objType, objName)
    if hasattr(result, 'AttachmentSupport'):
        result.AttachmentSupport = attSupport
    else:
        result.Support = attSupport
    return result

def placeObjectToLCS( attObj, attLink, attDoc, attLCS ):
    expr = makeExpressionDatum( attLink, attDoc, attLCS )
    # FCC.PrintMessage('expression = '+expr)
    # indicate the this fastener has been placed with the Assembly4 workbench
    if not hasattr(attObj,'SolverId'):
        makeAsmProperties(attObj)
    # the fastener is attached by its Origin, no extra LCS
    attObj.AttachedBy = 'Origin'
    # store the part where we're attached to in the constraints object
    attObj.AttachedTo = attLink+'#'+attLCS
    # load the built expression into the Expression field of the constraint
    attObj.setExpression( 'Placement', expr )
    # Which solver is used
    attObj.SolverId = 'Asm4EE'
    # recompute the object to apply the placement:
    attObj.recompute()
    container = attObj.getParentGeoFeatureGroup()
    if container:
        container.recompute()
    if attObj.Document:
        attObj.Document.recompute()




"""
    +-----------------------------------------------+
    |      Create default Assembly4 properties      |
    +-----------------------------------------------+
"""
def makeAsmProperties( obj, reset=False ):
    # property AttachedBy
    if not hasattr(obj,'AttachedBy'):
        obj.addProperty( 'App::PropertyString', 'AttachedBy', 'Assembly' )
    obj.setPropertyStatus('AttachedBy'  ,'ReadOnly')
    # property AttachedTo
    if not hasattr(obj,'AttachedTo'):
        obj.addProperty( 'App::PropertyString', 'AttachedTo', 'Assembly' )
    obj.setPropertyStatus('AttachedTo'  ,'ReadOnly')
    # property AttachmentOffset
    if not hasattr(obj,'AttachmentOffset'):
        obj.addProperty( 'App::PropertyPlacement', 'AttachmentOffset', 'Assembly' )
    # property SolverId
    if not hasattr(obj,'SolverId'):
        obj.addProperty( 'App::PropertyString', 'SolverId', 'Assembly' )
    if reset:
        obj.AttachedBy = ''
        obj.AttachedTo = ''
        obj.AttachmentOffset = App.Placement()
        obj.SolverId = ''
    return


# checks whether there is a Variables container, and returns it
def getVarContainer():
    retval = None
    # check whether there already is a Variables object
    variables = App.ActiveDocument.getObject('Variables')
    if variables and variables.TypeId=='App::FeaturePython':
            # signature of a PropertyContainer
            if hasattr(variables,'Type') :
                if variables.Type == 'App::PropertyContainer':
                    retval = variables
    return retval


# the Variables container
def makeVarContainer():
    retval = None
    # check whether there already is a Variables object
    variables = App.ActiveDocument.getObject('Variables')
    if variables :
        if variables.TypeId=='App::FeaturePython':
            # signature of a PropertyContainer
            if hasattr(variables,'Type') :
                if variables.Type == 'App::PropertyContainer':
                    retval = variables
            # for compatibility
            else: 
                variables.addProperty('App::PropertyString', 'Type')
                variables.Type = 'App::PropertyContainer'            
                retval = variables
        else:
            FCC.PrintWarning('This Part contains an incompatible \"Variables\" object, ')
            FCC.PrintWarning('this could lead to unexpected results\n')
    # there is none, so we create it
    else:
        variables = App.ActiveDocument.addObject('App::FeaturePython','Variables')
        variables.ViewObject.Proxy = setCustomIcon(object,'Asm4_Variables.svg')
        # signature or a PropertyContainer
        variables.addProperty('App::PropertyString', 'Type')
        variables.Type = 'App::PropertyContainer'
        retval = variables
    return retval


# custom icon
# views/view_custom.py
# https://wiki.freecadweb.org/Viewprovider
# https://wiki.freecadweb.org/Custom_icon_in_tree_view
#
# obj = App.ActiveDocument.addObject("App::FeaturePython", "Name")
# obj.ViewObject.Proxy = ViewProviderCustomIcon( obj, path + "FreeCADIco.png")
# icon download to file
#
# usage:
# object = App.ActiveDocument.addObject('App::FeaturePython','objName')
# object = model.newObject('App::FeaturePython','objName')
# object.ViewObject.Proxy = Asm4.setCustomIcon(object,'Asm4_Variables.svg')
class setCustomIcon():
    def __init__( self, obj, iconFile):
        #obj.Proxy = self
        self.customIcon = os.path.join( iconPath, iconFile )

    def getIcon(self):                                              # GetIcon
        return self.customIcon




"""
    +-----------------------------------------------+
    |         check whether a workbench exists      |
    +-----------------------------------------------+
"""
def checkWorkbench( workbench ):
    # checks whether the specified workbench is installed
    listWB = Gui.listWorkbenches()
    hasWB = False
    for wb in listWB.keys():
        if wb == workbench:
            hasWB = True
    return hasWB

# since Asm4 v0.20 an assembly is called "Assembly" again
def getAssembly():
    # return checkModel()
    retval = None
    if App.ActiveDocument:
        # the current (as per v0.90) assembly container
        assy = App.ActiveDocument.getObject('Assembly')
        if assy and assy.TypeId == 'App::Part'  \
                and assy.Type   == 'Assembly'   \
                and assy.getParentGeoFeatureGroup() is None:
            retval = assy
        else:
            # former Asm4 Model compatibility check:
            model = App.ActiveDocument.getObject('Model')
            if model and model.TypeId == 'App::Part'  \
                    and model.Type    == 'Assembly'   \
                    and model.getParentGeoFeatureGroup() is None:
                retval = model
            else:
                # last chance, very old Asm4 Model
                if model and model.TypeId=='App::Part'  \
                        and model.getParentGeoFeatureGroup() is None:
                    retval = model
    return retval


# checks and returns whether there is an Asm4 Assembly Model in the active document
# DEPRECATED : it's called Assembly again
def checkModel():
    return getAssembly()


# returns the selected object and its selection hierarchy
# the first element in the tree is the uppermost container name
# the last is the object name
# elements are separated by '.' (dot)
# usage:
# ( obj, tree ) = Asm4.getSelectionTree(index=0)
def getSelectionTree(index=0):
    retval = (None,None)
    # we obviously need something selected
    # if len(Gui.Selection.getSelection()) >= index:
    if len(Gui.Selection.getSelection()) > index:
        selObj = Gui.Selection.getSelection()[index]
        retval = ( selObj, None )
        # objects at the document root don't have a selection tree
        if len(Gui.Selection.getSelectionEx("", 0)[0].SubElementNames) >= index:
            # we only treat the first selected object
            # TODO : are we sure about that ? Shouldn't this be [index] ?
            # this is a dot-separated list of the selection hierarchy
            # selList = Gui.Selection.getSelectionEx("", 0)[index].SubElementNames[0]
            selList = Gui.Selection.getSelectionEx("", 0)[0].SubElementNames[index]
            # this is the final tree table
            # this first element will be overwritten later
            selTree = ['root part']
            # parse the list to find all objects
            rest = selList
            while rest:
                (parent, dot, rest) = rest.partition('.')
                # FCC.PrintMessage('found '+parent+'\n')
                selTree.append(parent)
            # if we did find things
            if len(selTree)>1:
                # if the last one is not the selected object, it might be a sub-element of it
                if selTree[-1]!=selObj.Name:
                    selTree = selTree[0:-1]
                # the last one should the selected object
                if selTree[-1]==selObj.Name:
                    topObj = App.ActiveDocument.getObject(selTree[1])
                    rootObj = topObj.getParentGeoFeatureGroup()
                    selTree[0] = rootObj.Name
                    # all went well, we return the selected object and its tree
                    retval = ( selObj, selTree )
    return retval


# get all datums in a part
def getPartLCS( part ):
    partLCS = [ ]
    # parse all objects in the part (they return strings)
    for objName in part.getSubObjects(1):
        # get the proper objects
        # all object names end with a "." , this needs to be removed
        obj = part.getObject( objName[0:-1] )
        if obj.TypeId in datumTypes:
            partLCS.append( obj )
        elif obj.TypeId == 'App::DocumentObjectGroup':
            datums = getPartLCS(obj)
            for datum in datums:
                partLCS.append(datum)
    return partLCS


# get the document group called Part
# (if it exists, else return None
def getPartsGroup():
    retval = None
    partsGroup = App.ActiveDocument.getObject('Parts')
    if partsGroup and partsGroup.TypeId=='App::DocumentObjectGroup':
        retval = partsGroup
    return retval


# Get almost all Objects within the passed Selection.
# A Selection is one or more marked Object(s) anywhere
# in the opened Document. The idea is to get a similar
# Selection back, as If you would "copy" the marked Objects.
# The Window that pops up and shows are affected Objects, calls it
# The Dependencies
# Objects within Compounds and Bodys and also Linked Objects are left out.
# 
# NOTE: Theoretically we could use the App.ActiveDocument.DependencyGraph function,
# to get really every Object behind a selection.
def getDependenciesList( CompleteSelection ):
    deDendenciesList = [ ]
    for Selection in CompleteSelection:
        # A possible container for more Sub-Objects
        SubObjects = [ ]
        # If an Object has more objects to offer, get them
        if hasattr(Selection,'getSubObjects'):
            SubObjNames=Selection.getSubObjects()
            # Some Objects return None Objects,
            # even if it has the 'getSubObjects' attribute
            # 'getSubObjects' delivers unique Names with a trailing .
            for SubObjName in SubObjNames:              
                SubObjects.append(App.ActiveDocument.getObject(SubObjName[0:-1]))
        # If they are more Sub-Objects within that particular selection,
        # go get them. It doesn't matter If it is a Group or Part or Link.
        if SubObjects is not None:            
            SubObjects = getDependenciesList(SubObjects)
            # Adding the Sub-Objects in that way, prevents nested Objects in Objects
            for SubObject in SubObjects:
                deDendenciesList.append(SubObject)
        # In order to make not iterable, single Objects,
        # iterable enclosing [] are needed
        deDendenciesList.append([Selection])
    return deDendenciesList


"""
    +-----------------------------------------------+
    |           get the next instance's name        |
    +-----------------------------------------------+
"""
def nextInstance( name, startAtOne=False ):
    # if there is no such name, return the original
    if not App.ActiveDocument.getObject(name) and not startAtOne:
        return name
    # there is already one, we increment
    else:
        if startAtOne:
            instanceNum = 1
        else:
            instanceNum = 2
        while App.ActiveDocument.getObject( name+'_'+str(instanceNum) ):
            instanceNum += 1
        return name+'_'+str(instanceNum)



"""
    +-----------------------------------------------+
    |          return the ExpressionEngine          |
    |           of the Placement property           |
    +-----------------------------------------------+
"""
def placementEE( EE ):
    if not EE:
        return None
    else:
        for expr in EE:
            if expr[0] == 'Placement':
                return expr[1]
    return None




"""
    +-----------------------------------------------+
    |              some geometry tests              |
    +-----------------------------------------------+
"""
def isVector( vect ):
    if isinstance(vect,App.Vector):
        return True
    return False

def isCircle(shape):
    if shape.isValid()  and hasattr(shape,'Curve') \
                        and shape.Curve.TypeId=='Part::GeomCircle' \
                        and hasattr(shape.Curve,'Center') \
                        and hasattr(shape.Curve,'Radius'):
        return True
    return False

def isLine(shape):
    if shape.isValid()  and hasattr(shape,'Curve') \
                        and shape.Curve.TypeId=='Part::GeomLine' \
                        and hasattr(shape,'Placement'):
        return True
    return False

def isSegment(shape):
    if shape.isValid()  and hasattr(shape,'Curve') \
                        and shape.Curve.TypeId=='Part::GeomLine' \
                        and hasattr(shape,'Length') \
                        and hasattr(shape,'Vertexes') \
                        and len(shape.Vertexes)==2:
        return True
    return False


def isFlatFace(shape):
    if shape.isValid()  and hasattr(shape,'Area')   \
                        and shape.Area > 1.0e-6     \
                        and hasattr(shape,'Volume') \
                        and shape.Volume < 1.0e-9:
        return True
    return False


def isHoleAxis(obj):
    if not obj:
        return False
    if hasattr(obj, 'AttacherType'):
        if obj.AttacherType == 'Attacher::AttachEngineLine':
            return True
    return False


def isPart(obj):
    if not obj:
        return False
    if hasattr(obj, 'TypeId'):
        if obj.TypeId == 'App::Part':
            return True
    return False


def isAppLink(obj):
    if not obj:
        return False
    if hasattr(obj, 'TypeId') and obj.TypeId == 'App::Link':
        return True
    return False


def isLinkToPart(obj):
    if not obj:
        return False
    if obj.TypeId == 'App::Link' and hasattr(obj.LinkedObject,'isDerivedFrom'):
        if  obj.LinkedObject.isDerivedFrom('App::Part') or obj.LinkedObject.isDerivedFrom('PartDesign::Body'):
            return True
    return False


def isAsm4EE(obj):
    if not obj:
        return False
    # we only need to check for the SolverId
    if hasattr(obj,'SolverId') :
        if obj.SolverId=='Asm4EE' or obj.SolverId=='Placement::ExpressionEngine' or obj.SolverId=='' :
            return True
    # legacy check
    # DEPRECATED, to be removed
    elif hasattr(obj,'AssemblyType') :
        if obj.AssemblyType == 'Asm4EE' or obj.AssemblyType == '' :
            FCC.PrintMessage('Found legacy AssemblyType property, adding new empty SolverId property\n')
            # add the new property to convert legacy object
            obj.addProperty( 'App::PropertyString', 'SolverId', 'Assembly' )
            return True
    return False


def isAssembly(obj):
    if not obj:
        return False
    if obj.TypeId=='App::Part' and obj.Name=='Assembly':
        if hasattr(obj,'Type') and obj.Type=='Assembly':
            return True
    return False


def isAsm4Model(obj):
    return isAssembly(obj)


"""
    +-----------------------------------------------+
    |           Shows a Warning message box         |
    +-----------------------------------------------+
"""
def warningBox( text ):
    msgBox = QtGui.QMessageBox()
    msgBox.setWindowTitle( 'FreeCAD Warning' )
    msgBox.setIcon( QtGui.QMessageBox.Critical )
    msgBox.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
    msgBox.setText( text )
    msgBox.exec_()
    return


def confirmBox( text ):
    msgBox = QtGui.QMessageBox()
    msgBox.setWindowTitle('FreeCAD Warning')
    msgBox.setIcon(QtGui.QMessageBox.Warning)
    msgBox.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
    msgBox.setText(text)
    msgBox.setInformativeText('Are you sure you want to proceed ?')
    msgBox.setStandardButtons(QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ok)
    msgBox.setEscapeButton(QtGui.QMessageBox.Cancel)
    msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
    retval = msgBox.exec_()
    # Cancel = 4194304
    # Ok = 1024
    if retval == 1024:
        # user confirmed
        return True
    # anything else than OK
    return False


"""
    +-----------------------------------------------+
    |        Drop-down menu to group buttons        |
    +-----------------------------------------------+
"""
# from https://github.com/HakanSeven12/FreeCAD-Geomatics-Workbench/commit/d82d27b47fcf794bf6f9825405eacc284de18996
class dropDownCmd:
    def __init__(self, cmdlist, menu, tooltip = None, icon = None):
        self.cmdlist = cmdlist
        self.menu = menu
        if tooltip is None:
            self.tooltip = menu
        else:
            self.tooltip = tooltip

    def GetCommands(self):
        return tuple(self.cmdlist)

    def GetResources(self):
        return { 'MenuText': self.menu, 'ToolTip': self.tooltip }




"""
    +-----------------------------------------------+
    |         returns the object Label (Name)       |
    +-----------------------------------------------+
"""


# Label (Name)
def labelName( obj ):
    if obj:
        if obj.Name == obj.Label:
            txt = obj.Label
        else:
            txt = obj.Label +' ('+obj.Name+')'
        return txt
    else:
        return None



"""
    +-----------------------------------------------+
    |         populate the ExpressionEngine         |
    +-----------------------------------------------+
"""
def makeExpressionPart( attLink, attDoc, attLCS, linkedDoc, linkLCS ):
    # if everything is defined
    if attLink and attLCS and linkedDoc and linkLCS:
        # this is where all the magic is, see:
        #
        # https://forum.freecadweb.org/viewtopic.php?p=278124#p278124
        #
        # as of FreeCAD v0.19 the syntax is different:
        # https://forum.freecadweb.org/viewtopic.php?f=17&t=38974&p=337784#p337784
        # expr = ParentLink.Placement * ParentPart#LCS.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1
        # expr = LCS_in_the_assembly.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1
        # the AttachmentOffset is now a property of the App::Link
        # expr = LCS_in_the_assembly.Placement * AttachmentOffset * LinkedPart#LCS.Placement ^ -1
        expr = attLCS+'.Placement * AttachmentOffset * '+linkedDoc+'#'+linkLCS+'.Placement ^ -1'
        # if we're attached to another sister part (and not the Parent Assembly)
        # we need to take into account the Placement of that Part.
        if attDoc:
            expr = attLink+'.Placement * '+attDoc+'#'+expr
    else:
        expr = False
    return expr


def makeExpressionDatum( attLink, attPart, attLCS ):
    # check that everything is defined
    if attLCS:
        # expr = Link.Placement * LinkedPart#LCS.Placement
        expr = attLCS +'.Placement * AttachmentOffset'
        if attLink and attPart:
            expr = attLink+'.Placement * '+attPart+'#'+expr
    else:
        expr = None
    return expr




"""
    +-----------------------------------------------+
    |        ExpressionEngine for Fasteners         |
    +-----------------------------------------------+
"""
# is in the FastenersLib.py file



# checks whether an App::Part is selected, and that it's at the root of the document
def getSelectedRootPart():
    retval = None
    selection = Gui.Selection.getSelection()
    if len(selection)==1:
        selObj = selection[0]
        # only consider App::Parts at the root of the document
        if selObj.TypeId=='App::Part' and selObj.getParentGeoFeatureGroup() is None:
            retval = selObj
    return retval


def getSelectedContainer():
    retval = None
    selection = Gui.Selection.getSelection()
    if len(selection)==1:
        selObj = selection[0]
        if selObj.TypeId in containerTypes:
            retval = selObj
    return retval


def getAppLinkObj():
    sels = Gui.Selection.getSelectionEx("", 0)
    sel = sels[0]
    doc = sel.Document
    sub = sel.SubElementNames[0] if sel.SubElementNames else ""
    subs = sub.split(".")[:-1]
    path = [sel.Object] + [doc.getObject(name) for name in subs]
    try:
        for o in path:
            if o.isDerivedFrom('App::Link') and o.LinkedObject is not None and o.LinkedObject.TypeId in containerTypes:
                return o
    except:
        return None


# returns the selected App::Link
def getSelectedLink():
    retval = None
    selection = Gui.Selection.getSelection()
    if len(selection)==1:
        selObj = selection[0]
        # it's an App::Link
        if selObj.isDerivedFrom('App::Link') and selObj.LinkedObject is not None and selObj.LinkedObject.TypeId in containerTypes:
            retval = selObj
    return retval


# returns the selected Asm4 variant link
def getSelectedVarLink():
    retval = None
    selection = Gui.Selection.getSelection()
    if len(selection)==1:
        selObj = selection[0]
        # it's an App::Link
        if selObj.TypeId=='Part::FeaturePython':
            if hasattr(selObj,'Type') and selObj.Type=='Asm4::VariantLink':
                retval = selObj
    return retval


def getSelectedDatum():
    selectedObj = None
    # check that something is selected
    if len(Gui.Selection.getSelection())==1:
        selection = Gui.Selection.getSelection()[0]
        # check that it's a datum
        if selection.TypeId in datumTypes:
            selectedObj = selection
    # now we should be safe
    return selectedObj


"""
    +-----------------------------------------------+
    |                 Unit Spin Box                 |
    +-----------------------------------------------+

usage:

self.YtranslSpinBox = QtGui.QDoubleSpinBox() → self.YtranslSpinBox = Asm4.QUnitSpinBox()
"""
class QUnitSpinBox(QtGui.QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        _, self.length_divisor, self.default_unit = (
            App.Units.schemaTranslate(
                App.Units.Quantity("1 mm"),
                App.Units.getSchema()
            )
        )
        self.setSuffix(" " + self.default_unit)

    def value(self) -> float:
        """gets the value in mm"""
        return super().value() * self.length_divisor

    def setValue(self, distance: float):
        """sets the value in mm"""        
        return super().setValue(
            distance / self.length_divisor,
        ) 
        

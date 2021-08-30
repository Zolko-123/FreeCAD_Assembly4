#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# libraries for FreeCAD's Assembly 4 workbench



"""
    +-----------------------------------------------+
    |          shouldn't these be DEFINE's ?        |
    +-----------------------------------------------+
"""

import os
#__dir__ = os.path.dirname(__file__)
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
 
 
def placeObjectToLCS( attObj, attLink, attDoc, attLCS ):
    expr = makeExpressionDatum( attLink, attDoc, attLCS )
    # indicate the this fastener has been placed with the Assembly4 workbench
    if not hasattr(attObj,'AssemblyType'):
        Asm4.makeAsmProperties(attObj)
    attObj.AssemblyType = 'Part::Link'
    # the fastener is attached by its Origin, no extra LCS
    attObj.AttachedBy = 'Origin'
    # store the part where we're attached to in the constraints object
    attObj.AttachedTo = attLink+'#'+attLCS
    # load the built expression into the Expression field of the constraint
    attObj.setExpression( 'Placement', expr )
    # Which solver is used
    attObj.SolverId = 'Placement::ExpressionEngine'
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
    # property AssemblyType
    if not hasattr(obj,'AssemblyType'):
        obj.addProperty( 'App::PropertyString', 'AssemblyType', 'Assembly' )
    # property AttachedBy
    if not hasattr(obj,'AttachedBy'):
        obj.addProperty( 'App::PropertyString', 'AttachedBy', 'Assembly' )
    # property AttachedTo
    if not hasattr(obj,'AttachedTo'):
        obj.addProperty( 'App::PropertyString', 'AttachedTo', 'Assembly' )
    # property AttachmentOffset
    if not hasattr(obj,'AttachmentOffset'):
        obj.addProperty( 'App::PropertyPlacement', 'AttachmentOffset', 'Assembly' )
    # property SolverId
    if not hasattr(obj,'SolverId'):
        obj.addProperty( 'App::PropertyString', 'SolverId', 'Assembly' )
    if reset:
        obj.AssemblyType = ''
        #obj.AttachedBy = ''
        #obj.AttachedTo = ''
        #obj.AttachmentOffset = App.Placement()
        obj.SolverId = ''
    return


# the Variables container
def createVariables():
    retval = None
    # check whether there already is a Variables object
    variables = App.ActiveDocument.getObject('Variables')
    if variables:
        retval = variables
    # there is none, so we create it
    else:
        variables = App.ActiveDocument.addObject('App::FeaturePython','Variables')
        variables.ViewObject.Proxy = setCustomIcon(object,'Asm4_Variables.svg')
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

# checks whether there is a FreeCAD Assembly at the root of the active document
def getAssembly():
    if App.ActiveDocument:
        # should we check for AssemblyType=='Part::Link' ?
        assy = App.ActiveDocument.getObject('Assembly')
        if assy and assy.TypeId=='App::Part'                        \
                and assy.Type == 'Assembly'                         \
                and assy.getParentGeoFeatureGroup() is None:
            return assy
        else:
            # legacy check for compatibility
            model = checkModel()
            if model:
                #FCC.PrintWarning('This is a legacy Asm4 Model\n')
                return model
    return None

# DEPRECATED checks whether there is an Asm4 Model at the root of the active document
def checkModel():
    if App.ActiveDocument:
        model = App.ActiveDocument.getObject('Model')
        if model and model.TypeId=='App::Part' and model.getParentGeoFeatureGroup() is None:
            return model
    return None

# checks whether an App::Link is to an App::Part
def isLinkToPart(obj):
    if not obj:
        return False
    if obj.TypeId == 'App::Link' and hasattr(obj.LinkedObject,'isDerivedFrom'):
        if  obj.LinkedObject.isDerivedFrom('App::Part') or obj.LinkedObject.isDerivedFrom('PartDesign::Body'):
            return True
    return False

# returns the selected object and its selection hierarchy
# the first element in the tree is the uppermost container name
# the last is the object name
# elements are separated by '.' (dot)
# usage:
# ( obj, tree ) = Asm4.getSelectionTree()
def getSelectionTree():
    retval = (None,None)
    # we obviously need something selected
    if len(Gui.Selection.getSelection())>0:
        selObj = Gui.Selection.getSelection()[0]
        retval = ( selObj, None )
        # objects at the document root dont have a selection tree
        if len(Gui.Selection.getSelectionEx("", 0)[0].SubElementNames)>0:
            # we only treat thefirst selected object 
            # this is a dot-separated list of the selection hierarchy
            selList = Gui.Selection.getSelectionEx("", 0)[0].SubElementNames[0]
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
                    # all went well, we return the selected object and it's tree
                    retval = ( selObj, selTree )
    return retval

'''
# get from the selected object the corresponding parent instance (link)
# deprecated for getSelectionTree()
def getLinkAndObj():
    retval = (None,None)
    # only for Asm4
    if checkModel() and len(Gui.Selection.getSelection())==1:
        parentAssembly = App.ActiveDocument.Model
        # find all the links to Part or Body objects
        childrenTable = []
        for objStr in parentAssembly.getSubObjects():
            # the string ends with a . that must be removed
            obj = App.ActiveDocument.getObject( objStr[0:-1] )
            if isLinkToPart(obj):
                # add it to our tree table if it's a link to an App::Part ...
                childrenTable.append( obj )
        # the selected datum
        selObj = Gui.Selection.getSelection()[0]
        # if indeed a datum is selected
        # if selObj.TypeId in datumTypes:
        if selObj.isDerivedFrom('Part::Feature'):
            # return at least the selected object
            retval = (None,selObj)
            # this returns the selection hierarchy in the form 'linkName.datumName.'
            selTree = Gui.Selection.getSelectionEx("", 0)[0].SubElementNames[0]
            (parents, toto, dot) = selTree.partition('.'+selObj.Name)
            link = App.ActiveDocument.getObject( parents )
            # if indeed the datum is the child of a link
            if dot =='.' and link in childrenTable:
                retval = (link,selObj)
            else:
                # see whether the datum is in a group, some people like to do that
                (parents2, dot, groupName) = parents.partition('.')
                link2 = App.ActiveDocument.getObject( parents2 )
                group = App.ActiveDocument.getObject( groupName )
                if link2 and group and link2 in childrenTable and group.TypeId=='App::DocumentObjectGroup':
                    retval = (link2,selObj)
    return retval
'''

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
    if hasattr(obj, 'TypeId'):
        if obj.TypeId == 'App::Link':
            return True
    return False


def isPartLinkAssembly(obj):
    if not obj:
        return False
    if hasattr(obj,'AssemblyType') and hasattr(obj,'SolverId'):
        if obj.AssemblyType == 'Part::Link' or obj.AssemblyType == '' :
            return True
    return False


def isAsm4EE(obj):
    if not obj:
        return False
    # we only need to check for the SolverId
    if hasattr(obj,'SolverId') :
        if obj.SolverId == 'Placement::ExpressionEngine' or obj.SolverId == '' :
            return True
    # legacy check
    elif hasattr(obj,'AssemblyType') :
        if obj.AssemblyType == 'Asm4EE' or obj.AssemblyType == '' :
            FCC.PrintMessage('Found legacy AssemblyType property, adding new empty SolverId property\n')
            # add the new property to convert legacy object
            obj.addProperty( 'App::PropertyString', 'SolverId', 'Assembly' )
            return True
    return False


"""
    +-----------------------------------------------+
    |           Shows a Warning message box         |
    +-----------------------------------------------+
"""
def warningBox( text ):
    msgBox = QtGui.QMessageBox()
    msgBox.setWindowTitle( 'FreeCAD Warning' )
    msgBox.setIcon( QtGui.QMessageBox.Critical )
    msgBox.setText( text )
    msgBox.exec_()
    return


def confirmBox( text ):
    msgBox = QtGui.QMessageBox()
    msgBox.setWindowTitle('FreeCAD Warning')
    msgBox.setIcon(QtGui.QMessageBox.Warning)
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
    |         the 3 base rotation Placements        |
    +-----------------------------------------------+
"""
rotX = App.Placement( App.Vector(0,0,0), App.Rotation( App.Vector(1,0,0), 90. ) )
rotY = App.Placement( App.Vector(0,0,0), App.Rotation( App.Vector(0,1,0), 90. ) )
rotZ = App.Placement( App.Vector(0,0,0), App.Rotation( App.Vector(0,0,1), 90. ) )




"""
    +-----------------------------------------------+
    |         returns the object Label (Name)       |
    +-----------------------------------------------+
def nameLabel( obj ):
    if obj:
        txt = obj.Name
        if obj.Name!=obj.Label:
            txt += ' ('+obj.Label+')'
        return txt
    else:
        return None
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
    if attLink and attLCS:
        # expr = Link.Placement * LinkedPart#LCS.Placement
        expr = attLCS +'.Placement * AttachmentOffset'
        if attPart:
            expr = attLink+'.Placement * '+attPart+'#'+expr
    else:
        expr = False
    return expr


"""
    +-----------------------------------------------+
    |  split the ExpressionEngine of a linked part  |
    |          to find the old attachment LCS       |
    |   (in the parent assembly or a sister part)   |
    |   and the old target LCS in the linked Part   |
    +-----------------------------------------------+

def splitExpressionLink( expr, parent ):
    # same document:
    # expr = LCS_target.Placement * AttachmentOffset * LCS_attachment.Placement ^ -1
    # external document:
    # expr = LCS_target.Placement * AttachmentOffset * linkedPart#LCS_attachment.Placement ^ -1
    # expr = sisterLink.Placement * sisterPart#LCS_target.Placement * AttachmentOffset * linkedPart#LCS_attachment.Placement ^ -1
    retval = ( expr, 'None', 'None' )
    restFinal = ''
    attLink = ''
    # expr is empty
    if not expr:
        return retval
    nbHash = expr.count('#')
    if nbHash==0:
        # linked part, sister part and assembly in the same document
        if parent == 'Parent Assembly':
            # we're attached to an LCS in the parent assembly
            # expr = LCS_in_the_assembly.Placement * AttachmentOffset * LCS_linkedPart.Placement ^ -1
            ( attLCS,     separator, rest1 ) = expr.partition('.Placement * AttachmentOffset * ')
            ( linkLCS,    separator, rest2 ) = rest1.partition('.Placement ^ ')
            restFinal = rest2[0:2]
            attLink = parent
            attPart = 'None'
        else:
            # we're attached to an LCS in a sister part
            # expr = ParentLink.Placement * LCS_parent.Placement * AttachmentOffset * LCS_linkedPart.Placement ^ -1
            ( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
            ( attLCS,     separator, rest2 ) = rest1.partition('.Placement * AttachmentOffset * ')
            ( linkLCS,    separator, rest3 ) = rest2.partition('.Placement ^ ')
            restFinal = rest3[0:2]
    elif nbHash==1:
        # an external part is linked to the assembly or a part in the same document as the assembly
        if parent == 'Parent Assembly':
            # we're attached to an LCS in the parent assembly
            # expr = LCS_assembly.Placement * AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
            ( attLCS,     separator, rest1 ) = expr.partition('.Placement * AttachmentOffset * ')
            ( linkedDoc,  separator, rest2 ) = rest1.partition('#')
            ( linkLCS,    separator, rest3 ) = rest2.partition('.Placement ^ ')
            restFinal = rest3[0:2]
            attLink = parent
            attPart = 'None'
        # a part from the document is attached to an external part
        else:
            # expr = Rail_40x40_Y.Placement * Rails_V_Slot#LCS_AR.Placement * AttachmentOffset * LCS_Plaque_Laterale_sym.Placement ^ -1
            # expr = parentLink.Placement * externalDoc#LCS_parentPart * AttachmentOffset * LCS_linkedPart.Placement ^ -1
            ( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
            ( linkedDoc,  separator, rest2 ) = rest1.partition('#')
            ( attLCS,     separator, rest3 ) = rest2.partition('.Placement * AttachmentOffset * ')
            ( linkLCS,    separator, rest4 ) = rest3.partition('.Placement ^ ')
            restFinal = rest4[0:2]
    elif nbHash==2:
        # linked part and sister part in external documents to the parent assembly:
        # expr = ParentLink.Placement * ParentPart#LCS.Placement * AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
        ( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
        ( attPart,    separator, rest2 ) = rest1.partition('#')
        ( attLCS,     separator, rest3 ) = rest2.partition('.Placement * AttachmentOffset * ')
        ( linkedDoc,  separator, rest4 ) = rest3.partition('#')
        ( linkLCS,    separator, rest5 ) = rest4.partition('.Placement ^ ')
        restFinal = rest5[0:2]
    else:
        # complicated stuff, we'll do it later
        pass
    # final check, all options should give the correct data
    if restFinal=='-1' and attLink==parent :
        # wow, everything went according to plan
        # retval = ( expr, attPart, attLCS, constrLink, partLCS )
        retval = ( attLink, attLCS, linkLCS )
    return retval
"""






"""
    +-----------------------------------------------+
    |           split the ExpressionEngine          |
    |        of a linked Datum object to find       |
    |         the old attachment Part and LCS       |
    +-----------------------------------------------+
def splitExpressionDatum( expr ):
    retval = ( expr, 'None', 'None' )
    # expr is empty
    if not expr:
        return retval
    restFinal = ''
    attLink = ''
    if expr:
        # Look for a # to see whether the linked part is in the same document
        # expr = Link.Placement * LinkedPart#LCS.Placement * AttachmentOffset
        # expr = Link.Placement * LCS.Placement * AttachmentOffset
        if '#' in expr:
            # the linked part is in another document
            # expr = Link.Placement * LinkedPart#LCS.Placement * AttachmentOffset
            ( attLink, separator, rest1 ) = expr.partition('.Placement * ')
            ( attPart, separator, rest2 ) = rest1.partition('#')
            ( attLCS,  separator, rest3 ) = rest2.partition('.Placement * ')
            restFinal = rest3[0:16]
        else:
            # the linked part is in the same document
            # expr = Link.Placement * LCS.Placement * AttachmentOffset
            ( attLink, separator, rest1 ) =  expr.partition('.Placement * ')
            ( attLCS,  separator, rest2 ) = rest1.partition('.Placement * ')
            restFinal = rest2[0:16]
            attPart = 'unimportant'
        if restFinal=='AttachmentOffset':
            # wow, everything went according to plan
            retval = ( attLink, attPart, attLCS )
            #self.expression.setText( attPart +'***'+ attLCS )
        else:
            # rats ! But still, if the decode is unsuccessful, put some text
            retval = ( restFinal, 'None', 'None' )
    return retval
"""



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


def getSelectedLink():
    # check that there is an App::Part called 'Model'
    #if App.ActiveDocument.getObject('Model') and App.ActiveDocument.Model.TypeId == 'App::Part':
    #if checkModel():
    retval = None
    selection = Gui.Selection.getSelection()
    if len(selection)==1:
        selObj = selection[0]
        # it's an App::Link
        if selObj.isDerivedFrom('App::Link') and selObj.LinkedObject is not None and selObj.LinkedObject.TypeId in containerTypes:
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





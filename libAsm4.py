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
    |           Object helper functions           |
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
        container = result.getParentGeoFeatureGroup()
        if container:
            container.recompute()
        if result.Document:
            result.Document.recompute()
    return result
 
 
def placeObjectToLCS( attObj, attLink, attDoc, attLCS ):
    expr = makeExpressionDatum( attLink, attDoc, attLCS )
    # indicate the this fastener has been placed with the Assembly4 workbench
    if not hasattr(attObj,'AssemblyType'):
        Asm4.makeAsmProperties(attObj)
    attObj.AssemblyType = 'Asm4EE'
    # the fastener is attached by its Origin, no extra LCS
    attObj.AttachedBy = 'Origin'
    # store the part where we're attached to in the constraints object
    attObj.AttachedTo = attLink+'#'+attLCS
    # load the built expression into the Expression field of the constraint
    attObj.setExpression( 'Placement', expr )
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
    if reset:
        obj.AssemblyType = ''
        obj.AttachedBy = ''
        obj.AttachedTo = ''
        obj.AttachmentOffset = App.Placement()
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


# custum icon
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

# checks whether there is an Asm4 Model in the active document
def checkModel():
    retval = None
    if App.ActiveDocument and App.ActiveDocument.getObject('Model'):
        model = App.ActiveDocument.getObject('Model')
        if model.TypeId=='App::Part':
            retval = model
    return retval

# checks whether an App::Link is to an App::Part
def isLinkToPart(obj):
    if obj.TypeId == 'App::Link' and hasattr(obj.LinkedObject,'isDerivedFrom'):
        if  obj.LinkedObject.isDerivedFrom('App::Part') or obj.LinkedObject.isDerivedFrom('PartDesign::Body'):
            return True
    else:
        return False


# get from the selected datum the corresponding link
def getLinkAndDatum():
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

        selObj = Gui.Selection.getSelection()[0]
        # a datum is selected
        if selObj.TypeId in datumTypes:
            # this returns the selection hierarchy in the form 'linkName.datumName.'
            selTree = Gui.Selection.getSelectionEx("", 0)[0].SubElementNames[0]
            (parents, toto, dot) = selTree.partition('.'+selObj.Name)
            link = App.ActiveDocument.getObject( parents )
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


# get from two selected datums the corresponding links
def getLinkAndDatum2():
    retval = (None, None, None, None)
    # only for Asm4 
    if checkModel() and len(Gui.Selection.getSelection()) == 2:
        parentAssembly = App.ActiveDocument.Model
        # find all the links to Part or Body objects
        childrenTable = []
        for objStr in parentAssembly.getSubObjects():
            # the string ends with a . that must be removed
            obj = App.ActiveDocument.getObject( objStr[0:-1] )
            if isLinkToPart(obj):
                # add it to our tree table if it's a link to an App::Part ...
                childrenTable.append( obj )

        selObjA = Gui.Selection.getSelection()[0]
        selObjB = Gui.Selection.getSelection()[1]
        # two datum objects are selected
        if ((selObjA.TypeId in datumTypes) and (selObjB.TypeId in datumTypes)):
            # this returns the selection hierarchy in the form 'linkName.datumName.'
            selTreeA = Gui.Selection.getSelectionEx("", 0)[0].SubElementNames[0]
            selTreeB = Gui.Selection.getSelectionEx("", 0)[0].SubElementNames[1]
            (parentsA, totoA, dotA) = selTreeA.partition('.'+selObjA.Name)
            (parentsB, totoB, dotB) = selTreeB.partition('.'+selObjB.Name)
            linkA = App.ActiveDocument.getObject( parentsA )
            linkB = App.ActiveDocument.getObject( parentsB )
            if (dotA =='.' and linkA in childrenTable) and (dotB =='.' and linkB in childrenTable):
                retval = (linkA, selObjA, linkB, selObjB)

            else:
                # see whether the datum objects are in a group, some people like to do that
                (parentsA2, dotA, groupNameA) = parentsA.partition('.')
                (parentsB2, dotB, groupNameB) = parentsB.partition('.')
                linkA2 = App.ActiveDocument.getObject( parentsA2 )
                linkB2 = App.ActiveDocument.getObject( parentsB2 )
                groupA = App.ActiveDocument.getObject( groupNameA )
                groupB = App.ActiveDocument.getObject( groupNameB )
                if ((linkA2 in childrenTable and groupA.TypeId=='App::DocumentObjectGroup') and (linkB2 in childrenTable and groupB.TypeId=='App::DocumentObjectGroup')):
                    retval = (linkA2,selObjA,linkB2,selObjB)

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


# get the document groupe called Part 
# (if it exists, else returne None
def getPartsGroup():
    retval = None
    partsGroup = App.ActiveDocument.getObject('Parts')
    if partsGroup and partsGroup.TypeId=='App::DocumentObjectGroup':
        retval = partsGroup
    return retval
    


"""
    +-----------------------------------------------+
    |           get the next instance's name         |
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
    +----def findObjectLink(obj, doc = App.ActiveDocument):
    for o in doc.Objects:
        if hasattr(o, 'LinkedObject'):
            if o.LinkedObject == obj:
                return o
    return(None)
-------------------------------------------+
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
    |         returns the object Name (Label)       |
    +-----------------------------------------------+
"""
def nameLabel( obj ):
    if obj:
        txt = obj.Name
        if obj.Name!=obj.Label:
            txt += ' ('+obj.Label+')'
        return txt
    else:
        return None




"""
    +-----------------------------------------------+
    |         populate the ExpressionEngine         |
    |             for a linked App::Part            |
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




"""
    +-----------------------------------------------+
    |  split the ExpressionEngine of a linked part  |
    |          to find the old attachment LCS       |
    |   (in the parent assembly or a sister part)   |
    |   and the old target LCS in the linked Part   |
    +-----------------------------------------------+
"""
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
    +-----------------------------------------------+
    |         populate the ExpressionEngine         |
    |               for a Datum object              |
    |       linked to an LCS in a sister part       |
    +-----------------------------------------------+
"""
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
    |           split the ExpressionEngine          |
    |        of a linked Datum object to find       |
    |         the old attachment Part and LCS       |
    +-----------------------------------------------+
"""
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
    +-----------------------------------------------+
    |        ExpressionEngine for Fasteners         |
    +-----------------------------------------------+
"""
# is in the FastenersLib.py file



"""
    +-----------------------------------------------+
    |              Show/Hide the LCSs in            |
    |   the provided object and all its children    |
    +-----------------------------------------------+

def showChildLCSs(obj, show, processedLinks):
    #global processedLinks
    # if its a datum apply the visibility
    if obj.TypeId in datumTypes:
        obj.Visibility = show
    # if it's a link, look for subObjects
    elif obj.TypeId == 'App::Link' and obj.Name not in processedLinks:
        processedLinks.append(obj.Name)
        for objName in obj.LinkedObject.getSubObjects(1):
            linkedObj = obj.LinkedObject.Document.getObject(objName[0:-1])
            showChildLCSs(linkedObj, show, processedLinks)
    # if it's a container
    else:
        if obj.TypeId in containerTypes:
            for subObjName in obj.getSubObjects(1):
                subObj = obj.getSubObject(subObjName, 1)    # 1 for returning the real object
                if subObj != None:
                    if subObj.TypeId in datumTypes:
                        #subObj.Visibility = show
                        # Apparently obj.Visibility API is very slow
                        # Using the ViewObject.show() and ViewObject.hide() API runs at least twice faster
                        if show:
                            subObj.ViewObject.show()
                        else:
                            subObj.ViewObject.hide()
"""


"""
    +-----------------------------------------------+
    |        Selection Helper functions             |
    +-----------------------------------------------+

def getModelSelected():
    if App.ActiveDocument.getObject('Model') and App.ActiveDocument.Model.TypeId == 'App::Part':
        selection = Gui.Selection.getSelection()
        if len(selection)==1:
            selObj = selection[0]
            if selObj.Name == 'Model' and selObj.TypeId == 'App::Part':
                return selObj
    return None
"""

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
        if selObj.isDerivedFrom('App::Link') and selObj.LinkedObject.TypeId in containerTypes:
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





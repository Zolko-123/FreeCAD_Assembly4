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



# Types of datum objects
datumTypes = [  'PartDesign::CoordinateSystem', \
                'PartDesign::Plane',            \
                'PartDesign::Line',             \
                'PartDesign::Point']


partInfo =[     'Description',                  \
                'Reference',                    \
                'Supplier',                     \
                'SupplierDescription',          \
                'SupplierReference' ]

containerTypes = [  'App::Part', \
                    'PartDesign::Body' ]

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
            if obj.TypeId == 'App::Link' and hasattr(obj.LinkedObject,'isDerivedFrom'):
                if  obj.LinkedObject.isDerivedFrom('App::Part') or obj.LinkedObject.isDerivedFrom('PartDesign::Body'):
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
                if link2 in childrenTable and group.TypeId=='App::DocumentObjectGroup':
                    retval = (link2,selObj)
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
def makeExpressionPart( attLink, attPart, attLCS, linkedDoc, linkLCS ):
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
            ( attLCS, separator, rest1 ) = expr.partition('.Placement * AttachmentOffset * ')
            ( linkLCS, separator, rest2 ) = rest1.partition('.Placement ^ ')
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
            ( attLCS, separator, rest1 ) = expr.partition('.Placement * AttachmentOffset * ')
            ( linkedDoc, separator, rest2 ) = rest1.partition('#')
            ( linkLCS, separator, rest3 ) = rest2.partition('.Placement ^ ')
            restFinal = rest3[0:2]
            attLink = parent
            attPart = 'None'
    elif nbHash==2:
        # linked part and sister part in external documents to the parent assembly:
        # expr = ParentLink.Placement * ParentPart#LCS.Placement * AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
        ( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
        ( attPart,    separator, rest2 ) = rest1.partition('#')
        ( attLCS,     separator, rest3 ) = rest2.partition('.Placement * AttachmentOffset * ')
        ( linkedDoc, separator, rest4 ) = rest3.partition('#')
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
    if attLink and attPart and attLCS:
        # expr = Link.Placement * LinkedPart#LCS.Placement
        expr = attLink +'.Placement * '+ attPart +'#'+ attLCS +'.Placement * AttachmentOffset'
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
    |        Selection Helper functions             |
    +-----------------------------------------------+
"""
def getModelSelected():
    if App.ActiveDocument.getObject('Model') and App.ActiveDocument.Model.TypeId == 'App::Part':
        selection = Gui.Selection.getSelection()
        if len(selection)==1:
            selObj = selection[0]
            if selObj.Name == 'Model' and selObj.TypeId == 'App::Part':
                return selObj
    return False
    
def getSelection():
    # check that there is an App::Part called 'Model'
    if App.ActiveDocument.getObject('Model') and App.ActiveDocument.Model.TypeId == 'App::Part':
        selection = Gui.Selection.getSelection()
        if len(selection)==1:
            selObj = selection[0]
            # it's an App::Link
            if selObj.isDerivedFrom('App::Link') and selObj.LinkedObject.TypeId in linkedObjTypes:
                return selObj
    return None

# type of App::Link target objects we're dealing with
linkedObjTypes = [ 'App::Part', 'PartDesign::Body' ]

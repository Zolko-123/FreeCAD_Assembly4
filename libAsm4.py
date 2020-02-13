#!/usr/bin/env python
# coding: utf-8
# 
# libraries for FreeCAD's Assembly Without Solver


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
# this is the case for a link to a part coming from another document
def splitExpressionLink( expr, parent ):
    # expr = ParentLink.Placement * ParentPart#LCS.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
    bad_EE = ( '', 'None', 'None' )
    if not expr:
        return bad_EE
    if parent == 'Parent Assembly':
        # we're attached to an LCS in the parent assembly
        # expr = LCS_in_the_assembly.Placement * AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
        ( attLCS, separator, rest1 ) = expr.partition('.Placement * AttachmentOffset * ')
        ( linkedDoc, separator, rest2 ) = rest1.partition('#')
        ( linkLCS, separator, rest3 ) = rest2.partition('.Placement ^ ')
        restFinal = rest3[0:2]
        attLink = parent
        attPart = 'None'
        #return ( restFinal, 'None', 'None', 'None', 'None', 'None')
    else:
        # we're attached to an LCS in a sister part
        # expr = ParentLink.Placement * ParentPart#LCS.Placement * AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
        ( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
        ( attPart,    separator, rest2 ) = rest1.partition('#')
        ( attLCS,     separator, rest3 ) = rest2.partition('.Placement * AttachmentOffset * ')
        ( linkedDoc, separator, rest4 ) = rest3.partition('#')
        ( linkLCS,    separator, rest5 ) = rest4.partition('.Placement ^ ')
        restFinal = rest5[0:2]
        #return ( restFinal, 'None', 'None', 'None', 'None', 'None')
    if restFinal=='-1' and attLink==parent :
        # wow, everything went according to plan
        # retval = ( expr, attPart, attLCS, constrLink, partLCS )
        retval = ( attLink, attLCS, linkLCS )
    else:
        # rats ! Didn't succeed in decoding the ExpressionEngine.
        # But still, if the decode is unsuccessful, put some text
        retval = bad_EE
    return retval


# this is the case for a link to a part coming from the same document as the assembly
def splitExpressionDoc( expr, parent ):
    # expr = ParentLink.Placement * LCS_parent.Placement * constr_linkName.AttachmentOffset * LCS_linkedPart.Placement ^ -1
    # expr = LCS_model.Placement * constr_linkName.AttachmentOffset * LCS_linkedPart.Placement ^ -1
    bad_EE = ( '', 'None', 'None' )
    if not expr:
        return bad_EE
    if parent == 'Parent Assembly':
        # we're attached to an LCS in the parent assembly
        # expr = LCS_in_the_assembly.Placement * constr_linkName.AttachmentOffset * LCS_linkedPart.Placement ^ -1
        ( attLCS, separator, rest1 ) = expr.partition('.Placement * AttachmentOffset * ')
        ( linkLCS, separator, rest2 ) = rest1.partition('.Placement ^ ')
        restFinal = rest2[0:2]
        attLink = parent
        attPart = 'None'
        #return ( restFinal, 'None', 'None', 'None', 'None', 'None')
    else:
        # we're attached to an LCS in a sister part
        # expr = ParentLink.Placement * LCS_parent.Placement * constr_linkName.AttachmentOffset * LCS_linkedPart.Placement ^ -1
        ( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
        ( attLCS,     separator, rest2 ) = rest1.partition('.Placement * AttachmentOffset * ')
        ( linkLCS,    separator, rest3 ) = rest2.partition('.Placement ^ ')
        restFinal = rest3[0:2]
        #return ( restFinal, 'None', 'None', 'None', 'None', 'None')
    if restFinal=='-1' and attLink==parent :
        # wow, everything went according to plan
        # retval = ( expr, attPart, attLCS, constrLink, partLCS )
        retval = ( attLink, attLCS, linkLCS )
    else:
        # rats ! Didn't succeed in decoding the ExpressionEngine.
        # But still, if the decode is unsuccessful, put some text
        retval = bad_EE
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
    # expr = Link.Placement * LinkedPart#LCS.Placement
    ( attLink, separator, rest1 ) = expr.partition('.Placement * ')
    ( attPart, separator, rest2 ) = rest1.partition('#')
    ( attLCS,  separator, rest3 ) = rest2.partition('.')
    restFinal = rest3[0:9]
    if restFinal=='Placement':
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




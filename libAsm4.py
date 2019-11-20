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
__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Resources/icons' )
libPath = os.path.join( __dir__, 'Resources/library' )


import FreeCADGui as Gui
import FreeCAD as App




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
    |         populate the ExpressionEngine         |
    |               for a Datum object              |
    |       linked to an LCS in a sister part       |
    +-----------------------------------------------+
"""
def makeExpressionDatum( attLink, attPart, attLCS ):
    # check that everything is defined
    if attLink and attPart and attLCS:
        # expr = Link.Placement * LinkedPart#LCS.Placement
        expr = attLink +'.Placement * '+ attPart +'#'+ attLCS +'.Placement'
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




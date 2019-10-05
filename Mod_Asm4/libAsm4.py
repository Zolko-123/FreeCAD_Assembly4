#!/usr/bin/env python
# coding: utf-8
# 
# libraries for FreeCAD's Assembly Without Solver


"""
    +-----------------------------------------------+
    |          shouldn't these be DEFINE's ?        |
    +-----------------------------------------------+
"""
constraintPrefix = 'constr_'

import os
__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'icons' )


"""
    +-----------------------------------------------+
    |         populate the ExpressionEngine         |
    |             for a linked App::Part            |
    +-----------------------------------------------+
"""
def makeExpressionPart( attLink, attPart, attLCS, constrName, linkedPart, linkLCS ):
	# if everything is defined
	if attLink and attLCS and constrName and linkedPart and linkLCS:
		# this is where all the magic is, see:
		# 
		# https://forum.freecadweb.org/viewtopic.php?p=278124#p278124
		#
		# as of FreeCAD v0.19 the syntax is different:
		# https://forum.freecadweb.org/viewtopic.php?f=17&t=38974&p=337784#p337784
		# expr = ParentLink.Placement * ParentPart#LCS.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1
		# expr = LCS_in_the_assembly.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1
		expr = attLCS+'.Placement * '+constrName+'.AttachmentOffset * '+linkedPart+'#'+linkLCS+'.Placement ^ -1'
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
def splitExpressionPart( expr, parent ):
		# expr = ParentLink.Placement * ParentPart#LCS.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
	bad_EE = ( '', 'None', 'None', 'None', 'None', 'None')
	if not expr:
		return ( 'Empty expression x1', 'None', 'None', 'None', 'None', 'None')
	if parent == 'Parent Assembly':
		# we're attached to an LCS in the parent assembly
		# expr = LCS_in_the_assembly.Placement * constr_Name.AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
		( attLCS, separator, rest1 ) = expr.partition('.Placement * ')
		( constrName, separator, rest2 ) = rest1.partition('.AttachmentOffset * ')
		( linkedPart, separator, rest3 ) = rest2.partition('#')
		( linkLCS, separator, rest4 ) = rest3.partition('.Placement ^ ')
		restFinal = rest4[0:2]
		attLink = parent
		attPart = 'None'
		#return ( restFinal, 'None', 'None', 'None', 'None', 'None')
	else:
		# we're attached to an LCS in a sister part
		# expr = ParentLink.Placement * ParentPart#LCS.Placement * constr_Name.AttachmentOffset * LinkedPart#LCS.Placement ^ -1'			
		( attLink,    separator, rest1 ) = expr.partition('.Placement * ')
		( attPart,    separator, rest2 ) = rest1.partition('#')
		( attLCS,     separator, rest3 ) = rest2.partition('.Placement * ')
		( constrName, separator, rest4 ) = rest3.partition('.AttachmentOffset * ')
		( linkedPart, separator, rest5 ) = rest4.partition('#')
		( linkLCS,    separator, rest6 ) = rest5.partition('.Placement ^ ')
		restFinal = rest6[0:2]
		#return ( restFinal, 'None', 'None', 'None', 'None', 'None')
	if restFinal=='-1':
		# wow, everything went according to plan
		# retval = ( expr, attPart, attLCS, constrLink, partLCS )
		retval = ( attLink, attPart, attLCS, constrName, linkedPart, linkLCS)
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



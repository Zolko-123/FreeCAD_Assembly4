#!/usr/bin/env python
# coding: utf-8
# 
# libraries for FreeCAD's Assembly Without Solver


"""
    ╔═══════════════════════════════════════════════╗
    ║          shouldn't these be DEFINE's ?        ║
    ╚═══════════════════════════════════════════════╝
"""
constraintPrefix = 'constr_'



"""
    ╔═══════════════════════════════════════════════╗
    ║         populate the ExpressionEngine         ║
    ║             for a linked App::Part            ║
    ╚═══════════════════════════════════════════════╝
"""
def makeExpressionPart( attPart, attLCS, constrName, linkLCS ):
	# <<Cuve>>.Placement.multiply(<<Cuve>>.<<LCS_0001.>>.Placement).multiply(<<PLM_Screw_1>>.Placement).multiply(.<<LCS_0.>>.Placement.inverse())
	# expr = '<<'+attPart+'>>.Placement.multiply( <<'+attPart+'>>.<<'+attLCS+'.>>.Placement ).multiply( '+offsetName+'.Offset ).multiply( .<<'+linkLCS+'.>>.Placement.inverse() )'
	#
	# if everything is defined
	if attPart and attLCS and constrName and linkLCS:
		# this is where all the magic is, see:
		# 
		# https://forum.freecadweb.org/viewtopic.php?p=278124#p278124
		# 
		# expr = '<<'+ a_Part +'>>.Placement.multiply( <<'+ a_Part +'>>.<<'+ a_LCS +'.>>.Placement ).multiply( '+ constrName +'.Offset ).multiply( .<<'+ l_LCS +'.>>.Placement.inverse() )'
		#
		# the syntax for an attachment to the parent assembly is shorter
		if attPart == 'Parent Assembly':
			expr = '<<'+attLCS+'>>.Placement.multiply( <<'+constrName+'>>.AttachmentOffset ).multiply( .<<'+linkLCS+'.>>.Placement.inverse() )'
		else:
			expr = '<<'+attPart+'>>.Placement.multiply( <<'+attPart+'>>.<<'+attLCS+'.>>.Placement ).multiply( <<'+constrName+'>>.AttachmentOffset ).multiply( .<<'+linkLCS+'.>>.Placement.inverse() )'			
	else:
		expr = False
	return expr



"""
    ╔═══════════════════════════════════════════════╗
    ║         populate the ExpressionEngine         ║
    ║               for a Datum object              ║
    ║       linked to an LCS in a sister part       ║
    ╚═══════════════════════════════════════════════╝
"""
def makeExpressionDatum( attPart, attLCS ):
	# expr = '<<'+attPart+'>>.Placement.multiply( <<'+attPart+'>>.<<'+attLCS+'.>>.Placement ).multiply( '+offsetName+'.Offset ).multiply( .<<'+linkLCS+'.>>.Placement.inverse() )'
	if attPart and attLCS:
		# don't forget the last '.' !!!
		# <<LinkName>>.Placement.multiply( <<LinkName>>.<<LCS.>>.Placement )
		expr = '<<'+ attPart +'>>.Placement.multiply( <<'+ attPart +'>>.<<'+ attLCS +'.>>.Placement )'
	else:
		expr = False
	return expr



"""
    ╔═══════════════════════════════════════════════╗
    ║  split the ExpressionEngine of a linked part  ║
    ║          to find the old attachment LCS       ║
    ║   (in the parent assembly or a sister part)   ║
    ║   and the old target LCS in the linked Part   ║
    ╚═══════════════════════════════════════════════╝
"""
def splitExpressionPart( expr, attPart ):
	#self.expression.setText( expr )
	if attPart == 'Parent Assembly':
		# we're attached to an LCS in the parent assembly
		# <<attLCS>>.Placement.multiply(<<constr_Link>>.Offset).multiply(.<<partLCS.>>.Placement.inverse())
		( attLCS, separator, rest1 ) = expr[2:-1].partition('>>')
		( crap, separator, rest2 ) = rest1.partition('<<')
		( constrLink, separator, rest3 ) = rest2.partition('>>')
		( crap, separator, rest4 ) = rest3.partition('.<<')
		( partLCS, separator, rest5 ) = rest4.partition('.>>.')
		restFinal = rest5[0:9]
		#self.expression.setText( restFinal )
	else:
		# we're attached to an LCS in a sister part
		# <<attPart>>.Placement.multiply(<<attPart>>.<<attLCS.>>.Placement).multiply(<<constr_Link>>.Offset).multiply(.<<partLCS.>>.Placement.inverse())
		( attPart, separator, rest1 ) = expr[2:-1].partition('>>')
		( crap, separator, rest2 ) = rest1.partition('<<')
		( check_attPart, separator, rest3 ) = rest2.partition('>>.<<')
		( attLCS, separator, rest4 ) = rest3.partition('.>>.')
		( crap, separator, rest5 ) = rest4.partition('<<')
		( constrLink, separator, rest6 ) = rest5.partition('>>')
		( crap, separator, rest7 ) = rest6.partition('.<<')
		( partLCS, separator, rest8 ) = rest7.partition('.>>.')
		restFinal = rest8[0:9]
	if restFinal=='Placement':
		# wow, everything went according to plan
		retval = ( expr, attPart, attLCS, constrLink, partLCS )
	else:
		# rats ! But still, if the decode is unsuccessful, put some text
		retval = ( False, 'None', 'None', 'None', 'None' )
	return retval




"""
    ╔═══════════════════════════════════════════════╗
    ║           split the ExpressionEngine          ║
    ║        of a linked Datum object to find       ║
    ║         the old attachment Part and LCS       ║
    ╚═══════════════════════════════════════════════╝
"""
def splitExpressionDatum( expr ):
	# no sense to be attached to an LCS in the parent assembly
	# <<attPart>>.Placement.multiply( <<attPart>>.<<attLCS.>>.Placement )
	#self.expression.setText( self.old_Expression )
	( attPart, separator, rest1 ) = expr[2:-1].partition('>>')
	( crap, separator, rest2 ) = rest1.partition('<<')
	( check_attPart, separator, rest3 ) = rest2.partition('>>.<<')
	( attLCS, separator, rest4 ) = rest3.partition('.>>.')
	rest5 = rest4[0:9]
	if rest5=='Placement':
		# wow, everything went according to plan
		retval = ( expr, attPart, attLCS )
		#self.expression.setText( attPart +'***'+ attLCS )
	else:
		# rats ! But still, if the decode is unsuccessful, put some text
		retval = ( False, 'None', 'None' )
	return retval



#!/usr/bin/env python3
# coding: utf-8
# 
# newPartCmd.py 




import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import libAsm4 as Asm4



"""
    +-----------------------------------------------+
    |    a class to create all container objects    |
    |         App::Part or PartDesign::Body         |
    +-----------------------------------------------+
"""
class newPart:

    def __init__(self, partName):
        self.partName = partName
        if self.partName    == 'Part':
            self.partType    = 'App::Part'
            self.menutext    = "New Part"
            self.tooltip     = "Create a new Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Part.svg')
        elif self.partName  == 'Body':
            self.partType    = 'PartDesign::Body'
            self.menutext    = "New Body"
            self.tooltip     = "Create a new Body"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Body.svg')


    def GetResources(self):
        return {"MenuText"   : self.menutext,
                "ToolTip"    : self.tooltip,
                "Pixmap"     : self.icon 
                }


    def IsActive(self):
        if App.ActiveDocument:
            return(True)
        else:
            return(False)


    def checkPart(self):
        selectedPart = None
        # if an App::Part is selected
        if Gui.Selection.getSelection():
            selectedObj = Gui.Selection.getSelection()[0]
            if selectedObj.TypeId == 'App::Part':
                selectedPart = selectedObj
        return selectedPart


    def Activated(self):
        instanceName = Asm4.nextInstance(self.partName)
        text,ok = QtGui.QInputDialog.getText(None, self.tooltip, 'Enter new '+self.partName+' name :'+' '*30, text = instanceName)
        if ok and text:
            # create Part
            part = App.ActiveDocument.addObject(self.partType,text)
            # container ?
            container = self.checkPart()
            if container and part.Name!='Model':
                container.addObject(part)
            # add an LCS at the root of the Part, and attach it to the 'Origin'
            lcs0 = part.newObject('PartDesign::CoordinateSystem','LCS_0')
            lcs0.Support = [(part.Origin.OriginFeatures[0],'')]
            lcs0.MapMode = 'ObjectXY'
            lcs0.MapReversed = False
            # If the 'Part' group exists, move it there:
            partsGroup = App.ActiveDocument.getObject('Parts')
            if partsGroup and partsGroup.TypeId=='App::DocumentObjectGroup' :
                App.ActiveDocument.getObject('Parts').addObject(part)
            # recompute
            part.recompute()
            App.ActiveDocument.recompute()



# add the command to the workbench
Gui.addCommand( 'Asm4_newPart', newPart('Part') )
Gui.addCommand( 'Asm4_newBody', newPart('Body') )

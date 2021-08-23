#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# newPartCmd.py 




import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import Asm4_libs as Asm4



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
        elif self.partName  == 'Group':
            self.partType    = 'App::DocumentObjectGroup'
            self.menutext    = "New Group"
            self.tooltip     = "Create a new Group"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Group.svg')


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
        instanceName = Asm4.nextInstance( self.partName )
        text,ok = QtGui.QInputDialog.getText(None, self.tooltip, 'Enter new '+self.partName+' name :'+' '*30, text = instanceName)
        if ok and text:
            # create Part
            newPart = App.ActiveDocument.addObject(self.partType,text)
            # add LCS if appropriate (not for groups)
            if self.partType in Asm4.containerTypes:
                # add an LCS at the root of the Part, and attach it to the 'Origin'
                lcs0 = newPart.newObject('PartDesign::CoordinateSystem','LCS_0')
                lcs0.Support = [(newPart.Origin.OriginFeatures[0],'')]
                lcs0.MapMode = 'ObjectXY'
                lcs0.MapReversed = False
            # If an App::Part container is selected, move the created part/body/group there
            container = None
            if len(Gui.Selection.getSelection())==1:
                obj = Gui.Selection.getSelection()[0]
                if obj.TypeId == 'App::Part':
                    container = obj
            if container :
                if newPart.Name != 'Assembly':
                    container.addObject(newPart)
            # If the 'Part' group exists, move it there:
            else:
                partsGroup = App.ActiveDocument.getObject('Parts')
                if partsGroup and partsGroup.TypeId=='App::DocumentObjectGroup' and newPart.TypeId in Asm4.containerTypes:
                    if newPart.Name != 'Assembly':
                        partsGroup.addObject(newPart)
            # recompute
            newPart.recompute()
            App.ActiveDocument.recompute()



# add the command to the workbench
Gui.addCommand( 'Asm4_newPart',  newPart('Part') )
Gui.addCommand( 'Asm4_newBody',  newPart('Body') )
Gui.addCommand( 'Asm4_newGroup', newPart('Group'))

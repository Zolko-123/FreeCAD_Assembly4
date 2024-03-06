#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# newPartCmd.py 




import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import Asm4_libs as Asm4
from Asm4_Translate import translate


"""
    +-----------------------------------------------+
    |    a class to create all container objects    |
    |         App::Part or PartDesign::Body         |
    +-----------------------------------------------+
"""
class newPart:

    def __init__(self, partName):
        self.partName = partName
        if self.partName == "Part":
            self.partType = "App::Part"
            self.menutext = "New Part"
            self.tooltip = translate("Commands1", "Create a new Part")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Part.svg")
        elif self.partName == "Body":
            self.partType = "PartDesign::Body"
            self.menutext = "New Body"
            self.tooltip = translate("Commands1", "Create a new Body")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Body.svg")
        elif self.partName == "Group":
            self.partType = "App::DocumentObjectGroup"
            self.menutext = "New Group"
            self.tooltip = translate("Commands1", "Create a new Group")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Group.svg")

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
            newPart.Label = text 
            # add stuff if appropriate (not for groups)
            if self.partType in Asm4.containerTypes:
                # add an LCS at the root of the Part, and attach it to the 'Origin'
                lcs0 = Asm4.newLCS(newPart, 'PartDesign::CoordinateSystem', 'LCS_Origin', [(newPart.Origin.OriginFeatures[0],'')])
                lcs0.MapMode = 'ObjectXY'
                lcs0.MapReversed = False
                # set nice colors for the Origin planes
                for origin in App.ActiveDocument.findObjects(Type='App::Origin'):
                    if origin.getParentGeoFeatureGroup() == newPart:
                        index = origin.Name[6:]
                        App.ActiveDocument.getObject('YZ_Plane'+index).ViewObject.ShapeColor=(1.0, 0.0, 0.0)
                        App.ActiveDocument.getObject('XZ_Plane'+index).ViewObject.ShapeColor=(0.0, 0.6, 0.0)
                        App.ActiveDocument.getObject('XY_Plane'+index).ViewObject.ShapeColor=(0.0, 0.0, 0.8)
                        App.ActiveDocument.getObject('X_Axis'+index).Visibility = False
                        App.ActiveDocument.getObject('Y_Axis'+index).Visibility = False
                        App.ActiveDocument.getObject('Z_Axis'+index).Visibility = False
                        # but only show it for PartDesign Bodies
                        if self.partType=='PartDesign::Body':
                            origin.Visibility = True
                # add AttachmentEngine
                # oooops, no, creates problems because it creates an AttachmentOffset property that collides with Asm4
                # newPart.addExtension("Part::AttachExtensionPython")
            if newPart.Name != 'Assembly':
                container = None
                # If an App::Part or a Group container is selected, put the created part/body/group there
                if len(Gui.Selection.getSelection())==1:
                    obj = Gui.Selection.getSelection()[0]
                    if obj.TypeId=='App::Part' or obj.TypeId=='App::DocumentObjectGroup':
                        container = obj
                elif Asm4.getAssembly():
                    # if there is a Parts group:
                    partsGroup = App.ActiveDocument.getObject('Parts')
                    if partsGroup and partsGroup.TypeId=='App::DocumentObjectGroup' and newPart.TypeId in Asm4.containerTypes:
                        container = partsGroup
                    else:
                        container = Asm4.getAssembly()
                if container :
                    container.addObject(newPart)
            # recompute
            newPart.recompute()
            App.ActiveDocument.recompute()



# add the command to the workbench
Gui.addCommand( 'Asm4_newPart',  newPart('Part') )
Gui.addCommand( 'Asm4_newBody',  newPart('Body') )
Gui.addCommand( 'Asm4_newGroup', newPart('Group'))

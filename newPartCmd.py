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
            self.menutext = translate("Asm4_newPart", "New Part")
            self.tooltip = translate("Commands1", "Create a new Part")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Part.svg")
        elif self.partName == "Body":
            self.partType = "PartDesign::Body"
            self.menutext = translate("Asm4_newPart", "New Body")
            self.tooltip = translate("Commands1", "Create a new Body")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Body.svg")
        elif self.partName == "Group":
            self.partType = "App::DocumentObjectGroup"
            self.menutext = translate("Asm4_newPart", "New Group")
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
        text,ok = QtGui.QInputDialog.getText(None, self.tooltip, translate("Asm4_newPart", 'Enter new ')+self.partName+translate("Asm4_newPart", ' name :')+' '*30, text = instanceName)
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
                # Customize Origin planes (colors, visibility)
                # print("> New Body:", newPart.Name, newPart.Label)
                for feature in newPart.Origin.OriginFeatures:
                    if feature.Name[1:6] == "_Axis":
                        feature.Visibility = False
                    if feature.Name[0:8] == "XY_Plane":
                        feature.ViewObject.ShapeColor=(0.0, 0.0, 0.8)
                    if feature.Name[0:8] == "YZ_Plane":
                        feature.ViewObject.ShapeColor=(1.0, 0.0, 0.0)
                    if feature.Name[0:8] == "XZ_Plane":
                        feature.ViewObject.ShapeColor=(0.0, 0.6, 0.0)
                if self.partType=='PartDesign::Body':
                    newPart.Origin.Visibility = True
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
                    if partsGroup and partsGroup.TypeId=='App::DocumentObjectGroup' and newPart.TypeId != 'App::DocumentObjectGroup':
                        container = partsGroup
                    else:
                        # container = Asm4.getAssembly()
                        pass
                if container :
                    container.addObject(newPart)
            # recompute
            newPart.recompute()
            App.ActiveDocument.recompute()



# add the command to the workbench
Gui.addCommand( 'Asm4_newPart',  newPart('Part') )
Gui.addCommand( 'Asm4_newBody',  newPart('Body') )
Gui.addCommand( 'Asm4_newGroup', newPart('Group'))

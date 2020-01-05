#!/usr/bin/env python3
# coding: utf-8
# 
# newDatumCmd.py 



import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import libAsm4 as Asm4



"""
    +-----------------------------------------------+
    |      a class to create all Datum objects      |
    +-----------------------------------------------+
"""
class newDatum:
    "My tool object"
    def __init__(self, datumName):
        self.datumName = datumName
        if self.datumName   == 'Point':
            self.datumType   = 'PartDesign::Point'
            self.menutext    = "New Point"
            self.tooltip     = "Create a new Datum Point in a Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Point.svg')
            self.datumColor  = (0.00,0.00,0.00)
            self.datumAlpha  = []
        elif self.datumName == 'Axis':
            self.datumType   = 'PartDesign::Line'
            self.menutext    = "New Axis"
            self.tooltip     = "Create a new Datum Axis in a Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Axis.svg')
            self.datumColor  = (0.00,0.00,0.50)
            self.datumAlpha  = []
        elif self.datumName == 'Plane':
            self.datumType   = 'PartDesign::Plane'
            self.menutext    = "New Plane"
            self.tooltip     = "Create a new Datum Plane in a Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Plane.svg')
            self.datumColor  = (0.50,0.50,0.50)
            self.datumAlpha  = 80
        elif self.datumName == 'LCS':
            self.datumType   = 'PartDesign::CoordinateSystem'
            self.menutext    = "New Coordinate System"
            self.tooltip     = "Create a new Coordinate System in a Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_AxisCross.svg')
            self.datumColor  = []
            self.datumAlpha  = []
        elif self.datumName == 'Sketch':
            self.datumType   = 'Sketcher::SketchObject'
            self.menutext    = "New Sketch"
            self.tooltip     = "Create a new Sketch in a Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Sketch.svg')
            self.datumColor  = []
            self.datumAlpha  = []


    def GetResources(self):
        return {"MenuText": self.menutext,
                "ToolTip": self.tooltip,
                "Pixmap" : self.icon }


    def IsActive(self):
        if App.ActiveDocument:
            # is something selected ?
            if Gui.Selection.getSelection():
                # This command adds a new Sketch only to App::Part objects ...
                if Gui.Selection.getSelection()[0].TypeId == ('App::Part'):
                    return(True)
                else:
                    return(False)
            # ... or if there is a Model object in the active document:
            elif App.ActiveDocument.getObject('Model'):
                return(True)
            # 
            else:
                return(False)
        else:
            return(False)


    def checkPart(self):
        # if something is selected ...
        if Gui.Selection.getSelection():
            selectedObj = Gui.Selection.getSelection()[0]
            # ... and it's an App::Part:
            if selectedObj.TypeId == 'App::Part':
                return(selectedObj)
        # or of nothing is selected ...
        if App.ActiveDocument.getObject('Model'):
            # ... but there is a Model:
            return App.ActiveDocument.getObject('Model')
        return False



    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # check that we have somewhere to put our stuff (an App::Part or an Asm4 Model
        partChecked = self.checkPart()
        # check whether there is already a similar datum, and increment the instance number 
        instanceNum = 1
        while App.ActiveDocument.getObject( self.datumName+'_'+str(instanceNum) ):
            instanceNum += 1
        datumName = self.datumName+'_'+str(instanceNum)
        if partChecked:
            # input dialog to ask the user the name of the Sketch:
            text,ok = QtGui.QInputDialog.getText(None,'Create new '+self.datumName,
                    'Enter '+self.datumName+' name :                              ', text = datumName)
            if ok and text:
                # App.activeDocument().getObject('Model').newObject( 'Sketcher::SketchObject', text )
                createdDatum = partChecked.newObject( self.datumType, text )
                # automatic resizing of datum Plane sucks, so we set it to manual
                if self.datumType=='PartDesign::Plane':
                    createdDatum.ResizeMode = 'Manual'
                    createdDatum.Length = 100
                    createdDatum.Width = 100
                # if color or transparency is specified for this datum type
                if self.datumColor:
                    Gui.ActiveDocument.getObject(createdDatum.Name).ShapeColor = self.datumColor
                if self.datumAlpha:
                    Gui.ActiveDocument.getObject(createdDatum.Name).Transparency = self.datumAlpha
                Gui.Selection.clearSelection()
                # Gui.Selection.addSelection( App.ActiveDocument.Name, 'Model', createdDatum.Name+'.' )
                Gui.Selection.addSelection( App.ActiveDocument.Name, partChecked.Name, createdDatum.Name+'.' )
                # Gui.runCommand('Part_EditAttachment',0)
                Gui.runCommand('Part_EditAttachment')



"""
    +-----------------------------------------------+
    |      a class to create an LCS on a hole       |
    +-----------------------------------------------+
"""
class newHole:
    def GetResources(self):
        return {"MenuText": "New Hole LCS",
                "Accel": "Ctrl+H",
                "ToolTip": "Create a Coordinate System attached to a hole",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_Hole.svg')
                }


    def IsActive(self):
        selection = self.getSelection()
        if selection == None:
            return False
        else:
            return True


    def getSelection(self):
        # check that we have selected a circular edge
        selection = None
        if App.ActiveDocument:
            # 1 thing is selected:
            if len(Gui.Selection.getSelection()) == 1: 
                # check whether it's a circular edge:
                edge = Gui.Selection.getSelectionEx()[0]
                if len(edge.SubObjects) == 1:
                    edgeObj = edge.SubObjects[0]
                    # if the edge is circular
                    if hasattr(edgeObj,"Curve") and hasattr(edgeObj.Curve,"Center"):
                        # find the feature on which the edge is located
                        parentObj = Gui.Selection.getSelection()[0]
                        edgeName = edge.SubElementNames[0]
                        selection = ( parentObj, edgeName )
        return selection


    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        ( selectedObj, edge ) = self.getSelection()
        # loop until exhaustion or until we encounter an App::Part
        parentPart = selectedObj
        while parentPart and parentPart.TypeId!='App::Part':
            # get the parent object 
            # the direct parent might be a Body, but we want the Part containing the Body
            parentPart = parentPart.getParentGeoFeatureGroup()
        # if the solid having the edge is indeed in an App::Part
        if parentPart.TypeId=='App::Part':
            lcs = parentPart.newObject('PartDesign::CoordinateSystem','Hole')
            lcs.Support = [( selectedObj, (edge,) )]
            lcs.MapMode = 'Concentric'
            lcs.MapReversed = False
            lcs.ViewObject.Zoom = 0.5
            lcs.recompute()
            parentPart.recompute()




"""
    +-----------------------------------------------+
    |       add the commands to the workbench       |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_newPoint', newDatum('Point') )
Gui.addCommand( 'Asm4_newAxis',  newDatum('Axis')  )
Gui.addCommand( 'Asm4_newPlane', newDatum('Plane') )
Gui.addCommand( 'Asm4_newLCS',   newDatum('LCS')   )
Gui.addCommand( 'Asm4_newSketch',newDatum('Sketch'))
Gui.addCommand( 'Asm4_newHole',  newHole()         )


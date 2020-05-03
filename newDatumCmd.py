#!/usr/bin/env python3
# coding: utf-8
# 
# newDatumCmd.py 



import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

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
        # recognised types
        self.datumTypes = ['PartDesign::Point','PartDesign::Line','PartDesign::Plane','PartDesign::CoordinateSystem']
        self.containers = [ 'App::Part', 'PartDesign::Body' ]
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
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_CoordinateSystem.svg')
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
            # is something correct selected ?
            if self.checkSelection():
                return(True)
        return(False)


    def checkSelection(self):
        # if something is selected ...
        if Gui.Selection.getSelection():
            selectedObj = Gui.Selection.getSelection()[0]
            # ... and it's an App::Part or an datum object
            if selectedObj.TypeId=='App::Part' or selectedObj.TypeId=='PartDesign::Body'or selectedObj.TypeId in self.datumTypes:
                return(selectedObj)
        # or of nothing is selected ...
        elif App.ActiveDocument.getObject('Model'):
            # ... but there is a Model:
            return App.ActiveDocument.getObject('Model')
        # if we're here it's because we didn't find a good reason to not be here
        return None



    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # check that we have somewhere to put our stuff
        selectedObj = self.checkSelection()
        
        # check whether we have selected a container
        if selectedObj.TypeId in self.containers:
            parentContainer = selectedObj
        # if a datum object is selected we try to find the parent container
        elif selectedObj.TypeId in self.datumTypes:
            parent = selectedObj.getParentGeoFeatureGroup()
            if parent.TypeId in self.containers:
                parentContainer = parent
        # something went wrong
        else:
            Asm4.warningBox("I can't create a "+self.datumType+" with the current selections")
            
        # check whether there is already a similar datum, and increment the instance number 
        instanceNum = 1
        while App.ActiveDocument.getObject( self.datumName+'_'+str(instanceNum) ):
            instanceNum += 1
        datumName = self.datumName+'_'+str(instanceNum)
        if parentContainer:
            # input dialog to ask the user the name of the Sketch:
            text,ok = QtGui.QInputDialog.getText(None,'Create new '+self.datumName,
                    'Enter '+self.datumName+' name :'+' '*40, text = datumName)
            if ok and text:
                # App.activeDocument().getObject('Model').newObject( 'Sketcher::SketchObject', text )
                createdDatum = parentContainer.newObject( self.datumType, text )
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
                # highlight the created datum object
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection( App.ActiveDocument.Name, parentContainer.Name, createdDatum.Name+'.' )




"""
    +-----------------------------------------------+
    |      a class to create an LCS on a hole       |
    +-----------------------------------------------+
"""
class newHole:
    def GetResources(self):
        return {"MenuText": "New Hole Axis",
                "ToolTip": "Create a Datum Axis attached to a hole",
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
                    if hasattr(edgeObj,"Curve") and hasattr(edgeObj.Curve,"centerOfCurvature"):
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
        parentPart = selectedObj.getParentGeoFeatureGroup()
        # if the solid having the edge is indeed in an App::Part
        if parentPart and (parentPart.TypeId=='App::Part' or parentPart.TypeId=='PartDesign::Body'):
            # check whether there is already a similar datum, and increment the instance number 
            instanceNum = 1
            while App.ActiveDocument.getObject( 'HoleAxis_'+str(instanceNum) ):
                instanceNum += 1
            axis = parentPart.newObject('PartDesign::Line','HoleAxis_'+str(instanceNum))
            axis.Support = [( selectedObj, (edge,) )]
            axis.MapMode = 'AxisOfCurvature'
            axis.MapReversed = False
            axis.ResizeMode = 'Manual'
            axis.Length = 40
            Gui.ActiveDocument.getObject(axis.Name).ShapeColor = (0.0,1.0,1.0)
            Gui.ActiveDocument.getObject(axis.Name).Transparency = 0
            axis.recompute()
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


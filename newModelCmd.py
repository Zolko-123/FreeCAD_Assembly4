#!/usr/bin/env python3
# coding: utf-8
# 
# newModelCmd.py 



import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import Asm4_libs as Asm4




class newModel:
    """
    +-----------------------------------------------+
    |          creates the Assembly4 Model          |
    |             which is an App::Part             |
    |    with some extra features and properties    |
    +-----------------------------------------------+
    
def makeAssembly():
    assembly = App.ActiveDocument.addObject('App::Part','Assembly')
    assembly.Type='Assembly'
    assembly.addProperty( 'App::PropertyString', 'AssemblyType', 'Assembly' )
    assembly.AssemblyType = 'Part::Link'
    assembly.newObject('App::DocumentObjectGroup','Constraints')
    return assembly

    """
    def GetResources(self):
        tooltip = "Create a new Assembly4 Model"
        iconFile = os.path.join( Asm4.iconPath , 'Asm4_Model.svg')
        return {"MenuText": "New Assembly", "ToolTip": tooltip, "Pixmap" : iconFile }


    def IsActive(self):
        if App.ActiveDocument:
            return(True)
        else:
            return(False)


    # checks whether there already is an Asm4 Model in the document
    def checkModel(self):
        if self.activeDoc.getObject('Model'):
            if self.activeDoc.Model.TypeId=='App::Part' and self.activeDoc.Model.Type=='Assembly4 Model':
                Asm4.warningBox("This document already contains an Assembly4 Model.")
            else:
                Asm4.warningBox("This document already contains another FreeCAD object called \"Model\". I cannot create an Assembly4 Model.")
            return(True)
        else:
            return(False)


    # the real stuff
    def Activated(self):
        # get the current active document to avoid errors if user changes tab
        self.activeDoc = App.activeDocument()
        # check whether there is already Model in the document
        if not self.checkModel():
            # create a group 'Parts' to hold all parts in the assembly document (if any)
            # must be done before creating the Asm4 Model
            partsGroup = self.activeDoc.getObject('Parts')
            if partsGroup is None:
                partsGroup = self.activeDoc.addObject( 'App::DocumentObjectGroup', 'Parts' )

            # create a new App::Part called 'Model'
            assembly = self.activeDoc.addObject('App::Part','Model')
            # set the type as a "proof" that it's an Assembly4 Model
            assembly.Type='Assembly'
            assembly.addProperty( 'App::PropertyString', 'AssemblyType', 'Assembly' )
            assembly.AssemblyType = 'Part::Link'
            # add an LCS at the root of the Model, and attach it to the 'Origin'
            lcs0 = assembly.newObject('PartDesign::CoordinateSystem','LCS_Origin')
            lcs0.Support = [(assembly.Origin.OriginFeatures[0],'')]
            lcs0.MapMode = 'ObjectXY'
            lcs0.MapReversed = False
            # create a group Constraints to store future solver constraints there
            assembly.newObject('App::DocumentObjectGroup','Constraints')
            # create an object Variables to hold variables to be used in this document
            assembly.addObject(Asm4.createVariables())
            # create a group Configurations to store future solver constraints there
            assembly.newObject('App::DocumentObjectGroup','Configurations')
            
            # move existing parts and bodies at the document root to the Parts group
            # not nested inside other parts, to keep hierarchy
            if partsGroup.TypeId=='App::DocumentObjectGroup':
                for obj in self.activeDoc.Objects:
                    if obj.TypeId in Asm4.containerTypes and obj.Name!='Model' and obj.getParentGeoFeatureGroup() is None:
                        partsGroup.addObject(obj)
            else:
                Asm4.warningBox(   'There seems to already be a Parts object, you might get unexpected behaviour' )

            # recompute to get rid of the small overlays
            assembly.recompute()
            self.activeDoc.recompute()



# add the command to the workbench
Gui.addCommand( 'Asm4_newModel', newModel() )




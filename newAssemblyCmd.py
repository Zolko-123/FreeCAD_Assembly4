#!/usr/bin/env python3
# coding: utf-8
#
# newAssemblyCmd.py
#
# LGPL
# Copyright HUBERT Zoltán



import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4




class newAssemblyCmd:
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
        tooltip  = "<p>Create a new Assembly container</p>"
        iconFile = os.path.join( Asm4.iconPath , 'Asm4_Model.svg')
        return {"MenuText": "New Assembly", "ToolTip": tooltip, "Pixmap" : iconFile }


    def IsActive(self):
        if App.ActiveDocument:
            return(True)
        else:
            return(False)


    # the real stuff
    def Activated(self):
        # check whether there is already Model in the document
        # assy = App.ActiveDocument.getObject('Assembly')
        assy = Asm4.getAssembly()
        if assy is not None:
            if assy.TypeId=='App::Part':
                message = "This document already contains a valid Assembly, please use it"
                Asm4.warningBox(message)
                # set the Type to Assembly
                assy.Type = 'Assembly'
            else:
                message  = "This document already contains another FreeCAD object called \"Assembly\", "
                message += "but it's of type \""+assy.TypeId+"\", unsuitable for an assembly. I can\'t proceed."
                Asm4.warningBox(message)
            # abort
            return

        # there is no object called "Assembly"
        # create a group 'Parts' to hold all parts in the assembly document (if any)
        # must be done before creating the assembly
        partsGroup = App.ActiveDocument.getObject('Parts')
        if partsGroup is None:
            partsGroup = App.ActiveDocument.addObject( 'App::DocumentObjectGroup', 'Parts' )
        # create a new App::Part called 'Assembly'
        assembly = App.ActiveDocument.addObject('App::Part','Assembly')
        # set the type as a "proof" that it's an Assembly
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
        App.ActiveDocument.getObject('Constraints').Visibility = False
        # create an object Variables to hold variables to be used in this document
        assembly.addObject(Asm4.makeVarContainer())
        # create a group Configurations to store future solver constraints there
        assembly.newObject('App::DocumentObjectGroup','Configurations')
        App.ActiveDocument.getObject('Configurations').Visibility = False

        # move existing parts and bodies at the document root to the Parts group
        # not nested inside other parts, to keep hierarchy
        if partsGroup.TypeId=='App::DocumentObjectGroup':
            for obj in App.ActiveDocument.Objects:
                if obj.TypeId in Asm4.containerTypes and obj.Name!='Assembly' and obj.getParentGeoFeatureGroup() is None:
                    partsGroup.addObject(obj)
        else:
            Asm4.warningBox( 'There seems to already be a Parts object, you might get unexpected behaviour' )

        # recompute to get rid of the small overlays
        assembly.recompute()
        App.ActiveDocument.recompute()



# add the command to the workbench
Gui.addCommand( 'Asm4_newAssembly', newAssemblyCmd() )




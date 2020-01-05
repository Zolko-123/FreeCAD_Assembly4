#!/usr/bin/env python3
# coding: utf-8
# 
# newModelCmd.py 



import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import libAsm4 as Asm4




class newModel:
    """
    +-----------------------------------------------+
    |          creates the Assembly4 Model          |
    |             which is an App::Part             |
    |    with some extra features and properties    |
    +-----------------------------------------------+
    """
    def GetResources(self):
        return {"MenuText": "New Model",
                "Accel": "Ctrl+M",
                "ToolTip": "Create a new Assembly4 Model",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_Model.svg')
                }


    def IsActive(self):
        if App.ActiveDocument:
            return(True)
        else:
            return(False)


    def Activated(self):
        # get the current active document to avoid errors if user changes tab
        self.activeDoc = App.activeDocument()
        # check whether there is already Model in the document
        if not self.checkModel():
            # create a group 'Parts' to hold all parts in the assembly document (if any)
            if not self.activeDoc.getObject('Parts'):
                self.activeDoc.addObject( 'App::DocumentObjectGroup', 'Parts' )
            # create a new App::Part called 'Model'
            model = self.activeDoc.addObject('App::Part','Model')
            # add an LCS at the root of the Model, and attach it to the 'Origin'
            lcs0 = model.newObject('PartDesign::CoordinateSystem','LCS_0')
            lcs0.Support = [(model.Origin.OriginFeatures[0],'')]
            lcs0.MapMode = 'ObjectXY'
            lcs0.MapReversed = False
            # create a group Constraints to store future solver constraints there
            model.newObject('App::DocumentObjectGroup','Constraints')
            # create an object Variables to hold variables to be used in this document
            model.newObject('App::FeaturePython','Variables')
            # create a Configuration property
            model.addProperty('App::PropertyEnumeration', 'Configuration', 'Parameters')
            model.Configuration = ['Default']
            # recompute to get rid of the small overlays
            model.recompute()
            self.activeDoc.recompute()


    def checkModel(self):
        # check wheter there is already a Model in the document
        # we don't check whether it's an App::Part or not
        # Returns True if there is an object called 'Model'
        if self.activeDoc.getObject('Model'):
            Asm4.warningBox("There is already an Assembly4 Model in this document.")
            return(True)
        else:
            return(False)


# add the command to the workbench
Gui.addCommand( 'Asm4_newModel', newModel() )

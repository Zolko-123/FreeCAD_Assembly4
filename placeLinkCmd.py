#!/usr/bin/env python3
# coding: utf-8
#
# placeLinkCmd.py


import os, time

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4
from placeLinkUI import placeLinkUI
from placePartUI import placePartUI
import selectionFilter





"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class placeLinkCmd():
    def __init__(self):
        super(placeLinkCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Edit Placement of a Part",
                "ToolTip": "Move/Attach a Part in the assembly",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Place_Link.svg')
                }

    def IsActive(self):
        # We only insert a link into an Asm4  Model
        if App.ActiveDocument:
            ( obj, tree ) = Asm4.getSelectionTree()
            # something at 2nd level is selected
            if tree and len(tree)==2:
                # the root container must be an App::Part
                root = App.ActiveDocument.getObject(tree[0])
                if root and root.TypeId=='App::Part':
                    # check that the object has a Placement property
                    if hasattr(obj,'Placement') and obj.getTypeIdOfProperty('Placement')=='App::PropertyPlacement':
                        return True
        return False

    def Activated(self):
        # try with a regular App::Link
        selection = Asm4.getSelectedLink()
        # may-be an Asm4::VariantLink ?
        if selection is None:
            selection = Asm4.getSelectedVarLink()
        # if we found a valid link
        if selection is not None:
            """
    +-----------------------------------------------+
    |            placement of a link                |
    +-----------------------------------------------+
            """
            # check that it's in the root assembly
            parent = selection.getParentGeoFeatureGroup()
            if parent and parent == Asm4.getAssembly():
                # if it's a valid assembly and part
                if Asm4.isAsm4EE(selection):
                    # launch the UI in the task panel
                    ui = placeLinkUI()
                    Gui.Control.showDialog(ui)
                # else try to convert it
                else:
                    convert = Asm4.confirmBox("This Part wasn't assembled with this Assembly4 WorkBench, but I can convert it.")
                    if convert:
                        Asm4.makeAsmProperties( selection, reset=True )
                        # launch the UI in the task panel
                        ui = placeLinkUI()
                        Gui.Control.showDialog(ui)
            else:
                Asm4.warningBox('Please select a link in the assembly Model.')
        else:
            """
    +-----------------------------------------------+
    |    placement of any object with a Placement   |
    +-----------------------------------------------+
            """
            # or any part that has a Placement ?
            if len(Gui.Selection.getSelection())==1:
                selection = Gui.Selection.getSelection()[0]
                # object has a Placement property
                if hasattr(selection,'Placement') and selection.getTypeIdOfProperty('Placement')=='App::PropertyPlacement':
                    # we don't want to mess with obects that are attached with the Attacher (MapMode)
                    if hasattr(selection,'MapMode'):
                        FCC.PrintMessage('Object has MapMode property, you should use that\n')
                    else:
                        # check that it's in the root assembly
                        parent = selection.getParentGeoFeatureGroup()
                        if parent and parent == Asm4.getAssembly():
                            # is it's a virgin object, give it Asm4 properties
                            if not hasattr(selection,'SolverId'):
                                Asm4.makeAsmProperties(selection)
                            # if it's a valid assembly and part
                            if Asm4.isAsm4EE(selection):
                                # launch the UI in the task panel
                                ui = placePartUI()
                                Gui.Control.showDialog(ui)
                            # else try to convert it
                            else:
                                convert = Asm4.confirmBox("This Part wasn't assembled with this Assembly4 WorkBench, but I can convert it.")
                                if convert:
                                    Asm4.makeAsmProperties( selection, reset=True )
                                    # launch the UI in the task panel
                                    ui = placePartUI()
                                    Gui.Control.showDialog(ui)
                        # the selected object doesn't belong to the root assembly
                        else:
                            Asm4.warningBox('Please select an object in the assembly Model.')
                            return

    
"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_placeLink', placeLinkCmd() )

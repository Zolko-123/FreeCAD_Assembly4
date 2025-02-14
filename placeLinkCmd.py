#!/usr/bin/env python3
# coding: utf-8
#
# placeLinkCmd.py
#
# LGPL
# Copyright HUBERT Zoltán


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

        root = Gui.Selection.getSelectionEx("", 0)[0].Object
        obj = Gui.Selection.getSelection()[0]

        if App.ActiveDocument:

            if root and root.TypeId=='App::Part' and root.AssemblyType == "Part::Link":

                # check that the object has a Placement property
                if hasattr(obj,'Placement') and obj.getTypeIdOfProperty('Placement')=='App::PropertyPlacement':
                    return True

                elif obj.TypeId != "App:Link":
                    direct_parent = Asm4.getDirectParent()
                    if direct_parent and direct_parent is not root:
                        Gui.Selection.clearSelection()
                        Gui.Selection.addSelection(App.ActiveDocument.Name, direct_parent.Name)
                        obj = Gui.Selection.getSelection()[0]
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
            # check that it's in the root assembly
            parent = selection.getParentGeoFeatureGroup()
            if parent and parent == Asm4.getAssembly():
                # if it's a valid assembly and part
                if Asm4.isAsm4EE(selection):
                    # BUGFIX: if the part was corrupted by Assembly4 v0.11.5:
                    if hasattr(selection,'MapMode'):
                        Asm4.warningBox("This Part has the Attachment extension, it can only be placed manually")
                    else:
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
            # or any part that has a Placement ?
            if len(Gui.Selection.getSelection())==1:

                selection = Gui.Selection.getSelection()[0]

                # object has a Placement property
                if hasattr(selection,'Placement') and selection.getTypeIdOfProperty('Placement')=='App::PropertyPlacement':
                    # we don't want to mess with obects that are attached with the Attacher (MapMode)
                    if hasattr(selection,'MapMode') and not Asm4.isAsm4EE(selection):
                        # FCC.PrintMessage('Object has MapMode property, you should use that\n')
                        Gui.runCommand('Part_EditAttachment')
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

                            # update selection if something inside the containers/link is selected
                            # specially when selecting objects by clicking in 3d model
                            if selection.TypeId != "App:Link":
                                direct_parent = Asm4.getDirectParent()
                                Gui.Selection.clearSelection()
                                Gui.Selection.addSelection(App.ActiveDocument.Name, direct_parent.Name)
                                selection = direct_parent
                                # selection = Gui.Selection.getSelection()[0]

                                if Asm4.isAsm4EE(selection):
                                    # launch the UI in the task panel
                                    ui = placePartUI()
                                    Gui.Control.showDialog(ui)
                                else:
                                    Asm4.warningBox('Please select an object in the assembly Model.')

                            else:
                                Asm4.warningBox('Please select an object in the assembly Model.')

                            return


"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_placeLink', placeLinkCmd() )

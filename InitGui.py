# -*- coding: utf-8 -*-
###################################################################################
#
#  InitGui.py
#  
#  Copyright 2018 Mark Ganson <TheMarkster> mwganson at gmail
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
###################################################################################

import asm4wb_locator
asm4wbPath = os.path.dirname( asm4wb_locator.__file__ )
asm4wb_icons_path = os.path.join( asm4wbPath, 'Resources/icons')

global main_Assembly4WB_Icon
main_Assembly4WB_Icon = os.path.join( asm4wb_icons_path , 'Assembly4.svg' )





"""
    +-----------------------------------------------+
    |            Initialize the workbench           |
    +-----------------------------------------------+
"""
class Assembly4_WorkBench(Workbench):
 
    global main_Assembly4WB_Icon

    MenuText = "Assembly 4"
    ToolTip = "Assembly 4 workbench"
    Icon = main_Assembly4WB_Icon

    
    def __init__(self):
        "This function is executed when FreeCAD starts"
        pass


    def Initialize(self):
        import newModelCmd       # creates a new App::Part container called 'Model'
        import newSketchCmd      # creates a new Sketch in 'Model'
        import newLCSCmd         # creates a new LCS in 'Model'
        import newPointCmd       # creates a new LCS in 'Model'
        import newPlaneCmd       # creates a new LCS in 'Model'
        import newPartCmd        # creates a new App::Part container called 'Model'
        import newBodyCmd        # creates a new Body in 'Model
        import insertLinkCmd     # inserts an App::Link to a 'Model' in another file
        import placeLinkCmd      # places a linked part by snapping LCS (in the Part and in the Assembly)
        import placeDatumCmd     # places an LCS relative to an external file (creates a local attached copy)
        import importDatumCmd    # creates an LCS in assembly and attaches it to an LCS relative to an external file
        import updateAssemblyCmd # updates all parts and constraints in the assembly
        self.listCmd =           [ "newModelCmd",   "newBodyCmd", "newPartCmd", "newSketchCmd", "newLCSCmd", "newPlaneCmd", "newPointCmd", "insertLinkCmd", "placeLinkCmd", "importDatumCmd", "placeDatumCmd", "updateAssemblyCmd" ] # A list of command names created in the line above
        self.itemsMenu =         [ "newModelCmd",   "newBodyCmd", "newPartCmd", "newSketchCmd", "newLCSCmd", "newPlaneCmd", "newPointCmd", "insertLinkCmd", "placeLinkCmd", "importDatumCmd", "placeDatumCmd", "updateAssemblyCmd" ] # A list of command names created in the line above
        self.itemsToolbar =      [ "newModelCmd",   "newBodyCmd", "newPartCmd", "newSketchCmd", "newLCSCmd", "newPlaneCmd", "newPointCmd", "insertLinkCmd", "placeLinkCmd", "importDatumCmd", "placeDatumCmd", "updateAssemblyCmd" ] # A list of command names created in the line above
        self.itemsContextMenu =  [ "insertLinkCmd", "placeLinkCmd",  "placeDatumCmd" ] # A list of command names created in the line above
        self.itemsCreateMenu =   [ "newSketchCmd",  "newBodyCmd",    "newLCSCmd",  "newPlaneCmd", "newPointCmd"] # A list of command names created in the line above
        self.appendToolbar("Assembly 4",self.itemsToolbar) # leave settings off toolbar
        self.appendMenu("&Assembly",self.itemsMenu) # creates a new menu
        #self.appendMenu(["&Edit","DynamicData"],self.list) # appends a submenu to an existing menu


    """
    +-----------------------------------------------+
    |          Standard necessary functions         |
    +-----------------------------------------------+
    """
    def Activated(self):
        "This function is executed when the workbench is activated"
        return


    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        return 


    def ContextMenu(self, recipient):
        "This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        self.appendContextMenu( "Assembly", self.itemsContextMenu ) # add commands to the context menu
        self.appendContextMenu( "Create", self.itemsCreateMenu ) # add commands to the context menu

 
    def GetClassName(self): 
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"



"""
    +-----------------------------------------------+
    |          actually make the workbench          |
    +-----------------------------------------------+
"""
wb = Assembly4_WorkBench()
Gui.addWorkbench(wb)






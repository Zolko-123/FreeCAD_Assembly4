# -*- coding: utf-8 -*-
###################################################################################
#
#  InitGui.py
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


import os

import asm4wb_locator
asm4wbPath = os.path.dirname( asm4wb_locator.__file__ )
asm4wb_icons_path = os.path.join( asm4wbPath, 'Resources/icons')

global main_Assembly4WB_Icon
main_Assembly4WB_Icon = os.path.join( asm4wb_icons_path , 'Assembly4.svg' )

# import treeSelectionOverride as selectionOverride


"""
    +-----------------------------------------------+
    |            Initialize the workbench           |
    +-----------------------------------------------+
"""
class Assembly4Workbench(Workbench):

    global main_Assembly4WB_Icon
    #global selectionOverride
    MenuText = "Assembly 4"
    ToolTip = "Assembly 4 workbench"
    Icon = main_Assembly4WB_Icon

    def __init__(self):
        "This function is executed when FreeCAD starts"
        pass

    def Activated(self):
        "This function is executed when the workbench is activated"
        #selectionOverride.Activate()
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        #selectionOverride.Deactivate()
        return 

    def GetClassName(self): 
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"


    def Initialize(self):
        import newModelCmd         # creates a new App::Part container called 'Model'
        import newDatumCmd         # creates a new LCS in 'Model'
        import newPartCmd          # creates a new App::Part container called 'Model'
        import infoPartCmd         # edits part information for BoM
        import insertLinkCmd       # inserts an App::Link to a 'Model' in another file
        import placeLinkCmd        # places a linked part by snapping LCS (in the Part and in the Assembly)
        import placeDatumCmd       # places an LCS relative to an external file (creates a local attached copy)
        import importDatumCmd      # creates an LCS in assembly and attaches it to an LCS relative to an external file
        import releaseAttachmentCmd# creates an LCS in assembly and attaches it to an LCS relative to an external file
        import VariablesLib        # creates an LCS in assembly and attaches it to an LCS relative to an external file
        import AnimationLib        # creates an LCS in assembly and attaches it to an LCS relative to an external file
        import updateAssemblyCmd   # updates all parts and constraints in the assembly
        #import newLinkArray        # creates a new array of App::Link
        #import makeLinkArray        # creates a new array of App::Link
        import gotoDocumentCmd     # opens the documentof the selected App::Link
        import Asm4_Measure        # Measure tool in the Task panel
        import makeBomCmd          # creates the parts list
        import HelpCmd             # shows a basic help window
        import showHideLcsCmd      # shows/hides all the LCSs
        import configurationEngine  # save/restore configuration

        # check whether the Fasteners workbench is installed
        if self.checkWorkbench('FastenersWorkbench'):
            # a library to handle fasteners from the FastenersWorkbench
            import FastenersLib
            FastenersCmd = 'Asm4_Fasteners'
        else:
            # a dummy library if the FastenersWorkbench is not installed
            import FastenersDummy
            FastenersCmd = 'Asm4_insertScrew'

        # create the toolbars and menus, nearly empty, to decide about their position
        self.appendToolbar("Assembly",["Asm4_newModel"])
        # self.appendToolbar("Design",["Asm4_newPart"])
        # self.appendMenu("&Design",["Asm4_newPart"])
        self.appendMenu("&Assembly",["Asm4_newModel"])
        self.appendMenu("&Help", ["Asm4_Help"])


        """
    +-----------------------------------------------+
    |                      Assembly                 |
    +-----------------------------------------------+
        """
        # commands to appear in the Assembly4 menu 'Assembly'
        itemsAssemblyMenu = [   "Asm4_newPart", 
                                "Asm4_newBody", 
                                "Asm4_insertLink", 
                                FastenersCmd, 
                                "Separator",
                                "Asm4_newSketch", 
                                "Asm4_newLCS", 
                                "Asm4_newPlane", 
                                "Asm4_newAxis", 
                                "Asm4_newPoint", 
                                "Asm4_newHole", 
                                "Asm4_importDatum", 
                                "Separator",
                                "Asm4_placeLink", 
                                "Asm4_placeFastener", 
                                "Asm4_placeDatum", 
                                "Asm4_releaseAttachment", 
                                #"Asm4_makeLinkArray",
                                "Separator",
                                "Asm4_infoPart", 
                                "Asm4_makeBOM", 
                                "Asm4_Measure", 
                                'Asm4_showLcs',
                                'Asm4_hideLcs',
                                "Asm4_addVariable", 
                                "Asm4_delVariable", 
                                "Asm4_Animate", 
                                "Asm4_updateAssembly"]
        self.appendMenu("&Assembly",itemsAssemblyMenu)
        # commands to appear in the Assembly4 toolbar
        itemsAssemblyToolbar = [ "Asm4_newPart", 
                                "Asm4_newBody", 
                                "Asm4_infoPart", 
                                "Asm4_insertLink", 
                                FastenersCmd, 
                                "Separator",
                                "Asm4_newSketch", 
                                'Asm4_createDatum',
                                "Asm4_importDatum", 
                                "Separator",
                                "Asm4_placeLink", 
                                'Asm4_placeFastener',
                                "Asm4_placeDatum", 
                                "Separator",
                                #"Asm4_makeLinkArray",
                                "Asm4_makeBOM", 
                                "Asm4_Measure", 
                                "Asm4_variablesCmd",
                                "Asm4_Animate",
                                "Asm4_updateAssembly"]
        self.appendToolbar("Assembly",itemsAssemblyToolbar)


    """
    +-----------------------------------------------+
    |                Contextual Menus               |
    +-----------------------------------------------+
    """
    def ContextMenu(self, recipient):
        # This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        contextMenu  = ['Asm4_gotoDocument'  ,
                        'Asm4_showLcs'       ,
                        'Asm4_hideLcs'       ]
        # commands to appear in the 'Assembly' sub-menu in the contextual menu (right-click)
        assemblySubMenu =[ "Asm4_insertLink"    , 
                        "Asm4_placeLink"     , 
                        "Asm4_importDatum"   ,
                        "Asm4_placeDatum"    ,
                        'Asm4_FSparameters'  ,
                        'Asm4_placeFastener' ,
                        'Separator'          ,
                        'Asm4_saveConfiguration',
                        'Asm4_restoreConfiguration']
        # commands to appear in the 'Create' sub-menu in the contextual menu (right-click)
        createSubMenu = [  "Asm4_newSketch",  
                        "Asm4_newBody", 
                        "Asm4_newLCS", 
                        "Asm4_newAxis", 
                        "Asm4_newPlane", 
                        "Asm4_newPoint", 
                        "Asm4_newHole", 
                        "Asm4_insertScrew", 
                        "Asm4_insertNut", 
                        "Asm4_insertWasher",
                        #"Asm4_makeLinkArray"
                        ]

        self.appendContextMenu( "", "Separator")
        self.appendContextMenu( "", contextMenu ) # add commands to the context menu
        self.appendContextMenu( "Assembly", assemblySubMenu ) # add commands to the context menu
        self.appendContextMenu( "Create", createSubMenu ) # add commands to the context menu
        self.appendContextMenu( "", "Separator")


    """
    +-----------------------------------------------+
    |               helper functions                |
    +-----------------------------------------------+
    """
    def checkWorkbench( self, workbench ):
        # checks whether the specified workbench (a 'string') is installed
        listWB = Gui.listWorkbenches()
        hasWB = False
        for wb in listWB.keys():
            if wb == workbench:
                hasWB = True
        return hasWB

    
    
    
    
"""
    +-----------------------------------------------+
    |          actually make the workbench          |
    +-----------------------------------------------+
"""
wb = Assembly4Workbench()
Gui.addWorkbench(wb)




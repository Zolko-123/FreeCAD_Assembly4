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

import treeSelectionOverride as selectionOverride

"""
    +-----------------------------------------------+
    |    Drop-down menu to switch Configurations    |
    +-----------------------------------------------+
"""
# from https://github.com/HakanSeven12/FreeCAD-Geomatics-Workbench/commit/d82d27b47fcf794bf6f9825405eacc284de18996
class dropDownCmdGroup:
    def __init__(self, cmdlist, menu, tooltip = None):
        self.cmdlist = cmdlist
        self.menu = menu
        if tooltip is None:
            self.tooltip = menu
        else:
            self.tooltip = tooltip

    def GetCommands(self):
        return tuple(self.cmdlist)

    def GetResources(self):
        return { 'MenuText': self.menu, 'ToolTip': self.tooltip }



"""
    +-----------------------------------------------+
    |            Initialize the workbench           |
    +-----------------------------------------------+
"""
class Assembly4Workbench(Workbench):

    global main_Assembly4WB_Icon
    global selectionOverride
    MenuText = "Assembly 4"
    ToolTip = "Assembly 4 workbench"
    Icon = main_Assembly4WB_Icon

    def __init__(self):
        "This function is executed when FreeCAD starts"
        pass

    def Activated(self):
        "This function is executed when the workbench is activated"
        selectionOverride.Activate()
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        selectionOverride.Deactivate()
        return 

    def GetClassName(self): 
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"


    def Initialize(self):
        global dropDownCmdGroup
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

        # create the toolbars and menus, nearly empty, to decide about their position
        self.appendToolbar("Assembly",["Asm4_newModel"])
        # self.appendToolbar("Design",["Asm4_newPart"])
        # self.appendMenu("&Design",["Asm4_newPart"])
        self.appendMenu("&Assembly",["Asm4_newModel"])
        self.appendMenu("&Help", ["Asm4_Help"])


        """
    +-----------------------------------------------+
    |                    DropDowns                  |
    +-----------------------------------------------+
        """
        # defines the drop-down button for Fasteners:
        insertFastenerList = [  'Asm4_insertScrew', 
                                'Asm4_insertNut', 
                                'Asm4_insertWasher', 
                                'Asm4_insertRod', 
                                'Asm4_FSparameters' ,
                                'Asm4_placeFastener'] 
        Gui.addCommand( 'Asm4_Fasteners', dropDownCmdGroup( insertFastenerList, 'Insert Fastener'))
        # check whether the Fasteners workbench is installed
        if self.checkWorkbench('FastenersWorkbench'):
            # a library to handle fasteners from the FastenersWorkbench
            import FastenersLib
            FastenersDropDown = 'Asm4_Fasteners'
        else:
            # a dummy library if the FastenersWorkbench is not installed
            import FastenersDummy
            FastenersDropDown = 'Asm4_insertScrew'

        # defines the drop-down button for Datum objects
        createDatumList = [     'Asm4_newLCS', 
                                'Asm4_newPlane', 
                                'Asm4_newAxis', 
                                'Asm4_newPoint', 
                                'Asm4_newHole' ]
        Gui.addCommand( 'Asm4_createDatum', dropDownCmdGroup( createDatumList, 'Create Datum Object'))


        # defines the drop-down button for boolean operations
        compBooleanList = [     "Part_Fuse", 
                                "Part_Common",
                                "Part_Cut", 
                                "Part_XOR",
                                "Part_Common", 
                                "Part_Slice", 
                                "Part_SliceApart", 
                                "Part_BooleanFragments",
                                "Part_Boolean" ]
        Gui.addCommand( 'Asm4_compBoolean', dropDownCmdGroup( compBooleanList, 'Boolean Operations'))


        """
    +-----------------------------------------------+
    |                      Assembly                 |
    +-----------------------------------------------+
        """
        # commands to appear in the Assembly4 menu 'Assembly'
        self.itemsAssemblyMenu = [ "Asm4_newPart", 
                                "Asm4_newBody", 
                                "Part_Import",
                                "Asm4_insertLink", 
                                "Asm4_insertScrew", 
                                "Asm4_insertNut", 
                                "Asm4_insertWasher",
                                'Asm4_insertRod', 
                                "Asm4_FSparameters",
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
                                "Asm4_releaseAttachment", 
                                "Asm4_placeFastener", 
                                "Asm4_placeDatum", 
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
        self.appendMenu("&Assembly",self.itemsAssemblyMenu)
        # commands to appear in the Assembly4 toolbar
        self.itemsAssemblyToolbar = [ "Asm4_newPart", 
                                "Asm4_newBody", 
                                "Asm4_infoPart", 
                                "Asm4_insertLink", 
                                FastenersDropDown, 
                                "Separator",
                                "Asm4_newSketch", 
                                'Asm4_newLCS', 
                                'Asm4_newPlane', 
                                'Asm4_newAxis', 
                                'Asm4_newPoint', 
                                "Asm4_newHole", 
                                "Asm4_importDatum", 
                                "Separator",
                                "Asm4_placeLink", 
                                #'Asm4_placeFastener',
                                "Asm4_placeDatum", 
                                "Separator",
                                #"Asm4_makeLinkArray",
                                "Asm4_makeBOM", 
                                "Asm4_Measure", 
                                "Asm4_addVariable", 
                                "Asm4_delVariable", 
                                "Asm4_Animate",
                                "Asm4_updateAssembly"]
        self.appendToolbar("Assembly",self.itemsAssemblyToolbar)


        """
    +-----------------------------------------------+
    |                Contextual Menus               |
    +-----------------------------------------------+
        """
        # commands to appear in the 'Assembly' sub-menu in the contextual menu (right-click)
        self.itemsContextMenu =["Asm4_insertLink"    , 
                                "Asm4_placeLink"     , 
                                "Asm4_placeFastener" , 
                                "Asm4_importDatum"   ,
                                "Asm4_placeDatum"    ,
                                'Asm4_FSparameters'  ,
                                'Asm4_placeFastener' ,
                                'Separator'          ,
                                'Asm4_showLcs'       ,
                                'Asm4_hideLcs'       ,
                                'Separator'          ,
                                'Asm4_saveConfiguration',
                                'Asm4_restoreConfiguration']
        # commands to appear in the 'Create' sub-menu in the contextual menu (right-click)
        self.itemsCreateMenu = ["Asm4_newSketch",  
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

        """
    +-----------------------------------------------+
    |                     Structure                 |
    +-----------------------------------------------+
        """
        # commands to add to the standard Structure toolbar
        itemsStructureToolbar = [ "Asm4_newBody", 
                                'Asm4_newLCS', 
                                'Asm4_newPlane', 
                                'Asm4_newAxis', 
                                'Asm4_newPoint', 
                                "Asm4_newSketch"]
        #self.removeToolbar('Std_LinkMake')
        #self.appendToolbar("Structure",itemsStructureToolbar)

        


    def ContextMenu(self, recipient):
        # This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        self.appendContextMenu( "", "Separator")
        self.appendContextMenu( "", ["Asm4_gotoDocument"] ) # add commands to the context menu
        self.appendContextMenu( "Assembly", self.itemsContextMenu ) # add commands to the context menu
        self.appendContextMenu( "Create", self.itemsCreateMenu ) # add commands to the context menu
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




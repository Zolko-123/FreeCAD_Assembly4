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

import FreeCAD
import Asm4_locator
from Asm4_Translate import _atr, QT_TRANSLATE_NOOP
global Asm4_icon, Asm4_path, Asm4_trans, _atr
Asm4_path = os.path.dirname( Asm4_locator.__file__ )
Asm4_icon = os.path.join( Asm4_path , '../Resources/icons/Assembly4.svg' )
Asm4_trans = os.path.join(Asm4_path, "../Resources/translations")


# I don't like this being here
import selectionFilter


"""
    +-----------------------------------------------+
    |            Initialize the workbench           |
    +-----------------------------------------------+
"""
class Assembly4Workbench(Workbench):

    global Asm4_icon
    global selectionFilter
    MenuText = _atr("Workbench","Assembly 4")
    ToolTip = _atr("Workbench","Assembly 4 workbench")
    Icon = Asm4_icon

    def __init__(self):
        "This function is executed when FreeCAD starts"

    def Activated(self):
        "This function is executed when the workbench is activated"
        # make buttons of the selection toolbar checkable
        from PySide import QtGui
        mainwin = Gui.getMainWindow()
        sf_tb = None
        for tb in mainwin.findChildren(QtGui.QToolBar):
            if tb.objectName()=='Selection Filter':
                sf_tb = tb
        # make all buttons except last one (clear selection filter) checkable
        if sf_tb is not None:
            for button in sf_tb.actions()[0:-1]:
                button.setCheckable(True)
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        selectionFilter.observerDisable()
        return

    def GetClassName(self):
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"


        """
    +-----------------------------------------------+
    |        This is where all is defined           |
    +-----------------------------------------------+
        """
    def Initialize(self):

        # check for FreeCAD version
        FCver = FreeCAD.Version()
        # print("This is FreeCAD version "+FCver[0]+"."+FCver[1]+"."+FCver[2]+"-"+FCver[3])
        if FCver[0]=='0' and FCver[1]=='22':
            try:
                git = int(FCver[3][0:5])
            except:
                git=666
            if isinstance(git, int) and git>35594 :
                FreeCAD.Console.PrintWarning("This version of FreeCAD ("+FCver[0]+"."+FCver[1]+"."+FCver[2]+"-"+str(git)+") ")
                FreeCAD.Console.PrintWarning("is not backward compatible with FreeCAD v0.21 and earlier\n")
                FreeCAD.Console.PrintWarning("It is rather suggested to use the stable FreeCAD v0.21 branch\n")

        # Translations
        # from Asm4_Translate import Qtranslate
        FreeCADGui.addLanguagePath(Asm4_trans)
        FreeCADGui.updateLocale()

        # Assembly4 version info
        # with file package.xml (FreeCAD ≥0.21)
        packageFile  = os.path.join( Asm4_path, 'package.xml' )
        try:
            metadata     = FreeCAD.Metadata(packageFile)
            Asm4_date    = metadata.Date
            Asm4_version = metadata.Version
        # with file VERSION (FreeCAD ≤0.20)
        except:
            versionPath  = os.path.join( Asm4_path, 'VERSION' )
            versionFile  = open(versionPath,"r")
            # read second line
            version = versionFile.readlines()[1]
            versionFile.close()
            # remove trailing newline
            Asm4_version = version[:-1]    
        
        FreeCAD.Console.PrintMessage("Initializing Assembly4 workbench"+ ' ('+Asm4_version+') .')
        FreeCADGui.updateGui()
        # import all stuff
        import newAssemblyCmd    # created an App::Part container called 'Assembly'
        self.dot()
        import newDatumCmd         # creates a new LCS in 'Model'
        self.dot()
        import newPartCmd          # creates a new App::Part container called 'Model'
        self.dot()
        import infoPartCmd         # edits part information for BoM
        self.dot()
        import insertLinkCmd       # inserts an App::Link to a 'Model' in another file
        self.dot()
        import placeLinkCmd        # places a linked part by snapping LCS (in the Part and in the Assembly)
        self.dot()
        import importDatumCmd      # creates an LCS in assembly and attaches it to an LCS relative to an external file
        self.dot()
        import releaseAttachmentCmd# creates an LCS in assembly and attaches it to an LCS relative to an external file
        self.dot()
        import makeBinderCmd       # creates an LCS in assembly and attaches it to an LCS relative to an external file
        self.dot()
        import VariablesLib        # creates an LCS in assembly and attaches it to an LCS relative to an external file
        self.dot()
        import AnimationLib        # creates an LCS in assembly and attaches it to an LCS relative to an external file
        self.dot()
        import updateAssemblyCmd   # updates all parts and constraints in the assembly
        self.dot()
        import makeArrayCmd        # creates a new array of App::Link
        self.dot()
        import variantLinkCmd      # creates a variant link
        self.dot()
        import gotoDocumentCmd     # opens the documentof the selected App::Link
        self.dot()
        import Asm4_Measure        # Measure tool in the Task panel
        self.dot()
        import makeBomCmd          # creates the parts list
        self.dot()
        import checkInterference   # check interferences btween parts inside the Assembly
        self.dot()
        import exportFiles         # creates a hierarchical tree listing of files in an assembly
        self.dot()
        import HelpCmd             # shows a basic help window
        self.dot()
        import showHideLcsCmd      # shows/hides all the LCSs
        self.dot()
        import configurationEngine # save/restore configuration
        self.dot()

        # Fasteners
        if self.checkWorkbench('FastenersWorkbench'):
            # a library to handle fasteners from the FastenersWorkbench
            import FastenersLib
            self.FastenersCmd = 'Asm4_Fasteners'
        else:
            # a dummy library if the FastenersWorkbench is not installed
            import FastenersDummy
            self.FastenersCmd = 'Asm4_insertScrew'
        self.dot()


        # Define Menus
        # commands to appear in the Assembly4 menu 'Assembly'
        self.appendMenu(FreeCAD.Qt.translate("Asm4", "&Assembly"), self.assemblyMenuItems())
        self.dot()

        # put all constraints related commands in a separate menu
        self.appendMenu(FreeCAD.Qt.translate("Asm4", "&Constraints"), self.constraintsMenuItems())
        self.dot()

        # self.appendMenu("&Geometry",["Asm4_newPart"])

        # additional entry in the Help menu
        # self.appendMenu(Qtranslate("Workbench", "&Help"), ["Asm4_Help"])
        self.appendMenu( FreeCAD.Qt.translate("Workbench", "&Help"), ["Asm4_Help"])
        self.dot()

        # Define Toolbars
        # commands to appear in the Assembly4 toolbar
        self.appendToolbar(FreeCAD.Qt.translate("Asm4", "Assembly"), self.assemblyToolbarItems())
        self.dot()

        # build the selection toolbar
        self.appendToolbar(FreeCAD.Qt.translate("Asm4", "Selection Filter"), self.selectionToolbarItems())
        self.dot()

        # self.appendToolbar("Geometry",["Asm4_newPart"])

        FreeCAD.Console.PrintMessage(" " + "done" + ".\n")
        """
    +-----------------------------------------------+
    |           Initialisation finished             |
    +-----------------------------------------------+
        """



    """
    +-----------------------------------------------+
    |            Assembly Menu & Toolbar            |
    +-----------------------------------------------+
    """
    def assemblyMenuItems(self):
        commandList = [ "Asm4_newAssembly",
                        "Asm4_newPart",
                        "Asm4_newBody",
                        "Asm4_newGroup",
                        "Asm4_newSketch",
                        'Asm4_createDatum',
                        self.FastenersCmd,
                        "Separator",
                        "Asm4_insertLink",
                        "Asm4_mirrorArray",
                        "Asm4_linearArray",
                        "Asm4_circularArray",
                        "Asm4_expressionArray",
                        "Asm4_variantLink",
                        "Separator",
                        "Asm4_cloneFastenersToAxes",
                        "Asm4_importDatum",
                        "Asm4_shapeBinder",
                        "Separator",
                        "Asm4_infoPart",
                        "Asm4_makeLocalBOM",
                        "Asm4_makeBOM",
                        "Asm4_listLinkedFiles",
                        "Asm4_checkInterference",
                        "Asm4_Measure",
                        'Asm4_showLcs',
                        'Asm4_hideLcs',
                        "Asm4_addVariable",
                        "Asm4_delVariable",
                        "Asm4_Animate",
                        "Asm4_openConfigurations"
                        ]
        return commandList

    def constraintsMenuItems(self):
        commandList = [ "Asm4_placeLink",
                        "Asm4_releaseAttachment",
                        "Separator",
                        "Asm4_updateAssembly",
                        "Separator",
                        ]
        return commandList

    def assemblyToolbarItems(self):
        commandList = [ "Asm4_newAssembly",
                        "Asm4_newPart",
                        "Asm4_newBody",
                        "Asm4_newGroup",
                        "Asm4_infoPart",
                        "Asm4_insertLink",
                        "Asm4_variantLink",
                        self.FastenersCmd,
                        "Separator",
                        "Asm4_newSketch",
                        'Asm4_createDatum',
                        "Asm4_importDatum",
                        "Asm4_shapeBinder",
                        "Separator",
                        "Asm4_placeLink",
                        "Asm4_releaseAttachment",
                        "Asm4_updateAssembly",
                        "Separator",
                        "Asm4_mirrorArray",
                        "Asm4_linearArray",
                        "Asm4_circularArray",
                        "Asm4_expressionArray",
                        "Asm4_variablesCmd",
                        "Separator",
                        "Asm4_Animate",
                        "Asm4_Measure",
                        "Asm4_makeBOM",
                        "Asm4_listLinkedFiles",
                        'Asm4_showLcs',
                        'Asm4_hideLcs',
                        "Asm4_checkInterference",
                        "Asm4_openConfigurations"
                        ]
        return commandList


    """
    +-----------------------------------------------+
    |                 Selection Toolbar             |
    +-----------------------------------------------+
    """
    def selectionToolbarItems(self):
        # commands to appear in the Selection toolbar
        commandList =  ["Asm4_SelectionFilterVertexCmd",
                        "Asm4_SelectionFilterEdgeCmd",
                        "Asm4_SelectionFilterFaceCmd",
                        "Asm4_selObserver3DViewCmd" ,
                        "Asm4_SelectionFilterClearCmd"]
        return commandList


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
        assemblySubMenu =[ "Asm4_insertLink" ,
                        "Asm4_placeLink"     ,
                        "Asm4_importDatum"   ,
                        'Asm4_FSparameters'  ,
                        'Separator'          ,
                        'Asm4_applyConfiguration']
        # commands to appear in the 'Create' sub-menu in the contextual menu (right-click)
        createSubMenu =["Asm4_newSketch",
                        "Asm4_newBody",
                        "Asm4_newLCS",
                        "Asm4_newAxis",
                        "Asm4_newPlane",
                        "Asm4_newPoint",
                        "Asm4_newHole",
                        "Asm4_insertScrew",
                        "Asm4_insertNut",
                        "Asm4_insertWasher",
                        'Separator',
                        'Asm4_newConfiguration']

        self.appendContextMenu("", "Separator")
        self.appendContextMenu("", contextMenu)  # add commands to the context menu
        self.appendContextMenu(FreeCAD.Qt.translate("Asm4", "Assembly"), assemblySubMenu)  # add commands to the context menu
        self.appendContextMenu(FreeCAD.Qt.translate("Asm4", "Create"), createSubMenu)  # add commands to the context menu
        self.appendContextMenu("", "Separator")



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

    # prints a dot in the consome window to show progress
    def dot(self):
        FreeCAD.Console.PrintMessage(".")
        FreeCADGui.updateGui()





"""
    +-----------------------------------------------+
    |          actually make the workbench          |
    +-----------------------------------------------+
"""
wb = Assembly4Workbench()
Gui.addWorkbench(wb)

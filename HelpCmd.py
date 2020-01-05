#!/usr/bin/env python3
# coding: utf-8
#
# HelpCmd.py


import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import libAsm4 as Asm4




"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class Asm4Help( QtGui.QDialog ):
    "My tool object"


    def __init__(self):
        super(Asm4Help,self).__init__()


    def GetResources(self):
        return {"MenuText": "Help for Assembly4",
                "ToolTip": "Show basic usage for FreeCAD and Assembly4",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_Help.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if App.ActiveDocument:
            # check that it's an Assembly4 'Model'
            if App.ActiveDocument.getObject('Model') and App.ActiveDocument.getObject('Model').TypeId=='App::Part':
                return True
        return False 


    def Activated(self):
        # Now we can draw the UI
        self.drawUI()
        self.show()


    """
    +-----------------------------------------------+
    |                      OK                       |
    +-----------------------------------------------+
    """
    def onOK(self):
        self.close()



    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        self.setWindowTitle('Help for FreeCAD and Assembly4')
        self.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumSize(600, 500)
        self.resize(600,500)
        self.setModal(False)
        # make this dialog stay above the others, always visible
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

        # Variable Type
        self.helpText = QtGui.QTextBrowser(self)
        self.helpText.move(10,25)
        self.helpText.setMinimumSize(580, 400)
        self.helpText.setSearchPaths( [os.path.join( Asm4.wbPath, 'Resources' )] )
        self.helpText.setSource( 'Asm4_Help.html' )
        #self.helpText.setText("Help Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.\n \nSed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?")

        # OK button
        self.OKButton = QtGui.QPushButton('OK', self)
        self.OKButton.setAutoDefault(True)
        self.OKButton.move(500, 450)
        self.OKButton.setDefault(True)

        # Actions
        self.OKButton.clicked.connect(self.onOK)




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_Help', Asm4Help() )

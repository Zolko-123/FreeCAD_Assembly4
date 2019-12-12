#!/usr/bin/env python3
# coding: utf-8
#
# placeDatumCmd.py


import time, math, re

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

from libAsm4 import *



"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class animateVariable( QtGui.QDialog ):
    "My tool object"


    def __init__(self):
        super(animateVariable,self).__init__()


    def GetResources(self):
        return {"MenuText": "Animate Assembly",
                "ToolTip": "Animate Assembly",
                "Pixmap" : os.path.join( iconPath , 'Asm4_GearsAnimate.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if App.ActiveDocument:
            # is this an Assembly4 Model ?
            if App.ActiveDocument.getObject('Model'):
                # are there Variables ?
                if App.ActiveDocument.getObject('Variables'):
                    return True
        return False 



    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):

        # grab the Variables container
        self.Variables = App.ActiveDocument.getObject('Variables')
        self.Model = App.ActiveDocument.getObject('Model')
        self.Run = True

        # Now we can draw the UI
        self.drawUI()
        self.show()

        # select the variables that are in the "Variables" group
        for prop in self.Variables.PropertiesList:
            if self.Variables.getGroupOfProperty(prop) == 'Variables':
                self.varList.addItem(prop)


    """
    +-----------------------------------------------+
    |                     Run                       |
    +-----------------------------------------------+
    vars = App.ActiveDocument.getObject('Variables')
    step = 2
    for angle in range( 0, 720+step, step ):
        vars.Angle_rot = angle
        App.ActiveDocument.recompute()
        FreeCADGui.updateGui()


    """
    def onRun(self):
        # the selected variable
        varName = self.varList.currentText()
        begin   = self.minValue.value()
        end     = self.maxValue.value()
        step    = self.stepValue.value()
        sleep   = self.sleepValue.value()
        # basic checks
        if varName:
            # if we go forwards ...
            if end>begin and step>0:
                varValue = begin
                while varValue <= end and self.Run:
                    setattr( self.Variables, varName, varValue )
                    #App.ActiveDocument.recompute()
                    App.ActiveDocument.Model.recompute('True')
                    Gui.updateGui()
                    varValue += step
                    time.sleep(sleep)
                self.Run = True
                return
            # ... or backwards
            elif end<begin and step<0:
                varValue = begin
                while varValue >= end and self.Run:
                    setattr( self.Variables, varName, varValue )
                    #App.ActiveDocument.recompute()
                    App.ActiveDocument.Model.recompute('True')
                    Gui.updateGui()
                    varValue += step
                    time.sleep(sleep)
                self.Run = True
                return
        return


    """
    +-----------------------------------------------+
    |                Emergency STOP                 |
    +-----------------------------------------------+
    """
    def onStop(self):
        self.Run = False
        return


    """
    +-----------------------------------------------+
    |                     Close                     |
    +-----------------------------------------------+
    """
    def onClose(self):
        self.close()


    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        self.setWindowTitle('Animate Assembly')
        self.setWindowIcon( QtGui.QIcon( os.path.join( iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumSize(470, 300)
        self.resize(470,300)
        self.setModal(False)
        # make this dialog stay above the others, always visible
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

        # select Variable
        self.varLabel = QtGui.QLabel(self)
        self.varLabel.setText("Select Variable")
        self.varLabel.move(10,25)
        # combobox showing all available variables
        self.varList = QtGui.QComboBox(self)
        self.varList.move(200,20)
        self.varList.setMinimumSize(260, 1)

        # Range
        self.rangeLabel = QtGui.QLabel(self)
        self.rangeLabel.setText("Range")
        self.rangeLabel.move(10,85)
        # Minimum
        self.minLabel = QtGui.QLabel(self)
        self.minLabel.setText("Begin :")
        self.minLabel.move(120,65)
        self.minValue = QtGui.QDoubleSpinBox(self)
        self.minValue.move(200,60)
        self.minValue.setMinimumSize(260, 1)
        self.minValue.setRange( -1000.0, 1000.0 )
        self.minValue.setValue( 0.0 )
        # Maximum
        self.maxLabel = QtGui.QLabel(self)
        self.maxLabel.setText("End :")
        self.maxLabel.move(120,105)
        self.maxValue = QtGui.QDoubleSpinBox(self)
        self.maxValue.move(200,100)
        self.maxValue.setMinimumSize(260, 1)
        self.maxValue.setRange( -1000.0, 1000.0 )
        self.maxValue.setValue( 10.0 )

        # Step
        self.stepLabel = QtGui.QLabel(self)
        self.stepLabel.setText("Step :")
        self.stepLabel.move(10,145)
        self.stepValue = QtGui.QDoubleSpinBox(self)
        self.stepValue.move(200,140)
        self.stepValue.setMinimumSize(260, 1)
        self.stepValue.setRange( -100.0, 100.0 )
        self.stepValue.setValue( 1.0 )

        # Sleep
        self.sleepLabel = QtGui.QLabel(self)
        self.sleepLabel.setText("Sleep (s) :")
        self.sleepLabel.move(10,185)
        self.sleepValue = QtGui.QDoubleSpinBox(self)
        self.sleepValue.move(200,180)
        self.sleepValue.setMinimumSize(260, 1)
        self.sleepValue.setRange( 0.0, 100.0 )
        self.sleepValue.setValue( 0.0 )

        # Buttons
        #
        # Cancel button
        self.CloseButton = QtGui.QPushButton('Close', self)
        self.CloseButton.setAutoDefault(False)
        self.CloseButton.move(10, 260)
        # Stop button
        self.StopButton = QtGui.QPushButton('Stop', self)
        self.StopButton.setAutoDefault(False)
        self.StopButton.move(190, 260)
        # OK button
        self.OKButton = QtGui.QPushButton('Run', self)
        self.OKButton.setAutoDefault(True)
        self.OKButton.move(380, 260)
        self.OKButton.setDefault(True)

        # Actions
        self.CloseButton.clicked.connect(self.onClose)
        self.StopButton.clicked.connect(self.onStop)
        self.OKButton.clicked.connect(self.onRun)




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_Animate', animateVariable() )

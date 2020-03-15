#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# AnimationLib.py



import os, time

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import libAsm4 as Asm4



"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class animateVariable( QtGui.QDialog ):
    "My tool object"


    def __init__(self):
        super(animateVariable,self).__init__()
        self.drawUI()



    def GetResources(self):
        return {"MenuText": "Animate Assembly",
                "ToolTip": "Animate Assembly",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_GearsAnimate.svg')
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
        self.show()

        # select the Float variables that are in the "Variables" group
        self.varList.clear()
        for prop in self.Variables.PropertiesList:
            if self.Variables.getGroupOfProperty(prop)=='Variables' :
                if self.Variables.getTypeIdOfProperty(prop)=='App::PropertyFloat' :
                    self.varList.addItem(prop)



    """
    +------------------------------------------------+
    |  fill default values when selecting a variable |
    +------------------------------------------------+
    """
    def onSelectVar(self):
        # the currently selected variable
        selectedVar = self.varList.currentText()
        # if it's indeed a property in the Variables object (one never knows)
        if selectedVar in self.Variables.PropertiesList:
            # get its value
            selectedVarValue = self.Variables.getPropertyByName(selectedVar)
            # initialise the Begin and End values with it
            self.minValue.setValue(selectedVarValue)
            self.maxValue.setValue(selectedVarValue)
        return



    """
    +-----------------------------------------------+
    |                     Run                       |
    +-----------------------------------------------+
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
            varValue = begin
            # if we go forwards ...
            if end>begin and step>0:
                while varValue <= end and self.Run:
                    setattr( self.Variables, varName, varValue )
                    self.slider.setValue(varValue)
                    App.ActiveDocument.Model.recompute('True')
                    Gui.updateGui()
                    varValue += step
                    time.sleep(sleep)
            # ... or backwards
            elif end<begin and step<0:
                while varValue >= end and self.Run:
                    setattr( self.Variables, varName, varValue )
                    self.slider.setValue(varValue)
                    App.ActiveDocument.Model.recompute('True')
                    Gui.updateGui()
                    varValue += step
                    time.sleep(sleep)
        self.Run = True
        return



    """
    +-----------------------------------------------+
    |                   Slider                      |
    +-----------------------------------------------+
    """
    def sliderMoved(self):
        self.Run = False
        varName = self.varList.currentText()
        varValue = self.slider.value()
        setattr( self.Variables, varName, varValue )
        App.ActiveDocument.Model.recompute('True')
        Gui.updateGui()
        return


    def onValuesChanged(self):
        self.sliderMinValue.setText( str(self.minValue.value()) )
        self.sliderMaxValue.setText( str(self.maxValue.value()) )
        self.slider.setRange( self.minValue.value(), self.maxValue.value() )
        self.slider.setSingleStep( self.stepValue.value() )
        return


    def stepMinus(self):
        return


    def stepPlus(self):
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
        self.Run = False
        self.close()


    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        # make this dialog stay above the others, always visible
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.setWindowTitle('Animate Assembly')
        self.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumWidth(470)
        self.setModal(False)
        # set main window widgets
        self.mainLayout = QtGui.QVBoxLayout(self)

        # Define the fields for the form ( label + widget )
        self.formLayout = QtGui.QFormLayout(self)
        # select Variable
        self.varList = QtGui.QComboBox(self)
        self.formLayout.addRow(QtGui.QLabel('Select Variable'),self.varList)
        # Range Minimum
        self.minValue = QtGui.QDoubleSpinBox(self)
        self.minValue.setRange( -1000000.0, 1000000.0 )
        self.formLayout.addRow(QtGui.QLabel('Range Begin'),self.minValue)
        # Maximum
        self.maxValue = QtGui.QDoubleSpinBox(self)
        self.maxValue.setRange( -1000000.0, 1000000.0 )
        self.formLayout.addRow(QtGui.QLabel('Range End'),self.maxValue)
        # Step
        self.stepValue = QtGui.QDoubleSpinBox(self)
        self.stepValue.setRange( -10000.0, 10000.0 )
        self.stepValue.setValue( 1.0 )
        self.formLayout.addRow(QtGui.QLabel('Step'),self.stepValue)
        # Sleep
        self.sleepValue = QtGui.QDoubleSpinBox(self)
        self.sleepValue.setRange( 0.0, 10.0 )
        self.sleepValue.setValue( 0.0 )
        self.formLayout.addRow(QtGui.QLabel('Sleep (s)'),self.sleepValue)
        # apply the layout
        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(QtGui.QLabel())

        # slider
        self.sliderLayout = QtGui.QHBoxLayout(self)
        self.slider = QtGui.QSlider()
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 10)
        self.slider.setTickInterval(0)
        self.sliderMinValue = QtGui.QLabel('Min')
        self.sliderMaxValue = QtGui.QLabel('Max')        
        #self.stepLeft  = QtGui.QPushButton('<', self)
        #self.stepRight = QtGui.QPushButton('>', self)
        #self.sliderLayout.addWidget(self.stepLeft)
        self.sliderLayout.addWidget(self.sliderMinValue)
        self.sliderLayout.addWidget(self.slider)
        self.sliderLayout.addWidget(self.sliderMaxValue)
        #self.sliderLayout.addWidget(self.stepRight)
        self.mainLayout.addLayout(self.sliderLayout)

        self.mainLayout.addWidget(QtGui.QLabel())
        self.mainLayout.addStretch()
        # the button row definition
        self.buttonLayout = QtGui.QHBoxLayout(self)
        # Close button
        self.CloseButton = QtGui.QPushButton('Close', self)
        self.buttonLayout.addWidget(self.CloseButton)
        self.buttonLayout.addStretch()
        # Stop button
        self.StopButton = QtGui.QPushButton('Stop', self)
        self.buttonLayout.addWidget(self.StopButton)
        self.buttonLayout.addStretch()
        # Run button
        self.RunButton = QtGui.QPushButton('Run', self)
        self.RunButton.setDefault(True)
        self.buttonLayout.addWidget(self.RunButton)
        # add buttons to layout
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.setLayout(self.mainLayout)

        # Actions
        self.varList.currentIndexChanged.connect( self.onSelectVar )
        self.slider.sliderMoved.connect(self.sliderMoved)
        self.CloseButton.clicked.connect(self.onClose)
        self.StopButton.clicked.connect(self.onStop)
        self.RunButton.clicked.connect(self.onRun)
        self.minValue.valueChanged.connect( self.onValuesChanged )
        self.maxValue.valueChanged.connect( self.onValuesChanged )
        self.stepValue.valueChanged.connect( self.onValuesChanged )
        #self.stepLeft.clicked.connect(self.stepMinus)
        #self.stepRight.clicked.connect(self.stepPlus)



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_Animate', animateVariable() )

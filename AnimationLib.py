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
class animateVariable():

    def __init__(self):
        super(animateVariable,self).__init__()
        self.UI = QtGui.QDialog()
        self.drawUI()



    def GetResources(self):
        return {"MenuText": "Animate Assembly",
                "ToolTip": "Animate Assembly",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_GearsAnimate.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if Asm4.checkModel() and App.ActiveDocument.getObject('Variables'):
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
        self.setRunning(False)

        # Now we can draw the UI
        self.UI.show()

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
        self.setRunning(True)
        # the selected variable
        varName = self.varList.currentText()
        begin   = self.minValue.value()
        end     = self.maxValue.value()
        step    = self.stepValue.value()
        sleep   = self.sleepValue.value()
        # basic checks
        if varName:
            # loop indefinitely
            if self.Loop.isChecked():
                while self.Run and self.Loop.isChecked():
                    self.runFwd(varName)
            # go back-and-forth indefinitely
            elif self.Pendulum.isChecked():
                while self.Run and self.Pendulum.isChecked():
                    self.runFwd(varName)
                    self.runBwd(varName)
            else:
                self.runFwd(varName)
        self.setRunning(False)
        return


    def runFwd( self, varName ):
        begin   = self.minValue.value()
        end     = self.maxValue.value()
        step    = self.stepValue.value()
        sleep   = self.sleepValue.value()
        varValue = begin
        # if we go positive ...
        if end>begin and step>0:
            while varValue <= end and self.Run:
                self.setVarValue(varName,varValue)
                self.slider.setValue(varValue)
                varValue += step
                time.sleep(sleep)
        # ... or negative
        elif end<begin and step<0:
            while varValue >= end and self.Run:
                self.setVarValue(varName,varValue)
                self.slider.setValue(varValue)
                varValue += step
                time.sleep(sleep)

    
    def runBwd( self, varName ):
        begin   = self.minValue.value()
        end     = self.maxValue.value()
        step    = self.stepValue.value()
        sleep   = self.sleepValue.value()
        varValue = end
        # if we went positive ...
        if end>begin and step>0:
            while varValue >= begin and self.Run:
                self.setVarValue(varName,varValue)
                self.slider.setValue(varValue)
                varValue -= step
                time.sleep(sleep)
        # ... or negative
        elif end<begin and step<0:
            while varValue <= begin and self.Run:
                self.setVarValue(varName,varValue)
                self.slider.setValue(varValue)
                varValue -= step
                time.sleep(sleep)


    def onLoop(self):
        self.setRunning(False)
        if self.Pendulum.isChecked() and self.Loop.isChecked():
            self.Pendulum.setChecked(False)
        return


    def onPendulum(self):
        self.setRunning(False)
        if self.Loop.isChecked() and self.Pendulum.isChecked():
            self.Loop.setChecked(False)
        return


    def setVarValue(self,name,value):
        setattr( self.Variables, name, value )
        App.ActiveDocument.Model.recompute('True')
        Gui.updateGui()


    """
    +-----------------------------------------------+
    |                   Slider                      |
    +-----------------------------------------------+
    """
    def sliderMoved(self):
        self.setRunning(False)
        varName = self.varList.currentText()
        varValue = self.slider.value()
        self.setVarValue(varName,varValue)
        #setattr( self.Variables, varName, varValue )
        #App.ActiveDocument.Model.recompute('True')
        #Gui.updateGui()
        return


    def onValuesChanged(self):
        self.setRunning(False)
        self.sliderMinValue.setText( str(self.minValue.value()) )
        self.sliderMaxValue.setText( str(self.maxValue.value()) )
        self.slider.setRange( self.minValue.value(), self.maxValue.value() )
        self.slider.setSingleStep( self.stepValue.value() )
        return



    """
    +-----------------------------------------------+
    |                Emergency STOP                 |
    +-----------------------------------------------+
    """
    def onStop(self):
        self.setRunning(False)
        return


    """
    +-----------------------------------------------+
    |                     Close                     |
    +-----------------------------------------------+
    """
    def onClose(self):
        self.setRunning(False)
        self.UI.close()


    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        # make this dialog stay above the others, always visible
        self.UI.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.UI.setWindowTitle('Animate Assembly')
        self.UI.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.UI.setMinimumWidth(470)
        self.UI.setModal(False)
        # set main window widgets
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        # Define the fields for the form ( label + widget )
        self.formLayout = QtGui.QFormLayout()
        # select Variable
        self.varList = QtGui.QComboBox()
        self.formLayout.addRow(QtGui.QLabel('Select Variable'),self.varList)
        # Range Minimum
        self.minValue = QtGui.QDoubleSpinBox()
        self.minValue.setRange( -1000000.0, 1000000.0 )
        self.formLayout.addRow(QtGui.QLabel('Range Begin'),self.minValue)
        # Maximum
        self.maxValue = QtGui.QDoubleSpinBox()
        self.maxValue.setRange( -1000000.0, 1000000.0 )
        self.formLayout.addRow(QtGui.QLabel('Range End'),self.maxValue)
        # Step
        self.stepValue = QtGui.QDoubleSpinBox()
        self.stepValue.setRange( -10000.0, 10000.0 )
        self.stepValue.setValue( 1.0 )
        self.formLayout.addRow(QtGui.QLabel('Step'),self.stepValue)
        # Sleep
        self.sleepValue = QtGui.QDoubleSpinBox()
        self.sleepValue.setRange( 0.0, 10.0 )
        self.sleepValue.setValue( 0.0 )
        self.formLayout.addRow(QtGui.QLabel('Sleep (s)'),self.sleepValue)
        # apply the layout
        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(QtGui.QLabel())

        # slider
        self.sliderLayout = QtGui.QHBoxLayout()
        self.slider = QtGui.QSlider()
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 10)
        self.slider.setTickInterval(0)
        self.sliderMinValue = QtGui.QLabel('Min')
        self.sliderMaxValue = QtGui.QLabel('Max')
        self.sliderLayout.addWidget(self.sliderMinValue)
        self.sliderLayout.addWidget(self.slider)
        self.sliderLayout.addWidget(self.sliderMaxValue)
        self.mainLayout.addLayout(self.sliderLayout)
        
        # loop and pendumlum tick-boxes
        self.Loop = QtGui.QCheckBox()
        self.Loop.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.Loop.setToolTip("Infinite Loop")
        self.Loop.setText("Loop")
        self.Loop.setChecked(False)
        self.mainLayout.addWidget(self.Loop)
        self.Pendulum = QtGui.QCheckBox()
        self.Pendulum.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.Pendulum.setToolTip("Back-and-forth pendulum")
        self.Pendulum.setText("Pendulum")
        self.Pendulum.setChecked(False)
        self.mainLayout.addWidget(self.Pendulum)

        self.mainLayout.addWidget(QtGui.QLabel())
        self.mainLayout.addStretch()
        # the button row definition
        self.buttonLayout = QtGui.QHBoxLayout()
        # Close button
        self.CloseButton = QtGui.QPushButton('Close')
        self.buttonLayout.addWidget(self.CloseButton)
        self.buttonLayout.addStretch()
        # Stop button
        self.StopButton = QtGui.QPushButton('Stop')
        self.buttonLayout.addWidget(self.StopButton)
        self.buttonLayout.addStretch()
        # Run button
        self.RunButton = QtGui.QPushButton('Run')
        self.RunButton.setDefault(True)
        self.buttonLayout.addWidget(self.RunButton)
        # add buttons to layout
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.varList.currentIndexChanged.connect( self.onSelectVar )
        self.slider.sliderMoved.connect(          self.sliderMoved)
        self.minValue.valueChanged.connect(       self.onValuesChanged )
        self.maxValue.valueChanged.connect(       self.onValuesChanged )
        self.stepValue.valueChanged.connect(      self.onValuesChanged )
        self.Loop.toggled.connect(                self.onLoop )
        self.Pendulum.toggled.connect(            self.onPendulum )
        self.CloseButton.clicked.connect(         self.onClose )
        self.StopButton.clicked.connect(self.onStop)
        self.RunButton.clicked.connect(           self.onRun )



    """
        +-----------------------------------------------+
        |       Helper to toggle Run State              |
        +-----------------------------------------------+
    """
    def setRunning(self, state):
        self.Run = state
        self.RunButton.setEnabled(not state)
        self.StopButton.setEnabled(state)

"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_Animate', animateVariable() )

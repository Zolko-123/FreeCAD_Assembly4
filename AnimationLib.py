#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# AnimationLib.py



import os, time

from PySide import QtGui, QtCore
from enum import Enum
import FreeCADGui as Gui
import FreeCAD as App

import libAsm4 as Asm4


"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class animateVariable():

    """
    +-----------------------------------------------+
    |           State and Transition Enums          |
    +-----------------------------------------------+
    """
    class AnimationState(Enum):
        STOPPED = 0
        RUNNING = 1

    class AnimationRequest(Enum):
        NONE = 0
        START = 1
        STOP = 2

    """
    +-----------------------------------------------+
    |         Initialization and Registration       |
    +-----------------------------------------------+
    """
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

        # Initialize States and timing logic.
        self.RunState = self.AnimationState.STOPPED
        self.reverseAnimation = False  # True flags when the animation is "in reverse" for the pendulum mode.
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.onTimerTick)

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
            self.beginValue.setValue(selectedVarValue)
            self.endValue.setValue(selectedVarValue)
        return



    """
    +-----------------------------------------------+
    |            Animation Tick Functions           |
    +-----------------------------------------------+
    """
    def initAnimation(self):
        # Set GUI-state, initial value and start the timer
        self.RunButton.setEnabled(False)
        self.StopButton.setEnabled(True)
        self.setVarValue(self.varList.currentText(), self.beginValue.value())
        sleep = self.sleepValue.value() * 1000.0
        self.timer.start(sleep)
        self.reverseAnimation = False

    def nextStep(self, reverse):
        # Calculate the next variable increment/decrement
        begin = self.beginValue.value()
        end   = self.endValue.value()
        step  = abs(self.stepValue.value())
        varName = self.varList.currentText()
        varValue  = self.Variables.getPropertyByName(varName)

        if reverse:
            begin, end = end, begin

        if begin < end:
            varValue += step
        elif begin > end:
            varValue -= step

        # Assert varValue is in currently set range (range can now update with the animation running)
        varValue = min(varValue, max(begin, end))
        varValue = max(varValue, min(begin, end))

        # Update document variable and slider
        self.setVarValue(varName, varValue)
        self.slider.setValue(varValue)

        # Flag when the end of one sweep is reached
        return (varValue == begin) or (varValue == end)


    def update(self, req):

        # STOPPED STATE; NO ANIMATION RUNNING
        if self.RunState == self.AnimationState.STOPPED:
            if req == self.AnimationRequest.START:
                self.RunState = self.AnimationState.RUNNING
                self.initAnimation()

        # RUNNING STATE
        elif self.RunState == self.AnimationState.RUNNING:
            endOfCycle = self.nextStep(self.reverseAnimation)
            stop = (req == self.AnimationRequest.STOP)
            stop |= endOfCycle and not (self.Pendulum.isChecked() or self.Loop.isChecked())
            sleep = self.sleepValue.value() * 1000.0
            self.timer.setInterval(sleep)

            if stop:
                self.RunButton.setEnabled(True)
                self.StopButton.setEnabled(False)
                self.timer.stop()
                self.RunState = self.AnimationState.STOPPED
            elif endOfCycle:
                if self.Loop.isChecked():
                    self.initAnimation()
                elif self.Pendulum.isChecked():
                    self.reverseAnimation = not self.reverseAnimation

        # SANITY CHECK
        else:
            print("Unknown State/Transition")


    def onTimerTick(self):
        self.update(self.AnimationRequest.NONE)


    def setVarValue(self,name,value):
        setattr( self.Variables, name, value )
        App.ActiveDocument.Model.recompute('True')
        Gui.updateGui()

    """
    +-----------------------------------------------+
    |            Loop or Pendulum Selector          |
    +-----------------------------------------------+
    """
    def onLoop(self):
        if self.Pendulum.isChecked() and self.Loop.isChecked():
            self.Pendulum.setChecked(False)
        return


    def onPendulum(self):
        if self.Loop.isChecked() and self.Pendulum.isChecked():
            self.Loop.setChecked(False)
        return


    """
    +-----------------------------------------------+
    |                   Slider                      |
    +-----------------------------------------------+
    """
    def sliderMoved(self):
        # Stop the animation when the user grabs the slider
        self.update(self.AnimationRequest.STOP)
        varName = self.varList.currentText()
        varValue = self.slider.value()
        self.setVarValue(varName, varValue)
        return


    def onValuesChanged(self):
        self.sliderMinValue.setText(str(self.beginValue.value()))
        self.sliderMaxValue.setText(str(self.endValue.value()))
        self.slider.setRange(self.beginValue.value(), self.endValue.value())
        self.slider.setSingleStep( self.stepValue.value() )
        return

    """
    +-----------------------------------------------+
    |                Star/Stop/Close                |
    +-----------------------------------------------+
    """

    def onRun(self):
        self.update(self.AnimationRequest.START)


    def onStop(self):
        self.update(self.AnimationRequest.STOP)
        return


    def onClose(self):
        self.update(self.AnimationRequest.STOP)
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
        self.beginValue = QtGui.QDoubleSpinBox()
        self.beginValue.setRange(-1000000.0, 1000000.0)
        self.formLayout.addRow(QtGui.QLabel('Range Begin'), self.beginValue)
        # Maximum
        self.endValue = QtGui.QDoubleSpinBox()
        self.endValue.setRange(-1000000.0, 1000000.0)
        self.formLayout.addRow(QtGui.QLabel('Range End'), self.endValue)
        # Step
        self.stepValue = QtGui.QDoubleSpinBox()
        self.stepValue.setRange( -10000.0, 10000.0 )
        self.stepValue.setValue( 1.0 )
        self.formLayout.addRow(QtGui.QLabel('Step Size'),self.stepValue)
        # Sleep
        self.sleepValue = QtGui.QDoubleSpinBox()
        self.sleepValue.setRange( 0.0, 10.0 )
        self.sleepValue.setValue( 0.0 )
        self.sleepValue.setSingleStep(0.01)
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
        self.StopButton.setEnabled(False)
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
        self.beginValue.valueChanged.connect(self.onValuesChanged)
        self.endValue.valueChanged.connect(self.onValuesChanged)
        self.stepValue.valueChanged.connect(      self.onValuesChanged )
        self.Loop.toggled.connect(                self.onLoop )
        self.Pendulum.toggled.connect(            self.onPendulum )
        self.CloseButton.clicked.connect(         self.onClose )
        self.StopButton.clicked.connect(self.onStop)
        self.RunButton.clicked.connect(           self.onRun )



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_Animate', animateVariable() )

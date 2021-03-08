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
        self.ForceGUIUpdate = False # True Forces GUI to update on every step of the animation.
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
        self.variableValue.setText('{:.2f}'.format(value))
        if self.ForceGUIUpdate:
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

    def onForceRender(self):
        self.ForceGUIUpdate = self.ForceRender.isChecked()


    """
    +-----------------------------------------------+
    |                   Slider                      |
    +-----------------------------------------------+
    """
    def sliderMoved(self):
        varName = self.varList.currentText()
        varValue = self.slider.value()
        self.setVarValue(varName, varValue)
        return


    def onValuesChanged(self):
        # Get range-values from spinboxes
        beginVal = self.beginValue.value()
        endVal   = self.endValue.value()

        # Update the slider's ranges
        # The slider will automatically settle to the nearest value possible based on the new begin/end/stepsize.
        self.slider.setRange(beginVal, endVal, self.stepValue.value())

        # Update the labels with the actual range of the slider
        self.sliderLeftValue.setText(str(self.slider.leftValue()))
        self.sliderRightValue.setText(str(self.slider.rightValue()))

        # Check the current variable state vs. the slider. Update if needed
        varName = self.varList.currentText()
        curVal = self.Variables.getPropertyByName(varName)
        sliderVal = self.slider.value()
        if curVal != sliderVal:
            self.setVarValue(varName, sliderVal)

        # Check whether the end of the range can actually be reached with the current stepping.
        # Flag label if needed.
        rangeShort = (self.slider.rightValue() < endVal) if (beginVal < endVal) else (self.slider.rightValue() > endVal)
        if rangeShort:
            self.sliderRightValue.setStyleSheet("background-color: tomato")
        else:
            self.sliderRightValue.setStyleSheet("background-color: none")


    """
    +-----------------------------------------------+
    |                Star/Stop/Close                |
    +-----------------------------------------------+
    """

    def onRun(self):
        self.update(self.AnimationRequest.START)


    def onStop(self):
        self.update(self.AnimationRequest.STOP)


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
        self.beginValue.setKeyboardTracking(False)
        self.formLayout.addRow(QtGui.QLabel('Range Begin'), self.beginValue)
        # Maximum
        self.endValue = QtGui.QDoubleSpinBox()
        self.endValue.setRange(-1000000.0, 1000000.0)
        self.endValue.setKeyboardTracking(False)
        self.formLayout.addRow(QtGui.QLabel('Range End'), self.endValue)
        # Step
        self.stepValue = QtGui.QDoubleSpinBox()
        self.stepValue.setRange( 0.01, 10000.0 )
        self.stepValue.setValue( 1.0 )
        self.stepValue.setKeyboardTracking(False)
        self.formLayout.addRow(QtGui.QLabel('Step Size'), self.stepValue)
        
        # Sleep
        self.sleepValue = QtGui.QDoubleSpinBox()
        self.sleepValue.setRange( 0.0, 10.0 )
        self.sleepValue.setValue( 0.0 )
        self.sleepValue.setSingleStep(0.01)
        self.sleepValue.setKeyboardTracking(False)
        self.formLayout.addRow(QtGui.QLabel('Sleep (s)'),self.sleepValue)
        # apply the layout
        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(QtGui.QLabel())

        # Current Variable Value
        self.curVarLayout = QtGui.QHBoxLayout()
        self.variableValue = QtGui.QLabel('Variable')
        self.curVarLayout.addWidget(QtGui.QLabel('Current Value:'))
        self.curVarLayout.addStretch()
        self.curVarLayout.addWidget(self.variableValue)

        self.mainLayout.addLayout(self.curVarLayout)

        # slider
        self.sliderLayout = QtGui.QHBoxLayout()
        self.slider = animationSlider()
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 10)
        self.slider.setTickInterval(0)
        self.sliderLeftValue = QtGui.QLabel('Begin')
        self.sliderRightValue = QtGui.QLabel('End')
        tt = "The last reachable variable value with the given stepping. "
        tt += "Flagged red in case this is not equal to the intended value. "
        tt += "The last step of the animation will be reduced to stay inside the configured limits."
        self.sliderRightValue.setToolTip(tt)
        self.sliderLayout.addWidget(self.sliderLeftValue)
        self.sliderLayout.addWidget(self.slider)
        self.sliderLayout.addWidget(self.sliderRightValue)

        self.mainLayout.addLayout(self.sliderLayout)


        # ForceUpdate, loop and pendulum tick-boxes
        self.ForceRender = QtGui.QCheckBox()
        self.ForceRender.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.ForceRender.setToolTip("Force GUI to update on every step.")
        self.ForceRender.setText("Force-render every step")
        self.ForceRender.setChecked(False)

        self.Loop = QtGui.QCheckBox()
        self.Loop.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.Loop.setToolTip("Infinite Loop")
        self.Loop.setText("Loop")
        self.Loop.setChecked(False)

        self.Pendulum = QtGui.QCheckBox()
        self.Pendulum.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.Pendulum.setToolTip("Back-and-forth pendulum")
        self.Pendulum.setText("Pendulum")
        self.Pendulum.setChecked(False)

        self.mainLayout.addWidget(self.Loop)
        self.cbLayout = QtGui.QFormLayout()
        self.cbLayout.addRow(self.ForceRender, self.Pendulum)
        self.mainLayout.addLayout(self.cbLayout)

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
        self.buttonLayout.addWidget(self.RunButton)

        # Add an invisibly dummy button to circumvent QDialogs default-button behavior.
        # We need the enter key to trigger spinbox-commits only, without also triggering button actions.
        self.DummyButton = QtGui.QPushButton('Dummy')
        self.DummyButton.setDefault(True)
        self.DummyButton.setVisible(False)
        self.buttonLayout.addWidget(self.DummyButton)

        # add buttons to layout
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.varList.currentIndexChanged.connect( self.onSelectVar )
        self.slider.sliderMoved.connect(          self.sliderMoved)
        self.slider.valueChanged.connect(self.sliderMoved)
        self.beginValue.valueChanged.connect(self.onValuesChanged)
        self.endValue.valueChanged.connect(self.onValuesChanged)
        self.stepValue.valueChanged.connect(      self.onValuesChanged )
        self.Loop.toggled.connect(                self.onLoop )
        self.Pendulum.toggled.connect(            self.onPendulum )
        self.ForceRender.toggled.connect(self.onForceRender)
        self.CloseButton.clicked.connect(         self.onClose )
        self.StopButton.clicked.connect(self.onStop)
        self.RunButton.clicked.connect(           self.onRun )




"""
    +-----------------------------------------------+
    |     Custom Slider handling inverse ranges     |     
    |               and steps != 1.                 |
    +-----------------------------------------------+
"""

class animationSlider(QtGui.QSlider):

    def __init__(self, parent=None):
        self.leftVal =  0.0
        self.rightVal = 1.0
        self.stepSize = 1.0
        super().__init__(parent)


    # All ranges will be mapped to positive whole numbers.
    # By definition, the "left hand side value" (begin range) will be reachable.
    # The last reachable "right hand side value" depends on the step-size
    # The functions below translate accordingly

    def setRange(self, leftVal, rightVal, stepSize=1.0):
        val = self.value()

        self.leftVal = leftVal
        self.rightVal = rightVal
        self.stepSize = abs(stepSize)
        if leftVal > rightVal:
            self.stepSize *= -1.0

        super().setRange(0, (rightVal - leftVal) / self.stepSize)

        # ensure that the exposed slider value stays stable and gets capped if needed
        sig = self.stepSize/abs(self.stepSize)
        val = max(val, leftVal * sig)
        val = min(val, rightVal * sig)
        self.setValue(val)


    def __calculateInternalValue__(self, value):
        return value * self.stepSize + self.leftVal

    def value(self):
        return self.__calculateInternalValue__(super().value())

    def leftValue(self):
        return self.__calculateInternalValue__(super().minimum())

    def rightValue(self):
        return self.__calculateInternalValue__(super().maximum())


    def setValue(self, value):
        super().setValue((value - self.leftVal) / self.stepSize)




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_Animate', animateVariable() )

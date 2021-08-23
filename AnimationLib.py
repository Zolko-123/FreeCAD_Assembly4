#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# AnimationLib.py



import os, numpy

from PySide import QtGui, QtCore
from enum import Enum
import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4

# from AnimationProvider import animationProvider



"""
    +-----------------------------------------------+
    |            animationProvider class            |
    +-----------------------------------------------+
"""
class animationProvider:
    #
    # Setup the scene for the next frame of the animation.
    # Set resetAnimation True for the first frame
    # Signals that the last frame has been reached by returning True
    #
    def nextFrame(self, resetAnimation) -> bool:
        raise NotImplementedError("animationProvider.nextFrame not implemented.")

    #
    # Optionally flag that pendulum (forth and back animation) is wanted.
    # Prevents the need to capture identical frames on the "returning path"
    # of the animation.
    #
    def pendulumWanted(self) -> bool:
        return False

    class Error(Exception):
        """
        Base class for exceptions thrown when issues with
        animating the scene from an animationProvider occur.
        """
        def __init__(self, shortMsg: str, detailMsg: str):
            self.shortMsg = shortMsg
            self.detailMsg = detailMsg


"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class animateVariable(animationProvider):

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
    |           Exception Definitions               |
    +-----------------------------------------------+
    """
    class variableInvalidError(animationProvider.Error):
        """
        Exception to be raised when animation fails because
        the selected variable is not valid/does not exist.
        """
        def __init__(self, varName):
            shortMsg = 'Variable name invalid'
            detailMsg = 'The selected variable name "' + varName + '" is not valid. ' + \
                    'Please select an existing variable.'
            super().__init__(shortMsg, detailMsg)
            self.varName = varName

    """
    +-----------------------------------------------+
    |         Initialization and Registration       |
    +-----------------------------------------------+
    """
    def __init__(self):
        super(animateVariable,self).__init__()
        self.UI = QtGui.QDialog()
        self.drawUI()
        self.MDIArea = Gui.getMainWindow().findChild(QtGui.QMdiArea)

        # Initialize States and timing logic.
        self.RunState = self.AnimationState.STOPPED
        self.reverseAnimation = False  # True flags when the animation is "in reverse" for the pendulum mode.
        self.ForceGUIUpdate = False  # True Forces GUI to update on every step of the animation.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(0)
        self.timer.timeout.connect(self.onTimerTick)

        self.ActiveDocument = None
        self.AnimatedDocument = None
        self.Variables = None
        self.knownDocumentList = []
        self.knownVariableList = []

        self.exporter = None


    def GetResources(self):
        return {"MenuText": "Animate Assembly",
                "ToolTip": "Animate Assembly",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_GearsAnimate.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if Asm4.getAssembly() and App.ActiveDocument.getObject('Variables'):
            return True
        return False



    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # grab the Variables container (just do it always, this prevents problems with newly opened docs)
        self.ActiveDocument = App.ActiveDocument
        self.Variables = self.AnimatedDocument.getObject('Variables') if self.AnimatedDocument else None
        # the root assembly in the current document
        self.rootAssembly = Asm4.getAssembly()

        self.updateDocList()
        self.updateVarList()

        # in case the dialog is newly opened, register for changes of the selected document
        if not self.UI.isVisible():
            self.MDIArea.subWindowActivated.connect(self.onDocChanged)
        self.UI.show()

    """
    +------------------------------------------------+
    |  fill default values when selecting a document |
    +------------------------------------------------+
    """

    def updateDocList(self):
        docDocs = ['- Select Document -']
        # Collect all documents currently available
        for doc in App.listDocuments():
            docDocs.append(doc)

        # only update the gui-element if documents actually changed
        if self.knownDocumentList != docDocs:
            self.docList.clear()
            self.docList.addItems(docDocs)
            self.knownDocumentList = docDocs
            
        # set current active documents per default
        #if self.AnimatedDocument is None:
        activeDoc = App.ActiveDocument
        if activeDoc in App.listDocuments().values():
            docIndex = list(App.listDocuments().values()).index(activeDoc)
            self.docList.setCurrentIndex(docIndex + 1)


    """
    +------------------------------------------------+
    |  fill default values when selecting a variable |
    +------------------------------------------------+
    """
    def updateVarList(self):
        docVars = ['- Select Variable (only float) -']
        # Collect all variables currently available in the doc
        if self.Variables:
            for prop in self.Variables.PropertiesList:
                if self.Variables.getGroupOfProperty(prop) == 'Variables':
                    if self.Variables.getTypeIdOfProperty(prop) == 'App::PropertyFloat':
                        docVars.append(prop)

        # only update the gui-element if variables actually changed
        if self.knownVariableList != docVars:
            self.varList.clear()
            self.varList.addItems(docVars)
            self.knownVariableList = docVars
            animationHints.cleanUp(self.Variables)

        # prevent active gui controls when no valid variable is selected
        self.onSelectVar()

    def onSelectDoc(self):
        self.update(self.AnimationRequest.STOP)
        # the currently selected document
        selectedDoc = self.docList.currentText()
        # if it's indeed a document (one never knows)
        documents = App.listDocuments()
        if len(selectedDoc) > 0 and selectedDoc in documents:
            # update vars
            self.AnimatedDocument = documents[selectedDoc]
            self.Variables = self.AnimatedDocument.getObject('Variables')
            self.updateVarList()
        else:
            self.AnimatedDocument = None
            self.Variables = None
            self.updateVarList()


    def onSelectVar(self):
        self.update(self.AnimationRequest.STOP)
        # the currently selected variable
        selectedVar = self.varList.currentText()
        # if it's indeed a property in the Variables object (one never knows)
        if self.isKnownVariable(selectedVar):
            # grab animationsHints related to the variable and init accordingly
            aniHints = animationHints.get(self.Variables, selectedVar)
            self.beginValue.setValue(aniHints[animationHints.Key.RangeBegin])
            self.endValue.setValue(aniHints[animationHints.Key.RangeEnd])
            self.stepValue.setValue(aniHints[animationHints.Key.StepSize])
            self.sleepValue.setValue(aniHints[animationHints.Key.SleepTime])
            self.Loop.setChecked(aniHints[animationHints.Key.Loop])
            self.Pendulum.setChecked(aniHints[animationHints.Key.Pendulum])
            self.enableDependentGuiElements(True)
        else:
            self.enableDependentGuiElements(False)

    def isKnownVariable(self, varName):
        """
        Returns True if a variable with name varName exists
        """
        return len(varName) > 0 and self.Variables and varName in self.Variables.PropertiesList


    """
    +-----------------------------------------------+
    |            Animation Tick Functions           |
    +-----------------------------------------------+
    """
    def initAnimation(self):
        # Set GUI-state, initial value and start the timer
        varName = self.varList.currentText()
        if not self.isKnownVariable(varName):
            self.updateVarList()
            raise animateVariable.variableInvalidError(varName)

        self.RunButton.setEnabled(False)
        self.StopButton.setEnabled(True)
        self.setVarValue(self.varList.currentText(), self.beginValue.value())
        self.reverseAnimation = False

    def nextStep(self, reverse):
        # Calculate the next variable increment/decrement
        begin = self.beginValue.value()
        end   = self.endValue.value()
        step  = abs(self.stepValue.value())
        varName = self.varList.currentText()
        if not self.isKnownVariable(varName):
            raise animateVariable.variableInvalidError(varName)
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
        # Flag out for end of cycle
        endOfCycle = False
        # STOPPED STATE; NO ANIMATION RUNNING
        if self.RunState == self.AnimationState.STOPPED:
            if req == self.AnimationRequest.START:
                self.initAnimation()
                self.RunState = self.AnimationState.RUNNING

        # RUNNING STATE
        elif self.RunState == self.AnimationState.RUNNING:
            stop = (req == self.AnimationRequest.STOP)
            if not stop:
                endOfCycle = self.nextStep(self.reverseAnimation)
            stop |= endOfCycle and not (self.Pendulum.isChecked() or self.Loop.isChecked())

            if stop:
                self.RunButton.setEnabled(True)
                self.StopButton.setEnabled(False)
                self.RunState = self.AnimationState.STOPPED
            elif endOfCycle:
                if self.Loop.isChecked():
                    self.initAnimation()
                elif self.Pendulum.isChecked():
                    self.reverseAnimation = not self.reverseAnimation

        # SANITY CHECK
        else:
            print("Unknown State/Transition")

        return endOfCycle


    def onTimerTick(self):
        try:
            self.update(self.AnimationRequest.NONE)
        except animationProvider.Error as e:
            self.timer.stop()
            self.RunState == self.AnimationState.STOPPED
            QtGui.QMessageBox.warning(self.UI, e.shortMsg, e.detailMsg)
        else:
            if self.ForceGUIUpdate:
                Gui.updateGui()
            if self.RunState == self.AnimationState.STOPPED:
                self.timer.stop()


    def setVarValue(self,name,value):
        setattr( self.Variables, name, value )
        if App.ActiveDocument == self.AnimatedDocument:
            self.rootAssembly.recompute('True')
        else:
            App.ActiveDocument.recompute(None, True, True)
        self.variableValue.setText('{:.2f}'.format(value))


    """
    +-----------------------------------------------+
    |            Loop or Pendulum Selector          |
    +-----------------------------------------------+
    """
    def onLoop(self):
        aniHints = animationHints.get(self.Variables, self.varList.currentText())
        aniHints[animationHints.Key.Loop] = self.Loop.isChecked()
        if self.Pendulum.isChecked() and self.Loop.isChecked():
            self.Pendulum.setChecked(False)


    def onPendulum(self):
        aniHints = animationHints.get(self.Variables, self.varList.currentText())
        aniHints[animationHints.Key.Pendulum] = self.Pendulum.isChecked()
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



    def updateSlider(self):
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


    def onBeginValChanged(self):
        varName = self.varList.currentText()
        val = self.beginValue.value()
        animationHints.get(self.Variables, varName)['rangeBegin'] = val
        self.updateSlider()

    def onEndValChanged(self):
        varName = self.varList.currentText()
        val = self.endValue.value()
        animationHints.get(self.Variables, varName)['rangeEnd'] = val
        self.updateSlider()

    def onStepValChanged(self):
        varName = self.varList.currentText()
        val = self.stepValue.value()
        animationHints.get(self.Variables, varName)['stepSize'] = val
        self.updateSlider()

    def onSleepValChanged(self):
        varName = self.varList.currentText()
        val = self.sleepValue.value()
        animationHints.get(self.Variables, varName)['sleepValue'] = val
        self.timer.setInterval(val * 1000)


    """
    +-----------------------------------------------+
    |                Star/Stop/Close/Export         |
    +-----------------------------------------------+
    """

    def onRun(self):
        try:
            self.update(self.AnimationRequest.START)
        except animationProvider.Error as e:
            QtGui.QMessageBox.warning(self.UI, e.shortMsg, e.detailMsg)
        else:
            self.timer.start()


    def onStop(self):
        self.update(self.AnimationRequest.STOP)
        self.timer.stop()


    def onClose(self):
        self.onStop()
        animationHints.cleanUp(self.Variables)
        self.MDIArea.subWindowActivated[QtGui.QMdiSubWindow].disconnect(self.onDocChanged)
        self.UI.close()

    def onExport(self):
        self.onStop()
        if not self.exporter:
            # Only import the export-lib if requested. Helps to keep WB loading times in check.
            import AnimationExportLib
            self.exporter = AnimationExportLib.animationExporter(self)
        self.exporter.openUI()

    def onDocChanged(self):
        if App.ActiveDocument != self.ActiveDocument:
            # Check if AnimatedDocument still exists
            if not self.AnimatedDocument in App.listDocuments().values():
                self.AnimatedDocument = None
            self.onStop()
            #self.Activated()


    #
    # animationProvider Interface
    #
    def nextFrame(self, resetAnimation) -> bool:
        req = animateVariable.AnimationRequest.START if resetAnimation else animateVariable.AnimationRequest.NONE

        endOfCycle = self.update(req)
        if endOfCycle:
            self.update(animateVariable.AnimationRequest.STOP)
        animationEnded = self.RunState == animateVariable.AnimationState.STOPPED

        return animationEnded


    def pendulumWanted(self) -> bool:
        return self.Pendulum.isChecked()


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
        # select Document
        self.docList = updatingComboBox()
        self.formLayout.addRow(QtGui.QLabel('Document'), self.docList)
        # select Variable
        self.varList = updatingComboBox()
        self.formLayout.addRow(QtGui.QLabel('Variable'),self.varList)
        # Range Minimum
        self.beginValue = QtGui.QDoubleSpinBox()
        self.beginValue.setRange(numpy.finfo(float).min, numpy.finfo(float).max)
        self.beginValue.setKeyboardTracking(False)
        self.formLayout.addRow(QtGui.QLabel('Range Begin'), self.beginValue)
        # Maximum
        self.endValue = QtGui.QDoubleSpinBox()
        self.endValue.setRange(numpy.finfo(float).min, numpy.finfo(float).max)
        self.endValue.setKeyboardTracking(False)
        self.formLayout.addRow(QtGui.QLabel('Range End'), self.endValue)
        # Step
        self.stepValue = QtGui.QDoubleSpinBox()
        self.stepValue.setRange( 0.01, numpy.finfo(float).max )
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
        # Export button
        self.ExportButton = QtGui.QPushButton('Export')
        self.buttonLayout.addWidget(self.ExportButton)
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
        self.docList.currentIndexChanged.connect(self.onSelectDoc)
        self.docList.popupList.connect(self.updateDocList)
        self.varList.currentIndexChanged.connect( self.onSelectVar )
        self.varList.popupList.connect(self.updateVarList)
        self.slider.sliderMoved.connect(          self.sliderMoved)
        self.slider.valueChanged.connect(self.sliderMoved)
        self.beginValue.valueChanged.connect(self.onBeginValChanged)
        self.endValue.valueChanged.connect(self.onEndValChanged)
        self.stepValue.valueChanged.connect(      self.onStepValChanged)
        self.sleepValue.valueChanged.connect(       self.onSleepValChanged)
        self.Loop.toggled.connect(                self.onLoop )
        self.Pendulum.toggled.connect(            self.onPendulum )
        self.ForceRender.toggled.connect(self.onForceRender)
        self.CloseButton.clicked.connect(         self.onClose )
        self.ExportButton.clicked.connect(self.onExport)
        self.StopButton.clicked.connect(self.onStop)
        self.RunButton.clicked.connect(           self.onRun )


    def enableDependentGuiElements(self, state):
        self.beginValue.setEnabled(state)
        self.endValue.setEnabled(state)
        self.stepValue.setEnabled(state)
        self.sleepValue.setEnabled(state)
        self.slider.setEnabled(state)
        self.RunButton.setEnabled(state)
        self.Loop.setEnabled(state)
        self.Pendulum.setEnabled(state)
        self.ExportButton.setEnabled(state)



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
    |     Custom Combobox that emits a Signal when  |     
    |     the user clicks for the popup menu.       |
    |     Needed to update the list of variables    |
    |     on the fly.                               |
    +-----------------------------------------------+
"""

class updatingComboBox(QtGui.QComboBox):

    popupList = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def showPopup(self):
        self.popupList.emit()
        super().showPopup()




"""
    +-----------------------------------------------+
    |            Animation Hint Record Helper       |
    +-----------------------------------------------+
"""

class animationHints():
    class Key:
        RangeBegin = 'rangeBegin'
        RangeEnd = 'rangeEnd'
        StepSize = 'stepSize'
        SleepTime = 'sleepTime'
        Loop = 'loop'
        Pendulum = 'pendulum'

    @staticmethod
    def get(variables, varName):
        # Get the hints for the given variable.
        # Ensure that hints with sensible values are created in case there is no entry yet
        varValue = variables.getPropertyByName(varName)

        defaultHints = {animationHints.Key.RangeBegin: varValue,
                        animationHints.Key.RangeEnd: varValue,
                        animationHints.Key.StepSize: 1.0,
                        animationHints.Key.SleepTime: 0.0,
                        animationHints.Key.Loop: False,
                        animationHints.Key.Pendulum: False}
        hintList = animationHints.__getHintList__(variables)
        return hintList.setdefault(varName, defaultHints)


    @staticmethod
    def __getHintList__(variables):
        # Ensure that a hint-dictionary is available and return it
        if "AnimationHintList" not in variables.PropertiesList:
            variables.addProperty("App::PropertyPythonObject", "AnimationHintList", "AnimationHints", "The hintfield for the animation dialog").AnimationHintList = {}
            variables.setPropertyStatus("AnimationHintList", "Hidden")
        return variables.getPropertyByName("AnimationHintList")


    @staticmethod
    def cleanUp(variables):
        if not variables:
            return
        # Walk through all variable-entries and collect the relevant hints for them
        newHints = {}
        hintList = animationHints.__getHintList__(variables)
        for entry in variables.PropertiesList:
            if variables.getGroupOfProperty(entry) == 'Variables':
                hint = hintList.get(entry, None)
                if hint:
                    newHints[entry] = hint
        # Throw old list away and use the new (possibly reduced) one
        setattr(variables, "AnimationHintList", newHints)




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_Animate', animateVariable() )

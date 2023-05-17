#!/usr/bin/env python3
# coding: utf-8
#
# checkInterference.py
#
# Check interferences between parts

import os
import random as rnd
import math
import logging
from timeit import default_timer as timer

from PySide import QtGui, QtCore

import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4
import showHideLcsCmd as lcs
import Part

MIN_VOLUME_ALLOWED = 0.0001

class checkInterference:

    def __init__(self):
        super(checkInterference, self).__init__()

        self.abort = 0
        self.current_value = 0
        self.log_msg = str()
        self.enable_fasteners_check = False

    def GetResources(self):
        menutext = "Check Intereferences"
        tooltip  = "Check interferences among assembled objects (may take time)"
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_Interference_Check.svg')
        return {
            "MenuText": menutext,
            "ToolTip": tooltip,
            "Pixmap": iconFile
        }

    def IsActive(self):
        if Asm4.getAssembly() is None:
            print("There is no Assembly in this file")
            return False
        else:
            return True

    def Activated(self):
        self.UI = QtGui.QDialog()
        self.modelDoc = App.ActiveDocument
        self.model = Asm4.getAssembly()
        self.abort = False
        lcs.showHide(False)
        self.drawUI()
        self.UI.show()
        self.log_msg = ""
        # self.log_view.clear()
        # self.log_view.setPlainText(self.log_msg)
        # self.log_number_of_objects()
        # self.log_number_of_comparisons()
        self.progress_bar.setMaximum(self.total_comparisons)

    def log_number_of_objects(self):
        self.n_objects = 0
        for obj in self.model.Group:
            # if obj.TypeId == 'App::Link' or obj.TypeId == 'Part::FeaturePython' and (obj.Content.find("FastenersCmd") or (obj.Content.find("PCBStandoff")) > -1):
            if obj.TypeId == 'App::Link':
                self.n_objects += 1

        msg="{} has {} objects".format(self.model.Label, self.n_objects)
        self.log_msg += "{}\n".format(msg)
        self.log_view.setPlainText(self.log_msg)
        # Gui.updateGui()

    def log_number_of_comparisons(self):
        self.total_comparisons = (int) ((math.factorial(self.n_objects) / (math.factorial(2) * math.factorial(self.n_objects - 2))) - self.n_objects)

        msg="Totaling {} possible comparisons".format(self.total_comparisons)
        self.log_msg += "{}\n".format(msg)
        self.log_view.setPlainText(self.log_msg)

        msg="Checking interferences may take time, hold on.".format(self.total_comparisons)
        self.log_msg += "{}\n".format(msg)
        self.log_view.setPlainText(self.log_msg)

    # the real stuff happens here
    def check_interferences(self, ilim=0, jlim=0):

        start_time_s = timer()

        doc = App.ActiveDocument
        self.model.Visibility = False
        self.modelDoc.Parts.Visibility = False
        for obj in self.modelDoc.Parts.Group:
            try:
                obj.Visibility = False
            except:
                pass

        # Create the Interferences folder
        intersections_folder = self.modelDoc.addObject('App::DocumentObjectGroup', 'Interferences')
        self.modelDoc.Tip = intersections_folder
        intersections_folder.Label = 'Interferences'

        shapes_copy = self.modelDoc.addObject('App::Part', 'ShapeCopies')
        self.modelDoc.Tip = shapes_copy
        shapes_copy.Label = 'ShapeCopies'
        intersections_folder.addObject(shapes_copy)

        # Create the Common folder inside of the Interferences
        Intersections = self.modelDoc.addObject('App::DocumentObjectGroup', 'Intersections')
        self.modelDoc.Tip = Intersections
        Intersections.Label = 'Intersections'
        intersections_folder.addObject(Intersections)

        c = 1 # number of comparisons done
        t = 1 # total number of objects

        i = 0
        checked_dict = dict()

        # parse the assembly
        for obj1 in self.model.Group:
            # we only check for visible objects
            if obj1.Visibility == True and (obj1.TypeId == 'App::Link' or (obj1.TypeId == 'Part::FeaturePython' and (obj1.Content.find("FastenersCmd") or (obj1.Content.find("PCBStandoff")) > -1))):

                i = i + 1
                j = 0
                # parse the assembly
                for obj2 in self.model.Group:
                    if obj2 != obj1:
                        if obj2.Visibility == True and (obj2.TypeId == 'App::Link' or (obj2.TypeId == 'Part::FeaturePython' and (obj2.Content.find("FastenersCmd") or (obj2.Content.find("PCBStandoff")) > -1))):
                            j = j + 1
                            if not jlim == 0 and j >= jlim:
                                break

                            if self.abort:
                                return

                            # msg = ">> {} ({}, {}) Checking: {} - {}".format(c, j, i, obj1.Label, obj2.Label)
                            msg = "{}. Checking: '{}' vs '{}'".format(c, obj1.Label, obj2.Label)
                            # print(msg)
                            self.log_msg += "{}\n".format(msg)
                            self.log_view.setPlainText(self.log_msg)

                            # When the 1st object was never compared
                            if not obj1.Label in checked_dict:

                                c += 1
                                checked_dict[obj1.Label] = []

                                obj1_model_cpy = self.make_shape_copy(doc, obj1)
                                shapes_copy.addObject(obj1_model_cpy)
                                obj1_model_cpy.Visibility = True
                                obj1_model_cpy.ViewObject.Transparency = 88
                                obj1_model_cpy.ViewObject.ShapeColor = (0.90, 0.90, 0.90)
                                obj1_model_cpy.ViewObject.DisplayMode = "Shaded"

                                # When the 2nd object was never compared
                                if not obj2.Label in checked_dict:

                                    checked_dict[obj2.Label] = []

                                    obj2_model_cpy = self.make_shape_copy(doc, obj2)
                                    shapes_copy.addObject(obj2_model_cpy)
                                    obj2_model_cpy.Visibility = True
                                    obj2_model_cpy.ViewObject.Transparency = 88
                                    obj2_model_cpy.ViewObject.ShapeColor = (0.90, 0.90, 0.90)
                                    obj2_model_cpy.ViewObject.DisplayMode = "Shaded"

                                checked_dict[obj1.Label].append(obj2.Label)
                                checked_dict[obj2.Label].append(obj1.Label)

                                obj1_cpy = self.make_shape_copy(doc, obj1)
                                obj2_cpy = self.make_shape_copy(doc, obj2)

                                common = self.make_intersection(doc, obj1_cpy, obj2_cpy, c)

                                if common:
                                    if not self.remove_empty_common(common):
                                        common.ViewObject.Transparency = 60
                                        r = rnd.random()
                                        g = rnd.random()
                                        b = rnd.random()
                                        common.ViewObject.ShapeColor = (r, g, b)
                                        Intersections.addObject(common)
                                        self.modelDoc.recompute()
                                    else:
                                        self.modelDoc.removeObject(common.Name)
                            else:

                                # When the 1st object was compared before but not with the 2nd object
                                if not obj2.Label in checked_dict[obj1.Label]:

                                    c += 1

                                    checked_dict[obj1.Label].append(obj2.Label)

                                    obj2_list = []
                                    obj2_list.append(obj2.Label)
                                    checked_dict[obj2.Label] = obj2_list

                                    obj1_cpy = self.make_shape_copy(doc, obj1)
                                    obj2_cpy = self.make_shape_copy(doc, obj2)
                                    common = self.make_intersection(doc, obj1_cpy, obj2_cpy, c)

                                    if common:
                                        if not self.remove_empty_common(common):
                                            common.ViewObject.Transparency = 60
                                            r = rnd.random()
                                            g = rnd.random()
                                            b = rnd.random()
                                            common.ViewObject.ShapeColor = (r, g, b)
                                            Intersections.addObject(common)
                                            self.modelDoc.recompute()
                                        else:
                                            self.modelDoc.removeObject(common.Name)
                                else:

                                    msg = "   Interference previously processed"
                                    # print(msg)
                                    self.log_msg += "{}\n".format(msg)
                                    self.log_view.setPlainText(self.log_msg)

                            self.progress_bar_progress()
                            Gui.updateGui()


            if not ilim == 0 and i >= ilim:
                break

        self.modelDoc.recompute()
        Gui.updateGui()

        # Remove the intersections folder if there is no interference
        if not Intersections.Group:
            msg = "\n>>> Design Clean <<<"
            # print(msg)
            self.log_msg += "{}\n".format(msg)
            self.log_view.setPlainText(self.log_msg)
            self.remove_interference_folder()
            self.model.Visibility = True
            Gui.updateGui()
        else:
            msg = "\n>>> {} has {} interferences <<<".format(self.model.Label, len(Intersections.Group))
            # print(msg)
            self.log_msg += "{}\n".format(msg)
            self.log_view.setPlainText(self.log_msg)


        end_time_s = timer()
        elapsed_time_s = end_time_s - start_time_s
        if elapsed_time_s < 1:
            msg = "\nElapsed time: {:0.2} ms".format(elapsed_time_s / 1000)
        elif elapsed_time_s < 60:
            msg = "\nElapsed time: {:0.2} s".format(elapsed_time_s)
        elif elapsed_time_s < 3600:
            msg = "\nElapsed time: {:0.2} min".format(elapsed_time_s / 60)
        else:
            msg = "\nElapsed time: {:0.2} h".format(elapsed_time_s / 3600)
        self.log_msg += "{}\n".format(msg)
        self.log_view.setPlainText(self.log_msg)


    # makes a new Part::Feature and assigns it the shape of the original object
    # works also with ShapeBinders but it's much slower
    def make_shape_copy(self, doc, obj):
        '''
        new_obj = doc.addObject('PartDesign::SubShapeBinder', obj.Label)
        new_obj.Support = [(obj, ('',))]
        '''
        __shape = Part.getShape(obj, '', needSubElement=False, refine=False)
        new_obj = doc.addObject('Part::Feature', obj.Label)
        new_obj.Label = obj.Label
        new_obj.Shape = __shape
        new_obj.ViewObject.ShapeColor = getattr(obj.getLinkedObject(True).ViewObject, 'ShapeColor', new_obj.ViewObject.ShapeColor)
        new_obj.ViewObject.LineColor  = getattr(obj.getLinkedObject(True).ViewObject, 'LineColor',  new_obj.ViewObject.LineColor)
        new_obj.ViewObject.PointColor = getattr(obj.getLinkedObject(True).ViewObject, 'PointColor', new_obj.ViewObject.PointColor)
        # doc.recompute()
        return new_obj


    def make_intersection(self, doc, obj1, obj2, count):

        shape_missing = 0

        if not obj1.Shape.Solids:
            shape_missing = 1
            msg = "   {} does not have a shape.".format(obj1.Label)
            App.Console.PrintWarning(msg)
            self.log_msg += "{}\n".format(msg)
            self.log_view.setPlainText(self.log_msg)
            Gui.updateGui()
        if not obj2.Shape.Solids:
            shape_missing = 1
            msg = "   {} does not have a shape.".format(obj2.Label)
            App.Console.PrintWarning(msg)
            self.log_msg += "{}\n".format(msg)
            self.log_view.setPlainText(self.log_msg)
            Gui.updateGui()

        if shape_missing:
            msg = "   Missing shape(s), skipping the check.\n".format(obj2.Label)
            App.Console.PrintWarning(msg)
            self.log_msg += "{}\n".format(msg)
            self.log_view.setPlainText(self.log_msg)
            Gui.updateGui()
            self.modelDoc.removeObject(obj1.Name)
            self.modelDoc.removeObject(obj2.Name)
            return

        obj = doc.addObject("Part::MultiCommon", "Common")

        obj.Shapes = [obj1, obj2]
        obj1.Visibility = False
        obj2.Visibility = False
        obj.Label = "Common {} - {} - {}".format(str(count), obj1.Label, obj2.Label)
        obj.ViewObject.DisplayMode = getattr(obj1.getLinkedObject(True).ViewObject, 'DisplayMode', obj.ViewObject.DisplayMode)
        obj.ViewObject.ShapeColor = (1., 0.666, 0.) # YELLOW
        obj.ViewObject.Transparency = 0
        obj.ViewObject.DisplayMode = "Shaded"
        doc.recompute()

        # Sometimes there are not shapes...
        # try:
        obj.Label2 = "Volume = {:4f}".format(obj.Shape.Volume)
        if obj.Shape.Volume > MIN_VOLUME_ALLOWED:
            return obj
        else:
            # Avoiding the following issue:
            # <Part> ViewProviderExt.cpp(1266): Cannot compute Inventor representation for the shape of <OBJECTNAME>: Bnd_Box is void
            self.modelDoc.removeObject(obj1.Name)
            self.modelDoc.removeObject(obj2.Name)
            self.modelDoc.removeObject(obj.Name)
            return
        # except:
        #     return

    def remove_empty_common(self, obj):
        try:
            if obj.Shape:
                try:
                    msg = "| Collision detected".format(obj.Label)
                    # msg = "  {} | Collision detected".format(obj.Label)
                    # print(msg)
                    self.log_msg += "{}\n".format(msg)
                    self.log_view.setPlainText(self.log_msg)
                    Gui.updateGui()

                    if obj.Shape.Volume > MIN_VOLUME_ALLOWED:
                        return False
                    else:
                        # msg = "| Touching faces (KEEPING)".format(obj.Label)
                        msg = "| Touching faces (REMOVING)".format(obj.Label)
                        # print(msg)
                        self.log_msg += "{}\n".format(msg)
                        self.log_view.setPlainText(self.log_msg)
                        Gui.updateGui()

                        for shape in obj.Shapes:
                            self.modelDoc.removeObject(shape.Name)
                        self.modelDoc.removeObject(obj.Name)
                        return True
                except:
                    for shape in obj.Shapes:
                        self.modelDoc.removeObject(shape.Name)
                    self.modelDoc.removeObject(obj.Name)
                    msg = "| Interference clear".format(obj.Label)
                    # print(msg)
                    self.log_msg += "{}\n".format(msg)
                    self.log_view.setPlainText(self.log_msg)
                    Gui.updateGui()

                    return True
        except:
            for shape in common.Shapes:
                self.modelDoc.removeObject(shape.Name)
            self.modelDoc.removeObject(common.Name)
            msg = "| Interference clear".format(obj.Label)
            # print(msg)
            self.log_msg += "{}\n".format(msg)
            self.log_view.setPlainText(self.log_msg)
            Gui.updateGui()

            return True


    # Remove existing folder and its contents
    def remove_interference_folder(self):
        self.modelDoc.Parts.Visibility = True
        for obj in self.modelDoc.Parts.Group:
            try:
                obj.Visibility = False
            except:
                pass
        try:
            existing_folder = self.modelDoc.getObject("Interferences")
            for obj in existing_folder.Group:

                if obj.TypeId == 'App::Part':
                    obj.removeObjectsFromDocument() # Remove Part's content
                    self.modelDoc.removeObject(obj.Name) # Remove the Part

                elif obj.TypeId == 'App::DocumentObjectGroup':

                    for obj2 in obj.Group:

                        if obj2.TypeId == "Part::MultiCommon":
                            for shape in obj2.Shapes:
                                self.modelDoc.removeObject(shape.Name) # Remove Common's Parts
                            self.modelDoc.removeObject(obj2.Name) # Remove Common

                    self.modelDoc.removeObject(obj.Name) # Remove Group

            self.modelDoc.removeObject(existing_folder.Name) # Remove Interferences folder
            self.modelDoc.recompute()
        except:
            pass

    def onStart(self):
        self.model = Asm4.getAssembly()
        self.StartButton.setEnabled(False)
        self.ClearButton.setEnabled(False)
        self.CancelButton.setText("Abort")
        # self.log_msg = str()
        # self.log_view.setPlainText(self.log_msg)
        self.progress_bar_reset()
        self.remove_interference_folder()
        self.check_interferences()
        self.model.recompute()
        self.StartButton.setEnabled(True)
        self.ClearButton.setEnabled(True)
        self.CancelButton.setText("Close")

    def onCancel(self):
        # do something to abort current operations, if any
        self.abort = True
        self.log_msg = str()
        self.log_view.setPlainText(self.log_msg)

        # TODO: if running only
        # self.log_msg += "\nOPERATION ABORTED\n"
        # self.log_view.setPlainText(self.log_msg)
        # self.remove_interference_folder()
        # self.model.Visibility = True
        # self.modelDoc.Parts.Visibility = True
        self.UI.close()

    def onClear(self):
        self.log_msg = str()
        self.log_view.setPlainText(self.log_msg)
        self.remove_interference_folder()
        self.log_number_of_objects()
        self.log_number_of_comparisons()
        self.log_msg += "Interference check may take time\n"
        self.log_view.setPlainText(self.log_msg)


    def onCheckFasterners(self, state):
        if state == QtCore.Qt.Checked:
            self.enable_fasteners_check = True
        else:
            self.enable_fasteners_check = False


    def progress_bar_reset(self):
        self.current_value = 0
        self.progress_bar.reset()

    def progress_bar_progress(self):
        if self.current_value <= self.progress_bar.maximum():
            self.current_value += 1
            self.progress_bar.setValue(self.current_value)

    # Define the UI (static elements, only)
    def drawUI(self):

        # Main Window (QDialog)
        self.UI.setWindowTitle('Interference Checks')
        self.UI.setWindowIcon(QtGui.QIcon(os.path.join(Asm4.iconPath , 'FreeCad.svg')))
        self.UI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.UI.setModal(False)
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        self.checkBox1 = QtGui.QCheckBox("Allow touching faces")
        self.checkBox2 = QtGui.QCheckBox("Include fasteners")
        self.checkBox1.setChecked(True)
        self.checkBox2.setChecked(False)

        self.formLayout = QtGui.QFormLayout()
        self.entry1 = QtGui.QLineEdit()
        self.volumeLabel = QtGui.QLabel("Ignoring interference with volume equal or less than:")
        self.min_volume = QtGui.QLineEdit()
        self.min_volume.setText(str(MIN_VOLUME_ALLOWED))
        self.formLayout.addRow(self.volumeLabel, self.min_volume)

        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addWidget(self.checkBox1)
        self.vbox.addWidget(self.checkBox2)
        self.vbox.addLayout(self.formLayout)
        self.vbox.addStretch(1)

        self.groupBox = QtGui.QGroupBox()
        self.groupBox.setLayout(self.vbox)
        self.mainLayout.addWidget(self.groupBox)

        self.progress_bar = QtGui.QProgressBar()
        self.progress_bar.setValue(0)
        self.mainLayout.addWidget(self.progress_bar)

        self.log_view = QtGui.QPlainTextEdit()
        self.log_view.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        self.log_view.setMinimumWidth(Gui.getMainWindow().width()/2)
        self.log_view.setMinimumHeight(Gui.getMainWindow().height()/3)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().minimum())
        # self.log_view.moveCursor(QtGui.QTextCursor.End)
        # self.log_view.ensureCursorVisible()

        f = QtGui.QFont("unexistent");
        f.setStyleHint(QtGui.QFont.Monospace);
        self.log_view.setFont(f);
        self.mainLayout.addWidget(self.log_view)

        # The button row definition
        self.buttonLayout = QtGui.QHBoxLayout()

        # Start button
        self.StartButton = QtGui.QPushButton('Start Checks')
        self.StartButton.setDefault(True)
        self.buttonLayout.addWidget(self.StartButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # Delete Interferences folder
        self.ClearButton = QtGui.QPushButton('Clear Checks')
        self.ClearButton.setDefault(True)
        self.buttonLayout.addWidget(self.ClearButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # Cancel button
        self.CancelButton = QtGui.QPushButton('Close')
        self.CancelButton.setDefault(True)
        self.buttonLayout.addWidget(self.CancelButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.StartButton.clicked.connect(self.onStart)
        self.CancelButton.clicked.connect(self.onCancel)
        self.ClearButton.clicked.connect(self.onClear)


# Add the command in the workbench
Gui.addCommand('Asm4_checkInterference',  checkInterference())

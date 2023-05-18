#!/usr/bin/env python3
# coding: utf-8
#
# checkInterference.py
#
# Check interferences between parts
#
# Author: Leandro Sehnem Heck

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

class checkInterference:

    def __init__(self):
        super(checkInterference, self).__init__()

        self.abort_processing = False
        self.min_volume_allowed = 0.0001
        self.allow_faces_touching = True
        self.current_progress_value = 0
        self.check_fasteners = False
        self.log_msg = str()
        self.interference_count = 0
        self.verbose = False

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
            print("Check interference works with Asm4 Assemblies and there is none in this file")
            return False
        else:
            return True


    def Activated(self):

        self.modelDoc = App.ActiveDocument
        self.model = Asm4.getAssembly()

        self.abort_processing = False
        lcs.showHide(False)

        self.UI = QtGui.QDialog()
        self.drawUI()
        self.UI.show()

        self.log_clear()
        self.log_number_of_objects()
        self.log_number_of_comparisons()

        if self.check_fasteners:
            self.progress_bar.setMaximum(self.total_comparisons)
        else:
            self.progress_bar.setMaximum(self.total_comparisons_without_fasteners)


    def log_clear(self):
        self.log_msg = str()
        self.log_view.setPlainText(self.log_msg)


    def log_write(self, msg):
        self.log_msg += "{}\n".format(msg)
        self.log_view.setPlainText(self.log_msg)
        Gui.updateGui()


    def log_number_of_objects(self):
        self.n_objects = 0
        self.n_objects_without_fasteners = 0
        for obj in self.model.Group:
            if obj.Visibility == True and (obj.TypeId == 'App::Link' or (obj.TypeId == 'Part::FeaturePython' and (obj.Content.find("FastenersCmd") or (obj.Content.find("PCBStandoff")) > -1))):
                self.n_objects += 1
            if obj.Visibility == True and (obj.TypeId == 'App::Link'):
                self.n_objects_without_fasteners += 1
        if self.check_fasteners:
            self.log_write("{} has {} objects. (with fasteners)".format(self.model.Label, self.n_objects))
        else:
            self.log_write("{} has {} objects.".format(self.model.Label, self.n_objects_without_fasteners))


    def log_number_of_comparisons(self):
        self.total_comparisons = (int) (math.factorial(self.n_objects) / (math.factorial(2) * math.factorial(self.n_objects - 2)))
        self.total_comparisons_without_fasteners = (int) (math.factorial(self.n_objects_without_fasteners) / (math.factorial(2) * math.factorial(self.n_objects_without_fasteners - 2)))
        if self.check_fasteners:
            self.log_write("Totaling {} possible comparisons (with fasteners)".format(self.total_comparisons))
        else:
            self.log_write("Totaling {} possible comparisons".format(self.total_comparisons_without_fasteners))
        self.log_write("Checking interferences may take time, hold on.")


    def log_elapsed_time(self, start_time_s, end_time_s):

        elapsed_time_s = end_time_s - start_time_s
        if elapsed_time_s < 1:
            self.log_write("\nElapsed time: {:.2f} ms".format(elapsed_time_s * 1000))
        elif elapsed_time_s < 60:
            self.log_write("\nElapsed time: {:.2f} s".format(elapsed_time_s))
        elif elapsed_time_s < 3600:
            self.log_write("\nElapsed time: {:.2f} min".format(elapsed_time_s / 60))
        else:
            self.log_write("\nElapsed time: {:.2f} h".format(elapsed_time_s / 3600))


    def width_of_number_of_objects(self):
        if self.check_fasteners:
            c_len = len(str(self.n_objects))
        else:
            c_len = len(str(self.n_objects_without_fasteners))
        return c_len


    def log_checked_objects(self, checked_dict):
        self.log_write("")
        self.log_write("Checked itens:")
        k=0
        for key, values in checked_dict.items():
            self.log_write("{}. {}".format(k+1, key))
            k+=1
            for i, value in enumerate(values):
                self.log_write("  {}. {}".format(i+1, value))


    def check_interferences(self):

        if self.check_fasteners:
            self.progress_bar.setMaximum(self.total_comparisons)
        else:
            self.progress_bar.setMaximum(self.total_comparisons_without_fasteners)

        self.log_write("\nStarting checking interferences...")

        start_time_s = timer()

        doc = App.ActiveDocument
        self.model.Visibility = False
        self.modelDoc.Parts.Visibility = False
        for obj in self.modelDoc.Parts.Group:
            try:
                obj.Visibility = False
            except:
                pass

        intersections_folder = self.modelDoc.addObject('App::DocumentObjectGroup', 'Interferences')
        self.modelDoc.Tip = intersections_folder
        intersections_folder.Label = 'Interferences'

        shapes_copy = self.modelDoc.addObject('App::Part', 'ShapeCopies')
        self.modelDoc.Tip = shapes_copy
        shapes_copy.Label = 'ShapeCopies'
        intersections_folder.addObject(shapes_copy)

        Intersections = self.modelDoc.addObject('App::DocumentObjectGroup', 'Intersections')
        self.modelDoc.Tip = Intersections
        Intersections.Label = 'Intersections'
        intersections_folder.addObject(Intersections)

        c = 1 # index of the comparison
        i = 0
        checked_dict = dict()

        # Walk thorough the Assembly
        for obj1 in self.model.Group:

            # Summary: VISIBLE && ( LINK || ( CHECK_FASTENERS && FASTENER ) )
            if obj1.Visibility == True and (obj1.TypeId == 'App::Link' or (self.check_fasteners and (obj1.TypeId == 'Part::FeaturePython' and (obj1.Content.find("FastenersCmd") or (obj1.Content.find("PCBStandoff")) > -1)))):

                i += 1
                j = 0

                # Walk thorough the Assembly (again)
                for obj2 in self.model.Group:

                    # Ignore checks with the same part
                    if obj2 != obj1:

                        # Summary: VISIBLE && ( LINK || ( CHECK_FASTENERS && FASTENER ) )
                        if obj2.Visibility == True and (obj2.TypeId == 'App::Link' or (self.check_fasteners and (obj2.TypeId == 'Part::FeaturePython' and (obj2.Content.find("FastenersCmd") or (obj2.Content.find("PCBStandoff")) > -1)))):

                            j += 1

                            if self.abort_processing:
                                return

                            # When the 1st object was never compared
                            if not obj1.Label in checked_dict:

                                self.log_write("{count: {width}}. {obj1} vs {obj2}".format(count=c, width=self.width_of_number_of_objects(), obj1=obj1.Label, obj2=obj2.Label))

                                c += 1

                                checked_dict[obj1.Label] = []

                                obj1_model_cpy = self.make_shape_copy(doc, obj1)
                                shapes_copy.addObject(obj1_model_cpy)
                                obj1_model_cpy.Visibility = True
                                obj1_model_cpy.ViewObject.Transparency = 88
                                obj1_model_cpy.ViewObject.ShapeColor = (0.90, 0.90, 0.90)
                                obj1_model_cpy.ViewObject.DisplayMode = "Shaded"

                                # When the Obj2 was never compared with Obj1
                                # if not obj2.Label in checked_dict:
                                if not obj2.Label in checked_dict[obj1.Label]:

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

                                common = self.make_part_intersection(doc, obj1_cpy, obj2_cpy, c)

                                if common:
                                    if not self.remove_common_if_empty(common, c):
                                        common.ViewObject.Transparency = 60
                                        r = rnd.random()
                                        g = rnd.random()
                                        b = rnd.random()
                                        common.ViewObject.ShapeColor = (r, g, b)
                                        Intersections.addObject(common)
                                        self.interference_count += 1
                                        self.modelDoc.recompute()
                                    else:
                                        self.modelDoc.removeObject(common.Name)

                                self.progress_bar_progress()

                            # When the 1st object was compared before but not with the 2nd object
                            elif not obj2.Label in checked_dict[obj1.Label]:

                                    self.log_write("{count: {width}}. {obj1} vs {obj2}".format(count=c, width=self.width_of_number_of_objects(), obj1=obj1.Label, obj2=obj2.Label))

                                    c += 1

                                    checked_dict[obj1.Label].append(obj2.Label)

                                    if not obj2.Label in checked_dict:
                                        checked_dict[obj2.Label] = []

                                    checked_dict[obj2.Label].append(obj1.Label)

                                    obj1_cpy = self.make_shape_copy(doc, obj1)
                                    obj2_cpy = self.make_shape_copy(doc, obj2)
                                    common = self.make_part_intersection(doc, obj1_cpy, obj2_cpy, c)

                                    if common:
                                        if not self.remove_common_if_empty(common, c):
                                            common.ViewObject.Transparency = 60
                                            r = rnd.random()
                                            g = rnd.random()
                                            b = rnd.random()
                                            common.ViewObject.ShapeColor = (r, g, b)
                                            Intersections.addObject(common)
                                            self.interference_count += 1
                                            self.modelDoc.recompute()
                                        else:
                                            self.modelDoc.removeObject(common.Name)

                                    self.progress_bar_progress()

                            else:
                                if self.verbose:
                                    self.log_write("{count: {width}}. {obj1} vs {obj2}".format(count=c, width=self.width_of_number_of_objects(), obj1=obj1.Label, obj2=obj2.Label))
                                    indent = " " * (self.width_of_number_of_objects() + 3)
                                    self.log_write("{}| Step already processed".format(indent))
                                    self.log_write("{}| See {} vs {}".format(indent, obj2.Label, obj1.Label))

                            Gui.updateGui()

        self.modelDoc.recompute()
        Gui.updateGui()

        if self.verbose:
            self.log_checked_objects(checked_dict)

        # Remove the intersections folder if there is no "ce
        if not Intersections.Group:
            self.log_write("\n>>> {} is clean! <<<".format(self.model.Label))
            self.remove_interference_folder()
            self.model.Visibility = True
            Gui.updateGui()

        end_time_s = timer()
        self.log_elapsed_time(start_time_s, end_time_s)


    # Makes a new Part::Feature and assigns it the shape of the original object
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
        return new_obj


    def make_part_intersection(self, doc, obj1, obj2, count):

        shape_missing = 0

        indent = " " * (self.width_of_number_of_objects() + 3)

        if not obj1.Shape.Solids:
            self.log_write("{}| {} does not have shape.".format(indent, obj1.Label))
            shape_missing = 1
            Gui.updateGui()

        if not obj2.Shape.Solids:
            self.log_write("{}| {} does not have shape.".format(indent, obj2.Label))
            shape_missing = 1
            Gui.updateGui()

        if shape_missing:
            self.log_write("{}| There are missing shape(s) (SKIPPING).".format(indent))
            self.modelDoc.removeObject(obj1.Name)
            self.modelDoc.removeObject(obj2.Name)
            Gui.updateGui()
            return

        obj = doc.addObject("Part::MultiCommon", "Common")

        obj.Shapes = [obj1, obj2]
        obj1.Visibility = False
        obj2.Visibility = False
        obj.Label = "Common {} - {} - {} - {}".format(self.interference_count+1, count-1, obj1.Label, obj2.Label)
        obj.ViewObject.DisplayMode = getattr(obj1.getLinkedObject(True).ViewObject, 'DisplayMode', obj.ViewObject.DisplayMode)
        obj.ViewObject.ShapeColor = (1., 0.666, 0.) # YELLOW
        obj.ViewObject.Transparency = 0
        obj.ViewObject.DisplayMode = "Shaded"
        doc.recompute()

        # Sometimes there are no shapes.
        # try:
        obj.Label2 = "Volume = {:4f}".format(obj.Shape.Volume)
        if obj.Shape.Volume > self.min_volume_allowed:
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

    def remove_common_if_empty(self, obj, count):

        indent = " " * (self.width_of_number_of_objects() + 3)

        try:
            if obj.Shape:
                try:
                    self.log_write("{}| Collision detected".format(indent))
                    self.log_write("{}| Object = {}".format(indent, obj.Label))
                    self.log_write("{}| Shape volume = {}".format(indent, obj.Shape.Volume))
                    if obj.Shape.Volume > self.min_volume_allowed:
                        return False
                    else:
                        if self.allow_faces_touching:
                            self.log_write("{}| Touching faces (KEEPING)".format(indent))
                            self.log_write("{}| {}".format(indent, obj.Label))
                            return False
                        else:
                            self.log_write("{}| Touching faces (REMOVING)".format(indent))
                            for shape in obj.Shapes:
                                self.modelDoc.removeObject(shape.Name)
                            self.modelDoc.removeObject(obj.Name)
                            return True
                except:
                    self.log_write("{}| Interference clear".format(indent))
                    for shape in obj.Shapes:
                        self.modelDoc.removeObject(shape.Name)
                    self.modelDoc.removeObject(obj.Name)
                    return True
        except:
            self.log_write("{}| Interference clear".format(indent))
            for shape in common.Shapes:
                self.modelDoc.removeObject(shape.Name)
            self.modelDoc.removeObject(common.Name)
            return True


    # Remove Interferences folder recursively
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


    def enable_elements(self, state):
        self.StartButton.setEnabled(state)
        self.checkBox1.setEnabled(state)
        self.checkBox2.setEnabled(state)
        self.volumeLabel.setEnabled(state)
        self.min_volume.setEnabled(state)
        self.ClearButton.setEnabled(state)


    def onStart(self):
        self.log_write("")
        self.log_write("=====================================\n")
        self.processing = True
        self.min_volume_allowed = float(self.min_volume.text())
        self.log_write("Minimum volume allowed to interfere set with = {}".format(self.min_volume_allowed))
        self.enable_elements(False)
        self.CancelButton.setText("Abort")
        self.model = Asm4.getAssembly()
        self.progress_bar_reset()
        self.remove_interference_folder()
        self.check_interferences()
        self.abort_processing = False
        self.model.recompute()
        self.enable_elements(True)
        self.CancelButton.setText("Close")
        self.processing = False


    def onCancel(self):
        if self.processing:
            self.abort_processing = True
            self.log_write("\n>>> OPERATION ABORTED <<<")
            self.progress_bar_reset()
            self.model.Visibility = True
            self.modelDoc.Parts.Visibility = True
        else:
            self.UI.close()


    def onClear(self):
        self.remove_interference_folder()
        self.log_clear()
        self.log_number_of_objects()
        self.log_number_of_comparisons()


    def onToggleAllowFaces(self, state):
        if state == QtCore.Qt.Checked:
            self.allow_faces_touching = True
        else:
            self.allow_faces_touching = False
        self.log_write("Allow faces touching = {}".format(self.allow_faces_touching))


    def onToggleCheckFasterners(self, state):
        if state == QtCore.Qt.Checked:
            self.check_fasteners = True
        else:
            self.check_fasteners = False
        self.log_clear()
        self.log_write("Check fasteners = {}".format(self.check_fasteners))
        self.log_write("==============================")
        self.log_number_of_objects()
        self.log_number_of_comparisons()

    def onToggleVerbosity(self, state):
        if state == QtCore.Qt.Checked:
            self.verbose = True
        else:
            self.verbose = False
        self.log_write("Verbose = {}".format(self.verbose))


    def progress_bar_reset(self):
        self.current_progress_value = 0
        self.progress_bar.reset()


    def progress_bar_progress(self):
        if self.current_progress_value <= self.progress_bar.maximum():
            self.current_progress_value += 1
            self.progress_bar.setValue(self.current_progress_value)


    # Define the UI (static elements, only)
    def drawUI(self):

        # Main Window (QDialog)
        self.UI.setWindowTitle('Interference Checks')
        self.UI.setWindowIcon(QtGui.QIcon(os.path.join(Asm4.iconPath , 'FreeCad.svg')))
        self.UI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.UI.setModal(False)
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        self.checkBox1 = QtGui.QCheckBox("Allow faces touching")
        self.checkBox2 = QtGui.QCheckBox("Include fasteners")
        self.checkBox3 = QtGui.QCheckBox("Verbose")
        self.checkBox1.setChecked(True)
        self.checkBox2.setChecked(False)
        self.checkBox3.setChecked(False)
        self.checkBox1.stateChanged.connect(self.onToggleAllowFaces)
        self.checkBox2.stateChanged.connect(self.onToggleCheckFasterners)
        self.checkBox3.stateChanged.connect(self.onToggleVerbosity)

        self.formLayout = QtGui.QFormLayout()
        self.entry1 = QtGui.QLineEdit()
        self.volumeLabel = QtGui.QLabel("Ignoring interference with volume equal or less than:")
        self.min_volume = QtGui.QLineEdit()
        self.min_volume.setFixedWidth(10)
        self.min_volume.setText(str(self.min_volume_allowed))
        self.formLayout.addRow(self.volumeLabel, self.min_volume)

        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addWidget(self.checkBox1)
        self.vbox.addWidget(self.checkBox2)
        self.vbox.addWidget(self.checkBox3)
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
        self.log_view.ensureCursorVisible()
        self.log_view.moveCursor(QtGui.QTextCursor.End)
        self.log_view.ensureCursorVisible()
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())
        # self.log_view.textChanged.connect(self.log_view.verticalScrollBar().maximum())


        f = QtGui.QFont("unexistent");
        f.setStyleHint(QtGui.QFont.Monospace);
        self.log_view.setFont(f);
        self.mainLayout.addWidget(self.log_view)

        # The button row definition
        self.buttonLayout = QtGui.QHBoxLayout()

        # Delete Interferences folder
        self.ClearButton = QtGui.QPushButton('Clear Checks')
        self.ClearButton.setDefault(True)
        self.buttonLayout.addWidget(self.ClearButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # Start button
        self.StartButton = QtGui.QPushButton('Check Interferences')
        self.StartButton.setDefault(True)
        self.buttonLayout.addWidget(self.StartButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # Cancel button
        self.CancelButton = QtGui.QPushButton('Cancel')
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

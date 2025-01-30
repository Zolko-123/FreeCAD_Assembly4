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
import time
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
            return False
        else:
            return True


    def Activated(self):

        self.Document = App.ActiveDocument
        self.Assembly = Asm4.getAssembly()

        self.processing = False
        self.abort_processing = False
        self.min_volume_allowed = 0.0001
        self.allow_faces_touching = True
        self.current_progress_value = 0
        self.check_fasteners = False
        self.log_msg = str()
        self.interference_count = 0
        self.verbose = False

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


    def log_write(self, msg, end="\n"):
        self.log_msg += "{}{}".format(msg, end)
        self.log_view.setPlainText(self.log_msg)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())
        Gui.updateGui()


    def log_number_of_objects(self):
        self.n_objects = 0
        self.n_objects_without_fasteners = 0
        for obj in self.Assembly.Group:
            if obj.Visibility == True and (obj.TypeId == 'App::Link' or (obj.TypeId == 'Part::FeaturePython' and (obj.Content.find("FastenersCmd") or (obj.Content.find("PCBStandoff")) > -1))):
                self.n_objects += 1
            if obj.Visibility == True and (obj.TypeId == 'App::Link'):
                self.n_objects_without_fasteners += 1
        if self.check_fasteners:
            self.log_write("The {} has {} objects. (with fasteners)".format(self.Assembly.Label, self.n_objects))
        else:
            self.log_write("The {} has {} objects.".format(self.Assembly.Label, self.n_objects_without_fasteners))


    def log_number_of_comparisons(self):

        if self.n_objects > 2:
            self.total_comparisons = (int) (math.factorial(self.n_objects) / (math.factorial(2) * math.factorial(self.n_objects - 2)))
        else:
            self.total_comparisons = 0

        if self.n_objects_without_fasteners > 2:
            self.total_comparisons_without_fasteners = (int) (math.factorial(self.n_objects_without_fasteners) / (math.factorial(2) * math.factorial(self.n_objects_without_fasteners - 2)))
        else:
            self.total_comparisons_without_fasteners = 0

        if self.check_fasteners:
            self.log_write("Totaling {} possible comparisons (with fasteners)".format(self.total_comparisons))
        else:
            self.log_write("Totaling {} possible comparisons".format(self.total_comparisons_without_fasteners))
        self.log_write("Interferences check may take time.")


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
        self.log_write("Checked items:")
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

        self.log_write("\n>>> Starting to check for interferences... <<<")

        start_time_s = timer()

        doc = App.ActiveDocument
        self.Assembly.Visibility = False

        try:
            self.Document.Parts.Visibility = False
            for obj in self.Document.Parts.Group:
                try:
                    obj.Visibility = False
                except:
                    pass
        except:
            pass

        # Main folder
        Interferences = self.Document.addObject('App::DocumentObjectGroup', 'Interferences')
        self.Document.Tip = Interferences
        Interferences.Label = 'Interferences'

        # Nested Part
        assembly_copy_name = self.Assembly.Label + "_copy"
        assembly_copy = self.Document.addObject('App::Part', assembly_copy_name)
        self.Document.Tip = assembly_copy
        assembly_copy.Label = assembly_copy_name
        Interferences.addObject(assembly_copy)

        # Nested folder
        Intersections = self.Document.addObject('App::DocumentObjectGroup', 'Intersections')
        self.Document.Tip = Intersections
        Intersections.Label = 'Intersections'
        Interferences.addObject(Intersections)

        c = 1 # index of the comparison
        i = 0
        checked_dict = dict()

        # Walk thorough the Assembly
        for obj1 in self.Assembly.Group:

            # Summary: VISIBLE && ( LINK || ( CHECK_FASTENERS && FASTENER ) )
            if obj1.Visibility == True and (obj1.TypeId == 'App::Link' or (self.check_fasteners and (obj1.TypeId == 'Part::FeaturePython' and (obj1.Content.find("FastenersCmd") or (obj1.Content.find("PCBStandoff")) > -1)))):

                i += 1
                j = 0

                # Walk thorough the Assembly (again)
                for obj2 in self.Assembly.Group:

                    # Ignore checks with the same part
                    if obj2 != obj1:

                        # Summary: VISIBLE && ( LINK || ( CHECK_FASTENERS && FASTENER ) )
                        if obj2.Visibility == True and (obj2.TypeId == 'App::Link' or (self.check_fasteners and (obj2.TypeId == 'Part::FeaturePython' and (obj2.Content.find("FastenersCmd") or (obj2.Content.find("PCBStandoff")) > -1)))):

                            j += 1

                            if self.abort_processing:
                                return

                            # When the 1st object was never compared
                            if not obj1.Label in checked_dict:

                                checked_dict[obj1.Label] = []

                                obj1_model_cpy = self.make_shape_copy(doc, obj1)
                                assembly_copy.addObject(obj1_model_cpy)
                                obj1_model_cpy.Visibility = True
                                obj1_model_cpy.ViewObject.Transparency = 88
                                obj1_model_cpy.ViewObject.ShapeColor = (0.90, 0.90, 0.90)
                                obj1_model_cpy.ViewObject.DisplayMode = "Shaded"

                            # When the 1st object was compared before but not with the 2nd object
                            if not obj2.Label in checked_dict[obj1.Label]:

                                    indent = self.width_of_number_of_objects()
                                    self.log_write("\n{count}. {obj1} vs {obj2}".format(count=str(c).rjust(indent), obj1=obj1.Label, obj2=obj2.Label))

                                    c += 1

                                    checked_dict[obj1.Label].append(obj2.Label)

                                    if not obj2.Label in checked_dict:
                                        checked_dict[obj2.Label] = []

                                        obj2_model_cpy = self.make_shape_copy(doc, obj2)
                                        assembly_copy.addObject(obj2_model_cpy)
                                        obj2_model_cpy.Visibility = True
                                        obj2_model_cpy.ViewObject.Transparency = 88
                                        obj2_model_cpy.ViewObject.ShapeColor = (0.90, 0.90, 0.90)
                                        obj2_model_cpy.ViewObject.DisplayMode = "Shaded"

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
                                            # common.ViewObject.LineColor = (0, 0, 0)
                                            common.ViewObject.DisplayMode = 'Flat Lines'
                                            Intersections.addObject(common)
                                            self.interference_count += 1
                                            self.Document.recompute()
                                        else:
                                            try:
                                                self.Document.removeObject(common.Name)
                                            except:
                                                pass

                                    self.progress_bar_progress()

                            else:
                                if self.verbose:
                                    self.log_write("{count: {width}}. {obj1} vs {obj2}".format(count=c, width=self.width_of_number_of_objects(), obj1=obj1.Label, obj2=obj2.Label))
                                    indent = " " * (self.width_of_number_of_objects() + 2)
                                    self.log_write("{}| Step already processed".format(indent))
                                    self.log_write("{}| See {} vs {}".format(indent, obj2.Label, obj1.Label))

                            Gui.updateGui()

        self.Document.recompute()
        Gui.updateGui()

        if self.verbose:
            self.log_checked_objects(checked_dict)

        # Remove the intersections folder if there is no intersections
        if not Intersections.Group:
            self.log_write("\n>>> No interferences were found. The {} is clean! <<<".format(self.Assembly.Label))
            self.remove_interference_folder()
            self.Assembly.Visibility = True
            Gui.updateGui()
        else:
            self.log_write("\n>>> Found {} interferences <<<".format(self.interference_count))

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

        indent = " " * (self.width_of_number_of_objects() + 2)

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
            self.Document.removeObject(obj1.Name)
            self.Document.removeObject(obj2.Name)
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

        # When objects dont intersect there are no shapes..
        try:
            obj.Label2 = "Volume = {:2f}".format(obj.Shape.Volume)
            if obj.Shape.Volume > self.min_volume_allowed:
                return obj
            else:
                # Avoiding the following issue:
                # <Part> ViewProviderExt.cpp(1266): Cannot compute Inventor representation for the shape of <OBJECTNAME>: Bnd_Box is void
                self.Document.removeObject(obj1.Name)
                self.Document.removeObject(obj2.Name)
                self.Document.removeObject(obj.Name)
                return
        except:
            return

    def remove_common_if_empty(self, obj, count):

        indent = " " * (self.width_of_number_of_objects() + 2)

        try:
            if obj.Shape:
                try:
                    self.log_write("{}| COLLISION DETECTED".format(indent))
                    self.log_write("{}| Object = {}".format(indent, obj.Label))
                    self.log_write("{}| Overlaping volume = {:.2f}".format(indent, obj.Shape.Volume))

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
                                self.Document.removeObject(shape.Name)
                            self.Document.removeObject(obj.Name)
                            return True
                except:
                    self.log_write("{}| Interference clear".format(indent))
                    for shape in obj.Shapes:
                        self.Document.removeObject(shape.Name)
                    self.Document.removeObject(obj.Name)
                    return True
        except:
            self.log_write("{}| Interference clear".format(indent))
            for shape in common.Shapes:
                self.Document.removeObject(shape.Name)
            self.Document.removeObject(common.Name)
            return True


    # Remove Interferences folder recursively
    def remove_interference_folder(self):

        try:
            self.Document.Parts.Visibility = True
            for obj in self.Document.Parts.Group:
                try:
                    obj.Visibility = False
                except:
                    pass
        except:
            pass

        try:
            existing_folder = self.Document.getObject("Interferences")
            for obj in existing_folder.Group:

                if obj.TypeId == 'App::Part':
                    obj.removeObjectsFromDocument() # Remove Part's content
                    self.Document.removeObject(obj.Name) # Remove the Part

                elif obj.TypeId == 'App::DocumentObjectGroup':

                    for obj2 in obj.Group:

                        if obj2.TypeId == "Part::MultiCommon":
                            for shape in obj2.Shapes:
                                self.Document.removeObject(shape.Name) # Remove Common's Parts
                            self.Document.removeObject(obj2.Name) # Remove Common

                    self.Document.removeObject(obj.Name) # Remove Group

            self.Document.removeObject(existing_folder.Name) # Remove Interferences folder
            self.Document.recompute()
        except:
            pass


    def enable_elements(self, state):
        self.check_button.setEnabled(state)
        self.touching_faces_checkbox.setEnabled(state)
        self.include_fasteners_checkbox.setEnabled(state)
        self.verbose_checkbox.setEnabled(state)
        self.min_volume_label.setEnabled(state)
        self.min_volume_input.setEnabled(state)
        self.clear_button.setEnabled(state)


    def on_check(self):
        self.log_write("")
        self.log_write("=====================================\n")
        self.processing = True
        self.min_volume_allowed = float(self.min_volume_input.text())
        self.log_write("Minimum interference volume = {}".format(self.min_volume_allowed))
        self.enable_elements(False)
        self.cancel_abort_button.setText("Abort")
        self.Assembly = Asm4.getAssembly()
        self.progress_bar_reset()
        self.remove_interference_folder()
        self.check_interferences()
        if self.abort_processing:
            self.progress_bar_reset()
            self.log_write("\n>>> OPERATION HAS BEEN ABORTED <<<")
        self.processing = False
        self.abort_processing = False
        self.enable_elements(True)
        self.cancel_abort_button.setText("Close")
        self.Assembly.recompute()


    def on_cancel_abort(self):
        if not self.processing:
            self.UI.close()
        else:
            self.abort_processing = True
            self.log_write("\nAborting the current processing...")
            self.Assembly.Visibility = True

            try:
                self.Document.Parts.Visibility = True
            except:
                pass


    def on_clear(self):
        self.remove_interference_folder()
        self.log_clear()
        self.log_number_of_objects()
        self.log_number_of_comparisons()
        self.cancel_abort_button.setText("Close")
        self.Assembly.Visibility = True


    def on_allow_touching_faces(self, state):
        if state == QtCore.Qt.Checked:
            self.allow_faces_touching = True
        else:
            self.allow_faces_touching = False
        self.log_write("Allow faces touching = {}".format(self.allow_faces_touching))


    def on_fasteners_check(self, state):
        if state == QtCore.Qt.Checked:
            self.check_fasteners = True
        else:
            self.check_fasteners = False
        self.log_clear()
        self.log_write("Check fasteners = {}".format(self.check_fasteners))
        self.log_write("==============================")
        self.log_number_of_objects()
        self.log_number_of_comparisons()

    def on_verbosity(self, state):
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
        self.main_layout = QtGui.QVBoxLayout(self.UI)

        # Checkboxes
        self.touching_faces_checkbox = QtGui.QCheckBox("Allow faces touching")
        self.include_fasteners_checkbox = QtGui.QCheckBox("Include fasteners")
        self.verbose_checkbox = QtGui.QCheckBox("Verbose")
        self.touching_faces_checkbox.setChecked(True)
        self.include_fasteners_checkbox.setChecked(False)
        self.verbose_checkbox.setChecked(False)
        self.touching_faces_checkbox.stateChanged.connect(self.on_allow_touching_faces)
        self.include_fasteners_checkbox.stateChanged.connect(self.on_fasteners_check)
        self.verbose_checkbox.stateChanged.connect(self.on_verbosity)

        self.form_layout = QtGui.QFormLayout()
        self.min_volume_label = QtGui.QLabel("Minimum interference volume:")
        self.min_volume_input = QtGui.QLineEdit()
        self.min_volume_input.setFixedWidth(10)
        self.min_volume_input.setText(str(self.min_volume_allowed))
        self.form_layout.addRow(self.min_volume_label, self.min_volume_input)

        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addWidget(self.touching_faces_checkbox)
        self.vbox.addWidget(self.include_fasteners_checkbox)
        self.vbox.addWidget(self.verbose_checkbox)
        self.vbox.addLayout(self.form_layout)
        self.vbox.addStretch(1)

        self.gbox = QtGui.QGroupBox()
        self.gbox.setLayout(self.vbox)
        self.main_layout.addWidget(self.gbox)

        self.progress_bar = QtGui.QProgressBar()
        self.progress_bar.setValue(0)
        self.main_layout.addWidget(self.progress_bar)

        self.log_view = QtGui.QTextEdit()
        self.log_view.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.log_view.setMinimumWidth(Gui.getMainWindow().width()/2)
        self.log_view.setMinimumHeight(Gui.getMainWindow().height()/3)
        self.log_view.ensureCursorVisible()
        self.log_view.moveCursor(QtGui.QTextCursor.End)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

        text_color = Gui.getMainWindow().palette().text().color()
        text_bg = Gui.getMainWindow().palette().background().color()

        self.log_view.setStyleSheet("QTextEdit:!editable{color: white, background-color: black};")

        f = QtGui.QFont("unexistent");
        f.setStyleHint(QtGui.QFont.Monospace);
        self.log_view.setFont(f);

        self.main_layout.addWidget(self.log_view)

        # self.log_view.TextColor = text_color

        # The button row definition
        self.button_layout = QtGui.QHBoxLayout()

        # Delete Interferences folder
        self.clear_button = QtGui.QPushButton('Clear Checks')
        self.clear_button.setDefault(True)
        self.button_layout.addWidget(self.clear_button)
        self.main_layout.addLayout(self.button_layout)

        # Start button
        self.check_button = QtGui.QPushButton('Check Interferences')
        self.check_button.setDefault(True)
        self.button_layout.addWidget(self.check_button)
        self.main_layout.addLayout(self.button_layout)

        # Cancel button
        self.cancel_abort_button = QtGui.QPushButton('Close')
        self.cancel_abort_button.setDefault(True)
        self.button_layout.addWidget(self.cancel_abort_button)
        self.main_layout.addLayout(self.button_layout)

        # Bind button Actions
        self.check_button.clicked.connect(self.on_check)
        self.cancel_abort_button.clicked.connect(self.on_cancel_abort)
        self.clear_button.clicked.connect(self.on_clear)

        # Apply the layout to the main window
        self.UI.setLayout(self.main_layout)


# Add the command in the workbench
Gui.addCommand('Asm4_checkInterference',  checkInterference())

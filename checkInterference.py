#!/usr/bin/env python3
# coding: utf-8
#
# checkInterference.py
#
# Check interferences between parts

import os
import random as rnd

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4
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
        self.UI = QtGui.QDialog()
        self.modelDoc = App.ActiveDocument
        # this has been checked before
        self.model = Asm4.getAssembly()
        self.remove_interference_folder()
        self.check_interferences()
        self.modelDoc.recompute()

    # the real stuff happens here
    def check_interferences(self, ilim=0, jlim=0):

        print("Check interferences has started. Hold on, this may take time")

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

        i = 0
        c = 1
        checked_dict = dict()

        # parse the assembly
        for obj1 in self.model.Group:
            # we only check for visible objects
            if obj1.Visibility == True and obj1.TypeId == 'App::Link' :
                i = i + 1
                j = 0
                # parse the assembly
                for obj2 in self.model.Group:
                    if obj2 != obj1:
                        if obj2.Visibility==True and obj2.TypeId == 'App::Link' :
                            j = j + 1
                            if not jlim == 0 and j >= jlim:
                                break

                            print(">> {} ({}, {}) Checking: {} - {}".format(c, j, i, obj1.Label, obj2.Label))

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
                                    else:
                                        self.modelDoc.removeObject(common.Name)

                            else:

                                # When the 1st object was compared before but not with the 2nd object
                                if not obj2.Label in checked_dict[obj1.Label]:

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
                                        else:
                                            self.modelDoc.removeObject(common.Name)

                                else:
                                    print("  Interference previously processed")



            if not ilim == 0 and i >= ilim:
                break

        self.modelDoc.recompute()
        Gui.updateGui()

        # Remove the intersections folder if there is no interference
        if not Intersections.Group:
            print("Design clean, no interference found")
            self.remove_interference_folder()
            self.model.Visibility = True


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
        obj.Label2 = "Volume = {:4f}".format(obj.Shape.Volume)
        if obj.Shape.Volume > 0.0:
            return obj
        else:
            # Avoiding the following issue:
            # <Part> ViewProviderExt.cpp(1266): Cannot compute Inventor representation for the shape of <OBJECTNAME>: Bnd_Box is void
            self.modelDoc.removeObject(obj1.Name)
            self.modelDoc.removeObject(obj2.Name)
            self.modelDoc.removeObject(obj.Name)
            return


    def remove_empty_common(self, obj):
        try:
            if obj.Shape:
                try:
                    print("  {} | Collision detected".format(obj.Label))
                    if obj.Shape.Volume > 0.0:
                        return False
                    else:
                        print("  Touching faces (REMOVING)".format(obj.Label))
                        for shape in obj.Shapes:
                            self.modelDoc.removeObject(shape.Name)
                        self.modelDoc.removeObject(obj.Name)
                        return True
                except:
                    for shape in obj.Shapes:
                        self.modelDoc.removeObject(shape.Name)
                    self.modelDoc.removeObject(obj.Name)
                    print("  Interference clear".format(obj.Label))
                    return True
        except:
            for shape in common.Shapes:
                self.modelDoc.removeObject(shape.Name)
            self.modelDoc.removeObject(common.Name)
            print("  Interference clear".format(obj.Label))
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

# Add the command in the workbench
Gui.addCommand('Asm4_checkInterference',  checkInterference())

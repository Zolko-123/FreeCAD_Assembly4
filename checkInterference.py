#!/usr/bin/env python3
# coding: utf-8
#
# checkInterference.py
#
# Check interferences between parts

import os
import json
import re
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
        try:
            self.model = self.modelDoc.Assembly
            print("ASM4> BOM of the Assembly 4 Model")
        except:
            try:
                self.model = self.modelDoc.Model
                print("ASM4> BOM of the legacy Assembly 4 Model")
            except:
                print("ASM4> BOM might not work with this file")

        doc = App.ActiveDocument
        self.check_interferences()
        doc.recompute()

    def make_simple_part_copy(self, doc, obj):
        __shape = Part.getShape(obj, '', needSubElement=False, refine=False)
        doc.addObject('Part::Feature', obj.Label).Shape = __shape
        doc.ActiveObject.Label = obj.Label
        new_obj = doc.ActiveObject
        new_obj.ViewObject.ShapeColor = getattr(obj.getLinkedObject(True).ViewObject, 'ShapeColor', new_obj.ViewObject.ShapeColor)
        new_obj.ViewObject.LineColor  = getattr(obj.getLinkedObject(True).ViewObject, 'LineColor',  new_obj.ViewObject.LineColor)
        new_obj.ViewObject.PointColor = getattr(obj.getLinkedObject(True).ViewObject, 'PointColor', new_obj.ViewObject.PointColor)
        doc.recompute()
        return new_obj

    def make_intersection(self, doc, obj1, obj2, count):
        obj = doc.addObject("Part::MultiCommon", "Common")
        obj.Shapes = [obj1, obj2]
        obj1.Visibility = False
        obj2.Visibility = False
        obj.Label = "Common {} - {} - {}".format(str(count), obj1.Label, obj2.Label)
        obj.ViewObject.DisplayMode = getattr(obj1.getLinkedObject(True).ViewObject, 'DisplayMode', obj.ViewObject.DisplayMode)
        obj.ViewObject.ShapeColor = (255, 170, 0) # YELLOW
        obj.ViewObject.Transparency = 0
        obj.ViewObject.DisplayMode = "Shaded"
        doc.recompute()
        obj.Label2 = "Volume = {:4f}".format(obj.Shape.Volume)
        return obj

    def remove_empty_common(self, obj):
        try:
            if obj.Shape:
                try:
                    if obj.Shape.Volume > 0.0:
                        print("{} | Collision detected".format(obj.Label))
                        return False
                    else:
                        print("{} | Touching faces (REMOVING)".format(obj.Label))
                        for shape in obj.Shapes:
                            doc.removeObject(shape.Name)
                        doc.removeObject(obj.Name)
                        return True
                except:
                    for shape in obj.Shapes:
                        doc.removeObject(shape.Name)
                    doc.removeObject(obj.Name)
                    return True
        except:
            for shape in common.Shapes:
                doc.removeObject(shape.Name)
            doc.removeObject(common.Name)
            return True

    def remove_interference_folder(self):

        doc = App.ActiveDocument

        try:
            model = doc.Model
            model.Visibility = True
        except:
            model = doc.Assembly
            model.Visibility = True

        doc.Parts.Visibility = True
        for obj in doc.Parts.Group:
            try:
                obj.Visibility = False
            except: 
                pass

        # Remove existing folder and its contents
        try:
            existing_folder = doc.getObject("Interference")
            for obj in existing_folder.Group:

                if obj.TypeId == 'App::Part':
                    obj.removeObjectsFromDocument() # Remove Part's content
                    doc.removeObject(obj.Name) # Remove the Part

                elif obj.TypeId == 'App::DocumentObjectGroup':

                    for obj2 in obj.Group:

                        if obj2.TypeId == "Part::MultiCommon":
                            for shape in obj2.Shapes:
                                doc.removeObject(shape.Name) # Remove Common's Parts
                            doc.removeObject(obj2.Name) # Remove Common

                    doc.removeObject(obj.Name) # Remove Group

            doc.removeObject(existing_folder.Name) # Remove Interference folder
            doc.recompute()
        except:
            pass

    def check_interferences(self, ilim=0, jlim=0):

        doc = App.ActiveDocument
        model = doc.Model

        if model == None:
            print("Assembly is missing")
            return

        self.remove_interference_folder()

        try:
            model = doc.Model
            model.Visibility = False
        except:
            model = doc.Assembly
            model.Visibility = False

        doc.Parts.Visibility = True
        for obj in doc.Parts.Group:
            try:
                obj.Visibility = False
            except: 
                pass

        # Create the Interference folder
        intersections_folder = doc.addObject('App::DocumentObjectGroup', 'Interference')
        doc.Tip = intersections_folder
        intersections_folder.Label = 'Interference'

        model_part = doc.addObject('App::Part', 'Assembly')
        doc.Tip = model_part
        model_part.Label = 'Assembly'
        intersections_folder.addObject(model_part)

        # Create the Common folder inside of the Interference
        common_folder = doc.addObject('App::DocumentObjectGroup', 'Common')
        doc.Tip = common_folder
        common_folder.Label = 'Common'
        intersections_folder.addObject(common_folder)

        doc.recompute()

        i = 0
        c = 1

        checked_dict = dict()

        for obj1 in model.Group:

            if obj1.Visibility == True and obj1.TypeId == 'App::Link':
            # if obj1.Visibility == True and
            #     ((obj1.TypeId == 'Part::FeaturePython' and (obj1.Content.find("FastenersCmd") or (obj1.Content.find("PCBStandoff")) > -1)) or
            #     (obj1.TypeId == 'App::Link')):

                print("\n==============================================================")
                i = i + 1
                j = 0

                for obj2 in model.Group:

                    if obj2 != obj1:

                        if obj2.Visibility == True and obj2.TypeId == 'App::Link':
                        # if obj2.Visibility == True and
                        #     ((obj2.TypeId == 'Part::FeaturePython' and (obj2.Content.find("FastenersCmd") or (obj2.Content.find("PCBStandoff")) > -1)) or
                        #     (obj2.TypeId == 'App::Link')):

                            j = j + 1
                            if not jlim == 0 and j >= jlim:
                                break

                            print(">> {} ({}, {}) {}, {}".format(c, i, j, obj1.Label, obj2.Label))

                            if not obj1.Label in checked_dict:

                                    c = c + 1

                                    # print("1st time {} being used, checking intersection (1)...".format(obj1.Label))

                                    obj1_list = []
                                    obj1_list.append(obj2.Label)
                                    checked_dict[obj1.Label] = obj1_list

                                    obj1_model_cpy = self.make_simple_part_copy(doc, obj1)
                                    model_part.addObject(obj1_model_cpy)
                                    obj1_model_cpy.Visibility = True
                                    obj1_model_cpy.ViewObject.Transparency = 92
                                    obj1_model_cpy.ViewObject.ShapeColor = (90, 90, 90)
                                    obj1_model_cpy.ViewObject.DisplayMode = "Shaded"

                                    # Also add the complement to the dictionary for complitude
                                    if not obj2.Label in checked_dict:
                                        obj2_list = []
                                        obj2_list.append(obj1.Label)
                                        checked_dict[obj2.Label] = obj2_list

                                        obj2_model_cpy = self.make_simple_part_copy(doc, obj2)
                                        model_part.addObject(obj2_model_cpy)
                                        obj2_model_cpy.Visibility = True
                                        obj2_model_cpy.ViewObject.Transparency = 92
                                        obj2_model_cpy.ViewObject.ShapeColor = (90, 90, 90)
                                        obj2_model_cpy.ViewObject.DisplayMode = "Shaded"


                                    obj1_cpy = self.make_simple_part_copy(doc, obj1)
                                    obj2_cpy = self.make_simple_part_copy(doc, obj2)
                                    common = self.make_intersection(doc, obj1_cpy, obj2_cpy, c)
                                    common_folder.addObject(common)

                            else:

                                if not obj2.Label in checked_dict[obj1.Label]:

                                    c = c + 1

                                    # print("Obj {} already used, checking intersection (2)...".format(obj1.Label))

                                    obj1_list = checked_dict[obj1.Label]
                                    obj1_list.append(obj2.Label)
                                    checked_dict[obj1.Label] = obj1_list

                                    if obj2.Label in checked_dict:
                                        obj2_list = checked_dict[obj2.Label]
                                        obj2_list.append(obj1.Label)
                                        checked_dict[obj2.Label] = obj2_list

                                    obj1_cpy = self.make_simple_part_copy(doc, obj1)
                                    obj2_cpy = self.make_simple_part_copy(doc, obj2)
                                    common = self.make_intersection(doc, obj1_cpy, obj2_cpy, c)
                                    common_folder.addObject(common)

                                # else:
                                    # print("Intersection already checked!")

                            Gui.updateGui()

                Gui.updateGui()

            if not ilim == 0 and i >= ilim:
                break


        # Update intersections (remove empty and change colors)
        print("\n>> PROCESSING INTERSECTIONS:")
        for obj in common_folder.Group:
            if obj.TypeId == "Part::MultiCommon":
                if not self.remove_empty_common(obj):
                    obj.ViewObject.Transparency = 60
                    r = rnd.random()
                    g = rnd.random()
                    b = rnd.random()
                    obj.ViewObject.ShapeColor = (r, g, b)

            Gui.updateGui()

        doc.recompute()

        # if obj1.TypeId == 'App::DocumentObjectGroup':
        #     for objname in obj1.getSubObjects():
        #         subobj = obj.Document.getObject(objname[0:-1])


        # print("\n>> CHECKED OBJECTS:")
        # for a, key in enumerate(checked_dict):
        #     print("  ", a+1, key)
        #     for b, item in enumerate(checked_dict[key]):
        #         print("    ", b+1, item)

        print("\n>> USED PARTS:")
        for p, part in enumerate(checked_dict):
            print("  ", p+1, part)
        print("")


class removeInterference:

    def __init__(self):
        super(removeInterference, self).__init__()

    def GetResources(self):

        menutext = "Remove Interference Checks"
        tooltip  = "Remove the generated interference checks, restoring visibilty of the Assembly."
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_Interference_Cleanup.svg')

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
        self.remove_interference_folder()

    def remove_interference_folder(self):

        doc = App.ActiveDocument

        try:
            model = doc.Model
            model.Visibility = True
        except:
            model = doc.Assembly
            model.Visibility = True

        doc.Parts.Visibility = True
        for obj in doc.Parts.Group:
            try:
                obj.Visibility = False
            except: 
                pass

        # Remove existing folder and its contents
        try:
            existing_folder = doc.getObject("Interference")
            for obj in existing_folder.Group:

                if obj.TypeId == 'App::Part':
                    obj.removeObjectsFromDocument() # Remove Part's content
                    doc.removeObject(obj.Name) # Remove the Part

                elif obj.TypeId == 'App::DocumentObjectGroup':

                    for obj2 in obj.Group:

                        if obj2.TypeId == "Part::MultiCommon":
                            for shape in obj2.Shapes:
                                doc.removeObject(shape.Name) # Remove Common's Parts
                            doc.removeObject(obj2.Name) # Remove Common

                    doc.removeObject(obj.Name) # Remove Group

            doc.removeObject(existing_folder.Name) # Remove Interference folder
            doc.recompute()
        except:
            pass


# Add the command in the workbench
Gui.addCommand('Asm4_checkInterference',  checkInterference())
Gui.addCommand('Asm4_removeInterference', removeInterference())

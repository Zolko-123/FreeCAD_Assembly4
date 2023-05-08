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

PARTID2CHECK = ['App::Link']


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
        # this has been checked before
        self.assembly = Asm4.getAssembly()
        self.modelDoc = self.assembly.Document
        # clean-up
        self.remove_interference_folder( self.modelDoc )
        self.assembly.Visibility = True
        self.modelDoc.recompute()
        Gui.updateGui()

        # Create the Interferences folder
        self.InterferencesGroup = self.modelDoc.addObject('App::DocumentObjectGroup', 'Interferences')
        self.InterferencesGroup.Label = 'Interferences'
        # This is where copies of the shapes are stored
        # self.ShapesCopy = self.modelDoc.addObject('App::Part', 'ShapesCopy')
        self.ShapesCopy = self.modelDoc.addObject('App::DocumentObjectGroup', 'ShapesCopy')
        self.ShapesCopy.Label = 'ShapesCopy'
        self.InterferencesGroup.addObject(self.ShapesCopy)
        # Create the Conflicts folder inside of the Interferences
        self.ConflictsGroup = self.modelDoc.addObject('App::DocumentObjectGroup', 'Conflicts')
        self.ConflictsGroup.Label = 'Conflicts'
        self.InterferencesGroup.addObject(self.ConflictsGroup)
        # self.ConflictsGroup = self.InterferencesGroup
        self.modelDoc.recompute()
        Gui.updateGui()

        # build the list of objects to consider
        self.partList = []
        print("\n>> BUILDING PART LIST ...")
        for obj in self.assembly.Group:
            if obj.Visibility and obj.TypeId in PARTID2CHECK :
                obj_cpy = self.make_shape_copy( self.modelDoc, obj )
                self.ShapesCopy.addObject( obj_cpy )
                self.partList.append( obj_cpy )
        print( "FOUND {} OBJECTS\n".format(len(self.partList)) )
        self.modelDoc.recompute()
        Gui.updateGui()

        # now check the interferences
        if len(self.partList) > 1:
            self.assembly.Visibility = False
            self.parse_interferences( self.modelDoc )
            # Update intersections (remove empty and change colors)
            print("\n>> PROCESSING INTERSECTIONS ... ")
            hasConflict = False
            for obj in self.ConflictsGroup.Group:
                if obj.TypeId == "Part::MultiCommon" :
                    if obj.Shape.Volume > 0.0:
                        hasConflict = True
                        obj.ViewObject.Transparency = 0
                        r = rnd.random()
                        g = rnd.random()
                        b = rnd.random()
                        obj.ViewObject.ShapeColor = (r, g, b)
                    else:
                        self.modelDoc.removeObject(obj.Name)
        else:
            print('Not enough parts for intersections\n')
        # Summary
        if hasConflict:
            print("DONE. \nThere seems to be some conflicts between parts\n")
        else:
            print("DONE. No conflicts found\n")
        self.modelDoc.recompute()
        Gui.updateGui()


    # makes a new Part::Feature and assignes it the shape of the original object
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
        new_obj.ViewObject.Transparency = 85
        new_obj.ViewObject.DisplayMode = "Shaded"
        new_obj.ViewObject.ShapeColor = (0.90, 0.90, 0.90)
        # doc.recompute()
        return new_obj


    def parse_interferences( self, doc ):
        l = len(self.partList)
        start = 0
        # obj1 parses all objects
        for obj1 in self.partList:
            start += 1
            # obj2 parses only objects after obj1
            for obj2 in self.partList[start:]:
                common = self.make_intersection( doc, obj1, obj2 )
                if common is not None:
                    self.ConflictsGroup.addObject(common)


    def make_intersection( self, doc, obj1, obj2 ):
        retval = None
        obj = doc.addObject("Part::MultiCommon", "Common")
        obj.Shapes = [obj1, obj2]
        obj1.Visibility = True
        obj2.Visibility = True
        obj.Label = "Conflict - {} - {}".format( obj1.Label, obj2.Label)
        obj.ViewObject.ShapeColor = (1.0, 0.666, 0.) # YELLOW
        obj.ViewObject.Transparency = 0
        obj.ViewObject.DisplayMode = "Shaded"
        doc.recompute()
        # if the shape is NULL remove the intersection
        if obj.Shape.isNull():
            doc.removeObject(obj.Name)
        else:
            obj.Label2 = "Volume = {:4f}".format(obj.Shape.Volume)
            retval = obj
        return retval


    # if restarting the test
    def remove_interference_folder(self, doc):
        for obj in doc.Parts.Group:
            try:
                obj.Visibility = False
            except: 
                pass
        # Remove existing folder and its contents
        try:
            existing_folder = doc.getObject("Interferences")
            for obj in existing_folder.Group:
                if obj.TypeId == 'App::Part' or obj.TypeId == 'App::DocumentObjectGroup':
                    obj.removeObjectsFromDocument() # Remove Part's content
                    doc.removeObject(obj.Name) # Remove the Part
                '''
                elif obj.TypeId == 'App::DocumentObjectGroup':
                    for obj2 in obj.Group:
                        if obj2.TypeId == "Part::MultiCommon":
                            for shape in obj2.Shapes:
                                doc.removeObject(shape.Name) # Remove Common's Parts
                            doc.removeObject(obj2.Name) # Remove Common
                    doc.removeObject(obj.Name) # Remove Group
                '''
            doc.removeObject(existing_folder.Name) # Remove Interference folder
            doc.recompute()
        except:
            pass



# Add the command in the workbench
Gui.addCommand('Asm4_checkInterference',  checkInterference())

#!/usr/bin/env python3
# coding: utf-8
#
# makeBomCmd.py
#
# Parses the Asm4 Assembly tree and creates a list of parts
#
# Customization
# - Follow_Subasseemblies
# - Consider Objects with the same name, from different sub-assemblies, the same. (Should Disable/Hide the Doc_Name column to group items)
# - Configurable depth inside the App::Parts

'''
    >>>> (Initial) BOM Rules <<<<<

    - Asm4 App:Part
      IF Main/Root Asm4: Follow objects
      ELSE:
         IF Visible:
            IF follow_subassemblies: Follow objects on Group
            ELSE: Create/Update its Record

    - App:Part (not Asm4)
      IF nested_level < max_nested_level: Follow objects on Group
      ELSE: Create/Update its Record

    - Visible App::Link
      Follow ALL LinkedObjects (passing the ElementsCount)

    - PartDesign::Body
      Create/Update its Record

    - Visible Python::Array
      Follow objects on Group (passing the ElementsCount)

    - Visible Python::Fastener
      Create/Update its Record

    - Visible App::DocumentObjectGroup
      Follow objects on Group
'''


import os
import json
import re
import math
from decimal import *

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4
import infoPartCmd
import infoKeys

create_partinfo_fields = infoPartCmd.infoPartUI.create_partinfo_fields
set_partinfo_data = infoPartCmd.infoPartUI.set_partinfo_data


class makeBOM:

    def __init__(self):
        super(makeBOM, self).__init__()
        self.log_msg = str()
        self.parts_dict = dict()
        self.follow_subassemblies = False
        self.subassembly_parts_are_the_same = True
        self.max_part_nested_level = 0
        self.parts_list_done = False
        self.total_number_of_objects = 0
        self.current_progress_value = 0
        self.abort_operation = False
        self.sort_doclabel = False
        self.verbose = True # TODO: IT SHOULD BE FALSE, HERE IS IS TRUE FOR DEBUGGIN


    def GetResources(self):

        menutext = "Bill of Materials"
        tooltip  = "Create the Bill of Materials of the Assembly with Sub-Assemblies"
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_PartsList_Subassemblies.svg')

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

        self.log_msg = str()

        self.UI = QtGui.QDialog()
        self.drawUI()
        self.UI.show()

        self.log_clear()
        self.load_config_file()

        if self.parts_dict:
            self.parts_dict.clear()

        # self.progress_bar.setMaximum()
        n_objs = self.number_of_objects()
        self.progress_bar.setMaximum(n_objs)

        # TODO: The VERBOSE should start as "False"
        # When it starts with True, it executes automatically (debugging only)
        if self.verbose:
            self.log_write('\n>>> DEBUGGING VERBOSE ACTIVATED <<<')
            self.log_write('\n>>> GENERATING PARTS LIST <<<\n')
            self.log_write('Chill, this may take time... \n')
            self.export_bom_button.setEnabled(False)
            self.cancel_button.setText("Abort")
            self.list_parts(self.Assembly)
            if not self.abort_operation:
                self.export_bom_button.setEnabled(True)
                self.log_write('\n>>> Parts Listing Done <<<\n')
                self.log_parts_dict()
                self.log_parts_quantities()
                self.create_bom_spreadsheet()
                self.cancel_button.setText("Close")
            else:
                self.log_write('\n>>> PARTS LISTING ABORTED <<<\n')
                self.cancel_button.setText("Cancel")
                self.progress_bar_reset()

            self.parts_list_done = True
            self.abort_operation = False


    def log_clear(self):
        self.log_msg = str()
        self.log_view.setPlainText(self.log_msg)


    def log_write(self, msg, end="\n"):
        self.log_msg += "{}{}".format(msg, end)
        self.log_view.setPlainText(self.log_msg)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())
        Gui.updateGui()


    def number_of_objects(self):
        n = self.count_parts(self.Assembly)
        self.log_write("Number of objects: {}".format(n))
        return n


    def count_parts(self, obj, hier_level=0, part_level=0, ignore_visibility=False, count=0):

        count_objs = count + 1

        if obj == None:
            return count_objs

        # Visible Assembly App::Part
        if self.isAssembly(obj):
            if hier_level == 0: # Assembly root
                if obj.Visibility == True:
                    for obj_name in obj.getSubObjects():
                        nested_obj = obj.Document.getObject(obj_name[0:-1])
                        count_objs = self.count_parts(nested_obj, hier_level+1, part_level, count=count_objs)
            else:
                if self.follow_subassemblies:
                    for obj_name in obj.getSubObjects():
                        nested_obj = obj.Document.getObject(obj_name[0:-1])
                        count_objs = self.count_parts(nested_obj, hier_level+1, part_level, count=count_objs)
                # else:
                    # pass

        # App::Part
        elif obj.TypeId == 'App::Part' and not self.isAssembly(obj):
            if part_level == self.max_part_nested_level:
                pass
            else:
                # level 0 until max-1
                for obj_name in obj.getSubObjects():
                    nested_obj = obj.Document.getObject(obj_name[0:-1])
                    count_objs = self.count_parts(nested_obj, hier_level+1, part_level+1, count=count_objs)

        # Visible App::Link (and App:Link Array)
        elif (obj.Visibility == True or ignore_visibility) and obj.TypeId == 'App::Link':
            if self.isAssembly(obj):
                pass
            else:
                count = obj.ElementCount
                if count == 0:
                    count = 1
                for i in range(count):
                    count_objs = self.count_parts(obj.LinkedObject, hier_level+1, part_level, ignore_visibility=True, count=count_objs)

        # PartDesign::Body
        elif obj.TypeId == 'PartDesign::Body':
            pass

        # Visible Python::Array
        elif (obj.Visibility == True or ignore_visibility) and obj.TypeId == 'Part::FeaturePython' and hasattr(obj, 'ArrayType'):
            count = obj.Count
            if count == 0:
                count = 1
            for i in range(count):
                count_objs = self.count_parts(obj.SourceObject, hier_level+1, part_level, ignore_visibility=True, count=count_objs)

        # Python::Fastener
        elif (obj.Visibility == True or ignore_visibility) and self.isFastener(obj):
            pass

        # Visible App::DocumentObjectGroup
        elif obj.Visibility == True and obj.TypeId == 'App::DocumentObjectGroup':
            for obj_name in obj.getSubObjects():
                nested_obj = obj.Document.getObject(obj_name[0:-1])
                count_objs = self.count_parts(nested_obj, hier_level+1, part_level, count=count_objs)

        # else:
            # pass

        return count_objs



    def log_parts_quantities(self):

        def filter_bodies(key_val):
            key, value = key_val
            if re.match("body*", value["Type_Label"],  re.IGNORECASE): return True
            else: return False

        def filter_parts(key_val):
            key, value = key_val
            if re.match("part*", value["Type_Label"],  re.IGNORECASE): return True
            else: return False

        def filter_fasteners(key_val):
            key, value = key_val
            if re.match("fastener*", value["Type_Label"],  re.IGNORECASE): return True
            else: return False

        def filter_subassemblies(key_val):
            key, value = key_val
            if re.match("sub[*]assembl*", value["Type_Label"],  re.IGNORECASE): return True
            else: return False

        def uniq_objs_qty(d):
            return len(d)

        def total_objs_qty(d):
            qty = 0
            for k, v in d.items():
                qty += v["Qty"]
            return qty

        def print_formatted_table(h,  d):
            self.log_write(' '.join([str(v) for v in h]))
            max_keylen = len(max(d.keys(), key=len))
            max_col_len = 6
            for k1, v1 in d.items():
                for k2, v2 in v1.items():
                    if k2 ==   "Uniq":   uniq = v2
                    if k2 ==  "Total":  total = v2
                    if k2 == "Reused": reused = v2
                self.log_write("{i} {u} {t} {r}".format(i=k1.rjust(max_keylen), u=str(uniq).rjust(max_col_len), t=str(total).rjust(max_col_len), r=str(reused).rjust(max_col_len)))


        bodies_d = dict(filter(filter_bodies, self.parts_dict.items()))
        parts_d = dict(filter(filter_parts, self.parts_dict.items()))
        fasteners_d = dict(filter(filter_fasteners, self.parts_dict.items()))
        subassemblies_d = dict(filter(filter_subassemblies, self.parts_dict.items()))

        # self.log_write('\n>>> PARTS ONLY <<<\n')
        # self.log_write(json.dumps(parts_d, indent=4))
        # self.log_write('\n>>> FASTENERS ONLY <<<\n')
        # self.log_write(json.dumps(fasteners_d, indent=4))

        self.log_write("\n>>> PARTS SUMMARY <<<\n")

        bom_summary = dict()

        bom_summary["Bodies"] = {
              "Uniq":  uniq_objs_qty(bodies_d),
             "Total": total_objs_qty(bodies_d),
            "Reused": total_objs_qty(bodies_d) - uniq_objs_qty(bodies_d)}

        bom_summary["Parts"] = {
              "Uniq":  uniq_objs_qty(parts_d),
             "Total": total_objs_qty(parts_d),
            "Reused": total_objs_qty(parts_d) - uniq_objs_qty(parts_d)}

        bom_summary["Fasteners"] = {
              "Uniq":  uniq_objs_qty(fasteners_d),
             "Total": total_objs_qty(fasteners_d),
            "Reused": total_objs_qty(fasteners_d) - uniq_objs_qty(fasteners_d)}

        bom_summary["Subassemblies"] = {
              "Uniq":  uniq_objs_qty(subassemblies_d),
             "Total": total_objs_qty(subassemblies_d),
            "Reused": total_objs_qty(subassemblies_d) - uniq_objs_qty(subassemblies_d)}

        bom_summary["Total"] = {
             "Uniq":  uniq_objs_qty(bodies_d) +  uniq_objs_qty(parts_d) +  uniq_objs_qty(fasteners_d) +  uniq_objs_qty(subassemblies_d),
            "Total": total_objs_qty(bodies_d) + total_objs_qty(parts_d) + total_objs_qty(fasteners_d) + total_objs_qty(subassemblies_d)}

        header = ["OBJECTS".rjust(13), "UNIQ".rjust(6), "TOTAL".rjust(6), "REUSED".rjust(6)]

        # self.log_write(json.dumps(bom_summary, indent=4))
        print_formatted_table(header, bom_summary)


    def load_config_file(self):
        self.infoKeysUser = infoPartCmd.load_config_file()


    def create_record(self, obj, doc_name, obj_label, qty=1):

        self.parts_dict[obj_label] = dict()

        for prop in self.infoKeysUser:

            value = ""
            info = ""

            if self.infoKeysUser.get(prop).get('active'):

                field_name = self.infoKeysUser.get(prop).get('userData')

                if not hasattr(obj, field_name):
                    create_partinfo_fields(self, obj)
                    # set_partinfo_data(obj)

                if hasattr(obj, field_name):
                    if getattr(obj, field_name):
                        value = getattr(obj, field_name)
                        info = "(from PartInfo)"

                if value == "" or value == "-":

                    info = "(from makeBOM)"

                    if prop == self.infoKeysUser.get("Doc_Label").get('userData'):
                        value = doc_name

                    elif prop == self.infoKeysUser.get("Type_Label").get('userData'):
                        if self.isAssembly(obj):
                            value = "Subassembly"
                        elif obj.TypeId == 'PartDesign::Body':
                            value = "Body"
                        else:
                            value = "Part"

                    elif prop == self.infoKeysUser.get("Part_Label").get('userData'):
                        value = obj_label

                    elif prop == self.infoKeysUser.get('Pad_Length').get('userData'):
                        if obj.Pad_Length:
                            value = obj.Pad_Length
                            # getcontext().prec = 2
                            # value = '\'' + Decimal(obj.Pad_Length).normalize().to_eng_string()
                        else:
                            value = "-"

                    elif prop == self.infoKeysUser.get('Shape_Length').get('userData'):
                        value = obj.Shape.Length
                        # getcontext().prec = 2
                        # value = '\'' + Decimal(obj.Shape.Length).normalize().to_eng_string()

                    elif prop == self.infoKeysUser.get('Shape_Volume').get('userData'):
                        if obj.Shape.Volume < 0:
                            value = ""
                        else:
                            value = obj.Shape.Volume
                        # getcontext().prec = 2
                        # value = '\'' + Decimal(obj.Shape.Volume).normalize().to_eng_string()


                    else:
                        value = "-"

                    if value == "":
                        # value = field_name
                        value = ""

                # if not "Fastener_" in prop:
                if self.infoKeysUser.get(prop).get('visible'):
                    if value != "-" or not self.verbose:
                        self.log_write("  | {}: {} {}".format(prop, value, info))

                self.parts_dict[obj_label][self.infoKeysUser.get(prop).get('userData')] = value

        self.parts_dict[obj_label]['Qty'] = 1
        self.log_write("  | Quantity = {}".format(self.parts_dict[obj_label]['Qty']))


    def increment_qty(self, obj, obj_label, qty=1):
        qty = self.parts_dict[obj_label]['Qty'] + int(qty)
        self.log_write("  | Already accounted for".format(qty))
        self.log_write("  | Quantity = {}".format(qty))
        self.parts_dict[obj_label]['Qty'] = qty


    def record_body(self, obj):

        doc_name = obj.Document.Label
        if self.infoKeysUser.get("Doc_Label").get('active'):
            if hasattr(obj, self.infoKeysUser.get("Doc_Label").get('userData')):
                if getattr(obj, self.infoKeysUser.get("Doc_Label").get('userData')):
                    doc_name = getattr(obj, self.infoKeysUser.get("Doc_Label").get('userData'))

        if not obj.Label in self.parts_dict:
            self.create_record(obj, doc_name, obj.Label)
        else:
            if self.parts_dict[obj.Label]["Doc_Label"] == doc_name or not self.subassembly_parts_are_the_same:
                self.increment_qty(obj, obj.Label)
            else:
                self.create_record(obj, doc_name, obj.Label)


    def record_part(self, obj):

        doc_field_name = self.infoKeysUser.get("Doc_Label").get('userData')

        # Recover doc_name from parts_dict
        try:
            if self.infoKeysUser.get("Doc_Label").get('active'):
                try:
                    doc_name = getattr(obj, doc_field_name)
                    if doc_name == "":
                        doc_name = obj.Document.Label
                except AttributeError:
                    doc_name = obj.Document.Label
            else:
                doc_name = obj.Document.Label
        except:
            doc_name = obj.Document.Label

        # Recover obj_label from parts_dict
        try:
            if self.infoKeysUser.get("Part_Label").get('active'):
                try:
                    obj_label = getattr(obj, self.infoKeysUser.get("Part_Label").get('userData'))
                    if obj_label == "":
                        obj_label = obj.Label
                except AttributeError:
                    obj_label = obj.Label
            else:
                obj_label = obj.Label
        except:
            obj_label = obj.Label

        # If multiple sub-assembly objects have the same name (Assembly/Model), they will be grouped
        # This is not intended and may happen since people don't rename this object like I do
        if obj_label == "Model" or obj_label == "Assembly":
           obj_label = doc_name


        if not obj_label in self.parts_dict:
            self.create_record(obj, doc_name, obj_label)
        else:
            if self.parts_dict[obj_label]["Doc_Label"] == doc_name or not self.subassembly_parts_are_the_same:
                self.increment_qty(obj, obj_label)
            else:
                self.create_record(obj, doc_name, obj_label)


    def isAssembly(self, obj):
        if not obj:
            return False
        if obj.TypeId == 'App::Part':
            if hasattr(obj, 'Type') and obj.Type == 'Assembly':
                return True
        return False

    def isFastener(self, obj):
        if not obj:
            return False
        if obj.TypeId == 'Part::FeaturePython' and ((obj.Content.find("FastenersCmd") > -1) or (obj.Content.find("PCBStandoff") > -1)):
            return True
        return False


    def record_fastener(self, obj):

        doc_name = os.path.splitext(os.path.basename(obj.Document.FileName))[0]
        obj_label = re.sub(r'[0-9]+$', '', obj.Label)

        if obj_label in self.parts_dict:

            if self.parts_dict[obj_label]["Doc_Label"] == doc_name or not self.subassembly_parts_are_the_same:
                qty = self.parts_dict[obj_label]['Qty'] + 1
                self.log_write("  | Quantity = {}".format(qty))
                self.parts_dict[obj_label]['Qty'] = qty

        else:

            self.parts_dict[obj_label] = dict()
            for prop in self.infoKeysUser:

                if prop == "Doc_Label":
                    value = doc_name

                elif prop == "Type_Label":
                    value = "Fastener"

                elif prop == "Part_Label":
                    value = obj_label

                elif prop == "Fastener_Diameter":
                    try:
                        value = obj.diameter
                    except:
                        value = obj.SourceObject.diameter

                elif prop == "Fastener_Type":
                    try:
                        value = obj.type
                    except:
                        value = obj.SourceObject.type

                elif prop == "Fastener_Length":
                    try:
                        value = obj.length
                    except:
                        value = obj.SourceObject.lengthCustom
                else:
                    value = "-"

                if value != "-" or not self.verbose:
                    self.log_write("  | {}: {}".format(prop, value))

                self.parts_dict[obj_label][self.infoKeysUser.get(prop).get('userData')] = value

            qty = 1
            self.parts_dict[obj_label]['Qty'] = qty
            self.log_write("  | Quantity = {}".format(qty))


    # Recursive method to collect BOM data
    def list_parts(self, obj, hier_level=0, part_level=0, ignore_visibility=False):

        if self.abort_operation:
            return

        if obj == None:
            return

        self.progress_bar_progress()

        if self.verbose:
            obj_visibility = ""
            if not obj.Visibility:
                obj_visibility = "(INVISIBLE)"
            self.log_write("\n> [DEBUG] [{hl},{pl}] ({tid}) {lbl} {v}".format(hl=hier_level, pl=part_level, tid=obj.TypeId, lbl=obj.Label, v=obj_visibility))

        # Visible Assembly App::Part
        if self.isAssembly(obj):
            self.log_write("> [{hl},{pl}] ({tid}) {lbl}".format(hl=hier_level, pl=part_level, tid="App::Part(Asm4)", lbl=obj.Label))
            if hier_level == 0: # Assembly root
                if obj.Visibility == True:
                    for obj_name in obj.getSubObjects():
                        nested_obj = obj.Document.getObject(obj_name[0:-1])
                        self.list_parts(nested_obj, hier_level+1, part_level)
            else:
                if self.follow_subassemblies:
                    for obj_name in obj.getSubObjects():
                        nested_obj = obj.Document.getObject(obj_name[0:-1])
                        self.list_parts(nested_obj, hier_level+1, part_level)
                else:
                    self.record_part(obj)

        # App::Part
        elif obj.TypeId == 'App::Part' and not self.isAssembly(obj):
            self.log_write("> [{hl},{pl}] ({tid}) {lbl}".format(hl=hier_level, pl=part_level, tid=obj.TypeId, lbl=obj.Label))
            if part_level == self.max_part_nested_level:
                self.record_part(obj)
            else:
                # level 0 until max-1
                for obj_name in obj.getSubObjects():
                    nested_obj = obj.Document.getObject(obj_name[0:-1])
                    self.list_parts(nested_obj, hier_level+1, part_level+1)

        # Visible App::Link (and App:Link Array)
        elif (obj.Visibility == True or ignore_visibility) and obj.TypeId == 'App::Link':
            if self.verbose:
                self.log_write("> [{hl},{pl}] ({tid}) {lbl}".format(hl=hier_level, pl=part_level, tid=obj.TypeId, lbl=obj.Label))
                if obj.ElementCount > 0:
                    self.log_write("  | Element count = {}".format(obj.ElementCount))
            if self.isAssembly(obj):
                if self.follow_subassemblies:
                    for obj_name in obj.getSubObjects():
                        nested_obj = obj.Document.getObject(obj_name[0:-1])
                        self.list_parts(nested_obj, hier_level+1, part_level)
                else:
                    # self.record_part(obj)
                    # self.record_part(obj.LinkedObject)
                    self.list_parts(obj.LinkedObject, hier_level, part_level, ignore_visibility=True)
            else:
                count = obj.ElementCount
                if count == 0:
                    count = 1
                for i in range(count):
                    self.list_parts(obj.LinkedObject, hier_level+1, part_level, ignore_visibility=True)

        # PartDesign::Body
        elif obj.TypeId == 'PartDesign::Body':
            self.log_write("> [{hl},{pl}] ({tid}) {lbl}".format(hl=hier_level, pl=part_level, tid=obj.TypeId, lbl=obj.Label))
            self.record_body(obj)

        # Visible Python::Array
        elif (obj.Visibility == True or ignore_visibility) and obj.TypeId == 'Part::FeaturePython' and hasattr(obj, 'ArrayType'):
            if self.verbose:
                self.log_write("> [{hl},{pl}] ({tid}) {lbl}".format(hl=hier_level, pl=part_level, tid="Python::Array", lbl=obj.Label))
                self.log_write("  | Link count = {}".format(obj.Count))
            count = obj.Count
            if count == 0:
                count = 1
            for i in range(count):
                self.list_parts(obj.SourceObject, hier_level+1, part_level, ignore_visibility=True)

        # Python::Fastener
        elif (obj.Visibility == True or ignore_visibility) and self.isFastener(obj):
            self.log_write("> [{hl},{pl}] ({tid}) {lbl}".format(hl=hier_level, pl=part_level, tid="Python::Fastener", lbl=obj.Label))
            self.record_fastener(obj)

        # Visible App::DocumentObjectGroup
        elif obj.Visibility == True and obj.TypeId == 'App::DocumentObjectGroup':
            if self.verbose:
                self.log_write("> [{hl},{pl}] ({tid}) {lbl}".format(hl=hier_level, pl=part_level, tid=obj.TypeId, lbl=obj.Label))
            for obj_name in obj.getSubObjects():
                nested_obj = obj.Document.getObject(obj_name[0:-1])
                self.list_parts(nested_obj, hier_level+1, part_level)

        else:
            if self.verbose:
                self.log_write("> NOT_USED: [{hl},{pl}] ({tid}) {lbl}".format(hl=hier_level, pl=part_level, tid=obj.TypeId, lbl=obj.Label))

        return


    def create_bom_spreadsheet(self):

        def write_row(drow: [str], row: int):
            for i, d in enumerate(drow):
                if row == 0: # header
                    self.bom_spreadsheet.set(str(chr(ord('a') + i)).upper() + str(row + 1), infoPartCmd.decodeXml(str(d)))
                else:
                    self.bom_spreadsheet.set(str(chr(ord('a') + i)).upper() + str(row + 1), str(d))

        def to_column_index(n):
            name = ''
            while n > 0:
                index = (n - 1) % 26
                name += chr(index + ord('A'))
                n = (n - 1) // 26
            return name[::-1]

        if not self.parts_list_done:
            self.export_bom_button.setEnabled(True)
            return

        if len(self.parts_dict) == 0:
            return

        creating_new_bom = 0
        if not hasattr(self.Document, 'BOM'):
            self.bom_spreadsheet = self.Document.addObject('Spreadsheet::Sheet', 'BOM')
            self.bom_spreadsheet.Label = "BOM"
            creating_new_bom = 1
        else:
            self.bom_spreadsheet = self.Document.BOM
            self.bom_spreadsheet.clearAll()

        local_parts_dict = self.parts_dict
        if self.sort_doclabel:
            local_parts_dict = dict(sorted(self.parts_dict.items()))

        parts_values = list(local_parts_dict.values())
        n_parts_values = len(parts_values[0].keys())

        write_row(parts_values[0].keys(), 0) # header
        for i, _ in enumerate(parts_values):
            write_row(parts_values[i].values(), i+1)

        # Customize spreadsheet header
        self.bom_spreadsheet.setAlignment( 'A1:{}1'.format(to_column_index(n_parts_values)), 'center|vcenter|vimplied')
        self.bom_spreadsheet.setForeground('A1:{}1'.format(to_column_index(n_parts_values)), (1.0, 1.0, 1.0, 1.0))
        self.bom_spreadsheet.setBackground('A1:{}1'.format(to_column_index(n_parts_values)), (0.0, 0.0, 0.0, 1.0))
        App.ActiveDocument.recompute()

        # Customize spreadsheet columns - Centralinzing text
        rows = len(list(local_parts_dict.values()))+1
        for i, header in enumerate(parts_values[0].keys()):
            if header == "Fastener_Diameter" or header == "Fastener_Length" or header == "Fastener_Type" or header == "Qty":
                self.bom_spreadsheet.setAlignment('{c}2:{c}{r}'.format(c=to_column_index(i+1), r=rows), 'center|vcenter|vimplied')

        # Optimize column width
        for i, header in enumerate(parts_values[0].keys()):
            l = list(map(str, [d[header] for d in parts_values]))
            l.append(header)
            max_len = len(max(l, key=len))
            pixel = 1/92
            pixels = math.ceil(max_len / pixel * 0.09)
            # mm = pixels * 1/92
            # print(header, max_len, pixels, mm)
            self.bom_spreadsheet.setColumnWidth('{c}'.format(c=to_column_index(i+1)), pixels)

        if creating_new_bom:
            self.log_write("\n>>> BOM was Created <<<")
        else:
            self.log_write("\n>>> BOM was Updated <<<")

        self.cancel_button.setText("Close")
        self.Document.recompute()

        self.parts_list_done = False  # to Reset it
        self.export_bom_button.setEnabled(False)

        App.ActiveDocument.recompute()
        Gui.updateGui()


    def on_follow_subassemblies_checkbox(self, state):
        if state == QtCore.Qt.Checked:
            self.follow_subassemblies = True
        else:
            self.follow_subassemblies = False


    def on_same_parts(self, state):
        if state == QtCore.Qt.Checked:
            self.subassembly_parts_are_the_same = True
        else:
            self.subassembly_parts_are_the_same = False


    def on_sort_doclabel_checkbox(self, state):
        if state == QtCore.Qt.Checked:
            self.sort_doclabel = True
        else:
            self.sort_doclabel = False


    def on_verbose_checkbox(self, state):
        if state == QtCore.Qt.Checked:
            self.verbose = True
        else:
            self.verbose = False


    def log_parts_dict(self):
        self.log_write('\n>>> PARTS DICTIONARY <<<\n')
        self.log_write(json.dumps(self.parts_dict, indent=4))


    def on_generate_parts_list(self):
        self.log_clear()
        self.progress_bar_reset()
        self.log_write('\n>>> GENERATING PARTS LIST <<<\n')
        self.log_write('Chill, this may take time, sometimes... \n')
        self.cancel_button.setText("Abort")
        self.max_part_nested_level = int(self.parts_depth_input.text())
        self.parts_dict.clear()
        self.export_bom_button.setEnabled(False)
        self.list_parts(self.Assembly)

        if not self.abort_operation:
            self.export_bom_button.setEnabled(True)
            self.log_write('\n>>> Parts Listing Done <<<\n')
            if self.verbose:
                self.log_parts_dict()
            self.log_parts_quantities()
            self.cancel_button.setText("Close")
        else:
            self.log_write('\n>>> PARTS LISTING ABORTED <<<\n')
            self.cancel_button.setText("Cancel")
            self.progress_bar_reset()

        self.parts_list_done = True
        self.abort_operation = False


    def on_update_bom_spreedsheet(self):
        self.create_bom_spreadsheet()
        self.export_bom_button.setText("Update BOM Spreadsheet")
        self.parts_list_done = False
        self.export_bom_button.setEnabled(False)


    def on_cancel(self):
        if not self.cancel_button.text() == "Abort":
            self.UI.close()
            try:
                Gui.Selection.addSelection(self.Document.Name, self.bom_spreadsheet.Name)
                Gui.updateGui()
            except:
                pass
        else:
            self.abort_operation = True


    def progress_bar_reset(self):
        self.current_progress_value = 0
        self.progress_bar.reset()


    def progress_bar_progress(self):
        if self.current_progress_value <= self.progress_bar.maximum():
            self.current_progress_value += 1
            self.progress_bar.setValue(self.current_progress_value)


    def drawUI(self):

        self.UI.setWindowTitle('Generate a Bill of Materials (BOM)')
        self.UI.setWindowIcon(QtGui.QIcon(os.path.join(Asm4.iconPath, 'FreeCad.svg')))
        self.UI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.UI.setModal(False)
        self.main_layout = QtGui.QVBoxLayout(self.UI)

        self.follow_subassemblies_checkbox = QtGui.QCheckBox("Include sub-assemblies parts?")
        tooltip = """
        (DEFAULT) If Unchecked, the Sub-assembly will be added to the BOM as a Part.
        Otherwise, if Checked, the contents of the Sub-assembly will be added instead.
        """
        self.follow_subassemblies_checkbox.setToolTip(tooltip)
        self.follow_subassemblies_checkbox.setChecked(self.follow_subassemblies)
        self.follow_subassemblies_checkbox.stateChanged.connect(self.on_follow_subassemblies_checkbox)

        self.form_layout = QtGui.QFormLayout()
        self.parts_depth_label = QtGui.QLabel("Non-Asm4 Parts depth")
        self.parts_depth_input = QtGui.QLineEdit()
        self.parts_depth_input.setFixedWidth(10)
        self.parts_depth_input.setText(str(self.max_part_nested_level))
        self.form_layout.addRow(self.parts_depth_label, self.parts_depth_input)

        self.same_parts_checkbox = QtGui.QCheckBox("Objects with same name, in different sub-assemblies, are the same object")
        self.same_parts_checkbox.setToolTip("Do not group objects with the same name in different sub-assemblies.")
        self.same_parts_checkbox.setChecked(self.subassembly_parts_are_the_same)
        self.same_parts_checkbox.stateChanged.connect(self.on_same_parts)

        self.sort_doclabel_checkbox = QtGui.QCheckBox("Sort Doc_Label Column on BOM")
        self.sort_doclabel_checkbox.setToolTip("Sort Doc_Label Column on spreadsheet, otherwise items are placed in the order they appear.")
        self.sort_doclabel_checkbox.setChecked(self.sort_doclabel)
        self.sort_doclabel_checkbox.stateChanged.connect(self.on_sort_doclabel_checkbox)

        self.verbose_checkbox = QtGui.QCheckBox("Verbose")
        self.verbose_checkbox.setChecked(self.verbose)
        self.verbose_checkbox.stateChanged.connect(self.on_verbose_checkbox)

        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addWidget(self.follow_subassemblies_checkbox)
        self.vbox.addWidget(self.same_parts_checkbox)
        self.vbox.addLayout(self.form_layout)
        self.vbox.addWidget(self.sort_doclabel_checkbox)
        self.vbox.addWidget(self.verbose_checkbox)
        self.vbox.addStretch(1)
        self.vbox.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        self.gbox = QtGui.QGroupBox()
        self.gbox.setLayout(self.vbox)
        self.main_layout.addWidget(self.gbox)

        self.progress_bar = QtGui.QProgressBar()
        self.progress_bar.setValue(0)
        self.main_layout.addWidget(self.progress_bar)

        self.log_view = QtGui.QPlainTextEdit()
        self.log_view.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        self.log_view.setMinimumWidth(Gui.getMainWindow().width()/2.8)
        self.log_view.setMinimumHeight(Gui.getMainWindow().height()/3)
        self.log_view.ensureCursorVisible()
        self.log_view.moveCursor(QtGui.QTextCursor.End)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())
        f = QtGui.QFont("unexistent");
        f.setStyleHint(QtGui.QFont.Monospace);
        self.log_view.setFont(f);
        self.main_layout.addWidget(self.log_view)

        self.button_layout = QtGui.QHBoxLayout()

        self.parse_bom_button = QtGui.QPushButton('Generate Parts Lists')
        self.parse_bom_button.setDefault(True)
        self.parse_bom_button.clicked.connect(self.on_generate_parts_list)

        if not hasattr(self.Document, 'BOM'):
            export_bom_button_text = "Create BOM Spreadsheet"
        else:
            export_bom_button_text = "Update BOM Spreadsheet"

        self.export_bom_button = QtGui.QPushButton(export_bom_button_text)
        self.export_bom_button.setDefault(True)
        self.export_bom_button.clicked.connect(self.on_update_bom_spreedsheet)

        self.cancel_button = QtGui.QPushButton('Cancel')
        self.cancel_button.setDefault(True)
        self.cancel_button.clicked.connect(self.on_cancel)

        self.button_layout.addWidget(self.parse_bom_button)
        self.button_layout.addWidget(self.export_bom_button)
        self.button_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(self.button_layout)

        self.UI.setLayout(self.main_layout)


Gui.addCommand('Asm4_makeBOM', makeBOM())

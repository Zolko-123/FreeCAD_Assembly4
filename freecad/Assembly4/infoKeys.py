#!/usr/bin/env python3
# coding: utf-8
#
# LGPL

# The intent to infoKeys.py is to allow for allow for user customization but also a basic core functionality so #that minimum part list can be extracted in part theory partInfoUser and InfoToolTup user could be blank and it #should till work.



import os, json
import FreeCAD as App

from . import Asm4_libs as Asm4

#UserAdded fields and routines should be defined  this is file.
# if you make modifications to this, you'll want to delete the Json file
# Then you'll need to go into the gui and



partInfoUserAdded = [
'FileName']
''' Implement this later
    'DrawnBy',
    'DrawnDate',
    'CheckedBy',
    'CheckDate']
'''

infoToolTipUserAdded ={
'FileName': 'File Name'}
'''
    'DrawnBy': 'Drawn By',
    'DrawnDate': 'Drawn Date',
    'CheckedBy': ' Checked By',
    'CheckDate': 'Check Date'}
'''



#infoPartCmd has base values that get used if this function fails
def AssignCustomerValuesIntoUserFieldsForPartWithSingleBody(part, doc, singleBodyOfPart):
    #Different people have different use cases
    #basic functionality should work if an exception is thrown.
    #JT I made some very specfic customizations for my work flow which work for me.
    #

    if '/home/jonasthomas' in doc.FileName:
        #
        jtCustomizations(part, doc, singleBodyOfPart)

    else:

        #The parts list will still generate from functions within infopartcmd
        raise NotImplementedError("Function not implemented yet")



def jtCustomizations(part, doc, singleBodyOfPart):
    # People are going to want to have there own customization and may not want to share
    # I don't have a problem sharing my system, but it may not be for everyone.
    # If this code makes it into zolko's repo and you want to modify this, please reach out to me,
    # otherwise feel free to made your own function either in this file, if you want to share or..
    # point to another file that's not in th e ASM4 repo and exclude it from git.

    # Basic explanation of my file numbering system
    # Q-003-S_0-01.FCStd
    # Everything up to the first _ is the base partIDa
    # If a .FCstd contains more than one part It is appended with a :1
    # After the _ is the revision
    # Within the base part ID there is a project id in this instance Q
    # and incremental counter (TODO need to automated that eventually)
    # Also a sub classication.  Currently done manually
    # C is  file with multiple parts
    # S is a sub assembly
    # A is the major assembly in the sub folder
    file_name = os.path.basename(doc.FileName)
    elements = file_name.split('_')
    print (file_name)
    if len(elements) == 1:
        base_part_id = elements[0].split('.')[0]
        revision = 'None'
    else:
        base_part_id, revision_with_extension = elements
        revision = revision_with_extension.split('.')[0]
    part.FileName = file_name
    part.DrawingName = base_part_id
    part.DrawingRevision = revision

    print("Base Part ID:", base_part_id)
    print("Revision:", revision)

    # Todo in my business rules base_part_id should be the PartID unless there are multiple parts in the drawing.
    # in that case the base_part_id should be prepended by a :1 :2 .etc
    # As some point I'll build the logic to assign  validate that those numbers match the object  At this point I through an exception if the actual numbering looks weird
    # and throw an exception so the part number can be fixed.
    # note the part number in the base object not the assembly is the one that is used.
    #
    # Check if base_part_id is a substring of part.Label
    partIdtoAdd ="JT business rule violation"

    if part.Type == 'Assembly':
        partIdtoAdd = base_part_id
        # leave part Label alone that contains the assembly name.
        part.PartDescription = part.Label
    else:

        if base_part_id == part.Label:
           # this can happen where there is only one part in a file
           partIdtoAdd = part.Label
        else:
            if not(base_part_id in part.Label):
                print (f'base_part_id={base_part_id}')
                print (f'part.Label = {part.Label}')
                message =f"PartID:{part.Label}\n             is supposed to contain \n        {base_part_id} Please fix the part number."
                print (message)
                Asm4.warningBox(message)
            else:
                if not(':' in part.Label):
                    message= f"If PartID:{part.Label} is not = { base_part_id} is should contain a : separator    /nPlease fix the part number in the root folder for that part./n(JT Business rules"
                    print (message)
                    Asm4.warningBox(message)
                else:
                    # Subtract base_part_id and '.' from part.Label and check if the result is an unsigned integer
                    remaining_part = part.Label.replace(base_part_id + ":", "")
                    if not remaining_part.isdigit():
                        message =f"The remaining part of part.Label is not an unsigned integer. Please fix the part number in the root folder for that part."
                        print (message)
                        Asm4.warningBox(message)
                    else:
                        #if we code to here JT business rules on the part number where followed
                        partIdtoAdd = part.Label

        # todo need to deal with the situation where we have more than one part in a table.
        if singleBodyOfPart is not None:
            part.PartDescription = singleBodyOfPart.Label
        else:
            part.PartDescription ="Multi Body Part(Not implemented)"
    part.PartID = partIdtoAdd




'''
# Check if the configuration file exists
try:
    file = open(ConfUserFilejson, 'r')
    file.close()
except:
    partInfoDef = dict()
    for prop in partInfo:
        partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': True})
    for prop in partInfo_Invisible:
        partInfoDef.setdefault(prop, {'userData': prop, 'active': True, 'visible': False})
    try:
        os.mkdir(ConfUserDir)
    except:
        pass
    file = open(ConfUserFilejson, 'x')
    json.dump(partInfoDef, file)
    file.close()

# Load user's config file
file = open(ConfUserFilejson, 'r')
infoKeysUser = json.load(file).copy()
file.close()
'''

# DEPRECATED : moved to infoPartCmd
'''
def infoDefault(self):

    file = open(ConfUserFilejson, 'r')
    infoKeysUser = json.load(file).copy()
    file.close()

    try:
        self.TypeId
        part = self
    except AttributeError:
        part = self.part

    doc = part.Document

    for i in range(len(part.Group)):
        if part.Group[i].TypeId == 'PartDesign::Body':
            body = part.Group[i]
            for i in range(len(body.Group)):
                if body.Group[i].TypeId == 'PartDesign::Pad':
                    pad = body.Group[i]
                    try:
                        sketch = pad.Profile[0]
                    except NameError :
                        # print('There is no Sketch on a Pad of the Part', part.FullName)
                        pass

        try:
            LabelDoc(self, part, doc)
        except NameError:
            # print('LabelDoc: there is no Document on the Part ', part.FullName)
            pass

        try:
            LabelPart(self, part)
        except NameError:
            # print('LabelPart: Part does not exist')
            pass

        try:
            PadLength(self, part, pad)
        except NameError:
            # print('PadLenght: there is no Pad in the Part ', part.FullName)
            pass

        try:
            ShapeLength(self, part, sketch)
        except NameError:
            # print('ShapeLength: there is no Sketch in the Part ', part.FullName)
            pass

        try:
            ShapeVolume(self, part, body)
        except NameError:
            # print('ShapeVolume: there is no Shape in the Part ', part.FullName)
            pass
'''


"""
How to create a NEW_AUTOINFO_FIELD:

    Add the ref to the NEW_AUTOINFO_FIELD_NAME in partInfo[]
    Add the description in infoToolTip = {}
    Put the NEW_AUTOINFO_FIELD_NAME in infoDefault() at the end with the right arg (pad,sketch...)

    Create a new function like:

        def NEW_AUTOINFO_FIELD_NAME(self, part, (optional: doc , body , pad , sketch)):
            auto_info_field = infoKeysUser.get('NEW_AUTOINFO_FIELD_NAME').get('userData')
            auto_info_fill = NEW_AUTOINFO_FIELD_INFO
            try:
                # If the command comes from makeBom, write the info directly on Part
                self.TypeId
                setattr(part, auto_info_field, str(auto_info_fill))
            except AttributeError:
                # If the command comes from infoPartUI, write info on auto-filling field on UI
                try:
                    # If the field is active
                    for i in range(len(self.infoTable)):
                        if self.infoTable[i][0] == auto_info_field:
                            self.infos[i].setText(str(auto_info_fill))
                except AttributeError:
                    # If the field is not active
                    pass
"""

# DEPRECATED : moved to infoPartCmd
'''
def LabelDoc(self, part, doc):
    auto_info_field = infoKeysUser.get('Doc_Label').get('userData')
    auto_info_fill = doc.Label
    try:
        self.TypeId
        setattr(part, auto_info_field, auto_info_fill)
    except AttributeError:
        try:
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0] == auto_info_field:
                    self.infos[i].setText(auto_info_fill)
        except AttributeError:
            self.infos[i].setText("-")

InfoKeys
def LabelPart(self, part):
    auto_info_field = infoKeysUser.get('Part_Label').get('userData')
    auto_info_fill = part.Label
    try:
        self.TypeId
        setattr(part, auto_info_field, auto_info_fill)
    except AttributeError:
        try:
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0] == auto_info_field:
                    self.infos[i].setText(auto_info_fill)
        except AttributeError:
            self.infos[i].setText("-")


def PadLength(self, part, pad):
    auto_info_field = infoKeysUser.get('Pad_Length').get('userData')
    try:
        auto_info_fill = str(pad.Length).replace('mm','')
    except AttributeError:
        return
    try:
        self.TypeId
        setattr(part, auto_info_field, auto_info_fill)
    except AttributeError:
        try:
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0] == auto_info_field:
                    self.infos[i].setText(auto_info_fill)
        except AttributeError:
            self.infos[i].setText("-")


def ShapeLength(self, part, sketch):
    auto_info_field = infoKeysUser.get('Shape_Length').get('userData')
    try:
        auto_info_fill = str(sketch.Shape.Length)
    except AttributeError:
        return
    try:
        self.TypeId
        setattr(part, auto_info_field, auto_info_fill)
    except AttributeError:
        try:
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0] == auto_info_field:
                    self.infos[i].setText(auto_info_fill)
        except AttributeError:
            self.infos[i].setText("-")


def ShapeVolume(self, part, body):
    auto_info_field = infoKeysUser.get('Shape_Volume').get('userData')
    bbc = body.Shape.BoundBox
    auto_info_fill = str(str(round(bbc.ZLength, 3)) + str(' mm x ') + str(round(bbc.YLength, 3)) + str(' mm x ') + str(round(bbc.XLength, 3)) + str(' mm'))
    try:
        self.TypeId
        setattr(part, auto_info_field, auto_info_fill)
    except AttributeError:
        try:
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0] == auto_info_field:
                    self.infos[i].setText(auto_info_fill)
        except AttributeError:
            self.infos[i].setText("-")
'''


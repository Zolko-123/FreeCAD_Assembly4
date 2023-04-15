#!/usr/bin/env python3
# coding: utf-8
#
# LGPL

import os, json

import FreeCAD as App
# import infoPartCmd

partInfo = [
    'Document',
    'PartName',
    'Reference',
    'PartLength',
    'PartWidth',
    'PartVolume']

infoToolTip = {
    'Document':     'Document or File name',
    'PartName':     'Part Name',
    'Reference':    'Part Reference',
    'PartLength':   'Cut length of the raw material',
    'PartWidth':    'Width of the raw material',
    'PartVolume':   'Object dimensions (x, y, z)'}

partInfo_Invisible = [
    'FastenerDiameter',
    'FastenerLenght',
    'FastenerType']

infoToolTip_Invisible = {
    'FastenerDiameter': 'Fastener diameter',
    'FastenerLenght':   'Fastener length',
    'FastenerType':     'Fastener type'}

ConfUserDir = os.path.join(App.getUserAppDataDir(),'Templates')
ConfUserFilename = "Asm4_infoPartConf.json"
ConfUserFilejson = os.path.join(ConfUserDir, ConfUserFilename)


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


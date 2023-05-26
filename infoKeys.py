#!/usr/bin/env python3
# coding: utf-8
#
# LGPL

import os
import json

import FreeCAD as App

# Incremente this to rewrite the config file
file_version = "1.1"

# Body and Part
part_info = [
    'Doc_Label',
    'Type',
    'Part_Label',
    'Pad_Length',
    'Shape_Length',
    'Shape_Volume']

part_info_tooltip = {
    'Doc_Label':    'Document or Group label',
    'Type':         'Allows user to set Part as Fasterner (Fastener|Part|Subassembly)',
    'Part_Label':   'Part label',
    'Pad_Length':   'Pad length',
    'Shape_Length': 'Shape length',
    'Shape_Volume': 'Object dimensions (x, y, z)'}

# should be hidden
fastener_info = [
    'Fastener_Diameter',
    'Fastener_Length',
    'Fastener_Type',]

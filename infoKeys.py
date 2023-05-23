#!/usr/bin/env python3
# coding: utf-8
#
# LGPL

import os
import json

import FreeCAD as App

# Incremente this to rewrite the config file
# file_version = "1.0"

# Body and Part
part_info = [
    'Doc_Label',
    'Part_Label',
    'Pad_Length',
    'Shape_Length',
    'Shape_Volume']

part_info_tooltip = {
    'Doc_Label':    'Document or Group label',
    'Part_Label':   'Part label',
    'Pad_Length':   'Pad length',
    'Shape_Length': 'Shape length',
    'Shape_Volume': 'Object dimensions (x, y, z)'}

# should be hidden
hidden_part_info = [
    'Fastener_Diameter',
    'Fastener_Length',
    'Fastener_Type']

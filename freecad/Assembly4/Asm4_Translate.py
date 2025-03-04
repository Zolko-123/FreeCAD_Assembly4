#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
#
# Asm4_Translate.py


import FreeCAD as App


# dummy function for the QT translator
def QT_TRANSLATE_NOOP(context, text):
    return text


# use latest available translate function
if hasattr(App, "Qt"):
    translate = App.Qt.translate
else:
    print("Translations will not be available")
    

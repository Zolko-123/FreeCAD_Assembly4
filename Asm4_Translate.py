#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
#
# Asm4_Translate.py


import FreeCAD as App

def _atr(context: str, text: str) -> str:
    """Wrap strings which should be translated in in this function."""
    return App.Qt.translate(context, text)

# dummy function for the QT translator
def QT_TRANSLATE_NOOP(context, text):
    return text


# use latest available translate function
if hasattr(App, "Qt"):
    translate = App.Qt.translate
else:
    print("Translations will not be available")
    

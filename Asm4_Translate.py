#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
#
# Asm4_Translate.py


import FreeCAD as App
import os, Asm4_locator

Asm4_path = os.path.dirname( Asm4_locator.__file__ )
Asm4_icon = os.path.join( Asm4_path , 'Resources/icons' )
Asm4_trans = os.path.join(Asm4_path, "Resources/translations")

# dummy function for the QT translator
def QT_TRANSLATE_NOOP(context, text):
    return text


# use latest available translate function

def _atr(context: str, text: str) -> str:
    """Wrap strings which should be translated in in this function."""
    return App.Qt.translate(context, text)

if hasattr(App, "Qt"):
    translate = App.Qt.translate
else:
    print("Translations will not be available")
    

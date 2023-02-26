#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
#
# Asm4_Translate.py

import os
import FreeCADGui as Gui
import FreeCAD as App

Gui.addLanguagePath(os.path.join(os.path.dirname(__file__), "Resources/translations"))


def _atr(context: str, text: str) -> str:
    """Wrap strings which should be translated in in this function."""
    return App.Qt.translate(context, text)


def QT_TRANSLATE_NOOP(context: str, text: str) -> str:
    """NOP Marker Macro Alias for strings for which FreeCAD/Qt handles translations."""
    return text

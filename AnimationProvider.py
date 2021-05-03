# !/usr/bin/env python3
# coding: utf-8
#
# LGPL

# Interface definition to make reusing animationExporter
# straightforward outside asm4
#
# Created as part of the Asm4 wb

class animationProvider:
    #
    # Setup the scene for the next frame of the animation.
    # Set resetAnimation True for the first frame
    # Signals that the last frame has been reached by returning True
    #
    def nextFrame(self, resetAnimation) -> bool:
        raise NotImplementedError("animationProvider.nextFrame not implemented.")

    #
    # Optionally flag that pendulum (forth and back animation) is wanted.
    # Prevents the need to capture identical frames on the "returning path"
    # of the animation.
    #
    def pendulumWanted(self) -> bool:
        return False

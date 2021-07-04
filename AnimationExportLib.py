# !/usr/bin/env python3
# coding: utf-8
#
# LGPL

# Library to store animations as video/image
# Created as part of the Asm4 wb

import os, numpy

from PySide import QtGui, QtCore
from PIL import Image, ImageFilter
from PIL.ImageQt import ImageQt
import tempfile
import pathlib
import cv2

import FreeCADGui as Gui
import FreeCAD as App
import Asm4_libs as Asm4

from AnimationLib import animationProvider


"""
    +-----------------------------------------------+
    |               Animation Export                |
    | Provides ability to export the animation as   |
    | single frames, mp4 or animated gif.           |
    +-----------------------------------------------+
"""


class animationExporter():

    def __init__(self, animProvider: animationProvider):
        self.animProvider = animProvider

        self.imageList = None    # list of grabbed animation frames
        self.grabbedView = None  # single grabbed scene used for preview
        self.bgImage = None      # rendered background for compositing
        self.logo = None         # logo for compositing
        self.shadow = None       # shadow for compositing

        # Create the GUI and connect signals/slots
        self.expDiag = exportDialog(self)
        self.createGuiConnections()


    #
    # static image acquisition and manipulation functions
    #

    # grab a single shot from the active scene
    @staticmethod
    def getFrame(size=(1024, 768), mod='Current') -> Image.Image:
        tempDir = tempfile.TemporaryDirectory()
        fName = pathlib.Path(tempDir.name) / "temp.png"
        Gui.ActiveDocument.ActiveView.saveImage(str(fName), size[0], size[1], mod)
        img = Image.open(str(fName))
        if img.mode != 'RGBA':
            img.putalpha(255)
        img.load()
        return img


    # create a background for the animation based on the given image
    # and/or color
    @staticmethod
    def createBackground(size, bgColor, imgFilename=None) -> Image.Image:
        cmpImg = Image.new("RGBA", size, bgColor)
        if imgFilename and os.path.isfile(imgFilename):
            bgImg = Image.open(imgFilename)
            if bgImg.mode != 'RGBA':
                bgImg.putalpha(255)
            bgImg = bgImg.resize(size)
            cmpImg = Image.alpha_composite(cmpImg, bgImg)
        return cmpImg


    # create an artistic shadow from a grabbed 2d image with the given
    # tint and fuzziness ("dropshadow")
    @staticmethod
    def createShadow(img, shColor, blur, scale, offset, mode=Image.BICUBIC) -> Image.Image:
        # Create artistic drop shadow by coloring everything in the wanted shadow-color and
        # squashing the image to the lower half of the resulting frame
        shadowColored = Image.new("RGBA", img.size, shColor)
        transparent = Image.new("RGBA", img.size, (0, 0, 0, 0))

        shadow = transparent.copy()
        shadow.paste(shadowColored, (0, 0), img)
        shSize = (int(img.size[0] * scale[0]), int(img.size[1] * scale[1]))
        shadow = shadow.resize(shSize, mode)
        blurred = shadow.filter(ImageFilter.GaussianBlur(blur))
        shadow = transparent.copy()
        absOffset = (int(offset[0] * img.size[0]), int(offset[1] * img.size[1]))
        shadow.paste(blurred, absOffset, blurred)

        return shadow

    # renders a logo-image to composite at the given position
    @staticmethod
    def createLogo(imgFilename, frameSize, scale=(1, 1), position=(0, 0), mode=Image.BICUBIC) -> Image.Image:
        cmpImg = Image.new("RGBA", frameSize, (0, 0, 0, 0))
        if imgFilename and os.path.isfile(imgFilename):
            logo = Image.open(imgFilename)
            if logo.mode != 'RGBA':
                logo.putalpha(255)
            logoSize = (int(logo.size[0] * scale[0]), int(logo.size[1] * scale[1]))
            logo = logo.resize(logoSize, mode)
            pPos = (int(position[0] * (frameSize[0]-logoSize[0])), int(position[1] * (frameSize[1]-logoSize[1])))
            cmpImg.paste(logo, pPos, logo)
        return cmpImg


    # Clean up alpha channel of the given image. FCs export puts alpha based on the topmost object, i.e.
    # image will not be fully opaque even when a non-transparent object is shown behind a transparent one.
    @staticmethod
    def alphaSanitize(img) -> Image.Image:
        imgBands = img.split()
        newAlpha = imgBands[3].point(lambda i: 0 if i == 0 else 255)
        imgBands[3].paste(newAlpha)
        img = Image.merge(img.mode, imgBands)
        return img


    #
    # instance bound image acquisition and exporting functions
    #

    # render and grab all frames as per the animation configuration
    def grabFrames(self, size=(1024, 768), mod='Current'):
        frames = []
        firstFrame = True
        endOfCycle = False
        while not endOfCycle:
            endOfCycle = self.animProvider.nextFrame(firstFrame)
            firstFrame = False
            Gui.updateGui()
            frame = animationExporter.getFrame(size, mod)
            frames.append(frame)

        self.imageList = frames


    # export all frames to animated gif
    def writeGif(self, filename):
        # append reversed list if pendulum is wanted
        if self.animProvider.pendulumWanted():
            self.imageList.extend(list(reversed(self.imageList)))

        # Use dithering for all frames
        for i, img in enumerate(self.imageList):
            tmp = img.convert(mode='P', palette=Image.ADAPTIVE, colors=256)
            img = img.convert('RGB')
            self.imageList[i] = img.quantize(256, Image.FASTOCTREE, 0, tmp, Image.FLOYDSTEINBERG)

        # export as animated gif
        loops = self.expDiag.sbOutLoops.value()
        frameMSec = int(1000/self.expDiag.sbOutFPS.value())
        self.imageList[0].save(filename, save_all=True, append_images=self.imageList[1:], optimize=True, duration=frameMSec, loop=loops)


    # export an mp4 from the rendered framed
    def writeVideo(self, filename):
        # append reversed list if pendulum is wanted
        if self.animProvider.pendulumWanted():
            self.imageList.extend(list(reversed(self.imageList)))

        # Grab the stats from image1 to use for the resultant video
        height, width, layers = numpy.array(self.imageList[0]).shape

        # create video
        fps = self.expDiag.sbOutFPS.value()
        loops = self.expDiag.sbOutLoops.value()
        fourccs = ['mp4v', 'avc1', 'X264', 'XVID']
        # codec = -1  # auto/select
        exported = False
        for fcc in fourccs:
            codec = cv2.VideoWriter_fourcc(*fcc)
            video = cv2.VideoWriter(filename, codec, fps, (width, height))

            for i in range(0, loops):
                for img in self.imageList:
                    img = img.convert('RGB')
                    video.write(cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2BGR))

            # write file
            video.release()
            if os.path.getsize(filename) > 0:
                exported = True
                break
        if not exported:
            App.Console.PrintError("Export failed for \"" + filename + "\". Using another container type can help.\n")

    # export each grabbed frame to a separate image
    def writeFrames(self, filename):
        # export frame by frame
        for i, img in enumerate(self.imageList):
            number = "{:04}".format(i)
            fname = filename[:-4] + number + filename[-4:]
            img.save(fname)


    # alpha composite all precalculated images
    def compositStack(self, outputSize, frameImg=None, shadowImg=None):
        # composite the final image from full-size bg-colored image, shadow, original (alpha-cleaned) image, etc
        frame = frameImg if frameImg else self.grabbedView

        cmpImg = self.bgImage if self.bgImage else Image.new("RGBA", frame.size, (0, 0, 0, 0))

        shadow = shadowImg if shadowImg else self.shadow
        if shadow:
            cmpImg = Image.alpha_composite(cmpImg, shadow)

        cmpImg = Image.alpha_composite(cmpImg, frame)

        if self.logo:
            cmpImg = Image.alpha_composite(cmpImg, self.logo)

        cmpImg = cmpImg.resize(outputSize, Image.BICUBIC)

        return cmpImg



    # progress dialog creation helper
    def createProgressDlg(self):
        pDlg = QtGui.QProgressDialog("Capturing and Exporting...", "Cancel", 0, 100)
        pDlg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        pDlg.setModal(True)
        pDlg.setMinimumDuration(1)
        pDlg.setValue(0)
        pDlg.setValue(1)
        return pDlg


    # the main working function
    # grabs all the frames as per the current animation configuration
    def exportAnimation(self):
        # get selected filename, pop up dialog if none selected yet
        fname = self.expDiag.outputFileSel.filename()
        if not fname:
            fname = self.expDiag.outputFileSel.selectFile()

        # pop up progress dialog...
        pDlg = self.createProgressDlg()
        # ... and grab frames (no progress in the dialog so far, the animation windows slider updates, tho
        gSize = self.getGrabSize()
        mode = "Transparent" if self.bgImage else "Current"
        self.grabFrames(gSize, mode)
        rSize = self.getResultSize()

        if pDlg.wasCanceled():
            return

        # do calculations for all grabbed frames
        pDlg.setMaximum(len(self.imageList)+5)
        for i, img in enumerate(self.imageList):
            img = self.alphaSanitize(img)
            shadow = self.shadowFromInputFields(img)
            self.imageList[i] = self.compositStack(rSize, img, shadow)
            pDlg.setValue(i+1)
            if pDlg.wasCanceled():
                return

        # export to the chosen filename, deduce format based in name
        if fname.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
            self.writeVideo(fname)
        elif fname.lower().endswith(".gif"):
            self.writeGif(fname)
        elif fname.lower().endswith(".png"):
            self.writeFrames(fname)
        pDlg.setValue(pDlg.maximum())


    #
    # GUI-bound image/layer calculations
    #

    # calculate a new preview based on selected values
    # make sure to force update other layers, if needed
    def updatePreview(self):
        gSize = self.getGrabSize()
        # check for size-change
        sizeChanged = (not self.grabbedView) or (self.grabbedView.size != gSize)
        mode = "Transparent" if self.bgImage else "Current"
        self.grabbedView = self.getFrame(gSize, mode)
        self.grabbedView = animationExporter.alphaSanitize(self.grabbedView)

        self.updateShadow()

        if sizeChanged:
            # Will have to recalc logo etc.
            self.updateBackground()
            self.updateLogo()


    # calculate a new background image layer
    # make sure to force update other layers, if needed
    def updateBackground(self):
        useBg = self.expDiag.gpbBG.isChecked()
        if not useBg:
            self.bgImage = None
            self.updatePreview()
        else:
            needNewGrab = not self.bgImage
            gSize = self.getGrabSize()
            fname = self.expDiag.bgImgFileSel.filename()
            color = self.expDiag.bgColorSel.color()
            self.bgImage = self.createBackground(gSize, color, fname)
            # also grab a new frame to ensure transparency, when bg is first selected.
            if needNewGrab:
                self.updatePreview()

        #self.expDiag.gpbShadow.setChecked(useBg and self.expDiag.gpbShadow.isChecked())
        #self.expDiag.gpbShadow.setEnabled(useBg)


    # calculate a new shadow layer
    def shadowFromInputFields(self, img):
        useShadow = False # self.expDiag.gpbShadow.isChecked()
        if useShadow:
            color = self.expDiag.shadowColSel.color()
            scale = (self.expDiag.sbShadowWidth.value() / 100.0, self.expDiag.sbShadowHeight.value() / 100.0)
            offset = (self.expDiag.sbShadowX.value() / 100.0, self.expDiag.sbShadowY.value() / 100.0)
            blur = self.expDiag.sbShadowBlur.value()
            return self.createShadow(img, color, blur, scale, offset)
        else:
            return None


    # calculate a new logo overlay layer
    def updateLogo(self):
        fname = self.expDiag.logoFileSel.filename()
        scale = (self.expDiag.sbLogoWidth.value()/100.0, self.expDiag.sbLogoHeight.value()/100.0)
        offset = (self.expDiag.sbLogoX.value()/100.0, self.expDiag.sbLogoY.value()/100.0)
        self.logo = self.createLogo(fname, self.grabbedView.size, scale, offset) if fname else None


    #
    # Minor Gui based helpers and slots
    #

    def getResultSize(self):
        w = self.expDiag.sbOutWidth.value()
        h = self.expDiag.sbOutHeight.value()
        return (w, h)

    def getGrabSize(self):
        s = self.getResultSize()
        sFac = self.expDiag.sbSmoothFactor.value() + 1
        return (s[0] * sFac, s[1] * sFac)


    def onUpdatePreview(self):
        self.updatePreview()
        self.compositAndPreview()


    def onUpdateBackground(self):
        self.updateBackground()
        self.compositAndPreview()


    def updateShadow(self):
        self.shadow = self.shadowFromInputFields(self.grabbedView)


    def onUpdateShadow(self):
        self.updateShadow()
        self.compositAndPreview()


    def onUpdateLogo(self):
        self.updateLogo()
        self.compositAndPreview()


    def compositAndPreview(self):
        rSize = self.getResultSize()
        img = self.compositStack(rSize)
        scale = self.expDiag.sbPreviewScale.value()/100.0
        self.expDiag.setImage(img, scale)


    def openUI(self):
        self.onUpdatePreview()
        self.expDiag.show()


    def onClose(self):
        self.expDiag.setImage(None)
        self.imageList = []


    #
    # Signal/Slot-Connections for the Dialog
    #

    def createGuiConnections(self):
        self.expDiag.sbPreviewScale.valueChanged.connect(self.onUpdatePreview)
        self.expDiag.pbRefreshPreview.clicked.connect(self.onUpdatePreview)
        self.expDiag.sbOutWidth.valueChanged.connect(self.onUpdatePreview)
        self.expDiag.sbOutHeight.valueChanged.connect(self.onUpdatePreview)
        self.expDiag.sbSmoothFactor.valueChanged.connect(self.onUpdatePreview)

        self.expDiag.gpbBG.toggled.connect(self.onUpdateBackground)
        self.expDiag.bgImgFileSel.fileChanged.connect(self.onUpdateBackground)
        self.expDiag.bgColorSel.colorChanged.connect(self.onUpdateBackground)

        #self.expDiag.gpbShadow.toggled.connect(self.onUpdateShadow)
        #self.expDiag.shadowColSel.colorChanged.connect(self.onUpdateShadow)
        #self.expDiag.sbShadowX.valueChanged.connect(self.onUpdateShadow)
        #self.expDiag.sbShadowY.valueChanged.connect(self.onUpdateShadow)
        #self.expDiag.sbShadowWidth.valueChanged.connect(self.onUpdateShadow)
        #self.expDiag.sbShadowHeight.valueChanged.connect(self.onUpdateShadow)
        #self.expDiag.sbShadowBlur.valueChanged.connect(self.onUpdateShadow)

        self.expDiag.gpbLogo.toggled.connect(self.onUpdateLogo)
        self.expDiag.logoFileSel.fileChanged.connect(self.onUpdateLogo)
        self.expDiag.sbLogoX.valueChanged.connect(self.onUpdateLogo)
        self.expDiag.sbLogoY.valueChanged.connect(self.onUpdateLogo)
        self.expDiag.sbLogoWidth.valueChanged.connect(self.onUpdateLogo)
        self.expDiag.sbLogoHeight.valueChanged.connect(self.onUpdateLogo)

        self.expDiag.pbCreateAndSave.clicked.connect(self.exportAnimation)

        self.expDiag.pbClose.clicked.connect(self.expDiag.close)



"""
    +-----------------------------------------------+
    |               Export Dialog UI                |
    +-----------------------------------------------+
"""

class exportDialog(QtGui.QDialog):
    def __init__(self, owner: animationExporter, parentWidget=None):
        super().__init__(parentWidget)

        self.owner = owner
        self.pilImage = None

        # The Gui-related things
        # self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Animation Export Preview')
        self.setWindowIcon(QtGui.QIcon(os.path.join(Asm4.iconPath, 'FreeCad.svg')))
        self.setMinimumWidth(640)
        self.setMinimumHeight(480)
        self.setModal(False)

        # add and layout widgets
        # upper part
        self.gpbPreview = QtGui.QGroupBox("Preview", self)
        self.lblPreview = QtGui.QLabel('TheImageLabel', self.gpbPreview)
        self.sbPreviewScale = QtGui.QSpinBox()
        self.sbPreviewScale.setRange(1, 100)
        self.sbPreviewScale.setValue(70)
        self.sbPreviewScale.setSuffix('%')
        self.sbPreviewScale.setKeyboardTracking(False)

        self.prevHL = QtGui.QHBoxLayout()
        self.prevHL.addStretch()
        self.prevHL.addWidget(QtGui.QLabel("Preview Scale:"))
        self.prevHL.addWidget(self.sbPreviewScale)

        self.prevVL = QtGui.QVBoxLayout()
        self.prevVL.addStretch()
        self.prevVL.addWidget(self.lblPreview)
        self.prevVL.addStretch()
        self.prevVL.addLayout(self.prevHL)
        self.gpbPreview.setLayout(self.prevVL)

        # # # Output Group Box # # #
        self.outputVLayout = QtGui.QVBoxLayout()
        self.gpbOutput = QtGui.QGroupBox("Output", self)
        self.outputFileSel = fileSelectorWidget("save", self.gpbOutput)

        self.sbOutWidth = QtGui.QSpinBox()
        self.sbOutWidth.setRange(1, 9999)
        self.sbOutWidth.setValue(1280)
        self.sbOutWidth.setKeyboardTracking(False)
        self.sbOutHeight = QtGui.QSpinBox()
        self.sbOutHeight.setRange(1, 9999)
        self.sbOutHeight.setValue(720)
        self.sbOutHeight.setKeyboardTracking(False)

        self.sbOutFPS = QtGui.QSpinBox()
        self.sbOutFPS.setRange(1, 999)
        self.sbOutFPS.setValue(10)
        self.sbOutLoops = QtGui.QSpinBox()
        self.sbOutLoops.setRange(1, 999)
        self.sbOutLoops.setValue(1)

        self.sbSmoothFactor = QtGui.QSpinBox()
        self.sbSmoothFactor.setRange(0, 3)
        self.sbSmoothFactor.setValue(0)
        self.sbSmoothFactor.setKeyboardTracking(False)

        self.outputVLayout.addWidget(self.outputFileSel)

        self.outputHL2 = QtGui.QHBoxLayout()
        self.outputHL2.addWidget(QtGui.QLabel("Width:"))
        self.outputHL2.addWidget(self.sbOutWidth)
        self.outputHL2.addWidget(QtGui.QLabel("Height:"))
        self.outputHL2.addWidget(self.sbOutHeight)
        self.outputVLayout.addLayout(self.outputHL2)

        self.outputHL3 = QtGui.QHBoxLayout()
        self.outputHL3.addWidget(QtGui.QLabel("FPS:"))
        self.outputHL3.addWidget(self.sbOutFPS)
        self.outputHL3.addWidget(QtGui.QLabel("Loops:"))
        self.outputHL3.addWidget(self.sbOutLoops)
        self.outputVLayout.addLayout(self.outputHL3)

        self.outputHL4 = QtGui.QHBoxLayout()
        self.outputHL4.addWidget(QtGui.QLabel("Smoothen:"))
        self.outputHL4.addWidget(self.sbSmoothFactor)
        self.outputVLayout.addLayout(self.outputHL4)

        self.gpbOutput.setLayout(self.outputVLayout)

        # # # Background Group Box # # #
        self.gpbBG = QtGui.QGroupBox("Background", self)
        self.gpbBG.setCheckable(True)
        self.gpbBG.setChecked(False)
        self.bgImgFileSel = fileSelectorWidget("read", self.gpbBG)
        self.bgColorSel = colorSelectorWidget((255, 255, 255, 255), self.gpbBG)

        self.bgVLayout = QtGui.QVBoxLayout()
        self.bgVLayout.addWidget(self.bgImgFileSel)
        self.bgVLayout.addWidget(self.bgColorSel)

        self.gpbBG.setLayout(self.bgVLayout)

        # # # Shadow Group Box # # #
        '''
        self.gpbShadow = QtGui.QGroupBox("shadow", self)
        self.gpbShadow.setCheckable(True)
        self.gpbShadow.setChecked(False)
        self.shadowColSel = colorSelectorWidget((0, 0, 0, 150), self.gpbShadow)

        self.sbShadowWidth = QtGui.QSpinBox()
        self.sbShadowWidth.setRange(1, 100)
        self.sbShadowWidth.setValue(100)
        self.sbShadowWidth.setKeyboardTracking(False)
        self.sbShadowWidth.setSuffix("%")
        self.sbShadowHeight = QtGui.QSpinBox()
        self.sbShadowHeight.setRange(1, 100)
        self.sbShadowHeight.setValue(50)
        self.sbShadowHeight.setKeyboardTracking(False)
        self.sbShadowHeight.setSuffix("%")

        self.sbShadowX = QtGui.QSpinBox()
        self.sbShadowX.setRange(0, 100)
        self.sbShadowX.setValue(0)
        self.sbShadowX.setKeyboardTracking(False)
        self.sbShadowX.setSuffix("%")
        self.sbShadowY = QtGui.QSpinBox()
        self.sbShadowY.setRange(0, 100)
        self.sbShadowY.setValue(50)
        self.sbShadowY.setKeyboardTracking(False)
        self.sbShadowY.setSuffix("%")

        self.sbShadowBlur = QtGui.QSpinBox()
        self.sbShadowBlur.setRange(0, 1000)
        self.sbShadowBlur.setValue(20)
        self.sbShadowBlur.setKeyboardTracking(False)

        self.shadowVLayout = QtGui.QVBoxLayout()
        self.shadowVLayout.addWidget(self.shadowColSel)

        self.shadowHL2 = QtGui.QHBoxLayout()
        self.shadowHL2.addWidget(QtGui.QLabel("Width:"))
        self.shadowHL2.addWidget(self.sbShadowWidth)
        self.shadowHL2.addWidget(QtGui.QLabel("Height:"))
        self.shadowHL2.addWidget(self.sbShadowHeight)
        self.shadowVLayout.addLayout(self.shadowHL2)

        self.shadowHL3 = QtGui.QHBoxLayout()
        self.shadowHL3.addWidget(QtGui.QLabel("X-Offset:"))
        self.shadowHL3.addWidget(self.sbShadowX)
        self.shadowHL3.addWidget(QtGui.QLabel("Y-Offset:"))
        self.shadowHL3.addWidget(self.sbShadowY)
        self.shadowVLayout.addLayout(self.shadowHL3)

        self.shadowHL4 = QtGui.QHBoxLayout()
        self.shadowHL4.addStretch(7)
        self.shadowHL4.addWidget(QtGui.QLabel("Blur:"), 3)
        self.shadowHL4.addWidget(self.sbShadowBlur, 3)
        self.shadowVLayout.addLayout(self.shadowHL4)

        self.gpbShadow.setLayout(self.shadowVLayout)
        '''

         # # # Logo Group Box # # #
        self.gpbLogo = QtGui.QGroupBox("Logo", self)
        self.logoFileSel = fileSelectorWidget("read", self.gpbLogo)
        self.logoFileSel.setFile(os.path.join(Asm4.iconPath, 'FreeCad.png'))

        self.sbLogoWidth = QtGui.QSpinBox()
        self.sbLogoWidth.setRange(1, 500)
        self.sbLogoWidth.setValue(50)
        self.sbLogoWidth.setKeyboardTracking(False)
        self.sbLogoWidth.setSuffix("%")
        self.sbLogoHeight = QtGui.QSpinBox()
        self.sbLogoHeight.setRange(1, 500)
        self.sbLogoHeight.setValue(50)
        self.sbLogoHeight.setKeyboardTracking(False)
        self.sbLogoHeight.setSuffix("%")

        self.sbLogoX = QtGui.QSpinBox()
        self.sbLogoX.setRange(0, 100)
        self.sbLogoX.setValue(97)
        self.sbLogoX.setKeyboardTracking(False)
        self.sbLogoX.setSuffix("%")
        self.sbLogoY = QtGui.QSpinBox()
        self.sbLogoY.setRange(0, 100)
        self.sbLogoY.setValue(95)
        self.sbLogoY.setKeyboardTracking(False)
        self.sbLogoY.setSuffix("%")

        self.LogoVLayout = QtGui.QVBoxLayout()
        self.LogoVLayout.addWidget(self.logoFileSel)

        self.LogoHL2 = QtGui.QHBoxLayout()
        self.LogoHL2.addWidget(QtGui.QLabel("Width:"))
        self.LogoHL2.addWidget(self.sbLogoWidth)
        self.LogoHL2.addWidget(QtGui.QLabel("Height:"))
        self.LogoHL2.addWidget(self.sbLogoHeight)
        self.LogoVLayout.addLayout(self.LogoHL2)

        self.LogoHL3 = QtGui.QHBoxLayout()
        self.LogoHL3.addWidget(QtGui.QLabel("X-Offset:"))
        self.LogoHL3.addWidget(self.sbLogoX)
        self.LogoHL3.addWidget(QtGui.QLabel("Y-Offset:"))
        self.LogoHL3.addWidget(self.sbLogoY)
        self.LogoVLayout.addLayout(self.LogoHL3)

        self.gpbLogo.setLayout(self.LogoVLayout)


    # # # RH Side Groupbox-Layout # # #
        self.upperRHVLayout = QtGui.QVBoxLayout()
        self.upperRHVLayout.addWidget(self.gpbOutput)
        self.upperRHVLayout.addWidget(self.gpbBG)
        #self.upperRHVLayout.addWidget(self.gpbShadow)
        self.upperRHVLayout.addWidget(self.gpbLogo)
        self.upperRHVLayout.addStretch()

        self.upperHLayout = QtGui.QHBoxLayout()
        self.upperHLayout.addWidget(self.gpbPreview)
        self.upperHLayout.addLayout(self.upperRHVLayout)

    # # # buttons incl. lower layout # # #
        self.pbClose = QtGui.QPushButton("Close")
        self.pbRefreshPreview = QtGui.QPushButton("Refresh Preview")
        self.pbCreateAndSave = QtGui.QPushButton("Create and Save")
        self.pbDummy = QtGui.QPushButton("Dummy")
        self.pbDummy.setDefault(True)
        self.pbDummy.setVisible(False)


        self.lowerButtonHLayout = QtGui.QHBoxLayout()
        self.lowerButtonHLayout.addWidget(self.pbClose)
        self.lowerButtonHLayout.addWidget(self.pbRefreshPreview)
        self.lowerButtonHLayout.addWidget(self.pbCreateAndSave)
        self.lowerButtonHLayout.addWidget(self.pbDummy)

        # Construct the overall layout
        self.mainVLayout = QtGui.QVBoxLayout()
        self.mainVLayout.addLayout(self.upperHLayout)
        self.mainVLayout.addLayout(self.lowerButtonHLayout)
        self.setLayout(self.mainVLayout)



    # update the main qlabel with the supplied image to preview rendering
    def setImage(self, img: Image.Image, scale=1.0):
        size = ( int(img.size[0]*scale), int(img.size[1]*scale) ) if img else None
        self.pilImage = img.resize(size, Image.BICUBIC) if img else None
        qtImg = ImageQt(self.pilImage) if img else ImageQt(Image.new("RGBA", (1, 1)))
        qtPix = QtGui.QPixmap.fromImage(qtImg)

        self.lblPreview.setPixmap(qtPix)
        if self.pilImage:
            self.__adjust()
            # get around Qt's resizing problem by making it resize from the eventloop again...
            QtCore.QTimer.singleShot(100, self.__adjust)

    def __adjust(self):
        self.lblPreview.setMinimumSize(self.pilImage.size[0], self.pilImage.size[1])
        self.lblPreview.adjustSize()
        self.adjustSize()


    # grab the close-event and ensure cleanup
    def closeEvent(self, evnt):
        self.owner.onClose()
        super().closeEvent(evnt)


"""
    +-----------------------------------------------+
    |               Custom FileSelector             |
    | Compound Widget including label, lineedit to  |
    | display filename and button to call the       |
    | file--dialog.                                 |
    +-----------------------------------------------+
"""

class fileSelectorWidget(QtGui.QWidget):

    fileChanged = QtCore.Signal()

    def __init__(self, type="read", parent=None):
        super().__init__(parent)

        self.label = QtGui.QLabel("File:", parent)
        self.leFilename = QtGui.QLineEdit(parent)
        self.pbSelectFile = QtGui.QPushButton("Select", parent)
        self.pbSelectFile.resize(50, self.pbSelectFile.height())
        self.pbSelectFile.setFixedWidth(50)

        self.lowerButtonHLayout = QtGui.QHBoxLayout()
        self.lowerButtonHLayout.addWidget(self.label)
        self.lowerButtonHLayout.addWidget(self.leFilename)
        self.lowerButtonHLayout.addWidget(self.pbSelectFile)
        self.setLayout(self.lowerButtonHLayout)

        self.type = type
        self.title = "Select File"
        self.filter = "Image Files (*.png *.jpg *.jpeg *.gif)" if self.type=="read" else "Supported Files (*.mp4 *.avi *.mov *.mkv *.gif *.png)"

        self.pbSelectFile.clicked.connect(self.selectFile)

    # Call the OS-fileselector and record selected file
    def selectFile(self):
        file = QtGui.QFileDialog.getOpenFileName(self, self.title, '', self.filter) if self.type=="read" else QtGui.QFileDialog.getSaveFileName(self, self.title, '', self.filter)
        return self.setFile(file[0])

    # Set the currently selected file
    def setFile(self, fName):
        self.leFilename.setText(fName)
        self.fileChanged.emit()
        return self.filename()

    # Return the filename or None, if empty
    def filename(self):
        ret = None
        if self.leFilename.text() != "":
            ret = self.leFilename.text()
        return ret



"""
    +-----------------------------------------------+
    |               Custom ColorSelector            |
    | Compound Widget including label, lineedit to  |
    | display color-code and button to call the     |
    | color-dialog.                                 |
    +-----------------------------------------------+
"""

class colorSelectorWidget(QtGui.QWidget):

    colorChanged = QtCore.Signal()

    def __init__(self, initialColor=(255, 255, 255, 255), parent=None):
        super().__init__(parent)

        self.label = QtGui.QLabel("Color:", parent)
        self.leColor = QtGui.QLineEdit(parent)
        self.leColor.setReadOnly(True)
        self.pbSelect = QtGui.QPushButton("Select", parent)
        self.pbSelect.resize(50, self.pbSelect.height())
        self.pbSelect.setFixedWidth(50)

        self.lowerButtonHLayout = QtGui.QHBoxLayout()
        self.lowerButtonHLayout.addWidget(self.label)
        self.lowerButtonHLayout.addWidget(self.leColor)
        self.lowerButtonHLayout.addWidget(self.pbSelect)
        self.setLayout(self.lowerButtonHLayout)

        self.selectedColor = self.setColor(initialColor)

        self.pbSelect.clicked.connect(self.selectColor)


    def selectColor(self):
        c = self.selectedColor
        color = QtGui.QColorDialog.getColor(initial=QtGui.QColor(c[0], c[1], c[2], c[3]), options=QtGui.QColorDialog.ShowAlphaChannel)
        return self.setColor(color.getRgb())

    def setColor(self, color):
        self.selectedColor = color
        self.leColor.setText(colorSelectorWidget.rgb2hex(self.selectedColor))
        self.__updateBtnColor()
        self.colorChanged.emit()
        return self.color()

    def color(self):
        return self.selectedColor

    def __updateBtnColor(self):
        c = self.selectedColor
        ci = (255 - c[0], 255 - c[1], 255 - c[2], 255)
        bgColStr = "rgb(" + str(c[0]) + "," + str(c[1]) + "," + str(c[2]) + ")"
        fgColStr = "rgb(" + str(ci[0]) + "," + str(ci[1]) + "," + str(ci[2]) + ")"
        style = "background-color: " + bgColStr + "; color: " + fgColStr + ";"
        self.pbSelect.setStyleSheet(style)

    @staticmethod
    def rgb2hex(color):
        return "#{:02x}{:02x}{:02x}{:02x}".format(color[0], color[1], color[2], color[3])


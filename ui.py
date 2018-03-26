import os
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from vendor.Qt import QtWidgets, QtCompat, QtCore
import AutoRig

def setupUi(uifile, base_instance=None):
    ui = QtCompat.loadUi(uifile)
    if not base_instance:
        return ui
    else:
        for member in dir(ui):
            if not member.startswith('__') and member is not 'staticMetaObject':
                setattr(base_instance, member, getattr(ui, member))
        return ui


class MrWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    def __init__(self):
        super(MrWindow, self).__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        mayaVersion = cmds.about(version = True)
        self.base_instance = setupUi(os.path.expanduser("~/maya/%s/scripts/MagicRig/window.ui" % mayaVersion), self)
        
        # connecting ui elements to functions
        # start page
        self.newRigBipBtn.clicked.connect(self.newRigBipFunc)
        self.newRigQipBtn.clicked.connect(self.newRigQipFunc)
        self.newRigCusBtn.clicked.connect(self.newRigCusFunc)
        # biped page
        self.charNameBox.textChanged.connect(self.charNameFunc)

        self.spineJointNumBox.valueChanged.connect(self.placeHolder)
        self.fingerNumBox.valueChanged.connect(self.placeHolder)
        self.toesNumBox.valueChanged.connect(self.placeHolder)

        self.footLockBox.stateChanged.connect(self.placeHolder)
        self.hipRollBox.stateChanged.connect(self.placeHolder)
        self.armRollBox.stateChanged.connect(self.placeHolder)
        self.fingerDblBox.stateChanged.connect(self.placeHolder)

        self.rigScaleBox.valueChanged.connect(lambda: AutoRig.scaleProxy())

        self.mirrorLeftBtn.clicked.connect(lambda: AutoRig.mirrorProxy("R"))
        self.resetBtn.clicked.connect(lambda: AutoRig.resetProxy())
        self.mirroRightBtn.clicked.connect(lambda: AutoRig.mirrorProxy("L"))
        self.createProxyBtn.clicked.connect(lambda: AutoRig.makeProxyBiped())
        
        self.createRigBtn.clicked.connect(lambda: AutoRig.makeSkeletonBiped())

        self.skinningBtn.clicked.connect(self.skinMenu)
        # quadruped page

        # custompage

    def charNameFunc(self):
        '''replace spaces with underscores'''
        text = self.charNameBox.text()
        newText = text.replace(" ", "_")
        self.charNameBox.setText(newText)
        AutoRig.prefix = newText
        cmds.setAttr("MR_Root.prefix", text, type="string")
        

    def newRigBipFunc(self):
        self.stackedWidget.setCurrentIndex(2)

    
    def newRigQipFunc(self):
        self.stackedWidget.setCurrentIndex(1)


    def newRigCusFunc(self):
        self.stackedWidget.setCurrentIndex(3)


    def goToStartFunc(self):
        self.stackedWidget.setCurrentIndex(0)


    def placeHolder(self):
        print("I need programming!")


    def skinMenu(self):
        cmds.SmoothBindSkinOptions()


if cmds.window("mrWindowWorkspaceControl", exists=True):
    cmds.deleteUI("mrWindowWorkspaceControl")
    #window.setparent(None)
    #window.deletelater()


window = MrWindow()
window.setDockableParameters(dockable=True, floating=True)
window.show()
window.raise_() # Move UI to front

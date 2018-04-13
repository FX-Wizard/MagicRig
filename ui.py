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
        ### start page ###
        self.newRigBipBtn.clicked.connect(lambda: self.changePage(2))
        self.newRigQipBtn.clicked.connect(lambda: self.changePage(1))
        self.newRigCusBtn.clicked.connect(lambda: self.changePage(3))
        ### biped page ###
        self.backBtn.clicked.connect(lambda: self.changePage(0))

        self.charNameBox.textChanged.connect(self.charNameFunc)

        #self.spineJointNumBox.valueChanged.connect(self.placeHolder)
        self.fingerNumBox.valueChanged.connect(self.fingerNumChanged)
        self.toesNumBox.valueChanged.connect(self.toesNumChanged)

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
        ### quadruped page ###
        self.qBackBtn.clicked.connect(lambda: self.changePage(0))

        self.qCharNameBox.textChanged.connect(self.qCharNameFunc)

        self.createProxyQBtn.clicked.connect(lambda: AutoRig.makeProxyQuad())

        self.qRigScaleBox.valueChanged.connect(lambda: AutoRig.scaleProxy())

        self.createRigQBtn.clicked.connect(lambda: AutoRig.makeSkeletonQuad())

        self.qSkinningBtn.clicked.connect(self.skinMenu)
        
        ### custompage ###
        self.cBackBtn.clicked.connect(lambda: self.changePage(0))
        #self.charNameBox.textChanged.connect(self.charNameFunc)

        self.cSkinningBtn.clicked.connect(self.skinMenu)

    def charNameFunc(self):
        '''replace spaces with underscores'''
        text = self.charNameBox.text()
        newText = text.replace(" ", "_")
        self.charNameBox.setText(newText)
        AutoRig.prefix = newText
        cmds.setAttr("MR_Root.prefix", newText, type="string")


    def qCharNameFunc(self):
        '''replace spaces with underscores'''
        text = self.qCharNameBox.text()
        newText = text.replace(" ", "_")
        self.qCharNameBox.setText(newText)
        AutoRig.prefix = newText
        cmds.setAttr("MR_Root.prefix", newText, type="string")

    
    def spineNumChanged(self):
        pass


    def fingerNumChanged(self):
        pass
        # get num existing fingers from node
        # add new fingers
        # update node


    def toesNumChanged(self):
        pass


    def changePage(self, index):
        self.stackedWidget.setCurrentIndex(index)


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

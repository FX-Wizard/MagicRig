import os, sys
import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore
from PySide2.QtUiTools import QUiLoader
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import time

from MagicRig import AutoRig

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class MrWindow(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(MrWindow, self).__init__(parent)
        # load UI file
        ui_file_name = os.environ['MAYA_APP_DIR'] + '/2022/scripts/MagicRig/window.ui'
        ui_file = QtCore.QFile(ui_file_name)
        #ui_file.open(QtCore.QFile.ReadOnly)
        if not ui_file.open(QtCore.QIODevice.ReadOnly):
            print(f'Cannot open {ui_file_name}: {ui_file.errorString()}')
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        if not self.window:
            print(loader.errorString())
        self.window.show()

        # self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.stackedWidget = self.window.findChild(QtWidgets.QStackedWidget, 'stackedWidget')
        
        # connecting ui elements to functions
        ### start page ###
        self.newRigBipBtn = self.window.findChild(QtWidgets.QPushButton, 'newRigBipBtn')
        self.newRigQipBtn = self.window.findChild(QtWidgets.QPushButton, 'newRigQipBtn')
        self.newRigCusBtn = self.window.findChild(QtWidgets.QPushButton, 'newRigCusBtn')
        self.newRigBipBtn.clicked.connect(lambda: self.changePage(2))
        self.newRigQipBtn.clicked.connect(lambda: self.changePage(1))
        self.newRigCusBtn.clicked.connect(lambda: self.changePage(3))
        ### biped page ###
        self.backBtn = self.window.findChild(QtWidgets.QCommandLinkButton, 'backBtn')
        self.backBtn.clicked.connect(lambda: self.changePage(0))

        self.charNameBox = self.window.findChild(QtWidgets.QLineEdit, 'charNameBox')
        self.charNameBox.textChanged.connect(self.charNameFunc)

        #self.spineJointNumBox.valueChanged.connect(self.placeHolder)
        self.fingerNumBox = self.window.findChild(QtWidgets.QSpinBox, 'fingerNumBox')
        self.fingerNumBox.valueChanged.connect(self.fingerNumChanged)
        self.toesNumBox = self.window.findChild(QtWidgets.QSpinBox, 'toesNumBox')
        self.toesNumBox.valueChanged.connect(self.toesNumChanged)

        self.footLockBox = self.window.findChild(QtWidgets.QCheckBox, 'footLockBox')
        self.footLockBox.stateChanged.connect(self.placeHolder)
        self.hipRollBox = self.window.findChild(QtWidgets.QCheckBox, 'hipRollBox')
        self.hipRollBox.stateChanged.connect(self.placeHolder)
        self.armRollBox = self.window.findChild(QtWidgets.QCheckBox, 'armRollBox')
        self.armRollBox.stateChanged.connect(self.placeHolder)
        self.fingerDblBox = self.window.findChild(QtWidgets.QCheckBox, 'fingerDblBox')
        self.fingerDblBox.stateChanged.connect(self.placeHolder)
        

        self.rigScaleBox = self.window.findChild(QtWidgets.QDoubleSpinBox, 'rigScaleBox')
        self.rigScaleBox.valueChanged.connect(lambda: AutoRig.scaleProxy())

        self.mirrorLeftBtn = self.window.findChild(QtWidgets.QPushButton, 'mirrorLeftBtn')
        self.mirrorLeftBtn.clicked.connect(lambda: AutoRig.mirrorProxy("R"))
        self.resetBtn = self.window.findChild(QtWidgets.QPushButton, 'resetBtn')
        self.resetBtn.clicked.connect(lambda: AutoRig.resetProxy())
        self.mirrorRightBtn = self.window.findChild(QtWidgets.QPushButton, 'mirrorRightBtn')
        self.mirrorRightBtn.clicked.connect(lambda: AutoRig.mirrorProxy("L"))
        self.createProxyBtn = self.window.findChild(QtWidgets.QPushButton, 'createProxyBtn')
        self.createProxyBtn.clicked.connect(lambda: AutoRig.makeProxyBiped())
        
        self.stretchyIkBtn = self.window.findChild(QtWidgets.QCheckBox, 'stretchyIkBtn')
        self.spineJointNumBox = self.window.findChild(QtWidgets.QSpinBox, 'spineJointNumBox')
        
        self.createRigBtn = self.window.findChild(QtWidgets.QPushButton, 'createRigBtn')
        self.createRigBtn.clicked.connect(lambda: AutoRig.makeSkeletonBiped())
        
        self.skinningBtn = self.window.findChild(QtWidgets.QPushButton, 'skinningBtn')
        self.skinningBtn.clicked.connect(self.skinMenu)
        ### quadruped page ###
        self.qBackBtn = self.window.findChild(QtWidgets.QCommandLinkButton, 'qBackBtn')
        self.qBackBtn.clicked.connect(lambda: self.changePage(0))
        self.qCharNameBox = self.window.findChild(QtWidgets.QLineEdit, 'qCharNameBox')
        self.qCharNameBox.textChanged.connect(self.qCharNameFunc)
        self.createProxyQBtn = self.window.findChild(QtWidgets.QPushButton, 'createProxyQBtn')
        self.createProxyQBtn.clicked.connect(lambda: AutoRig.makeProxyQuad())
        self.qRigScaleBox = self.window.findChild(QtWidgets.QDoubleSpinBox, 'qRigScaleBox')
        self.qRigScaleBox.valueChanged.connect(lambda: AutoRig.scaleProxy())
        self.createRigQBtn = self.window.findChild(QtWidgets.QPushButton, 'createRigQBtn')
        self.createRigQBtn.clicked.connect(lambda: AutoRig.makeSkeletonQuad())
        self.qSkinningBtn = self.window.findChild(QtWidgets.QPushButton, 'qSkinningBtn')
        self.qSkinningBtn.clicked.connect(self.skinMenu)

        self.tailNumBox = self.window.findChild(QtWidgets.QSpinBox, 'tailNumBox')
        
        ### custompage ###
        self.cBackBtn = self.window.findChild(QtWidgets.QCommandLinkButton, 'cBackBtn')
        self.cBackBtn.clicked.connect(lambda: self.changePage(0))
        #self.charNameBox.textChanged.connect(self.charNameFunc)
        self.cSkinningBtn = self.window.findChild(QtWidgets.QPushButton, 'cSkinningBtn')
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

    
    def customRigModule(self):
        pass
        '''
        model = QStandardItemModel()
        QStandardItem()
        '''


#print(cmds.window("mrWindowWorkspaceControl", exists=True))
#print(cmds.window("Magic Rig", exists=True))
#if cmds.window("Magic Rig", exists=True):
    #print("ere")
    #cmds.deleteUI("mrWindowWorkspaceControl")
print("RUN!")
window = MrWindow()

#print(cmds.window("Magic Rig", exists=True))
#print(cmds.window("mrWindowWorkspaceControl", exists=True))
# window.setDockableParameters(dockable=True, floating=True)
# window.show()
# window.raise_() # Move UI to front

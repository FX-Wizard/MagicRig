import maya.cmds as cmds

from rigUtils import FkIkBlend, freezeTransforms
from Control import Control
from proxyObj import proxyObj
from ui import window
from . import rigparts
from .rignode import MrNode
from .StretchyIK import makeStretchyIK

# set root rig node
if cmds.objExists("MR_Root"):
    prefix = cmds.getAttr("MR_Root.prefix")
    window.charNameBox.setText(prefix)
else:
    rootNode = MrNode("MR_Root")
    prefix = window.charNameBox.text()
    rootNode.addAttr("prefix", value=" ")
    rootNode.addAttr("masterScale", value=1.0)
    rootNode.addAttr("masterControl", value=" ")

# global joint lists
proxyList = []
proxyExtra = []
jointList = []


# Step 1: Create Proxy
def getModelScale():
    selection = cmds.ls(sl=True)
    if len(selection) > 0:
        modelScale = cmds.polyEvaluate(boundingBox=True)
        return modelScale[1]
    else:
        return 0


def makeProxyBiped():
    '''layout proxies for biped rig'''
    if cmds.objExists("proxyRig"):
        cmds.delete("proxyRig", "proxyExtra")
    proxyList[:] = [] # Clear proxyList
    # Proxy Group
    #cmds.group(name="proxyRig", empty=True)
    # global instances
    global root, spine, legL, legR, head, armL, armR
    # Root proxy object
    root = rigparts.root()
    # Spine
    sJointNum = window.spineJointNumBox.value()
    spine = rigparts.spine(sJointNum)
    # Leg + Foot
    numToes = window.toesNumBox.value()
    stretchy = window.stretchyIkBtn.checkState()
    legL = rigparts.leg("L", stretchy, numToes)
    legR = rigparts.leg("R", stretchy, numToes)
    # Head
    head = rigparts.head()
    # Arm + Hand
    numFingers = window.fingerNumBox.value()
    armRoll = window.armRollBox.checkState()
    armL = rigparts.arm("L", numFingers, armRoll, stretchy)
    armR = rigparts.arm("R", numFingers, armRoll, stretchy)
    # initial mirror
    cmds.select(clear=True)
    mirrorProxy("R")


def makeProxyQuad():
    '''layout proxies for quadruped rig'''
    if cmds.objExists("proxyRig"):
        cmds.delete("proxyRig", "proxyExtra")
    proxyList[:] = [] # Clear proxyList

    global root, spine, legFrontL, legFrontR, legBackL, legBackR, head, tail
    root = rigparts.root()
    cmds.move(0, 16, -8, root.rootJoint.name)
    # spine
    sJointNum = window.spineJointNumBox.value()
    spine = rigparts.spine(sJointNum)
    cmds.rotate(90, spine.mover, rotateX=True)
    cmds.move(0, 16, 0, spine.mover)
    # legs
    legFrontL = rigparts.quadLeg("Front_L")
    legFrontR = rigparts.quadLeg("Front_R")
    legBackL = rigparts.quadLeg("Back_L")
    legBackR = rigparts.quadLeg("Back_R")
    # head
    head = rigparts.head()
    cmds.move(0, 17, 10, head.mover)
    cmds.scale(1.3, 1.3, 1.3, head.mover)
    # tail
    tailJointNum = window.tailNumBox.value()
    tail = rigparts.tail(tailJointNum)
    cmds.move(0, 16, -10, tail.mover)
    # initial mirror
    cmds.select(clear=True)
    mirrorProxy("R")

def makeProxyCustom():
    '''layout proxies for custom rig'''
    proxyList[:] = [] # Clear proxyList


def scaleProxy():
    '''change total size of proxy rig'''
    value = window.rigScaleBox.value()
    cmds.scale(value, value, value, prefix + "_Rig", pivot=(0, 0, 0))
    cmds.setAttr("MR_Root.masterScale", value)


def resetProxy():
    '''delete proxy rig and create new proxy rig'''
    cmds.delete("proxyRig")
    proxyList[:] = []
    proxyExtra[:] = []
    jointList[:] = []
    if window.stackedWidget.getCurrentIndex() == 1:
        makeProxyBiped()
    elif window.stackedWidget.getCurrentIndex() == 2:
        makeProxyQuad()
    else:
        makeProxyCustom()


def mirrorProxy(orient):
    if orient == "R":
        source = "L"
    else:
        source = "R"
    for proxy in proxyList:
        if orient in proxy[-3:]:
            pos = cmds.getAttr("%s.translate" % proxy[::-1].replace(orient, source, 1)[::-1])
            cmds.setAttr("%s.translate" % proxy, (pos[0][0] * -1), pos[0][1], pos[0][2], type="float3")
    cmds.select(clear=True)


def makeSkeletonBiped():
    if not cmds.objExists(prefix + "_Rig"):
            makeProxyBiped()
    else:
        root.toJoint()
        spine.toJoint(root.rootJoint)
        legL.toJoint(root.rootJoint)
        legR.toJoint(root.rootJoint)
        armL.toJoint(spine.topJoint)
        armR.toJoint(spine.topJoint)
        head.toJoint(spine.topJoint)
        cmds.delete("proxyExtra")
        addControlsBiped()


def makeSkeletonQuad():
    if not cmds.objExists(prefix + "_Rig"):
        makeProxyBiped()
        root.toJoint()
        spine.toJoint()
        legFrontL.toJoint()
        legFrontR.toJoint()
        legBackL.toJoint()
        legBackR.toJoint()
        head.toJoint()
        tail.toJoint()
        cmds.delete("proxyExtra")
        addControlsQuad()
    else:
        makeProxyQuad()


# Step 2: Create Skeleton
def proxyToJoint():
    # Convert proxies to joints
    proxyList = cmds.ls("proxyRig", dagObjects=True, exactType="transform")
    del proxyList[0]

    for proxy in proxyList:
        cmds.select(proxy)
        jointName = proxy.lstrip("p")
        cmds.joint(name=jointName)
        cmds.ungroup(proxy)
        cmds.delete(proxy)
        jointList.append(jointName)
        cmds.makeIdentity(jointName, apply=True, translate=True, rotate=True, scale=True, jointOrient=True)

    jointGroup = cmds.group(jointList, name=prefix + "_rig")
    cmds.parent(jointGroup, world=True)

    cmds.delete("proxyExtra")
    cmds.delete("proxyRig")


def hideJoints():
    '''hide all joints in jointList'''
    for joint in jointList:
        cmds.setAttr(joint + ".drawStyle", 2)


def addControlsBiped():
    '''adds the controls to the biped character template'''
    superMover = Control("Master_Control", shape="ctrlMultiArrow", scale=2.2, parent=None)
    cmds.setAttr("MR_Root.masterControl", superMover.ctrlName, type="string")

    head.control()
    spine.control()
    legL.control()
    legR.control()
    armL.control()
    armR.control()


def addControlsQuad():
    superMover = Control("Master_Control", shape="ctrlMultiArrow", scale=2.2, parent=None)
    cmds.setAttr("MR_Root.masterControl", superMover.ctrlName, type="string")
    
    spine.control()
    legFrontL.control()
    legFrontR.control()
    legBackL.control()
    legBackR.control()
    head.control()
    tail.control()


def orientJoints(name, direction):
    # ensure the X axis of the joint is lined up with the direction of bone
    # Commet is an example script that can help
    if direction == "end":
        cmds.setAttr("%s.jointOrientX" % name, 0)
        cmds.setAttr("%s.jointOrientY" % name, 0)
        cmds.setAttr("%s.jointOrientZ" % name, 0)


def endJointOrient(name):
    cmds.setAttr("%s.jointOrientX" % name, 0)
    cmds.setAttr("%s.jointOrientY" % name, 0)
    cmds.setAttr("%s.jointOrientZ" % name, 0)
    # important to set end joint orient to 0

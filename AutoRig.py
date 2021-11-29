import maya.cmds as cmds
from Control import Control
print("HERE")
from ui import window
print("THERE")
from . import rigparts
from .rignode import MrNode

rootNode = None

def startup():
    global rootNode
    # set root rig node
    if cmds.objExists("MR_Root"):
        prefix = cmds.getAttr("MR_Root.prefix")
        window.charNameBox.setText(prefix)
        load()
    else:
        rootNode = MrNode("MR_Root")
        value = " "
        if window.charNameBox.text() != "":
            value = window.charNameBox.text()
        rootNode.addAttr("prefix", value=value)
        rootNode.addAttr("masterScale", value=1.0)
        rootNode.addAttr("masterControl")
        rootNode.addAttr("proxyObjects")
        rootNode.addAttr("controls")


# Create Proxy
def makeProxyBiped():
    '''layout proxies for biped rig'''
    if cmds.objExists("proxyExtra"):
        cmds.delete("proxyExtra")
    cmds.deleteAttr("MR_Root.proxyObjects")
    cmds.addAttr("MR_Root", ln="proxyObjects", at="message")
    # global instances
    global root, spine, legL, legR, head, armL, armR
    # Root proxy object
    root = rigparts.root("rootRig")
    # Spine
    sJointNum = window.spineJointNumBox.value()
    spine = rigparts.spine("spineRig", sJointNum)
    # Leg + Foot
    numToes = window.toesNumBox.value()
    stretchy = window.stretchyIkBtn.checkState()
    legL = rigparts.leg("legRigL", "L", stretchy, numToes)
    legR = rigparts.leg("legRigR","R", stretchy, numToes)
    # Head
    head = rigparts.head("headRig")
    # Arm + Hand
    numFingers = window.fingerNumBox.value()
    armRoll = window.armRollBox.checkState()
    armL = rigparts.arm("armRigL", "L", numFingers, armRoll, stretchy)
    armR = rigparts.arm("armRigR", "R", numFingers, armRoll, stretchy)
    # initial mirror
    cmds.select(clear=True)
    mirrorProxy("R")


def makeProxyQuad():
    '''layout proxies for quadruped rig'''
    if cmds.objExists("proxyExtra"):
        cmds.delete("proxyExtra")
    cmds.deleteAttr("MR_Root.proxyObjects")
    cmds.addAttr("MR_Root", ln="proxyObjects", at="message")

    global root, spine, legFrontL, legFrontR, legBackL, legBackR, head, tail
    root = rigparts.root("root")
    cmds.move(0, 16, -8, root.rootJoint)
    # spine
    sJointNum = window.spineJointNumBox.value()
    spine = rigparts.spine("spineRig", sJointNum)
    cmds.rotate(90, spine.mover, rotateX=True)
    cmds.move(0, 16, 0, spine.mover)
    # legs
    legFrontL = rigparts.quadLeg("Front_L", "L")
    cmds.move(2.4,14,5.662, legFrontL.mover)
    legFrontR = rigparts.quadLeg("Front_R", "R")
    cmds.move(-2.4,14,5.662, legFrontR.mover)
    legBackL = rigparts.quadLeg("Back_L", "L")
    legBackR = rigparts.quadLeg("Back_R", "R")
    # head
    head = rigparts.head("head")
    cmds.move(0, 17, 10, head.mover)
    cmds.scale(1.3, 1.3, 1.3, head.mover)
    # tail
    tailJointNum = window.tailNumBox.value()
    tail = rigparts.tail("tail", tailJointNum)
    cmds.move(0, 16, -10, tail.mover)
    # initial mirror
    cmds.select(clear=True)
    mirrorProxy("R")


def makeProxyCustom():
    '''layout proxies for custom rig'''
    cmds.deleteAttr("MR_Root.proxyObjects")
    cmds.addAttr("MR_Root", ln="proxyObjects", at="message")


# Make proxies into joints
def makeSkeletonBiped():
    if not cmds.objExists(getPrefix() + "_Rig"):
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
    if not cmds.objExists(getPrefix() + "_Rig"):
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


def makeSkeletonCustom():
    pass
    childObjects = cmds.listConnections("MR_Root.child")
    for parts in childObjects():
        parts.toJoint()


# Create control rig
def addControlsBiped():
    '''adds the controls to the biped character template'''
    # master controler
    superMover = Control("Master_Control", shape="ctrlMultiArrow", scale=2.2, parent=None, master=True)
    cmds.disconnectAttr("MR_Root.controls", superMover.ctrlName + ".controlName")
    cmds.connectAttr("MR_Root.masterControl", superMover.ctrlName + ".controlName")
    # make controls
    head.control()
    spine.control()
    legL.control()
    legR.control()
    armL.control()
    armR.control()


def addControlsQuad():
    # master controler
    superMover = Control("Master_Control", shape="ctrlMultiArrow", scale=2.2, parent=None, master=True)
    cmds.disconnectAttr("MR_Root.controls", superMover.ctrlName + ".controlName")
    cmds.connectAttr("MR_Root.masterControl", superMover.ctrlName + ".controlName")
    # make controls
    spine.control()
    legFrontL.control()
    legFrontR.control()
    legBackL.control()
    legBackR.control()
    head.control()
    tail.control()
    cleanup()


def addControlsCustom():
    # master controler
    superMover = Control("Master_Control", shape="ctrlMultiArrow", scale=2.2, parent=None, master=True)
    cmds.disconnectAttr("MR_Root.controls", superMover.ctrlName + ".controlName")
    cmds.connectAttr("MR_Root.masterControl", superMover.ctrlName + ".controlName")
    cleanup()


def getModelScale():
    selection = cmds.ls(sl=True)
    if len(selection) > 0:
        modelScale = cmds.polyEvaluate(boundingBox=True)
        return modelScale[1]
    else:
        return 0
    

def scaleProxy():
    '''change total size of proxy rig'''
    value = window.rigScaleBox.value()
    cmds.scale(value, value, value, getPrefix() + "_Rig", pivot=(0, 0, 0))
    cmds.setAttr("MR_Root.masterScale", value)


def resetProxy():
    '''delete proxy rig and create new proxy rig'''
    cmds.delete(getPrefix() + "_Rig")
    #cmds.setAttr("MR_Root.proxyObjects", " ")
    print(window.stackedWidget.currentIndex())
    if window.stackedWidget.currentIndex() == 2:
        makeProxyBiped()
    elif window.stackedWidget.getCurrentIndex() == 1:
        makeProxyQuad()
    else:
        makeProxyCustom()


def mirrorProxy(orient):
    if orient == "R":
        source = "L"
    else:
        source = "R"
    proxyList = cmds.listConnections("MR_Root.proxyObjects")
    for proxy in proxyList:
        if orient in proxy[-2:]:
            pos = cmds.getAttr("%s.translate" % proxy[::-1].replace(orient, source, 1)[::-1])
            cmds.setAttr("%s.translate" % proxy, (pos[0][0] * -1), pos[0][1], pos[0][2], type="float3")
    cmds.select(clear=True)


def getPrefix():
    ''' returns rig name '''
    return cmds.getAttr("MR_Root.prefix")


def load():
    rigNodes = cmds.listConnections("MR_Root.child")


def cleanup():
    # parent all controllers to master control
    ctrlOffsets = []
    controls = cmds.listConnections("MR_Root.controls")
    for ctrl in controls:
        ctrlOffsets.append(cmds.listConnections(ctrl + "controlOffset")[0])
    masterCtrl = cmds.listConnections("MR_Root.masterControl")[0]
    cmds.parent(ctrlOffsets, masterCtrl)


# create callbacks
#cmds.scriptJob(e=("NewSceneOpened", lambda: startup()), parent="mrWindowWorkspaceControl")

# run startup
startup()

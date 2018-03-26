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
    cmds.group(name="proxyRig", empty=True)
    # Root proxy object
    rootNode = MrNode("rootNode", parent="MR_Root")
    #rootNode.setParent("MR_Root")
    proxyObj("pRoot", (0, 14.5, 0))
    # Spine
    rigparts.spine()
    # Leg + Foot
    rigparts.leg("L")
    rigparts.leg("R")
    # Head
    rigparts.head()
    # Arm + Hand
    rigparts.arm("L")
    rigparts.arm("R")
    # Group extra proxy stuff
    cmds.group(proxyExtra, name="proxyExtra")
    cmds.select(clear=True)
    mirrorProxy("R")


def makeProxyQuad():
    '''layout proxies for quadruped rig'''
    proxyList[:] = [] # Clear proxyList


def makeProxyCustom():
    '''layout proxies for custom rig'''
    proxyList[:] = [] # Clear proxyList


def scaleProxy():
    '''change total size of proxy rig'''
    value = window.rigScaleBox.value()
    cmds.scale(value, value, value, "proxyRig", pivot=(0, 0, 0))
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
        if proxy[-1] == orient:
            pos = cmds.getAttr("%s.translate" % (proxy.rstrip(orient) + source))
            cmds.setAttr("%s.translate" % proxy, (pos[0][0] * -1), pos[0][1], pos[0][2], type="float3")
    cmds.select(clear=True)


def makeSkeletonBiped():
    proxyToJoint()
    buildSpine()
    buildLegs()
    buildArms()
    buildHead()
    #hideJoints()
    addControls()


def makeSkeletonQuad():
    proxyToJoint()


# Step 2: Create Skeleton
def proxyToJoint(): # old name = buildSkeleton
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


def buildSpine():
    # Dynamicly created Spine
    spineList = ["Root"]

    for joint in jointList:
        if "Spine" in joint:
            spineList.append(joint)

    for i in range(1, len(spineList)):
        cmds.select(spineList[i - 1])
        cmds.parent(jointList[i])


def buildLegs():
    '''build leg joints from proxy spine'''
    legJointsL = ["HipL", "KneeL", "AnkleL", "FootL", "ToeL"]
    legJointsR = ["HipR", "KneeR", "AnkleR", "FootR", "ToeR"]

    cmds.parent(["HipL", "HipR"], "Root")

    for i in range(1, len(legJointsL)):
        cmds.select(legJointsL[i - 1])
        cmds.parent(legJointsL[i])

    for i in range(1, len(legJointsR)):
        cmds.select(legJointsR[i - 1])
        cmds.parent(legJointsR[i])

    if window.footLockBox.checkState():
        cmds.parent("FootLockL", "AnkleL")
        cmds.parent("FootLockR", "AnkleR")


def buildArms():
    # Arms
    sJointNum = window.spineJointNumBox.value() - 1

    cmds.parent("ClavicleL", "Spine" + str(sJointNum))
    cmds.parent("ShoulderL", "ClavicleL")
    cmds.parent("ElbowL", "ShoulderL")
    if window.armRollBox.checkState():
        cmds.parent("ForearmRollL", "ElbowL")
        cmds.parent("WristL", "ForearmRollL")
    else:
        cmds.parent("WristL", "ElbowL")

    cmds.parent("ClavicleR", "Spine" + str(sJointNum))
    cmds.parent("ShoulderR", "ClavicleR")
    cmds.parent("ElbowR", "ShoulderR")
    if window.armRollBox.checkState():
        cmds.parent("ForearmRollR", "ElbowR")
        cmds.parent("WristR", "ForearmRollR")
    else:
        cmds.parent("WristR", "ElbowR")
    # Hand bone
    cmds.select("WristL", replace=True)
    cmds.joint(name="HandL")
    jointList.append("HandL")
    cmds.select("WristR", replace=True)
    cmds.joint(name="HandR")
    jointList.append("HandR")
    # Fingers
    numFingers = window.fingerNumBox.value()
    for i in range(1, numFingers):
        # left
        cmds.parent("FingerBase" + str(i) + "L", "HandL")
        cmds.parent("FingerMiddle" + str(i) + "L", "FingerBase" + str(i) + "L")
        cmds.parent("FingerEnd" + str(i) + "L", "FingerMiddle" + str(i) + "L")
        cmds.parent("FingerTip" + str(i) + "L", "FingerEnd" + str(i) + "L")

        # right
        cmds.parent("FingerBase" + str(i) + "R", "HandR")
        cmds.parent("FingerMiddle" + str(i) + "R", "FingerBase" + str(i) + "R")
        cmds.parent("FingerEnd" + str(i) + "R", "FingerMiddle" + str(i) + "R")
        cmds.parent("FingerTip" + str(i) + "R", "FingerEnd" + str(i) + "R")

    # Thumb L
    cmds.parent("ThumbBaseL", "HandL")
    cmds.parent("ThumbMidL", "ThumbBaseL")
    cmds.parent("ThumbEndL", "ThumbMidL")
    cmds.parent("ThumbTipL", "ThumbEndL")
    # Thumb R
    cmds.parent("ThumbBaseR", "HandR")
    cmds.parent("ThumbMidR", "ThumbBaseR")
    cmds.parent("ThumbEndR", "ThumbMidR")
    cmds.parent("ThumbTipR", "ThumbEndR")


def buildHead():
    # Head
    sJointNum = window.spineJointNumBox.value() - 1
    cmds.parent("Neck", "Spine" + str(sJointNum))
    cmds.parent("Head", "Neck")
    cmds.parent(["HeadTip", "Jaw", "EyeL", "EyeR"], "Head")
    cmds.parent("JawTip", "Jaw")

    # Orient joints
    cmds.joint("HipL", edit=True, orientJoint="xyz", secondaryAxisOrient="yup", zeroScaleOrient=True)
    cmds.joint("HipR", edit=True, orientJoint="xyz", secondaryAxisOrient="yup", zeroScaleOrient=True)

    cmds.joint("KneeL", edit=True, orientJoint="xyz", secondaryAxisOrient="yup", zeroScaleOrient=True)
    cmds.joint("KneeR", edit=True, orientJoint="xyz", secondaryAxisOrient="yup", zeroScaleOrient=True)

    cmds.joint("AnkleL", edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)
    cmds.joint("AnkleL", edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)

    cmds.joint("ClavicleR", edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True)
    cmds.joint("ClavicleL", edit=True, orientJoint="xyz", secondaryAxisOrient="ydown", children=True)


def hideJoints():
    '''hide all joints in jointList'''
    for joint in jointList:
        cmds.setAttr(joint + ".drawStyle", 2)


def addControls():
    ##########################################################################
    # Controllers
    ##########################################################################
    superMover = Control("superMover", shape="ctrlMultiArrow", scale=2.2, parent=None)

    ## head
    headCtrl = Control("head", scale=2, snapTo="HeadTip", pointTo="HeadTip")
    pos = cmds.joint("Neck", query=True, absolute=True, position=True)
    cmds.move(pos[0], pos[1], pos[2], headCtrl.ctrlName + ".scalePivot", headCtrl.ctrlName + ".rotatePivot")
    cmds.parentConstraint(headCtrl.ctrlOff, "Neck", maintainOffset=True)

    # Spine
    sJointNum = cmds.getAttr("spineNode.spineJointNum") - 1
    cmds.ikHandle(name="ikSpine", solver="ikSplineSolver", createCurve=True,
                startJoint="Spine0", endEffector="Spine" + str(sJointNum))
    ikCurve = cmds.ikHandle("ikSpine", query=True, curve=True)
    ikCurve = (ikCurve.split("|"))[3]
    cmds.rename(ikCurve, "ikSpineCurve")

    # Spine and hips
    sJointNum = sJointNum = window.spineJointNumBox.value() - 1
    #Control("upperBackIKCtrl", scale=4, snapTo="Spine" + str(sJointNum))
    #Control("lowerBackIKCtrl", scale=4, snapTo="Root")
    centerMassCtrl = Control("centerMass", scale=5.5, snapTo="Root")

    curveCVs = cmds.ls("ikSpineCurve.cv[:]", flatten=True)
    for i, CV in enumerate(curveCVs):
        cmds.cluster(CV, name="spine" + str(i) + "Cluster")
        back = Control("Back" + str(i), scale=4, snapTo="Spine" + str(i))
        cmds.parent("spine" + str(i) + "ClusterHandle", back.ctrlName)
        cmds.parent(back.ctrlOff, centerMassCtrl.ctrlName)

    #cmds.parent("spine3ClusterHandle", "upperBackIKCtrl")
    #cmds.orientConstraint("upperBackIKCtrl", "Spine" + str(sJointNum), maintainOffset=True)
    #cmds.parent("spine0ClusterHandle", "lowerBackIKCtrl")
    cmds.parentConstraint(prefix + "_Back0_ctrl", "Root", maintainOffset=True)

    cmds.parent("ikSpineCurve", world=True) # fix double translate bug
    cmds.setAttr("ikSpineCurve.inheritsTransform", 0)

    # Legs
    ikLegL, legCtrlL = FkIkBlend(["HipL", "KneeL", "AnkleL"], "Leg", 4, superMover.ctrlName, side="L")
    ikLegR, legCtrlR = FkIkBlend(["HipR", "KneeR", "AnkleR"], "Leg", 4, superMover.ctrlName, side="R")

    # Ik foot
    cmds.ikHandle(name="ikFootL", startJoint="AnkleL", endEffector="FootL", solver="ikSCsolver")
    cmds.ikHandle(name="ikFootR", startJoint="AnkleR", endEffector="FootR", solver="ikSCsolver")
    cmds.ikHandle(name="ikToeL", startJoint="FootL", endEffector="ToeL", solver="ikSCsolver")
    cmds.ikHandle(name="ikToeR", startJoint="FootR", endEffector="ToeR", solver="ikSCsolver")
    # Left foot
    footCtrlL = Control("footCtrlL", snapTo="FootL", scale=[2, 2, 3])
    cmds.parent([prefix + "_AnkleLIK_L_offset", "ikFootL", "ikToeL"], footCtrlL.ctrlName)
    # toe tip
    pos = cmds.joint("ToeL", query=True, absolute=True, position=True)
    cmds.group(prefix + "_AnkleLIK_L_offset", "ikFootL", "ikToeL", name="toeTipPivotL")
    cmds.move(pos[0], pos[1], pos[2], "toeTipPivotL.scalePivot", "toeTipPivotL.rotatePivot")
    # toe tap
    pos = cmds.joint("FootL", query=True, absolute=True, position=True)
    cmds.group("ikFootL", "ikToeL", name="toeTapPivotL")
    cmds.move(pos[0], pos[1], pos[2], "toeTapPivotL.scalePivot", "toeTapPivotL.rotatePivot")
    # heel peel
    cmds.group(prefix + "_AnkleLIK_L_offset", name="heelPeelPivotL")
    cmds.move(pos[0], pos[1], pos[2], "heelPeelPivotL.scalePivot", "heelPeelPivotL.rotatePivot")
    # heel tap
    cmds.group("toeTipPivotL", name="heelTapPivotL")
    jpos = cmds.joint("FootLockR", query=True, absolute=True, position=True)
    cmds.move(jpos[0], jpos[1], jpos[2], "heelTapPivotL.scalePivot", "heelTapPivotL.rotatePivot")

    # right foot
    footCtrlR = Control("footCtrlR", snapTo="FootR",  scale=[2, 2, 3])
    cmds.parent([prefix + "_AnkleRIK_R_offset", "ikFootR", "ikToeR"], footCtrlR.ctrlName)
    # toe tip
    pos = cmds.joint("ToeR", query=True, absolute=True, position=True)
    cmds.group(prefix + "_AnkleRIK_R_offset", "ikFootR", "ikToeR", name="toeTipPivotR")
    cmds.move(pos[0], pos[1], pos[2], "toeTipPivotR.scalePivot", "toeTipPivotR.rotatePivot")
    # toe tap
    pos = cmds.joint("FootR", query=True, absolute=True, position=True)
    cmds.group("ikFootR", "ikToeR", name="toeTapPivotR")
    cmds.move(pos[0], pos[1], pos[2], "toeTapPivotR.scalePivot", "toeTapPivotR.rotatePivot")
    # heel peel
    cmds.group(prefix + "_AnkleRIK_R_offset", name="heelPeelPivotR")
    cmds.move(pos[0], pos[1], pos[2], "heelPeelPivotR.scalePivot", "heelPeelPivotR.rotatePivot")
    # heel tap
    cmds.group("toeTipPivotR", name="heelTapPivotR")
    jpos = cmds.joint("FootLockR", query=True, absolute=True, position=True)
    cmds.move(jpos[0], jpos[1], jpos[2], "heelTapPivotR.scalePivot", "heelTapPivotR.rotatePivot")

    # Clavicle
    ClavicleCtrlL = Control("ClavicleCtrlL", scale=0.5, direction="x", snapTo="ShoulderL", moveTo=["y", 24])
    cmds.ikHandle(name="clavicleIkL", startJoint="ClavicleL", endEffector="ShoulderL", solver="ikRPsolver")
    cmds.pointConstraint(ClavicleCtrlL.ctrlName, "clavicleIkL", maintainOffset=True)
    ClavicleCtrlR = Control("ClavicleCtrlR", scale=0.5, direction="x", snapTo="ShoulderR", moveTo=["y", 24])
    cmds.ikHandle(name="clavicleIkR", startJoint="ClavicleR", endEffector="ShoulderR", solver="ikRPsolver")
    cmds.pointConstraint(ClavicleCtrlR.ctrlName, "clavicleIkR", maintainOffset=True)
    # Arms
    ikArmL, armCtrlL = FkIkBlend(["ShoulderL", "ElbowL", "WristL"], "Arm", -4, superMover.ctrlName, side="L")
    ikArmR, armCtrlR = FkIkBlend(["ShoulderR", "ElbowR", "WristR"], "Arm", -4, superMover.ctrlName, side="R")

    # Finger FK controls
    numFingers = window.fingerNumBox.value()
    for i in range(1, numFingers):
        # left
        FingerBaseCtrl = Control("FingerBase_" + str(i) + "L", scale=0.5, snapTo="FingerBase" + str(i) + "L",
                pointTo="FingerMiddle" + str(i) + "L", parent="WristL", direction="z")
        cmds.orientConstraint(FingerBaseCtrl.ctrlName, "FingerBase" + str(i) + "L", maintainOffset=True)

        FingerMiddleCtrl = Control("FingerMiddle_" + str(i) + "L", scale=0.5, snapTo="FingerMiddle" + str(i) + "L",
                pointTo="FingerBase" + str(i) + "L", parent=FingerBaseCtrl.ctrlName, direction="z")
        cmds.orientConstraint(FingerMiddleCtrl.ctrlName, "FingerMiddle" + str(i) + "L", maintainOffset=True)

        FingerEndCtrl = Control("FingerEnd_" + str(i) + "L", scale=0.5, snapTo="FingerEnd" + str(i) + "L",
                pointTo="FingerTip" + str(i) + "L", parent=FingerMiddleCtrl.ctrlName, direction="z")
        cmds.orientConstraint(FingerEndCtrl.ctrlName, "FingerEnd" + str(i) + "L", maintainOffset=True)

        # right
        FingerBaseCtrl = Control("FingerBase_" + str(i) + "R", scale=0.5, snapTo="FingerBase" + str(i) + "R",
                pointTo="FingerMiddle" + str(i) + "R", parent="WristR", direction="z")
        cmds.orientConstraint(FingerBaseCtrl.ctrlName, "FingerBase" + str(i) + "R", maintainOffset=True)

        FingerMiddleCtrl = Control("FingerMiddle_" + str(i) + "R", scale=0.5, snapTo="FingerMiddle" + str(i) + "R",
                pointTo="FingerBase" + str(i) + "R", parent=FingerBaseCtrl.ctrlName, direction="z")
        cmds.orientConstraint(FingerMiddleCtrl.ctrlName, "FingerMiddle" + str(i) + "R", maintainOffset=True)

        FingerEndCtrl = Control("FingerEnd_" + str(i) + "R", scale=0.5, snapTo="FingerEnd" + str(i) + "R",
                pointTo="FingerTip" + str(i) + "R", parent=FingerMiddleCtrl.ctrlName, direction="z")
        cmds.orientConstraint(FingerEndCtrl.ctrlName, "FingerEnd" + str(i) + "R", maintainOffset=True)

    # left thumb
    ThumbBaseCtrlL = Control("ThumbBase_L", scale=0.5, snapTo="ThumbBaseL", pointTo="ThumbMidL", 
                            parent="WristL", direction="z")
    cmds.orientConstraint(ThumbBaseCtrlL.ctrlName, "ThumbBaseL", maintainOffset=True)

    ThumbMidCtrlL = Control("ThumbMid_L", scale=0.5, snapTo="ThumbMidL", pointTo="ThumbBaseL", 
                            parent=ThumbBaseCtrlL.ctrlName, direction="z")
    cmds.orientConstraint(ThumbMidCtrlL.ctrlName, "ThumbMidL", maintainOffset=True)

    ThumbEndCtrlL = Control("ThumbEnd_L", scale=0.5, snapTo="ThumbEndL", pointTo="ThumbMidL", 
                            parent=ThumbMidCtrlL.ctrlName, direction="z")
    cmds.orientConstraint(ThumbEndCtrlL.ctrlName, "ThumbEndL", maintainOffset=True)
    # right thumb
    ThumbBaseCtrlR = Control("ThumbBase_R", scale=0.5, snapTo="ThumbBaseR", pointTo="ThumbMidR", 
                            parent="WristR", direction="z")
    cmds.orientConstraint(ThumbBaseCtrlR.ctrlName, "ThumbBaseR", maintainOffset=True)

    ThumbMidCtrlR = Control("ThumbMid_R", scale=0.5, snapTo="ThumbMidR", pointTo="ThumbBaseR", 
                            parent=ThumbBaseCtrlR.ctrlName, direction="z")
    cmds.orientConstraint(ThumbMidCtrlR.ctrlName, "ThumbMidR", maintainOffset=True)

    ThumbEndCtrlR = Control("ThumbEnd_R", scale=0.5, snapTo="ThumbEndR", pointTo="ThumbMidR", 
                            parent=ThumbMidCtrlR.ctrlName, direction="z")
    cmds.orientConstraint(ThumbEndCtrlR.ctrlName, "ThumbEndR", maintainOffset=True)

    # Finger IK controls
    '''
    ### this is totaly broken and wont make it into the rig before the deadline ###
    for i in range(1, numFingers):
        cmds.ikHandle(name="ikFinger" + str(i) + "L", startJoint="IKJFingerBase" + str(i) + "L",
                endEffector="IKJFingerTip" + str(i) + "L", solver="ikSCsolver")
        cmds.parent("ikFinger" + str(i) + "L", "FingerTipCtrl" + str(i) + "L")
        cmds.ikHandle(name="ikFinger" + str(i) + "R", startJoint="IKJFingerBase" + str(i) + "R",
                endEffector="IKJFingerTip" + str(i) + "R", solver="ikSCsolver")
        cmds.parent("ikFinger" + str(i) + "R", "FingerTipCtrl" + str(i) + "R")
    cmds.ikHandle(name="ikThumbL", startJoint="IKJThumbBaseL",
            endEffector="IKJThumbTipL", solver="ikSCsolver")
    cmds.parent("ikThumbL", "ThumbTipCtrlL")
    cmds.ikHandle(name="ikThumbR", startJoint="IKJThumbBaseR",
            endEffector="IKJThumbTipR", solver="ikSCsolver")
    cmds.parent("ikThumbR", "ThumbTipCtrlR")
    '''

    # Connetct Attributes to controlers
    # toe tip
    cmds.addAttr(footCtrlL.ctrlName, longName="toe_tip", attributeType="float", min=0, max=90, defaultValue=0)
    cmds.setAttr(footCtrlL.ctrlName + ".toe_tip", edit=True, keyable=True)
    cmds.connectAttr(footCtrlL.ctrlName + ".toe_tip", "toeTipPivotL.rx")

    cmds.addAttr(footCtrlR.ctrlName, longName="toe_tip", attributeType="float", min=0, max=90, defaultValue=0)
    cmds.setAttr(footCtrlR.ctrlName + ".toe_tip", edit=True, keyable=True)
    cmds.connectAttr(footCtrlR.ctrlName + ".toe_tip", "toeTipPivotR.rx")

    # toe tap
    cmds.addAttr(footCtrlL.ctrlName, longName="toe_tap", attributeType="float", defaultValue=0)
    cmds.setAttr(footCtrlL.ctrlName + ".toe_tap", edit=True, keyable=True)
    cmds.connectAttr(footCtrlL.ctrlName + ".toe_tap", "toeTapPivotL.rx")

    cmds.addAttr(footCtrlR.ctrlName, longName="toe_tap", attributeType="float", defaultValue=0)
    cmds.setAttr(footCtrlR.ctrlName + ".toe_tap", edit=True, keyable=True)
    cmds.connectAttr(footCtrlR.ctrlName + ".toe_tap", "toeTapPivotR.rx")

    # heel peel
    cmds.addAttr(footCtrlL.ctrlName, longName="heel_peel", attributeType="float", min=0, max=100, defaultValue=0)
    cmds.setAttr(footCtrlL.ctrlName + ".heel_peel", edit=True, keyable=True)
    cmds.connectAttr(footCtrlL.ctrlName + ".heel_peel", "heelPeelPivotL.rx")

    cmds.addAttr(footCtrlR.ctrlName, longName="heel_peel", attributeType="float", min=0, max=100, defaultValue=0)
    cmds.setAttr(footCtrlR.ctrlName + ".heel_peel", edit=True, keyable=True)
    cmds.connectAttr(footCtrlR.ctrlName + ".heel_peel", "heelPeelPivotR.rx")

    # heel tap
    cmds.addAttr(footCtrlL.ctrlName, longName="heel_tap", attributeType="float", defaultValue=0)
    cmds.setAttr(footCtrlL.ctrlName + ".heel_tap", edit=True, keyable=True)
    cmds.connectAttr(footCtrlL.ctrlName + ".heel_tap", "heelTapPivotL.rx")

    cmds.addAttr(footCtrlR.ctrlName, longName="heel_tap", attributeType="float", defaultValue=0)
    cmds.setAttr(footCtrlR.ctrlName + ".heel_tap", edit=True, keyable=True)
    cmds.connectAttr(footCtrlR.ctrlName + ".heel_tap", "heelTapPivotR.rx")

    # stretchy IK
    if window.stretchyIkBtn.checkState():
        makeStretchyIK(ikLegL, controlObj=legCtrlL)
        makeStretchyIK(ikLegR, controlObj=legCtrlR)
        makeStretchyIK(ikArmL, controlObj=armCtrlL)
        makeStretchyIK(ikArmR, controlObj=armCtrlR)


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

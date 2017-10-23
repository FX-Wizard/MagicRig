import maya.cmds as cmds

# create UI

if cmds.window("magiRigWin", exists = True):
    cmds.deleteUI("magiRigWin")
    
window = cmds.window("magiRigWin", title="Magic Rig", resizeToFitChildren = True)
cmds.columnLayout("magiRootLayout", adjustableColumn = True)

# proxy
cmds.frameLayout("stepOne", label = "Step 1: Create Proxy Rig", collapsable = True, collapse = False, parent = "magiRootLayout")
cmds.intSliderGrp("spineJointNumUi", label = "Spine joint number", field = True, minValue = 1, maxValue = 33, value = 4, parent = "stepOne")
cmds.intSliderGrp("fingersNumUi", label = "fingers number", field = True, minValue = 1, maxValue = 6, value = 5, parent = "stepOne")
cmds.intSliderGrp("toesNumUi", label = "toes number", field = True, minValue = 1, maxValue = 6, value = 1, parent = "stepOne")
cmds.checkBox("footLockUi", label = "Reverse Foot Lock", parent = "stepOne", value = True)
cmds.checkBox("rollJointUi", label = "Add roll joints", parent = "stepOne", value = True)
cmds.floatSliderGrp("rigScaleUi", label = "Rig Scale", minValue = 0, maxValue = 10, value = 1, field = True, dragCommand = 'scaleProxy()', parent = "stepOne")
cmds.rowLayout("threeBtnLayout", numberOfColumns = 3, ad3 = 2, parent = "stepOne")
cmds.button(label = "<-- Mirror", command = 'mirrorProxy("R")', parent = "threeBtnLayout")
cmds.button(label = "reset",command = 'resetProxy()',  parent = "threeBtnLayout")
cmds.button(label = "Mirror -->", command = 'mirrorProxy("L")', parent = "threeBtnLayout")
cmds.button(label = "Create Proxy!", command = 'createProxy()', parent = "stepOne")

# joints
cmds.frameLayout("stepTwo", label = "Step 2: Position Proxy", collapsable = True, collapse = False, parent = "magiRootLayout")
cmds.text("helpTwo", wordWrap = True, parent = "stepTwo", label = "Adjust the proxy joints to match your model, then press create rig")
cmds.button(label = "Create Rig!", command = 'buildSkeleton()', parent = "stepTwo")

# controls
cmds.frameLayout("stepThree", label = "Step 3: Skin the rig", collapsable = True, collapse = False, parent = "magiRootLayout")
cmds.text("helpThree", wordWrap = True, parent = "stepThree", label = "need some instructions here")
cmds.button(label = "Add Controls!", command = 'autoSkin()', parent = "stepThree")

cmds.showWindow()

# Step 1: Create Proxy
proxyList = []
jointList = []

def getModelScale():
    selection = cmds.ls(sl = True)
    if len(selection) > 0:
        modelScale = cmds.polyEvaluate(boundingBox = True)
        return modelScale[1]
    else:
        return 0


# Create proxy object from curves. Takes name of proxy object as an argument.
def proxyObj(proxyName, move = None):
    scale = getModelScale()
    cmds.circle(name = proxyName,
    normal = (0, 1, 0),
    center = (0, 0, 0),
    sweep = 360,
    radius = (0.25))

    # makeProxyJoint
    cmds.duplicate(returnRootsOnly = True, name = (proxyName + "Y"))
    cmds.rotate(90,0,0)
    cmds.makeIdentity(apply = True, t = 1, r = 1, s = 1, n = 0)
    cmds.duplicate(returnRootsOnly = True, name = (proxyName + "Z"))
    cmds.rotate(0,90,0)
    cmds.makeIdentity(apply = True, t = 1, r = 1, s = 1, n = 0)
    cmds.parent(((proxyName + "YShape"), (proxyName + "ZShape")), proxyName, shape = True, relative = True)
    cmds.delete((proxyName + "Y"), (proxyName + "Z"))

    if move:
        cmds.move(move[0], move[1], move[2], proxyName)

    proxyList.append(proxyName)


def createProxy():
    # Root
    proxyObj("pRoot", (0, 14.5, 0))

    # Spine
    sJointNum = cmds.intSliderGrp("spineJointNumUi", query = True, value = True)

    seperation = (7.1 / (sJointNum - 1))

    for i in range(sJointNum):
        proxyObj("pSpine" + str(i), (0, (seperation * i) + 15, 0, ))

    # Leg
    proxyObj("pHipL", (1.7, 14, 0))
    proxyObj("pKneeL", (1.7, 8 , 0))
    proxyObj("pAnkleL", (1.7, 1.6, 0))

    # Foot
    proxyObj("pFootL", (1.7, 0, 2.3))
    proxyObj("pToeL", (1.7, 0, 4))

    if cmds.checkBox("footLockUi", query = True, value = True):
        proxyObj("pFootLockL", (1.7, 0, -0.5))

    # Head
    proxyObj("pNeck", (0, 23.5, 0))
    proxyObj("pHead", (0, 24.5, 0))
    proxyObj("pHeadTip", (0, 28, 0))
    proxyObj("pJaw", (0, 25, 0.4))
    proxyObj("pJawTip", (0, 24.4, 1.9))
    proxyObj("pEyeL", (0.6, 26, 1.6))

    # Arms
    proxyObj("pClavicleL", (1.25, 22.5, 0))
    proxyObj("pShoulderL", (3, 22.5, 0))
    proxyObj("pElbowL", (6.4, 22.5, 0))
    proxyObj("pWristL",(10, 22.5, 0))

    if cmds.checkBox("rollJointUi", query = True, value = True):
        proxyObj("pForearmRollL", (7.5, 22.5, 0))

    # Hand
    numFingers = cmds.intSliderGrp("fingersNumUi", query = True, value = True)

    proxyObj("pThumbBaseL", (11, 22.5, 0.5))
    proxyObj("pThumbMidL", (11, 22.5, 1))
    proxyObj("pThumbEndL", (11, 22.5, 1.5))
    proxyObj("pThumbTipL", (11, 22.5, 2))

    space = 0.5
    start = space * (numFingers / 2)
    for i in range(1, numFingers):
        proxyObj("pFingerBase" + str(i) + "L", (12, 22.5, start - (space * i)))
        proxyObj("pFingerMiddle" + str(i) + "L", (12.5, 22.5, start - (space * i)))
        proxyObj("pFingerEnd" + str(i) + "L", (13, 22.5, start - (space * i)))
        proxyObj("pFingerTip" + str(i) + "L", (13.5, 22.5, start - (space * i)))

    # initial mirror from L to R
    for item in proxyList:
        if item[-1] == "L":
            pos = cmds.getAttr("%s.translate" % item)
            proxyObj(item.rstrip("L") + "R", ((pos[0][0] * -1), pos[0][1], pos[0][2]))

    # Group proxies
    cmds.select(proxyList)
    cmds.group(name = "proxyRig")
    cmds.select(clear = True)


def scaleProxy():
    value = cmds.floatSliderGrp("rigScaleUi", query = True, value = True)
    cmds.scale(value, value, value, "proxyRig", pivot = (0, 0, 0))


def resetProxy():
    cmds.delete("proxyRig")
    proxyList[:] = []
    jointList[:] = []
    createProxy()


def mirrorProxy(orient):
    if orient == "R":
        source = "L"
    else:
        source = "R"
    for proxy in proxyList:
        if proxy[-1] == orient:
            pos = cmds.getAttr("%s.translate" % (proxy.rstrip(orient) + source))
            cmds.move((pos[0][0] * -1), pos[0][1], pos[0][2], proxy)
    cmds.select(clear = True)


# Step 2: Create Skeleton
def buildSkeleton():
    # Convert proxies to joints
    proxyList = cmds.ls("proxyRig", dagObjects = True, exactType = "transform")
    del proxyList[0]

    for joint in proxyList:
        cmds.select(joint)
        newName = joint.lstrip("p")
        cmds.joint(name = newName, scaleCompensate = True)
        cmds.ungroup(joint)
        cmds.delete(joint)
        jointList.append(newName)
        cmds.makeIdentity(newName, apply = True, translate = True, rotate = True, scale = True, jointOrient = True)

    # Parent joints
    # Dynamicly created joints
    spineList = ["Root"]

    for joint in (jointList):
        if "Spine" in joint:
            spineList.append(joint)

    # Spine
    for i in range(1, len(spineList)):
        cmds.select(spineList[i - 1])
        cmds.parent(jointList[i])

    # Fingers
    numFingers = cmds.intSliderGrp("fingersNumUi", query = True, value = True)
    for i in range(1, numFingers):
        # left
        cmds.parent("FingerBase" + str(i) + "L", "WristL")
        cmds.parent("FingerMiddle" + str(i) + "L", "FingerBase" + str(i) + "L")
        cmds.parent("FingerEnd" + str(i) + "L", "FingerMiddle" + str(i) + "L")
        cmds.parent("FingerTip" + str(i) + "L", "FingerEnd" + str(i) + "L")
        # right
        cmds.parent("FingerBase" + str(i) + "R", "WristR")
        cmds.parent("FingerMiddle" + str(i) + "R", "FingerBase" + str(i) + "R")
        cmds.parent("FingerEnd" + str(i) + "R", "FingerMiddle" + str(i) + "R")
        cmds.parent("FingerTip" + str(i) + "R", "FingerEnd" + str(i) + "R")

    # Legs
    legJointsL = ["HipL", "KneeL", "AnkleL",  "FootL",  "ToeL"]
    legJointsR = ["HipR", "KneeR", "AnkleR", "FootR", "ToeR"]

    cmds.parent(["HipL", "HipR"], "Root")

    for i in range(1, len(legJointsL)):
        cmds.select(legJointsL[i - 1])
        cmds.parent(legJointsL[i])

    for i in range(1, len(legJointsR)):
        cmds.select(legJointsR[i - 1])
        cmds.parent(legJointsR[i])

    if cmds.checkBox("footLockUi", query = True, value = True):
        cmds.parent("FootLockL", "AnkleL")
        cmds.parent("FootLockR", "AnkleR")

    # Arms
    sJointNum = (cmds.intSliderGrp("spineJointNumUi", query = True, value = True) - 1)

    cmds.parent("ClavicleL", "Spine" + str(sJointNum))
    cmds.parent("ShoulderL", "ClavicleL")
    cmds.parent("ElbowL", "ShoulderL")
    if cmds.checkBox("rollJointUi", query = True, value = True):
        cmds.parent("ForearmRollL", "ElbowL")
        cmds.parent("WristL", "ForearmRollL")
    else:
        cmds.parent("WristL", "ElbowL")

    cmds.parent("ClavicleR", "Spine" + str(sJointNum))
    cmds.parent("ShoulderR", "ClavicleR")
    cmds.parent("ElbowR", "ShoulderR")
    if cmds.checkBox("rollJointUi", query = True, value = True):
        cmds.parent("ForearmRollR", "ElbowR")
        cmds.parent("WristR", "ForearmRollR")
    else:
        cmds.parent("WristR", "ElbowR")
 
    # Thumb
    cmds.parent("ThumbBaseL", "WristL")
    cmds.parent("ThumbMidL", "ThumbBaseL")
    cmds.parent("ThumbEndL", "ThumbMidL")
    cmds.parent("ThumbTipL", "ThumbEndL")

    cmds.parent("ThumbBaseR", "WristR")
    cmds.parent("ThumbMidR", "ThumbBaseR")
    cmds.parent("ThumbEndR", "ThumbMidR")
    cmds.parent("ThumbTipR", "ThumbEndR")

    # Head
    cmds.parent("Neck", "Spine" + str(sJointNum))
    cmds.parent("Head", "Neck")
    cmds.parent(["HeadTip", "Jaw", "EyeL", "EyeR"], "Head")
    cmds.parent("JawTip", "Jaw")

    # Orient joints
    cmds.joint("HipL", edit = True,  orientJoint = "xyz", secondaryAxisOrient = "yup", zeroScaleOrient = True)
    cmds.joint("HipR", edit = True,  orientJoint = "xyz", secondaryAxisOrient = "yup", zeroScaleOrient = True)
    
    cmds.joint("KneeL", edit = True,  orientJoint = "xyz", secondaryAxisOrient = "yup", zeroScaleOrient = True)
    cmds.joint("KneeR", edit = True,  orientJoint = "xyz", secondaryAxisOrient = "yup", zeroScaleOrient = True)

    cmds.joint("AnkleL", edit = True,  orientJoint = "xyz", secondaryAxisOrient = "yup", children = True, zeroScaleOrient = True)
    cmds.joint("AnkleL", edit = True,  orientJoint = "xyz", secondaryAxisOrient = "yup", children = True, zeroScaleOrient = True)

    cmds.joint("ClavicleR", edit = True,  orientJoint = "xyz", secondaryAxisOrient = "yup", children = True)
    cmds.joint("ClavicleL", edit = True,  orientJoint = "xyz", secondaryAxisOrient = "ydown", children = True)

    ### Controlers ###
    makeControl("superMover", ctrlSize = 8, ctrlNormal = (0, 1, 0))
    # FK
    # head
    makeControl("headCtrl", ctrlSize = 2, snapJoint = "HeadTip", ctrlNormal = (0, 1, 0))
    pos = cmds.joint("Neck", query = True, absolute = True, position = True)
    cmds.move(pos[0], pos[1], pos[2], "headCtrl.scalePivot", "headCtrl.rotatePivot")
    cmds.parentConstraint("headCtrl", "Neck", maintainOffset = True)
    lockHide("headCtrl", rotate = False)
    # left hip
    makeControl("hipCtrlL", ctrlSize = 1.5, snapJoint = "HipL", ctrlNormal = (0, 1, 0))
    cmds.orientConstraint("hipCtrlL", "HipL", maintainOffset = True)
    lockHide("hipCtrlL", rotate = False)
    # left knee
    makeControl("kneeCtrlL", ctrlSize = 1.5, snapJoint = "KneeL", ctrlNormal = (0, 1, 0))
    cmds.orientConstraint("kneeCtrlL", "KneeL", maintainOffset = True)
    cmds.parent("kneeCtrlL", "hipCtrlL")
    lockHide("kneeCtrlL", rotate = False)
    # Left ankle
    makeControl("ankleCtrlL", ctrlSize = 2, snapJoint = "AnkleL", ctrlNormal = (0, 1, 0))
    cmds.orientConstraint("ankleCtrlL", "AnkleL", maintainOffset = True)
    cmds.parent("ankleCtrlL", "kneeCtrlL")
    lockHide("ankleCtrlL", rotate = False)

    # right hip
    makeControl("hipCtrlR", ctrlSize = 1.5, snapJoint = "HipR", ctrlNormal = (0, 1, 0))
    cmds.orientConstraint("hipCtrlR", "HipR", maintainOffset = True)
    lockHide("hipCtrlR", rotate = False)
    # right knee
    makeControl("kneeCtrlR", ctrlSize = 1.5, snapJoint = "KneeR", ctrlNormal = (0, 1, 0))
    cmds.orientConstraint("kneeCtrlR", "KneeR", maintainOffset = True)
    cmds.parent("kneeCtrlR", "hipCtrlR")
    lockHide("kneeCtrlR", rotate = False)
    # right ankle
    makeControl("ankleCtrlR", ctrlSize = 2, snapJoint = "AnkleR", ctrlNormal = (0, 1, 0))
    cmds.orientConstraint("ankleCtrlR", "AnkleR", maintainOffset = True)
    cmds.parent("ankleCtrlR", "kneeCtrlR")
    lockHide("ankleCtrlR", rotate = False)
    # Arms
    # left shoulder
    makeControl("shoulderCtrlL", ctrlSize = 2, snapJoint = "ShoulderL", orientJoint = "ElbowL", ctrlNormal = (0, 1, 0))
    cmds.orientConstraint("shoulderCtrlL", "ShoulderL", maintainOffset = True)
    lockHide("shoulderCtrlL", rotate = False)
    #left elbow
    makeControl("elbowCtrlL", ctrlSize = 1.5, snapJoint = "ElbowL", orientJoint = "WristL", ctrlNormal = (0, 1, 0), constrain = "shoulderCtrlL")
    cmds.orientConstraint("elbowCtrlL", "ElbowL", maintainOffset = True)
    lockHide("elbowCtrlL", rotate = False)
    # right shoulder
    makeControl("shoulderCtrlR", ctrlSize = 2, snapJoint = "ShoulderR", orientJoint = "ElbowR", ctrlNormal = (0, 1, 0))
    cmds.orientConstraint("shoulderCtrlR", "ShoulderR", maintainOffset = True)
    lockHide("shoulderCtrlR", rotate = False)
    #right elbow
    makeControl("elbowCtrlR", ctrlSize = 1.5, snapJoint = "ElbowR", orientJoint = "WristR", ctrlNormal = (0, 1, 0), constrain = "shoulderCtrlR")
    cmds.orientConstraint("elbowCtrlR", "ElbowR", maintainOffset = True)
    lockHide("elbowCtrlR", rotate = False)
    # 
    # Spine
    cmds.ikHandle(name = "ikSpine", solver = "ikSplineSolver", createCurve = True, startJoint = "Spine0", endEffector = "Spine" + str(sJointNum))
    ikCurve = cmds.ikHandle("ikSpine", query = True, curve = True)
    ikCurve = (ikCurve.split("|"))[3]
    cmds.rename(ikCurve, "ikSpineCurve")
    # Legs
    cmds.ikHandle(name = "ikLegL", startJoint = "HipL", endEffector = "AnkleL", solver = "ikSCsolver")
    cmds.ikHandle(name = "ikLegR", startJoint = "HipR", endEffector = "AnkleR", solver = "ikSCsolver")
    cmds.ikHandle(name = "ikFootL", startJoint = "AnkleL", endEffector = "FootL", solver = "ikSCsolver")
    cmds.ikHandle(name = "ikFootR", startJoint = "AnkleR", endEffector = "FootR", solver = "ikSCsolver")
    cmds.ikHandle(name = "ikToeL", startJoint = "FootL", endEffector = "ToeL", solver = "ikSCsolver")
    cmds.ikHandle(name = "ikToeR", startJoint = "FootR", endEffector = "ToeR", solver = "ikSCsolver")

    # Arms
    if cmds.checkBox("rollJointUi", query = True, value = True):
        cmds.ikHandle(name = "ikArmL", startJoint = "ShoulderL", endEffector = "ForearmRollL", solver = "ikSCsolver")
        effector = cmds.ikHandle("ikArmL", query = True, endEffector = True)
        cmds.rename(effector, "effectorIkArmL")
        pivot = cmds.joint("WristL", query = True, absolute = True, position = True)
        cmds.move(pivot[0], pivot[1], pivot[2], "effectorIkArmL.scalePivot", "effectorIkArmL.rotatePivot")
        cmds.move(pivot[0], pivot[1], pivot[2], "ikArmL")

        cmds.ikHandle(name = "ikArmR", startJoint = "ShoulderR", endEffector = "ForearmRollR", solver = "ikSCsolver")
        cmds.ikHandle("ikArmR", query = True, endEffector = True)
        cmds.rename(effector, "effectorIkArmR")
        pivot = cmds.joint("WristR", query = True, absolute = True, position = True)
        cmds.move(pivot[0], pivot[1], pivot[2], "effectorIkArmR.scalePivot", "effectorIkArmR.rotatePivot")
        cmds.move(pivot[0], pivot[1], pivot[2], "ikArmR")

    else:
        cmds.ikHandle(name = "ikArmL", startJoint = "ShoulderL", endEffector = "WristL", solver = "ikSCsolver")
        cmds.ikHandle(name = "ikArmR", startJoint = "ShoulderR", endEffector = "WristR", solver = "ikSCsolver")

    # Control Curves
    # Spine and hips
    sJointNum = (cmds.intSliderGrp("spineJointNumUi", query = True, value = True) - 1)
    makeControl("upperBackIKCtrl", ctrlSize = 4, snapJoint = "Spine" + str(sJointNum), ctrlNormal = (0, 1, 0))
    makeControl("lowerBackIKCtrl", ctrlSize = 4, snapJoint = "Root", ctrlNormal = (0, 1, 0))
    makeControl("backCtrl", ctrlSize = 5.5, snapJoint = "Root", ctrlNormal = (0, 1, 0))

    curveCVs = cmds.ls("ikSpineCurve.cv[:]", flatten = True)
    cmds.cluster(curveCVs[0], name = "spineLowCluster")

    curveCVs = cmds.ls("ikSpineCurve.cv[:]", flatten = True)
    cmds.cluster(curveCVs[-1], name = "spineUpCluster")

    cmds.parent("spineUpClusterHandle", "upperBackIKCtrl")
    cmds.orientConstraint("upperBackIKCtrl", "Spine" + str(sJointNum), maintainOffset = True)
    cmds.parent("spineLowClusterHandle", "lowerBackIKCtrl")
    cmds.parent(["upperBackIKCtrl", "lowerBackIKCtrl"], "backCtrl")
    cmds.parentConstraint("lowerBackIKCtrl", "Root",  maintainOffset = True)

    cmds.parent("backCtrl", "superMover")
    # fix bug with ik curve parent
    cmds.parent("ikSpineCurve", world = True)
    # Legs
    # knee pole vector
    makeControl("kneePVCtrlL", 0.5, "KneeL", None, ("z", 4))
    cmds.poleVectorConstraint("kneePVCtrlL", "ikLegL")
    #cmds.parent("kneePVCtrlL", "AnkleL")
    lockHide("kneePVCtrlL", translate = False)
    # Left foot
    makeControl("footCtrlL", ctrlSize = 2, snapJoint = "FootL", ctrlNormal = (0, 1, 0), ctrlScale = (0.8, 1, 1.7))
    cmds.parent(["ikLegL", "ikFootL", "ikToeL"], "footCtrlL")
    cmds.parent("footCtrlL", "superMover")
    # toe tip
    pos = cmds.joint("ToeL", query = True, absolute = True, position = True)
    cmds.group("ikLegL", "ikFootL", "ikToeL", name = "toeTipPivotL")
    cmds.move(pos[0], pos[1], pos[2], "toeTipPivotL.scalePivot", "toeTipPivotL.rotatePivot")
    # toe tap
    pos = cmds.joint("FootL", query = True, absolute = True, position = True)
    cmds.group("ikFootL", "ikToeL", name = "toeTapPivotL")
    cmds.move(pos[0], pos[1], pos[2], "toeTapPivotL.scalePivot", "toeTapPivotL.rotatePivot")
    # heel peel
    cmds.group("ikLegL", name = "heelPeelPivotL")
    cmds.move(pos[0], pos[1], pos[2], "heelPeelPivotL.scalePivot", "heelPeelPivotL.rotatePivot")
    # heel tap
    cmds.group("toeTipPivotL", name = "heelTapPivotL")
    jpos = cmds.joint("FootLockR", query = True, absolute = True, position = True)
    cmds.move(jpos[0], jpos[1], jpos[2], "heelTapPivotL.scalePivot", "heelTapPivotL.rotatePivot")

    # Right foot
    # knee pole vector
    makeControl("kneePVCtrlR", ctrlSize = 0.5, snapJoint = "KneeR", offset = ("z", 4))
    cmds.poleVectorConstraint("kneePVCtrlR", "ikLegR")
    #cmds.parent("kneePVCtrlR", "AnkleR")
    lockHide("kneePVCtrlR", translate = False)
    # right foot
    makeControl("footCtrlR", ctrlSize = 2, snapJoint = "FootR", ctrlNormal = (0, 1, 0), ctrlScale = (0.8, 1, 1.7))
    cmds.parent(["ikLegR", "ikFootR", "ikToeR"], "footCtrlR")
    cmds.parent("footCtrlR", "superMover")
    # toe tip
    pos = cmds.joint("ToeR", query = True, absolute = True, position = True)
    cmds.group("ikLegR", "ikFootR", "ikToeR", name = "toeTipPivotR")
    cmds.move(pos[0], pos[1], pos[2], "toeTipPivotR.scalePivot", "toeTipPivotR.rotatePivot")
    # toe tap
    pos = cmds.joint("FootR", query = True, absolute = True, position = True)
    cmds.group("ikFootR", "ikToeR", name = "toeTapPivotR")
    cmds.move(pos[0], pos[1], pos[2], "toeTapPivotR.scalePivot", "toeTapPivotR.rotatePivot")
    # heel peel
    cmds.group("ikLegR", name = "heelPeelPivotR")
    cmds.move(pos[0], pos[1], pos[2], "heelPeelPivotR.scalePivot", "heelPeelPivotR.rotatePivot")
    # heel tap
    cmds.group("toeTipPivotR", name = "heelTapPivotR")
    jpos = cmds.joint("FootLockR", query = True, absolute = True, position = True)
    cmds.move(jpos[0], jpos[1], jpos[2], "heelTapPivotR.scalePivot", "heelTapPivotR.rotatePivot")

    # Left Arm
    # elbow
    makeControl("elbowPoleCtrlL", ctrlSize = 0.5, snapJoint = "ElbowL", orientJoint ="ElbowL", offset = ("z", -4), ctrlNormal = (0, 0, 1))
    cmds.poleVectorConstraint("elbowPoleCtrlL", "ikArmL")
    #cmds.pointConstraint("ikArmL", "elbowCtrlL", maintainOffset = True, skip = "y")
    cmds.parent("elbowPoleCtrlL", "superMover")
    lockHide("elbowPoleCtrlL", translate = False)
    # wrist
    makeControl("wristCtrlL", ctrlSize = 2, snapJoint = "WristL", orientJoint ="ElbowL", ctrlNormal = (0, 1, 0))
    #lockHide("wristCtrlL", translate = False)
    cmds.pointConstraint("wristCtrlL", "ikArmL", maintainOffset = True)
    cmds.orientConstraint("wristCtrlL", "WristL", maintainOffset = True)
    cmds.orientConstraint("WristL", "wristCtrlL", maintainOffset = True)

    # Right Arm
    # elbow
    makeControl("elbowPoleCtrlR", ctrlSize = 0.5, snapJoint = "ElbowR", offset = ("z", -4), ctrlNormal = (0, 0, 1))
    cmds.poleVectorConstraint("elbowPoleCtrlR", "ikArmR")
    #cmds.pointConstraint("ikArmR", "elbowCtrlR", maintainOffset = True, skip = "y")
    cmds.parent("elbowPoleCtrlR", "superMover")
    lockHide("elbowPoleCtrlR", translate = False)
    # wrist
    makeControl("wristCtrlR", ctrlSize = 2, snapJoint = "WristR", orientJoint ="ElbowR", ctrlNormal = (0, 1, 0))
    #lockHide("wristCtrlR", translate = False)
    cmds.pointConstraint("wristCtrlR", "ikArmR", maintainOffset = True)
    cmds.orientConstraint("wristCtrlL", "WristR", maintainOffset = True)
    cmds.orientConstraint("WristR", "wristCtrlR", maintainOffset = True)

    # Finger FK controls
    numFingers = cmds.intSliderGrp("fingersNumUi", query = True, value = True)
    for i in range(1, numFingers):
        # left
        makeControl("FingerBaseCtrl" + str(i) + "L", ctrlSize = 0.5, snapJoint = "FingerBase" + str(i) + "L", 
                    orientJoint = "FingerMiddle" + str(i) + "L", ctrlNormal = (0, 1, 0), constrain = "elbowCtrlL")
        cmds.orientConstraint("FingerBaseCtrl" + str(i) + "L", "FingerBase" + str(i) + "L", maintainOffset = True)
        
        makeControl("FingerMiddleCtrl" + str(i) + "L", ctrlSize = 0.5, snapJoint = "FingerMiddle" + str(i) + "L", 
                    orientJoint = "FingerBase" + str(i) + "L", ctrlNormal = (0, 1, 0), constrain = "FingerBaseCtrl" + str(i) + "L")
        cmds.orientConstraint("FingerMiddleCtrl" + str(i) + "L", "FingerMiddle" + str(i) + "L", maintainOffset = True)
        
        makeControl("FingerEndCtrl" + str(i) + "L", ctrlSize = 0.5, snapJoint = "FingerEnd" + str(i) + "L", 
                    orientJoint = "FingerTip" + str(i) + "L", ctrlNormal = (0, 1, 0), constrain = "FingerMiddleCtrl" + str(i) + "L")
        cmds.orientConstraint("FingerEndCtrl" + str(i) + "L", "FingerEnd" + str(i) + "L", maintainOffset = True)
        
        #makeControl("FingerTipCtrl" + str(i) + "L", ctrlSize = 0.5, snapJoint = "FingerTip" + str(i) + "L", ctrlNormal = (1, 0, 0))

        # right
        makeControl("FingerBaseCtrl" + str(i) + "R", ctrlSize = 0.5, snapJoint = "FingerBase" + str(i) + "R", 
                    orientJoint = "FingerMiddle" + str(i) + "R", ctrlNormal = (0, 1, 0), constrain = "elbowCtrlR")
        cmds.orientConstraint("FingerBase" + str(i) + "R", "FingerBase" + str(i) + "R", maintainOffset = True)

        makeControl("FingerMiddleCtrl" + str(i) + "R", ctrlSize = 0.5, snapJoint = "FingerMiddle" + str(i) + "R", 
                    orientJoint = "FingerBase" + str(i) + "R", ctrlNormal = (0, 1, 0), constrain = "FingerBaseCtrl" + str(i) + "R")
        cmds.orientConstraint("FingerMiddleCtrl" + str(i) + "R", "FingerMiddle" + str(i) + "R", maintainOffset = True)

        makeControl("FingerEndCtrl" + str(i) + "R", ctrlSize = 0.5, snapJoint = "FingerEnd" + str(i) + "R", 
                    orientJoint = "FingerTip" + str(i) + "R", ctrlNormal = (0, 1, 0), constrain = "FingerMiddleCtrl" + str(i) + "R")
        cmds.orientConstraint("FingerEndCtrl" + str(i) + "R", "FingerEnd" + str(i) + "R", maintainOffset = True)

        #makeControl("FingerTipCtrl" + str(i) + "R", ctrlSize = 0.5, snapJoint = "FingerTip" + str(i) + "R", ctrlNormal = (1, 0, 0))
    
    # left thumb
    makeControl("ThumbBaseCtrlL", ctrlSize = 0.5, snapJoint = "ThumbBaseL", 
                orientJoint = "ThumbMidL", ctrlNormal = (0, 1, 0), constrain = "elbowCtrlL")
    cmds.orientConstraint("ThumbBaseCtrlL", "ThumbBaseL", maintainOffset = True)

    makeControl("ThumbMidCtrlL", ctrlSize = 0.5, snapJoint = "ThumbMidL", 
                orientJoint = "ThumbBaseL", ctrlNormal = (0, 1, 0), constrain = "ThumbBaseCtrlL")
    cmds.orientConstraint("ThumbMidCtrlL", "ThumbMidL", maintainOffset = True)

    makeControl("ThumbEndCtrlL", ctrlSize = 0.5, snapJoint = "ThumbEndL", 
                orientJoint = "ThumbMidL", ctrlNormal = (0, 1, 0), constrain = "ThumbMidCtrlL")
    cmds.orientConstraint("ThumbEndCtrlL", "ThumbEndL", maintainOffset = True)

    #makeControl("ThumbTipCtrlL", ctrlSize = 0.5, snapJoint = "ThumbTipL", ctrlNormal = (0, 0, 1))
    
    # right thumb
    makeControl("ThumbBaseCtrlR", ctrlSize = 0.5, snapJoint = "ThumbBaseR", 
                orientJoint = "ThumbMidR", ctrlNormal = (0, 1, 0), constrain = "elbowCtrlR")
    cmds.orientConstraint("ThumbBaseCtrlR", "ThumbBaseR", maintainOffset = True)

    makeControl("ThumbMidCtrlR", ctrlSize = 0.5, snapJoint = "ThumbMidR", 
                orientJoint = "ThumbBaseR", ctrlNormal = (0, 1, 0), constrain = "ThumbBaseCtrlR")
    cmds.orientConstraint("ThumbMidCtrlR", "ThumbMidR", maintainOffset = True)

    makeControl("ThumbEndCtrlR", ctrlSize = 0.5, snapJoint = "ThumbEndR", 
                orientJoint = "ThumbMidR", ctrlNormal = (0, 1, 0), constrain = "ThumbMidCtrlR")
    cmds.orientConstraint("ThumbEndCtrlR", "ThumbEndR", maintainOffset = True)

    #makeControl("ThumbTipCtrlR", ctrlSize = 0.5, snapJoint = "ThumbTipR", ctrlNormal = (0, 0, 1))

    # Finger IK controls
    ''' 
    ### this is totaly broken and wont make it into the rig before the assignment deadline ###
    for i in range(1, numFingers):
        cmds.ikHandle(name = "ikFinger" + str(i) + "L", startJoint = "IKJFingerBase" + str(i) + "L", 
                endEffector = "IKJFingerTip" + str(i) + "L", solver = "ikSCsolver")
        cmds.parent("ikFinger" + str(i) + "L", "FingerTipCtrl" + str(i) + "L")

        cmds.ikHandle(name = "ikFinger" + str(i) + "R", startJoint = "IKJFingerBase" + str(i) + "R", 
                endEffector = "IKJFingerTip" + str(i) + "R", solver = "ikSCsolver")
        cmds.parent("ikFinger" + str(i) + "R", "FingerTipCtrl" + str(i) + "R")

    cmds.ikHandle(name = "ikThumbL", startJoint = "IKJThumbBaseL", 
            endEffector = "IKJThumbTipL", solver = "ikSCsolver")
    cmds.parent("ikThumbL", "ThumbTipCtrlL")

    cmds.ikHandle(name = "ikThumbR", startJoint = "IKJThumbBaseR", 
            endEffector = "IKJThumbTipR", solver = "ikSCsolver")
    cmds.parent("ikThumbR", "ThumbTipCtrlR")
    

    # IK/FK switches
    # whole body
    # TODO: make full body IK work
    otherBones = ["Neck", "Jaw", "JawTip", "Head", "HeadTip"]
    for joint in (jointList):
        if "Spine" in joint:
            otherBones.append(joint)
    connectChainAttribute("Root", "backCtrl", "IK_Whole_Body")
    connectChainAttribute("Root", "backCtrl", "FK_Whole_Body", fkik = "FK", pos = "W1")
    # left arm
    connectChainAttribute("ShoulderL", "shoulderCtrlL", "IK_Left_Arm")
    connectChainAttribute("ShoulderL", "shoulderCtrlL", "FK_Left_Arm", fkik = "FK", pos = "W1")
    # right arm
    connectChainAttribute("ShoulderR", "shoulderCtrlR", "IK_Right_Arm")
    connectChainAttribute("ShoulderR", "shoulderCtrlR", "FK_Right_Arm", fkik = "FK", pos = "W1")
    # left leg
    connectChainAttribute("HipL", "hipFKCtrlL", "IK_Left_Leg")
    connectChainAttribute("HipL", "hipFKCtrlL", "FK_Left_Leg", fkik = "FK", pos = "W1")
    # right leg
    connectChainAttribute("HipR", "hipFKCtrlR", "IK_Right_Leg")
    connectChainAttribute("HipR", "hipFKCtrlR", "FK_Right_Leg", fkik = "FK", pos = "W1")
    '''

    # Connetct Attributes to controlers
    # toe tip
    cmds.addAttr("footCtrlL", longName = "toe_tip", attributeType = "float", min = 0, max = 90, defaultValue = 0)
    cmds.setAttr("footCtrlL.toe_tip", edit = True, keyable = True)
    cmds.connectAttr("footCtrlL.toe_tip", "toeTipPivotL.rx")

    cmds.addAttr("footCtrlR", longName = "toe_tip", attributeType = "float", min = 0, max = 90, defaultValue = 0)
    cmds.setAttr("footCtrlR.toe_tip", edit = True, keyable = True)
    cmds.connectAttr("footCtrlR.toe_tip", "toeTipPivotR.rx")

    # toe tap
    cmds.addAttr("footCtrlL", longName = "toe_tap", attributeType = "float", defaultValue = 0)
    cmds.setAttr("footCtrlL.toe_tap", edit = True, keyable = True)
    cmds.connectAttr("footCtrlL.toe_tap", "toeTapPivotL.rx")

    cmds.addAttr("footCtrlR", longName = "toe_tap", attributeType = "float", defaultValue = 0)
    cmds.setAttr("footCtrlR.toe_tap", edit = True, keyable = True)
    cmds.connectAttr("footCtrlR.toe_tap", "toeTapPivotR.rx")

    # heel peel
    cmds.addAttr("footCtrlL", longName = "heel_peel", attributeType = "float", min = 0, max = 100, defaultValue = 0)
    cmds.setAttr("footCtrlL.heel_peel", edit = True, keyable = True)
    cmds.connectAttr("footCtrlL.heel_peel", "heelPeelPivotL.rx")

    cmds.addAttr("footCtrlR", longName = "heel_peel", attributeType = "float", min = 0, max = 100, defaultValue = 0)
    cmds.setAttr("footCtrlR.heel_peel", edit = True, keyable = True)
    cmds.connectAttr("footCtrlR.heel_peel", "heelPeelPivotR.rx")

    # heel tap
    cmds.addAttr("footCtrlL", longName = "heel_tap", attributeType = "float", defaultValue = 0)
    cmds.setAttr("footCtrlL.heel_tap", edit = True, keyable = True)
    cmds.connectAttr("footCtrlL.heel_tap", "heelTapPivotL.rx")

    cmds.addAttr("footCtrlR", longName = "heel_tap", attributeType = "float", defaultValue = 0)
    cmds.setAttr("footCtrlR.heel_tap", edit = True, keyable = True)
    cmds.connectAttr("footCtrlR.heel_tap", "heelTapPivotR.rx")


def makeControl(ctrlName, ctrlSize = 1, snapJoint = None, orientJoint = None,
                offset = None, ctrlNormal = (0, 0, 0), ctrlScale = None, constrain = None):
    ctrlSize = ctrlSize * cmds.floatSliderGrp("rigScaleUi", query = True, value = True)
    cmds.circle(name = ctrlName, center = (0, 0, 0), normal = ctrlNormal, sweep = 360, radius = ctrlSize)
    if snapJoint:
        pos = cmds.joint(snapJoint, query = True, absolute = True, position = True)
        cmds.move(pos[0], pos[1], pos[2], ctrlName)
    if orientJoint:
        offsetName = ctrlName + "offset"
        cmds.group(ctrlName, name = offsetName)
        cmds.aimConstraint(orientJoint, offsetName, aimVector = (0, 1, 0), maintainOffset = False)
        cmds.aimConstraint(orientJoint, offsetName, edit = True, remove = True)
        if constrain:
            cmds.parentConstraint(constrain, offsetName, maintainOffset = True)
    if offset:
        cmds.select(ctrlName)
        if offset[0] == "x":
            cmds.move(offset[1], x = True)
        elif offset[0] == "y":
            cmds.move(offset[1], y = True)
        else:
            cmds.move(offset[1], z = True)
        cmds.select(clear = True)
    if ctrlScale:
        cmds.scale(ctrlScale[0], ctrlScale[1], ctrlScale[2], ctrlName)

    # set control colour
    if ctrlName[-1] == "L":
        cmds.setAttr(ctrlName + ".overrideEnabled", 1)
        cmds.setAttr(ctrlName + ".overrideColor", 6)
    elif ctrlName[-1] == "R":
        cmds.setAttr(ctrlName + ".overrideEnabled", 1)
        cmds.setAttr(ctrlName + ".overrideColor", 13)
    else:
        cmds.setAttr(ctrlName + ".overrideEnabled", 1)
        cmds.setAttr(ctrlName + ".overrideColor", 22)

    freezeTransforms(ctrlName)


def freezeTransforms(obj):
    cmds.makeIdentity(obj, apply = True, translate = True, rotate = True, scale = True)
    cmds.delete(obj, constructionHistory = True)


def lockHide(obj, translate = True, rotate = True, scale = True, vis = True):
    if translate:
        cmds.setAttr(obj + ".tx" ,lock = True, keyable = False, channelBox = False)
        cmds.setAttr(obj + ".ty" ,lock = True, keyable = False, channelBox = False)
        cmds.setAttr(obj + ".tz" ,lock = True, keyable = False, channelBox = False)
    if rotate:
        cmds.setAttr(obj + ".rx" ,lock = True, keyable = False, channelBox = False)
        cmds.setAttr(obj + ".ry" ,lock = True, keyable = False, channelBox = False)
        cmds.setAttr(obj + ".rz" ,lock = True, keyable = False, channelBox = False)
    if scale:
        cmds.setAttr(obj + ".sx" ,lock = True, keyable = False, channelBox = False)
        cmds.setAttr(obj + ".sy" ,lock = True, keyable = False, channelBox = False)
        cmds.setAttr(obj + ".sz" ,lock = True, keyable = False, channelBox = False)
    if vis:
        cmds.setAttr(obj + ".v" ,lock = True, keyable = False, channelBox = False)


def connectChainAttribute(topJoint, controlName, switchName, fkik = "IK", pos = "W0"):
    attribute = controlName + "." + switchName
    cmds.addAttr(controlName, longName = switchName, attributeType = "float", min = 0, max = 1, defaultValue = 0)
    cmds.setAttr(attribute, edit = True, keyable = True)

    jointList = cmds.listRelatives(topJoint, allDescendents = True, type = "joint")
    jointList.append(topJoint)
    for joint in jointList:
        cmds.connectAttr(attribute, joint + "_parentConstraint1." + fkik + "J" + joint + pos)


### Unused or obsolete functions ###

def orientJoints(name, direction):
    # ensure the X axis of the joint is lined up with the direction of bone
    # Commet is an example script that can help
    if direction == "end":
        cmds.setAttr("%s.jointOrientX" % name, 0)
        cmds.setAttr("%s.jointOrientY" % name, 0)
        cmds.setAttr("%s.jointOrientZ" % name, 0)


def squareControlCurve():
    cmds.circle(center = (0, 0, 0), normal = (0, 1, 0), sweep = 360,
            radius = 1, degree = 1, sections = 4)


def endJointOrient():
    cmds.setAttr("%s.jointOrientX" % name, 0)
    cmds.setAttr("%s.jointOrientY" % name, 0)
    cmds.setAttr("%s.jointOrientZ" % name, 0)
    # important to set end joint orient to 0


def align(src, dst):
    pos = cmds.xform(dst, query = True, translation = True, worldSpace = True)
    rot = cmds.xform(dst, query = True, rotation = True, worldSpace = True)
    cmds.select(src)
    cmds.move(pos[0], pos[1], pos[2])
    cmds.rotate(rot[0], rot[1], rot[2])


def pConstrainAndDetach(destination, source):
    cmds.parentConstraint(destination, source, weight = 1)
    cmds.parentConstraint(destination, source, edit = True, remove = True)

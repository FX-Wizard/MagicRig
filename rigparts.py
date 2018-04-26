import maya.cmds as cmds

from proxyObj import proxyObj
from ui import window
from .rignode import MrNode, MetaNode
from .Control import Control
from rigUtils import FkIkBlend, freezeTransforms, uniqueName, locator
from .StretchyIK import makeStretchyIK

#prefix = cmds.getAttr("MR_Root.prefix")

def proxyToJoint(proxy, parent=None):
    '''convert proxy to joint'''
    cmds.select(proxy)
    jointName = uniqueName(proxy.lstrip("p"))
    cmds.joint(name=jointName)
    cmds.ungroup(proxy)
    cmds.delete(proxy)
    cmds.makeIdentity(jointName, apply=True, translate=True, rotate=True, scale=True, jointOrient=True)
    #cmds.setAttr(jointName + ".drawStyle", 2)
    if parent:
        cmds.parent(jointName, parent)
    return jointName


def connectTo():
    ''' connect limb to another limb '''
    pass


def joint(name, parent=None):
    '''make joint and parent'''
    jointName = uniqueName(name)
    cmds.joint(name=jointName)
    #cmds.setAttr(jointName + ".drawStyle", 2)
    if parent:
        cmds.parent(jointName, parent)
    return jointName


#=============================================================================
# ROOT
#=============================================================================
class root(MetaNode, object):
    def __init__(self, name="root"):
        self.name = name
        self.setParent("MR_Root")
        self.addAttr("heirachyParent")
        self.addAttr("heirachyChild")
        self.proxy()


    def proxy(self):
        self.rootJoint = proxyObj("pRoot", (0, 14.5, 0))

    
    def toJoint(self):
        self.rootJoint = proxyToJoint(self.rootJoint)


    def control(self):
        pass
        #self.centerMassCtrl = Control("centerMass", scale=5.5, snapTo="Root")


#=============================================================================
# SPINE
#=============================================================================
class spine(MetaNode, object):
    ''' create new spine
    Args:
        spineJointNum (int) amount of joints in the spine
    '''
    def __init__(self, name, spineJointNum=4):
        self.name = name
        self.setParent("MR_Root")
        self.addAttr("heirachyParent")
        self.addAttr("heirachyChild")
        self.addAttr("spineJointNum", spineJointNum)
        
        self.sJointNum = spineJointNum

        self.proxy()


    def proxy(self):
        ''' make spine proxy '''
        self.spineList = []
        seperation = (7.1 / (self.sJointNum - 1))
        for i in range(self.sJointNum):
            new = proxyObj("pSpine" + str(i), (0, (seperation * i) + 15, 0, ))
            self.spineList.append(new)
        self.mover = locator("spineLoc")
        cmds.delete(cmds.parentConstraint(self.spineList[0], self.spineList[-1], self.mover))
        cmds.parent(self.spineList, self.mover)


    def toJoint(self, parent=None):
        ''' turn spine proxies to joints '''
        self.spineList[0] = proxyToJoint(self.spineList[0])

        for i in range(1, self.sJointNum):
            new = proxyToJoint(self.spineList[i], self.spineList[i - 1])
            self.spineList[i] = new

        self.topJoint = self.spineList[-1]
        self.bottomJoint = self.spineList[0]
        
        if parent:
            cmds.parent(self.bottomJoint, parent)

        # cleanup mover
        cmds.delete(self.mover)


    def control(self):
        ''' add spine controls '''
        cmds.ikHandle(name="ikSpine", solver="ikSplineSolver", createCurve=True,
                    startJoint=self.spineList[0], endEffector=self.spineList[-1])
        ikCurve = cmds.ikHandle("ikSpine", query=True, curve=True)
        ikCurve = (ikCurve.split("|"))[3]
        cmds.rename(ikCurve, "ikSpineCurve")

        #Control("upperBackIKCtrl", scale=4, snapTo="Spine" + str(sJointNum))
        #Control("lowerBackIKCtrl", scale=4, snapTo="Root")
        centerMassCtrl = Control("centerMass", scale=5.5, snapTo="Root")

        curveCVs = cmds.ls("ikSpineCurve.cv[:]", flatten=True)
        backCtrlList = []
        for i, CV in enumerate(curveCVs):
            cmds.cluster(CV, name="spine" + str(i) + "Cluster")
            back = Control("Back" + str(i), scale=4, snapTo=self.spineList[i], pointTo=self.spineList[i - 1])
            backCtrlList.append(back.ctrlName)
            cmds.parent("spine" + str(i) + "ClusterHandle", back.ctrlName)
            cmds.parent(back.ctrlOff, centerMassCtrl.ctrlName)

        for i in reversed(range(1, len(backCtrlList))):
            cmds.parent(backCtrlList[i], backCtrlList[i - 1])

        #cmds.parent("spine3ClusterHandle", "upperBackIKCtrl")
        #cmds.orientConstraint("upperBackIKCtrl", "Spine" + str(sJointNum), maintainOffset=True)
        #cmds.parent("spine0ClusterHandle", "lowerBackIKCtrl")

        # might not be needed
        #cmds.parentConstraint(prefix + "_Back0_ctrl", "Root", maintainOffset=True)

        cmds.parent("ikSpineCurve", world=True) # fix double translate
        #cmds.setAttr("ikSpineCurve.inheritsTransform", 0)


#=============================================================================
# LEG
#=============================================================================
class leg(MetaNode, object):
    ''' make new leg (human)
    Args:
        side = string "L" or "R"

        stretchy (bool) add stretchy limb

        numToes (int) number of toes 
    '''
    def __init__(self, name, side, stretchy, numToes):
        self.name = name
        self.setParent("MR_Root")
        self.addAttr("heirachyParent")
        self.addAttr("heirachyChild")
        self.addAttr("side", value=side, lock=True)
        self.addAttr("numToes", value=numToes, lock=True)

        self.side = side
        self.stretchy = stretchy
        self.numToes = numToes
        self.proxy()


    def proxy(self):
        ''' make leg proxy '''
        s = self.side
        # Leg
        self.hip = proxyObj("pHip" + s, (1.7, 14, 0))
        self.knee = proxyObj("pKnee" + s, (1.7, 8, 0), self.hip)
        self.ankle = proxyObj("pAnkle" + s, (1.7, 1.6, 0), self.knee)
        # Foot
        self.toe = proxyObj("pToe" + s, (1.7, 0, 2.3), self.ankle)
        self.toeTip = proxyObj("pToeTip" + s, (1.7, 0, 4), self.toe)
        self.footLock = locator("heelLoc" + s, (1.7, 0, -0.5))
        self.footInside = locator("footBankInside" + s, (1, 0, 2.3))
        self.footOutside = locator("footBankOutside" + s, (3, 0, 2.3))
        if self.numToes:
            self.toes = []
            space = 0.5
            start = space * (self.numToes / 2)
            for i in range(self.numToes):
                new = finger(self.side, self.toe, start - (space * i), form="toe")
                self.toes.append(new)

        self.mover = locator("legLoc" + s, snapTo=self.hip)
        cmds.parent(self.hip, self.mover)

    def toJoint(self, parent=None):
        ''' turn LEG proxies into joints '''
        self.hip = proxyToJoint(self.hip, parent=parent)
        self.knee = proxyToJoint(self.knee, self.hip)
        self.ankle = proxyToJoint(self.ankle, self.knee)
        self.toe = proxyToJoint(self.toe, self.ankle)
        self.toeTip = proxyToJoint(self.toeTip, self.toe)
        cmds.delete(self.footLock + "Shape")
        cmds.delete(self.footInside + "Shape")
        cmds.delete(self.footOutside + "Shape")
        if self.numToes:
            for toe in self.toes:
                toe.toJoint()
        # cleanup mover
        cmds.delete(self.mover)

        # Orient joints
        cmds.joint(self.hip, edit=True, orientJoint="xyz", secondaryAxisOrient="yup", zeroScaleOrient=True)
        cmds.joint(self.knee, edit=True, orientJoint="xyz", secondaryAxisOrient="yup", zeroScaleOrient=True)
        cmds.joint(self.ankle, edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)


    def control(self):
        ''' add leg controls '''
        prefix = cmds.getAttr("MR_Root.prefix")
        s = self.side
        # Legs
        masterCtrl = cmds.listConnections("MR_Root.masterControl")[0]
        ikLeg, legCtrl, legOffset = FkIkBlend([self.hip, self.knee, self.ankle], "Leg", 4, masterCtrl, side=s)

        # Ik foot
        cmds.ikHandle(name="ikFoot" + s, startJoint=self.ankle, endEffector=self.toe, solver="ikSCsolver")

        cmds.ikHandle(name="ikToe" + s, startJoint=self.toe, endEffector=self.toeTip, solver="ikSCsolver")

        # foot
        footCtrl = Control("footCtrl" + s, snapTo=self.toe, scale=[2, 2, 3])
        cmds.parent([legOffset, "ikFoot" + s, "ikToe" + s], footCtrl.ctrlName)
        # toe tip
        posTip = cmds.joint(self.toeTip, query=True, absolute=True, position=True)
        toeTipPivot = cmds.group(legOffset, "ikFoot" + s, "ikToe" + s, name="toeTipPivot" + s)
        cmds.move(posTip[0], 0, posTip[2], toeTipPivot + ".scalePivot", toeTipPivot + ".rotatePivot")
        # toe tap
        pos = cmds.joint(self.toe, query=True, absolute=True, position=True)
        toeTapPivot = cmds.group("ikFoot" + s, "ikToe" + s, name="toeTapPivot" + s)
        cmds.move(pos[0], pos[1], pos[2], toeTapPivot + ".scalePivot", toeTapPivot + ".rotatePivot")
        # heel peel
        heelPeelPivot = cmds.group(legOffset, name="heelPeelPivot" + s)
        cmds.move(posTip[0], posTip[1], posTip[2], heelPeelPivot + ".scalePivot", heelPeelPivot + ".rotatePivot")
        # heel tap
        heelTapPivot = cmds.group(toeTipPivot, name="heelTapPivot" + s)
        pos = cmds.getAttr(self.footLock + ".translate")[0]
        cmds.move(pos[0], pos[1], pos[2], heelTapPivot + ".scalePivot", heelTapPivot + ".rotatePivot")
        # foot bank
        cmds.parent(self.footInside, self.footOutside)
        cmds.parent(toeTipPivot, self.footInside)
        cmds.parent(self.footOutside, heelTapPivot)

        # Connetct Attributes to controlers
        # toe tip
        toeTipCtrl = Control("footBankCtrl" + s, direction="x", snapTo=self.toe, pointTo=self.toeTip, parent=footCtrl.ctrlName)
        cmds.addAttr(toeTipCtrl.ctrlName, longName="toe_tip", attributeType="float", min=0, max=90, defaultValue=0)
        cmds.setAttr(toeTipCtrl.ctrlName + ".toe_tip", edit=True, keyable=True)
        cmds.connectAttr(toeTipCtrl.ctrlName + ".rx", toeTipPivot + ".rx")

        # toe tap
        cmds.addAttr(footCtrl.ctrlName, longName="toe_tap", attributeType="float", defaultValue=0)
        cmds.setAttr(footCtrl.ctrlName + ".toe_tap", edit=True, keyable=True)
        cmds.connectAttr(footCtrl.ctrlName + ".toe_tap", "toeTapPivot%s.rx" % s)

        # heel peel
        cmds.addAttr(footCtrl.ctrlName, longName="heel_peel", attributeType="float", min=0, max=100, defaultValue=0)
        cmds.setAttr(footCtrl.ctrlName + ".heel_peel", edit=True, keyable=True)
        cmds.connectAttr(footCtrl.ctrlName + ".heel_peel", "heelPeelPivot%s.rx" % s)

        # heel tap
        cmds.addAttr(footCtrl.ctrlName, longName="heel_tap", attributeType="float", defaultValue=0)
        cmds.setAttr(footCtrl.ctrlName + ".heel_tap", edit=True, keyable=True)
        cmds.connectAttr(footCtrl.ctrlName + ".heel_tap", "heelTapPivot%s.rx" % s)

        # foot bank
        bankCond = cmds.shadingNode("condition", asUtility = True)
        cmds.setAttr(bankCond + ".operation", 4)
        cmds.connectAttr(toeTipCtrl.ctrlName + ".rz", bankCond + ".firstTerm")
        cmds.connectAttr(toeTipCtrl.ctrlName + ".rz", bankCond + ".colorIfFalse.colorIfFalseR")
        cmds.connectAttr(toeTipCtrl.ctrlName + ".rz", bankCond + ".colorIfTrue.colorIfTrueG")

        cmds.connectAttr(bankCond + ".outColor.outColorR", self.footInside + ".rz")
        cmds.connectAttr(bankCond + ".outColor.outColorG", self.footOutside + ".rz")

        if self.numToes:
            for toe in self.toes:
                toe.control()

        # stretchy IK
        if self.stretchy:
            makeStretchyIK(ikLeg, controlObj=legCtrl)


#=============================================================================
# HEAD
#=============================================================================
class head(MetaNode, object):
    ''' make new head
    Args:
        name -- name of head
    '''
    def __init__(self, name, parent=None):
        self.name = name
        self.setParent(parent="MR_Root")
        self.addAttr("heirachyParent")
        self.addAttr("heirachyChild")
        self.parent = parent
        self.proxy()


    def proxy(self):
        ''' make head proxy '''
        # Head
        self.neck = proxyObj("pNeck", (0, 23.5, 0))
        self.head = proxyObj("pHead", (0, 24.5, 0), self.neck)
        self.headTip = proxyObj("pHeadTip", (0, 28, 0), self.head)
        self.jaw = proxyObj("pJaw", (0, 25, 0.4), self.head)
        self.jawTip = proxyObj("pJawTip", (0, 24.4, 1.9), self.jaw)
        self.eyeL = proxyObj("pEyeL", (0.6, 26, 1.6), self.head)
        self.eyeR = proxyObj("pEyeR", (0.6, 26, 1.6), self.head)
        
        self.mover = locator("headLoc", snapTo=self.neck)
        cmds.parent(self.neck, self.head, self.headTip, self.jaw,
                    self.jawTip, self.eyeL, self.eyeR, self.mover)


    def toJoint(self, parent=None):
        ''' turn head proxies to joints '''
        self.neck = proxyToJoint(self.neck, parent)
        self.head = proxyToJoint(self.head, self.neck)
        self.headTip = proxyToJoint(self.headTip, self.head)
        self.jaw = proxyToJoint(self.jaw, self.head)
        self.jawTip = proxyToJoint(self.jawTip, self.jaw)
        self.eyeL = proxyToJoint(self.eyeL, self.head)
        self.eyeR = proxyToJoint(self.eyeR, self.head)
        # cleanup mover
        cmds.delete(self.mover)


    def control(self):
        ''' add head controls '''
        headCtrl = Control("head", scale=2, snapTo=self.headTip, pointTo=self.headTip)
        pos = cmds.joint(self.neck, query=True, absolute=True, position=True)
        cmds.move(pos[0], pos[1], pos[2], headCtrl.ctrlName + ".scalePivot", headCtrl.ctrlName + ".rotatePivot")
        cmds.parentConstraint(headCtrl.ctrlName, self.neck, maintainOffset=True)


    def connect(self, parent):
        #cmds.setAttr(self.headNode.name + ".heirachyParent", parent)
        cmds.parent(self.neck, parent)


#=============================================================================
# ARM
#=============================================================================
class arm(MetaNode, object):
    ''' make new head
    Args:
    name -- name of arm
    side -- (string) "L" or "R"
    numFingers -- (int) number of fingers
    armRoll -- (bool) add arm roll joint
    stretchy -- (bool) add stretchy limb
    '''
    def __init__(self, name, side, numFingers, armRoll, stretchy):
        self.name = name
        self.setParent("MR_Root")
        self.addAttr("heirachyParent")
        self.addAttr("heirachyChild")
        self.addAttr("side", value=side, lock=True)
        self.addAttr("numFingers", value=numFingers, lock=True)

        self.side = side
        self.numFingers = numFingers
        self.armRoll = armRoll
        self.stretchy = stretchy
        self.proxy()

    def proxy(self):
        ''' make spine proxy '''
        s = self.side
        # Arm
        self.clavicle = proxyObj("pClavicle" + s, (1.25, 22.5, 0))
        self.shoulder = proxyObj("pShoulder" + s, (3, 22.5, 0), self.clavicle)
        self.elbow = proxyObj("pElbow" + s, (6.4, 22.5, 0), self.shoulder)
        self.wrist = proxyObj("pWrist" + s, (10, 22.5, 0), self.elbow)
        
        # Hand
        # thumb
        self.thumb = finger(self.side, self.wrist, 11, form="Thumb")
        # fingers
        self.fingers = []
        space = 0.5
        start = space * (self.numFingers / 2)
        for i in range(1, self.numFingers):
            new = finger(self.side, self.wrist, start - (space * i))
            self.fingers.append(new)

        self.mover = locator("armLoc" + s, snapTo=self.clavicle)
        cmds.parent(self.clavicle, self.shoulder, self.elbow, self.wrist, self.mover)


    def toJoint(self, parent=None):
        ''' turn arm proxies to joints '''
        s = self.side

        # Arms
        self.clavicle = proxyToJoint(self.clavicle, parent)
        self.shoulder = proxyToJoint(self.shoulder, self.clavicle)
        self.elbow = proxyToJoint(self.elbow, self.shoulder)
        self.wrist = proxyToJoint(self.wrist)

        # Arm roll joint
        if self.armRoll:
            self.forearmRoll = joint(name="ForearmRoll" + self.side)
            cmds.delete(cmds.parentConstraint([self.elbow, self.wrist], self.forearmRoll))
            cmds.parent(self.forearmRoll, self.elbow)
            cmds.parent(self.wrist, self.forearmRoll)
        else:
            cmds.parent(self.wrist, self.elbow)

        # Hand bone
        cmds.select(self.wrist, replace=True)
        self.hand = joint(name="Hand" + self.side)
        #jointList.append("HandL")

        # Fingers
        for finger in self.fingers:
            finger.toJoint()

        self.thumb.toJoint()

        # Orient joints
        if s == "L":
            cmds.joint(self.clavicle, edit=True, orientJoint="xyz", secondaryAxisOrient="ydown", children=True)
        else:
            cmds.joint(self.clavicle, edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True)

        # cleanup mover
        cmds.delete(self.mover)


    def control(self):
        ''' add arm controls '''
        s = self.side
        # Clavicle
        ClavicleCtrl = Control("ClavicleCtrl" + s, scale=0.5, direction="x", snapTo=self.shoulder, moveTo=["y", 24])
        cmds.ikHandle(name="clavicleIk" + s, startJoint=self.clavicle, endEffector=self.shoulder, solver="ikRPsolver")
        cmds.pointConstraint(ClavicleCtrl.ctrlName, "clavicleIk" + s, maintainOffset=True)

        # Arms
        masterCtrl = cmds.listConnections("MR_Root.masterControl")[0]
        ikArm, armCtrl, armOffset = FkIkBlend([self.shoulder, self.elbow, self.wrist], "Arm", -4, masterCtrl, side=s)

        if self.armRoll:
            # connect arm roll
            div_armRoll = cmds.shadingNode("multiplyDivide", asUtility = True, name = cmds.getAttr("MR_Root.prefix") + "_div_armRoll" + s)
            cmds.setAttr(div_armRoll + ".operation", 2)
            cmds.connectAttr(ikArm + ".rotateX", div_armRoll + ".input1X")
            cmds.setAttr(div_armRoll + ".input2X", 2)
            cmds.connectAttr(div_armRoll + ".outputX", "ForearmRoll%s.rotateX" % s)

        # Finger FK controls
        for finger in self.fingers:
            finger.control()

        self.thumb.control()

        # stretchy IK
        if self.stretchy:
            makeStretchyIK(ikArm, controlObj=armCtrl)


#=============================================================================
# Quadrudped Leg
#=============================================================================
class quadLeg(MetaNode, object):
    def __init__(self, name, side, numToes=0):
        self.name = name
        self.setParent(parent="MR_Root")
        self.addAttr("heirachyParent")
        self.addAttr("heirachyChild")
        self.addAttr("side", value=side, lock=True)
        self.addAttr("numToes", value=numToes, lock=True)

        self.side = side
        self.numToes = numToes
        
        #self.stretchy = stretchy
        self.proxy()

    
    def proxy(self):
        s = self.side
        self.hip = proxyObj("pHip" + s, (2.4, 14, -8))
        self.knee = proxyObj("pKnee" + s, (2.4, 8.5, -8.8), self.hip)
        self.ankle = proxyObj("pAnkle" + s, (2.4, 4.5, -11), self.knee)
        self.foot = proxyObj("pFoot" + s, (2.4, 1.6, -10), self.ankle)
        self.toe = proxyObj("pToe" + s, (2.4, 0.9, -6), self.foot)

        self.mover = locator("locQuadLeg" + s, snapTo=self.hip)
        cmds.parent(self.hip, self.knee, self.ankle, self.foot,
                    self.toe, self.mover)
        if "ront" in s:
            cmds.move(8, self.mover, moveZ=True)


    def toJoint(self, parent=None):
        self.parent = parent
        # convert proxies to joints
        self.hip = proxyToJoint(self.hip, self.parent)
        self.knee = proxyToJoint(self.knee, self.hip)
        self.ankle = proxyToJoint(self.ankle, self.knee)
        self.foot = proxyToJoint(self.foot, self.ankle)
        self.toe = proxyToJoint(self.toe, self.foot)

        # orient joint
        cmds.joint(self.hip, edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)

        # Clean up
        cmds.ungroup(self.mover)
        cmds.delete(self.mover)


    def control(self):
        s = self.side
        # IK setup
        upperLegIk = cmds.ikHandle(name="upperLegIk" + s, startJoint=self.hip, endEffector=self.ankle, solver="ikRPsolver")[0]
        lowerLegIK = cmds.ikHandle(name="lowerLegIK" + s, startJoint=self.ankle, endEffector=self.foot, solver="ikSCsolver")[0]
        footIK = cmds.ikHandle(name="footIK" + s, startJoint=self.foot, endEffector=self.toe, solver="ikSCsolver")[0]
        # Controls
        ankleCtrl = Control("ankleCtrl" + s, snapTo=self.ankle)
        cmds.parent(lowerLegIK, footIK, ankleCtrl.ctrlName)
        footCtrl = Control("footCtrl" + s, snapTo=self.foot)
        cmds.parent(footIK, footCtrl.ctrlName)
        legIkCtrl = Control("legIkCtrl" + s, scale=[2, 1, 2.7], snapTo=self.toe, moveTo=("Y", 0))
        cmds.parent(upperLegIk, legIkCtrl.ctrlName)

        hipCtrl = Control("hip" + s, shape="sphere", snapTo=self.hip, scale=2)
        if self.parent:
            hipIk = cmds.ikHandle(name="hipIK" + s, startJoint=self.parent, endEffector=self.hip, solver="ikSCsolver")[0]
            cmds.parent(hipCtrl)
        else:
            cmds.parent(self.hip, hipCtrl.ctrlName)


#=============================================================================
# TAIL
#=============================================================================
class tail(MetaNode, object):
    ''' Create new tail rig
    Kwargs:
        numJoints (int) number of joints in the tail
    '''
    def __init__(self, name, numJoints=4):
        self.name = name
        self.setParent("MR_Root")
        self.addAttr("heirachyParent")
        self.addAttr("heirachyChild")
        self.addAttr("numJoints", value=numJoints)
        self.numJoints = numJoints
        self.proxy()


    def proxy(self):
        ''' make tail proxy '''
        self.tailJointList = []
        self.mover = locator("tailLoc")
        for i in range(self.numJoints):
            new = proxyObj("pTail%s" % i, move=(0, 0, i * -1.5))
            self.tailJointList.append(new)
            cmds.parent(new, self.mover)


    def toJoint(self, parent=None):
        ''' turn tail proxies into joints '''
        if parent:
            self.parent = parent
        else:
            self.parent = "Root"
        #self.tailJointList.append(self.parent)
        # convert to joints
        self.tailJointList[0] = proxyToJoint(self.tailJointList[0])
        cmds.duplicate(self.tailJointList[0], name="FKJ_" + self.tailJointList[0], parentOnly=True)
        cmds.duplicate(self.tailJointList[0], name="IKJ_" + self.tailJointList[0], parentOnly=True)
        for i in range(1, len(self.tailJointList)):
            new = proxyToJoint(self.tailJointList[i], self.tailJointList[i - 1])
            self.tailJointList[i] = new
            cmds.duplicate(new, name="FKJ_" + new, parentOnly=True)
            cmds.duplicate(new, name="IKJ_" + new, parentOnly=True)

        for i in range(1, len(self.tailJointList)):
            cmds.parent("FKJ_" + self.tailJointList[i], "FKJ_" + self.tailJointList[i - 1])
            cmds.parent("IKJ_" + self.tailJointList[i], "IKJ_" + self.tailJointList[i - 1])


    def control(self):
        # FK
        tailCtrl = Control("tailFK", snapTo=self.tailJointList[0], pointTo=self.tailJointList[1], parent=self.parent)
        cmds.parent("FKJ_" + self.tailJointList[0], tailCtrl.ctrlName)
        for i, joint in enumerate(self.tailJointList, start=1):
            tailCtrl = Control("tailFK", snapTo=joint, pointTo=self.tailJointList[i -1], parent=self.tailJointList[i - 1])
            cmds.parent("FKJ_" + self.tailJointList[i], tailCtrl.ctrlName)
        # IK


#=============================================================================
# FINGER
#=============================================================================
class finger(object):
    def __init__(self, side, parent, pos, form="Finger"):
        '''make new finger or toe
        form (string) "thumb", "toe", default="finger"
        '''
        self.parent = parent
        self.side = side
        self.form = form
        self.proxy(form)
        self.position(pos)


    def proxy(self, form):
        #if self.form == "toe":
        #    y = 0
        #else:
        #    y = 22.5
        self.base = proxyObj("p%sBase%s" % (form, self.side), (12, 0, 0), self.parent, radius=0.2)
        self.mid = proxyObj("p%sMid%s" % (form, self.side), (12.5, 0, 0), self.base, radius=0.2)
        self.end = proxyObj("p%sEnd%s" % (form, self.side), (13, 0, 0), self.mid, radius=0.2)
        self.tip = proxyObj("p%sTip%s" % (form, self.side), (13.5, 0, 0), self.end, radius=0.2)
        
        self.mover = locator("loc%s%s" % (self.form, self.side), snapTo=self.base)
        cmds.parent(self.base, self.mid, self.end, self.tip, self.mover)
        cmds.delete(cmds.parentConstraint(self.parent, self.mover))
        #self.name = self.base.replace("Base", "") # dont remember what this is for?


    def toJoint(self):
        self.parent = self.parent.lstrip("p")
        self.base = proxyToJoint(self.base, self.parent)
        self.mid = proxyToJoint(self.mid, self.base)
        self.end = proxyToJoint(self.end, self.mid)
        self.tip = proxyToJoint(self.tip, self.end)
        # cleanup
        #cmds.ungroup(self.mover, absolute=True)
        cmds.delete(self.mover)


    def control(self):
        BaseCtrl = Control(self.base, scale=0.5, snapTo=self.base, pointTo=self.mid,
            parent=self.parent, direction="z", lockChannels=["s", "t"], hideChannels=["s", "t"])
        cmds.orientConstraint(BaseCtrl.ctrlName, self.base, maintainOffset=True)

        MidCtrl = Control(self.mid, scale=0.5, snapTo=self.mid, pointTo=self.base,
            parent=BaseCtrl.ctrlName, direction="z", lockChannels=["s", "t"], hideChannels=["s", "t"])
        cmds.orientConstraint(MidCtrl.ctrlName, self.mid, maintainOffset=True)

        EndCtrl = Control(self.end, scale=0.5, snapTo=self.end, pointTo=self.mid,
            parent=MidCtrl.ctrlName, direction="z", lockChannels=["s", "t"], hideChannels=["s", "t"])
        cmds.orientConstraint(EndCtrl.ctrlName, self.end, maintainOffset=True)
        
        # Finger IK controls
        '''
        for i in range(1, self.numFingers):
            cmds.ikHandle(name="ikFinger" + str(i) + s, startJoint="IKJFingerBase" + str(i) + s,
                    endEffector="IKJFingerTip" + str(i) + s, solver="ikSCsolver")
            cmds.parent("ikFinger" + str(i) + s, "FingerTipCtrl" + str(i) + s)
        cmds.ikHandle(name="ikThumb" + s, startJoint="IKJThumbBase" + s,
                endEffector="IKJThumbTip" + s, solver="ikSCsolver")
        cmds.parent("ikThumb" + s, "ThumbTipCtrl" + s)
        '''


    def position(self, pos):
        if self.form == "Finger":
            cmds.move(2, self.mover, x=True, relative=True)
            cmds.move(pos, self.mover, z=True, worldSpace=True)
        elif self.form == "toe":
            p = cmds.getAttr(self.parent + ".translate")[0]
            cmds.move(p[0], p[1], p[2], self.mover, worldSpace=True, absolute=True)
            cmds.rotate(-90, self.mover, rotateY=True)
            cmds.move(pos, self.mover, x=True)
        elif "R" in self.base[-3:]:
            cmds.rotate(90, self.mover, rotateY=True)
            cmds.move(pos, self.mover, x=True, worldSpace=True)
        else:
            cmds.rotate(-90, self.mover, rotateY=True)
            cmds.move(pos, self.mover, x=True, worldSpace=True)


#=============================================================================
# RIBBON
#=============================================================================
class ribbon(object):
    ''' create new ribbon spine 
    Args:
        name (string) name of ribbon
    Kwargs:
        length (int) length and of the ribbon (default 10)
    '''
    def __init__(self, name, length=10):
        ratio = length / 2
        nurbsPlane = cmds.nurbsPlane(name=name + "Ribbon", pivot=[0, 0, 0], axis=[0, 1, 0], width=2,
                lengthRatio=ratio, patchesU=1, patchesV=ratio, constructionHistory=False)[0]

        for i in range(1, length, 2):
            self.createFollicle(nurbsPlane, name + "RibFolGrp", 0.5, i / 10.0)


        # Blend Shape
        cmds.duplicate(nurbsPlane, name=nurbsPlane + "_blendShp")
        cmds.blendShape(nurbsPlane + "_blendShp", nurbsPlane, name=nurbsPlane + "_blendNode")
        cmds.setAttr(nurbsPlane + "_blendNode." + nurbsPlane + "_blendShp", 1)

        # Wire Deformer
        # Get ribbon blend shape location
        startPos = cmds.xform(nurbsPlane + "_blendShp.cv[0][0]", query=True, translation=True)
        midPos = cmds.objectCenter(nurbsPlane + "_blendShp")
        endPos = cmds.xform(nurbsPlane + "_blendShp.cv[0][7]", query=True, translation=True)
        # Create curve
        wire = cmds.curve(d=2, p=[(midPos[0], midPos[1], startPos[2]),
                         (midPos[0], midPos[1], midPos[2]),
                         (midPos[0], midPos[1], endPos[2])],
                         k=[0, 0, 1, 1], name=name + "Wire")
        cmds.wire(nurbsPlane + "_blendShp", w=name + "Wire", dropoffDistance=[0, 20])
        
        # Clusters
        CstrBtm, CstrBtmHand = cmds.cluster(wire + ".cv[0:1]", relative=True, name=name + "CstrBtm")
        CstrMid, CstrMidHand = cmds.cluster(wire + ".cv[1]", relative=True, name=name + "CstrMid")
        CstrTop, CstrTopHand = cmds.cluster(wire + ".cv[1:2]", relative=True, name=name + "CstrTop")
        ClusterGrp = cmds.group(CstrBtmHand, CstrMidHand, CstrTopHand, name=name + "ClusterGrp")
        
        cmds.percent(name + "CstrBtm", wire + ".cv[1]", value=0.5)
        cmds.percent(name + "CstrTop", wire + ".cv[1]", value=0.5)
        #TODO: need to move transforms to end of nurbs plane
        #cmds.move(0, 0, 2.5, "spineCstrBtmHandle.scalePivot", "spineCstrBtmHandle.rotatePivot", relative=True)
        # Controlls
        topCtrl = Control("topCtrl", snapTo=startPos, direction="x")
        cmds.connectAttr(topCtrl.ctrlName + ".translate", name + "CstrTopHandle.translate", force=True)
        cmds.connectAttr(topCtrl.ctrlName + ".rotate", name + "CstrTopHandle.rotate", force=True)
        cmds.connectAttr(topCtrl.ctrlName + ".scale", name + "CstrTopHandle.scale", force=True)
        midCtrl = Control("midCtrl", direction="x")
        cmds.connectAttr(midCtrl.ctrlName + ".translate", name + "CstrMidHandle.translate", force=True)
        cmds.connectAttr(midCtrl.ctrlName + ".rotate", name + "CstrMidHandle.rotate", force=True)
        cmds.connectAttr(midCtrl.ctrlName + ".scale", name + "CstrMidHandle.scale", force=True)
        baseCtrl = Control("baseCtrl", snapTo=endPos, direction="x")
        cmds.connectAttr(baseCtrl.ctrlName + ".translate", name + "CstrBtmHandle.translate", force=True)
        cmds.connectAttr(baseCtrl.ctrlName + ".rotate", name + "CstrBtmHandle.rotate", force=True)
        cmds.connectAttr(baseCtrl.ctrlName + ".scale", name + "CstrBtmHandle.scale", force=True)
        cmds.pointConstraint(topCtrl.ctrlName, baseCtrl.ctrlName, midCtrl.ctrlName, name="midCtrl_pointCons")
        ctrlGroup = cmds.group(topCtrl.ctrlName, midCtrl.ctrlName, baseCtrl.ctrlName, name=name + "ctrlGroup")
        # Twist Deformer
        cmds.nonLinear(nurbsPlane + "_blendShp", type="twist")
        cmds.rename(name + "TwistHandle") # fix for nonLinear name arg bug
        cmds.setAttr(name + "TwistHandle.rotateX", -90)
        cmds.connectAttr(topCtrl.ctrlName + ".rotateZ", name + "TwistHandle.endAngle", force=True)
        cmds.connectAttr(baseCtrl.ctrlName + ".rotateZ", name + "TwistHandle.startAngle", force=True)
        cmds.setAttr(topCtrl.ctrlName + ".rotateOrder", 2)
        cmds.setAttr(baseCtrl.ctrlName + ".rotateOrder", 2)
        cmds.reorderDeformers("wire1", "twist1", "spineRibbon_blendShp") #ITS NOT WORKING
        # Global scale
        cmds.group(ClusterGrp, wire, name + "Ribbon_blendShp", name + "WireBaseWire", name + "RibFolGrp", name + "TwistHandle", name=name + "nodes")
        cmds.group(nurbsPlane, ctrlGroup, name=name + "GlobalMove")
        cmds.group(name + "nodes", name + "GlobalMove", name=nurbsPlane + "Master")
        folGrp = cmds.ls("spineRibFolGrp", dag=True, exactType="transform")
        jntList = []
        for i in range(1, len(folGrp)):
            fol = folGrp[i]
            cmds.scaleConstraint(name + "GlobalMove", fol, name=fol + "_sclCon")
            # Make joints
            cmds.select(fol)
            newJnt = cmds.joint(name = name + "joint" + fol[-1], scaleCompensate=True)
            jntList.append(newJnt)
        # Squash and stretch
        curveInfo = cmds.arclen(wire, constructionHistory=True)
        cmds.circle(name=name + "GlobalCtrl", center=[2, 0, 0], normal=[0, 1, 0], sweep=360, radius=0.5, constructionHistory=False)
        cmds.circle(name=name + "GlobalCtrl", center=[-2, 0, 0], normal=[0, 1, 0], sweep=360, radius=0.5, constructionHistory=False)
        cmds.parent(name + "GlobalCtrl1Shape", name + "GlobalCtrl")
        cmds.parent("spineGlobalMove", name + "GlobalCtrl")
        cmds.addAttr(name + "GlobalCtrl", longName = "Squash_Stretch", attributeType="bool", defaultValue=0)
        cmds.setAttr((name + "GlobalCtrl" + "." +  "Squash_Stretch"), edit=True, keyable=True)

        condition1 = cmds.shadingNode("condition", asUtility=True, name=name + "_cond1")
        cmds.setAttr(condition1 + ".secondTerm", 1)
        cmds.connectAttr((name + "GlobalCtrl" + "." +  "Squash_Stretch"), condition1 + ".firstTerm", force=True)
        divide1 = cmds.shadingNode("multiplyDivide", asUtility=True, name=name + "_div1_len")
        divide2 = cmds.shadingNode("multiplyDivide", asUtility=True, name=name + "_div2_vol")
        cmds.setAttr(divide1 + ".operation", 2)
        cmds.setAttr(divide2 + ".operation", 2)
        cmds.connectAttr((curveInfo + ".arcLength"), (divide1 + ".input1X"), force=True)
        cmds.setAttr((divide1 + ".input2X"), length)
        cmds.setAttr(divide2 + ".input1X", 1)
        cmds.connectAttr((divide1 + ".outputX"), (divide2 + ".input2X"), force=True)
        cmds.connectAttr((divide2 + ".outputX"), (condition1 + ".colorIfTrueR"), force=True)
        for jnt in jntList:
            cmds.connectAttr((condition1 + ".outColorR"), (jnt + ".scaleZ"), force=True)
            cmds.connectAttr((condition1 + ".outColorR"), (jnt + ".scaleY"), force=True)


    def createFollicle(self, surfaceName, folGroup, u, v):
        ''' create new follicle on nurbs surface '''
        follicleShape = cmds.createNode("follicle")
        follicleName =  follicleShape.replace("Shape", "")
        # Connect Attributes
        cmds.connectAttr(surfaceName + ".worldMatrix[0]", follicleShape + ".inputWorldMatrix", force=True)
        cmds.connectAttr(surfaceName + ".local", follicleShape + ".inputSurface", force=True)
        cmds.connectAttr(follicleShape + ".outRotate", follicleName + ".rotate", force=True)
        cmds.connectAttr(follicleShape + ".outTranslate", follicleName + ".translate", force=True)
        # Position On Plane
        cmds.setAttr(follicleShape + ".parameterU", u)
        cmds.setAttr(follicleShape + ".parameterV", v)
        # Group
        if cmds.objExists(folGroup):
            cmds.parent(follicleName, folGroup)
        else:
            cmds.group(follicleName, name=folGroup)

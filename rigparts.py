import maya.cmds as cmds

from proxyObj import proxyObj
from ui import window
from .rignode import MrNode
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


def joint(name, parent=None):
    '''make joint and parent'''
    jointName = uniqueName(name)
    cmds.joint(name=jointName)
    #cmds.setAttr(jointName + ".drawStyle", 2)
    if parent:
        cmds.parent(jointName, parent)
    return jointName


# biped
#=============================================================================
# ROOT
#=============================================================================
class root(object):
    def __init__(self):
        self.rootNode = MrNode("rootNode", parent="MR_Root")
        self.rootNode.addAttr("heirachyParent")
        self.rootNode.addAttr("heirachyChild")
        self.proxy()


    def proxy(self):
        self.rootJoint = proxyObj("pRoot", (0, 14.5, 0))

    
    def toJoint(self):
        self.rootJoint = proxyToJoint(self.rootJoint.name)


    def control(self):
        pass
        #self.centerMassCtrl = Control("centerMass", scale=5.5, snapTo="Root")


#=============================================================================
# SPINE
#=============================================================================
class spine(object):
    ''' create new spine
    Args:
        spineJointNum (int) amount of joints in the spine
    '''
    def __init__(self, spineJointNum):
        self.spineNode = MrNode("spineNode", parent="MR_Root")
        self.spineNode.addAttr("heirachyParent")
        self.spineNode.addAttr("heirachyChild")
        self.spineNode.addAttr("spineJointNum", spineJointNum)
        
        self.sJointNum = spineJointNum

        self.proxy()


    def proxy(self):
        ''' make spine proxy '''
        self.spineList = []
        seperation = (7.1 / (self.sJointNum - 1))
        for i in range(self.sJointNum):
            new = proxyObj("pSpine" + str(i), (0, (seperation * i) + 15, 0, ))
            self.spineList.append(new.name)


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


    def control(self):
        ''' add spine controls '''
        sJointNum = cmds.getAttr("spineNode.spineJointNum") - 1
        cmds.ikHandle(name="ikSpine", solver="ikSplineSolver", createCurve=True,
                    startJoint="Spine0", endEffector="Spine" + str(sJointNum))
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
            back = Control("Back" + str(i), scale=4, snapTo="Spine" + str(i))
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
class leg(object):
    ''' make new leg (human)
    Args:
        side = string "L" or "R"

        stretchy (bool) add stretchy limb
    '''
    def __init__(self, side, stretchy, numToes):
        self.legNode = MrNode("legNode" + side, parent="spineNode")
        self.legNode.addAttr("heirachyParent")
        self.legNode.addAttr("heirachyChild")
        self.legNode.addAttr("side", value=side, lock=True)

        self.side = side
        self.stretchy = stretchy
        self.numToes = numToes
        self.proxy()


    def proxy(self):
        ''' make leg proxy '''
        s = self.side
        # Leg
        self.hip = proxyObj("pHip" + s, (1.7, 14, 0))
        self.knee = proxyObj("pKnee" + s, (1.7, 8, 0), self.hip.name)
        self.ankle = proxyObj("pAnkle" + s, (1.7, 1.6, 0), self.knee.name)
        # Foot
        self.toe = proxyObj("pToe" + s, (1.7, 0, 2.3), self.ankle.name)
        self.toeTip = proxyObj("pToeTip" + s, (1.7, 0, 4), self.toe.name)
        self.footLock = locator("heelLoc" + s, (1.7, 0, -0.5))
        self.footInside = locator("footBankInside" + s, (1, 0, 2.3))
        self.footOutside = locator("footBankOutside" + s, (3, 0, 2.3))
        if self.numToes:
            self.toes = []
            space = 0.5
            start = space * (self.numToes / 2)
            for i in range(self.numToes):
                new = finger(self.side, self.toe.name, start - (space * i), form="toe")
                self.toes.append(new)

    def toJoint(self, parent=None):
        ''' turn LEG proxies into joints '''
        self.hip = proxyToJoint(self.hip.name)
        self.knee = proxyToJoint(self.knee.name, self.hip)
        self.ankle = proxyToJoint(self.ankle.name, self.knee)
        self.toe = proxyToJoint(self.toe.name, self.ankle)
        self.toeTip = proxyToJoint(self.toeTip.name, self.toe)
        cmds.delete(self.footLock + "Shape")
        cmds.delete(self.footInside + "Shape")
        cmds.delete(self.footOutside + "Shape")
        if self.numToes:
            for toe in self.toes:
                toe.toJoint()

        if parent:
            cmds.parent(self.hip, parent)

        # Orient joints
        cmds.joint(self.hip, edit=True, orientJoint="xyz", secondaryAxisOrient="yup", zeroScaleOrient=True)
        cmds.joint(self.knee, edit=True, orientJoint="xyz", secondaryAxisOrient="yup", zeroScaleOrient=True)
        cmds.joint(self.ankle, edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)


    def control(self):
        ''' add leg controls '''
        prefix = cmds.getAttr("MR_Root.prefix")
        s = self.side
        # Legs
        ikLeg, legCtrl, legOffset = FkIkBlend([self.hip, self.knee, self.ankle], "Leg", 4, cmds.getAttr("MR_Root.masterControl"), side=s)

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
class head(object):
    ''' make new head
    Args:
        None
    '''
    def __init__(self):
        self.headNode = MrNode("headNode", parent="spineNode")
        self.headNode.addAttr("heirachyParent")
        self.headNode.addAttr("heirachyChild")
        self.proxy()


    def proxy(self):
        ''' make head proxy '''
        # Head
        self.neck = proxyObj("pNeck", (0, 23.5, 0))
        self.head = proxyObj("pHead", (0, 24.5, 0), self.neck.name)
        self.headTip = proxyObj("pHeadTip", (0, 28, 0), self.head.name)
        self.jaw = proxyObj("pJaw", (0, 25, 0.4), self.head.name)
        self.jawTip = proxyObj("pJawTip", (0, 24.4, 1.9), self.jaw.name)
        self.eyeL = proxyObj("pEyeL", (0.6, 26, 1.6), self.head.name)
        self.eyeR = proxyObj("pEyeR", (0.6, 26, 1.6), self.head.name)


    def toJoint(self, parent=None):
        ''' turn head proxies to joints '''
        self.neck = proxyToJoint(self.neck.name)
        self.head = proxyToJoint(self.head.name, self.neck)
        self.headTip = proxyToJoint(self.headTip.name, self.head)
        self.jaw = proxyToJoint(self.jaw.name, self.head)
        self.jawTip = proxyToJoint(self.jawTip.name, self.jaw)
        self.eyeL = proxyToJoint(self.eyeL.name, self.head)
        self.eyeR = proxyToJoint(self.eyeR.name, self.head)
        if parent:
            cmds.parent(self.neck, parent)


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
class arm(object):
    ''' make new head
    Args:
        side = string "L" or "R"

        numFingers (int) number of fingers
        
        armRoll (bool) add arm roll joint
    
        stretchy (bool) add stretchy limb
    '''
    def __init__(self, side, numFingers, armRoll, stretchy):
        self.armNode = MrNode("armNode", parent="spineNode")
        self.armNode.addAttr("heirachyParent")
        self.armNode.addAttr("heirachyChild")
        self.armNode.addAttr("side", value=side, lock=True)
        #self.numFingers = window.fingerNumBox.value()
        self.armNode.addAttr("numFingers", value=numFingers, lock=True)

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
        self.shoulder = proxyObj("pShoulder" + s, (3, 22.5, 0), self.clavicle.name)
        self.elbow = proxyObj("pElbow" + s, (6.4, 22.5, 0), self.shoulder.name)
        self.wrist = proxyObj("pWrist" + s, (10, 22.5, 0), self.elbow.name)
        
        # Hand
        # thumb
        self.thumb = finger(self.side, self.wrist.name, 1, form="Thumb")
        # fingers
        self.fingers = []
        space = 0.5
        start = space * (self.numFingers / 2)
        for i in range(1, self.numFingers):
            new = finger(self.side, self.wrist.name, start - (space * i))
            self.fingers.append(new)

    def toJoint(self, parent=None):
        ''' turn arm proxies to joints '''
        s = self.side

        # Arms
        self.clavicle = proxyToJoint(self.clavicle.name)
        self.shoulder = proxyToJoint(self.shoulder.name, self.clavicle)
        self.elbow = proxyToJoint(self.elbow.name, self.shoulder)
        self.wrist = proxyToJoint(self.wrist.name)

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

        if parent:
            cmds.parent(self.clavicle, parent)

        # Orient joints
        if s == "L":
            cmds.joint(self.clavicle, edit=True, orientJoint="xyz", secondaryAxisOrient="ydown", children=True)
        else:
            cmds.joint(self.clavicle, edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True)
        


    def control(self):
        ''' add arm controls '''
        s = self.side
        # Clavicle
        ClavicleCtrl = Control("ClavicleCtrl" + s, scale=0.5, direction="x", snapTo=self.shoulder, moveTo=["y", 24])
        cmds.ikHandle(name="clavicleIk" + s, startJoint=self.clavicle, endEffector=self.shoulder, solver="ikRPsolver")
        cmds.pointConstraint(ClavicleCtrl.ctrlName, "clavicleIk" + s, maintainOffset=True)

        # Arms
        ikArm, armCtrl, armOffset = FkIkBlend([self.shoulder, self.elbow, self.wrist], "Arm", -4, cmds.getAttr("MR_Root.masterControl"), side=s)

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
        if self.form == "toe":
            y = 0
        else:
            y = 22.5
        self.base = proxyObj("p%sBase%s" % (form, self.side), (12, y, 0), self.parent, radius=0.2)
        self.mid = proxyObj("p%sMid%s" % (form, self.side), (12.5, y, 0), self.base.name, radius=0.2)
        self.end = proxyObj("p%sEnd%s" % (form, self.side), (13, y, 0), self.mid.name, radius=0.2)
        self.tip = proxyObj("p%sTip%s" % (form, self.side), (13.5, y, 0), self.end.name, radius=0.2)
        self.group = cmds.group(self.base.name, self.mid.name, self.end.name, self.tip.name)
        self.name = self.base.name.replace("Base", "")
        pos = cmds.getAttr(self.parent + ".translate")[0]
        cmds.move(pos[0], pos[1], pos[2], self.group + ".rotatePivot")
        


    def toJoint(self):
        self.parent = self.parent.lstrip("p")
        self.base = proxyToJoint(self.base.name, self.parent)
        self.mid = proxyToJoint(self.mid.name, self.base)
        self.end = proxyToJoint(self.end.name, self.mid)
        self.tip = proxyToJoint(self.tip.name, self.end)


    def control(self):
        BaseCtrl = Control(self.base, scale=0.5, snapTo=self.base, pointTo=self.mid,
                                parent=self.parent, direction="z")
        cmds.orientConstraint(BaseCtrl.ctrlName, self.base, maintainOffset=True)

        MidCtrl = Control(self.mid, scale=0.5, snapTo=self.mid, pointTo=self.base,
                                parent=BaseCtrl.ctrlName, direction="z")
        cmds.orientConstraint(MidCtrl.ctrlName, self.mid, maintainOffset=True)

        EndCtrl = Control(self.end, scale=0.5, snapTo=self.end, pointTo=self.mid,
                                parent=MidCtrl.ctrlName, direction="z")
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
            cmds.move(pos, self.group, z=True, worldSpace=True)
        elif self.form == "toe":
            p = cmds.getAttr(self.parent + ".translate")[0]
            cmds.move(p[0], p[1], p[2], self.group, worldSpace=True, absolute=True)
            cmds.rotate(-90, self.group, rotateY=True)
            cmds.move(pos, self.group, x=True)
        elif "R" in self.base.name[-3:]:
            cmds.rotate(90, self.group, rotateY=True)
            cmds.move(pos, self.group, x=True, worldSpace=True)
        else:
            cmds.rotate(-90, self.group, rotateY=True)
            cmds.move(pos, self.group, x=True, worldSpace=True)
        cmds.ungroup(self.group, absolute=True)

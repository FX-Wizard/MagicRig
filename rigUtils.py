import maya.cmds as cmds

import AutoRig
import proxyObj
from Control import Control

def FkIkBlend(joints, name, pvOffset, switchCtrl, side=""):
    '''Create an FK/IK controls with blend from joint list
    Only works with RP solver

    Args:
        joints, list, 3 joints to create controls on
        
        name, Str, name of fk/ik system e.g. "left_arm"
        
        pvOffset, float, position of pole vector control in relation to the middle joint 
        
        switchCtrl, str, the object the blend control attributes will be added to
        
    Kwargs:
        Side, str, Default="", optional side prefix e.g. "L" or "R"

    Returns:
        IK handle name
    '''
    # Duplicate and reparent joints
    for i in joints:
        cmds.duplicate(i, parentOnly=True, name="FKJ_" + i)
        cmds.parent("FKJ_" + i, world=True)
        cmds.duplicate(i, parentOnly=True, name="IKJ_" + i)
        cmds.parent("IKJ_" + i, world=True)

    cmds.parent("FKJ_" + joints[1], "FKJ_" + joints[0])
    cmds.parent("FKJ_" + joints[2], "FKJ_" + joints[1])
    cmds.parent("IKJ_" + joints[1], "IKJ_" + joints[0])
    cmds.parent("IKJ_" + joints[2], "IKJ_" + joints[1])

    # FK Controls
    ctrlName = joints[0] + "FK_" + side
    controlFK0 = Control(ctrlName, scale=1.5, snapTo=joints[0], pointTo=joints[1], hideChannels=["s", "t", "v"], direction="z")
    cmds.orientConstraint(controlFK0.ctrlName, "FKJ_" + joints[0], maintainOffset=True)
    cmds.pointConstraint(joints[0], controlFK0.ctrlName, maintainOffset=True)

    ctrlName = joints[1] + "FK_" + side
    controlFK1 = Control(ctrlName, scale=1.5, snapTo=joints[1], pointTo=joints[0], hideChannels=["s", "t", "v"], direction="z")
    cmds.orientConstraint(controlFK1.ctrlName, "FKJ_" + joints[1], maintainOffset=True)

    ctrlName = joints[2] + "FK_" + side
    controlFK2 = Control(ctrlName, scale=1.5, snapTo=joints[2], pointTo=joints[1], hideChannels=["s", "t", "v"], direction="z")
    cmds.orientConstraint(controlFK2.ctrlName, "FKJ_" + joints[2], maintainOffset=True)

    cmds.parent(controlFK1.ctrlOff, controlFK0.ctrlName)
    cmds.parent(controlFK2.ctrlOff, controlFK1.ctrlName)
    # IK Controls
    
    handleName = "ik" + name + side
    cmds.ikHandle(name=handleName, startJoint="IKJ_" + joints[0], endEffector="IKJ_" + joints[2], solver="ikRPsolver")
    controlIK = Control(joints[2] + "IK_" + side, scale=2, snapTo=joints[2], pointTo=joints[1], 
                        hideChannels=["s", "t", "v"], direction="z")
    cmds.parentConstraint(controlIK.ctrlName, "ik" + name + side, maintainOffset=True)
    cmds.orientConstraint(controlIK.ctrlName, "IKJ_" + joints[2], maintainOffset=True)
    # Polevector
    ctrlName = joints[1] + "PV_" + side
    controlIKPV = Control(ctrlName, scale=0.5, direction="x", snapTo=joints[1], moveTo=("z", pvOffset), hideChannels=["s", "t", "v"])
    cmds.poleVectorConstraint(controlIKPV.ctrlName, "ik" + name + side)

    # Constraints
    cmds.pointConstraint(joints[0], "FKJ_" + joints[0], maintainOffset=False)
    cmds.pointConstraint(joints[0], "IKJ_" + joints[0], maintainOffset=False)

    cmds.orientConstraint("FKJ_" + joints[0], "IKJ_" + joints[0], joints[0], weight=10, maintainOffset=False)
    cmds.orientConstraint("FKJ_" + joints[1], "IKJ_" + joints[1], joints[1], weight=10, maintainOffset=False)
    cmds.orientConstraint("FKJ_" + joints[2], "IKJ_" + joints[2], joints[2], weight=10, maintainOffset=False)

    # Add attributes
    cmds.addAttr(switchCtrl, longName="Blend_FkIk_" + name + side, attributeType="float", min=0, max=10, defaultValue=0)
    cmds.setAttr((switchCtrl + ".Blend_FkIk_" + name + side), edit=True, keyable=True)

    cmds.connectAttr(switchCtrl + ".Blend_FkIk_" + name + side, joints[0] + "_orientConstraint1." + "FKJ_" + joints[0] + "W0")
    cmds.connectAttr(switchCtrl + ".Blend_FkIk_" + name + side, joints[1] + "_orientConstraint1." + "FKJ_" + joints[1] + "W0")
    cmds.connectAttr(switchCtrl + ".Blend_FkIk_" + name + side, joints[2] + "_orientConstraint1." + "FKJ_" + joints[2] + "W0")

    rev = cmds.shadingNode("plusMinusAverage", asUtility=True, name=name + side + "_Minus")
    cmds.setAttr((rev + ".operation"), 2)
    cmds.setAttr(rev + ".input1D[0]", 10)
    cmds.connectAttr(switchCtrl + ".Blend_FkIk_" + name + side, rev + ".input1D[1]")

    cmds.connectAttr(rev + ".output1D", joints[0] + "_orientConstraint1." + "IKJ_" + joints[0] + "W1")
    cmds.connectAttr(rev + ".output1D", joints[1] + "_orientConstraint1." + "IKJ_" + joints[1] + "W1")
    cmds.connectAttr(rev + ".output1D", joints[2] + "_orientConstraint1." + "IKJ_" + joints[2] + "W1")

    # Visibility Toggle
    cmds.addAttr(switchCtrl, longName="Show_FK_" + name + side, attributeType="bool", defaultValue=1)
    cmds.setAttr(switchCtrl + ".Show_FK_" + name + side, edit=True, keyable=True)
    cmds.connectAttr(switchCtrl + ".Show_FK_" + name + side, controlFK0.ctrlName + ".visibility")
    cmds.connectAttr(switchCtrl + ".Show_FK_" + name + side, controlFK1.ctrlName + ".visibility")
    cmds.connectAttr(switchCtrl + ".Show_FK_" + name + side, controlFK2.ctrlName + ".visibility")

    cmds.addAttr(switchCtrl, longName="Show_IK_" + name + side, attributeType="bool", defaultValue=1)
    cmds.setAttr(switchCtrl + ".Show_IK_" + name + side, edit=True, keyable=True)
    cmds.connectAttr(switchCtrl + ".Show_IK_" + name + side, controlIK.ctrlName + ".visibility")
    cmds.connectAttr(switchCtrl + ".Show_IK_" + name + side, controlIKPV.ctrlName + ".visibility")

    return (handleName, controlIK.ctrlName)


def freezeTransforms(obj):
    cmds.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True)
    cmds.delete(obj, constructionHistory=True)

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
    controlFK0 = joints[0] + "FK_Ctrl" + side
    makeControl(controlFK0, ctrlSize=1.5, snapJoint=joints[0], orientJoint=joints[1], ctrlNormal=(0, 1, 0))
    cmds.orientConstraint(controlFK0, "FKJ_" + joints[0], maintainOffset=True)
    lockHide(controlFK0, rotate=False, vis=False)

    controlFK1 = joints[1] + "FK_Ctrl" + side
    makeControl(controlFK1, ctrlSize=1.5, snapJoint=joints[1], orientJoint=joints[2], ctrlNormal=(0, 1, 0))
    cmds.orientConstraint(controlFK1, "FKJ_" + joints[1], maintainOffset=True)
    lockHide(controlFK1, rotate=False, vis=False)

    controlFK2 = joints[2] + "FK_Ctrl" + side
    makeControl(controlFK2, ctrlSize=1.5, snapJoint=joints[2], orientJoint=joints[1], ctrlNormal=(0, 1, 0))
    cmds.orientConstraint(controlFK2, "FKJ_" + joints[2], maintainOffset=True)
    lockHide(controlFK2, rotate=False, vis=False)

    cmds.parent(controlFK1, controlFK0)
    cmds.parent(controlFK2, controlFK1)
    # IK Controls
    controlIK = joints[2] + "IK_Ctrl" + side
    cmds.ikHandle(name="ik" + name + side, startJoint="IKJ_" + joints[0], endEffector="IKJ_" + joints[2], solver="ikRPsolver")
    makeControl(controlIK, ctrlSize=2, snapJoint=joints[2], orientJoint=joints[1], ctrlNormal=(0, 1, 0))
    cmds.parentConstraint(controlIK, "ik" + name + side, maintainOffset=True)
    cmds.orientConstraint(controlIK, "IKJ_" + joints[2], maintainOffset=True)
    # Polevector
    controlIKPV = joints[1] + "PV_Ctrl" + side
    makeControl(controlIKPV, ctrlSize=0.5, snapJoint=joints[1], offset=("z", pvOffset))
    cmds.poleVectorConstraint(controlIKPV, "ik" + name + side)
    lockHide(controlIKPV, translate=False, vis=False)

    # Constraints
    cmds.pointConstraint(joints[0], "FKJ_" + joints[0])
    cmds.pointConstraint(joints[0], "IKJ_" + joints[0])

    cmds.orientConstraint("FKJ_" + joints[0], "IKJ_" + joints[0], joints[0], weight=10)
    cmds.orientConstraint("FKJ_" + joints[1], "IKJ_" + joints[1], joints[1], weight=10)
    cmds.orientConstraint("FKJ_" + joints[2], "IKJ_" + joints[2], joints[2], weight=10)

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
    cmds.connectAttr(switchCtrl + ".Show_FK_" + name + side, controlFK0 + ".visibility")
    cmds.connectAttr(switchCtrl + ".Show_FK_" + name + side, controlFK1 + ".visibility")
    cmds.connectAttr(switchCtrl + ".Show_FK_" + name + side, controlFK2 + ".visibility")

    cmds.addAttr(switchCtrl, longName="Show_IK_" + name + side, attributeType="bool", defaultValue=1)
    cmds.setAttr(switchCtrl + ".Show_IK_" + name + side, edit=True, keyable=True)
    cmds.connectAttr(switchCtrl + ".Show_IK_" + name + side, controlIK + ".visibility")
    cmds.connectAttr(switchCtrl + ".Show_IK_" + name + side, controlIKPV + ".visibility")

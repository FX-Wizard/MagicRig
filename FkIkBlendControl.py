def FkIkBlend(joints, name, pvOffset, switchCtrl, side = ""):
    '''Create an FK/IK controls with blend from joint list
    
    Args:
        joints, list, 3 joints to create controls on
        
        name, Str, name of fk/ik system e.g. "left_arm"
        
        pvOffset, float, position of pole vector control in relation to the middle joint 
        
        switchCtrl, str, the object the blend controll attributes will be added to
        
    Kwargs:
        Side, str, Default = "", optional side prefix e.g. "L" or "R"
    '''
    # Duplicate and reparent joints
    for i in joints:
        cmds.duplicate(i, parentOnly = True, name = "FKJ_" + i)
        #cmds.parent("FKJ_" + i, world = True)
        cmds.duplicate(i, parentOnly = True, name = "IKJ_" + i)
        #cmds.parent("IKJ_" + i, world = True)

    cmds.parent("FKJ_" + joints[1], "FKJ_" + joints[0])
    cmds.parent("FKJ_" + joints[2], "FKJ_" + joints[1])
    cmds.parent("IKJ_" + joints[1], "IKJ_" + joints[0])
    cmds.parent("IKJ_" + joints[2], "IKJ_" + joints[1])
    
    # FK Controls
    for i in joints:
        makeControl(i + "FK_Ctrl" + side, ctrlSize = 1.5, snapJoint = i, ctrlNormal = (0, 1, 0))
        cmds.orientConstraint(i + "FK_Ctrl" + side, "FKJ_" + i, maintainOffset = True)
        lockHide(i + "FK_Ctrl" + side, rotate = False)
    
    # IK Controls
    cmds.ikHandle(name = "ik" + name, startJoint = "IKJ_" + joints[0], endEffector = "IKJ_" + joints[2], solver = "ikRPsolver")
    makeControl(joints[2] + "IK_Ctrl" + side, ctrlSize = 2, snapJoint = joints[2], orientJoint =joints[1], ctrlNormal = (0, 1, 0))
    cmds.parentConstraint(joints[2] + "IK_Ctrl" + side, "ik" + name, maintainOffset = True)
    # Polevector
    makeControl(joints[1] + "PV_Ctrl" + side, 0.5, joints[1], None, ("z", pvOffset))
    cmds.poleVectorConstraint(joints[1] + "PV_Ctrl" + side, "ik" + name)
    lockHide(joints[1] + "PV_Ctrl" + side, translate = False)

    # Constraints
    cmds.pointConstraint(joints[0], "FKJ_" + joints[0])
    cmds.pointConstraint(joints[0], "IKJ_" + joints[0])

    cmds.orientConstraint("FKJ_" + joints[0], "IKJ_" + joints[0], joints[0], weight = 10)
    cmds.orientConstraint("FKJ_" + joints[1], "IKJ_" + joints[1], joints[1], weight = 10)
    cmds.orientConstraint("FKJ_" + joints[2], "IKJ_" + joints[2], joints[2], weight = 10)

    # Add attributes  
    cmds.addAttr(switchCtrl, longName = "SWITCH_FK_" + name, attributeType = "float", min = 0, max = 10, defaultValue = 0)
    cmds.setAttr((switchCtrl + "." +  "SWITCH_FK_" + name), edit = True, keyable = True)

    cmds.connectAttr(switchCtrl + "." +  "SWITCH_FK_" + name, joints[0] + "_orientConstraint1." + "FKJ_" + joints[0] + "W0")
    cmds.connectAttr(switchCtrl + "." +  "SWITCH_FK_" + name, joints[1] + "_orientConstraint1." + "FKJ_" + joints[1] + "W0")
    cmds.connectAttr(switchCtrl + "." +  "SWITCH_FK_" + name, joints[2] + "_orientConstraint1." + "FKJ_" + joints[2] + "W0")

    cmds.addAttr(switchCtrl, longName = "SWITCH_IK_" + name, attributeType = "float", min = 0, max = 10, defaultValue = 1)
    cmds.setAttr((switchCtrl + "." +  "SWITCH_IK_" + name), edit = True, keyable = True)

    cmds.connectAttr(switchCtrl + "." +  "SWITCH_IK_" + name, joints[0] + "_orientConstraint1." + "IKJ_" + joints[0] + "W1")
    cmds.connectAttr(switchCtrl + "." +  "SWITCH_IK_" + name, joints[1] + "_orientConstraint1." + "IKJ_" + joints[1] + "W1")
    cmds.connectAttr(switchCtrl + "." +  "SWITCH_IK_" + name, joints[2] + "_orientConstraint1." + "IKJ_" + joints[2] + "W1")

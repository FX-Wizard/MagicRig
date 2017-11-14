import maya.cmds as cmds
from math import sqrt, pow

def makeStretchyIK(IKHandleName, jointOffset = 0):
	"""Add stretch property to IK handle
	
	Args:
		IKHandleName (str): Name of IK handle to apply stretch.
	
	Kwargs:
		jointOffset (default = 0): If ikHandle has been moved from end position 
		how many joints back is it?
	"""
	startJoint = cmds.ikHandle(IKHandleName, query = True, startJoint = True)
	endEffector = cmds.ikHandle(IKHandleName, query = True, endEffector = True)
	jointList = cmds.ikHandle(IKHandleName, query = True, jointList = True)

	# Get length of joint hierarchy
	totalDistance = 0
	cmds.select(startJoint, replace = True)
	
	for i in range((len(jointList) + 1) - jointOffset):
		j1 = cmds.joint(query = True, position = True, absolute = True)
		cmds.pickWalk(direction = "down")
		j2 = cmds.joint(query = True, position = True, absolute = True)
		distance = sqrt(pow(j1[0] - j2[0], 2) + pow(j1[1] - j2[1], 2) + pow(j1[2] - j2[2], 2))
		totalDistance += distance
	
    # ControlBox
	ControlBox = cmds.group(IKHandleName, name = IKHandleName + "_StretchContol")

	cmds.addAttr(longName = "_____", attributeType = "double")
	cmds.setAttr(ControlBox + "._____", edit = True, keyable = True, lock = True)

	cmds.addAttr(longName = "Stretch", attributeType = "double", min = 0, max = 1, defaultValue = 1)
	cmds.setAttr(ControlBox + ".Stretch", edit = True, keyable = True)

	cmds.addAttr(longName = "Squish", attributeType = "double", min = 0, max = 1, defaultValue = 1)
	cmds.setAttr(ControlBox + ".Squish", edit = True, keyable = True)
	
	#cmds.addAttr(longName = "Scale", attributeType = "double", min = 0, max = 1, defaultValue = 0)
	#cmds.setAttr(ControlBox + ".Scale", edit = True, keyable = True)
	
	# Create and connect utility nodes
	distanceNode = cmds.shadingNode("distanceBetween", asUtility = True, name = "dist_" + IKHandleName)
	conditionNode = cmds.shadingNode("condition", asUtility = True, name = "cond_" + IKHandleName)
	divide1 = cmds.shadingNode("multiplyDivide", asUtility = True, name = "div1_" + IKHandleName)
	multiply1 = cmds.shadingNode("multiplyDivide", asUtility = True, name = "mult1_" + IKHandleName)
	multiply2 = cmds.shadingNode("multiplyDivide", asUtility = True, name = "mult2_" + IKHandleName)
	plusMinusAverage1 = cmds.shadingNode("plusMinusAverage", asUtility = True, name = "subtract_" + IKHandleName)
	plusMinusAverage2 = cmds.shadingNode("plusMinusAverage", asUtility = True, name = "sum_" + IKHandleName)

	cmds.connectAttr((startJoint + ".translate"), (distanceNode + ".point1"), force = True)
	cmds.connectAttr((IKHandleName + ".translate"), (distanceNode + ".point2"), force = True)

	cmds.connectAttr((distanceNode + ".distance"), (divide1 + ".input1Y"), force = True)

	cmds.connectAttr((divide1 + ".input2Z"), (plusMinusAverage1 + ".input1D[1]"), force = True)
	cmds.connectAttr((divide1 + ".outputY"), (plusMinusAverage1 + ".input1D[0]"), force = True)

	cmds.connectAttr((plusMinusAverage1 + ".output1D"), (multiply1 + ".input2Y"), force = True)

	cmds.connectAttr((multiply1 + ".outputY"), (plusMinusAverage2 + ".input1D[0]"), force = True)
	cmds.connectAttr((multiply1 + ".input2Z"), (plusMinusAverage2 + ".input1D[1]"), force = True)

	cmds.connectAttr((ControlBox + ".Stretch"), (multiply1 + ".input1Y"), force = True)

	cmds.connectAttr((plusMinusAverage2 + ".output1D"), (conditionNode + ".colorIfFalseG"), force = True)
	cmds.connectAttr((plusMinusAverage2 + ".output1D"), (conditionNode + ".firstTerm"), force = True)
	cmds.connectAttr((ControlBox + ".Squish"), (conditionNode + ".secondTerm"), force = True)
	cmds.connectAttr((ControlBox + ".Squish"), (conditionNode + ".colorIfTrueG"), force = True)

	cmds.connectAttr((conditionNode + ".outColorG"), (multiply2 + ".input1Y"), force = True)

	cmds.setAttr((divide1 + ".operation"), 2)
	cmds.setAttr((plusMinusAverage1 + ".operation"), 2)
	cmds.setAttr((conditionNode + ".operation"), 4)
	cmds.setAttr((plusMinusAverage2 + ".operation"), 1)

	cmds.setAttr((divide1 + ".input2Y"), totalDistance)

	# Connect utility nodes to joints
	currentJoint = startJoint

	for i in range(len(jointList) + 1):
		# scale
		#cmds.connectAttr((multiply2 + ".outputY"), (currentJoint + ".scaleX"), force = True)
		
		# translate
		multiply4 = cmds.shadingNode("multiplyDivide", asUtility = True)
		
		cmds.select(currentJoint)
		cmds.pickWalk(direction = "down")
		currentJoint = cmds.ls(selection = True)
		
		currentTranslateValue = cmds.getAttr(currentJoint[0] + ".translateX")
		
		cmds.connectAttr((multiply2 + ".outputY"), (multiply4 + ".input1Y"), force = True)
		cmds.setAttr((multiply4 + ".input2Y"), currentTranslateValue)
		
		cmds.connectAttr((multiply4 + ".outputY"), (currentJoint[0] + ".translateX"), force = True)
    

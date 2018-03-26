import os
import maya.cmds as cmds
import json
from ui import window

class Control:
    ''' Rig control class '''
    def __init__(self,
                 name = "new_Ctrl",
                 #prefix = "",
                 shape = "circle",
                 scale = [1.0, 1.0, 1.0],
                 direction = "",
                 snapTo = "",
                 pointTo = "",
                 moveTo = "",
                 parent = "",
                 lockChannels = ["s"],
                 hideChannels = ["s", "v"]
                 ):
        prefix = cmds.getAttr("MR_Root.prefix") #window.charNameBox.text()
        # create shape
        if shape == "circle":
            ctrlObject = cmds.circle(name=prefix + "_" + name + "_ctrl", ch=False, normal=[0, 1, 0], radius=1)[0]
        else:
            mayaVersion = cmds.about(version = True)
            jsonFile = os.path.expanduser("~/maya/%s/scripts/MagicRig/ControlShapes.json" % mayaVersion)
            shapes = json.load(open(jsonFile))
            ctrlObject = cmds.curve(p=shapes[shape], d=1, name=prefix + "_" + name + "_ctrl")
        ctrlOffset = cmds.group([ctrlObject], name=prefix + "_" + name + "_offset")

        # scale
        masterScale = cmds.getAttr("MR_Root.masterScale")
        if type(scale) is int or type(scale) is float:
            scale = scale * masterScale
            cmds.scale(scale, scale, scale, ctrlOffset)
        else:# scale != [1.0, 1.0, 1.0]:
            scale = [x * masterScale for x in scale]
            cmds.scale(scale[0], scale[1], scale[2], ctrlOffset)

        # direction
        if direction == "x":
            cmds.rotate(90, 0, 0, ctrlOffset, absolute=True)
        elif direction == "y":
            cmds.rotate(0, 90, 0, ctrlOffset, absolute=True)
        elif direction == "z":
            cmds.rotate(0, 0, 90, ctrlOffset, absolute=True)

        # snap to
        if cmds.objExists(snapTo):
            cmds.delete(cmds.pointConstraint(snapTo, ctrlOffset))

        # point to
        if cmds.objExists(pointTo):
            cmds.makeIdentity(ctrlOffset, apply=True, rotate=True)
            cmds.delete(cmds.orientConstraint(pointTo, ctrlOffset))

        # move to
        if moveTo:
            cmds.select(ctrlOffset)
            if moveTo[0] == "x":
                cmds.move(moveTo[1] * masterScale, x=True)
            elif moveTo[0] == "y":
                cmds.move(moveTo[1] * masterScale, y=True)
            elif moveTo[0] == "z":
                cmds.move(moveTo[1] * masterScale, z=True)
            cmds.select(clear=True)

        # parent
        if parent and cmds.objExists(parent):
            cmds.parent(ctrlOffset, parent)

        # lock
        if "t" in lockChannels:
            cmds.setAttr(ctrlObject + ".tx", lock=True, keyable=False, channelBox=False)
            cmds.setAttr(ctrlObject + ".ty", lock=True, keyable=False, channelBox=False)
            cmds.setAttr(ctrlObject + ".tz", lock=True, keyable=False, channelBox=False)
        if "r" in lockChannels:
            cmds.setAttr(ctrlObject + ".rx", lock=True, keyable=False, channelBox=False)
            cmds.setAttr(ctrlObject + ".ry", lock=True, keyable=False, channelBox=False)
            cmds.setAttr(ctrlObject + ".rz", lock=True, keyable=False, channelBox=False)
        if "s" in lockChannels:
            cmds.setAttr(ctrlObject + ".sx", lock=True, keyable=False, channelBox=False)
            cmds.setAttr(ctrlObject + ".sy", lock=True, keyable=False, channelBox=False)
            cmds.setAttr(ctrlObject + ".sz", lock=True, keyable=False, channelBox=False)
        if "v" in lockChannels:
            cmds.setAttr(ctrlObject + ".v", lock=True, keyable=False, channelBox=False)

        # set control colour
        ctrlShape = cmds.listRelatives(ctrlObject, s=1)[0]
        cmds.setAttr(ctrlShape + ".overrideEnabled", 1)
        if name[-1] == "L":
            cmds.setAttr(ctrlShape + ".overrideColor", 6)
        elif name[-1] == "R":
            cmds.setAttr(ctrlShape + ".overrideColor", 13)
        else:
            cmds.setAttr(ctrlShape + ".overrideColor", 22)

        # tag as control for parallel eval
        cmds.select(ctrlObject)
        cmds.TagAsController()
        cmds.select(clear=True)

        # set public names
        self.ctrlName = ctrlObject
        self.ctrlOff = ctrlOffset

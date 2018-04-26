import os
import maya.cmds as cmds
import json

#from rignode import MetaNode

class Control(object):
    ''' Creates new controller object
    Kwargs:
        name (string) name of new control
        shape (string) shape of object, default "circle"
        scale (list, float3) size of controller [X, Y, Z]
        direction (char) direction control faces, "x" or "y" or "z"
        snapTo (string) snap controller to object
        pointTo (string) point controller at object
        moveTo (string) move controller
        parent (string) set controllers parent
        lockChannels (list) ["t", "r", "s", "v"]
        hideChannels (list) ["t", "r", "s", "v"]

    Public Attr:
        ctrlName, name of control
        ctrlOff name of controls offset
    '''
    def __init__(self,
                 name = "new_Ctrl",
                 shape = "circle",
                 scale = [1.0, 1.0, 1.0],
                 direction = "",
                 snapTo = "",
                 pointTo = "",
                 moveTo = "",
                 parent = "",
                 lockChannels = ["s"],
                 hideChannels = ["s", "v"],
                 master = False
                 ):
        prefix = cmds.getAttr("MR_Root.prefix")
        # create shape
        if shape == "circle":
            ctrlObject = cmds.circle(name=prefix + "_" + name + "_ctrl", ch=False, normal=[0, 1, 0], radius=1)[0]
        else:
            jsonFile = os.path.dirname(__file__) + "/ControlShapes.json"
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

        # parent master
        if not master:
            masterCtrl = cmds.listConnections("MR_Root.masterControl")[0]
            cmds.parent(ctrlOffset, masterCtrl)

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
        if "L" in name[-3:]:
            cmds.setAttr(ctrlShape + ".overrideColor", 6)
        elif "R" in name[-3:]:
            cmds.setAttr(ctrlShape + ".overrideColor", 13)
        else:
            cmds.setAttr(ctrlShape + ".overrideColor", 22)

        # tag as control for parallel eval
        cmds.select(ctrlObject)
        cmds.TagAsController()
        cmds.select(clear=True)

        # connect to parent node
        cmds.addAttr(ctrlObject, ln="controlName", at="message")
        cmds.connectAttr("MR_Root.controls", ctrlObject + ".controlName")
        # connect message to offset
        cmds.addAttr(ctrlObject, ln="controlOffset", at="message")
        cmds.addAttr(ctrlOffset, ln="offsetControl", at="message")
        cmds.connectAttr(ctrlObject + ".controlOffset", ctrlOffset + ".offsetControl")

        # set public names
        self.ctrlName = ctrlObject
        self.ctrlOff = ctrlOffset

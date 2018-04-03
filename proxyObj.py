import maya.cmds as cmds
import AutoRig
from Control import Control

class proxyObj:
    def __init__(self, proxyName, move=None, proxyBone=None, radius=0.5):
        # check name is unique
        newName = proxyName
        i = 1
        while cmds.objExists(newName):
            newName = proxyName + str(i)
            i += 1
        name = newName
        # Make Proxy Shape
        obj = cmds.sphere(name=name, r=radius, d=3, s=4, nsp=2, ch=False)[0]
        objShape = cmds.listRelatives(obj, shapes=True)[0]
        cmds.disconnectAttr(objShape + ".instObjGroups[0]", "initialShadingGroup.dagSetMembers[0]")
        # set colour
        cmds.setAttr(objShape + ".overrideEnabled", 1)
        if proxyName[-1] == "L":
            cmds.setAttr(objShape + ".overrideColor", 6)
        elif proxyName[-1] == "R":
            cmds.setAttr(objShape + ".overrideColor", 13)
        else:
            cmds.setAttr(objShape + ".overrideColor", 4)
        
        if move:
            cmds.move(move[0], move[1], move[2], name)

        if proxyBone:
            bone = Control(name + "_bone", shape="proxyBone", scale=[radius, radius, radius], snapTo=proxyBone, pointTo=obj, lockChannels=["t", "r", "s"])

            tip = cmds.cluster(bone.ctrlName + ".cv[2]", bone.ctrlName + ".cv[6]", name="_tip_")[0]
            cmds.setAttr(tip + "Handle.visibility", 0)
            cmds.parent(tip + "Handle", bone.ctrlOff)
            cmds.pointConstraint(obj, tip + "Handle")
            
            base = cmds.cluster(bone.ctrlName + ".cv[0:1]", bone.ctrlName + ".cv[3:5]", bone.ctrlName + ".cv[7:8]", name="_base_")[0]
            cmds.setAttr(base + "Handle.visibility", 0)
            cmds.parent(base + "Handle", bone.ctrlOff)
            cmds.pointConstraint(proxyBone, base + "Handle")

            try:
                cmds.parent(bone.ctrlOff, "proxyExtra")
            except:
                cmds.group(bone.ctrlOff, name="proxyExtra")
            
        AutoRig.proxyList.append(name)
        try:
            cmds.parent(name, "proxyRig")
        except:
            cmds.group(name, name="proxyRig")

        # public names
        self.name = name

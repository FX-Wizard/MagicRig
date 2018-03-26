import maya.cmds as cmds
import AutoRig
from Control import Control

class proxyObj:
    def __init__(self, proxyName, move=None, proxyBone=None, radius=0.5):
        # scale = AutoRig.getModelScale()
        # Make Proxy Shape
        '''
        cmds.circle(name="proxyShape",
                    normal=(0, 1, 0),
                    center=(0, 0, 0),
                    sweep=360,
                    radius=(0.25))
        cmds.duplicate(returnRootsOnly=True, name=("proxyShapeY"))
        cmds.rotate(90, 0, 0)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
        cmds.duplicate(returnRootsOnly=True, name=("proxyShapeZ"))
        cmds.rotate(0, 90, 0)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
        cmds.parent(("proxyShapeYShape", "proxyShapeZShape"), "proxyShape", shape=True, relative=True)
        cmds.delete("proxyShapeY", "proxyShapeZ")
        '''

        obj = cmds.sphere(name=proxyName, r=radius, d=3, s=4, nsp=2, ch=False)[0]
        objShape = cmds.listRelatives(obj, shapes=True)[0]
        cmds.disconnectAttr(objShape + ".instObjGroups[0]", "initialShadingGroup.dagSetMembers[0]")
        #cmds.rename("proxyShape", proxyName)

        cmds.setAttr(objShape + ".overrideEnabled", 1)
        if proxyName[-1] == "L":
            cmds.setAttr(objShape + ".overrideColor", 6)
        elif proxyName[-1] == "R":
            cmds.setAttr(objShape + ".overrideColor", 13)
        else:
            cmds.setAttr(objShape + ".overrideColor", 4)

        if move:
            cmds.move(move[0], move[1], move[2], proxyName)

        if proxyBone:
            bone = Control(proxyName + "_bone", shape="proxyBone", scale=[radius, radius, radius], snapTo=proxyBone, pointTo=obj, lockChannels=["t", "r", "s"])

            tip = cmds.cluster(bone.ctrlName + ".cv[2]", bone.ctrlName + ".cv[6]", name="_tip_")[0]
            cmds.setAttr(tip + "Handle.visibility", 0)
            cmds.parent(tip + "Handle", bone.ctrlOff)
            cmds.pointConstraint(obj, tip + "Handle")
            
            base = cmds.cluster(bone.ctrlName + ".cv[0:1]", bone.ctrlName + ".cv[3:5]", bone.ctrlName + ".cv[7:8]", name="_base_")[0]
            cmds.setAttr(base + "Handle.visibility", 0)
            cmds.parent(base + "Handle", bone.ctrlOff)
            cmds.pointConstraint(proxyBone, base + "Handle")

            AutoRig.proxyExtra.append(bone.ctrlOff)

        AutoRig.proxyList.append(proxyName)
        cmds.parent(proxyName, "proxyRig")

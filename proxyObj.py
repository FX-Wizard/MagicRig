import os
import json
import maya.cmds as cmds

MAX_SIZE = 2147483647

def proxyObj(proxyName, move=None, proxyBone=None, radius=0.5):
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
     # catch bug where initial shading group cannot be disconnected
    for pos in range(MAX_SIZE + 1):
        try:
            cmds.disconnectAttr(objShape + ".instObjGroups", f"initialShadingGroup.dagSetMembers[{pos}]")
            break
        except:
            if pos == MAX_SIZE:
                cmds.error("Failed to disconnect initialShadingGroup")
            else:
                pass
    # set colour
    cmds.setAttr(objShape + ".overrideEnabled", 1)
    if "L" in proxyName[-3:]:
        cmds.setAttr(objShape + ".overrideColor", 6)
    elif "R" in proxyName[-3:]:
        cmds.setAttr(objShape + ".overrideColor", 13)
    else:
        cmds.setAttr(objShape + ".overrideColor", 4)
    
    if move:
        cmds.move(move[0], move[1], move[2], name)

    if proxyBone:
        jsonFile = os.path.dirname(__file__) + "/ControlShapes.json"
        shapes = json.load(open(jsonFile))
        bone = cmds.curve(p=shapes["proxyBone"], d=1, name=name + "_bone")

        tip = cmds.cluster(bone + ".cv[2]", bone + ".cv[6]", name="_tip_")[0]
        cmds.setAttr(tip + "Handle.visibility", 0)
        cmds.pointConstraint(obj, tip + "Handle")
        
        base = cmds.cluster(bone + ".cv[0:1]", bone + ".cv[3:5]", bone + ".cv[7:8]", name="_base_")[0]
        cmds.setAttr(base + "Handle.visibility", 0)
        cmds.pointConstraint(proxyBone, base + "Handle")

        try:
            cmds.parent(bone, "proxyExtra")
        except:
            cmds.group(bone, name="proxyExtra")
        cmds.parent(tip + "Handle", "proxyExtra")
        cmds.parent(base + "Handle", "proxyExtra")
        
    # Add proxy to root nodes proxy object list
    cmds.addAttr(name, ln="proxyName", at="message")
    cmds.connectAttr("MR_Root.proxyObjects", name + ".proxyName")
    
    # Add to rig group
    try:
        cmds.parent(name, cmds.getAttr("MR_Root.prefix") + "_Rig")
    except:
        cmds.group(name, name=cmds.getAttr("MR_Root.prefix") + "_Rig")

    # public names
    return name

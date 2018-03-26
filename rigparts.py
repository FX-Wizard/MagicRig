import maya.cmds as cmds
from proxyObj import proxyObj
from ui import window
from .rignode import MrNode

#prefix = cmds.getAttr("MR_Root.prefix")

# biped
def spine():
    # Spine
    spineNode = MrNode("spineNode", parent="rootNode")
    sJointNum = window.spineJointNumBox.value()
    spineNode.addAttr("spineJointNum", sJointNum)

    seperation = (7.1 / (sJointNum - 1))

    for i in range(sJointNum):
        proxyObj("pSpine" + str(i), (0, (seperation * i) + 15, 0, ))


def leg(side):
    ''' make proxy leg
    Args:
        side = string "L" or "R"
    '''
    legNode = MrNode("legNode", parent="spineNode")
    legNode.addAttr("side", value=side, lock=True)

    proxyObj("pHip" + side, (1.7, 14, 0))
    proxyObj("pKnee" + side, (1.7, 8, 0), "pHip" + side)
    proxyObj("pAnkle" + side, (1.7, 1.6, 0), "pKnee" + side)

    # Foot
    proxyObj("pFoot" + side, (1.7, 0, 2.3), "pAnkle" + side)
    proxyObj("pToe" + side, (1.7, 0, 4), "pToe" + side)

    proxyObj("pFootLock" + side, (1.7, 0, -0.5))


def head():
    # Head
    headNode = MrNode("headNode", parent="spineNode")
    proxyObj("pNeck", (0, 23.5, 0))
    proxyObj("pHead", (0, 24.5, 0), "pNeck")
    proxyObj("pHeadTip", (0, 28, 0), "pHead")
    proxyObj("pJaw", (0, 25, 0.4), "pHead")
    proxyObj("pJawTip", (0, 24.4, 1.9), "pJaw")
    proxyObj("pEyeL", (0.6, 26, 1.6), "pHead")
    proxyObj("pEyeR", (0.6, 26, 1.6), "pHead")


def arm(side):
    ''' make proxy arms
    Args:
        side = string "L" or "R"
    '''
    armNode = MrNode("armNode", parent="spineNode")
    armNode.addAttr("side", value=side, lock=True)

    proxyObj("pClavicle" + side, (1.25, 22.5, 0))
    proxyObj("pShoulder" + side, (3, 22.5, 0), "pClavicle" + side)
    proxyObj("pElbow" + side, (6.4, 22.5, 0), "pShoulder" + side)
    proxyObj("pWrist" + side, (10, 22.5, 0), "pElbow" + side)
    
    # roll joint
    if window.armRollBox.checkState():
        proxyObj("pForearmRoll" + side, (7.5, 22.5, 0))
    
    # Hand
    numFingers = window.fingerNumBox.value()
    
    # thumb
    proxyObj("pThumbBase" + side, (11, 22.5, 0.5), "pWrist" + side, radius=0.2)
    proxyObj("pThumbMid" + side, (11, 22.5, 1), "pThumbBase" + side, radius=0.2)
    proxyObj("pThumbEnd" + side, (11, 22.5, 1.5), "pThumbMid" + side, radius=0.2)
    proxyObj("pThumbTip" + side, (11, 22.5, 2), "pThumbEnd" + side, radius=0.2)
    
    #fingers
    space = 0.5
    start = space * (numFingers / 2)
    for i in range(1, numFingers):
        proxyObj("pFingerBase" + str(i) + side, (12, 22.5, start - (space * i)),
                "pWrist" + side, radius=0.2)
        proxyObj("pFingerMiddle" + str(i) + side, (12.5, 22.5, start - (space * i)),
                "pFingerBase" + str(i) + side, radius=0.2)
        proxyObj("pFingerEnd" + str(i) + side, (13, 22.5, start - (space * i)),
                "pFingerMiddle" + str(i) + side, radius=0.2)
        proxyObj("pFingerTip" + str(i) + side, (13.5, 22.5, start - (space * i)),
                "pFingerEnd" + str(i) + side, radius=0.2)

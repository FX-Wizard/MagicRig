import maya.cmds as cmds

class MrNode():
    def __init__(self, name, version="0.1", parent="", child=""):
        name = cmds.createNode("network", name=name)
        # default attributes
        self.addAttr("parent")
        self.addAttr("child")
        
        if parent:
            cmds.connectAttr(parent + ".child", name + ".parent")
               
        #public vars
        self.name = name
        self.parent = parent
    
    
    def addAttr(self, name, value=None, options="", lock=False):
        '''adds attributes to MrNode
        args:
            name = name of attribute
        kwargs:
            options = enum names (list)
            value = value to be added to attribute
        '''
        if options:
            options = ":".join(options)
            cmds.addAttr(longName=name, attributeType="enum", enumName=options)
        elif type(value) == str:
            cmds.addAttr(longName=name, dataType="string")
        elif type(value) == int:
            cmds.addAttr(longName=name, attributeType="long")
        elif type(value) == float:
            cmds.addAttr(longName=name, attributeType="double")
        elif type(value) == bool:
            cmds.addAttr(longName=name, attributeType="bool")
        else:
            cmds.addAttr(longName=name, attributeType="message")
        if value:
            self.modAttr(name, value, lock=lock)


    def modAttr(self, name, value, lock=False):
        if type(value) == str:
            cmds.setAttr(self.name + "." + name, value, type="string", lock=lock)
        else:
            cmds.setAttr(self.name + "." + name, value, lock=lock)
        

    def setParent(self, parent):
        cmds.connectAttr(parent + ".child", self.name + ".parent")


class MetaNode(object):
    '''add metadata nodes to inherited classes'''
    def __new__(cls, name, *args, **kwargs):
        #if not name:
        #    name = cls.__name__
        #if type(name) == int:
            #name = cls.__name__
        #print(type(name))
        cls.node = cmds.createNode("network", name=name)
        cmds.addAttr(longName="parent", attributeType="message")
        cmds.addAttr(longName="child", attributeType="message")
        # set object type
        cmds.addAttr(longName="object", dataType="string")
        #print(cmds.getAttr('rootRig.object'))
        cmds.setAttr(name + ".object", cls.__name__, type="string", lock=False)
        
        return super(cls.__class__, cls).__new__(cls)


    def __init__(self, name, *args, **kwargs):
        print("super __init__ was called")
        self.name = name
    
    
    def addAttr(self, name, value=None, options="", lock=False):
        '''adds attributes to MrNode
        Args:
        name -- name of attribute
        kwargs:
        options -- enum names (list)
        value -- value to be added to attribute (default None)
        '''
        if options:
            options = ":".join(options)
            cmds.addAttr(longName=name, attributeType="enum", enumName=options)
        elif type(value) == str:
            cmds.addAttr(longName=name, dataType="string")
        elif type(value) == int:
            cmds.addAttr(longName=name, attributeType="long")
        elif type(value) == float:
            cmds.addAttr(longName=name, attributeType="double")
        elif type(value) == bool:
            cmds.addAttr(longName=name, attributeType="bool")
        else:
            cmds.addAttr(longName=name, attributeType="message")
        if value:
            self.modAttr(name, value, lock=lock)


    def modAttr(self, name, value, lock=False):
        if type(value) == str:
            cmds.setAttr(self.name + "." + name, value, type="string", lock=False)
        else:
            cmds.setAttr(self.name + "." + name, value, lock=False)
        

    def setParent(self, parent):
        print(parent + ".child")
        print(self.name + ".parent")
        try:
            cmds.connectAttr(parent + ".child", self.name + ".parent")
        except:
            pass


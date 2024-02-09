# Copyright 2024 Dirk Pleiter <dirk.pleiter@pm.me>

"""Module infra

Classes and methods for managing infrastructure-related information
"""

import xml.dom.minidom as minidom


class Node:
    def __init__(self):
        self.id = None
        self.type = None
        self.attr = {}

    def toXML(self):
        return ""


class Infrastructure:
    def nNode(self):
        return len(self.nodeList)

    def parseXML(self, file):
        dom = minidom.parse(file)

        domNodeList = dom.getElementsByTagName("node")
        for domNode in domNodeList:
            node = Node()
            attr = {}
            for domChild in domNode.childNodes:
                if domChild.nodeType == domNode.ELEMENT_NODE:
                    key = domChild.nodeName
                    value = domChild.firstChild.data
                    if key == 'id':
                        node.id = value
                    elif key == 'type':
                        node.type = value
                    else:
                        attr[key] = value
            node.attr = attr.copy()
            self.nodeList.append(node)

    def __init__(self, file):
        self.nodeList = []
        self.parseXML(file)

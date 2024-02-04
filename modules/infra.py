# Copyright 2024 Dirk Pleiter <dirk.pleiter@pm.me>

"""Module infra

Classes and methods for managing infrastructure-related information
"""

import xml.dom.minidom as minidom


class Node:
    id = None
    type = None
    attr = {}

    def toXML(self):
        return ""


class Infrastructure:
    nodeList = []

    def nNode(self):
        return len(self.nodeList)

    def parseXML(self, file):
        dom = minidom.parse(file)

        domNodeList = dom.getElementsByTagName("node")
        for domNode in domNodeList:
            node = Node()
            for domChild in domNode.childNodes:
                if domChild.nodeType == domNode.ELEMENT_NODE:
                    key = domChild.nodeName
                    value = domChild.firstChild.data
                    if key == 'id':
                        node.id = value
                    elif key == 'type':
                        node.type = value
                    else:
                        node.attr[key] = value
            self.nodeList.append(node)

    def __init__(self, file):
        self.parseXML(file)

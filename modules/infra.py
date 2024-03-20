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


class Connection:
    def __init__(self):
        self.endPoint = []
        self.lat = None
        self.bw = None
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

        domNodeList = dom.getElementsByTagName("connection")
        for domNode in domNodeList:
            connection = Connection()
            for domChild in domNode.childNodes:
                if domChild.nodeType == domNode.ELEMENT_NODE:
                    key = domChild.nodeName
                    value = domChild.firstChild.data
                    if key == 'endPoint':
                        connection.endPoint.append(value)
                    elif key == 'lat':
                        connection.lat = float(value)
                    elif key == 'bw':
                        connection.bw = float(value)
                    else:
                        connection.attr[key] = value
            if (len(connection.endPoint) != 2):
                print("Parse error")
                exit(1)
            self.connectionList.append(connection)

    def __init__(self, file):
        self.nodeList = []
        self.connectionList = []
        self.parseXML(file)

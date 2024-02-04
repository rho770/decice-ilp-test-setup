# Copyright 2024 Dirk Pleiter <dirk.pleiter@pm.me>

"""Module appl

Classes and methods for managing application-related information
"""

import xml.dom.minidom as minidom


class Container:
    id = None
    type = None
    nodeType = None
    attr = {}

    def toXML(self):
        return "FIXME: TO BE IMPLEMENTED"


class Application:
    containerList = []

    def nContainer(self):
        return len(self.containerList)

    def parseXML(self, file):
        dom = minidom.parse(file)

        domNodeList = dom.getElementsByTagName("container")
        for domNode in domNodeList:
            container = Container()
            for domChild in domNode.childNodes:
                if domChild.nodeType == domNode.ELEMENT_NODE:
                    key = domChild.nodeName
                    value = domChild.firstChild.data
                    if key == 'id':
                        container.id = value
                    elif key == 'type':
                        container.type = value
                    elif key == 'nodeType':
                        container.nodeType = value
                    else:
                        container.attr[key] = value
            self.containerList.append(container)

    def __init__(self, file):
        self.parseXML(file)

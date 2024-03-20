# Copyright 2024 Dirk Pleiter <dirk.pleiter@pm.me>

"""Module appl

Classes and methods for managing application-related information
"""

import xml.dom.minidom as minidom


class Container:

    def __init__(self):
        self.id = None
        self.type = None
        self.nodeType = None
        self.attr = {}

    def toXML(self):
        return "FIXME: TO BE IMPLEMENTED"


class Latency:

    def __init__(self):
        self.id = None
        self.containerId = []
        self.I = None
        self.limit = None
        self.attr = {}

    def toXML(self):
        return "FIXME: TO BE IMPLEMENTED"


class Application:
    def nContainer(self):
        return len(self.containerList)

    def nLatency(self):
        return len(self.latencyList)

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

        domNodeList = dom.getElementsByTagName("latency")
        for domNode in domNodeList:
            latency = Latency()
            for domChild in domNode.childNodes:
                if domChild.nodeType == domNode.ELEMENT_NODE:
                    key = domChild.nodeName
                    value = domChild.firstChild.data
                    if key == 'id':
                        latency.id = value
                    elif key == 'containerId':
                        latency.containerId.append(value)
                    elif key == 'I':
                        latency.I = float(value)
                    elif key == 'limit':
                        latency.limit = float(value)
                    else:
                        latency.attr[key] = value
            if (len(latency.containerId) != 2):
                print("Parse error")
                exit(1)
            self.latencyList.append(latency)

    def __init__(self, file):
        self.containerList = []
        self.latencyList = []
        self.parseXML(file)

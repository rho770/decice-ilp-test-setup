# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 15:19:13 2024

@author: Francesco Brandoli
"""

import xml.etree.ElementTree as ET

class Container:
    def __init__(self, container_data, index):
        self.id = index  # Use the index as the ID
        self.type = container_data['type']
        self.nodeType = container_data['nodeType']
        self.Ncore = container_data['Ncore']
        self.mainMemory = container_data['mainMemory']
        self.risk = container_data['risk']
        self.region = container_data['region']

class Node:
    def __init__(self, node_data, index):
        self.id = index  # Use the index as the ID
        self.type = node_data['type']
        self.Ncore = node_data['Ncore']
        self.mainMemory = node_data['mainMemory']
        self.risk = node_data['risk']
        self.region = node_data['region']
        self.power = node_data['power']
        self.eprice = node_data['eprice']

def parse_application_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    container_list = []
    
    for index, container in enumerate(root.findall('container')):
        container_data = {
            'type': container.find('type').text,
            'nodeType': container.find('nodeType').text,
            'Ncore': int(container.find('Ncore').text),
            'mainMemory': int(container.find('mainMemory').text),
            'risk': float(container.find('risk').text),
            'region': int(container.find('region').text),
        }
        container_list.append(Container(container_data, index))  # Pass index
    
    return container_list

def parse_infrastructure_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    node_list = []
    
    for index, node in enumerate(root.findall('node')):
        node_data = {
            'type': node.find('type').text,
            'Ncore': int(node.find('Ncore').text),
            'mainMemory': int(node.find('mainMemory').text),
            'risk': float(node.find('risk').text),
            'power': float(node.find('power').text),
            'eprice': float(node.find('eprice').text),
            'region': int(node.find('region').text),
        }
        node_list.append(Node(node_data, index))  # Pass index
    
    return node_list


class Application:
    def __init__(self, xml_file):
        self.containerList = parse_application_xml(xml_file)
    
    def nContainer(self):
        return len(self.containerList)
    
    def count_containers(self):
        cloud_count, edge_count = 0, 0
        zero_cloud, zero_edge = 0, 0
        for container in self.containerList:
            if 'cloud' in container.nodeType:
                cloud_count += 1
                if container.region == 0:
                    zero_cloud += 1 
            elif 'edge' in container.nodeType:
                edge_count += 1
                if container.region == 0:
                    zero_edge +=1
        return cloud_count, edge_count, zero_cloud, zero_edge
    
    def average_ncore(self):
        #Hardcoded - modify?
        avg_cloud = 4
        avg_edge = 4
        return avg_cloud, avg_edge
        
    def containers_per_region(self, region):
        cloud_count, edge_count = 0, 0
        for container in self.containerList:
            if 'cloud' in container.nodeType and region == container.region:
                cloud_count += 1
            elif 'edge' in container.nodeType and region == container.region:
                edge_count += 1
        return cloud_count, edge_count

class Infrastructure:
    def __init__(self, xml_file):
        self.nodeList = parse_infrastructure_xml(xml_file)
    
    def nNode(self):
        return len(self.nodeList)
    
    def max_eprice(self):
        """Calculate the maximum electricity price among the nodes."""
        if not self.nodeList:
            return None  # Handle empty node list case
        return max(node.eprice for node in self.nodeList)
    
    def min_eprice(self):
        """Calculate the maximum electricity price among the nodes."""
        if not self.nodeList:
            return None  # Handle empty node list case
        return min(node.eprice for node in self.nodeList)
    
    def max_risk(self):
        """Calculate the maximum risk for edge and cloud pods."""
        max_cloud_risk = max(node.risk for node in self.nodeList if 'cloud' in node.type)         
        max_edge_risk = max(node.risk for node in self.nodeList if 'edge' in node.type) 
        return max_cloud_risk, max_edge_risk

    def min_risk(self):
        """Calculate the maximum risk for edge and cloud pods."""
        min_cloud_risk = min(node.risk for node in self.nodeList if 'cloud' in node.type)         
        min_edge_risk = min(node.risk for node in self.nodeList if 'edge' in node.type) 
        return min_cloud_risk, min_edge_risk

    def power_consumption(self):
        #Hardcoded - modify?
        P_cloud = 392
        P_edge = 4
        return P_cloud, P_edge

    def ncores(self):
        
        Ncpu_cloud = 128
        Ncpu_edge  = 4
        return Ncpu_cloud, Ncpu_edge
    
    def count_nodes(self):
        cloud_count, edge_count = 0, 0
        for node in self.nodeList:
            if 'cloud' in node.type:
                cloud_count += 1
            elif 'edge' in node.type:
                edge_count += 1
        return cloud_count, edge_count
    
    def count_nodes_per_region(self, region):
        cloud_count, edge_count = 0, 0
        for node in self.nodeList:
            if 'cloud' in node.type and region == node.region:
                cloud_count += 1
            elif 'edge' in node.type and region == node.region:
                edge_count += 1
        return cloud_count, edge_count
    

    

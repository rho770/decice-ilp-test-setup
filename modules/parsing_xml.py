# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 15:19:13 2024

@author: Francesco Brandoli
"""

import xml.etree.ElementTree as ET

class Container:
    def __init__(self, container_data):
        self.id = container_data['id']
        self.type = container_data['type']
        self.nodeType = container_data['nodeType']
        self.Ncore = container_data['Ncore']
        self.mainMemory = container_data['mainMemory']
        self.risk = container_data['risk']
        self.region = container_data['region']
        self.request_id = container_data['request_id']
        self.r_time = container_data['r_time']
        self.arr_time = container_data['arr_time']


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
        self.activation = node_data['activation']

def parse_application_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    container_list = []
    
    for index, container in enumerate(root.findall('container')):
        container_data = {
            'id': int(container.find('id').text.split(':', 1)[1]),
            'type': container.find('type').text,
            'nodeType': container.find('nodeType').text,
            'Ncore': int(container.find('Ncore').text),
            'mainMemory': int(container.find('mainMemory').text),
            'risk': float(container.find('risk').text),
            'region': int(container.find('region').text),
            'r_time': float(container.find('r_time').text),
            'request_id': int(container.find('request_id').text),
            'arr_time' : float(container.find('arr_time').text),
        }
        container_list.append(Container(container_data))  # Pass index
    
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
            'activation': float(node.find('activation').text),
        }
        node_list.append(Node(node_data, index))  # Pass index
    
    return node_list


class Application:
    def __init__(self, xml_file):
        self.containerList = parse_application_xml(xml_file)
        self.xml_file = xml_file
    
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
    
    def count_requests(self):
        root = ET.parse(self.xml_file)
        request_ids = {container.request_id for container in self.containerList}
        return len(request_ids)
    
    def count_requests_in_window(self, t_start, t_end):
        root = ET.parse(self.xml_file)
        request_ids = {container.request_id for container in self.containerList if container.arr_time>= t_start and container.arr_time<=t_end}
        return len(request_ids)
    
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
   
    
    def filter_request_batch(self, batch_start, batch_size, output_xml_path=None):
        """
        Keep only containers belonging to a specific batch of requests.

        Args:
            batch_start: index of the first request inside the batch
            batch_size: number of unique requests per batch
            output_xml_path: if provided, writes filtered XML here

        Returns:
            max_arrival: the latest arr_time in the selected batch (or None)
        """
        # Parse XML and collect unique request IDs in order
        tree = ET.parse(self.xml_file)
        root = tree.getroot()
        unique_ids = []
        for elem in root.findall('container'):
            try:
                rid = int(elem.find('request_id').text)
            except (AttributeError, TypeError, ValueError):
                continue
            if rid not in unique_ids:
                unique_ids.append(rid)
        # Determine batch slice
        start = batch_start
        end = start + batch_size
        batch_ids = unique_ids[start:end]
        # Filter containers
        new_root = ET.Element(root.tag, root.attrib)
        for elem in root.findall('container'):
            try:
                rid = int(elem.find('request_id').text)
            except Exception:
                continue
            if rid in batch_ids:
                new_root.append(elem)
        # Write XML if requested
        if output_xml_path:
            ET.ElementTree(new_root).write(output_xml_path, encoding='utf-8', xml_declaration=True)
        # Rebuild list
        self.containerList = []
        for idx, elem in enumerate(new_root.findall('container')):
            data = {
                'id': int(elem.find('id').text.split(':',1)[1]),
                'type': elem.find('type').text,
                'nodeType': elem.find('nodeType').text,
                'Ncore': int(elem.find('Ncore').text),
                'mainMemory': int(elem.find('mainMemory').text),
                'risk': float(elem.find('risk').text),
                'region': int(elem.find('region').text),
                'r_time': float(elem.find('r_time').text),
                'request_id': int(elem.find('request_id').text),
                'arr_time': float(elem.find('arr_time').text),
            }
            self.containerList.append(Container(data))
        # Return last arrival time
        if not self.containerList:
            return None, None
        first = min(c.arr_time for c in self.containerList)
        last = max(c.arr_time for c in self.containerList)
        return first, last
    
    
    def filter_containers_by_arrival(self,
                                     min_arr: float,
                                     max_arr: float,
                                     output_xml_path: str = None):
        """
        Filter the original XML to keep only containers with
        min_arr <= arr_time < max_arr.

        Updates self.containerList and optionally writes filtered XML to output_xml_path.

        Args:
            min_arr: lower bound (inclusive)
            max_arr: upper bound (exclusive)
            output_xml_path: if provided, write filtered XML here
        """
        tree = ET.parse(self.xml_file)
        root = tree.getroot()

        # Create new root for filtered containers
        new_root = ET.Element(root.tag, root.attrib)
        for container in root.findall('container'):
            try:
                arr = float(container.find('arr_time').text)
            except (AttributeError, TypeError, ValueError):
                continue
            if min_arr <= arr < max_arr:
                new_root.append(container)

        # Write out if requested
        new_tree = ET.ElementTree(new_root)
        if output_xml_path:
            new_tree.write(output_xml_path, encoding='utf-8', xml_declaration=True)

        # Rebuild in-memory containerList
        self.containerList = []
        for index, container in enumerate(new_root.findall('container')):
            data = {
                'id': int(container.find('id').text.split(':', 1)[1]),
                'type': container.find('type').text,
                'nodeType': container.find('nodeType').text,
                'Ncore': int(container.find('Ncore').text),
                'mainMemory': int(container.find('mainMemory').text),
                'risk': float(container.find('risk').text),
                'region': int(container.find('region').text),
                'r_time': float(container.find('r_time').text),
                'request_id': int(container.find('request_id').text),
                'arr_time': float(container.find('arr_time').text),
            }
            self.containerList.append(Container(data))

    def trim_last_requests(self, batch_size):
        """
        Remove and return containers having the maximal request ID among self.containerList.
        """
        if not self.containerList:
            return [], []
        max_id = max(c.request_id for c in self.containerList)
        trimmed = [c for c in self.containerList if c.request_id == max_id]
        # Update ID for each trimmed container
        self.containerList = [c for c in self.containerList if c.request_id != max_id]
        print(len(self.containerList))
        min_id = min(c.request_id for c in trimmed)
        print('min_id',min_id)
        return trimmed, min_id
    

    def append_containers(self, containers):
        """
        Append a list of Container objects to self.containerList.
        """
        self.containerList.extend(containers)

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
    
    def set_node_activation(self, node_id, new_value):
        """
        Find the node with the given `node_id` and set its activation.
        Returns True if successful, False if no such node exists.
        """
        for node in self.nodeList:
            if node.id == node_id:
                node.activation = new_value
                return True
        return False
    
    def update_node_resources(self, node_id, cpu_delta, mem_delta):
        """
        After a pod is deployed on the specified node, deduct CPU cores (cpu_delta) and
        memory (mem_delta) from the node's available resources.
        Raises ValueError if the node doesn't exist or resources would go negative.
        """
        for node in self.nodeList:
            if node.id == node_id:
                if node.Ncore < cpu_delta or node.mainMemory < mem_delta:
                    print('Available', node.Ncore, node.mainMemory, 'requested', cpu_delta, mem_delta )
                    raise ValueError(f"Not enough resources on node {node_id}")
                node.Ncore -= cpu_delta
                node.mainMemory -= mem_delta
                return True
        raise ValueError(f"Node {node_id} not found")

        

    

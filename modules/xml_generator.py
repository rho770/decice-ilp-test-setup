
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 18:22:30 2024

@author: Francesco Brandoli
"""

import xml.etree.ElementTree as ET
import os
import sys
from node_risk_attribute import *
import random

BASEDIR = os.path.dirname(sys.argv[0])
bin_dir = os.path.join(BASEDIR, '../bin')
sys.path.append(bin_dir)

from parameters import *

# Define electricity prices for each region
electricity_prices = {
    1: 0.0921,  # Finland (FI)
    2: 0.1313,  # Estonia (EE)
    3: 0.1648,  # Lithuania (LT)
    4: 0.2169,  # Croatia (HR)
    5: 0.2543   # Ireland (IE)
}

def calculate_risk(nodetype):
    risk_attribute_samples = monte_carlo_risk_simulation(nodetype, num_samples=10000, alpha=0.5, beta=0.5)
    return round(extract_random_risk_sample(risk_attribute_samples),1)

# Function to generate a single node XML element
def generate_node(node_id, node_type, ncore, memory,  power, region):
    node = ET.Element("node")

    # Add node ID
    id_elem = ET.SubElement(node, "id")
    id_elem.text = f"{node_type}:{node_id}"

    # Add node type (cloud-cpu or edge-cpu)
    type_elem = ET.SubElement(node, "type")
    type_elem.text = node_type

    # Add CPU cores (cloud: 128, edge: 4)
    ncore_elem = ET.SubElement(node, "Ncore")
    ncore_elem.text = str(ncore)

    # Add main memory (cloud: 128 GiB, edge: 4 GiB)
    memory_elem = ET.SubElement(node, "mainMemory")
    memory_elem.text = str(memory)
    
    # Add energy consumption (cloud: 392 W, edge: 4 W)
    
    power_elem = ET.SubElement(node, "power")
    power_elem.text = str(power)

    # Add risk (using node_risk_attribute)
    risk_elem = ET.SubElement(node, "risk")
    risk_elem.text = f"{calculate_risk(node_type):.1f}"

    # Add region 
    region_elem = ET.SubElement(node, "region")
    region_elem.text = str(region)
    
    # Add electricity price
    electricity_price = electricity_prices.get(region, 0.0)  # Default to 0.0 if region not found
    price_elem = ET.SubElement(node, "eprice")
    price_elem.text = f"{electricity_price:.4f}"


    return node

# Function to generate the XML for a given number of cloud and edge nodes
# Each region contains the same number of cloud and edge nodes
def create_infrastructure_xml(cloud_nodes, edge_nodes, num_regions,selected_regions, filename, directory):
    infrastructure = ET.Element("infrastructure")

    # Calculate number of cloud and edge nodes per region
    cloud_nodes_per_region = cloud_nodes // num_regions
    edge_nodes_per_region = edge_nodes // num_regions

    # Distribute any remaining nodes evenly across regions
    remaining_cloud_nodes = cloud_nodes % num_regions
    remaining_edge_nodes = edge_nodes % num_regions

    node_id = 0
    # Generate nodes for each region
    for region in selected_regions:
        # Cloud nodes for the current region
        for i in range(cloud_nodes_per_region + (1 if remaining_cloud_nodes > 0 else 0)):
            node = generate_node(node_id, "cloud-cpu", 128, 128, 392, region)
            infrastructure.append(node)
            node_id += 1
        remaining_cloud_nodes -= 1 if remaining_cloud_nodes > 0 else 0

        # Edge nodes for the current region
        for i in range(edge_nodes_per_region + (1 if remaining_edge_nodes > 0 else 0)):
            node = generate_node(node_id, "edge-cpu", 4, 4, 4, region)
            infrastructure.append(node)
            node_id += 1
        remaining_edge_nodes -= 1 if remaining_edge_nodes > 0 else 0

    # Create the tree and write it to a file
    tree = ET.ElementTree(infrastructure)
    input_dir = os.path.join("../data/input", directory)
    output_dir = os.path.join("../data/output", directory)
    
    # Create the directories for input and output files.
    if os.path.exists(input_dir):
        print(f"The directory '{input_dir}' already exists.")
    else:
        print(f"The directory '{input_dir}' does not exist.")
        os.makedirs(input_dir)
        os.makedirs(output_dir)
        print(f"Directories '{input_dir}' and {output_dir} created successfully.")
    
    filepath = os.path.join(input_dir, filename)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)

    print(f"XML file '{filename}' created with {cloud_nodes} cloud nodes and {edge_nodes} edge nodes distributed across {num_regions} regions.")
    
    
# Function to generate the application XML file
def create_application_xml(cloud_containers, edge_containers, selected_regions, filename, directory):
    application = ET.Element("application")

    # Generate cloud containers
    for i in range(cloud_containers):
        container = generate_container(i, "cloud-cpu", selected_regions)
        application.append(container)

    # Generate edge containers
    for i in range(edge_containers):
        container = generate_container(cloud_containers + i, "edge-cpu", selected_regions)
        application.append(container)

    # Create the tree and write it to a file
    tree = ET.ElementTree(application)
    input_dir = os.path.join("../data/input", directory)
    filepath = os.path.join(input_dir, filename)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)

    print(f"XML file '{filename}' created with {cloud_containers} cloud containers and {edge_containers} edge containers.")

# Function to generate a single container XML element
def generate_container(container_id, node_type, selected_regions, ncore=4, memory=4,r_max = 0.7, p_e = p_e):
    container = ET.Element("container")

    # Add container ID
    id_elem = ET.SubElement(container, "id")
    id_elem.text = f"global:{container_id}"

    # Add container type (cloud or edge)
    type_elem = ET.SubElement(container, "type")
    type_elem.text = "global-service" 

    # Add node type (cloud-cpu or edge-cpu)
    node_type_elem = ET.SubElement(container, "nodeType")
    node_type_elem.text = node_type

    # Add CPU cores (always 4)
    ncore_elem = ET.SubElement(container, "Ncore")
    ncore_elem.text = str(ncore)

    # Add main memory (always 4 GiB)
    memory_elem = ET.SubElement(container, "mainMemory")
    memory_elem.text = str(memory)

    # Add risk (always 0.7 - High Risk)
    risk_elem = ET.SubElement(container, "risk")
    risk_elem.text = str(r_max)

    # Add region (random integer within the range of regions specified)
    # Caveat: in case region is not specified, we assign the value 0
    region_elem = ET.SubElement(container, "region")
    #Probability of region, being specified
    
    if random.random() < p_e :
        region_elem.text = str(random.choice(selected_regions))
    else :
        region_elem.text = str(0)

    return container

def configuration(cloud_nodes,edge_nodes, cloud_containers, edge_containers, selected_regions, p_e):

    infra_file = f"Ncloud_{cloud_nodes}_Nedge_{edge_nodes}_E{selected_regions}.xml"
    appl_file = f"Pcloud_{cloud_containers}_Pedge_{edge_containers}_E{selected_regions}_pe{p_e}.xml"
    case_dir = f'Ncloud_{cloud_nodes}_Nedge_{edge_nodes}'
    
    return infra_file, appl_file, case_dir
    


# Main function to generate the XML files
def main():

    configurations = configuration(cloud_nodes,edge_nodes, cloud_containers, edge_containers, selected_regions, p_e)
    # Create the infrastructure and application XML files
    create_infrastructure_xml(cloud_nodes, edge_nodes, num_regions, selected_regions, configurations[0], configurations[2])
    create_application_xml(cloud_containers, edge_containers, selected_regions, configurations[1], configurations[2])

# Run the script
if __name__ == "__main__":
    main()

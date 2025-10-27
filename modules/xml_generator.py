
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 18:22:30 2024

@author: Francesco Brandoli
"""

import xml.etree.ElementTree as ET
import os
import sys
from node_risk_attribute import *
from poisson_arrivals import *
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

# Define Container's arrivals time 
arrivals = poisson_arrivals_in_window(lambda_rate, simulation_time)

def calculate_risk(nodetype):
    risk_attribute_samples = monte_carlo_risk_simulation(nodetype, num_samples=10000, alpha=0.5, beta=0.5)
    return round(extract_random_risk_sample(risk_attribute_samples),4)

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
    risk_elem.text = f"{calculate_risk(node_type):.4f}"

    # Add region 
    region_elem = ET.SubElement(node, "region")
    region_elem.text = str(region)
    
    # Add electricity price
    electricity_price = electricity_prices.get(region, 0.0)  # Default to 0.0 if region not found
    epsilon = 7e-2
    random_vector = random.uniform (1-epsilon, 1+epsilon)
    price_elem = ET.SubElement(node, "eprice")
    price_elem.text = f"{electricity_price*random_vector:.4f}"
    
    # Add activation status (Empty infrastructure)
    activation_status = ET.SubElement(node, "activation")
    activation_status.text = str(0)


    return node

# Function to generate the XML for a given number of cloud and edge nodes
# Each region contains the same number of cloud and edge nodes
def create_infrastructure_xml(cloud_nodes_per_region,edge_nodes_per_region, selected_regions,filename, directory):
    infrastructure = ET.Element("infrastructure")
    node_id = 0

    for region in selected_regions:
        # generate cloud nodes
        for _ in range(cloud_nodes_per_region):
            node = generate_node(node_id,node_type="cloud-cpu", ncore=128, memory=128,power=392,region=region)
            infrastructure.append(node)
            node_id += 1

        # generate edge nodes
        for _ in range(edge_nodes_per_region):
            node = generate_node(node_id,node_type="edge-cpu", ncore=4, memory=4,power=4,region=region)
            infrastructure.append(node)
            node_id += 1

    # write out XML exactly as before…
    tree = ET.ElementTree(infrastructure)
    input_dir  = os.path.join("../data/input",  directory)
    output_dir = os.path.join("../data/output", directory)
    os.makedirs(input_dir,  exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(input_dir, filename)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)

    print(f"XML file '{filename}' created with "
          f"{cloud_nodes_per_region} cloud-nodes and "
          f"{edge_nodes_per_region} edge-nodes in each of "
          f"{len(selected_regions)} regions.")
   
    
# Function to generate the application XML file
def create_application_xml(cloud_containers, edge_containers, user_region, filename, directory, initial_id = 0):
    application = ET.Element("application")
 
    # Decide which cloud containers are heavy (10%)
    big_cloud_count = max(1, cloud_containers // 10)  # at least 1 if nonzero
    big_cloud_ids = set(random.sample(range(cloud_containers), big_cloud_count)) # heavy container have random id
    print('big id', big_cloud_ids)
    # Generate cloud containers
    for i in range(cloud_containers):
        if i in big_cloud_ids:
            container = generate_container(i + initial_id, "cloud-cpu", user_region, arrival_label, request_id,
                                           ncore=128, memory=128)
        else:
            container = generate_container(i + initial_id, "cloud-cpu", user_region, arrival_label, request_id)
        application.append(container)
        
    # Generate edge containers
    for i in range(edge_containers):
        container = generate_container(cloud_containers + i+initial_id, "edge-cpu", user_region, arrival_label, request_id)
        application.append(container)

    # Create the tree and write it to a file
    tree = ET.ElementTree(application)
    input_dir = os.path.join("../data/input", directory)
    filepath = os.path.join(input_dir, filename)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)

    print(f"XML file '{filename}' created with {cloud_containers} cloud containers and {edge_containers} edge containers.")

def create_queue_application_xml(request_specs, user_region,
                           filename, directory, initial_id=0):
    """
    request_specs: list of (n_cloud, n_edge) pairs, one per request
    e.g. [(2,1),   # request 0 needs 2 clouds + 1 edge
          (1,3),   # request 1 needs 1 cloud  + 3 edges
          …]
    """
    application = ET.Element("application")
    current_id = initial_id
    
    total_cloud = sum(n_cloud for n_cloud, _ in request_specs)

    
    # Set a 10% of "heavier" cloud containers
    big_cloud_count = max(1, total_cloud // 10) 
    big_cloud_indices = set(random.sample(range(total_cloud), big_cloud_count))
    
    # this index tracks the "nth cloud container overall"
    global_cloud_index = 0  

    for request_id, (n_cloud, n_edge) in enumerate(request_specs):
        # we consider different users spread in the 5 regions
        user_region = random.choice([0] + selected_regions)
        # Cloud containers
        for _ in range(n_cloud):
            if global_cloud_index in big_cloud_indices:
                c = generate_container(current_id, "cloud-cpu", user_region,
                                       arrival_label, request_id,
                                       ncore=128, memory=128)
            else:
                c = generate_container(current_id, "cloud-cpu", user_region,
                                       arrival_label, request_id)
            application.append(c)
            current_id += 1
            global_cloud_index += 1

        # Edge containers
        for _ in range(n_edge):
            c = generate_container(current_id, "edge-cpu", user_region,
                                   arrival_label, request_id)
            application.append(c)
            current_id += 1
            
    # write XML out
    tree = ET.ElementTree(application)
    input_dir = os.path.join("../data/input", directory)
    os.makedirs(input_dir, exist_ok=True)
    filepath = os.path.join(input_dir, filename)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)

    total_cloud = sum(c for c, _ in request_specs)
    total_edge  = sum(e for _, e in request_specs)
    print(f"Created {filename}: {total_cloud} cloud & "
          f"{total_edge} edge containers across "
          f"{len(request_specs)} requests.")


def update_application_xml(cloud_containers, edge_containers, selected_regions, filename, directory, initial_id = 0):
    input_dir = os.path.join("../data/input", directory)
    os.makedirs(input_dir, exist_ok=True)
    filepath = os.path.join(input_dir, filename)

    # Check if file exists
    if os.path.exists(filepath):
        tree = ET.parse(filepath)
        application = tree.getroot()
    else:
        application = ET.Element("application")
        tree = ET.ElementTree(application)

    # Find highest numeric ID from existing containers
    max_id = -1
    for container in application.findall("container"):
        id_elem = container.find("id")
        if id_elem is not None and id_elem.text and id_elem.text.startswith("global:"):
            try:
                num = int(id_elem.text.split(":")[1])
                max_id = max(max_id, num)
            except (IndexError, ValueError):
                continue

    next_id = max_id + 1
    # Append cloud containers
    for i in range(cloud_containers):
        container = generate_container(next_id + i +initial_id, "cloud-cpu", selected_regions)
        application.append(container)
        last_id = next_id + i +initial_id

    # Append edge containers
    for i in range(edge_containers):
        container = generate_container(next_id + initial_id+ cloud_containers + i, "edge-cpu", selected_regions)
        application.append(container)

    # Write back to the file
    tree.write(filepath, encoding="utf-8", xml_declaration=True)


# Function to generate a single container XML element
def generate_container(container_id, node_type, user_region, arrival_label, request_id, ncore=4, memory=4,r_max = r_max):
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

    # Add risk
    risk_elem = ET.SubElement(container, "risk")
    risk_elem.text = str(r_max)

    # Add region (random integer within the range of regions specified)
    # Caveat: in case region is not specified, we assign the value 0
    # Caveat: Edge pods are deployed only in the user's region
    region_elem = ET.SubElement(container, "region")
    
    if node_type == "edge-cpu" :
        region_elem.text = str(user_region)
    else :
        
        region_elem.text = str(random.choice([0, random.choice(selected_regions)]))
        
    # Add running time (For now fixed)
    running_time = ET.SubElement(container, "r_time")
    running_time.text = str(24) #[hours]
    
    if arrival_label == True:
        
        # Add request ID
        request_id_elem = ET.SubElement(container, "request_id")
        request_id_elem.text = str(request_id)
        
        # Add poissonian arrival time 
        arrival_time = ET.SubElement(container, "arr_time")    
        arrival_time.text = str(arrivals[request_id]) #[hours]
        
    return container

def configuration(cloud_nodes,edge_nodes, cloud_containers, edge_containers, selected_regions, user_region):

    infra_file = f"Ncloud_{cloud_nodes}_Nedge_{edge_nodes}_E{selected_regions}.xml"
    appl_file = f"Pcloud_{cloud_containers}_Pedge_{edge_containers}_E{selected_regions}.xml"
    case_dir = f'Ncloud_{cloud_nodes}_Nedge_{edge_nodes}'
    
    return infra_file, appl_file, case_dir


# Main function to generate the XML files
def main():

    configurations = configuration(cloud_nodes,edge_nodes, cloud_containers, edge_containers, selected_regions, user_region)
    # Create the infrastructure and application XML files
    create_infrastructure_xml(cloud_nodes, edge_nodes, selected_regions, configurations[0], configurations[2])
    create_application_xml(cloud_containers, edge_containers, user_region, configurations[1], configurations[2])

# Run the script
if __name__ == "__main__":
    main()

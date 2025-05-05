# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 13:57:51 2025

@author: Francesco Brandoli
"""

import numpy as np
import pulp
from time import time, strftime
import time
import os
import sys

import ilp_solver
from parsing_xml import *
from parameters import *

BASEDIR = os.path.dirname(sys.argv[0])
modules_dir = os.path.join(BASEDIR, '../modules')
sys.path.append(modules_dir)

from xml_generator import configuration, create_infrastructure_xml, create_application_xml, update_application_xml
from writing_output import *

configurations = configuration(cloud_nodes,edge_nodes, cloud_containers, edge_containers, selected_regions, user_region)

# Create the infrastructure and application XML files
create_infrastructure_xml(cloud_nodes, edge_nodes, selected_regions, configurations[0], configurations[2])
create_application_xml(0, 0, user_region, configurations[1], configurations[2] )

infra_file, appl_file, case_dir = configuration(cloud_nodes, edge_nodes, cloud_containers, edge_containers, selected_regions, user_region)
output_file = f"../data/output/{case_dir}/Ncloud_{cloud_nodes}_Nedge_{edge_nodes}_E{selected_regions}_Pcloud_{cloud_containers}_Pedge_{edge_containers}_user{user_region}.txt"
xml_path = os.path.join(BASEDIR, '../data/input', case_dir, appl_file )

# Create object for the infrastructure
infra = Infrastructure(os.path.join(BASEDIR, '../data/input', case_dir, infra_file))

overwrite_file(output_file)

# --------------------------------------------------------------------------
# Parameters for the queue
# --------------------------------------------------------------------------

window_duration = 3 # [s] # Time window for collecting incoming requests
simulation_time= 15 # [s] # Total time for the simulation 
lambda_rate = 1/2     # Mean number of requests per time step
poll_interval = 1.0   # time between each check/generation, in seconds

allocations = [] # List to keep track of the pods currently running on the infrastructure
max_id= 0

rng = np.random.default_rng(seed=42)

simulation_start = time.time()

# --------------------------------------------------------------------------
# M/D/1 Queue simulation starts here
# --------------------------------------------------------------------------

while (time.time() - simulation_start) < simulation_time:
    window_start = time.time()
    counter = 0

    print(f"Opening window for {window_duration} seconds...\n")

    while (time.time() - window_start) < window_duration:    
        arrivals = rng.poisson(lambda_rate)
        counter +=1
        print(f"[{time.strftime('%H:%M:%S')}] Requests arriving: {arrivals}")
        for arrival in range(arrivals): 
           if counter == 1 or not os.path.exists(xml_path):
               if not os.path.exists(xml_path):
                   print(f"The file '{BASEDIR+ '/../data/input/'+ case_dir+appl_file}' does NOT exist.")
               create_application_xml(cloud_containers, edge_containers, user_region, configurations[1], configurations[2], max_id)
               counter +=1

           else:
               update_application_xml(cloud_containers, edge_containers, user_region, configurations[1], configurations[2])
    
               print(f'Queue update {arrival+1} time')
        # Wait before next arrival tick
        time.sleep(poll_interval)
    
    if not os.path.exists(xml_path):
        print('No requests received...')
        continue
    
    # Create object for the application
    appl = Application(os.path.join(BASEDIR, '../data/input', case_dir, appl_file))

    # --------------------------------------------------------------------------
    # Solve the ILP problem
    # --------------------------------------------------------------------------
    
    print('solving ILP problem...')        
    problem = ilp_solver.main(appl, infra, output_file)
    
    # --------------------------------------------------------------------------
    # Update the infrastructure (scale memory, CPUs, activation costs)
    # --------------------------------------------------------------------------

    allocation_time = time.time()

    print('Updating nodes availability...')        
    
    for var in problem.variables():
        if var.name.startswith('X_') and var.varValue ==1:
            node_id= int(var.name.split('_')[2])
            container_id = int(var.name.split('_')[1])
            infra.set_node_activation(node_id, 1)
            
            for container in appl.containerList:
                if container.id == container_id:
                    infra.update_node_resources(node_id,container.Ncore, container.mainMemory)
                    for node in infra.nodeList:
                        if node.id == node_id:
                            allocations.append((container, node, allocation_time))
                max_id = container.id + 1

    # Update allocation list                
    # Should we do this also before the new allocation?
    for index, allocation in enumerate(allocations):
        if time.time()-allocation[2] > allocation[0].r_time:
            print(f"{time.time()-allocation[2]} > {allocation[0].r_time}")
            print(f'Removing {allocation[0].nodeType} pod {allocation[0].id} from {allocation[1].id}')

            infra.update_node_resources(allocation[1].id, -allocation[0].Ncore, -allocation[0].mainMemory)
            if 'edge' in allocation[1].type or allocation[1].mainMemory == 128:
                infra.set_node_activation(allocation[1].id, 0)
            if allocation[1].mainMemory == 128:
                print('the cloud node {node.id} is empty')

            allocations.pop(index)
            
    print(f"Solver Status: {problem.status}")
    for var in problem.variables():
         if var.varValue ==1:
             print(f"{var.name} = {var.varValue}")

    # Remove application xml file             
    os.remove(xml_path)
    print(f"'{xml_path}' has been deleted.")
    
    for node in infra.nodeList:
        if node.activation == 1:
            print('id:', node.id, node.type, 'activation:', node.activation, 'region:', node.region, node.mainMemory, node.Ncore)
    

print("Simulation completed.") 
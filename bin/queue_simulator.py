# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 13:57:51 2025

@author: Francesco Brandoli
"""

import numpy as np
import pulp
import time
import os
import sys

import ilp_solver
from parsing_xml import *
from parameters import *

BASEDIR = os.path.dirname(sys.argv[0])
modules_dir = os.path.join(BASEDIR, '../modules')
sys.path.append(modules_dir)

from xml_generator import *
from writing_output import *

configurations = configuration(cloud_nodes,edge_nodes, cloud_containers, edge_containers, selected_regions, user_region)

# Create the infrastructure and application XML files
create_infrastructure_xml(cloud_nodes, edge_nodes, selected_regions, configurations[0], configurations[2])

infra_file, appl_file, case_dir = configuration(cloud_nodes, edge_nodes, cloud_containers, edge_containers, selected_regions, user_region)
output_file = f"../data/output/{case_dir}/Ncloud_{cloud_nodes}_Nedge_{edge_nodes}_E{selected_regions}_Pcloud_{cloud_containers}_Pedge_{edge_containers}_user{user_region}.txt"
xml_path = os.path.join(BASEDIR, '../data/input', case_dir, appl_file )

# Create object for the infrastructure
infra = Infrastructure(os.path.join(BASEDIR, '../data/input', case_dir, infra_file))

# Create list of poissonian arrivals. Each request has Pcloud = 1 and Pedge = 1
request_specs = generate_request_specs(int(len(arrivals)), 1, 1)

# Create xml file and application object, containing all pods in the simulation
create_queue_application_xml(request_specs,user_region, configurations[1], configurations[2] )
appl = Application(os.path.join(BASEDIR, '../data/input', case_dir, appl_file))

overwrite_file(output_file)

# --------------------------------------------------------------------------
# Parameters for the queue
# --------------------------------------------------------------------------

window_duration = 3 # [s] Time window for collecting incoming requests

allocations = [] # List to keep track of the pods currently running on the infrastructure
trimmed_list = []
t = 0
rng = np.random.default_rng(seed=42)

# --------------------------------------------------------------------------
# M/D/1 Queue simulation starts here
# --------------------------------------------------------------------------

simulation_start = time.time()

while (time.time() - simulation_start) < simulation_time:
    window_start = time.time()
         

    # This simulate the collecting time 
    print(f"\nOpening window for {window_duration} seconds...")
    time.sleep(window_duration)

# --------------------------------------------------------------------------
# Clean the infastructure (containers deallocation)
# --------------------------------------------------------------------------
        
    for index, allocation in enumerate(allocations):
        if time.time()-allocation[2] > allocation[0].r_time:
            print(f"{time.time()-allocation[2]} > {allocation[0].r_time}")
            print(f'Removing {allocation[0].nodeType} pod {allocation[0].id} from {allocation[1].id}')

            infra.update_node_resources(allocation[1].id, -allocation[0].Ncore, -allocation[0].mainMemory)
            if 'edge' in allocation[1].type or allocation[1].mainMemory == 128:
                infra.set_node_activation(allocation[1].id, 0)
            if allocation[1].mainMemory == 128:
                print(f'the cloud node {allocation[1].id} is empty')

            allocations.pop(index)

# --------------------------------------------------------------------------
# Collecting requests for the ILP problem
# --------------------------------------------------------------------------

    # Select requests in time window
    appl.filter_containers_by_arrival(window_duration*t,window_duration*(t+1))
    print(f'Selecting request in ({window_duration*t}, {window_duration*(t+1)})')
    num_requests = appl.count_requests()

    # Append unresolved requests from previous cycle
    appl.append_containers(trimmed_list)
    num_requests_total = appl.count_requests()

    print(f'{num_requests} request arrived. In total {num_requests_total} requests to serve')

    t+=1
    if num_requests_total == 0:
        print('No requests to serve...continue')
        continue
    
    print(f'Time: {time.time() - window_start}s')

# --------------------------------------------------------------------------
# Solve the ILP problem
# --------------------------------------------------------------------------
    
    print('solving ILP problem...')        
    problem = ilp_solver.main(appl, infra, output_file)
    solver_status = problem.status
    solver_time = problem.solutionTime
    
    print(f'Checking feasibility of the solution...status= {solver_status}')
    
    trimmed_list = []
    while solver_status == -1:
        excluded_containers = appl.trim_last_requests()
        trimmed_list.extend(excluded_containers)
        print(f"{len(trimmed_list)} containers removed from the ILP and moved to next cycle")
        
        problem = ilp_solver.main(appl, infra, output_file)
        solver_status = problem.status

# --------------------------------------------------------------------------
# Update the infrastructure (scale memory, CPUs, activation costs)
# --------------------------------------------------------------------------

    print(f"Optimal solution found: solver took {solver_time:.2f}s")


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

    # Update allocation list                
    for index, allocation in enumerate(allocations):
        if time.time()-allocation[2] > allocation[0].r_time:
            print(f"{time.time()-allocation[2]} > {allocation[0].r_time}")
            print(f'Removing {allocation[0].nodeType} pod {allocation[0].id} from {allocation[1].id}\n')

            infra.update_node_resources(allocation[1].id, -allocation[0].Ncore, -allocation[0].mainMemory)
            if 'edge' in allocation[1].type or allocation[1].mainMemory == 128:
                infra.set_node_activation(allocation[1].id, 0)
            if allocation[1].mainMemory == 128:
                print(f'the cloud node {allocation[1].id} is empty')

            allocations.pop(index)
                
# --------------------------------------------------------------------------
# Print output
# --------------------------------------------------------------------------
       
    for var in problem.variables():
        if var.varValue ==1:
            print(f"{var.name} = {var.varValue}")
    
    for node in infra.nodeList:
        if node.activation == 1:
            print('id:', node.id, node.type, 'activation:', node.activation, 'region:', node.region, node.mainMemory, node.Ncore)
        
    
print("Simulation completed.") 
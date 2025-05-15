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

if cloud_nodes+edge_nodes <= 1000:
    k = 50 
elif cloud_nodes+edge_nodes > 1000:
    k = 25
window_duration = (k-1)/lambda_rate # [s] Time window for collecting incoming requests t<k/λ

allocations = [] # List to keep track of the pods currently running on the infrastructure
trimmed_list = [] # List to keep track of unresolved requests
sim_time= 0
service_start = 0
rng = np.random.default_rng(seed=42)

# --------------------------------------------------------------------------
# M/G/1 Queue simulation starts here
# --------------------------------------------------------------------------

while sim_time < simulation_time:
    print(f'Opening window:{sim_time}')
    # This simulates the collecting time 
    print(f"\nOpening window for {window_duration} seconds...")
    window_start = sim_time
    window_end = sim_time + window_duration

# --------------------------------------------------------------------------
# Clean the infastructure (containers deallocation)
# --------------------------------------------------------------------------
        
    for index, allocation in enumerate(allocations):
        if sim_time-allocation[2] > allocation[0].r_time:
            print(f"{sim_time-allocation[2]} > {allocation[0].r_time}")
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

    # Select requests in time window + requests arrived during the service
    appl.filter_containers_by_arrival(service_start,window_end)
    print(f'Selecting request in ({service_start}, {window_end})')
    num_requests = appl.count_requests()

    # Append unresolved requests from previous cycle
    appl.append_containers(trimmed_list)
    num_requests_total = appl.count_requests()

    print(f'{num_requests} request arrived. In total {num_requests_total} requests to serve')

    if num_requests_total == 0:
        print('No requests to serve...continue')
        sim_time = window_end
        continue
    
    # When the window is closed the batch is sent to the scheduler
    print('closing window :', window_end)
    

# --------------------------------------------------------------------------
# Solve the ILP problem
# --------------------------------------------------------------------------
    
    print('solving ILP problem...') 
    service_start = window_end       
    problem = ilp_solver.main(appl, infra, output_file)
    solver_status = problem.status
    
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
    solver_time = problem.solutionTime
    service_end = service_start+solver_time
    service_time = service_end-service_start
    print(f"Optimal solution found: solver took {solver_time:.2f}s")
    print(f"Service time = {service_time}")

    # Update simulation time    
    sim_time = window_end + solver_time

    allocation_time = sim_time

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
        if allocation_time-allocation[2] > allocation[0].r_time:
            print(f"{allocation_time-allocation[2]} > {allocation[0].r_time}")
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

    if not os.path.exists('response_time.txt') or os.path.getsize('response_time.txt') == 0:
        with open('response_time.txt', "w", encoding="utf-8") as f:
            f.write('lambda_rate solver_time total_requests N_pods Ncloud Nedge Status window_duration window_end ' + "\n")


    with open("response_time.txt", "a", encoding="utf-8") as f:
                 f.write(f"{lambda_rate} {solver_time} {num_requests_total} {len(appl.containerList)} {cloud_nodes} {edge_nodes} {solver_status} {window_duration} {window_end}"  + "\n")

    if not os.path.exists('queuing_time.txt') or os.path.getsize('queuing_time.txt') == 0:
        with open('queuing_time.txt', "w", encoding="utf-8") as f:
            f.write('Request_id container_id arrival_time queue_time solver_time total_time window_end lambda_rate' + "\n")

    for container in appl.containerList:
        with open("queuing_time.txt", "a", encoding="utf-8") as f:
                     f.write(f"{container.request_id} {container.id} {container.arr_time} {window_end-container.arr_time} {service_time} {sim_time-container.arr_time} {window_end} {lambda_rate}"  + "\n")
        
print("Simulation completed.") 
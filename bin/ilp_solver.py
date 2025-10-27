# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 11:09:20 2025

@author: Francesco Brandoli 

ILP formulation for Container-Node Assignment
"""

import os
import sys
from time import time
from pulp import *

start_time = time()
BASEDIR = os.path.dirname(sys.argv[0])
modules_dir = os.path.join(BASEDIR, '../modules')
sys.path.append(modules_dir)

from parsing_xml import *
from parameters import *
from writing_output import *
from xml_generator import configuration


def main(appl, infra, output_file):
    
    # Precompute valid (container, node) pairs
    valid_pairs = {}
    for container in appl.containerList:
        valid_nodes = [node for node in infra.nodeList if container.nodeType == node.type 
                       and node.risk <= container.risk 
                       and (container.region == 0 or container.region == node.region)
                       and (node.activation == 0 or container.nodeType == 'cloud-cpu')]
        valid_pairs[container] = valid_nodes
    
    # --------------------------------------------------------------------------
    # Generate ILP Problem
    # --------------------------------------------------------------------------
    
    problem_start = time()
    
    # Define decision variables
    decision_vars = { (container, node): LpVariable(f'X_{container.id}_{node.id}', cat='Binary')
                      for container, nodes in valid_pairs.items() for node in nodes }
    node_usage = { node: LpVariable(f'Y_{node.id}', cat='Binary') for node in infra.nodeList if node.type == 'cloud-cpu' }
    
    # Initialise problem
    problem = LpProblem("Container_Node_Assignment", LpMinimize)
    
    # Constraints
    for container in appl.containerList:
        problem += lpSum(decision_vars[(container, node)] for node in valid_pairs[container]) == 1, f"unicity_{container.id}"
    
    for node in infra.nodeList:
        valid_containers = [container for container in appl.containerList if (container, node) in decision_vars]
        problem += lpSum(decision_vars[(container, node)] * container.Ncore for container in valid_containers) <= node.Ncore, f"CPU_{node.id}"
        problem += lpSum(decision_vars[(container, node)] * container.mainMemory for container in valid_containers) <= node.mainMemory, f"memory_{node.id}"
    
        if node.type == 'cloud-cpu': 
            problem += lpSum(decision_vars[(container, node)] for container in valid_containers) <= node_usage[node] * len(valid_containers), f"NodeUsage_{node.id}"
            problem += lpSum(decision_vars[(container, node)] for container in valid_containers) >= node_usage[node], f"NodeUsage2_{node.id}"
        
    # Cost terms
    risk_terms_edge = [decision_vars[(container, node)] * node.risk for container, node in decision_vars if node.type == 'edge-cpu']
    risk_terms_cloud = [decision_vars[(container, node)] * node.risk for container, node in decision_vars if node.type == 'cloud-cpu']
    
    # Cloud nodes cores varies during the loop, keep them fixed to 128
    # PuLP doesn't allow for exactly 0 coefficient, add 1e-10 as arbitrarily small number
    el_terms_edge = [decision_vars[(container, node)] * (node.power/1000 * node.eprice * container.Ncore / node.Ncore) for container, node in decision_vars if node.type == 'edge-cpu']
    el_terms_cloud = [decision_vars[(container, node)] * 0.5*(node.power/1000 * node.eprice * container.Ncore / 128) for container, node in decision_vars if node.type == 'cloud-cpu']
    el_terms_act = [(node_usage[node])*(1-node.activation+1e-10) * node.power / 1000 * node.eprice * 0.5 for node in infra.nodeList if node.type == 'cloud-cpu']
    
    
    # Normalization 
    max_el_cloud = sum(infra.power_consumption()[0]/1000 * infra.max_eprice()*0.5*container.Ncore/128 for container in appl.containerList if container.nodeType == 'cloud-cpu')
    max_el_edge  = sum(infra.power_consumption()[1]/1000 * infra.max_eprice()  for container in appl.containerList if container.nodeType == 'edge-cpu')
    max_el_act  = sum(node.power/1000 * infra.max_eprice()*0.5 for node in infra.nodeList if node.type == 'cloud-cpu')

    
    max_risk_cloud = infra.max_risk()[0]
    max_risk_edge = infra.max_risk()[1]
    
    # Cost function (security)    
    f_risk_edge = lpSum(risk_terms_edge) / (edge_containers*max_risk_edge)  if edge_containers > 0 and max_risk_edge > 0 else 0
    f_risk_cloud = lpSum(risk_terms_cloud) / (cloud_containers*max_risk_cloud) if cloud_containers > 0 and max_risk_cloud > 0 else 0
    
    f_risk = (f_risk_cloud+f_risk_edge)/2
    
    # Cost function (electricity)
    f_el_edge = lpSum(el_terms_edge) / max_el_edge  if max_el_edge  > 0 else 0
    f_el_cloud = lpSum(el_terms_cloud) / max_el_cloud  if max_el_cloud  > 0 else 0
    f_el_act = lpSum(el_terms_act) / max_el_act  if max_el_act  > 0 else 0
    
    f_el = (f_el_cloud + f_el_edge + f_el_act)/3
    
    # Weights
    theta_risk = 0.5
    theta_el = 0.5
    
    # Add weighted cost functions to the problem
    problem += theta_risk * f_risk + theta_el * f_el
    
    problem_end = time()
    
    # --------------------------------------------------------------------------
    # Solve Problem and Display Results
    # --------------------------------------------------------------------------
    problem.solve() 
    results = []
    results.append(f"Solver Status: {LpStatus[problem.status]}")
    results.append(f"Objective Value: {value(problem.objective)}")
#   results.append(f"Number of cost function terms: {len(problem.objective.items())}")
#   results.append(f"Number of constraints: {len(problem.constraints)}")
#   results.append(f"Number of decision variables: {len(problem.variables())}")
    
    results.append(f"f_security value (norm): {value(f_risk)}")
#   results.append(f"f_security value: {value(f_risk_edge)*(edge_containers*max_risk_edge)+value(f_risk_cloud)*(cloud_containers*max_risk_cloud)}")
    results.append(f"f_security_cloud: {value(f_risk_cloud)} ")
    results.append(f"f_security_edge: {value(f_risk_edge)} ")
    
    results.append(f"f_electricity value (norm): {value(f_el)}")
#   results.append(f"f_electricity value: {value(f_el_cloud)*max_el_cloud+value(f_el_edge)*max_el_edge+value(f_el_act)*max_el_act}")
    results.append(f"f_electricity_cloud (norm): {value(f_el_cloud)}")
    results.append(f"f_electricity_edge (norm): {value(f_el_edge)}")
    results.append(f"f_electricity_activation (norm): {value(f_el_act)}")
    
    results.append(f"f_electricity_tot (norm): {f_el}")
    results.append(f"f_security_tot (norm): {f_risk}")
    
#   results.append(f"f_electricity_cloud (norm): {f_el_cloud}")
#   results.append(f"f_electricity_act (norm): {f_el_act}")
#   results.append(f"f_electricity_edge (norm): {f_el_edge}")
#   results.append(f"f_security_cloud (norm): {f_risk_cloud}")
#   results.append(f"f_security_edge (norm): {f_risk_edge}")

       
#   results.append(f"f_electricity : {(f_el_cloud)*max_el_cloud+value(f_el_edge)*max_el_edge+value(f_el_act)*max_el_act}")
#   results.append(f"f_security: {f_risk_edge*(edge_containers*max_risk_edge)+(f_risk_cloud)*(cloud_containers*max_risk_cloud)}")
#   results.append(f"Objective function: {theta_risk * f_risk + theta_el * f_el}")
    
#   results.append(f"Total execution time: {time() - start_time:.4f} s")
#   results.append(f"Problem creation time: {problem_end - problem_start:.4f} s")
    results.append(f"Solver time: {problem.solutionTime} s")
    
    
    for var in problem.variables():
         if var.varValue ==1:
             results.append(f"{var.name} = {var.varValue}")

    print_to_file(output_file, '\n'.join(results))

#   Output for queue simulation analysis         
    # if LpStatus[problem.status] == 'Optimal':
    #     with open(f"queue_distribution.txt", "a", encoding="utf-8") as f:
    #              f.write(f"{cloud_containers} {edge_containers} {cloud_nodes} {edge_nodes} {len(problem.constraints)} {len(problem.variables())} {problem.solutionTime}"  + "\n")
    
    # if LpStatus[problem.status] == 'Optimal':
    #     with open(f"../plots/Queue/Single_vs_batch/{simulation_time}_5_1/Queue_batch_b=24_bootstrap_1.txt", "a", encoding="utf-8") as f:
    #             f.write(f"{value(f_el_cloud)*max_el_cloud+value(f_el_edge)*max_el_edge+value(f_el_act)*max_el_act} {value(f_risk_edge)*(edge_containers*max_risk_edge)+value(f_risk_cloud)*(cloud_containers*max_risk_cloud)} {lambda_rate}"  + "\n")


    return problem

if __name__ == "__main__":
    infra_file, appl_file, case_dir = configuration(cloud_nodes, edge_nodes, cloud_containers, edge_containers, selected_regions, user_region)
    output_file = f"../data/output/{case_dir}/Ncloud_{cloud_nodes}_Nedge_{edge_nodes}_E{selected_regions}_Pcloud_{cloud_containers}_Pedge_{edge_containers}_user{user_region}.txt"

    overwrite_file(output_file)
    appl = Application(os.path.join(BASEDIR, '../data/input', case_dir, appl_file))
    infra = Infrastructure(os.path.join(BASEDIR, '../data/input', case_dir, infra_file))


    problem= main(appl,infra, output_file)
    print(LpStatus[problem.status])
    print(problem.solutionTime)
    

# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 16:17:40 2025

@author: Francesco Brandoli
"""
import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from pulp import *

# Add modules directory to path (adjust BASEDIR if needed)
BASEDIR = os.path.dirname(sys.argv[0])
modules_dir = os.path.join(BASEDIR, '../modules')
sys.path.append(modules_dir)

from parsing_xml import *
from parameters import *
from writing_output import *
from xml_generator import configuration

# Get configuration parameters (same as in your original code)
infra_file, appl_file, case_dir = configuration(cloud_nodes, edge_nodes, cloud_containers, edge_containers, selected_regions, user_region)

# Parse application and infrastructure XML files
appl = Application(os.path.join(BASEDIR, '../data/input', case_dir, appl_file))
infra = Infrastructure(os.path.join(BASEDIR, '../data/input', case_dir, infra_file))

# Precompute valid (container, node) pairs
valid_pairs = {}
for container in appl.containerList:
    for container in appl.containerList:
        valid_nodes = [node for node in infra.nodeList if container.nodeType == node.type 
                       and node.risk <= container.risk 
                       and (container.region == 0 or container.region == node.region)
                       and (node.activation == 0 or container.nodeType == 'cloud-cpu')]
        valid_pairs[container] = valid_nodes

def solve_ilp(theta_risk, theta_el):
    """
    Build and solve the ILP with a weighted sum objective defined by theta_risk and theta_el.
    Returns the normalized risk and electricity cost values.
    """
    # Create a new ILP problem instance
    problem = LpProblem("Container_Node_Assignment", LpMinimize)
    
    # Define decision variables
    decision_vars = { (container, node): LpVariable(f'X_{container.id}_{node.id}', cat='Binary')
                      for container, nodes in valid_pairs.items() for node in nodes }
    node_usage = { node: LpVariable(f'Y_{node.id}', cat='Binary') for node in infra.nodeList }
    
    # Constraints: ensure each container is assigned to exactly one node
    for container in appl.containerList:
        problem += lpSum(decision_vars[(container, node)] for node in valid_pairs[container]) == 1, f"unicity_{container.id}"
    
    # Node capacity constraints (CPU and memory) and node usage constraints
    for node in infra.nodeList:
        valid_containers = [container for container in appl.containerList if (container, node) in decision_vars]
        problem += lpSum(decision_vars[(container, node)] * container.Ncore for container in valid_containers) <= node.Ncore, f"CPU_{node.id}"
        problem += lpSum(decision_vars[(container, node)] * container.mainMemory for container in valid_containers) <= node.mainMemory, f"memory_{node.id}"
        problem += lpSum(decision_vars[(container, node)] for container in valid_containers) <= node_usage[node] * len(valid_containers), f"NodeUsage_{node.id}"
        problem += lpSum(decision_vars[(container, node)] for container in valid_containers) >= node_usage[node], f"NodeUsage2_{node.id}"
    
    
    # Objective Function
    risk_terms_edge = [decision_vars[(container, node)] * node.risk for container, node in decision_vars if node.type == 'edge-cpu']
    risk_terms_cloud = [decision_vars[(container, node)] * node.risk for container, node in decision_vars if node.type == 'cloud-cpu']
    
    el_terms_edge = [decision_vars[(container, node)] * (node.power/1000 * node.eprice * container.Ncore / node.Ncore) for container, node in decision_vars if node.type == 'edge-cpu']
    el_terms_cloud = [decision_vars[(container, node)] * 0.5*(node.power/1000 * node.eprice * container.Ncore / node.Ncore) for container, node in decision_vars if node.type == 'cloud-cpu']
    el_terms_act = [node_usage[node] * node.power / 1000 * node.eprice * 0.5 for node in infra.nodeList if node.type == 'cloud-cpu']
    
    max_el_cloud = sum(infra.power_consumption()[0]/1000 * 0.5*infra.max_eprice()*container.Ncore/128 for container in appl.containerList if container.nodeType == 'cloud-cpu')
    max_el_edge  = sum(infra.power_consumption()[1]/1000 * infra.max_eprice()  for container in appl.containerList if container.nodeType == 'edge-cpu')
    max_el_act  = sum(node.power/1000 * infra.max_eprice()*0.5 for node in infra.nodeList if node.type == 'cloud-cpu')
    
    min_el_cloud = sum(infra.power_consumption()[0]/1000 * 0.5*infra.min_eprice()*container.Ncore/128 for container in appl.containerList if container.nodeType == 'cloud-cpu')
    min_el_edge  = sum(infra.power_consumption()[1]/1000 * infra.min_eprice()  for container in appl.containerList if container.nodeType == 'edge-cpu')
    min_el_act  = sum(node.power/1000 * infra.min_eprice()*0.5 for node in infra.nodeList if node.type == 'cloud-cpu')
    
    
    max_risk_cloud = infra.max_risk()[0]
    max_risk_edge = infra.max_risk()[1]
    
    min_risk_cloud = infra.min_risk()[0]
    min_risk_edge = infra.min_risk()[1]
    
    #Penso che dovremmo introdurre il massimo rischio concesso per questa simulazione r_max 
    # e non considerare 1, in questo modo i dati saranno spaziati in maniera più uniforme
    f_risk_edge = (lpSum(risk_terms_edge)) / (edge_containers*max_risk_edge)
    f_risk_cloud = lpSum(risk_terms_cloud) / (cloud_containers*max_risk_cloud)
    
    f_risk = (f_risk_cloud+f_risk_edge)/2
    
    f_el_edge = (lpSum(el_terms_edge)) / (max_el_edge)
    f_el_cloud = (lpSum(el_terms_cloud)) / (max_el_cloud)
    f_el_act = (lpSum(el_terms_act)) / (max_el_act)
    
    f_el = (f_el_cloud + f_el_edge+f_el_act)/3
    
    # Objective: weighted sum of the two normalized functions.
    problem +=  theta_el * f_el + theta_risk * f_risk , "Weighted_Objective"
    
    # Solve the problem (you can adjust time limits and other solver options as needed)
    problem.solve()
#    print(f_el_act.value())
    # Return the obtained normalized objective values (if infeasible, they will be None)
    return value(f_risk), value(f_el), value(f_risk_edge), value(f_el_edge), value(f_risk_cloud), value(f_el_cloud)

# --------------------------
# Generate Pareto Front
# --------------------------

pareto_results = []
pareto_cloud = []
pareto_edge = []

# Sweep over weight values between 0 and 1. (For equal granularity, you can adjust num_points.)
num_points = 10
weights = np.linspace(0.1, 1, num_points)
for w in weights:
    theta_risk = w
    theta_el = 1 - w
    # Solve the ILP for this weight combination
    f_risk_val, f_el_val, f_risk_edge, f_el_edge, f_risk_cloud, f_el_cloud = solve_ilp(theta_risk, theta_el)
    print(f_el_val, f_risk_val, theta_risk, theta_el)
    if f_risk_val is not None and f_el_val is not None:
        pareto_results.append((theta_risk, f_risk_val, f_el_val))
        pareto_cloud.append((theta_risk, f_risk_cloud, f_el_cloud))
        pareto_edge.append((theta_risk, f_risk_edge, f_el_edge))
        
    else:
        print(f"Problem infeasible for weights: risk {theta_risk}, electricity {theta_el}")

pareto_results = np.array(pareto_results)
pareto_cloud = np.array(pareto_cloud)
pareto_edge = np.array(pareto_edge)


#print("Pareto Results (theta_risk, normalized risk, normalized electricity cost):")
#print(pareto_cloud)

# --------------------------
# Plot the Pareto Front
# --------------------------
plt.figure(figsize=(10,6))
plt.plot(pareto_results[:,1], pareto_results[:,2], 'o-', label="Pareto Front Total")
plt.plot(pareto_edge[:,1], pareto_edge[:,2], 'o-', label="Pareto Front edge")
plt.plot(pareto_cloud[:,1], pareto_cloud[:,2], 'o-', label="Pareto Front cloud")

plt.xlabel('Normalized Risk', fontsize=18)
plt.ylabel('Normalized Electricity Cost', fontsize=18)
#plt.title('Pareto Front: Risk vs Electricity Cost')
plt.grid(True)

plt.legend()
plt.legend(fontsize=18)

# Increase tick label size
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
# Annotate each point with the weight values
for i, (theta_risk, f_risk_val, f_el_val) in enumerate(pareto_results):
    theta_el = 1 - theta_risk
    # Adjust the text position slightly for clarity
 #   plt.text(f_risk_val, f_el_val, f"({theta_risk:.1f}, {theta_el:.1f})", fontsize=9,
#             ha='left', va='bottom')
plt.tight_layout()
plt.show()

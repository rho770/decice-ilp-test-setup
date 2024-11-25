#!/usr/bin/env python3

import os
import sys
from time import time
from pulp import *
import random

start_time = time()
BASEDIR = os.path.dirname(sys.argv[0])
modules_dir = os.path.join(BASEDIR, '../modules')
sys.path.append(modules_dir)

from parsing_xml import *
from parameters import *
from writing_output import *
from xml_generator import configuration

infra_file, appl_file, case_dir = configuration(cloud_nodes,edge_nodes, cloud_containers, edge_containers, selected_regions, p_e)
output_file = "../data/output/"+ case_dir + f'/Ncloud_{cloud_nodes}_Nedge_{edge_nodes}_E{selected_regions}_+Pcloud_{cloud_containers}_Pedge_{edge_containers}_pe{p_e}.txt' 
overwrite_file(output_file)

# --------------------------------------------------------------------------
# Parse application and infrastructure XML files
# --------------------------------------------------------------------------

appl = Application(os.path.join(BASEDIR,'../data/input', case_dir, appl_file))
infra = Infrastructure(os.path.join(BASEDIR,'../data/input',case_dir, infra_file ))

# --------------------------------------------------------------------------
# Generate ILP Problem
# --------------------------------------------------------------------------

problem_start = time()

# Define decision variables
variables = {}
for container in appl.containerList:
    for node in infra.nodeList:
        if (
            container.nodeType == node.type and 
            node.risk < container.risk and
            (container.region == 0 or container.region == node.region)
        ):
            var_name = f'X_{container.id}_{node.id}'
            variables[(container, node)] = LpVariable(var_name, cat='Binary')

        
# Initialise problem
problem = LpProblem("Container_Node_Assignment", LpMinimize)

# --------------------------------------------------------------------------
# Add constraints
# --------------------------------------------------------------------------

# Constraint: Each container must be assigned to exactly one node
for container in appl.containerList:
    problem += lpSum(variables[(container, node)] 
                     for node in infra.nodeList 
                     if (container, node) in variables) == 1, f"unicity_{container.id}"

# Constraint: Node resources must not be exceeded (CPU cores)
for node in infra.nodeList:
    problem += lpSum(variables[(container, node)] * container.Ncore
                     for container in appl.containerList
                     if (container, node) in variables) <= node.Ncore, f"CPU_{node.id}"

# Constraint: Node resources must not be exceeded (main memory)
for node in infra.nodeList:
    problem += lpSum(variables[(container, node)] * container.mainMemory
                     for container in appl.containerList
                     if (container, node) in variables) <= node.mainMemory, f"memory_{node.id}"

# --------------------------------------------------------------------------
# Create objective function
# --------------------------------------------------------------------------

# Objective function: Minimize costs and risks
cost_terms = []
el_terms = []
risk_terms = []

for container in appl.containerList:
    w = 1.0
    for node in infra.nodeList:
        if (container, node) in variables:
            cost_terms.append(w*variables[(container, node)])
            risk_terms.append(variables[(container, node)] * node.risk)
            el_terms.append(variables[(container, node)]* 
                            node.power * node.eprice * container.Ncore/ node.Ncore)
            w += 1

# Electricity weight function
weight_func = (appl.average_ncore()[0]/infra.ncores()[0]*appl.count_containers()[0]*infra.power_consumption()[0]+
               appl.average_ncore()[1]/infra.ncores()[1]*appl.count_containers()[1]*infra.power_consumption()[1]) * infra.max_eprice() 

weight_el = 0.6
weight_risk = 0.1
weight_cost = 0.3 

problem += weight_cost * lpSum(cost_terms) + weight_risk * (lpSum(risk_terms)/(appl.count_containers()[0]+appl.count_containers()[1] )) + weight_el*(1/weight_func)*lpSum(el_terms)
problem_end = time()

# --------------------------------------------------------------------------
# Solve Problem and Display Results
# --------------------------------------------------------------------------
solver_start = time()
problem.solve()
solver_end = time()

print_to_file(output_file, f'{problem}')

# Display variable values
for var in problem.variables():
    print_to_file(output_file, f"{var.name} = {var.varValue}")

# Display status and objective value
print_to_file(output_file, f"Solver Status: {LpStatus[problem.status]}")
print_to_file(output_file, f"Objective Value: {value(problem.objective)}")

# Display execution time
end_time = time()      
elapsed_time = end_time - start_time
print_to_file(output_file, f"Total execution time: {elapsed_time:.4f} s")
print_to_file(output_file, f"Problem creation time: {problem_end-problem_start:.4f} s" )
print_to_file(output_file, f"Solver time: {solver_end-solver_start:.4f} s" )
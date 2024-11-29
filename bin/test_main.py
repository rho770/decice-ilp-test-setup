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

Npod_c = appl.count_containers()[0] #Number of cloud pods to be scheduled
Npod_e = appl.count_containers()[1] #Number of edge pods to be scheduled
Nnode_c = infra.count_nodes()[0]    #Total number of cloud servers
Nnode_e = infra.count_nodes()[1]    #Total number of edge servers
n_cpu_c = appl.average_ncore()[0]   #Average number of CPU cores requested by a cloud pod
n_cpu_e = appl.average_ncore()[1]   #Average number of CPU cores requested by an edge pod
N_cpu_c = infra.ncores()[0]         #Number of CPU cores provided by a cloud node
N_cpu_e = infra.ncores()[1]         #Number of CPU cores provided by an edge node

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
risk_terms = []
el_terms = []

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
w_el = (n_cpu_c/N_cpu_c*Npod_c*infra.power_consumption()[0]+
        n_cpu_e/N_cpu_e*Npod_e*infra.power_consumption()[1]) * infra.max_eprice() 

# Cost weight function
nu_c = Nnode_c - (Npod_c*n_cpu_c/N_cpu_c) 
nu_e = Nnode_e - (Npod_e*n_cpu_e/N_cpu_e)
w_cost = ((N_cpu_c/ (2*n_cpu_c) )*(Nnode_c*(Nnode_c+1)-(nu_c-1)*nu_c)+
          (N_cpu_e/ (2*n_cpu_e) )*(Nnode_e*(Nnode_e+1)-(nu_e-1)*nu_e) )
         
# Theta_i
theta_cost = 0.1
theta_risk = 0.3
theta_el = 0.6 

# Add objective functions to the problem
problem += theta_cost * lpSum(cost_terms) / w_cost
problem += theta_risk * (lpSum(risk_terms)/(Npod_c+Npod_e ))
problem += theta_el*lpSum(el_terms)/w_el

problem_end = time()

# --------------------------------------------------------------------------
# Solve Problem and Display Results
# --------------------------------------------------------------------------
solver_start = time()
problem.solve()
solver_end = time()

#print_to_file(output_file, f'{problem}')

# Display variable values
#for var in problem.variables():
#    print_to_file(output_file, f"{var.name} = {var.varValue}")

# Display status and objective value
print_to_file(output_file, f"Solver Status: {LpStatus[problem.status]}")
print_to_file(output_file, f"Objective Value: {value(problem.objective)}")
#print(problem.objective)
print(f"Solver Status: {LpStatus[problem.status]}")
print(f"Objective Value: {value(problem.objective)}")



# Display execution time
end_time = time()      
elapsed_time = end_time - start_time
print_to_file(output_file, f"Total execution time: {elapsed_time:.4f} s")
print_to_file(output_file, f"Problem creation time: {problem_end-problem_start:.4f} s" )
print_to_file(output_file, f"Solver time: {solver_end-solver_start:.4f} s" )
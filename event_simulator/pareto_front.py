# -*- coding: utf-8 -*-
"""
Discrete Event Simulation that generates a Pareto front curve.
"""
import xml.etree.ElementTree as ET
import simpy
import os
import sys
from time import time
import numpy as np
import matplotlib.pyplot as plt

# Setup directories and import custom modules
BASEDIR = os.path.dirname(sys.argv[0])
bin_dir =  os.path.join(BASEDIR, '../bin')
sys.path.append(bin_dir)
modules_dir = os.path.join(BASEDIR, '../modules')
sys.path.append(modules_dir)

from parameters import *
from parsing_xml import *
from writing_output import *
from xml_generator import configuration

# Get configuration parameters 
infra_file, appl_file, case_dir = configuration(cloud_nodes, edge_nodes, cloud_containers, edge_containers, selected_regions, user_region)

# Application and infrastructure XML files
appl_file = os.path.join(BASEDIR, '../data/input', case_dir, appl_file)
infra_file = os.path.join(BASEDIR, '../data/input', case_dir, infra_file)

output_file = f'../data/output/{case_dir}/DES_Ncloud_{cloud_nodes}_Nedge_{edge_nodes}_E{selected_regions}_Pcloud_{cloud_containers}_Pedge_{edge_containers}_user{user_region}.txt'
overwrite_file(output_file)

# ------------------------------------------------------------------
# Classes and functions
# ------------------------------------------------------------------
class Node:
    def __init__(self, env, node_id, node_type, main_memory, Ncore, risk, region, eprice, power, activation):
        self.env = env
        self.node_id = node_id
        self.node_type = node_type
        self.region = int(region)
        self.risk = float(risk)
        self.eprice = float(eprice)  
        self.total_memory = int(main_memory)
        self.total_cpu = int(Ncore)
        self.power = int(power)
        self.activation = int(activation)

        # Use simpy.Container for memory and CPU tracking
        self.memory = simpy.Container(env, init=self.total_memory, capacity=self.total_memory)
        self.cpu = simpy.Container(env, init=self.total_cpu, capacity=self.total_cpu)

    def __repr__(self):
        return (f"Node({self.node_id}, type={self.node_type}, region={self.region}, "
                f"risk={self.risk:.4f}, eprice={self.eprice:.4f}, "
                f"mem={self.memory.level}/{self.total_memory}, "
                f"cpu={self.cpu.level}/{self.total_cpu})")
    
class Pod:
    def __init__(self, pod_id, required_node_type, required_memory, required_risk, required_region, required_cpu):
        self.pod_id = pod_id
        self.required_node_type = required_node_type  # e.g., "cloud-cpu" or "edge-cpu"
        self.required_memory = int(required_memory)
        self.required_risk = float(required_risk)
        self.required_region = int(required_region)
        self.required_cpu = int(required_cpu)

    def __repr__(self):
        return (f"Pod({self.pod_id}, type={self.required_node_type}, "
                f"mem={self.required_memory}, risk={self.required_risk}, region={self.required_region})")

def parse_nodes(xml_file, env):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    nodes = []
    for node in root.findall('node'):
        node_id = node.find('id').text
        node_type = node.find('type').text
        main_memory = node.find('mainMemory').text
        Ncore = node.find('Ncore').text
        risk = node.find('risk').text
        region = node.find('region').text
        eprice = node.find('eprice').text  
        power = node.find('power').text
        activation = node.find('activation').text
        nodes.append(Node(env, node_id, node_type, main_memory, Ncore, risk, region, eprice, power, activation))
    return nodes

def parse_pods(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    pods = []
    for container in root.findall('container'):
        pod_id = container.find('id').text
        required_node_type = container.find('nodeType').text
        main_memory = container.find('mainMemory').text
        required_risk = container.find('risk').text
        required_region = container.find('region').text
        required_cpu = container.find('Ncore').text  # Pod's required CPU cores
        pods.append(Pod(pod_id, required_node_type, main_memory, required_risk, required_region, required_cpu))
    return pods

def max_eprice(nodes):
    """Calculate the maximum electricity price among the nodes."""
    return max(node.eprice for node in nodes)

def max_risk(nodes):
    """Calculate the maximum risk for cloud and edge nodes."""
    max_cloud_risk = max(node.risk for node in nodes if 'cloud' in node.node_type)         
    max_edge_risk = max(node.risk for node in nodes if 'edge' in node.node_type) 
    return max_cloud_risk, max_edge_risk

def scheduler(env, pod_queue, nodes):
    global total_energy_cost, total_risk
    Ncloud_int = cloud_nodes*num_regions
    
    while pod_queue:
        yield env.timeout(1) # scheduling interval
        pod = pod_queue.pop(0) # submit first pod to the scheduler
        scheduled = False
        
        if 'cloud' in pod.required_node_type:       
            nodes = sorted(nodes, key=lambda n: (theta_risk * n.risk/max_risk(nodes)[0] + theta_price * (n.eprice/max_eprice(nodes)+(1-n.activation)*n.eprice/max_eprice(nodes))))
        elif 'edge' in pod.required_node_type:
            nodes = sorted(nodes, key=lambda n: (theta_risk * n.risk/max_risk(nodes)[1] + theta_price * (n.eprice/max_eprice(nodes))))

        for node in nodes:
            # Check node type
            if node.node_type != pod.required_node_type:
                continue
            # Check region: if pod.required_region != 0, node must be in that region
            if pod.required_region != 0 and node.region != pod.required_region:
                continue
            # Check risk: node's risk must be less than the pod's required risk
            if node.risk > pod.required_risk:
                continue
            # Check if the node has enough memory or CPU available
            if node.memory.level < pod.required_memory or node.cpu.level < pod.required_cpu:
                continue

            # if node not yet activated 
            if node.activation == 0 and "cloud" in node.node_type:
                norm_activation_cost =  (Ncloud_int*max_eprice(nodes) * 0.5*node.power / 1000)
#                print('rnom act', norm_activation_cost, max_eprice(nodes), node.power, Ncloud_int)
                activation_cost = 0.5*((node.eprice * node.power / 1000)) / norm_activation_cost
                node.activation =1
            else:
                activation_cost = 0
                
            
            # Allocate CPU and Memory
            yield node.cpu.get(pod.required_cpu)
            yield node.memory.get(pod.required_memory)
            scheduled = True
            # Compute normalized risk and energy cost
            if "cloud" in node.node_type:
                alpha = 2
                norm_risk = max_risk(nodes)[0] * cloud_containers
                norm_el = (cloud_containers/alpha) * (max_eprice(nodes) * node.power / 1000) * pod.required_cpu / node.total_cpu
            else:
                alpha = 1
                norm_risk = max_risk(nodes)[1] * edge_containers
                norm_el = (edge_containers/alpha) * (max_eprice(nodes) * node.power / 1000) * pod.required_cpu / node.total_cpu

            el_cost = ((node.eprice * node.power / 1000) * pod.required_cpu / node.total_cpu) / (alpha*norm_el)
            risk_cost = node.risk/norm_risk
            total_energy_cost += (el_cost+activation_cost) / 3  
            total_risk += risk_cost / 2
            
            results = []
            decision_var_name = f'X_{pod.pod_id}_{node.node_id}'
            id_, a, b = decision_var_name.split("_")

            results.append('Var_name, f_el(norm), f_risk(norm), f_obj(norm)')
            results.append(f"{id_}_{a.split(':')[1]}_{b.split(':')[1]}, {activation_cost}, {risk_cost / 2}, {theta_price*(el_cost) / 3 + theta_risk*risk_cost / 2}")
            
            print_to_file(output_file, '\n'.join(results))

            break
        if not scheduled:
            # Re-queue the unscheduled pod
            pod_queue.append(pod)

# ------------------------------------------------------------------
# Simulation function that runs one instance for given theta values
# ------------------------------------------------------------------
def run_simulation(theta_price, theta_risk):
    global total_energy_cost, total_risk
    # Reset metrics
    total_energy_cost = 0
    total_risk = 0

    # Set up a new simulation environment
    env = simpy.Environment()
    # Parse nodes and pods for the DES
    pods = parse_pods(appl_file)
    nodes = parse_nodes(infra_file, env)
    
    # Start the scheduler process
    env.process(scheduler(env, pods, nodes))
    
    # Run simulation until time 1000 (or adjust as needed)
    sim_start = time()
    env.run(until=1000)
    sim_end = time()
    
    solver_time = sim_end - sim_start
    objective_value = theta_price*total_energy_cost + theta_risk*total_risk
    return total_energy_cost, total_risk, objective_value, solver_time

# ------------------------------------------------------------------
# Loop over theta values and collect simulation results
# ------------------------------------------------------------------
results = []
theta_values = []
energy_costs = []
risks = []

# Create 'num_points' pairs for theta
num_points = 10
weights = np.linspace(0.1, 1, num_points)
for w in weights:
    theta_risk = w
    theta_price = 1 - w
    #print(f"Running simulation for theta_price={theta_price:.1f}, theta_risk={theta_risk:.1f} ...")
    cost, risk, obj_val, solver_time = run_simulation(theta_price, theta_risk)
    results.append({
        'theta_price': theta_price,
        'theta_risk': theta_risk,
        'total_energy_cost': cost,
        'total_risk': risk,
        'objective_value': obj_val,
        'solver_time': solver_time
    })
    theta_values.append((theta_price, theta_risk))
    energy_costs.append(cost)
    risks.append(risk)

# Optionally: print the results
for res in results:
    print(res)

# ------------------------------------------------------------------
# Plot the Pareto front (trade-off between risk and energy cost)
# ------------------------------------------------------------------
plt.figure(figsize=(8,6))
plt.plot(risks, energy_costs, marker='o', linestyle='-')
for i, (cost, risk) in enumerate(zip(energy_costs, risks)):
    plt.annotate(f"({theta_values[i][0]:.1f},{theta_values[i][1]:.1f})", (risk, cost))
plt.xlabel("Total Risk")
plt.ylabel("Total Energy Cost")
plt.title("Pareto Front: Energy Cost vs Risk")
plt.grid(True)
plt.tight_layout()
plt.savefig("pareto_front.png")
plt.show()

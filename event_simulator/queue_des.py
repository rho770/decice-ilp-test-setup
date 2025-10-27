import xml.etree.ElementTree as ET
import simpy
import os
import sys
import numpy as np
from time import time

# -----------------------------
# Configuration & Parameters
# -----------------------------
BASEDIR = os.path.dirname(sys.argv[0])
modules_dir = os.path.join(BASEDIR, '../modules')
bin_dir =  os.path.join(BASEDIR, '../bin')
sys.path.append(modules_dir)
output_file= BASEDIR+f'Queue_des.txt'
sys.path.append(bin_dir)

from parsing_xml import *    
from writing_output import * 
from parameters import *


# Simulation settings
theta_risk = 0.5                 # weight for risk
theta_price = 0.5                # weight for electricity price

# Deployment parameters
Ncloud = cloud_nodes
Ncloud_int = cloud_nodes*num_regions
Nedge  = edge_nodes
Pcloud = cloud_containers
Pedge  = edge_containers

# Output file
overwrite_file(f"data/Ncloud_{Ncloud}_Nedge_{Nedge}_E{selected_regions}_Pcloud_{Pcloud}_Pedge_{Pedge}.txt")

# -----------------------------
# Data Classes
# -----------------------------
class Node:
    def __init__(self, node_data, env):
        self.id = node_data['id']
        self.type = node_data['type']
        self.region = node_data['region']
        self.risk = node_data['risk']
        self.eprice = node_data['eprice']
        self.total_cpu = node_data['Ncore']
        self.total_memory = node_data['mainMemory']
        self.power = node_data['power']
        self.env = env
        self.activation = node_data['activation']

        # capacity containers
        self.cpu = simpy.Container(env, capacity=self.total_cpu, init=self.total_cpu)
        self.memory = simpy.Container(env, capacity=self.total_memory, init=self.total_memory)

class Pod:
    def __init__(self, container):
        self.id = container['id']
        self.arr_time = container['arr_time']
        self.required_nodeType = container['nodeType']
        self.required_cpu = container['Ncore']
        self.required_memory = container['mainMemory']
        self.required_risk = container['risk']
        self.required_region = container['region']
        self.service_time = container['r_time']

# -----------------------------
# XML Parsing
# -----------------------------
def parse_infrastructure_xml(xml_file, env):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    nodes = []
    for idx, node in enumerate(root.findall('node')):
        data = {
            'id': idx,
            'type': node.find('type').text,
            'Ncore': float(node.find('Ncore').text),
            'mainMemory': float(node.find('mainMemory').text),
            'risk': float(node.find('risk').text),
            'power': float(node.find('power').text),
            'eprice': float(node.find('eprice').text),
            'region': int(node.find('region').text),
            'activation': int(node.find('activation').text)
        }
        nodes.append(Node(data, env))
    return nodes


def parse_application_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    pods = []
    for container in root.findall('container'):
        data = {
            'id': int(container.find('id').text.split(':',1)[1]),
            'type': container.find('type').text,
            'nodeType': container.find('nodeType').text,
            'Ncore': int(container.find('Ncore').text),
            'mainMemory': int(container.find('mainMemory').text),
            'risk': float(container.find('risk').text),
            'region': int(container.find('region').text),
            'r_time': float(container.find('r_time').text),
            'arr_time': float(container.find('arr_time').text)
        }
        pods.append(Pod(data))
    return pods

# -----------------------------
# Cost & Risk Helpers
# -----------------------------
def max_eprice(nodes):
    return max(node.eprice for node in nodes)


def max_risk(nodes):
    cloud_r = max(n.risk for n in nodes if 'cloud' in n.type)
    edge_r  = max(n.risk for n in nodes if 'edge' in n.type)
    return cloud_r, edge_r

# -----------------------------
# Allocation Logic
# -----------------------------
# Global trackers
total_energy_cost = 0.0
total_risk = 0.0


def allocate_pod(env, pod, nodes, retry_interval=0.1, max_interval = 1):
    global total_energy_cost, total_risk
    
    allocation = False
    max_risk_cloud = max_risk(nodes)[0]
    max_risk_edge =max_risk(nodes)[1]
    max_price = max_eprice(nodes)
    
    if 'cloud' in pod.required_nodeType:       
        nodes = sorted(nodes, key=lambda n: (theta_risk/2 * n.risk/(cloud_containers*max_risk_cloud)+ theta_price/3 * (n.eprice/(cloud_containers*max_price))+theta_price/3*(1-n.activation)*n.eprice/(Ncloud_int*max_price)))
    elif 'edge' in pod.required_nodeType:
        nodes = sorted(nodes, key=lambda n: (theta_risk/2 * n.risk/(edge_containers*max_risk_edge) + theta_price/3 * (n.eprice/(edge_containers*max_price))))

    while allocation == False:
        for node in nodes:
            # 1) type match
            if node.type != pod.required_nodeType:
                continue
            # 2) region constraint
            if pod.required_region != 0 and node.region != pod.required_region:
                continue
            # 3) risk constraint
            if node.risk > pod.required_risk:
                continue
            # 4) capacity check
            if node.cpu.level < pod.required_cpu or node.memory.level < pod.required_memory:
                continue
            # 5) activation cost if first use
            if node.memory.level == node.total_memory and 'cloud' in node.type:
                #norm_act = int(Pcloud)*(max_eprice(nodes)*node.power/1000)*0.5
                act_cost = ((node.eprice*node.power/1000)*0.5)#/norm_act
#               print('node_activated')
            else:
                act_cost = 0
            # reserve resources
            yield node.cpu.get(pod.required_cpu)
            yield node.memory.get(pod.required_memory)
            print(f"Time {env.now:.2f}: Pod {pod.id} allocated to Node {node.id}")
#           print_to_file(output_file, (f"Time {env.now:.2f}: Pod {pod.id} allocated to Node {node.id} in region {node.region}"))
    
            # energy + risk metrics
            if 'cloud' in node.type:
                alpha = 2
                P = int(Pcloud)
                total_cpu=128
                #norm_r = max_risk(nodes)[0]*P
                #norm_e = P*(max_eprice(nodes)*node.power/1000)*(pod.required_cpu/node.total_cpu)
            else:
                P = int(Pedge)
                alpha = 1
                total_cpu = 4
#               norm_r = max_risk(nodes)[1]*P
#               norm_e = P*(max_eprice(nodes)*node.power/1000)*(pod.required_cpu/node.total_cpu)
            el = ((node.eprice*node.power/1000)*(pod.required_cpu/node.total_cpu))/alpha #/norm_e
            
            rc = node.risk#/(2*norm_r)
#           print_to_file('values_cloud_week.txt', (f"{el+act_cost} {rc} {lambda_rate} "))
            
            total_energy_cost += (act_cost + el)#/3
#           print(total_energy_cost)
            total_risk += rc#/2 
            # schedule release
            env.process(release_pod(env, node, pod))
            allocation = True
            return allocation
        print(f"Time {env.now:.2f}: Pod {pod.id} could not be allocated. Retry in {retry_interval} hour")
        yield env.timeout(retry_interval)
        retry_interval = min(retry_interval * 2, max_interval)
    return allocation


def release_pod(env, node, pod):
    yield env.timeout(pod.service_time)
    yield node.cpu.put(pod.required_cpu)
    yield node.memory.put(pod.required_memory)
#    print_to_file(output_file, (f"Time {env.now:.2f}: Pod {pod.id} released from Node {node.id}"))

    print(f"Time {env.now:.2f}: Pod {pod.id} released from Node {node.id}")

# -----------------------------
# Processes
# -----------------------------
def arrival_and_allocate(env, nodes, pods):
    for pod in pods:
        # wait until arrival
        yield env.timeout(pod.arr_time - env.now)
        
        print(f"Time {env.now:.2f}: Pod {pod.id} arrived")
#        print_to_file(output_file, (f"Time {env.now:.2f}: Pod {pod.id} arrived"))
        # immediately try to allocate
        env.process(allocate_pod(env, pod, nodes))

# -----------------------------
# Main Simulation
# -----------------------------
if __name__ == '__main__':
    env = simpy.Environment()

    # If rollout is considered
    infra_xml = f'../data/input/Ncloud_{Ncloud}_Nedge_{Nedge}/Rollout_Ncloud_{Ncloud}_Nedge_{Nedge}_E{selected_regions}.xml'
    # If rollout is not considered
    #infra_xml = f'../data/input/Ncloud_{Ncloud}_Nedge_{Nedge}/Ncloud_{Ncloud}_Nedge_{Nedge}_E{selected_regions}.xml'
    appl_xml  = f'../data/input/Ncloud_{Ncloud}_Nedge_{Nedge}/Pcloud_{Pcloud}_Pedge_{Pedge}_E{selected_regions}.xml'

    nodes = parse_infrastructure_xml(infra_xml, env)
    pods  = parse_application_xml(appl_xml)

    # start arrival/allocation process
    env.process(arrival_and_allocate(env, nodes, pods))

    start = time()
    env.run(until=simulation_time)
    end = time()

    # write results
    results = [
        f"Sim runtime: {end - start:.2f}s",
        f"Total energy cost: {total_energy_cost:.4f}",
        f"Total risk: {total_risk:.4f}",
        f"Objective = {theta_price*total_energy_cost + theta_risk*total_risk:.4f}"
    ]
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write('f_el f_risk lambda' + "\n")

    
    print_to_file(output_file, (f"{total_energy_cost} {total_risk} {lambda_rate}"))
    print("\n".join(results))

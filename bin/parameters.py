# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 17:56:44 2024

@author: Francesco Brandoli
"""
# number of cloud and edge nodes to generate per region
cloud_nodes = int(2)
edge_nodes = int(2)

# List regions allowed
selected_regions = [1,2,3,4,5]

# User's region
user_region = 3
num_regions = len(selected_regions)

# number of cloud and edge containers to generate in total
cloud_containers = 50
edge_containers = 50

# Maximum security risk level allowed for pods
r_max = 1

# Label to activate containers'attributes related to the queue (request_id, arrival_time)
arrival_label = True
request_id = 0

# Poissonian arrival rate [req/hour]
lambda_rate = 20

# Simulation Time [hour] 
simulation_time = 24
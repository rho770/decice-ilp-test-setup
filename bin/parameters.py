# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 17:56:44 2024

@author: Francesco Brandoli
"""
# number of cloud and edge nodes to generate per region
cloud_nodes = 10
edge_nodes = 15

# List regions allowed
selected_regions = [1, 2, 3, 4, 5]

# User's region
user_region = 4
num_regions = len(selected_regions)

# number of cloud and edge containers to generate in total
cloud_containers = 1
edge_containers = 1

# Maximum security risk level allowed for pods
r_max = 1

# Label to activate containers'attributes related to the queue (request_id, arrival_time)
arrival_label = True

# Poissonian arrival rate 
lambda_rate = 1

# Simulation Time [s] 
simulation_time = 15
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 11:18:43 2024

@author: Francesco Brandoli
"""
import numpy as np
import matplotlib.pyplot as plt


def normalize_0_1(data):
    min_val = np.min(data)
    max_val = np.max(data)
    normalized_data = (data - min_val) / (max_val - min_val)
    return normalized_data

def monte_carlo_risk_simulation(nodetype, num_samples=10000, alpha=0.5, beta=0):

    
    # Security Risk - uniform distribution to avoid assumptions(protect sensitive data)
    if 'cloud' in nodetype: #for cloud nodes we assume an upper limit of 0.7
        upper_limit = 0.7
        lower_limit = 0.0
    else: 
        upper_limit = 1.0
        lower_limit = 0.0
    
    # Reliability Risk -  Weibull distribution (node failure probability)
    scale_reliability, shape_reliability = 1.0, 1.5  #scale and shape, find proper values!
        
    # Perform num_samples montecarlo simulations
    security_risk_samples = np.random.uniform(lower_limit, upper_limit,num_samples)
    reliability_risk_samples = normalize_0_1(np.random.weibull(shape_reliability, num_samples) * scale_reliability)
    
    
    # Estimate total risk considering a weighted sum
    risk_attribute_samples = normalize_0_1(alpha * security_risk_samples + 
                              beta * reliability_risk_samples)  
    
    return risk_attribute_samples

def extract_random_risk_sample(risk_attribute_samples):
    return np.random.choice(risk_attribute_samples)

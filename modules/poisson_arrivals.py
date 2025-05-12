# -*- coding: utf-8 -*-
"""
Created on Thu May  8 15:55:58 2025

@author: Francesco Brandoli
"""
import numpy as np

def poisson_arrivals_in_window(lambda_rate, simulation_time):
    """
    Generate poissonian arrivals in a time window [0, T]

    Args:
        lambda_rate (float): arrival rate per unit time
        T (float): time interval considered

    Returns:
        np.ndarray: arrivals list in range [0, T]
    """
    arrival_times = []
    current_time = 0.0

    while True:

        inter_time = np.random.exponential(scale=1 / lambda_rate)
        current_time += inter_time
        if current_time > simulation_time:
            break
        arrival_times.append(current_time)

    return np.array(arrival_times)

def generate_request_specs(n_requests, n_cloud_per_request=1, n_edge_per_request=1):
    return [(n_cloud_per_request, n_edge_per_request) for _ in range(n_requests)]


if __name__ == "__main__":
    np.random.seed(42)  
    arrivals_list = poisson_arrivals_in_window(lambda_rate=2, simulation_time=10)
    print(arrivals_list)

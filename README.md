# Security- and Energy-Costs-Aware Pod Scheduling in the Compute Continuum

This repository contains the code, data, and supplementary materials for the paper "Multi-Objective Integer Linear Programming for Scheduling Kubernetes Pods Across the Compute Continuum." It includes the implementation of the MOILP (Multi-Objective Integer Linear
Programming)-based scheduler, as well as scripts for reproducing the experiments described in the paper.

## Table of content
- [About](#about)
- [Features](#features)
  - [MOILP solver](#MOILP-solver)
  - [Discrete Event Simulation](#Discrete-Event-Simulation)
  - [Pareto front comparison](#Pareto-front-comparison)
  - [M/G^b/1 Queue simulation with ILP-based scheduling](#mg^b1-queue-simulation-with-ilp-based-scheduling)
  - [M/G^b/1 Queue simulation with sequential scheduling](#mg^b1-queue-simulation-with-sequential-scheduling)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

### About ###
The Compute Continuum (CC) paradigm aims to seamlessly distribute and connect applications along a continuum of resources that spans from edge to cloud devices. This paradigm, however, introduces challenges in Pod deployment due to security requirements and energy costs. Inefficient Pod scheduling can, in fact, contribute to increased electricity costs and potential security risks, particularly in environments where workloads are security-sensitive and energy consumption is a major component of operational costs. In this paper, we propose a security- and energy-costs-aware scheduling approach for Kubernetes-managed Pods, formulated as a Multi-Objective Integer Linear
Programming (MOILP) problem. Our method targets minimizing security risks and electricity costs while maintaining a design readily adaptable to other container orchestration systems.

### Features

#### MOILP solver ####

The MOILP solver is based on the Python module PuLP (V.2.9.0). PuLP’s default solver, used during our test case, is the COIN-OR Branch and
Cut solver (CBC, V.2.10.3).
Following Section III.A of our paper, we propose a formulation based on two decision variables, a prefiltering step, and a multiobjective minimization problem.

#### Discrete Event Simulation ####

The Discrete Event Simulations (DES) are conducted by employing the process-based DES framework SimPy (V.4.1.1)

#### Pareto front comparison ####

We access the differences between an ILP- and DES-based Pareto fronts by using the hypervolume (HV) indicator described in the Python module Pymoo (V.0.6.1.5).
### Installation ###

1. Clone the repository:
```bash
git clone https://github.com/rho770/decice-ilp-test-setup.git
cd decice-ilp-test-setup
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
### Usage ###

#### Generating the Test Case ####
To generate a test case, modify the ```/bin/parameters.py``` script. The user is allowed to specify the following parameters:

- Number of edge and cloud nodes per region
- Number of edge and cloud containers 
- List of regions to be considered [See table below]
- User's region
- Maximum security risk level allowed for containers
- Poissonian arrival rate [requests/hour]
- Length of the simulation [hours]

The parameters are then used by the ```/modules/xml_generator.py``` script. This Python script will generate two directories inside ```/data/``` to store input and output files based on the infrastructure considered, and the XML files containing the information on nodes and containers. 

- Example name directory: ```Ncloud_10_Nedge_100, Ncloud_100_Nedge_1000, Ncloud_1000_Nedge_10000```
- Example .xml file name: ```Ncloud_10_Nedge_1000_E[3], Pcloud_1_Pedge_10_E[3]```

Each region will contain the inserted number of cloud and edge nodes. To minimize latency considerations, edge containers are forced to be deployed in the user's region. Cloud containers can be deployed on any of the regions considered by the test case. In case their regional dependencies are not specified, they are expressed with the label 0 in the XML file. 

| Rank | Country    |
|------|------------|
| 1    | Finland (FI) |
| 2    | Estonia (EE) |
| 3    | Lithuania (LT) |
| 4    | Croatia (HR) |
| 5    | Ireland (IE) |

#### Node Risk Assignment ####
The risk of each node is randomly assigned in ```modules/node_risk_attribute.py```, and is based on the following criteria:

Cloud nodes: The risk value is chosen from a uniform distribution in the range [0, 0.7].
Edge nodes: The risk value is selected from a uniform distribution in the range [0, 1], following the CVSS (Common Vulnerability Scoring System) rating, and then rescaled to fit within the [0, 1] range.

#### Simple test ####
To run the test, after modifying the parameter file, create the XML files for the infrastructure and application using ```modules/xml_generator.py```. To solve the ILP problem, run ```bin/ilp_solver.py```.

#### Output ####
The script generates an output file containing the following details:

- The cost function
- The constraints of the ILP problem
- The value of the decision variables
- The status of the ILP solver after execution
- The final value of the minimized cost function
- The time taken to run the test inluding I/O operations
- The time taken to solve the ILP

#### Pareto front comparison ####
After having modified the parameter file and generated the XML file contaning the infrastructure and the application, it is possible to run an evaluation of the two algorithms by comparing the hypervolume (HV) indicators of their pareto fronts. This is done automatically by the ```bin/ilp_vs_des.py``` script. 

#### M/G^b/1 Simulations ####
Specify the desired arrival rate of requests and simulation length (in hours) from the parameter file and generate the XML file of the infrastructure.
To simulate the ILP-based scheduler, open the file called ```bin/queue_simulator.py``` and select the number of edge and cloud Pods that reach the scheduler in each poissonian request as well as the size of the batch $b$. 
To simulate the sequential scheduler, run ```event_simulator/queue_des.py```, this script will consider as input the infrastructure described in the current parameter file.

### LICENSE ###
This project is licensed under the BSD 3-Clause License – see the [LICENSE](LICENSE) file for details.



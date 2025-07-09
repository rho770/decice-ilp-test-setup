# DECICE ILP Test Setup

This README describes how to generate and run a test case for the DECICE ILP (Integer Linear Programming) optimization problem.

### Generating the Test Case ###
To generate a test case, modify the /bin/parameters.py script. You are allowed to specify the following parameters:

- Number of edge and cloud nodes per region
- Number of edge and cloud containers 
- List of regions to be considered [See table below]
- User's region
- Maximum security risk level allowed for containers

The parameters are then used by the /modules/xml_generator.py script. This python script will generate two directories inside /data/ to store input and output files based on the infrastructure considered, and the xml files containing the information on nodes and containers. 

- Example name directory: Ncloud_10_Nedge_100, Ncloud_100_Nedge_1000, Ncloud_1000_Nedge_10000
- Example .xml file name: Ncloud_10_Nedge_1000_E[3], Pcloud_1_Pedge_10_E[3]

Each region will contain an equal number of cloud and edge nodes. To minimise latency considerations, edge containers are forced to be deployed in the user's region. Cloud containers can be deployed on any of the region considered by the test-case. Their regional dependencies are expressed with the label 0 in the .xml file. 

| Rank | Country    |
|------|------------|
| 1    | Finland (FI) |
| 2    | Estonia (EE) |
| 3    | Lithuania (LT) |
| 4    | Croatia (HR) |
| 5    | Ireland (IE) |

### Node Risk Assignment ###
The risk of each node is randomly assigned based on the following criteria:

Cloud nodes: The risk value is chosen from a uniform distribution in the range [0, 0.7].
Edge nodes: The risk value is selected from a uniform distribution in the range [0, 1], following the CVSS (Common Vulnerability Scoring System) rating, and then rescaled to fit within the [0, 1] range.

The containers have a fixed risk r_max = 0.7. This parameter can be modified inside the generate_container() function.

### Run the test ###
To run the test, execute the /bin/workflow.py script. The latter will execute xml.generator to create the input files and test_main.py to run the ILP solver.

### Output ###
The script generates an output file containing the following details:

- The cost function
- The constraints of the ILP problem
- The value of the decision variables
- The status of the ILP solver after execution
- The final value of the minimized cost function
- The time taken to run the test inluding I/O operations
- The time taken to solve the ILP 

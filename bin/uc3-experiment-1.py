#!/usr/bin/env python3

import os
import sys
import argparse

BASEDIR = os.path.dirname(sys.argv[0])
sys.path.append(BASEDIR + '/../modules')

import appl
import infra
import pulpintf


#------------------------------------------------------------------------------
# Initialisation
#------------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('--appl', dest='applCfg', type=str, required=True)
parser.add_argument('--infra', dest='infraCfg', type=str, required=True)
args = parser.parse_args()

appl = appl.Application(args.applCfg)
infra = infra.Infrastructure(args.infraCfg)
pulpInf = pulpintf.PulpInterface()

#------------------------------------------------------------------------------
# Generate ILP problem
#------------------------------------------------------------------------------

# Define decision parameters

pulpInf.addComment("Decision parameters:")

varList = []
for type in ['cloud-cpu', 'cloud-gpu', 'edge-cpu']:
    for iContainer in range(appl.nContainer()):
        if appl.containerList[iContainer].nodeType == type:
            for iNode in range(infra.nNode()):
                if infra.nodeList[iNode].type == type:
                    name = 'X_' + str(iContainer) + '_' + str(iNode)
                    varList.append(
                            {
                                "iContainer": iContainer,
                                "container": appl.containerList[iContainer],
                                "kNode": iNode,
                                "node": infra.nodeList[iNode],
                                "name": name
                             }
                        )
                    pulpInf.addComment("container=%s, node=%s" %
                            (
                                appl.containerList[iContainer].id,
                                infra.nodeList[iNode].id
                            )
                        )
                    pulpInf.addVarBinary(name)

varListAux = []
for var1 in varList:
    iContainer = var1["iContainer"]
    kNode = var1["kNode"]
    for var2 in varList:
        jContainer = var2["iContainer"]
        lNode = var2["kNode"]
        if (id(var1) != id(var2) and (iContainer < jContainer)):
            name = 'Y_' + str(iContainer) + '_' + str(kNode) + '_' + str(jContainer) + '_' + str(lNode)
            varListAux.append(
                {
                    "iContainer": iContainer,
                    "iContainerId": appl.containerList[iContainer].id,
                    "kNode": kNode,
                    "kNodeId": infra.nodeList[kNode].id,
                    "jContainer": jContainer,
                    "jContainerId": appl.containerList[jContainer].id,
                    "lNode": lNode,
                    "lNodeId": infra.nodeList[lNode].id,
                    "name": name
                }
            )
            pulpInf.addComment("Pair [(container=%s,node=%s),(container=%s,node=%s)]" %
                    (
                        var1["container"].id,
                        var1["node"].id,
                        var2["container"].id,
                        var2["node"].id
                    )
                )
            pulpInf.addVarBinary(name)
            
#exit(1)

# Initialise solver

pulpInf.addComment("Solver setup:")
pulpInf.defProblem("uc3-experiment-1")

# Add constraints

pulpInf.addComment(
    "Constraint: Ordinary and auxiliary decision variables need to match")

for varAux in varListAux:
    x1 = 'X_' + str(varAux["iContainer"]) + '_' + str(varAux["kNode"]);
    x2 = 'X_' + str(varAux["jContainer"]) + '_' + str(varAux["lNode"]);
    pulpInf.resetLinTerm()
    pulpInf.addLinTerm(+1, x1)
    pulpInf.addLinTerm(+1, x2)
    pulpInf.addLinTerm(-2, varAux["name"])
    pulpInf.addConstraint(">=", 0)
    pulpInf.resetLinTerm()
    pulpInf.addLinTerm(+1, x1)
    pulpInf.addLinTerm(+1, x2)
    pulpInf.addLinTerm(-2, varAux["name"])
    pulpInf.addConstraint("<=", 1)

pulpInf.addComment(
    "Constraint: All containers must be scheduled on exactly one node")

for container in appl.containerList:
    pulpInf.resetLinTerm()
    for var in varList:
        if id(container) == id(var["container"]):
            pulpInf.addLinTerm(1, var["name"])
    pulpInf.addConstraint("==", 1)

pulpInf.addComment("Constraint: Do not allocate more cores than available")

for node in infra.nodeList:
    pulpInf.resetLinTerm()
    for var in varList:
        if id(node) == id(var["node"]):
            pulpInf.addLinTerm(
                    var["container"].attr["Ncore"], var["name"]
                )
    pulpInf.addConstraint("<=", node.attr["Ncore"])

pulpInf.addComment("Constraint: Do not allocate more mainMemory than available")

for node in infra.nodeList:
    pulpInf.resetLinTerm()
    for var in varList:
        if id(node) == id(var["node"]):
            pulpInf.addLinTerm(
                    var["container"].attr["mainMemory"], var["name"]
                )
    pulpInf.addConstraint("<=", node.attr["mainMemory"])

# Constraints related to communication latencies

pulpInf.addComment(
    "Constraint: Communication latency limits")

for varAux in varListAux:
    for latency in appl.latencyList:
        if (varAux["iContainerId"] in latency.containerId and varAux["jContainerId"] in latency.containerId):
            for connection in infra.connectionList:
                if (varAux["kNodeId"] in connection.endPoint and varAux["lNodeId"] in connection.endPoint):
                    dt = connection.bw / connection.lat + latency.I / connection.bw
                    pulpInf.resetLinTerm()
                    pulpInf.addLinTerm(dt, varAux["name"])
                    pulpInf.addConstraint("<=", latency.limit)

# Objective function

pulpInf.addComment(
    "Objective function: Assume costs to increase for larger number of nodes")

list = []
for type in ['cloud-cpu', 'edge-cpu']:
    w = 1.0
    for node in infra.nodeList:
        if node.type == type:
            for var in varList:
                if id(node) == id(var["node"]):
                    list.append("%.1f * %s" % (w, var["name"]))
            w += 1.0
s = ''
for i in range(len(list)):
    if i < len(list)-1:
        s += "%s + " % (list[i])
    else:
        s += "%s" % (list[i])
pulpInf.defObjective(s)

# Call solver and print results

pulpInf.addComment("Call solver:")
pulpInf.callSolver()

pulpInf.addComment("Print values:")
pulpInf.prValues()

#------------------------------------------------------------------------------
# Print Pulp script
#------------------------------------------------------------------------------

pulpInf.print_lines()

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
parser.add_argument('--appl', dest='applCfg', type=str)
parser.add_argument('--infra', dest='infraCfg', type=str)
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
for type in ['cloud-cpu', 'edge-cpu']:
    for iContainer in range(appl.nContainer()):
        if appl.containerList[iContainer].nodeType == type:
            for iNode in range(infra.nNode()):
                if infra.nodeList[iNode].type == type:
                    name = 'X_' + str(iContainer) + '_' + str(iNode)
                    varList.append(
                          { "container": appl.containerList[iContainer],
                            "node": infra.nodeList[iNode],
                            "name": name
                          }
                        )
                    pulpInf.addComment("container=%s, node=%s" %
                        (appl.containerList[iContainer].id,
                         infra.nodeList[iNode].id))
                    pulpInf.addVar(name, 0, 1)

# Initialise solver

pulpInf.addComment("Solver setup:")
pulpInf.defProblem("experiment-1")

# Add constraints

pulpInf.addComment(
    "Constraint: All containers must be scheduled on exactly one node")

for container in appl.containerList:
    list = []
    for var in varList:
        if id(container) == id(var["container"]):
            list.append(var)
    if len(list) > 0:
        s = ''
        for i in range(len(list)):
            if i < len(list)-1:
                s += "%s + " % (list[i]["name"])
            else:
                s += "%s == 1" % (list[i]["name"])
        pulpInf.addConstraint(s)

pulpInf.addComment("Constraint: Do not allocate more cores than available")

for node in infra.nodeList:
    list = []
    for var in varList:
        if id(node) == id(var["node"]):
            list.append(var)
    if len(list) > 0:
        s = ''
        for i in range(len(list)):
            if i < len(list)-1:
                s += "%s + " % (list[i]["name"])
            else:
                s += "%s <= %s" % (list[i]["name"], node.attr["Ncore"])
        pulpInf.addConstraint(s)

# Constaint: Do not allocate more memory than available

# FIXME: to be done

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

pulpInf.print()

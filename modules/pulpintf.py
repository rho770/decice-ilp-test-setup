# Copyright 2024 Dirk Pleiter <dirk.pleiter@pm.me>

"""Module pulp-intf

Classes and methods for interfacing with Pulp
"""

import os
import pulp as P

class PulpInterface:
    script = []
    varList = []
    linTermList = []

    def __init__(self):
        self.script.append("import pulp as P\n")

    def print_lines(self):
        for line in self.script:
            print(line)

    def addLine(self, line):
        self.script.append(line)

    def addVar(self, name, min, max):
        self.varList.append(name)
        self.script.append("%s = P.LpVariable(\"%s\", %d, %d)" % (name, name, min, max))

    def addVarBinary(self, name):
        self.varList.append(name)
        self.script.append("%s = P.LpVariable(\"%s\", cat=\"Binary\")" % (name, name))

    def resetLinTerm(self):
        self.linTermList = []

    def addLinTerm(self, a, x):
        self.linTermList.append([a, x])

    def addConstraint(self, rel, rhs):
        if (len(self.linTermList) > 0):
            s = 'prob += '
            for i in range(len(self.linTermList)):
                if i < len(self.linTermList)-1:
                    s += "%s * %s + " % (
                            self.linTermList[i][0],
                            self.linTermList[i][1]
                    )
                else:
                    s += "%s * %s %s %s" % (
                            self.linTermList[i][0],
                            self.linTermList[i][1],
                            rel, rhs
                    )
            self.script.append(s)

    def addComment(self, s):
        self.script.append("# %s" % (s))

    def defProblem(self, name):
        self.script.append("prob = P.LpProblem(\"%s\", %s)" % (name, "P.LpMinimize"))

    def defObjective(self, s):
        self.script.append("prob += %s" % (s))

    def callSolver(self):
        self.script.append("status = prob.solve(P.GLPK(msg = 0))")
        self.script.append("print(P.LpStatus[status])")

    def prValues(self):
        for var in self.varList:
            self.script.append("print(\"" + var + " = %.1f\" % (P.value(" + var + ")))")

# Copyright 2024 Dirk Pleiter <dirk.pleiter@pm.me>

"""Module pulp-intf

Classes and methods for interfacing with Pulp
"""


class PulpInterface:
    script = []
    varList = []

    def __init__(self):
        self.script.append("import pulp as P\n")

    def print(self):
        for line in self.script:
            print(line)

    def addLine(self, line):
        self.script.append(line)

    def addVar(self, name, min, max):
        self.varList.append(name)
        self.script.append("%s = P.LpVariable(\"%s\", %d, %d)" % (name, name, min, max))

    def addConstraint(self, s):
        self.script.append("prob += %s" % (s))

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
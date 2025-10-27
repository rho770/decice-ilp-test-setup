# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 15:09:34 2025

@author: Francesco Brandoli
"""
import numpy as np
import matplotlib.pyplot as plt
from pareto_front_main import *

BASEDIR = os.path.dirname(sys.argv[0])
modules_dir = os.path.join(BASEDIR, '../event_simulator')
sys.path.append(modules_dir)

from pareto_front import *

risks_ilp = pareto_results[:,1] 
costs_ilp = pareto_results[:,2]
risks = np.array(risks)
energy_costs = np.array(energy_costs)
plt.figure(figsize=(10,6))
plt.plot(risks_ilp, costs_ilp, marker='.', linestyle='dashed', label="Pareto Front ILP", alpha= 0.8)
plt.plot(risks, energy_costs, marker='o', linestyle='-', label = "Pareto Front GA", alpha= 0.8)
# for i, (cost, risk) in enumerate(zip(energy_costs, risks)):
#     plt.annotate(f"({theta_values[i][0]:.1f},{theta_values[i][1]:.1f})", (risk, cost))

plt.xlabel(r'$f_{sec}(\theta)$', fontsize=20)
plt.ylabel(r'$f_{el}(1-\theta)$', fontsize=20)
plt.grid(True)

plt.legend()
plt.legend(fontsize=20)

# Increase tick label size
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)

plt.tight_layout()
plt.show()

##########################################################################
# Check plot
##########################################################################

# fig, ax = plt.subplots(figsize=(10,6))

# ax.plot(weights, risks_ilp, label=r'$f_{sec}^{ILP}$', linestyle='dashed')
# ax.plot(weights, risks, label = r'$f_{sec}^{des}$')
# ax.plot(weights, risks-risks_ilp, label = r'$\Delta_{sec}$')
# ax.plot(weights, energy_costs-costs_ilp, label = r'$\Delta_{el}$')


# ax.plot(weights, weights*risks_ilp+(1-weights)*costs_ilp, label=r'$f\left(\{X\}\right)$', linestyle='dashed')
# ax.plot(weights, weights*risks+(1-weights)*energy_costs, label = r'$f^{des}\left(\{X\}\right)$')
# ax.plot(weights, (risks+energy_costs)-(risks_ilp+costs_ilp), label=r'$\Delta_{el}+\Delta_{sec}$', linestyle='dotted')
# ax.plot(weights, costs_ilp, label= r'$f_{el}^{ILP}$', linestyle='dashed')
# ax.plot(weights, energy_costs, label = r'$f_{el}^{des}$')

# ax.set_xlabel(r'$\theta_{sec}$', fontsize=18)

# # Add secondary x-axis: 1 - weights
# secax = ax.secondary_xaxis('top', functions=(lambda x: 1-x, lambda x: 1-x))
# secax.set_xlabel(r'$\theta_{el}$', fontsize=18)

# ax.legend(loc='upper right')
# plt.show()

##########################################################################
# Estimate differences
##########################################################################
import numpy as np

risks_des, risks_ilp = weights*np.array(risks), weights*np.array(risks_ilp)
costs_des, costs_ilp = (1-weights)*np.array(energy_costs), (1-weights)*np.array(costs_ilp)

# 1) Risk improvements
delta_r   = risks_des - risks_ilp
avg_risk  = np.mean(delta_r)
max_risk  = np.max(delta_r)
tot_risk  = np.trapz(delta_r, x=risks_des)
max_pct_risk = np.max(100 * delta_r/risks_des)
avg_pct_risk = np.mean(100*delta_r/risks_des)

# 1A) Cost improvements
delta_c   = costs_des - costs_ilp
avg_cost  = np.mean(delta_c)
max_cost  = np.max(delta_c)
tot_cost  = np.trapz(delta_c, x=costs_des)
max_pct_cost = np.max(100 * delta_c/costs_des)
avg_pct_cost = np.mean(100*delta_c/costs_des)


# 2A) Euclidean joint improvement
euclid    = np.sqrt(delta_c**2 + delta_r**2)
avg_euc   = np.mean(100 * euclid / (risks_des+costs_des))
max_euc   = np.max(100 * euclid / (risks_des+costs_des))

print(f"Avg risk saving:   {avg_risk:.4f}")
print(f"Max risk saving:   {max_risk:.4f}")
print(f"Total risk saving: {tot_risk:.4f} (area units)")
print(f"Max % risk impr.: {max_pct_risk:.2f}%")
print(f"Avg % risk impr.: {avg_pct_risk:.2f}%")


print(f"Avg cost saving:   {avg_cost:.4f}")
print(f"Max cost saving:   {max_cost:.4f}")
print(f"Total cost saving: {tot_cost:.4f} (area units)")
print(f"Max % cost impr.: {max_pct_cost:.2f}%")
print(f"Avg % cost impr.: {avg_pct_cost:.2f}%")

print(f"Avg Euclid impr.:  {avg_euc:.4f}%")
print(f"Max Euclid impr.:  {max_euc:.4f}%")

from pymoo.indicators.hv import HV

# 2C) Hypervolume joint (re‑compute with reference point)
des = np.column_stack((risks_des, costs_des))
ilp = np.column_stack((risks_ilp, costs_ilp))

# Reference point requested:
max_risk= max(max(risks_ilp), max(risks_des))
max_cost= max(max(costs_ilp), max(costs_des))
ref_point = np.array([max_risk+max_risk*0.1, max_cost+max_cost*0.1])
hv = HV(ref_point=ref_point)

hv_des = hv(des)
hv_ilp = hv(ilp)

print(f"Reference point: {ref_point}")
print(f"HV(des) = {hv_des:.6f}")
print(f"HV(ilp) = {hv_ilp:.6f}")
print(f"ΔHV = {hv_ilp - hv_des:.6f} ({100*(hv_ilp-hv_des)/hv_des:.2f} % improvement)")

##############################################################################
# Check the quality of the reference point
##############################################################################

hv_des_values = [hv(des[i]) for i in range(len(des))]
hv_ilp_values = [hv(ilp[i]) for i in range(len(ilp))]

# --- contributions: hv(full) - hv(full without point i) ---
hv_des_without_i = np.array([ hv(np.delete(des, i, axis=0)) for i in range(len(des)) ])
hv_ilp_without_i = np.array([ hv(np.delete(ilp, i, axis=0)) for i in range(len(ilp)) ])

hv_des_contrib = hv_des - hv_des_without_i
hv_ilp_contrib = hv_ilp - hv_ilp_without_i

# Print results
print("\nPer-point: hv(single)    contribution (hv_full - hv_without_i)")
for i in range(len(des)):
    print(f"des[{i}]: hv(single) = {hv_des_values[i]:.9f}   contrib = {hv_des_contrib[i]:.9f}")
for i in range(len(ilp)):
    print(f"ilp[{i}]: hv(single) = {hv_ilp_values[i]:.9f}   contrib = {hv_ilp_contrib[i]:.9f}")

indices = np.arange(len(des))  # x-axis: solution indices
width = 0.35  # width of the bars

plt.figure(figsize=(12, 6))
plt.bar(indices - width/2, hv_des_contrib, width=width, label='HV(des)')
plt.bar(indices + width/2, hv_ilp_contrib, width=width, label='HV(ilp)')
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
plt.plot(risks, energy_costs, marker='o', linestyle='-', label = "Pareto Front DES", alpha= 0.8)
# for i, (cost, risk) in enumerate(zip(energy_costs, risks)):
#     plt.annotate(f"({theta_values[i][0]:.1f},{theta_values[i][1]:.1f})", (risk, cost))

plt.xlabel('Normalized Risk', fontsize=18)
plt.ylabel('Normalized Electricity Cost', fontsize=18)
#plt.title('Pareto Front: Risk vs Electricity Cost')
plt.grid(True)

plt.legend()
plt.legend(fontsize=18)

# Increase tick label size
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)

plt.tight_layout()
plt.show()

plt.figure(figsize=(10,6))
plt.plot(weights, risks_ilp, label='ilp risk', linestyle='dashed')
plt.plot(weights, risks, label = 'des_risk')
plt.plot(weights, risks_ilp+costs_ilp, label='ilp total', linestyle='dashed')
plt.plot(weights, risks+energy_costs, label = 'des_total')
plt.plot(weights, (risks+energy_costs)-(risks_ilp+costs_ilp), label='difference', linestyle='dotted')

plt.plot(weights, costs_ilp, label= 'ilp_costs', linestyle='dashed')
plt.plot(weights, energy_costs, label = 'des_costs')
plt.legend()
plt.show()


##########################################################################
import numpy as np

# your aligned arrays:
risks, risks_ilp = np.array(risks), np.array(risks_ilp)
costs_des, costs_ilp = np.array(energy_costs), np.array(costs_ilp)

# 1) Risk improvements
delta_r   = risks - risks_ilp
avg_risk  = np.mean(delta_r)
max_risk  = np.max(delta_r)
tot_risk  = np.trapz(delta_r, x=risks)
max_pct_risk = np.max(100 * delta_r/risks)

# 1A) Cost improvements
delta_c   = costs_des - costs_ilp
avg_cost  = np.mean(delta_c)
max_cost  = np.max(delta_c)
tot_cost  = np.trapz(delta_c, x=costs_des)
max_pct_cost = np.max(100 * delta_c/costs_des)


# 2A) Euclidean joint improvement

euclid    = np.sqrt(delta_c**2 + delta_r**2)
avg_euc   = np.mean(euclid)
max_euc   = np.max(euclid)

# 2C) Hypervolume joint (re‑compute with reference point)
r_ref = max(risks.max(), risks_ilp.max()) + 0.01
c_ref = max(costs_des.max(), costs_ilp.max()) + 0.01
# Flip both arrays if needed
hv_des = np.trapz(costs_des[::-1], x=risks[::-1])
hv_ilp = np.trapz(costs_ilp[::-1], x=risks_ilp[::-1])
delta_hv = hv_des - hv_ilp

print(f"Avg risk saving:   {avg_risk:.4f}")
print(f"Max risk saving:   {max_risk:.4f}")
print(f"Total risk saving: {tot_risk:.4f} (area units)")
print(f"Max % risk impr.: {max_pct_risk:.2f}%")

print(f"Avg cost saving:   {avg_cost:.4f}")
print(f"Max cost saving:   {max_cost:.4f}")
print(f"Total cost saving: {tot_cost:.4f} (area units)")
print(f"Max % cost impr.: {max_pct_cost:.2f}%")

print(f"Avg Euclid impr.:  {avg_euc:.4f}")
print(f"Max Euclid impr.:  {max_euc:.4f}")
print(f"Hypervolume Δ:     {delta_hv:.4f}")

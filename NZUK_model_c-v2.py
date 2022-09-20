#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Copyright (c) 2022 Andrew Williams
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# Part 3 of the net zero model - to analyse supply, demand and storage requirements 
# Andy Williams, Loughborough Uni, 2022


fig3 = plt.figure(figsize=(18,20))
ax3 = fig3.add_subplot(413)
ax3.set_xlim(GW_daily.index[0], GW_daily.index[-1])
#ax3.set_xlim(GW_daily.index[300], GW_daily.index[360])   # setup to zoom in to a chosen area
ax3.set(xlabel= 'Date', ylabel='Power GW', ylim=(0, 140), title='Daily electricity pricing and demand elasticity with %.0f weather' % year)
ax3.plot(GW_daily.index, Elec_df['elec_from_methane'], label = 'Original electricity from biomethane', color = 'seagreen')

ax30 = ax3.twinx()
ax30.set(ylabel='LCOE - £/MWh', ylim=(0, 2300))
ax30.plot(GW_daily.index, cost[1:366], label = 'electricity price', color = 'blue')


# New supply & demand graph taking elasticity into account
#=========================================================

elastic_mult_lo  = (1 - (1 / (0.0001 + (cost / LCOE_per_MWh)))) * Elasticity    # the 0.001 to fix div 0 error
elastic_mult_hi  = (cost / Average_LCOE) * Elasticity
elastic_demand   = [1]

for i in range(1, excess_energy.size):
    if elastic_mult_lo[i] < 0:
        e_demand = new_electrical_load[i] + (elastic_mult_lo[i] * new_electrical_load[i])
    else:
        e_demand = new_electrical_load[i] - (elastic_mult_hi[i] * new_electrical_load[i])
    elastic_demand.append(e_demand)

ax3.plot(GW_daily.index, new_electrical_load, label = 'Original demand', color = 'black')
ax3.plot(GW_daily.index, elastic_demand, label = 'Demand with elasticity', color = 'red')

elastic_demand_total = sum(elastic_demand)/1000*24

print('Total demand without elasticity = %.1f' % + (new_electrical_load.sum().sum()/1000*24))
print('Total demand with elasticity    = %.1f' % + elastic_demand_total)

demand_diff = (elastic_demand / new_electrical_load)

fig4 = plt.figure(figsize=(18,10))
ax4 = fig4.add_subplot(413)
ax4.set_xlim(GW_daily.index[0], GW_daily.index[-1]) 
ax4.set(xlabel= 'Date', ylabel='% ', ylim=(80, 110), title='Demand difference with elasticity %.0f' % year)
ax4.plot(GW_daily.index, demand_diff*100, label = 'Difference with elasticity', color = 'black')
zero_line = [100] * excess_energy.size
ax4.plot(GW_daily.index, zero_line, color = 'grey')
ax40 = ax4.twinx();  ax40.set(ylabel='%', ylim=(80, 110))  # Dummy axis to get this graph to line up with others

ax3.legend(loc = 'upper center')
ax30.legend(loc='upper right')
ax4.legend(loc='lower center')


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


# Part 2 of the net zero model - to analyse supply, demand and storage requirements 
# Andy Williams, Loughborough Uni, 2022


fig2 = plt.figure(figsize=(18,30))
ax2 = fig2.add_subplot(412)
ax2.set_xlim(GW_daily.index[0], GW_daily.index[-1])
#ax2.set_xlim(Heat_load.index[120], Heat_load.index[150])      # setup to zoom in to a chosen area
ax2.set(xlabel= 'Date', ylabel='Average daily power balance, GW', ylim=(-60, 150), title='Supply minus demand using storage %.0f' % year)
zero_line = [0] * excess_energy.size
ax2.plot(GW_daily.index, zero_line, color = 'grey')

# Recalculate total energy
Total_energy = (GW_daily['wind'] + GW_daily['solar'] + GW_daily['hydro'] + GW_daily['nuclear']                 + GW_daily['biomass'] + tidal)      

new_excess_energy = (Total_energy - new_electrical_load)
if (no_elasticity == 0):
    excess_energy = new_excess_energy                          # removes industrial and biomass measures 
ax2.plot(GW_daily.index, excess_energy,  label = 'Excess renewable energy', color = 'darkred')

Deficit = pd.DataFrame(excess_energy, index=GW_daily.index)    # make a dataframe
Deficit[Deficit > 0] = 0  
Deficit = Deficit.sum().sum() /(-1000) *24                     # so sum up all the deficits
print("Total energy deficit without storage          = %.1f" % Deficit + " TWh")


# ADD METHANE STORAGE
# ===================

# Some parameters are in "top"
if (second_pass == 0 and no_elasticity == 0):
    Methane_capacity =  Methane_store *10    # When testing elasticity, need to always burn methane when needed on first pass
else:   
    Methane_capacity =  Methane_store 
Methane_efficiency   = 0.5                   # Power station efficiency of methane 
Electrolysis_efficiency = 0.8                # 
Hydrogen_to_methane  = 2.0                   # 1.0 kWh biomass + 0.5 kWh hydrogen →  1.0 kWh methane 
Compression          = 0.15                  # fraction of hydrogen energy to compress methane and H2
Hydrogen_stored      = [Hydrogen_capacity/1.33] # Starting point 3/4 full
Methane_stored       = [Methane_capacity/1.33]  # Starting point 3/4 full
Elec_from_methane    = [0]                   # Starting point to find daily electricity generated from burning methane
Balance_w_Methane    = [0]                   # Supply minus demand 
CO2_removal          = (0.57 * 0.85)         # 85% CCS from gas or biomass power stations, in units of kg/kWh or Mt/TWh

    
# Generate hydrogen and convert to methane. Use to run power stations

Hydrogen = Hydrogen_stored
Methane = Methane_stored
Total_hydrogen_produced = 0
Total_methane_produced = 0
Methane_produced = [0]
state = 0
M_state = 0
 
#print("\nState Surplus \t New_H \t H_stored  H \t New_M  M_stored Bal \t Elec  M_produced M_state")
for i in range(1, excess_energy.size):
    prev_H = Hydrogen[i-1]
    prev_M = Methane[i-1]
    Generated_elec = 0                                      # electricity generated from methane
    New_H = 0                                               # hydrogen generated that day
    New_M = 0                                               # methane added. SPLIT EFFICIENCIES
    Bal = 0                                                 # electrical balance
    surplus = excess_energy[i]                              # surplus (or -deficit) energy for the day

    if surplus < 0:                                         # energy deficit
        if (Methane_stored < -surplus*24 / Methane_efficiency):  # not enough methane left
            state = 1
            New_M = -Methane_stored                         # use some methane to make up the deficit
            Generated_elec = (Methane_stored * Methane_efficiency)/24  
            Bal = surplus + Generated_elec                  # so a negative elec balance
        else:                                               # enough methane available
            state = 2
            New_M = (surplus*24 / Methane_efficiency)       # use some methane to make up the deficit
            Generated_elec = (-surplus) 
    else:                                                   # energy surplus
        if  (Hydrogen_stored + surplus) > Hydrogen_capacity:    # hydrogen store is full
            state = 3
            Bal = surplus
        else:                                               # hydrogen store not full
            if surplus > (Electrolysis_rate * (1 + Compression)):    # a lot of excess energy
                state = 4
                Bal = surplus - (Electrolysis_rate * (1 + Compression))
                New_H = Electrolysis_rate * Electrolysis_efficiency * 24   # make as much gas as electrolysers can handle.
                Total_hydrogen_produced += New_H
            else:                                           # limited excess energy
                state = 5
                New_H = (surplus*24 * Electrolysis_efficiency) * (1-Compression)  # use all but compression fraction to make gas
                Total_hydrogen_produced += New_H
               
    Hydrogen_stored = New_H + prev_H       
    Balance_w_Methane.append(Bal)

    if (Methane_stored + surplus) < Methane_capacity:       # methane store is not full
        if (Hydrogen_stored > Bleed_off):
            M_state = 1
            New_M += (Bleed_off * Hydrogen_to_methane)      # methane added
            Total_methane_produced += (Bleed_off * Hydrogen_to_methane)
            Methane_produced.append(5 * Bleed_off * Hydrogen_to_methane)            
        else:                                               # not much hydrogen left
            M_state = 2
            New_M += (Hydrogen_stored * Hydrogen_to_methane)  # use it all to make methane    
            Methane_produced.append(5 * Hydrogen_stored * Hydrogen_to_methane)   
    else:
        M_state = 3
        Methane_produced.append(0)                          # methane store is full

    if (Hydrogen_stored > Bleed_off):
        Hydrogen.append(Hydrogen_stored - Bleed_off)        # use some hydrogen to make methane
    else:
        Hydrogen.append(0)                                  # no hydrogen left

    Methane_stored = New_M + prev_M
    Methane.append(Methane_stored)   
    Elec_from_methane.append(Generated_elec)

#    print( "%.0f"% state, "\t %.0f" % surplus, "\t %.0f"% New_H, "\t %.0f"% Hydrogen_stored, "\t %.0f"% Hydrogen[i],\
#                             "\t %.0f"% New_M, "\t %.0f"% Methane_stored, "\t %.0f"% Bal, "\t %.0f"% Generated_elec,\
#                             "\t %.0f"%  Methane_produced[i], "\t %.0f"%  M_state)


ax20 = ax2.twinx()
ax20.set(ylabel='Gas stored, GWh', ylim=(0, 35000))
ax20.plot(GW_daily.index, Hydrogen, label = 'Hydrogen stored', color = 'darkorange')
ax20.plot(GW_daily.index, Methane, label = 'Methane stored', color = 'black')
ax20.plot(GW_daily.index, (Methane_produced), label = 'Methane produced x 5', color = 'burlywood')
ax20.plot(GW_daily.index, zero_line, color = 'silver')
ax2.plot(GW_daily.index, Balance_w_Methane, label = 'Balance including Methane', color = 'darkviolet')
ax2.fill_between(GW_daily.index, Balance_w_Methane, color = 'plum')

Deficit_w_Methane_Df = pd.DataFrame(Balance_w_Methane, index=GW_daily.index)     # make a dataframe
Deficit_w_Methane_Df[Deficit_w_Methane_Df > 0] = 0                               # delete all positive values
energy_deficit_w_Methane = Deficit_w_Methane_Df.sum().sum() /(-1000)             # so sum up all the deficits
print("Total energy deficit with methane             = %.2f" % energy_deficit_w_Methane + " TWh")
print("Total biomethane produced                     = %.1f" % (Total_methane_produced/1000) + " TWh")
print("Total biomass to make methane                 = %.1f" % (Total_methane_produced/1000) + " TWh")
print("Electrolysers needed                          = %.1f" % (Electrolysis_rate + 6) + " GW")
 
Surplus_w_Methane_Df = pd.DataFrame(Balance_w_Methane, index=GW_daily.index, columns=['Bal'])     # make a dataframe
Surplus_w_Methane_Df[Surplus_w_Methane_Df < 0] = 0                               # delete all negative values
energy_surplus_w_Methane = Surplus_w_Methane_Df.sum().sum() *24 /1000            # so sum up all the surpluses
print("Total energy surplus with methane             = %.1f" % energy_surplus_w_Methane + " TWh")
#print(Deficit_w_Methane_Df)

Deficit_days = (Deficit_w_Methane_Df < (-1)).sum()  
print("Number of days with energy deficit            = %.0f" % Deficit_days)
Elec_from_methane_DF = pd.DataFrame(Elec_from_methane, index=GW_daily.index, columns=['elec_from_methane'])  # make a df 
Total_elec_from_biomethane = Elec_from_methane_DF.sum().sum() *24 /1000 
efficiency_losses = (1/Methane_efficiency) * (1/Electrolysis_efficiency) * Total_elec_from_biomethane
print("Total electricity produced from biomethane    = %.1f" % Total_elec_from_biomethane + " TWh")
CO2_removed = CO2_removal * (Total_elec_from_biomethane + Biomass_total)
print("CO2 removed if power stations have CCS        = %.1f" % (CO2_removed) + " Mt")
print("Total energy used up with methane losses      = %.1f" % efficiency_losses + " TWh")
print("Methane in stock at end of year               = %.1f" % (Methane_stored/1000) + " TWh")
print("... percentage of max reserves                = %.1f" % (100*Methane_stored/Methane_capacity) + " %  (should be ~75%)")


print('\nPOWER STATIONS')
#========================

print("Biomass power stations needed                 = %.1f" % (Total_biomass/days_to_run_biomass/24) + " GW" +     "   (capacity of DRAX is 3.9 GW)")
Elec_from_methane_DF[Elec_from_methane_DF < 0] = 0                               # delete negatives
ax2.plot(GW_daily.index, Elec_from_methane, label = 'Electricity from biomethane', color = 'green') # Can't plot Elec_from_methane_DF??
ax2.fill_between(GW_daily.index, Elec_from_methane_DF["elec_from_methane"], color = 'palegreen') 
Max_daily_elec_from_methane = Elec_from_methane_DF['elec_from_methane'].nlargest(n=1)
print("Methane power stations needed                 = %.1f" % (Max_daily_elec_from_methane) + " GW" +      "  (max gas-fired power in 2021 was 25 GW)")
print("Total electricity generated from methane      = %.1f" % (Elec_from_methane_DF.sum().sum()/1000 *24) + " TWh")



# Work out marginal cost of electricity
#======================================

print('\n\nELECTRICITY COSTS ' + str(year) + '\n')

# Count how many days (-1) the marginal power station will be used
# (from https://stackoverflow.com/questions/58750929/python-pandas-dataframe-count-values-greater-than-or-equal-to-a-value-in-the-da)
# 'counts' is the number of days on which more power has to be generated than this day
counts = ( (Elec_from_methane_DF.sort_values('elec_from_methane',ascending=False)
              .expanding().count()-1).sort_index() 
                                     .groupby(Elec_from_methane_DF['elec_from_methane'])                                                              
                                     .transform('max') ) + 1
Elec_df = Elec_from_methane_DF.assign(greater_than_value = counts)
#print(Elec_df)


# So work out the cost of electricity for each day
# Some of following figures from gov site - see notes 
Capex_per_MW          = 500000
Infrastructure        = 15000000      # assume that to be for a 1000MW station 
Operating_cost_per_MW = 16000
Gas_cost_per_MWh      = 105           # see notes - NOT including electricity price
Hours_per_year        = 365*24
Simple_term           = 20
Efficiency            = 0.5
LCOE_of_renewables    = 50            # £50 per MWh approx (all power other than gas fired)
cost = [0]                            # starting point cost of electricity per MWh (£)
days_with_gas = 0 
cost_with_gas = 0

# So for a 1000 MW power station
for i, row in Elec_df.iterrows():
    if Elec_df.at[i,'greater_than_value'] == 365:
        Elec_per_MWh = LCOE_of_renewables
    else:
        days_with_gas += 1
        Load_factor = (Elec_df.at[i,'greater_than_value']) / 365
        Elec_per_MWh = ((((Capex_per_MW *1000)+(Infrastructure)) / Simple_term) + (Operating_cost_per_MW *1000))                      / ((Hours_per_year *1000 *Load_factor)) + (Gas_cost_per_MWh / Efficiency) 
        cost_with_gas += Elec_per_MWh
    cost.append(Elec_per_MWh)

# (Gas generation cost is overstated by about 10% because all power stations get paid at the top marginal rate)

Average_LCOE = sum(cost[1:366])/365
Average_cost_with_gas = cost_with_gas / days_with_gas       
    
# Now calculate total electricity price - can run with different scenarios
# Do not include infrastructure such as grid strengthening as that should be common for all      

# LCOE £/MWh  - see notes
wind_price             = 46
solar_price            = 39
other_renewables_price = 100
nuclear_price          = 87

def nice_print_1(name, price):
    price_f = (format(int(price), ',d'))
    print(name + " = £" + str(price_f) + "m")

def nice_print_2(name, price):
    price_f = (format(int(price), ',d'))
    print(name + " = £" + str(price_f))

def nice_print_3(name, price, gen, total_gen, total_price):
    price_f = (format(int(price), ',d'))
    print(name + " = £" + str(price_f) + "m")
    print("   percentage of total gen:   %.1f" % (100 * gen / total_gen) + "%")
    print("   percentage of total cost:  %.1f" % (100 * price / total_price) + "%\n")

other_renewables       = Hydro_total + Biomass_total + Tidal_total
gas_gen                = Elec_from_methane_DF.sum().sum()/1000 *24

# Total price for each generator - in units of £m
wind_total_price               = Wind_total * wind_price
solar_total_price              = Solar_total * solar_price
other_renewables_total_price   = other_renewables * other_renewables_price
nuclear_total_price            = Nuclear_total * nuclear_price
gas_fired_total_price          = Average_cost_with_gas * gas_gen
total_LCOE                     = wind_total_price + solar_total_price + other_renewables_total_price +                                  nuclear_total_price + gas_fired_total_price
LCOE_per_MWh                   = total_LCOE / Demand_total

nice_print_2("Average LCOE/MWh          ", Average_LCOE)    
#nice_print_2("Average gas gen LCOE/MWh  ", Average_cost_with_gas)    
nice_print_3("\nWind total LCOE           ", wind_total_price, Wind_total, Generation_total, total_LCOE)
nice_print_3("Solar total LCOE          ", solar_total_price, Solar_total, Generation_total, total_LCOE)    
nice_print_3("Other renewables LCOE     ", other_renewables_total_price, other_renewables, Generation_total, total_LCOE)    
nice_print_3("Nuclear LCOE              ", nuclear_total_price, Nuclear_total, Generation_total, total_LCOE)    
nice_print_3("Gas fired_total LCOE      ", gas_fired_total_price, gas_gen, Generation_total, total_LCOE)    
nice_print_1("Total electricity LCOE    ", total_LCOE)    

nice_print_2("\nAverage cost/MWh - top marginal cost basis                                   ", Average_LCOE)    
nice_print_2("Average generation price per MWh - cost to generate basis, free surplus      ", LCOE_per_MWh)  
nice_print_2("Average generation price per MWh - cost to generate basis, non-free surplus  ", (total_LCOE / Generation_total))  

ax2.legend(loc='upper left')
ax20.legend(loc='upper right')

"""""
# Special plot for illustration in report
fig5 = plt.figure(figsize=(6,30)) 
ax5 = fig5.add_subplot(512)
ax5.set_xlim(GW_daily.index[220], GW_daily.index[310])   # setup to zoom in to a chosen area
ax5.set(xlabel='date', ylabel='Average daily power balance, GW', ylim=(-60, 150), title='Supply minus demand with storage %.0f' % year)
zero_line = [0] * excess_energy.size
plt.xticks([2021-12])  # this stops the dates being printed along x axis
ax5.plot(GW_daily.index, zero_line, color = 'grey')
ax5.plot(GW_daily.index, excess_energy,  label = 'Excess renewable energy', color = 'darkred')
ax5.fill_between(GW_daily.index, excess_energy, color = 'cyan')
ax50 = ax5.twinx()
ax50.set(ylabel='Gas stored, GWh', ylim=(0, 15000))
ax50.plot(GW_daily.index, Hydrogen, label = 'Hydrogen stored, GWh', color = 'darkorange')
ax50.plot(GW_daily.index, Methane, label = 'Methane stored, GWh', color = 'black')

ax5.legend(loc='upper left')
ax50.legend(loc='upper right')
"""""


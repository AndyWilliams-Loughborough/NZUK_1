#!/usr/bin/env python
# coding: utf-8

# In[1]:


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

# When testing with elasticity we want to suppress the first-pass pre-elastic results
def conditional_print(message):
    if (second_pass == 1 or no_elasticity == 1):
        print(message)
    
# Suppress the graph for the first-pass pre-elastic results
if (second_pass == 1 or no_elasticity == 1):
    fig2 = plt.figure(figsize=(18,40))
    ax2 = fig2.add_subplot(412)
    ax2.set_xlim(GW_daily.index[0], GW_daily.index[-1])
    #ax2.set_xlim(Heat_load.index[120], Heat_load.index[150])      # setup to zoom in to a chosen area
    ax2.set(xlabel= 'Date', ylabel='Average daily power balance, GW', ylim=(-80, 160), title='Supply minus demand using storage, %.0f weather' % year)
    zero_line = [0] * excess_energy.size
    ax2.plot(GW_daily.index, zero_line, color = 'grey')

# Recalculate total energy
Total_energy = (GW_daily['wind'] + GW_daily['solar'] + GW_daily['hydro'] + GW_daily['nuclear']                 + GW_daily['biomass'] + tidal)      

new_excess_energy = (Total_energy - new_electrical_load)
if (no_elasticity == 0):
    excess_energy = new_excess_energy                          # removes industrial and biomass measures 
if (second_pass == 1 or no_elasticity == 1):
    ax2.plot(GW_daily.index, excess_energy,  label = 'Excess renewable energy', color = 'darkred')

Deficit = pd.DataFrame(excess_energy, index=GW_daily.index)    # make a dataframe
Deficit[Deficit > 0] = 0  
Deficit = Deficit.sum().sum() /(-1000) *24                     # so sum up all the deficits
conditional_print("Total energy deficit without storage          = %.1f" % Deficit + " TWh")


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
CO2_removal          = (0.365 * 0.85)        # 85% CCS from gas or biomass power stations, in units of kg/kWh or Mt/TWh

    
# Generate hydrogen and convert to methane. Use to run power stations

Hydrogen = Hydrogen_stored
Methane = Methane_stored
Total_hydrogen_produced = 0
Total_methane_produced = 0
Methane_producedx20 = [0]
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
        if (Methane_stored < -surplus*24 / Methane_efficiency):  # not enough methane left for the day
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
            Methane_producedx20.append(20 * Bleed_off * Hydrogen_to_methane)    # the x20 is for the graph        
        else:                                               # not much hydrogen left
            M_state = 2
            New_M += (Hydrogen_stored * Hydrogen_to_methane)  # use it all to make methane    
            Methane_producedx20.append(20 * Hydrogen_stored * Hydrogen_to_methane)   
    else:
        M_state = 3
        Methane_producedx20.append(0)                       # methane store is full

    if (Hydrogen_stored > Bleed_off):
        Hydrogen.append(Hydrogen_stored - Bleed_off)        # use some hydrogen to make methane
    else:
        Hydrogen.append(0)                                  # no hydrogen left

    Methane_stored = New_M + prev_M
    Methane.append(Methane_stored)   
    Elec_from_methane.append(Generated_elec)


# For debugging
#    print( "%.0f"% state, "\t %.0f" % surplus, "\t %.0f"% New_H, "\t %.0f"% Hydrogen_stored, "\t %.0f"% Hydrogen[i],\
#                             "\t %.0f"% New_M, "\t %.0f"% Methane_stored, "\t %.0f"% Bal, "\t %.0f"% Generated_elec,\
#                             "\t %.0f"%  Methane_producedx20[i], "\t %.0f"%  M_state)

if (second_pass == 1 or no_elasticity == 1):
    fig20 = plt.figure(figsize=(18,40))
    ax20 = fig20.add_subplot(412)
    ax20.set_xlim(GW_daily.index[0], GW_daily.index[-1])
    ax20.set(xlabel= 'Date', ylabel='Gas stored, GWh', ylim=(0, 38000))
    ax20.plot(GW_daily.index, Hydrogen, label = 'Hydrogen stored', color = 'darkorange')
    ax20.plot(GW_daily.index, Methane, label = 'Methane stored', color = 'black')
    ax20.plot(GW_daily.index, (Methane_producedx20), label = 'Methane produced x 20', color = 'turquoise')
    ax20.plot(GW_daily.index, zero_line, color = 'silver')
    ax2.plot(GW_daily.index, Balance_w_Methane, label = 'Balance including Methane', color = 'darkviolet')
    ax2.fill_between(GW_daily.index, Balance_w_Methane, color = 'plum')

Deficit_w_Methane_Df = pd.DataFrame(Balance_w_Methane, index=GW_daily.index)     # make a dataframe
Deficit_w_Methane_Df[Deficit_w_Methane_Df > 0] = 0                               # delete all positive values
energy_deficit_w_Methane = Deficit_w_Methane_Df.sum().sum() /(-1000)             # so sum up all the deficits
conditional_print("Total energy deficit with methane             = %.2f" % energy_deficit_w_Methane + " TWh")
conditional_print("Total biomethane produced                     = %.1f" % (Total_methane_produced/1000) + " TWh")
conditional_print("Total biomass to make methane                 = %.1f" % (Total_methane_produced/1000) + " TWh")
conditional_print("Electrolysers needed                          = %.1f" % (Electrolysis_rate + 6) + " GW")
 
Surplus_w_Methane_Df = pd.DataFrame(Balance_w_Methane, index=GW_daily.index, columns=['Bal'])     # make a dataframe
Surplus_w_Methane_Df[Surplus_w_Methane_Df < 0] = 0                               # delete all negative values
energy_surplus_w_Methane = Surplus_w_Methane_Df.sum().sum() *24 /1000            # so sum up all the surpluses
conditional_print("Total energy surplus with methane             = %.1f" % energy_surplus_w_Methane + " TWh")
#print(Deficit_w_Methane_Df)

Deficit_days = (Deficit_w_Methane_Df < (-1)).sum()  
conditional_print("Number of days with energy deficit            = %.0f" % Deficit_days)
Elec_from_methane_DF = pd.DataFrame(Elec_from_methane, index=GW_daily.index, columns=['elec_from_methane'])  # make a df 
Total_elec_from_biomethane = Elec_from_methane_DF.sum().sum() *24 /1000 
efficiency_losses = ((1/Methane_efficiency) * (1/Electrolysis_efficiency) * Total_elec_from_biomethane) - Total_elec_from_biomethane
conditional_print("Total electricity produced from biomethane    = %.1f" % Total_elec_from_biomethane + " TWh")
CO2_removed = CO2_removal * (Total_elec_from_biomethane + Biomass_total)
conditional_print("CO2 removed if power stations have CCS        = %.1f" % (CO2_removed) + " Mt")
conditional_print("Total energy used up with methane losses      = %.1f" % efficiency_losses + " TWh")
conditional_print("Methane in stock at end of year               = %.1f" % (Methane_stored/1000) + " TWh")
conditional_print("... percentage of max reserves                = %.1f" % (100*Methane_stored/Methane_capacity) + " %  (should be ~75%)")
#print(Elec_from_methane_DF)

conditional_print('\nPOWER STATIONS')
#========================

conditional_print("Biomass power stations needed                 = %.1f" % (Total_biomass/days_to_run_biomass/24) + " GW" +     "   (capacity of DRAX is 3.9 GW)")
Elec_from_methane_DF[Elec_from_methane_DF < 0] = 0               # delete negatives
if (second_pass == 1 or no_elasticity == 1):
    ax2.plot(GW_daily.index, Elec_from_methane, label = 'Electricity from biomethane', color = 'green') # Can't plot Elec_from_methane_DF??
    ax2.fill_between(GW_daily.index, Elec_from_methane_DF["elec_from_methane"], color = 'palegreen') 
Max_daily_elec_from_methane = Elec_from_methane_DF['elec_from_methane'].nlargest(n=1)
conditional_print("Methane power stations needed                 = %.1f" % (Max_daily_elec_from_methane) + " GW" + "  (max gas-fired power in 2021 was 25 GW)")
conditional_print("Total electricity generated from methane      = %.1f" % (Elec_from_methane_DF.sum().sum()/1000 *24) + " TWh")



# Work out marginal cost of electricity
#======================================

conditional_print('\n\nELECTRICITY COSTS ' + str(year) + '\n')

# Count how many days (-1) the marginal power station will be used
# 'counts' is the number of days on which more power has to be generated than this day
counts = ( (Elec_from_methane_DF.sort_values('elec_from_methane',ascending=False)
              .expanding().count()-1).sort_index() 
                                     .groupby(Elec_from_methane_DF['elec_from_methane'])                                                              
                                     .transform('max') ) + 1
Elec_df = Elec_from_methane_DF.assign(greater_than_value = counts)
#print('Elec_df = ', Elec_df )

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
lf_accum = 0


# Calculate daily LCOE

# First add renewables supply and gas required columns to DeficitDf
DeficitDf['gen']  = Total_energy*24
if second_pass == 0:
    DeficitDf['load'] = new_electrical_load*24

for i, row in DeficitDf.iterrows():
     if DeficitDf.at[i,'Balance'] < 0:
        gas_gen = (DeficitDf.at[i,'Balance']*24) * (-1)
        renewables_used = DeficitDf.at[i,'load'] - gas_gen
        renewables_unit_cost = LCOE_of_renewables
     else:
        gas_gen = 0
        renewables_unit_cost = LCOE_of_renewables * (DeficitDf.at[i,'gen'] / DeficitDf.at[i,'load'])
  
     DeficitDf.at[i,'gas_gen'] = gas_gen
     renewables_used = DeficitDf.at[i,'load'] - gas_gen
     DeficitDf.at[i,'renewables_used'] = renewables_used
     DeficitDf.at[i,'renewables_unit_cost'] = renewables_unit_cost
    

# So for a 1000 MW power station
for i, row in Elec_df.iterrows():
    if Elec_df.at[i,'greater_than_value'] == 365:
        Elec_per_MWh = LCOE_of_renewables
        DeficitDf.at[i,'gas_unit_cost'] = 0        
    else:
        days_with_gas += 1
        Load_factor = (Elec_df.at[i,'greater_than_value']) / 365
        Elec_per_MWh = ((((Capex_per_MW *1000)+(Infrastructure)) / Simple_term) + (Operating_cost_per_MW *1000))                      / ((Hours_per_year *1000 *Load_factor)) + (Gas_cost_per_MWh / Efficiency) 
        cost_with_gas += Elec_per_MWh
        lf_accum += Load_factor
    cost.append(Elec_per_MWh)
    DeficitDf.at[i,'gas_unit_cost'] = (Elec_per_MWh + 223)/2  # Average with the lowest gas cost since most stations not marginal
    DeficitDf.at[i,'gas_cost'] = (DeficitDf.at[i,'gas_unit_cost'] * DeficitDf.at[i,'gas_gen']) 
    DeficitDf.at[i,'renewables_cost'] = (DeficitDf.at[i,'renewables_unit_cost'] * DeficitDf.at[i,'renewables_used'])  
    DeficitDf.at[i,'daily_cost'] = (DeficitDf.at[i,'renewables_cost'] + DeficitDf.at[i,'gas_cost'])      
    DeficitDf.at[i,'unit_cost'] = (DeficitDf.at[i,'daily_cost'] / DeficitDf.at[i,'load'])      

Average_LCOE = sum(cost[1:366])/365

# Export to csv to analyse
#DeficitDf.to_csv('/Users/User/Documents/MSc/Dissertation/Data/DeficitDf_3.csv')

#"""""
fig6 = plt.figure(figsize=(18,30))
ax6 = fig6.add_subplot(413)
ax6.set_xlim(GW_daily.index[0], GW_daily.index[-1]) 
ax6.set(xlabel= 'Date', ylabel='Electricity daily LCOE £m', ylim=(0, 800), title='Daily total cost of electricity %.0f weather' % year)
ax6.plot(GW_daily.index, DeficitDf['daily_cost']/1000, label = 'Electricity daily LCOE', color = 'black')
ax6.legend(loc='upper center')
"""""
fig7 = plt.figure(figsize=(18,30))
ax7 = fig7.add_subplot(413)
ax7.set_xlim(GW_daily.index[0], GW_daily.index[-1]) 
ax7.set(xlabel= 'Date', ylabel='Daily unit LCOE £/MWh', ylim=(0, 900), title='Daily unit cost of electricity %.0f' % year)
ax7.plot(GW_daily.index, DeficitDf['unit_cost'], label = 'Electricity daily unit LCOE', color = 'black')
ax7.legend(loc='upper center')
"""""

Av_LF = lf_accum / 365
conditional_print("Average gas power station load factor = %.3f" % Av_LF)

     
# Now calculate total electricity price - can run with different scenarios
# Do not include infrastructure such as grid strengthening as that should be common for all      

# LCOE £/MWh  - see notes
wind_price             = 46
solar_price            = 39
other_renewables_price = 100
nuclear_price          = 70 

def nice_print_1(name, price):
    price_f = (format(int(price), ',d'))
    conditional_print(name + " = £" + str(price_f) + "m")

def nice_print_2(name, price):
    price_f = (format(int(price), ',d'))
    conditional_print(name + " = £" + str(price_f))

def nice_print_4(name, gen, total_gen):
    conditional_print(name)     
    conditional_print("   percentage of total gen: %.1f" % (100 * gen / total_gen) + "%")
     
other_renewables       = Hydro_total + Biomass_total + Tidal_total
gas_gen                = DeficitDf['gas_gen'].sum().sum()/1000

# Total price for each generator - in units of £m
wind_total_price               = Wind_total * wind_price
solar_total_price              = Solar_total * solar_price
other_renewables_total_price   = other_renewables * other_renewables_price
nuclear_total_price            = Nuclear_total * nuclear_price
non_gas_total_gen              = DeficitDf['renewables_used'].sum().sum()
non_gas_total_cost             = DeficitDf['renewables_cost'].sum().sum()
gas_fired_total_price          = DeficitDf['gas_cost'].sum().sum()
total_LCOE                     = DeficitDf['daily_cost'].sum().sum()/1000  # to convert from thousands to millions
LCOE_per_MWh                   = DeficitDf['unit_cost'].mean()
Total_generation               = DeficitDf['gen'].sum().sum()/1000   #TWh


nice_print_4("\nWind total           ", Wind_total, Total_generation)
nice_print_4("Solar total            ", Solar_total, Total_generation)    
nice_print_4("Other renewables       ", other_renewables, Total_generation)    
nice_print_4("Nuclear                ", Nuclear_total, Total_generation)    
nice_print_4("Gas fired_total        ", gas_gen, Total_generation)
print('\n')
nice_print_1("Total electricity LCOE ", total_LCOE)    
nice_print_2("Average LCOE/MWh       ", LCOE_per_MWh)  

if (second_pass == 1 or no_elasticity == 1):
    ax2.legend(loc='upper left')
    ax20.legend(loc='upper left')

                                   
"""""
# Special plot for illustration in report
# Make the graph text normal
plt.rc('axes', titlesize=14)
plt.rc('axes', labelsize=12)
plt.rc('xtick', labelsize=12)
plt.rc('ytick', labelsize=12)
plt.rc('legend', fontsize=12)

fig5 = plt.figure(figsize=(8,30)) 
ax5 = fig5.add_subplot(512)
ax5.set_xlim(GW_daily.index[220], GW_daily.index[310])   # setup to zoom in to a chosen area
ax5.set(xlabel='date', ylabel='Average daily power balance, GW', ylim=(-60, 150), title='Supply minus demand with storage example')
zero_line = [0] * excess_energy.size

plt.xticks(rotation=45)  # this stops the dates being printed along x axis
ax5.plot(GW_daily.index, zero_line, color = 'grey')
ax5.plot(GW_daily.index, excess_energy,  label = 'Excess renewable energy', color = 'blue')
ax5.fill_between(GW_daily.index, excess_energy, color = 'cyan')
ax5.plot(GW_daily.index, Elec_from_methane, label = 'Electricity from biomethane', color = 'red')

ax50 = ax5.twinx()
ax50.set(ylabel='Gas stored, GWh', ylim=(0, 25000))
ax50.plot(GW_daily.index, Hydrogen, label = 'Hydrogen stored, GWh', color = 'darkorange')
ax50.plot(GW_daily.index, Methane, label = 'Methane stored, GWh', color = 'black')

ax5.legend(loc='upper left')
ax50.legend(loc='upper right')
"""""


# In[ ]:





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


# Part 1 of the net zero model - to analyse supply, demand and storage requirements 
# Andy Williams, Loughborough Uni, 2022

# Add solar and wind multipliers for year relative to installed capacities of 2021
#    so we can compare like with like when we change year of gridwatch data. From ONS data
# Also derate nuclear so that it is about 4.9GW average each year

if year == 2021:                       # no energy deficit days
    installed_wind  = 1.03
    installed_solar = 1.19
    mult_nuclear    = 1
elif year == 2020:                     # no energy deficit days
    installed_wind  = 1.10
    installed_solar = 1.21   
    mult_nuclear    = 0.91
elif year == 2019:                     # 3 energy deficit day - bad first part of year
    installed_wind  = 1.13
    installed_solar = 1.28
    mult_nuclear    = 0.82
elif year == 2018:                     # no energy deficit days
    installed_wind  = 1.30
    installed_solar = 1.22
    mult_nuclear    = 0.71
elif year == 2017:                     # 5 energy deficit day - bad first part of year
    installed_wind  = 1.46
    installed_solar = 1.20
    mult_nuclear    = 0.65

# Load Gridwatch data for selected year - available from: http://www.gridwatch.templar.co.uk/download.php
path = os.path.normpath('/Users/User/Documents/MSc/Dissertation/Data')
GW = np.genfromtxt(path + '/gridwatch_full_'+ str(year) + '.csv', delimiter=',', 
                        skip_header=1, usecols=[*range(0,14)], max_rows=104914)

# Set up a dataframe (had to reduce end time to make indices match)
ts = pd.date_range(start='2021-01-01 00:01', end='2021-12-31 6:50', freq = '5min') # (for 2019 data with fewest rows)
GWdf = pd.DataFrame(GW, index=ts, columns=['id','timestamp','demand','frequency','coal', 
                            'nuclear','ccgt','wind','pumped','hydro','biomass','oil','solar','ocgt'])

# Resample to one reading per day (average power rather than energy)
GW_daily = GWdf.resample(rule='D', closed='right', label='left').sum() /12 /1000 /24 
GW_daily['wind']    = GW_daily['wind']    * 1.28 * mult_wind * installed_wind     # The 1.28 uplift is for embedded gen found from Drax Insights
GW_daily['biomass'] = GW_daily['biomass'] * 0.47            # Only the proportion of energy from non-imported biomass
GW_daily['solar']   = GW_daily['solar']   * mult_solar * installed_solar
GW_daily['nuclear'] = GW_daily['nuclear'] * mult_nuclear
tidal = [(16*1000/365/24)]   *365                           # Resource 16 TWh/y divided across 365 days(from gov est)


print('SUPPLY')
#==============

# Plot daily power
fig1 = plt.figure(figsize=(18,30))
ax1 = fig1.add_subplot(411)
ax1.set_xlim(GW_daily.index[0], GW_daily.index[-1])
ax1.set(xlabel= 'Date', ylabel='Average daily power, GW', ylim=(0, 225), title='Supply and demand %.0f' % year)
ax1.plot(GW_daily.index, GW_daily['wind'],     label = 'Wind power',    color = 'lime')
ax1.plot(GW_daily.index, GW_daily['solar'],    label = 'Solar_power',   color = 'orange')
Total_energy = (GW_daily['wind'] + GW_daily['solar'] + GW_daily['hydro'] + GW_daily['nuclear']                 + GW_daily['biomass'] + tidal)
ax1.plot(GW_daily.index, Total_energy, label = 'Total power supply', color = 'royalblue')

# Now calculate and print the totals for the energy sources, using this template
text1 = "Total {0:<13} energy for year = {1:5.0f} TWh, equivalent to continuous {2:5.1f} GW"

Wind_total = GW_daily['wind'].sum().sum() /1000 *24
print(text1.format('wind', Wind_total, (Wind_total *1000 /365 /24)))

Solar_total = GW_daily['solar'].sum().sum() /1000 *24
print(text1.format('solar PV', Solar_total, (Solar_total *1000 /365 /24)))
 
Hydro_total = GW_daily['hydro'].sum().sum() /1000 *24
print(text1.format('hydro', Hydro_total, (Hydro_total *1000 /365 /24)))

Biomass_total = GW_daily['biomass'].sum().sum() /1000 *24
print(text1.format('biomass', Biomass_total, (Biomass_total *1000 /365 /24)))

Nuclear_total = GW_daily['nuclear'].sum().sum() /1000 *24
print(text1.format('nuclear', Nuclear_total, (Nuclear_total *1000 /365 /24)))

Tidal_total = 16
print(text1.format('tidal', Tidal_total, (Tidal_total *1000 /365 /24)))

Generation_total = sum(Total_energy)/1000 *24
print(text1.format('generation', Generation_total, (Generation_total *1000 /365 /24)))


print('\nDEMAND')
#================

# Load Central England temperature data, as downloaded from CEDA
Temperature = np.genfromtxt(path +'/met_meantemp_'+ str(year) +'.csv', delimiter=',', usecols=(1))

# Set up a dataframe
ts_d = pd.date_range(start='2021-01-01 00:01', end='2021-12-31 9:00', freq = 'D') # (transpose year data to 2021)
T17df = pd.DataFrame(Temperature, index=ts_d, columns=['Temp'])

# Don't understand why I have to do this mock resampling.... 
daily_temp = T17df.resample(rule='D', closed='right', label='left').sum()
Av_temp = (daily_temp["Temp"])  

# As per CAT ZCB-Methodology p5, calculate heat load from a base temp of 13.1C
# Derate electrical load by CoP and a further 10% for geothermal heat
heating_cop = 2.9
Heat_load = (13.1 - Av_temp) * 5.6                     # Total building heat loss = 5.6 GW/degC
Heat_load[Heat_load < 0] = 0                           # Only consider positive heat loads of course
Elec_heat_load = ((Heat_load / heating_cop) * 0.9)     # Derate electrical load
Heat_total = Elec_heat_load.sum().sum() /1000 *24      # Mult by 24 to get total energy. Div 1000 for TWh
print(text1.format('space heating', Heat_total, (Heat_total *1000 /365 /24)))

# Add the other loads - mostly in line with CAT methodology but see Notes
# Derate electrical load of hot water by CoP for heat pumps and a further 10% for geothermal heat
hot_water_cop = 2
hot_water_first_half_winter = [257*0.9/(hot_water_cop *24)] * 130       # More energy needed to heat water in winter
hot_water_summer = [175*0.9/(hot_water_cop *24)] * (Elec_heat_load.size - 182)
hot_water_second_half_winter = [257*0.9/(hot_water_cop *24)] * 52
elec_for_hot_water = hot_water_first_half_winter + hot_water_summer + hot_water_second_half_winter
Hot_water = sum(elec_for_hot_water)/1000 *24
print(text1.format('hot water', Hot_water, (Hot_water *1000 /365 /24)))

cooking = [(69.3+292.3)/24] * Elec_heat_load.size      # Cooking 25.3 TWh, Lighting and appliances 106.7 TWh
Cooking_total = sum(cooking)/1000 *24
print(text1.format('cooking etc', Cooking_total, (Cooking_total *1000 /365 /24)))

# Calculate cooling load in same way as heat load, with base temp of 14C
Cooling_load = (Av_temp - 14) * 5.6
Cooling_load[Cooling_load < 0] = 0                     # Only consider positive cooling loads of course
Cooling_load = Cooling_load / 3                        # to give about same total as projected in CAT
Cooling_total = Cooling_load.sum().sum() /1000 *24
print(text1.format('cooling', Cooling_total, (Cooling_total *1000 /365 /24)))
ax1.plot(GW_daily.index, (Cooling_load), label = 'Cooling load', color = 'black')
ax1.plot(GW_daily.index, (Elec_heat_load), label = 'Elec_heat_load', color = 'red')

Industrial = [699/24] * Elec_heat_load.size
Industrial_total = sum(Industrial)/1000 *24
print(text1.format('industrial', Industrial_total, (Industrial_total *1000 /365 /24)))

transport_total = 130000 /24   # 130 TWh/y
transport_half_winter = [1.2*transport_total/365] * 90           # electric vehicles less efficient in winter
transport_summer = [0.8*transport_total/365] * (Elec_heat_load.size - 180)
Transport = transport_half_winter + transport_summer + transport_half_winter
Transport_total = sum(Transport)/1000 *24
print(text1.format('transport', Transport_total, (Transport_total *1000 /365 /24)))

Direct_H2_demand = [(25/0.8)*1000/365/24] * Elec_heat_load.size  # 25 TWh/y with 80% electrolysis efficiency
H2_total = sum(Direct_H2_demand)/1000 *24
print(text1.format('industrial H2', H2_total, (H2_total *1000 /365 /24)))

# Total demand
wire_losses = 0.1                      # assume 10% grid losses
electrical_load_1 = Elec_heat_load + elec_for_hot_water + cooking + Cooling_load
electrical_load_2 = electrical_load_1 + Industrial + Transport + Direct_H2_demand
grid_losses = electrical_load_2 * wire_losses
electrical_load = electrical_load_2 + grid_losses

ax1.plot(GW_daily.index, electrical_load, label = 'Electrical demand', color = 'red')
Demand_total = electrical_load.sum().sum() /1000 *24
print(text1.format('demand', Demand_total, (Demand_total *1000 /365/24)))

#"""""
# Special (stacked) plots for illustration in report or for closer examination of generation and demand

fig11 = plt.figure(figsize=(18,80))  
ax11 = fig11.add_subplot(615)
ax11.set_xlim(GW_daily.index[0], GW_daily.index[-1])
ax11.set(xlabel= 'Date', ylabel='Average daily power, GW', ylim=(0, 115), title='Daily demand %.0f weather' % year )
colors = sns.color_palette("tab10")
labels=["Cooling", "Space heating", "Transport", "Industrial", "Hot water", "Cooking and appliances", "Industrial hydrogen", "grid losses"]
plt.stackplot(GW_daily.index, Cooling_load, Elec_heat_load, Transport, Industrial, elec_for_hot_water, cooking, Direct_H2_demand, grid_losses, labels=labels, colors=colors)
plt.legend(loc = "upper center")

fig12 = plt.figure(figsize=(18,40)) #80
ax12 = fig12.add_subplot(616)
ax12.set_xlim(GW_daily.index[0], GW_daily.index[-1])
ax12.set(xlabel= 'Date', ylabel='Average daily power, GW', ylim=(0, 250), title='Daily supply %.0f weather' % year) #220
labels=["Solar power", "Hydroenergy", "Biomass energy", "Nuclear energy", "Tidal energy", "Wind power"]
plt.stackplot(GW_daily.index, GW_daily['solar'], GW_daily['hydro'], GW_daily['biomass'], GW_daily['nuclear'], tidal, GW_daily['wind'], labels=labels, colors=colors)
ax12.plot(GW_daily.index, electrical_load,      label = 'Total demand',   color = 'black')  # for comparison
plt.legend(loc = "upper center")

#"""""

print('\nSUPPLY minus DEMAND')
#=========================

excess_energy = (Total_energy - electrical_load)  # per day
excess_energy = (excess_energy[0:365])  # very strange - subtracting one 365-element list from another gives 366? 

# Make a dataframe of energy deficits
DeficitDf = pd.DataFrame(excess_energy, index=GW_daily.index, columns=['Balance']) 


# Now decrease industrial demand by 50% during weeks of highest energy costs
# ==========================================================================
# Make industrial demand into a data frame. Ind_df
ts_day = pd.date_range(start='2021-01-01', end='2021-12-31', freq = 'D')
Ind_df = pd.DataFrame(Industrial, index=ts_day, columns=['ind'])

# Now find the worst 4 weeks of energy deficit
DeficitDf_weekly = DeficitDf.resample(rule='W', closed='right', label='left').sum()
Worst_weeks = DeficitDf_weekly['Balance'].nsmallest(n=4)
#print('\n Worst weeks, week starting:\n', Worst_weeks)

# dummy to initialise Worst_days
Worst_days = [str((Worst_weeks.index[1] + datetime.timedelta(days=i)).date()) for i in range(7)]

# Extract the seven days up to the week-ending
for d in range(0, Worst_weeks.size):
    start_date = Worst_weeks.index[d]
    Worst_days[d] = [str((start_date + datetime.timedelta(days=i)).date()) for i in range(7)]
#print(Worst_days)

# Now halve each sample coinciding with a Worst_day, else mult by 365/350
for i, row in Ind_df.iterrows():
    date = str(i.date())
    if date in Worst_days[0] or date in Worst_days[1] or date in Worst_days[2] or date in Worst_days[3]:
        Ind_df.at[i,'ind'] = (Ind_df.at[i,'ind'] * 0.5)
    else:
        Ind_df.at[i,'ind'] = (Ind_df.at[i,'ind'] * 365/350)

#ax1.plot(GW_daily.index, Ind_df['ind', label ='New industrial demand', color ='darkkhaki')   # shows the four weeks of shutdown

# Recalculate demand and excess    
new_electrical_load = electrical_load - Industrial + Ind_df['ind']
if no_elasticity == 1:
    new_electrical_load = electrical_load # not counting shutdowns
ax1.plot(GW_daily.index, new_electrical_load, label = 'New electrical demand', color = 'black')


# Now arrange to run biomass power stations on just the worst n days
# ==================================================================
Total_biomass = Biomass_total * 1000         # GWh/y of electrical energy (from gridwatch figs)
days_to_run_biomass = 60                     # 60 days was found to be optimum (for 2021)

Worst_n_days = DeficitDf['Balance'].nsmallest(n=days_to_run_biomass)

for i, row in GW_daily.iterrows():
    date = str(i.date())
    if date in Worst_n_days:
        GW_daily.at[i,'biomass'] = (Total_biomass/days_to_run_biomass/24)
    else:
        GW_daily.at[i,'biomass'] = 0

ax1.plot(GW_daily.index, GW_daily['biomass'], label = 'New biomass power', color = 'blue')
ax1.legend() 


# In[ ]:





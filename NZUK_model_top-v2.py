#!/usr/bin/env python
# coding: utf-8

# In[7]:


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


# To run the three parts of the net zero model - to analyse supply, demand and storage requirements 
# Andy Williams, Loughborough Uni, 2022

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os
import numpy as np
import datetime
from datetime import date
import csv
plt.style.use("seaborn")
pd.set_option('display.max_rows', None)

# Make the graph text larger
plt.rc('axes', titlesize=20)
plt.rc('axes', labelsize=18)
plt.rc('xtick', labelsize=15)
plt.rc('ytick', labelsize=15)
plt.rc('legend', fontsize=15)

year          = 2021                       # set a year from 2017 to 2021 to test
condition     = 'no_demand_side_response'  # set a condition
Elasticity    = -0.2                       # price elasticity of electricity demand 
no_elasticity = 0                          # set to 1 if demand side responses not used
second_pass   = 0                          # first time though "b" to set high biomethane for elasticity test


# Set some parameters, and multipliers to renewables
# First some test cases with demand reduction built in

# This one has not been updated so probably WON'T WORK
if condition == 'high_renewables':         # includes demand-side response measures
    mult_wind             = 13             # muliple of 2021 capacity
    mult_solar            = 9.5            # muliple of 2021 capacity
    Electrolysis_rate     = 12             # maximum rate of conversion, GW
    Bleed_off             = 130            # GWh. Daily hydrogen used to make methane with biogas
    Hydrogen_capacity     = 5000           # GWh storage
    Methane_store         = 20000          # GWh storage

# To run with elasticity but without industrial shutdowns comment out line 245 in "a"
    
elif condition == 'high_biomethane':       # includes demand-side response measures
    no_elasticity         = 0              # E and Ind s/d    just E
    mult_wind             = 8.75           # 8.75             9.25
    mult_solar            = 13.5           # 13.5            12.25
    Electrolysis_rate     = 28             # 
    Bleed_off             = 200            # 
    Hydrogen_capacity     = 5000           # 
    Methane_store         = 30000          # 
    
# Now run without the benfit of elasticity or industrial shutdowns for four weeks of year
# (Adjusts line 214 in script 'a' and lines 40 and 54 in 'b') 
# to run with just industrial shutdowns, comment out 245 and 246 in "a", uncomment 241

elif condition == 'no_demand_side_response': 
    no_elasticity         = 1              # normal   ind shutdowns
    mult_wind             = 11.5           # 11.5     10.5
    mult_solar            = 10.5           # 10.5     10.8
    Electrolysis_rate     = 29             # 
    Bleed_off             = 250            # 
    Hydrogen_capacity     = 5000           # 
    Methane_store         = 30000          #    


""""                                       # Comment out to test all years, else just selected year

# Run the sub-scripts for each year successively

year = 2017
print('\n\n\n YEAR ', year, '\n\n'  )
second_pass   = 0          
%run NZUK_model_a-v2.ipynb
%run NZUK_model_b-v2.ipynb
if no_elasticity == 0:
    %run NZUK_model_c-v2.ipynb
    print('\n=========================================================================')
    print(' Repeating with demand modified due to elasticity of %.2f' % Elasticity, '   Year:', year)  
    print('=========================================================================\n')
    new_electrical_load = elastic_demand   # for demand with elasticity
    second_pass = 1
    %run NZUK_model_b-v2.ipynb

year = 2018
print('\n\n\n YEAR ', year, '\n\n'  )
second_pass   = 0          
%run NZUK_model_a-v2.ipynb
%run NZUK_model_b-v2.ipynb
if no_elasticity == 0:
    %run NZUK_model_c-v2.ipynb
    print('\n=========================================================================')
    print(' Repeating with demand modified due to elasticity of %.2f' % Elasticity, '   Year:', year)  
    print('=========================================================================\n')
    new_electrical_load = elastic_demand   # for demand with elasticity
    second_pass = 1
    %run NZUK_model_b-v2.ipynb

year = 2019
print('\n\n\n YEAR ', year, '\n\n'  )
second_pass   = 0          
%run NZUK_model_a-v2.ipynb
%run NZUK_model_b-v2.ipynb
if no_elasticity == 0:
    %run NZUK_model_c-v2.ipynb
    print('\n=========================================================================')
    print(' Repeating with demand modified due to elasticity of %.2f' % Elasticity, '   Year:', year)  
    print('=========================================================================\n')
    new_electrical_load = elastic_demand   # for demand with elasticity
    second_pass = 1
    %run NZUK_model_b-v2.ipynb

year = 2020
print('\n\n\n YEAR ', year, '\n\n'  )
second_pass   = 0          
%run NZUK_model_a-v2.ipynb
%run NZUK_model_b-v2.ipynb
if no_elasticity == 0:
    %run NZUK_model_c-v2.ipynb
    print('\n=========================================================================')
    print(' Repeating with demand modified due to elasticity of %.2f' % Elasticity, '   Year:', year)  
    print('=========================================================================\n')
    new_electrical_load = elastic_demand   # for demand with elasticity
    second_pass = 1
    %run NZUK_model_b-v2.ipynb

year = 2021

#"""""    

# Run the sub-scripts for selected year 

print('\n\n\n YEAR ', year, '\n\n'  )
second_pass   = 0          
get_ipython().run_line_magic('run', 'NZUK_model_a-v2.ipynb')
get_ipython().run_line_magic('run', 'NZUK_model_b-v2.ipynb')
if no_elasticity == 0:
    get_ipython().run_line_magic('run', 'NZUK_model_c-v2.ipynb')
    print('\n=========================================================================')
    print(' Repeating with demand modified due to elasticity of %.2f' % Elasticity, '   Year:', year)  
    print('=========================================================================\n')
    new_electrical_load = elastic_demand   # for demand with elasticity
    second_pass = 1
    get_ipython().run_line_magic('run', 'NZUK_model_b-v2.ipynb')


# In[ ]:





# In[ ]:





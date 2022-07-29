# NZUK_1
Python model of electricity generation, storage and demand for a net zero UK, with supporting data files.

This model was written as part of a dissertation for an MSc in "Renewable Energy Systems Technology" at Loughborough University in 2021-2022. The dissertation is entitled "Net Zero UK – the Generation and Energy Storage Requirements for the UK to Become Carbon Neutral". A link to the paper will be posted here shortly.

The python code was written on Jupyter Notebooks. The script NZUK_model_top.py is the top level: it executes NZUK_[a,b,c].py in the proper sequence.

The met_meantemp_[2017-2021].csv files are the Central England daily average temperature data files, downloaded from the CEDA website, and manually subdivided into discrete years. The gridwatch_full_[2017-2021].csv files are generation data files downloaded for discrete years from the GridWatch website. These data files are accessed by the code.

Before running the model locally it will be necessary to change the path at line 51 in NZUK_model_a to point to where the CEDA and GridtWatch data files are located.

The model does the following:
* Plots electrity supply and demand curves for a given year, from 2017 to 2021, with a granularity of one day. The temperature and renewable generation resources for that year are derived from the CEDA and GridWatch csv files
* Certain parameters can easily be modified in the top level file to change the combinations of primary renewable generation and biomethane generation
* The model tracks the hydrogen and biomethane generated and used, and plots curves showing the state of the stores
* The model also estimates the LCOE over the year so that the lowest-cost option can be sought 
* Finally the model tests the effectiveness of demand-side responses, including direct price elasticity
* As well as plotting graphs, the model also prints out a lot of derived data

The dissertation should be read in conjunction with the code. It puts the model into context and gives implicit instructions on how to use it. The model is being made freely available here so that the claims in the dissertation can be verified. It is also hoped that other researchers might improve the model, or use it as a starting point for further research. 

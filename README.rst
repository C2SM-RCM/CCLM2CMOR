=====================================================================================
CCLM2CMOR - Climate model output rewriting of COSMO-CLM climate model data for CORDEX
=====================================================================================
 
Worldwide coordinated projects for climate data like CMIP and CORDEX demand that the data meet specific standards very strictly if they are supposed to be integrated and uploaded to an 
archive for a world wide distribution (typically an Earth System Grid Federation node (ESGF) or long term archives as World Data Centre for Climate (WDCC)). 
The model output has to be transformed to meet these specific standards, and this process is often referred to as CMOR, which stands for Climate Model Output Rewriting.

In this project we are developing a CMORization tool which works specifically for the COSMO-CLM (CCLM) model. However, the different processing steps are separated in such a way that it
is also possible to use the tool with other models than the CCLM model.

Requirements
============
which shell commands and Python packages are needed

Usage
=====

The CMOR process is divided into two subprocesses which are explained below.

First step
----------
In a first step the model output data is prepared for the actual CMOR process:
Separate yearly time-series files have to be created for each required variable with the time variable meeting the CORDEX requirements. Additional required fields that are not contained 
in the model output have to be calculated. Note that this step is dependent on the climate model used.
In this project the step is carried out for the CCLM model. The scripts here are not directly applicable to other models.

For the CCLM model the first step of CMOR can be achieved by calling the script *master_post.sh*. Before that, adjust the file *settings.sh* to your needs. You can change the name of the 
driving GCM and the driving experiment name, the time range for the post-processing, directory paths and some more specific settings which are explained later on. The available command
line options are displayed with the command *ksh master_post --help (or -h)*. The script can either be called with the shell command *ksh* or with *sbatch* (if available). If using sbatch,
change the name of your account and the location of the log output and error in the first few lines of *master_post.sh*. Without the option *--no_batch* set, the script will continously 
give out jobs with *sbatch* for one year each to process as many years simultaneously as possible. Without the option --no_extract the script assumes each year is compressed in a tar 
archive and extracts these archives when needed. In batch mode, it actually extracts a number of years at once (controlled with --num_extract).

The master script calls two subscripts: *first.sh* and *second.sh*. In the first script separate monthly time series files are generated for each variable. This script was extracted 
from the post-script routine of the subchain job-control from the CCLM starter package. Thus, if you use the post-processing of the starter package you do not need to carry out this step. 
Use the option --second to skip it. 
Otherwise: nboundcut, IETOT, jobf.sh....

second.sh....


Second step
-----------

All options and features, settings

how to change .ini file

Quality Check
=============






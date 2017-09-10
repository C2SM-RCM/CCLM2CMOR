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
command line programs: ncrcat ncks ncap2 ncatted nccopy cdo
python packages: defined in python files, you will see...

Usage
=====

The CMOR process is divided into two subprocesses which are explained below.

First step
----------
In a first step the model output data is prepared for the actual CMOR process:
Separate yearly time-series files have to be created for each required variable with the time variable meeting the CORDEX requirements. Additional required fields that are not contained 
in the model output have to be calculated. Note that this step is dependent on the climate model used.
In this project the step is carried out for the **CCLM** model. The scripts here are not directly applicable to other models.

For the CCLM model the first step of CMOR can be achieved by calling the script *master_post.sh*. Before that, adjust the file *settings.sh* to your needs. You can change the name of the 
driving GCM and the driving experiment name, the time range for the post-processing, directory paths and some more specific settings which are explained later on. The available command
line options are displayed with the command *ksh master_post.sh --help*. The script can either be called with the shell command *ksh* or with *sbatch* (if available). If using sbatch,
change the name of your account and the location of the log output and error in the first few lines of *master_post.sh*. Without the option *--no_batch* set, the script will continously 
give out jobs with *sbatch* for one year each to process as many years simultaneously as possible. Without the option --no_extract the script assumes each year is compressed in a tar 
archive and extracts these archives when needed. In batch mode, it actually extracts a number of years at once (controlled with --num_extract). The base path to the archives has to be specified 
in *settings.sh*, whereas the specific subdirectory *ARCH_SUB* for the chosen GCM and experiment is created in *master_post.sh* just after reading the command line arguments. How this subdirectory
is created can be changed there.

The master script calls two subscripts: *first.sh* and *second.sh*. In the first script separate monthly time series files are generated for each variable. This script was extracted 
from the post-script routine of the subchain job-control from the CCLM starter package. Thus, if you use the post-processing of the starter package you do not need to carry out this step. 
Use the option --second to skip it. Otherwise you need to specify three values in *settings.sh*: The number of boundary lines (latitude and longitude) to be cut off from the data, *NBOUNDCUT*
and the total number of grid points in longitudinal and latitudinal direction *IE_TOT* and *JE_TOT*. To set *NBOUNDCUT* you can look at the recommended extent of your domain in the CORDEX 
archive specifications (https://is-enes-data.github.io/cordex_archive_specifications.pdf). For the first script to work another file has to be modified: *timeseries.sh*. Here the timeseries
function is called for all variables to be processed. The first argument is the variable name and the second the output stream in which the variable is located in the model output. 
For variables on several pressure levels the function *timeseriesp* is used. The pressure levels *PLEVS* on which the variable is extracted into separate files can be specified right before 
the function. Otherwise the value from the settings file is taken. To create *timeseries.sh* you can use the Python script *write_vars.py*. This script reads in the *CORDEX_CMOR_CCLM_variables_table.csv*
to obtain the required variables (and levels) and the CCLM file which which contains the information on the output streams (e.g. *INPUT_IO.1949*) and creates the file *timeseries.sh*. 
Specify the paths to the input files in *write_vars.py*.

The second script invoked by *master_post.sh* (*second.sh*) concatenates monthly time-series data to annual files with different treatment of accumulated and instantaneous fields. Additionally,
it manipulates the time variable and creates the additional required fields. In *settings.sh* you can tell the program to process all available variables or restrict the processing to specific variables.

Finally, in case of the batch processing, the extracted archives are deleted and the logs of the different years concatenated.

Second step
-----------



how to change .ini file




Sources
=======
overview over source code files: tbd

Quality Check
=============

tbd




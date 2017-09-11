=====================================================================================
CCLM2CMOR - Climate model output rewriting of COSMO-CLM climate model data for CORDEX
=====================================================================================
 
Worldwide coordinated projects for climate data like CMIP and CORDEX demand
that the data meet specific standards very strictly if they are supposed
to be integrated and uploaded to an archive for a world wide distribution
(typically an Earth System Grid Federation node (ESGF) or long term
archives as World Data Centre for Climate (WDCC)). The model output has
to be transformed to meet these specific standards, and this process is
often referred to as CMOR, which stands for Climate Model Output
Rewriting.

In this project we are developing a CMORization tool which works
specifically for the COSMO-CLM (CCLM) model. However, the different
processing steps are separated in such a way that it is also possible
to use the tool with other models than the CCLM model.

Requirements
============
For this tool to work a number of command line tools and Python packages
needed.
The command line programs you need are: ncrcat,ncks,ncap2,ncatted,nccopy,cdo
For the Python packages please look into the .py source code files or
just try to run the code to see which packages are 
missing.
The code works with Python 2.7 and 3.6 (and maybe also older versions)
If you have the relevant tools installed on your machine, there is no 
further installation needed.

Sources
=======

Here is a quick overview of the different source code files and
additional files, their location and their purpose. The location is
relative to the source code directory *src*.

=======================================   ==================   ====================================================================================
Filename                                  Location             Purpose
=======================================   ==================   ====================================================================================
**FIRST STEP**
---------------------------------------------------------------------------------------------------------------------------------------------------
master_post.sh                            .                    Job script that executes the first step of the CMORization
settings.sh                               .                    Configuration file for this first step
help                                      cclm_post            Prints helping information on the command line options of *master_post.sh*
first.sh                                  cclm_post            First subscript 
timeseries.sh                             cclm_post            Variable information for first subscript
second.sh                                 cclm_post            Second subscript
xfer.sh                                   cclm_post            Job script to extract archives
delete.sh                                 cclm_post            Job script to delete archives
**SECOND STEP**                                                  
---------------------------------------------------------------------------------------------------------------------------------------------------
master_cmor.sh                               .                 Job script that executes the second step of the CMORization (the Python script)
cmorlight.py                              CMORlight            Main script of the second CMOR step. Calls all other Python functions.
control_cmor.ini                          CMORlight            Configuration file
init_log.py                               CMORlight            Sets up custom logger
configuration.py                          CMORlight            Reads in configuration from *control_cmor.ini* and provides functions to read or change the entries
settings.py                               CMORlight            Processes some of the entries in the configuration file and reads in the variables table
tools.py                                  CMORlight            Contains all the functions for processing the files
CORDEX_CMOR_CCLM_variables_table.csv      CMORlight/Config     Variables table for the CCLM model controlling which variables are processed at what resolution          
CORDEX_CMOR_WRF_variables_table.csv       CMORlight/Config     Variables table for the WRF model
coordinates_cordex_eur11.nc               CMORlight/Config     NetCDF file containing e.g. latitude and longitude arrays for domain EUR-11
coordinates_cordex_eur44.nc               CMORlight/Config     As above but for the domain EUR-44
**ADDITIONAL**                                                  
---------------------------------------------------------------------------------------------------------------------------------------------------
write_vars.py                             add_scripts          Python script to create the file *timeseries.sh* for the first CMOR step

=======================================   ==================   ====================================================================================


Usage
=====

The CMOR process is divided into two subprocesses which are explained below.

First step
----------
In a first step the model output data is prepared for the actual CMOR process:
Separate yearly time-series files have to be created for each required
variable with the time variable meeting the CORDEX requirements.
Additional required fields that are not contained in the model output
have to be calculated. Note that this step is dependent on the climate
model used. In this project the step is carried out for the **CCLM**
model. The scripts here are not directly applicable to other models.

For the CCLM model the first step of CMOR can be achieved by calling the
script *master_post.sh*. Before that, adjust the file *settings.sh* to
your needs. You can change the name of the driving GCM and the driving
experiment name, the time range for the post-processing, directory paths
and some more specific settings which are explained later on.
The available command line options are displayed with the command
``ksh master_post.sh --help``. The script can either be called with the
shell command ``ksh`` or with ``sbatch`` (if available). If using sbatch,
change the name of your account and the location of the log output and
error in the first few lines of *master_post.sh*. Without the option
``--no_batch`` set, the script will continuously give out jobs with
``sbatch`` for one year each to process as many years simultaneously
as possible. Without the option --no_extract the script assumes each
year is compressed in a tar archive and extracts these archives when
needed. In batch mode, it actually extracts a number of years at once
(controlled with --num_extract). The base path to the archives has to
be specified in *settings.sh*, whereas the specific subdirectory
*ARCH_SUB* for the chosen GCM and experiment is created in
*master_post.sh* just after reading the command line arguments.
How this subdirectory is created can be changed there.

The master script calls two subscripts: *first.sh* and *second.sh*. In
the first script separate monthly time series files are generated for
each variable. This script was extracted from the post-script routine
of the subchain job-control from the CCLM starter package. Thus, if
you use the post-processing of the starter package you do not need
to carry out this step. Use the option --second to skip it. Otherwise
you need to specify three values in *settings.sh*: The number of
boundary lines (latitude and longitude) to be cut off from the data,
*NBOUNDCUT* and the total number of grid points in longitudinal and
latitudinal direction *IE_TOT* and *JE_TOT*. To set *NBOUNDCUT* you
can look at the recommended extent of your domain in the CORDEX archive
specifications (https://is-enes-data.github.io/cordex_archive_specifications.pdf).
For the first script to work another file has to be modified: *timeseries.sh*.
Here the timeseries function is called for all variables to be processed.
The first argument is the variable name and the second the output stream
in which the variable is located in the model output. For variables on
several pressure levels the function *timeseriesp* is used. The pressure
levels *PLEVS* on which the variable is extracted into separate files can
be specified right before the function. Otherwise the value from the settings
file is taken. To create *timeseries.sh* you can use the Python script
*write_vars.py*. This script reads in the *CORDEX_CMOR_CCLM_variables_table.csv*
to obtain the required variables (and levels) and the CCLM file which
which contains the information on the output streams (e.g. *INPUT_IO.1949*)
and creates the file *timeseries.sh*. Specify the paths to the input
files in *write_vars.py*.

The second script invoked by *master_post.sh* (*second.sh*) concatenates
monthly time-series data to annual files with different treatment of
accumulated and instantaneous fields. Additionally, it manipulates
the time variable and creates the additional required fields.
In *settings.sh* you can tell the program to process all available
variables or restrict the processing to specific variables.

Finally, in case of the batch processing, the extracted archives are
deleted and the logs of the different years concatenated.

Second step
-----------

The actual CMORization takes place in the second step. The Python script
processes each variable at the required/desired resolution. It derotates
the wind speed variables, adds the correct 
global attributes, variable attributes and time bounds, concatenates the
files to chunks depending on resolution and creates the correct directory
structure and filenames.

Before running the program type ``export IGNORE_ATT_COORDINATES=1``
into your terminal to make the derotation possible.

The script is run with ``python cmorlight.py [OPTIONS]``. All available
command line options are displayed when using the ``--help`` option and
are repeated here:

optional arguments:
  -h, --help            show this help message and exit
  -i INIFILE, --ini INIFILE
                        configuration file (.ini)
  -t VARTABLE, --table VARTABLE
                        variables table
  -r RESLIST, --resolution RESLIST
                        list of desired output resolutions, comma-separated
                        (supported: 1hr (1-hourly), 3hr (3-hourly),6hr
                        (6-hourly),day (daily),mon (monthly) ,sem
                        (seasonal),fx (for time invariant variables)
  -v VARLIST, --varlist VARLIST
                        comma-separated list of variables to be processed
  -a, --all             process all available variables
  -c, --chunk-var
  -n USE_VERSION, --use-version USE_VERSION
                        version to be added to directory structure
  -d, --no_derotate     derotate all u and v avariables
  -m SIMULATION, --simulation SIMULATION
                        which simulation specific settings to choose
  -g DRIVING_MODEL_ID, --gcm DRIVING_MODEL_ID
                        set used driving model
  -x DRIVING_EXPERIMENT_NAME, --exp DRIVING_EXPERIMENT_NAME
                        set used experiment
  -E DRIVING_MODEL_ENSEMBLE_MEMBER, --ensemble DRIVING_MODEL_ENSEMBLE_MEMBER
                        set used ensemble
  -O, --overwrite       Overwrite existent output files
  -f, --force_proc      Try to process variable at specific resolution
                        regardless of what is written in the parameter table
  -S, --silent          Write only minimal information to log (variables and
                        resolutions in progress, warnings and errors)
  -V, --verbose         Verbose logging for debugging
  -A, --append_log      Append to log instead of overwrite
  -l, --limit           Limit time range for processing (range set in .ini
                        file or parsed)
  -s PROC_START, --start PROC_START
                        Start year for processing if --limit is set.
  -e PROC_END, --end PROC_END
                        End year for processing if --limit is set.
  -M, --multi           Use multiprocessing with number of cores specified in
                        .ini file.
  -P, --propagate       Propagate log to standard output.
  --remove              Remove source files after chunking


In a file here called *control_cmor.ini* processing options, paths and
simulation details are set. You can create several such configuration
files and choose the one you want to use with the ``--ini`` option when
running the main script *cmorlight.py*. All lists in this file should
be comma-separated and not contain spaces. In the last section
(e.g. named *settings_CCLM*) of this file you can set simulation specific
options such as global attributes. You can define several such sections
(always named *settings_[EXT]* and choose one by specifying the
extension EXT in the configuration file (entry *simulation*) or in the
command line (option ``--sim``). Detailed instructions which
variables should be processed with what method at which resolution are
taken from a modified version of the CORDEX variables requirement table.
Here a table for the CCLM model and for the WRF model are included.
Specify which table to use in the configuration file (*paramfile*) or
on the command line (``--param`` option). For other models you have
to create your own table starting with the CORDEX variables requirement
table (pdf version here: https://is-enes-data.github.io/CORDEX_variables_requirement_table.pdf).
Make sure to use the semicolon ";" as delimiter and include a header line.
MORE ON THE TABLE?

If essential variables as *lon*, *lat* or *rotated_pole* are missing in
the data, the script tries to copy them from a file specified under
*coordinates_file* in the configuration file. 
Make sure to provide such a file suitable for your domain and resolution.
Here, files for the domains EUR-11 and EUR-44 are provided.
If you want to add vertices to your output files, you have to specify a
file from which to take them (entry *vertices_file*) and set
*add_vertices=True*.

If you want to process all variables in the table, use the ``--all`` option.
Otherwise, specify the variables with ``--varlist``. You can also choose
the resolutions at which to produce the output with ``--resolution`` or
in the variable *reslist* in the configuration file. Unless ``--force_proc``
is set, only the resolutions specified in the table are considered for
each variable. Note that the seasonal processing uses the output of
the daily processing. Hence, the latter has to be executed before the
former.

You can limit the time range for processing with the option ``--limit``
and providing the start and end years on the command line
(``--start``,``--end``) or in the configuration file. Otherwise,
all available years are processed.

The processing will finish much faster when using multiprocessing
(``--multi``). In this way several years are processed simultaneously.
For this, specify the number of available cores in the configuration file 
and the desired time range over the command line or in the configuration
file.

After the processing you can concatenate the files to chunks by running
the script again with the ``--chunk-var`` option. Add the option
``--remove`` to this call to delete the superfluent yearly files .

You can use the job script *master_cmor.sh* to run the job on a
compute node with ``sbatch master_cmor.sh [OPTIONS]``. You can
directly pass the options of the python program. With the option
``--batch`` you can run several jobs simultaneously processing *cores*
years each. In this case you have to specify the variable *cores* in
this script.


Quality Assessment
==================

We cannot guarantee that the data processed with this tool perfectly meet
the CORDEX requirements after processing. Please use the Quality Assessment
tool of the DKRZ to check your data. You can find the latest version 
of it here: https://github.com/IS-ENES-Data/QA-DKRZ/
If any errors occur that might have to do with the CMOR tool, don't 
hesitate to contact us.


Contributing
============

We are happy for everybody who wants to participate in the development 
of the CMOR tool. Look at the open issues to see what there is to do
or create an issue yourself if you found one.


Involved people
===============

In the development of this tool a number of people from different
institutions were involved:

- Matthias Göbel (Swiss Federal Institute of Technology (ETH), Zürich,Switzerland)
- Hans Ramthun (German Climate Computing Center(DKRZ), Hamburg,Germany)
- Hans-Jürgen Panitz (Karlsruhe Institute of Technology (KIT),Karlsruhe, Germany)
- Klaus Keuler (Brandenburgische Technische Universität Cottbus-Senftenberg (BTU), Cottbus, Germany)
- Christian Steger (Deutscher Wetterdienst (DWD), Offenbach, Germany)


Hans-Jürgen Panitz, Klaus Keuler and Christian
Steger initiated the development of the tool and decided on its
general structure. They also created the table for the Python script for
the CCLM model. Hans Ramthun developed most of the Python code and
Klaus Keuler wrote the script *second.sh*. Matthias Göbel combined the
different scripts to this complete tool, fixed numerous bugs in the
Python code, increased the user-friendliness and flexibility of it and
wrote the first version of this documentation. Silje Sørland,
Daniel Lüthi (both ETH Zürich) and Hans-Jürgen Panitz helped him
with that.

Thanks to all these people for your work!





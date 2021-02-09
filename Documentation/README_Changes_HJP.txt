Changes by H.-J. Panitz, IMK-TRO/KIT; look for "HJP" in scripts being changed
You find the scripts that I changed in CCLM2CMOR/src/CMMORlight (if you did not change the standard diretory structure of the CCLM2CMOR package)

December, 2020

affected script
  - tools.py, see "#HJP Dec 2020"
    def compress_output:
      change nccopy command to deflation rate 1, but using shuffling;
      this change reduces the size of a file by about 47% compared to the previous compression;
      of course, results will no be changed

    def derotate_uv:
     in case of derotation of u and v wind-components, which uses the CDO-method,
     the Environment variable IGNORE_ATT_COORDINATES will always get the required value 1,
     in order to avoid a crash of the tool if the value is wrong
     It will be checked whether the variable exist or not, and if yes, which value it has; this already set value will be stored
     Then, the value will be set to 1 in any case
     At the end of "derotate_uv" the value of IGNORE_ATT_COORDINATES will be
     - kept, if the Envrionment variable had not been defined before
     - put back to the stored original value, if the variable had already been defined before 

November, 2020

affected script:
  - tools.py, process_file_fix
    comment out the line "mulc_factor = 1.0" (about line 750)
    there might be mulc_factors different from 1 also for fx-fields, e.g. sftlf that has to be given in %

October 2020

Include Directory "Batch" in CCLM2CMOR.
Offers the opportunity to run the CMOR-process and subsequent chunking as batch-jobs.
It is an alternative to the schedular "job" in CCLM2CMOR/src
Infos are given in "README_Batch.rst" in Directory CCLM2CMOR/Documentaion.

Include a PDF that explains the CSV-Table located in CCLM2CMOR/src/CMORlight/Config.
Look into Directory CCLM2CMOR/Documentation.
Name of the PDF: Explaining_CSV_table.pdf


cleaning of affected scripts with respect to "traces" related to extended Directory-and Filenamestructure,
especially everthing related to the former "global_attr_list_2ndNest"

affected files and scripts:
 - control_cmor.ini 
 - cmorlight.py
 - settings.py
 - tools.py

tools.py
- it might happen that the data-type of "rotated_pole" is not consistent among the CMORized variables.
  For most of them the data-type is "char", as it is coded in "tools.py", for some it might be "int".
  This depends on
  - whether the variable has the "_FillValue" and/or "missing_value" attribute
  - the value of theses attributes, the CCLM default is -1E20
  - the CDO version you are using
  If you are considering such a variable, then the CMOR-tool sets the CCLM default missing value to the
  CMOR standard +1E20, using the appropriate CDO command. When you are using one of the recent CDO-Version,
  e.g. with version no. > 1.7, then the impact of the application of any CDO command is that the data-type
  of rotated_pole is always set to "int". Don't ask me why!!
  Therefore and in order to get consistency among all CMORized variables, I included the NCO command
  "ncap2" twice in tools.py, setting the data-type of the CMORized variables to "char".
  Why might this change be important?
  In subsequent applications that use the CMORized data the consistency might be necessary since
  inconsistency leads to a crashes of the applications.
  Prominent example: the tool, written for EURO-CORDEX, that remaps from rotated coordinates to regular
  geographical lon/lat coordinates.

August 2020

Change of "tools.py" in order to get a version of the tool that is compatible to the structures
required by CORDEX:
- Directory structure
- file name structure
- names of mandatory globla attributes
see also:
CORDEX Archive Design
http://cordex.dmi.dk/joomla/images/CORDEX/cordex_archive_specifications.pdf
Version 3.1, 3 March 2014
by
Christensen et al.

Opinion of HJP:
we should keep both version of the tool, respectively of script "tools.py",
- the version compatible to CORDEX standards
- and the version taking into account the extended directory- and filename structures

February 2020
Changes by H.-J. Panitz, IMK-TRO/KIT; look for "HJP" in scripts being changed
Change has also been implemented in most recent GITHUB Version by Marie-Estelle


tools.py:
 - the conversion factors possibly defined in the CSV-table must not be divided by the time resolution of the input data
    the correct value for this factor, if it is needed, is in the responsibility of the user
    therefore, the follwing lines are commented out
        #conversion factor
#       conv_factor = params[config.get_config_value('index','INDEX_CONVERT_FACTOR')].strip().replace(',','.')
#       #if  conv_factor not in ['', '0', '1']:
#       if  conv_factor not in ['', '0', '1', '-1']:
#           #change conversion factor for accumulated variables
#           if params[config.get_config_value('index','INDEX_FRE_AGG')] == 'a':
#               conv_factor = str(float(conv_factor) / input_res_hr)
#           cmd_mul = ' -mulc,%s ' %  conv_factor
#       elif conv_factor == '-1':
#           cmd_mul = ' -mulc,%s ' %  conv_factor
#       else:
#           cmd_mul = ""
#       logger.debug("Multiplicative conversion factor: %s" % cmd_mul)
#
#  now the change starts; the factor won't be divided by the time resolution anymore
        #conversion factor
        conv_factor = params[config.get_config_value('index','INDEX_CONVERT_FACTOR')].strip().replace(',','.')
        if  conv_factor not in ['', '0', '1']:
            cmd_mul = ' -mulc,%s ' %  conv_factor
        else:
            cmd_mul = ""
        logger.debug("Multiplicative conversion factor: %s" % cmd_mul)

March and September 2019

cmorlight.py
- move the definintion of LOG-files after the setting of varlist
  and extension of name of Log-File by element "0" (the first entry in varlist) of varlist,
  which denotes the CMOR-name of the first variable in the list
  Purpose of this change: if the script is executed several times, either in foreground or using a batch-environment,
  but with different variables, then the LOG-file will not be overwritten, but several LOG-files will be created that
  can be distinguished by the CMOR-nmae of the the first entry in varlist


control_cmor.ini:
- include consideration of variables on Z-Level (this was necessary for FPS Convection, for example)
    define name of the level type in the variables table if the variable on Z levels should be considered

- create index name for column 23 of CSV-table where one can include some explaining comment for a variable
    this explanation will be incuded in the output files as variables's attributte "comment"

- issue: naming of output directories and output files in case of a 2-nest modelling approach
   if the current simulation is the 2nd nest from a double nest approach,
   set list of extensions for final directory structure and filename
   Name of list: first_nest_list
   put None as the entry of "first_nest_list" if the current simulation is only a 1-Nest approach
   entries for list variables, in case of a double nest approach, are defined in section 'settings_CCLM'


tools.py:
- include consideration of variables on Z-Level:
    include variable "height" and its attributes

- include consideration of mrso1, total moisture content of uppermost soil level
    for mrso1 select only the first soil level from W_SO

- package "netcdftime" might not exist in the used python-Installation (for example, at HLRS, Stuttgart)
    then comment the line 
      "from netCDF4 import netcdftime"
    and try to use the package "utime"
      "from cftime import utime"

- include variable's attribute "comment" if the corresponding entry in CSV-table is not empty

- possibility to to put extended information of intermediate nest into the directory structure (module "create_outpath"); has been commented out again in the current version

- possibility to to put extended information of intermediate nest into the filename structure (module "create_filename"); has been commented out again in the current version

- the current version of "tools.py" (September 2019) creates ESGF conformal structures for directory- and filenames; thus, the extended structures according to the discussions within
    the CLM-Community are not yet "active", but could be "reactivated" rather easily


CSV-Table:  (which, by default, resides in CCLM2CMOR/src/CMMORlight/Config)
  the title of column 25 (counting starts with 0) was "description"; entries in this column have not been considered so far
  I changed the title of this column to "comment".
  The idea is that the user now can include explaining comments there; for example, for CMOR variable "mrso", the total soil moisture integrated over a certain number of soli layers,
   one can say that the moisture has been summed over a certain amount of layers, e.g. 8, and what the depth of the deepest layer is
  Such an explantion for mrso, for example, is required for the CMORization process of Convection FPS as an additional variable attribute called "comment".
  The CCLM2CMOR script now includes this attribute if the entry in column 23, related to a variable, is not empty.

  Some further important hints for the CSV table:
  - Each entry in the different cells must not begin with an empty space, especially those cells describing the NETCDF cell-methods
  - The first column must contain the CCLM variable name as it is indicated in the names of the input path and input NETCDF file
  - The second column must contain the variable name as it is written in the NETCDF input file itself 
     (the two names in the path and filename, and in the file itself must not necessarily be identical)
  - if you want to create also seasonal data for a variable, then you must have created the daily data before; the daily CMORized data will be used as input for the 
    creation of seasonal files




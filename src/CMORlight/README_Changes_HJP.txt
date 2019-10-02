March and September 2019
Changes by H.-J. Panitz, IMK-TRO/KIT; look for "HJP" in scripts being changed
You find the scrpits that I changted in CCLM2CMOR/src/CMMORlight (if you did not change the standard diretory structure of the CCLM2CMOR package)

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
  the title of column 23 (counting starts with 0) was "description"; entries in this column have not been considered so far
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




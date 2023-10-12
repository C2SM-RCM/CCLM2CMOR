"""

Contains all the functions for processing the files

"""
import os
import sys
from netCDF4 import Dataset
from netCDF4 import num2date
from netCDF4 import date2num
#MED Apr 2019: netcdftime package no longer included in netCDF4, try 'import netcdftime' or use the package "utime" depending on your Python installation.
#import netcdftime
import cftime

from collections import OrderedDict
import tempfile
import subprocess
import numpy as np
import datetime
import uuid
import time as timepkg
# global variables
import settings
# configuration
import get_configuration as config

import logging
log = logging.getLogger("cmorlight")

# -----------------------------------------------------------------------------
def shell(cmd,logger=log):
    '''
    Call a shell command
    Parameters
    ----------
    cmd : str
        Shell command to execute
    logger : logging.Logger
        Which logger to use
    '''
    prc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    prc.wait()
    if prc.returncode != 0:
        raise Exception('Shell Error: %s for command: %s' % (prc.communicate()[0], cmd) )
    else:
        logger.debug(cmd)

    return prc.communicate()[0]

# -----------------------------------------------------------------------------
def get_input_path(derotated=False):
    '''
    Read input path from settings, take derotated one if needed
    '''
    if derotated:
        retVal = settings.DirDerotated
    else:

        retVal = settings.DirIn
    return retVal

# -----------------------------------------------------------------------------
def get_var_lists():
    '''
    Extract all required variables from parameter table
    '''
    lst = []
    for row in sorted(settings.param):
        var=settings.param[row][config.get_config_value('index','INDEX_VAR')]
        if not var in lst: #do not append variables twice as they appear twice in params
            lst.append(var)
    return sorted(lst)

# -----------------------------------------------------------------------------
def set_attributes(params):
    '''
    Fill dictionaries in settings with global attributes and additional netcdf attributes
    '''
    # get global attributes from ini-file
    for name in settings.global_attr_list :
        try:
            settings.Global_attributes[name.strip()] = config.get_sim_value(name.strip())
        except:
            raise Exception("Global attribute " + name + " is in global_attr_list but is not defined in the configuration file!")

    #Invariant attributes
    #settings.Global_attributes['project_id']="CORDEX" #global attribute "project_id" should be variable, thus defined in the ini-file
    settings.Global_attributes['product']="output"

    # set addtitional netcdf attributes
    settings.netCDF_attributes['RCM_NAME'] = params[config.get_config_value('index','INDEX_VAR')]
    settings.netCDF_attributes['RCM_NAME_ORG'] = params[config.get_config_value('index','INDEX_RCM_NAME_ORG')]
    settings.netCDF_attributes['long_name'] = params[config.get_config_value('index','INDEX_VAR_LONG_NAME')]
    settings.netCDF_attributes['standard_name'] = params[config.get_config_value('index','INDEX_VAR_STD_NAME')]
    settings.netCDF_attributes['units'] = params[config.get_config_value('index','INDEX_UNIT')]
    settings.netCDF_attributes['missing_value'] = np.float32(config.get_config_value('float','missing_value'))
    settings.netCDF_attributes['_FillValue'] = config.get_config_value('float','missing_value')

# -----------------------------------------------------------------------------
def print_progress(currfile,nfiles):
    '''
    Prints progress to standard output
    '''
    percent = float(currfile) /float(nfiles)
    hashes = '#' * int(round(percent * 20))
    spaces = ' ' * (20 - len(hashes))
    sys.stdout.write('\r'+"[{0}] {1:.1f}%".format(hashes + spaces, percent * 100))
    sys.stdout.flush() 

# -----------------------------------------------------------------------------
def create_outpath(res,var):
    '''
    Create and return the output path string from global attributes and dependent on resolution res and variable var
    '''
    result = "%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s" % \
                (settings.Global_attributes["project_id"],
                 settings.Global_attributes["mip_era"],
                 settings.Global_attributes["activity_id"],
                 settings.Global_attributes["CORDEX_domain"],
                 settings.Global_attributes["institute_id"],
                 settings.Global_attributes["driving_model_id"],
                 settings.Global_attributes["experiment_id"],
                 settings.Global_attributes["driving_model_ensemble_member"],
                 settings.Global_attributes["model_id"],
                 settings.Global_attributes["rcm_version_id"],
                 res,
                 var
                )

    if settings.use_version!="":
        result += "/" + settings.use_version
    return result

# -----------------------------------------------------------------------------
def create_filename(var,res,dt_start,dt_stop,logger=log):
    '''
    Create and return the filename string from global attributes and dependent on resolution res, variable var and time range dt_start to dt_stop
    '''
    #File naming different for instantaneous and interval representing (average,min,max) variables
    agg=settings.param[var][config.get_config_value('index','INDEX_FRE_AGG')] #subdaily aggregation method: average or instantaneous

    if res in ["1hr","3hr","6hr","12hr"]:
        if agg=="i":
            bounds=[["0000","2300"],["0000","2100"],["00","18"],["00","12"]]
        elif agg=="a":
            bounds=[["0030","2330"],["0130","2230"],["03","21"],["06","18"]]
        else:
            bounds=[["0000","2300"],["0000","2100"],["00","18"],["00","12"]]
            logger.error("Subdaily aggregation method in column %s of parameter table must be 'i' or 'a'! Assumed instantaneous..." % config.get_config_value('index','INDEX_FRE_AGG'))

    if res == "1hr":
        dt_start = "%s%s" % (dt_start,bounds[0][0])
        dt_stop = "%s%s" % (dt_stop,bounds[0][1])
    if res == "3hr":
        dt_start = "%s%s" % (dt_start,bounds[1][0])
        dt_stop = "%s%s" % (dt_stop,bounds[1][1])
    elif res == "6hr":
        dt_start = "%s%s" % (dt_start,bounds[2][0])
        dt_stop = "%s%s" % (dt_stop,bounds[2][1])
    elif res == "12hr":
        dt_start = "%s%s" % (dt_start,bounds[3][0])
        dt_stop = "%s%s" % (dt_stop,bounds[3][1])
    elif res == "day":
        dt_start = dt_start[:8]
        dt_stop = dt_stop[:8]
    elif res in ["mon","sem"]:
        dt_start = dt_start[:6]
        dt_stop = dt_stop[:6]
    
    #time range to add to file name for non-constant variables
    if res == 'fx':
        trange = ""
    else:
        trange = "_%s-%s" % (dt_start,dt_stop)

    logger.debug("Filename start/stop: %s, %s" % (dt_start,dt_stop))

    result = "%s_%s_%s_%s_%s_%s_%s_%s%s.nc" % (var,
                  settings.Global_attributes["CORDEX_domain"],
                  settings.Global_attributes["driving_model_id"],
                  settings.Global_attributes["experiment_id"],
                  settings.Global_attributes["driving_model_ensemble_member"],
                  settings.Global_attributes["model_id"],
                  settings.Global_attributes["rcm_version_id"],
                  res,
                  trange,
                )

    return result

# -----------------------------------------------------------------------------
def compress_output(outpath,year=0,logger=log):
    '''
    Compress files with nccopy
    '''
    if os.path.exists(outpath):
        ftmp_name = "%s/%s-%s.nc" % (settings.DirWork,year,str(uuid.uuid1()))
#HJP Dev 2020 Begin
#       cmd = "nccopy -k 4 -d 4 %s %s" % (outpath,ftmp_name)
        cmd = "nccopy -d 1 -s %s %s" % (outpath,ftmp_name)
#HJP Dev 2020 End
        retval=shell(cmd,logger=logger) 
        # remove help file
        os.remove(outpath)
        retval=shell("mv %s %s" % (ftmp_name,outpath),logger=logger)
    
    else:
        logger.error("File does not exist: (%s)" % outpath)

# -----------------------------------------------------------------------------
def set_attributes_create(outpath,res=None,year=0,logger=log):
    '''
    Set and delete some (global) attributes
    '''
    if os.path.exists(outpath):
        f_out = Dataset(outpath,'r+')
        if res:
            f_out.setncattr("frequency",res)

        try: #delete unnecessary attribute
            f_out.variables["lon"].delncattr("_CoordinateAxisType")
            f_out.variables["lat"].delncattr("_CoordinateAxisType")
        except RuntimeError:
            pass

        # set new tracking_id
        tracking_id=str(uuid.uuid1())
        f_out.setncattr("tracking_id",tracking_id)
        logger.debug("Set tracking_id: "+tracking_id)
        # set new creation_date
        f_out.setncattr("creation_date",datetime.datetime.now().strftime(settings.FMT))

        if 'history' in f_out.ncattrs():
            f_out.delncattr("history")

        # commit changes
        f_out.sync()
        # close output file
        f_out.close()
        logger.info("File: %s" % outpath)
        logger.info("final attributes created")
    else:
#       logger.error("File does not exist: (%s)" % outpath)
        logger.error("File does not exist: %s" % outpath)

# -----------------------------------------------------------------------------
def set_coord_attributes(f_var,f_out):
    '''
    Set the attributes of the pressure or height variable and the coordinates attribute of the variable f_var
    Parameters
    ----------
    f_var : netCDF4._netCDF4.Variable
        Variable of netCDF Dataset being processed
    f_out : netCDF4._netCDF4.Dataset
        Input file opened as a netCDF Dataset
    '''
    if not f_out:
        log.warning("No output object for setting coordinates value available!")
        return

    if 'plev' in f_out.variables:
        var_out = f_out.variables ['plev']
        var_out.units = "Pa"
        var_out.axis = "Z"
        var_out.positive = "down"
        var_out.long_name = "pressure"
        var_out.standard_name = "air_pressure"
        if 'lon' in f_out.variables and 'lat' in f_out.variables:
            f_var.coordinates = 'plev lat lon'
        else:
            cmd = "No lon/lat coordinates available!"
            raise Exception(cmd)

    elif 'height' in f_out.variables:
        var_out = f_out.variables ['height']
        var_out.units = "m"
        var_out.axis = "Z"
        var_out.positive = "up"
        var_out.long_name = "height"
        var_out.standard_name = "height"
        if 'lon' in f_out.variables and 'lat' in f_out.variables:
            f_var.coordinates = 'height lat lon'
        else:
            cmd = "No lon/lat coordinates available!"
            raise Exception(cmd)

    else:
        if 'lon' in f_out.variables and 'lat' in f_out.variables:
            f_var.coordinates = 'lat lon'
        else:
            cmd = "No lon/lat coordinates available!"
            log.error(cmd)
            raise Exception(cmd)

# -----------------------------------------------------------------------------
def new_dataset_version():
    '''
    Create and return new dataset version from current date
    this will be inserted in the output directory structure
    if add_version_to_outpath=True in configuration file
    '''
    return "v%s" % datetime.datetime.now().strftime("%Y%m%d")

# -----------------------------------------------------------------------------
def get_out_dir(var,res,createdir=True):
    '''
    Create and return the complete output path string using the resolution res and the variable var
    and make the corresponding directory
    '''
    outpath = create_outpath(res,var)
    outpath = "%s/%s" % (settings.DirOut,outpath)
    #try to make directory
    if createdir:
        try:
            os.makedirs(outpath)
        except:
            pass
    return outpath

# -----------------------------------------------------------------------------
def proc_chunking(params,reslist):
    '''
    Create AGG_DAY (daily), AGG_MON (monthly) and/or AGG_SEM (seasonal) years chunks of yearly input files
    (as defined in configuration file; default: 5,10 and 10, respectively) depending on resolutions in reslist
    '''
    # get cdf variable name
    var = params[config.get_config_value('index','INDEX_VAR')]

    for res in reslist:
        if res == 'day':
            max_agg = config.get_config_value('integer','AGG_DAY')
        elif res == 'mon':
            max_agg = config.get_config_value('integer','AGG_MON')
        elif res == 'sem':
            max_agg = config.get_config_value('integer','AGG_SEM')
        else:
            cmd = "Resolution (%s) is not supported in chunking, keep it as it is." % res
            log.debug(cmd)
            continue
        log.log(35,"\nresolution: %s " % (res))
        indir = get_out_dir(var,res,False)
        if not os.path.isdir(indir):
            log.info("Input directory %s does not exist!" % indir)
            continue
        outdir = indir
        #extra directory to put chunked files into
        if config.get_config_value('settings','chunk_into',exitprog=False)!="":
            outdir=outdir+"/"+config.get_config_value('settings','chunk_into',exitprog=False)

        log.debug("Output directory: %s" % outdir)
        for dirpath,dirnames,filenames in os.walk(indir):
            f_list = []
            start_date = 0
            if len(filenames) == 0:
                log.warning("Directory is empty: %s" % indir)
            
            for f in sorted(filenames):
                if f[-3:] != ".nc": #skip unsuitable files
                    continue
                idx = f.index("%s_" % res)
                dates=f.split("_")[-1][:-3].split("-")
                if start_date == 0:
                    start_date=dates[0]
                start_yr=int(dates[0][:4])
                stop_date=dates[1]
                stop_yr=int(stop_date[:4])
                trange=np.round(stop_yr+int(stop_date[4:6])/12-start_yr-(int(dates[0][4:6])-1)/12,5)              
                # if there is more than one year between start and stop year: skip file
                if trange > 1:
                    log.debug("%s is not a yearly file. Skipping..." % f)
                    continue

                f_list.append("%s/%s" % (indir,f))
                if stop_yr % max_agg == 0:

                    do_chunking(f_list,var,res,start_date, stop_date,outdir)
                    # reset parameter
                    f_list = []
                    start_date = 0
            # do the same for whats left in list
            if len(f_list) > 1:
                do_chunking(f_list,var,res,start_date, stop_date,outdir)

# -----------------------------------------------------------------------------
def do_chunking(f_list,var,res,start_date, stop_date, outdir):
    '''
    Execute actual chunking of files in f_list
    '''
    # generate complete output path with output filename
    outfile = create_filename(var,res,start_date,stop_date)
    # generate outpath with outfile and outdir

    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    outpath = "%s/%s" % (outdir,outfile)

    # generate input filelist
    flist = " ".join(f_list)
    # cat files to aggregation file
    # skip if exist
    if (not os.path.isfile(outpath)) or config.get_config_value('boolean','overwrite'):
        if os.path.isfile(outpath):
            log.info("Output file exists: %s, overwriting..." % (outfile))
        else:
            log.info("Concatenating files to %s" % (outfile))
        retval=shell("ncrcat -h -O %s %s " % (flist,outpath))

        # set attributes
        set_attributes_create(outpath,res)
    else:
        log.info("Output file exist: %s, skipping!" % (outfile))
    # remove source files
    if outpath in f_list:
        f_list.remove(outpath)
        flist = " ".join(f_list)
    for l in f_list:
        log.info(l.split("/")[-1])
    if config.get_config_value('boolean','remove_src') and len(f_list)!=0:
        log.info("Removing yearly input files")
        retval=shell("rm -f %s " % (flist))

# -----------------------------------------------------------------------------
def leap_year(year, calendar='standard'):
    '''
    Determine if year is a leap year
    '''
    leap = False
    if ((calendar in ['standard','gregorian','proleptic_gregorian','julian']) and (year % 4 == 0)):
        leap = True
        if ((calendar == 'proleptic_gregorian') and (year % 100 == 0) and (year % 400 != 0)):
            leap = False
        elif ((calendar in ['standard', 'gregorian']) and (year % 100 == 0) and (year % 400 != 0) and (year < 1583)):
            leap = False
    return leap

# -----------------------------------------------------------------------------
def add_vertices(f_out,logger=log):
    '''
    Add vertices to output file from vertices file
    '''
    # read vertices from file if exist
    if os.path.isfile(config.get_sim_value("vertices_file")):
        f_vert = Dataset(config.get_sim_value("vertices_file"),'r')
        if 'vertices' in f_vert.dimensions.keys() and 'vertices' not in f_out.dimensions.keys():
            # is present I know the content of this file
            if 'vertices' in f_vert.dimensions.keys():
                f_out.createDimension('vertices',len(f_vert.dimensions['vertices']))
            else:
                # standard len
                f_out.createDimension('vertices',4)
        if 'lon_vertices' in f_vert.variables.keys() and 'lon_vertices' not in f_out.variables.keys():
            lon_vertices = f_vert.variables['lon_vertices']
            # create lon_vertices in output
            var_out = f_out.createVariable('lon_vertices',datatype='d',dimensions=lon_vertices.dimensions)
            # copy content to new datatype
            if 'lon' in f_vert.variables.keys():
                f_lon = f_vert.variables['lon']
                if 'units' in f_lon.ncattrs():
                    var_out.units = str(f_lon.units)
                else:
                    var_out.units = "degrees_east"
                if not 'lon' in f_out.variables.keys():
                    copy_var(f_vert,f_out,'lon',logger=logger)
            else:
                var_out.units = "degrees_east"
            f_out_lon = f_out.variables['lon']
            f_out_lon.bounds = 'lon_vertices'
            var_out[:] = lon_vertices[:]
            logger.info("Vertices (lon) set!")
        if 'lat_vertices' in f_vert.variables.keys() and 'lat_vertices' not in f_out.variables.keys():
            lat_vertices = f_vert.variables['lat_vertices']
            # create lat_vertices in output
            #var_out = f_out.createVariable('lat_vertices',datatype='f',dimensions=['rlat','rlon','vertices'])
            var_out = f_out.createVariable('lat_vertices',datatype='d',dimensions=lat_vertices.dimensions)
            # copy content to new datatype
            if 'lat' in f_vert.variables.keys():
                f_lat = f_vert.variables['lat']
                if 'units' in f_lon.ncattrs():
                    var_out.units = str(f_lat.units)
                else:
                    var_out.units = "degrees_north"
                if not 'lat' in f_out.variables.keys():
                    copy_var(f_vert,f_out,'lat',logger=logger)
            else:
                var_out.units = "degrees_north"
            f_out_lat = f_out.variables['lat']
            f_out_lat.bounds = 'lat_vertices'
            var_out[:] = lat_vertices[:]
            logger.info("Vertices (lat) set!")

        # commit changes
        f_out.sync()

    else:
        logger.error("Vertices file %s does not exist! No vertices added..." % config.get_sim_value("vertices_file") )

# -----------------------------------------------------------------------------
def check_resolution(params,res,process_table_only):
    '''
    Check whether resolution "res" is declared in specific row of variables table "param".
    '''
    #MED>> add additional subdaily resolution 
    if res in ["1hr","3hr","6hr","12hr"]:
        res_hr=(float(res[:-2])) #extract time resolution in hours
        freq=24./res_hr
        freq_table=params[config.get_config_value('index','INDEX_FRE_ASU')]
        if (freq_table=="" or float(freq_table) != freq) and process_table_only:
            freq_table=params[config.get_config_value('index','INDEX_FRE_SUB')]	
    #MED<<
    elif res=="day":
        freq_table=params[config.get_config_value('index','INDEX_FRE_DAY')]
        freq=1. #requested samples per day
    elif res=="mon":
        freq_table=params[config.get_config_value('index','INDEX_FRE_MON')]
        freq=1. #requested samples per month
    elif res=="sem":
        freq_table=params[config.get_config_value('index','INDEX_FRE_SEM')]
        freq=1. #requested samples per month
    elif res == 'fx':
        freq_table=params[config.get_config_value('index','INDEX_FX')]
        freq=freq_table
    else:
        log.warning("Time resolution (%s) is not supported, skipping..." % res)
        return False

    #if process_table_only is set: check if requested time resolution is declared in table
    if (freq_table=="" or float(freq_table) != freq) and process_table_only:
        log.info("Requested time resolution (%s) not declared in parameter table. Skipping.." % res)
        return False
    else:
        return True

# -----------------------------------------------------------------------------
def get_attr_list(var_name,args=[]):
    '''
    Set pre defined attributes for variables lon,lat
    '''
    att_lst = OrderedDict()
    if var_name == 'lon':
        att_lst['standard_name'] = 'longitude'
        att_lst['long_name'] = 'longitude'
        att_lst['units'] = 'degrees_east'
        if config.get_config_value('boolean','add_vertices') == True:
            att_lst['bounds'] = "lon_vertices"
            
    elif var_name == 'lat':
        att_lst['standard_name'] = 'latitude'
        att_lst['long_name'] = 'latitude'
        att_lst['units'] = 'degrees_north'
        if config.get_config_value('boolean','add_vertices') == True:
            att_lst['bounds'] = "lat_vertices"

    elif var_name == 'rlon':
        att_lst['standard_name'] = 'grid_longitude'
        att_lst['long_name'] = 'longitude in rotated pole grid'
        att_lst['units'] = 'degrees'
        att_lst['axis'] = 'X'

    elif var_name == 'rlat':
        att_lst['standard_name'] = 'grid_latitude'
        att_lst['long_name'] = 'latitude in rotated pole grid'
        att_lst['units'] = 'degrees'
        att_lst['axis'] = 'Y'
        
    elif var_name == 'time':
        att_lst['standard_name'] = 'time'
        att_lst['long_name'] = 'time'
        att_lst['units'] = args[0]
        att_lst['calendar'] = args[1]
        att_lst['axis'] = 'T'
        
    elif var_name == 'rotated_pole':
        att_lst['long_name'] = 'coordinates of the rotated North Pole'
        att_lst['grid_mapping_name'] = 'rotated_latitude_longitude'
        att_lst['grid_north_pole_latitude'] = float(args[0])
        att_lst['grid_north_pole_longitude'] = float(args[1])
        
    return att_lst

# -----------------------------------------------------------------------------
def copy_var(f_in,f_out,var_name,logger=log):
    '''
    Copy variable with corresponding attributes from in_file to out_file if present there
    '''
    if var_name in f_in.variables and var_name not in f_out.variables:
        var_in = f_in.variables[var_name]
        j = 0
        for var_dim in var_in.dimensions:
            if var_dim not in f_out.dimensions:
                f_out.createDimension(var_dim,size=var_in.shape[j])
            j = j+1

        if var_name in ['rlat','rlon','lat','lon','time','time_bnds']:
            new_datatype = 'd'
        elif var_name in ['rotated_latitude_longitude','rotated_pole']:
            new_datatype = 'c'
        else:
            new_datatype = 'f'
        var_out = f_out.createVariable(var_name,datatype=new_datatype,dimensions=var_in.dimensions )
        # set all as character converted with str() function
        if var_name in ['lat','lon','rlon','rlat','time']:
            att_lst = get_attr_list(var_name)
        elif var_name == 'rotated_pole':
            att_lst = get_attr_list(var_name,[var_in.grid_north_pole_latitude,var_in.grid_north_pole_longitude])

        else:
            att_lst = OrderedDict()
            for k in var_in.ncattrs():
                if config.get_config_value('boolean','add_vertices') == False and k == 'bounds':
                    continue
                att_lst[k] = var_in.getncattr(k)

        var_out.setncatts(att_lst)
        # copy content to new datatype
        if var_name not in ['rotated_latitude_longitude','rotated_pole']:
            var_out[:] = var_in[:]
        logger.info("Variable %s added" % var_name)

# -----------------------------------------------------------------------------
def add_coordinates(f_out,logger=log):
    '''
    Add lat,lon and rotated_pole to output file from coordinates file if present there
    '''
    if os.path.isfile(settings.coordinates_file):
        f_coor = Dataset(settings.coordinates_file,'r')
        try:
            # copy lon
            copy_var(f_coor,f_out,'lon',logger=logger)
            # copy lat
            copy_var(f_coor,f_out,'lat',logger=logger)
            # copy rlon
            copy_var(f_coor,f_out,'rlon',logger=logger)
            # copy rlat
            copy_var(f_coor,f_out,'rlat',logger=logger)
            #copy rotated pole
            copy_var(f_coor,f_out,'rotated_pole',logger=logger)
            copy_var(f_coor,f_out,'rotated_latitude_longitude',logger=logger)

            # commit changes
            f_out.sync()
            f_coor.close()
        except IndexError:
            raise IndexError("\n Coordinates file does not have the same resolution as the input data! Change it!")
    else:
        raise Exception("Coordinates file %s does not exist!" % settings.coordinates_file)

# -----------------------------------------------------------------------------
def get_derotate_vars():
    '''
    Read from variables table all variables that are supposed to be derotated
    '''
    lst = []
    for row in settings.param:
        rotate=settings.param[row][config.get_config_value('index','INDEX_VAR_ROTATE')]
        if rotate.lower() in ['derotate','yes','1']:
            var=settings.param[row][config.get_config_value('index','INDEX_VAR')]
            if not var in lst:
                lst.append(var)
    return lst

# -----------------------------------------------------------------------------
def process_file_fix(params,in_file):
    '''
    Main function for constant variables: process input_file
    '''
    # get cdf variable name

    var = params[config.get_config_value('index','INDEX_VAR')]

    # create object from netcdf file to access all parameters and attributes
    f_in = Dataset(in_file,"r")
    
    for name in f_in.ncattrs():
        if name in settings.global_attr_file: #only take attribute from file if in this list
            settings.Global_attributes[name] = str(f_in.getncattr(name))

    settings.Global_attributes["driving_model_ensemble_member"] = 'r0i0p0'
    
    # out directory
    outdir = get_out_dir(var,'fx')
    # get file name
    outfile = create_filename(var,'fx','','')
    # create complete outpath: outdir + outfile
    outpath = "%s/%s" % (outdir,outfile)
    
    # skip file if exists or overwrite
    if os.path.isfile(outpath):
        log.info("Output file exists: %s" % (outpath))
        if not config.get_config_value('boolean','overwrite'):
            log.info("Skipping...")
            return
        else:
            log.info("Overwriting..")
    log.info("Output to: %s" % (outpath))
    
    f_out = Dataset(outpath,'w')

    # create dimensions in target file
    for name, dimension in f_in.dimensions.items():
        # skip dimension
        if name in settings.varlist_reject or name in ['bnds','time']:
            continue
        else:
            f_out.createDimension(name, len(dimension) if not dimension.isunlimited() else None)

    # set dimension vertices only if set to True in settings file
    if config.get_config_value('boolean','add_vertices') == True:
        f_out.createDimension('vertices',4)

    try:
        mulc_factor = float(params[config.get_config_value('index','INDEX_CONVERT_FACTOR')].strip().replace(',','.'))
    except ValueError:
        log.warning("No conversion factor set in parameter table. Setting it to 1...")
        mulc_factor = 1.0
    if mulc_factor == 0:
        log.warning("Conversion factor is set to 0 in parameter table. Setting it to 1...")
        mulc_factor = 1.0

    if config.get_config_value('boolean','nc_compress') == True:
        log.info("COMPRESS all variables")
    else:
        log.info("NO COMPRESS")
    for var_name, variable in f_in.variables.items():
        mulc_fac = mulc_factor
        if var_name in settings.varlist_reject or var_name == 'time':
            continue
        var_in = f_in.variables[var_name]
        # create output variable
        if var_name in ['rlon','rlat','lon','lat','time']:
            data_type = 'd'
            mulc_fac = 1.0
        elif var_name == 'rotated_pole':
            data_type = 'c'
            mulc_fac = 1.0
        elif var_name in [settings.netCDF_attributes['RCM_NAME_ORG'],settings.netCDF_attributes['RCM_NAME']]:
            data_type = 'f'
        else:
            continue

        dim_lst = []
        for dim in var_in.dimensions:
            if dim != 'time' and dim not in settings.varlist_reject:
                dim_lst.append(dim)
        var_dims = tuple(dim_lst)
        log.debug("Attributes (of variable %s): %s" % (var_name,var_in.ncattrs()))
        
        if var_name in [var,settings.netCDF_attributes['RCM_NAME_ORG'],settings.netCDF_attributes['RCM_NAME']]:
            if config.get_config_value('boolean','nc_compress') == True:
                var_out = f_out.createVariable(var,datatype=data_type,
                    dimensions=var_dims,complevel=4,fill_value=settings.netCDF_attributes['missing_value'])
            else:
                var_out = f_out.createVariable(var,datatype=data_type,
                    dimensions=var_dims,fill_value=settings.netCDF_attributes['missing_value'])

        else:
#
#HJP, Nov 2020 Begin
# there might be mulc_factors different from 1 also for fx-fields, e.g. sftlf that has to be given in %
            #no conversion factor needed
#           mulc_factor = 1.0
#HJP, Nov 2020 END
            if config.get_config_value('boolean','nc_compress') == True:
                var_out = f_out.createVariable(var_name,datatype=data_type,dimensions=var_dims,complevel=4)
            else:
                var_out = f_out.createVariable(var_name,datatype=data_type,dimensions=var_dims)

            change_fill=False
            if var_name in ['lat','lon','rlat','rlon']:
                att_lst = get_attr_list(var_name)
            elif var_name == 'rotated_pole':
                att_lst = get_attr_list(var_name,[var_in.grid_north_pole_latitude,var_in.grid_north_pole_longitude])
            else:
                att_lst = OrderedDict()
                for k in var_in.ncattrs():
                    if config.get_config_value('boolean','add_vertices') == False and k == 'bounds':
                        continue
                    elif k in ["_FillValue","missing_value"]:
                        if var_in.getncattr(k) != settings.netCDF_attributes['missing_value']:
                            #fillvalue or missing_value is incorrect and needs to be changed                            
                            change_fill = True
                        att_lst[k] = settings.netCDF_attributes['missing_value']
                    else:
                        att_lst[k] = var_in.getncattr(k)
            var_out.setncatts(att_lst)

        # copy content to new datatype
        try:
            var_out[:] = mulc_fac * var_in[:]
        except TypeError:
            pass

    # commit changes
    f_out.sync()

    ###################################
    # do some additional settings
    ###################################

    # set all predefined global attributes
    f_out.setncatts(settings.Global_attributes)
    log.info("Global attributes set!")

    # add lon/lat variables if not yet present
    add_coordinates(f_out)

    # commit changes
    f_out.sync()

    # add vertices from extra file if requested in config file 
    if config.get_config_value('boolean','add_vertices') == True:
        add_vertices(f_out)

    f_var = f_out.variables[var]
    # set additional variables attributes
    f_var.standard_name = settings.netCDF_attributes['standard_name']
    f_var.long_name = settings.netCDF_attributes['long_name']
    f_var.units = settings.netCDF_attributes['units']
    #add coordinates attribute to fx-variables
    f_var.coordinates = 'lon lat'

    # set attributes missing_value and grid_mapping
    f_var.missing_value = settings.netCDF_attributes['missing_value']
    f_var.setncattr('grid_mapping','rotated_pole')

    # commit changes
    f_out.sync()

    #close output file
    f_out.close()

    # set attributes: frequency,tracking_id,creation_date
    set_attributes_create(outpath,"fx")
       # change fillvalue in file (not just attribute) if necessary
    if change_fill:
        #use help file as -O option for cdo does not seem to work here
        log.info("Changing missing values to %s" % settings.netCDF_attributes['missing_value'])
        help_file = "%s/help-missing-%s-%s.nc" % (settings.DirWork,var,str(uuid.uuid1()))
        cmd="cdo setmisstoc,%s %s %s" % (settings.netCDF_attributes['missing_value'],outpath,help_file)
        shell(cmd)
        cmd="ncks -h -A -v lon,lat %s %s" % (outpath,help_file)
        shell(cmd)    
        os.remove(outpath)
        shell ("mv %s %s" % (help_file, outpath))
    # ncopy file to correct output format
    if config.get_config_value('boolean','nc_compress') == True:
        compress_output(outpath)

    # close input file
    f_in.close()

# -----------------------------------------------------------------------------
def proc_seasonal(params,year):
    '''
    Create seasonal mean for one variable and one year from daily data
    '''
    if config.get_config_value("integer","multi") > 1:
        logger = logging.getLogger("cmorlight_"+year)
    else:
        logger = logging.getLogger("cmorlight")

    # get cdf variable name
    var = params[config.get_config_value('index','INDEX_VAR')]
    
    # get output directory of daily data: input for seasonal
    indir = get_out_dir(var,"day")
    logger.info("Inputdir: %s" % (indir))

    # seasonal mean
    res = 'sem'
    # get cell method
    cm_type = params[config.get_config_value('index','INDEX_VAR_CM_SEM')]

    logger.info("#########################")
    logger.log(35,"     resolution: '%s'" % res)
    logger.debug("cell method: '%s' " % (cm_type))
    logger.info("#########################")

    #create possible filenames and check their existence -> skip or overwrite file
    outdir = get_out_dir(var,res)
    outfile1 = create_filename(var,res,year+"03",year+"11",logger=logger)
    outpath1 = "%s/%s" % (outdir,outfile1)
    outfile2 = create_filename(var,res,str(int(year)-1)+"12",year+"11",logger=logger)
    outpath2 = "%s/%s" % (outdir,outfile2)

    if os.path.isfile(outpath1) or os.path.isfile(outpath2):
        if os.path.isfile(outpath1):
            logger.info("Output file exists: %s" % (outpath1))
        else:
            logger.info("Output file exists: %s" % (outpath2))

        if not config.get_config_value('boolean','overwrite'):
            logger.info("Skipping...")
            return
        else:
            logger.info("Overwriting..")


    # get files with monthly data from the same input (if exist)
    input_exist=False  #is changed if input file was found
    for dirpath,dirnames,filenames in os.walk(indir):

        if cm_type != '':
            t_delim = 'mean over days'
            if t_delim in cm_type:
                cm = 'mean'
            elif cm_type in ['maximum','minimum']:
                cm = cm[:3]
            else:
                cm = cm_type
            logger.info("Cell method used for cdo command: %s" % (cm))

            f_lst = sorted(filenames)
            i = 0
            for f in f_lst:
                year1=f.split("_")[-1][:4]
                year2=f.split("-")[-1][:4]

                if year1 != year or int(year2)>int(year1)+1: #only process file if the year is correct and if it is not a chunked file
                    i=i+1

                    continue
                else:
                    input_exist=True

                # first a temp file
                ftmp_name = "%s/%s-%s%s" % (settings.DirWork,year,str(uuid.uuid1()),'-help.nc')
                # generate input path
                f = "%s/%s" % (dirpath,f)

                # for season the last month from the previous year is needed
                if i == 0:
                    #for first file: from March to November
                    cmd = "cdo -f %s -seas%s -selmon,3/11 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,f,ftmp_name)
                    try:
                        retval=shell(cmd,logger=logger)
                    except: 
                       logger.warning("Year does probably not contain all months from March to November! Skipping this year...")
                       break  
                else:
                    # get December of previous year
                    f_hlp12 = tempfile.NamedTemporaryFile(dir=settings.DirWork,delete=False,suffix=str(year)+"sem")
                    f_prev = "%s/%s" % (dirpath,f_lst[i-1])

                    cmd = "cdo -f %s selmon,12 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),f_prev,f_hlp12.name)
                    
                    if config.get_config_value("integer","multi") > 1:
                        timepkg.sleep(5) #wait for previous year to definitely finish when using multiprocessing
                          
                    shell(cmd,logger=logger)
                        
                    # get months 1 to 11 of actual year
                    f_hlp1_11 = tempfile.NamedTemporaryFile(dir=settings.DirWork,delete=False,suffix=str(year)+"sem")
                    cmd = "cdo -f %s selmon,1/11 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),f,f_hlp1_11.name)
                    retval = shell(cmd,logger=logger)

                    # now concatenate all 12 montha
                    f_hlp12_11 = tempfile.NamedTemporaryFile(dir=settings.DirWork,delete=False,suffix=str(year)+"sem")
                    cmd = "ncrcat -h -O %s %s %s" % (f_hlp12.name,f_hlp1_11.name,f_hlp12_11.name)
                    retval = shell(cmd,logger=logger)

                    cmd = "cdo -f %s seas%s,3 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,f_hlp12_11.name,ftmp_name)
                    retval = shell(cmd,logger=logger)

                    # remove all temp files
                    os.remove(f_hlp12.name)
                    os.remove(f_hlp1_11.name)
                    os.remove(f_hlp12_11.name)

                # create netcdf4 object from file
                f_tmp = Dataset(ftmp_name,'r+')

                # commit changes
                f_tmp.sync()

                # now copy rotated pole variable to output
                f_in = Dataset(f,'r')

                # variable object
                f_var = f_tmp.variables[var]

                # copy variables from input file if they got lost in cdo commands
                var_in = f_in.variables[var]
                for var_name in ['rlon','rlat','lat','lon','rotated_pole','plev','height']:
                    copy_var(f_in,f_tmp,var_name,logger=logger)
                f_var.setncattr('grid_mapping','rotated_pole')
                f_var.cell_methods = "time: %s" % (cm_type)

                # commit changes
                f_tmp.sync()

                # close input object
                f_in.close()

                # set attribute coordinates
                set_coord_attributes(f_var=f_tmp.variables[var],f_out=f_tmp)
                #Delete unnecessary argument

                # commit changes
                f_tmp.sync()

                # get time variable from input
                time = f_tmp.variables['time']
                time_bnds = f_tmp.variables['time_bnds']
                # get the first time value and convert to date
                dt1 = num2date(time_bnds[0,0],time.units,time.calendar)
                # get the last time value and convert to date
                dt2 = num2date(time_bnds[-1,1]-1,time.units,time.calendar)
                dt_start = str(dt1)[:7].replace("-","")
                dt_stop = str(dt2)[:7].replace("-","")
                
                if config.get_config_value('boolean','add_vertices') == True:
                    add_vertices(f_tmp)
                    
                # close output object
                f_tmp.close()

                # create outpath to store
                outfile = create_filename(var,res,dt_start,dt_stop,logger=logger)
                outpath = "%s/%s" % (outdir,outfile)
                logger.info("Output for seasonal processing: %s" % (outpath))
                # move temp file to output file
                retval = shell("mv %s %s" % (ftmp_name,outpath))
#               retval = shell("cp %s %s" % (ftmp_name,outpath))

                # set attributes
                set_attributes_create(outpath,res,year,logger=logger)
                
#HJP
                help_file = "%s/help-pole_%s.nc" % (outdir,outfile)
                cmd="ncap2 -h -O -s 'rotated_pole=char(rotated_pole)' %s %s" % (outpath,help_file)
                shell(cmd,logger=logger)
                os.remove(outpath)
                shell ("mv %s %s" % (help_file, outpath),logger=logger)
#HJP
                # compress output
                if config.get_config_value('boolean','nc_compress') == True:
                    compress_output(outpath,year,logger=logger)



                # next file index in the list
                i += 1
            if not input_exist:
                logger.warning("Input file (daily resolution) for seasonal processing does not exist. Skipping this year...")
            else:
                break
        else:
            logger.warning("No cell method set for this variable (%s) and time resolution (%s)." % (var,res))

# -----------------------------------------------------------------------------
def derotate_uv(params,in_file,var,logger=log):
    '''
    Derotate input file if this is declared for the variable in the variables table (generally for wind speed variables)
    '''
    logger.info("Derotating file")
    #set environment variable IGNORE_ATT_COORDINATES=1
#HJP Dec 2020 Begin
    if "IGNORE_ATT_COORDINATES" in os.environ:
        envvar = os.getenv('IGNORE_ATT_COORDINATES')
        os.environ["IGNORE_ATT_COORDINATES"] = "1"
    else:
        os.environ["IGNORE_ATT_COORDINATES"] = "1"
        envvar = os.getenv('IGNORE_ATT_COORDINATES')
#HJP Dec 2020 End

    if var not in get_derotate_vars():
        logger.warning("Variable not derotated as this was not declared in parameter table!")
        return

    #assign u and v variables
    filename = in_file.split("/")[-1]
    varRCM = params[config.get_config_value('index','INDEX_RCM_NAME')]
    if var.find("u") == 0:
        in_var_u = varRCM
        in_var_v =  varRCM.replace('U','V')
        filename_u = filename
        filename_v = filename.replace('U','V')

    elif var.find("v") == 0:
        in_var_v = varRCM
        in_var_u =  varRCM.replace('V','U')
        filename_v = filename
        filename_u = filename.replace('V','U')

    else:
        cmd="Error in parameter table. Variable to be derotated starts with neither 'u' nor 'v' !"
        logger.error(cmd)
        raise Exception(cmd)

    #filenames
    in_file_v = "%s/%s/%s" % (settings.DirIn,in_var_v,filename_v)
    in_file_u = "%s/%s/%s" % (settings.DirIn,in_var_u,filename_u)
    if not os.path.isfile(in_file_u) or not os.path.isfile(in_file_v):
        logger.warning("File %s or %s does not exist! Skipping this variable..." % (in_file_u,in_file_v))
        return
    out_dir_u = "%s/%s" % (get_input_path(True),in_var_u)
    out_dir_v = "%s/%s" % (get_input_path(True),in_var_v)
    out_file_u = "%s/%s" % (out_dir_u,filename_u)
    out_file_v = "%s/%s" % (out_dir_v,filename_v)


    # start if output files do NOT exist
    if (not os.path.isfile(out_file_u)) or (not os.path.isfile(out_file_v)) or (config.get_config_value('boolean','overwrite')):
        # make directories
        try:
            os.makedirs(out_dir_u)
            os.makedirs(out_dir_v)
        except:
            pass
    
        start_range = in_file[in_file.rindex('_')+1:in_file.rindex('.')]

        out_file = "%s/UV_%s-%s_%s.nc" % (settings.DirWork,in_var_u,in_var_v,start_range)
        out_file_derotate = "%s/UV_%s-%s_%s_derotate.nc" % (settings.DirWork,in_var_u,in_var_v,start_range)
        if not os.path.isfile(out_file) or config.get_config_value('boolean','overwrite'):
            cmd = "cdo -O merge %s %s %s" % (in_file_u,in_file_v,out_file)
            retval = shell(cmd,logger=logger)

        # only these two have the names as CCLM variable in the file
        try:
            if in_var_u == "U_10M" or in_var_v == "V_10M":
                if not os.path.isfile(out_file_derotate) or config.get_config_value('boolean','overwrite'):
                    cmd = "cdo -O rotuvb,%s,%s %s %s" % (in_var_u,in_var_v,out_file,out_file_derotate)
                    retval = shell(cmd,logger=logger)

                if not os.path.isfile(out_file_u) or config.get_config_value('boolean','overwrite'):
                    cmd = "cdo -O selvar,%s %s %s" % (in_var_u,out_file_derotate,out_file_u)
                    retval = shell(cmd,logger=logger)

                if not os.path.isfile(out_file_v) or config.get_config_value('boolean','overwrite'):
                    cmd = "cdo -O selvar,%s %s %s" % (in_var_v,out_file_derotate,out_file_v)
                    retval = shell(cmd,logger=logger)

            # all other have only U and V inside
            else:
                if not os.path.isfile(out_file_derotate) or config.get_config_value('boolean','overwrite'):
                    cmd = "cdo -O rotuvb,U,V %s %s" % (out_file,out_file_derotate)
                    retval = shell(cmd,logger=logger)
                if not os.path.isfile(out_file_u) or config.get_config_value('boolean','overwrite'):
                    cmd = "cdo -O selvar,U %s %s" % (out_file_derotate,out_file_u)
                    retval = shell(cmd,logger=logger)
                if not os.path.isfile(out_file_v) or config.get_config_value('boolean','overwrite'):
                    cmd = "cdo -O selvar,V %s %s" % (out_file_derotate,out_file_v)
                    retval = shell(cmd,logger=logger)

        except Exception as e:
            cmd=str(e)+"\n Derotation failed. Typing 'export IGNORE_ATT_COORDINATES=1' into your shell before starting the script might solve the problem."
            logger.error(cmd)
            raise Exception(cmd)

        #remove temp files
        if os.path.isfile(out_file):
            os.remove(out_file)
        if os.path.isfile(out_file_derotate):
            os.remove(out_file_derotate)
#HJP Dec 2020 Begin
    #set environment variable IGNORE_ATT_COORDINATES back to its original value or keep 1
    os.environ["IGNORE_ATT_COORDINATES"] = envvar
#HJP Dec 2020 End

    return out_file_u, out_file_v

# -----------------------------------------------------------------------------
def process_file(params,in_file,var,reslist,year,firstlast):
    '''
    Main function for time-dependent variables: process input_file at resolutions defined in reslist
    '''
    #choose logger
    if config.get_config_value("integer","multi") > 1:
        logger = logging.getLogger("cmorlight_"+year)
    else:
        logger = logging.getLogger("cmorlight")

    #derotate if required
    if var in get_derotate_vars() and config.get_config_value('boolean','derotate_uv'):
        in_file_u, in_file_v = derotate_uv(params,in_file,var,logger)
        #change input file
        if var.find("u") != -1:
            in_file = in_file_u
        else:
            in_file = in_file_v
        logger.info("Changed input file to derotated file: %s" % in_file)

    if config.get_config_value('boolean','use_alt_units'): #if units attribute is wrong -> take from config file
        temp_name = "%s/%s-%s-%s.nc" % (settings.DirWork,year,str(uuid.uuid1()),var)
        cmd = 'ncatted -a units,time,o,c,"%s" %s %s' % (config.get_config_value("settings","alt_units"),in_file,temp_name)
        logger.info("Changing units attribute of input")
        shell(cmd,logger=logger)
        in_file = temp_name
 
   # create object from netcdf file to access all parameters and attributes
    f_in = Dataset(in_file,"r")
    
    for name in f_in.ncattrs():
        if name in settings.global_attr_file: #only take attribute from file if in this list
            settings.Global_attributes[name] = str(f_in.getncattr(name))


    # get time variable from input
    time_in = f_in.variables['time']
     
    # if 'calendar' in time_in.ncattrs():
    in_calendar = str(time_in.calendar)
    #else:
     #   in_calendar = config.get_sim_value("calendar",exitprog = False)
      #  if in_calendar=="":
       #     raise Exception("Calendar attribute not found in input file! Specify calendar in simulation settings section of configuration file instead!")
  
    time_in_units = time_in.units

    # now get the 'new' time/date
    #MED>>dt_in = num2date(time_in[:],time_in_units,calendar=in_calendar)
    if in_calendar in ['standard','gregorian','proleptic_gregorian','julian']:
       dt_in = num2date(time_in[:],time_in_units,calendar=in_calendar)
    else:
       dt_in = num2date(time_in[:]+1.e-6,time_in_units,calendar=in_calendar) #to prevent roundoff error due to lack of precision
    #MED<<

    # calculate time difference between first two time steps (in hours)
    a = datetime.datetime.strptime(str(dt_in[0]), settings.FMT)
    b = datetime.datetime.strptime(str(dt_in[1]), settings.FMT)
    
    time_delta_raw = np.array(time_in)[1]-np.array(time_in)[0]
    time_delta = b-a
    #input time resolution in hours
    input_res_hr = time_delta.total_seconds() / 3600. 

    logger.info("First time step in input file: %s" % (str(a)))
    if input_res_hr not in [1.,3.,6.,12.,24]:
        cmd = "Time resolution of input data must be 1,3,6,12 or 24 hours, found %s hours!" % (input_res_hr)
        logger.error(cmd)
        raise(cmd) 
        
    logger.debug("Input data time interval: %shourly" % (str(input_res_hr)))
  
    #check if time variable is correct
  
    #correct start and end date for averaged and instantaneous variables
    start_date =  num2date(0,"seconds since {}-{:02d}-01".format(int(year),firstlast[0]),calendar=in_calendar)
    endyear = int(year)
    if firstlast[1]==12:
        endyear += 1
        endmonth = 1
    else:
        endmonth = firstlast[1]+1
        
    end_date = num2date(0,"seconds since {}-{:02d}-01".format(endyear,endmonth),calendar=in_calendar)
    if params[config.get_config_value('index','INDEX_FRE_AGG')] == 'i':
        end_date -= time_delta
    else:
        start_date += datetime.timedelta(seconds=time_delta.total_seconds()/2) 
        end_date -= datetime.timedelta(seconds=time_delta.total_seconds()/2)     
    #convert to numbers
    start_num = date2num(start_date,time_in_units,calendar=in_calendar)   
    end_num = date2num(end_date, time_in_units, calendar=in_calendar)   
    #correct time array
    time_range = np.round(np.arange(start_num ,end_num+time_delta_raw/2, time_delta_raw),5)
    time_in_arr=np.round(np.array(time_in),5)
    if not (set(time_range) <=  set(time_in_arr)):
        cmd = "Time variable of input data is not correct! It has to contain all required time steps between January 1st and \
December 30th/31st (depending on calendar) of the respective year. The first time step for \
instantaneous and interval representing variables must be 0 UTC and (resolution * 0.5) UTC, respectively. \
The last time step must be (24 - resolution) UTC and (24 - resolution * 0.5) UTC, respectively. 'resolution' \
is here the time resolution of the input data in hours."
        logger.error(cmd)
        raise Exception(cmd) 
    #Define time steps which to take from input
    start_in,end_in = np.where(time_in_arr==time_range[0])[0][0], np.where(time_in_arr==time_range[-1])[0][0]
    tsteps = "%s/%s" %(start_in+1,end_in+1)
    
    #change time array
    dt_in = dt_in[start_in:end_in+1]
    time_in = time_in[start_in:end_in+1]

    # start date for file names
    dt_start_in = str(dt_in[0])
    dt_start_in = dt_start_in[:dt_start_in.index(' ')].replace('-','')

    # stop date for file names
    dt_stop_in = str(dt_in[-1])
    dt_stop_in = dt_stop_in[:dt_stop_in.index(' ')].replace('-','')

    ## AD, RP Sept 2022 Begin (CORDEX-CMIP6 adaptations)
    # for mrsol and mrsfl: provide an extraction of layers in a 3D field -> done later due to running time
    # for mrso and mrfso: sum up all soil layers which are hydrologically active (control those by variables table)
    if var in ['mrso','mrfso']:
        f_in.close()

        # use start soil layer 1 
        idx_from = 1
        # take stop soil layer from table
        idx_to = int(params[config.get_config_value('index','INDEX_VAL_LEV')].strip())

        f_hlp = tempfile.NamedTemporaryFile(dir=settings.DirWork,delete=False,suffix=year)
#AD Version retval = shell("cdo -f %s vertsum %s %s" %(config.get_config_value('settings', 'cdo_nctype'),in_file,f_hlp.name),logger=logger)
        #Ronny Version:
        retval = shell("cdo -f %s vertsum -sellevidx,%d/%d %s %s" %(config.get_config_value('settings', 'cdo_nctype'),idx_from,idx_to,in_file,f_hlp.name),logger=logger)

        # switch from original in_file to the new in_file
        in_file = f_hlp.name
        f_in = Dataset(in_file,"r")

    # for mrsos and mrfsos: sum up top 10 cm (number of layers defined in variables table)
    if var in ['mrsos','mrfsos']:
        f_in.close()

        # use start soil layer 1 
        idx_from = 1
        # take stop soil layer from table
        idx_to = int(params[config.get_config_value('index','INDEX_VAL_LEV')].strip())

        f_hlp = tempfile.NamedTemporaryFile(dir=settings.DirWork,delete=False,suffix=year)
        retval = shell("cdo -f %s vertsum -sellevidx,%d/%d %s %s" %(config.get_config_value('settings', 'cdo_nctype'),idx_from,idx_to,in_file,f_hlp.name),logger=logger)
            
        # switch from original in_file to the new in_file
        in_file = f_hlp.name
        f_in = Dataset(in_file,"r")

    # for mrsol and mrsfl: store the range from the variable definition table
    if var in ['mrsol','mrsfl']:
        # use start soil layer 1 
        idx_soillev_from = 1
        # take stop soil layer from table
        idx_soillev_to = int(params[config.get_config_value('index','INDEX_VAL_LEV')].strip())
    ##
    ## AD, RP sept 2022 End

    new_reslist=list(reslist) #remove resolutions from this list that are higher than the input data resolution
    # process all requested resolutions
    
    for res in reslist:
        #MED>> add additional subdaily resolution
        #if res in ["1hr","3hr","6hr","12hr"]:
        #    res_hr = float(res[:-2]) #extract time resolution in hours
        #    cm_type = params[config.get_config_value('index','INDEX_VAR_CM_SUB')]
        if res in ["1hr","3hr","6hr","12hr"]:
            res_hr = float(res[:-2]) #extract time resolution in hours
            freq=24./res_hr
            freq_table=params[config.get_config_value('index','INDEX_FRE_ASU')]
            cm_type = params[config.get_config_value('index','INDEX_VAR_CM_ASU')]
            if (cm_type=="" or float(freq_table) != freq):
                cm_type = params[config.get_config_value('index','INDEX_VAR_CM_SUB')]
        #MED<<
        elif res=="day":
            res_hr=24.
            cm_type = params[config.get_config_value('index','INDEX_VAR_CM_DAY')]
        elif res=="mon":
            res_hr= 28*24.  #minimum number of hours per month
            cm_type = params[config.get_config_value('index','INDEX_VAR_CM_MON')]

        #check if requested time resolution is possible given the input time resolution
        if res_hr < input_res_hr:
            logger.warning("Requested time resolution (%s) is higher than time resolution of input data (%s hr). Skip this resolution for all following files.." % (res,input_res_hr))
            new_reslist.remove(res)
            continue

        # process only if cell method is defined in input matrix
        if cm_type == '':
            cmd = "No cell method set for this variable (%s) and time resolution (%s)." % (var,res)
            logger.warning(cmd)
            # close input file and return
            f_in.close()
            return new_reslist
            
        logger.info("#########################")
        logger.log(35,"     resolution: '%s'" % res)
        logger.debug("cell method: '%s' " % (cm_type))
        logger.info("#########################")

        # output directory
        outdir = get_out_dir(var,res)

        # get file name
        outfile = create_filename(var,res,dt_start_in,dt_stop_in,logger=logger)
        
        # create complete outpath: outdir + outfile
        outpath = "%s/%s" % (outdir,outfile)
        
        # skip file if exist
        if os.path.isfile(outpath):
            logger.info("Output file exists: %s" % (outpath))
            if not config.get_config_value('boolean','overwrite'):
                logger.info("Skipping...")
                continue
            else:
                logger.info("Overwriting..")
        logger.debug("Output to: %s" % (outpath))

# HJP Feb 2020 Begin of change
#  Note: the conversion factors possibly defined in the CSV-table must not be divided by the time resolution of the input data
#        the correct value for this factor, if it is needed, is in the responsibility of the user
#        therefore, the follwing lines are commented out
        #conversion factor
#       conv_factor = params[config.get_config_value('index','INDEX_CONVERT_FACTOR')].strip().replace(',','.')
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
# HJP Feb 2020 End   of change

        ftmp_name = "%s/%s-%s-%s.nc" % (settings.DirWork,year,str(uuid.uuid1()),var)

        # get type of cell method to create the output file: point,mean,maximum,minimum,sum
        cm = cm_type
        
        #for monthly resolution: determine cell method within days time
        if res == 'mon' and 'within days time' in cm_type:
            cm = cm[:cm.find(" ")]
        
        #Change cm to max/min
        if cm in ['maximum','minimum']:
            cm = cm[:3]
        
        if res_hr < 24:
            selhour = str(list(np.arange(0,24,int(res_hr))))[1:-1].replace(" ","")
            nstep = res_hr / input_res_hr
            if cm == 'point':
                cmd = "cdo -L -f %s -s -selhour,%s -seltimestep,%s %s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),selhour,tsteps,cmd_mul,in_file,ftmp_name)
            else:
                cmd = "cdo -L -f %s -s -timsel%s,%s -seltimestep,%s %s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,int(nstep),tsteps,cmd_mul,in_file,ftmp_name)
        
        # For monthly resolution daily processing is sometimes necessary first
        elif res == 'day' or 'within days time' in cm_type:
            cmd = "cdo -L -f %s -s day%s -seltimestep,%s %s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,tsteps,cmd_mul,in_file,ftmp_name)
        
        #monthy resolution
        else:
            cmd = "cdo -L -f %s -s -mon%s -seltimestep,%s %s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,tsteps,cmd_mul,in_file,ftmp_name)

        retval = shell(cmd,logger=logger)
        
        #now do mean over days for each month
        if 'within days time' in cm_type:
            ftmp_name2 = "%s/%s-%s-%s.nc" % (settings.DirWork,year,str(uuid.uuid1()),var)
            cmd = "cdo -f %s -s -monmean -seltimestep,%s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),tsteps,ftmp_name,ftmp_name2)
            retval = shell(cmd,logger=logger)
            ftmp_name = ftmp_name2
            
        ####################################################
        # open output file
        ####################################################

        # open ftmp_name for reading
        f_tmp = Dataset(ftmp_name,'r')

        # create object for output file
        f_out = Dataset(outpath,'w')

        # create dimensions in target file
        # RP adopt to the needs of additional dimensions in case of mrsol and mrsfl
        for name, dimension in f_tmp.dimensions.items():
            # skip some dimensions (be aware of W_SO and soil1)
            if (name not in settings.varlist_reject): 
                f_out.createDimension(name, len(dimension) if not dimension.isunlimited() else None)
            elif ( var in ['mrsol','mrsfl'] and name == 'soil1' ):
                f_out.createDimension(name, idx_soillev_to-idx_soillev_from+1)
            else:
                continue
        # END RP

        # set dimension vertices only if set to True in settings file
        if config.get_config_value('boolean','add_vertices') == True:
            f_out.createDimension('vertices',4)
            logger.info("Add vertices")
        # copy variables from temp file
        for var_name in f_tmp.variables.keys():

            if var_name in ['rlon','rlat','lon','lat','time']:
                data_type = 'd'
            elif var_name == 'rotated_pole':
                data_type = 'c'
            elif var_name in [settings.netCDF_attributes['RCM_NAME_ORG'],settings.netCDF_attributes['RCM_NAME']]:
                data_type = 'f'
            else:
                continue
                
            var_in = f_tmp.variables[var_name]

            if config.get_config_value('boolean','nc_compress') == True:
                logger.debug("COMPRESS variable: %s" % (var_name))

            # RP adopt to the needs of additional dimensions in case of mrsol and mrsfl
            dim_lst = []
            for dim in var_in.dimensions:
                if (str(dim) not in settings.varlist_reject) or (var in ['mrsol','mrsfl'] and str(dim) == 'soil1'):
                    dim_lst.append(dim)
            # END RP
            var_dims = tuple(dim_lst)
            logger.debug("Dimensions (of variable %s): %s" % (var_name,str(var_dims)))
            logger.debug("Attributes (of variable %s): %s" % (var_name,var_in.ncattrs()))

            if var_name in [settings.netCDF_attributes['RCM_NAME_ORG'],settings.netCDF_attributes['RCM_NAME']]:
                if config.get_config_value('boolean','nc_compress') == True:
                    var_out = f_out.createVariable(var,datatype=data_type,
                        dimensions=var_dims,complevel=4,fill_value=settings.netCDF_attributes['missing_value'])
                else:
                    var_out = f_out.createVariable(var,datatype=data_type,
                        dimensions=var_dims,fill_value=settings.netCDF_attributes['missing_value'])
            else:
                if config.get_config_value('boolean','nc_compress') == True:
                    var_out = f_out.createVariable(var_name,datatype=data_type,dimensions=var_dims,complevel=4)
                else:
                    var_out = f_out.createVariable(var_name,datatype=data_type,dimensions=var_dims)
            
            # create attribute list
            change_fill=False
            if var_name in ['lat','lon','rlon','rlat','time']:
                att_lst = get_attr_list(var_name,[time_in_units,in_calendar])
            elif var_name == 'rotated_pole':
                att_lst = get_attr_list(var_name,[var_in.grid_north_pole_latitude,var_in.grid_north_pole_longitude])
            else:
                att_lst = OrderedDict()
                for k in var_in.ncattrs():
                    if k in ["_FillValue","missing_value"]:
                        if var_in.getncattr(k) != settings.netCDF_attributes['missing_value']:
                            #fillvalue or missing_value is incorrect and needs to be changed                            
                            change_fill = True
                        att_lst[k] = settings.netCDF_attributes['missing_value']
                    else:
                        att_lst[k] = var_in.getncattr(k)
            var_out.setncatts(att_lst)

            # copy content to new datatype
            logger.debug("Copy data from tmp file: %s" % (var_out.name))
            if var_name not in ['rotated_latitude_longitude','rotated_pole']:
                if var_out.name in ['mrsol','mrsfl']:
                    ##asumes the soil-dimension to be on second place
                    var_out[:] = var_in[:,(idx_soillev_from-1):idx_soillev_to,:,:] 
                else:
                    var_out[:] = var_in[:]


        # copy lon/lat and rlon/rlat from input if needed:
        for var_name in f_in.variables.keys():
            if (var_name in ['lon','lat','rlon','rlat','rotated_pole'] and var_name not in f_out.variables.keys() ):
                var_in = f_in.variables[var_name]
                j = 0
                for var_dim in var_in.dimensions:
                    if var_dim not in f_out.dimensions:
                        f_out.createDimension(var_dim,size=var_in.shape[j])
                    j = j + 1

                # create output variable
                var_out = f_out.createVariable(var_name,datatype="d",dimensions=var_in.dimensions)
                # create attribute list
                if var_name in ['lat','lon','rlat','rlon']:
                    att_lst = get_attr_list(var_name)
                elif var_name == 'rotated_pole':
                    att_lst = get_attr_list(var_name,[var_in.grid_north_pole_latitude,var_in.grid_north_pole_longitude])
              
                var_out.setncatts(att_lst)
                # copy content to new datatype
                if var_name not in ['rotated_latitude_longitude','rotated_pole']:
                    var_out[:] = var_in[:]

                logger.debug("Copy from input: %s" % (var_out.name))

        ##############################
        # now correct time,time_bnds #
        ##############################
        # get time variable from output
        time = f_out.variables['time']
        # create time_bnds for averaged variables
        if ( cm != 'point' ):
            f_out.createDimension('bnds',size=2)
            time_bnds = f_out.createVariable('time_bnds',datatype="d",dimensions=('time','bnds'))
            time.bounds = 'time_bnds'
        #get start date: first time value for inst. input, first lower time bound for averaged input
        if params[config.get_config_value('index','INDEX_FRE_AGG')] == 'a':
            date_start = dt_in[0]-datetime.timedelta(hours=input_res_hr*0.5)
        else:
            date_start = dt_in[0]        
            
        # get length of data array
        data_len = f_out.variables[var].shape[0]
     
        # move the reference date to the one given in the config file (for CORDEX: 1949-12-01T00:00:00Z)
        time.units = config.get_config_value('settings','units')
        
        # the first time step (or first lower time bound) as numeric value in the desired time units
        num_date_start = date2num(date_start,time.units,calendar=in_calendar)
        
        if res_hr <= 24:
            # reference date
            refdate = num2date(0,time.units,calendar=in_calendar)
        
            #output time resolution measured in the time units from the config file       
            res_units = date2num(refdate + datetime.timedelta(hours=res_hr),time.units,calendar=in_calendar)
        
            # set time and time_bnds
            if cm != 'point':
                for n in range(data_len):
                    time_bnds[n,0] = num_date_start + (n * res_units)
                    time_bnds[n,1] = num_date_start + ((n + 1) * res_units)
                    time[n] = (time_bnds[n,0] + time_bnds[n,1]) / 2.0
            else:
                # set time
                for n in range(data_len):
                    time[n] = num_date_start + n * res_units

        elif res == 'mon':
            y = int(year)
            for num,n in enumerate(np.arange(firstlast[0],firstlast[1]+1)):
                time_bnds[num,0] = date2num(datetime.datetime(y,n,1),time.units,calendar=in_calendar)
                m = n+1
                #For December: end date is 1st January the following year                
                if n == 12:
                    y += 1
                    m = 1
                time_bnds[num,1] = date2num(datetime.datetime(y,m,1),time.units,calendar=in_calendar)
                time[num] = (time_bnds[num,0] + time_bnds[num,1]) / 2.0

        # commit changes
        f_out.sync()

        #from IPython import embed
        #embed()
        ###################################
        # do some additional settings
        ###################################

        # set all predefined global attributes
        if settings.Global_attributes=={}:
            logger.error("List of global attributes is empty!")
        else:
            f_out.setncatts(settings.Global_attributes)
            logger.info("Global attributes set!")

        # commit changes
        f_out.sync()

        # add vertices from extra file if requested in config file 
        if config.get_config_value('boolean','add_vertices') == True:
            add_vertices(f_out,logger=logger)

        # create variable object to output file
        f_var = f_out.variables[var]
        # set additional variables attributes
        f_var.standard_name = settings.netCDF_attributes['standard_name']
        f_var.long_name = settings.netCDF_attributes['long_name']
        f_var.units = settings.netCDF_attributes['units']
        f_var.cell_methods = "time: %s" % (cm_type)

        #HJP Mar 2019 Begin
        #include variable's attribute "comment" if the corresponding entry in the ini-file is not empty
        comment = params[config.get_config_value('index','INDEX_VAR_COMMENT')]
        if comment !='':
            settings.netCDF_attributes['comment'] = params[config.get_config_value('index','INDEX_VAR_COMMENT')]
            f_var.comment = settings.netCDF_attributes['comment']
        else:
            logger.info("No comment attribute")
        #HJP Mar 2019 End

        #create pressure/height variables for variables which are not at the surface
        if (int(params[config.get_config_value('index','INDEX_VAL_LEV')].strip()) > 0) and \
            (var not in ['mrsos','mrfsos','mrso','mrfso']):
            if params[config.get_config_value('index','INDEX_MODEL_LEVEL')] == config.get_config_value('settings','PModelType'):
                if not 'plev' in f_out.variables:
                    var_out = f_out.createVariable('plev',datatype='d')
                    var_out.units = "Pa"
                    var_out.axis = "Z"
                    var_out.positive = "down"
                    var_out.long_name = "pressure"
                    var_out.standard_name = "air_pressure"
                    var_out[0] = params[config.get_config_value('index','INDEX_VAL_PLEV')]
                    coordinates = 'plev lat lon'

            #model level variable
            elif params[config.get_config_value('index','INDEX_MODEL_LEVEL')] == config.get_config_value('settings','MModelType'):
                if not 'height' in f_out.variables:
                    var_out = f_out.createVariable('height',datatype='d')
                    var_out.units = "m"
                    var_out.axis = "Z"
                    var_out.positive = "up"
                    var_out.long_name = "height"
                    var_out.standard_name = "height"
                    var_out[0] = params[config.get_config_value('index','INDEX_VAL_HEIGHT')]
                    coordinates = 'height lat lon'
	    #HJP Mar 2019 Begin
            # z-level variable
            elif params[config.get_config_value('index','INDEX_MODEL_LEVEL')] == config.get_config_value('settings','ZModelType'):
                if not 'height' in f_out.variables:
                    var_out = f_out.createVariable('height',datatype='d')
                    var_out.units = "m"
                    var_out.axis = "Z"
                    var_out.positive = "up"
                    var_out.long_name = "height"
                    var_out.standard_name = "height"
                    var_out[0] = params[config.get_config_value('index','INDEX_VAL_HEIGHT')]
                    coordinates = 'height lat lon'
            else:
                logger.warning("Column %s (Level) should be either %s or %s or %s! Got %s." % (config.get_config_value('index','INDEX_MODEL_LEVEL'),config.get_config_value('settings','PModelType'),config.get_config_value('settings','MModelType'),config.get_config_value('settings','ZModelType'),params[config.get_config_value('index','INDEX_MODEL_LEVEL')]))
            #HJP Mar 2019 End
        else:
            coordinates = 'lat lon'

        # AD, RP Sept 2022 Begin (CORDEX-CMIP6 adaptations)
        # copy soil depth variable for mrsol and mrsfl
        if var in ['mrsol','mrsfl']:
            if ( not 'soil1' in f_out.variables ) and ( not 'soil1_bnds' in f_out.variables ):
                soil_in = f_in.variables['soil1']
                soilbnds_in = f_in.variables['soil1_bnds']
                ## create an additional dimension to handle soil_bnds 
                f_out.createDimension('dim_sbounds', 2)
                # create soil1 variable and attributes
                var_outs = f_out.createVariable('soil1',datatype="f",dimensions='soil1')
                var_outsbnd = f_out.createVariable('soil1_bnds',datatype="f",dimensions=('soil1','dim_sbounds'))
                var_outs.units = "m"
                var_outsbnd.units = "m"
                var_outs.axis = "Z"
                var_outs.positive = "down"
                var_outs.long_name = "depth of soil layers"
                var_outsbnd.long_name = "boundaries of soil layers"
                var_outs.standard_name = "depth"
                var_outs.bounds = "soil1_bnds"
                # copy soil values
                var_outs[:] = soil_in[(idx_soillev_from-1):idx_soillev_to]
                var_outsbnd[:] = soilbnds_in[(idx_soillev_from-1):idx_soillev_to,:] ##assuming that the first dimension is soil1
                coordinates = 'lat lon'
                logger.debug("Copy from input: %s" % (var_out.name))
        # AD, RP sept 2022 End
        
        
        f_var.coordinates = coordinates
        
        # copy variables lon,lat,rlon,rlat,rotated_pole from extra file if needed
        add_coordinates(f_out,logger=logger)

        #TODO: what to do with this function?
        # set attribute coordinates
        # set_coord_attributes(f_var,f_out)

        # set attribute missing_value
        f_var.missing_value = settings.netCDF_attributes['missing_value']
        
        f_var.setncattr('grid_mapping','rotated_pole')

       # commit changes
        f_out.sync()
	
        f_out.close()

        # remove help file
        os.remove(ftmp_name)


       # change fillvalue in file (not just attribute) if necessary
        if change_fill:
            #use help file as -O option for cdo does not seem to work here
            logger.info("Changing missing values to %s" % settings.netCDF_attributes['missing_value'])
            help_file = "%s/help-missing-%s-%s-%s.nc" % (settings.DirWork,year,var,str(uuid.uuid1()))
            cmd="cdo setmisstoc,%s %s %s" % (settings.netCDF_attributes['missing_value'],outpath,help_file)
            shell(cmd,logger=logger)
            #add lon,lat,height,plev coordinates as they got lost by cdo command
            add_vars='lon,lat'
            if 'height' in coordinates:
                add_vars += ',height'
            elif 'plev' in coordinates:
                add_vars += ',plev'
            cmd="ncks -h -A -v %s %s %s" % (add_vars,outpath,help_file)
            shell(cmd,logger=logger)    
            
            os.remove(outpath)
            shell ("mv %s %s" % (help_file, outpath),logger=logger)
            #add coordinates attribute
            cmd="ncatted -a coordinates,%s,o,c,'%s' %s" % (var,coordinates,outpath)
            shell(cmd,logger=logger)    

#HJP
        help_file = "%s/help-pole-%s-%s-%s.nc" % (settings.DirWork,year,var,str(uuid.uuid1()))
        cmd="ncap2 -h -O -s 'rotated_pole=char(rotated_pole)' %s %s" % (outpath,help_file)
        shell(cmd,logger=logger)
        os.remove(outpath)
        shell ("mv %s %s" % (help_file, outpath),logger=logger)
#HJP


        # ncopy file to correct output format
        if config.get_config_value('boolean','nc_compress') == True:
            compress_output(outpath,year,logger=logger)
        
        # set global attributes: frequency,tracking_id,creation_date
        set_attributes_create(outpath,res,year,logger=logger)
    
    # delete help file
    if var in ['mrsos','mrfsos','mrso','mrfso'] and os.path.isfile(f_hlp.name):
        os.remove(f_hlp.name)

    if config.get_config_value('boolean','use_alt_units'): 
        os.remove(temp_name)
    # close input file
    f_in.close()
    
    #return updated reslist
    return new_reslist

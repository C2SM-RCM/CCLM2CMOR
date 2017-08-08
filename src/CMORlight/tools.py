# tools.py

# default
import os
import sys

import numpy as np
# netcdf4 Library
from netCDF4 import Dataset
from netCDF4 import num2date
from netCDF4 import date2num

# sub process library
import subprocess

# configuration
import configuration as config

# global variables
import settings

from datetime import datetime
#from datetime import timedelta

# uuid support
import uuid

# support logging
import logging
log = logging.getLogger('cmorlight')



# -----------------------------------------------------------------------------
def test_log():
    '''
    for logging test only
    '''
    log.info("something")
    print("something")


# -----------------------------------------------------------------------------
def shell(cmd):
    '''
    this helper will call a shell command
    '''
    log.info("Command: '%s'" % cmd)
    prc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    prc.wait()
    if prc.returncode != 0:
        raise Exception('Shell Error: %s' % prc.communicate()[0])
    return prc.communicate()[0]


# -----------------------------------------------------------------------------
# get list of variables to rotate
def get_input_path(var):
    ''' '''
    var_list_rotated = get_derotate_vars(flt=None)
    if var in var_list_rotated:
        retVal = settings.DirOutRotated
    else:

        retVal = settings.DirIn
    return retVal

# -----------------------------------------------------------------------------
def get_var_lists(flt=None):
    '''
    INDEX_VAR_ROTATE
    '''
    lst = []
    for row in sorted(settings.param):
        if settings.param[row][config.get_config_value('index','INDEX_RCM_NAME_ORG')] != '' and settings.param[row][config.get_config_value('index','INDEX_VAR')] != '':
            lst.append(row)
    return sorted(lst)


# -----------------------------------------------------------------------------
# set global attributes
def set_attributes(params,proc_list=None):
    '''
    fill dictionary with global attributes
    fill dictionary with additional netcdf attributes

    '''
    # get attributes for actual model: CCLM or WRF
    for name in settings.global_attr_list :
        if config.get_model_value(name.strip()) != '':
            settings.Global_attributes[name.strip()] = config.get_model_value(name.strip())
    if proc_list:
        settings.Global_attributes['driving_model_id'] = proc_list[0]
        settings.Global_attributes['driving_experiment_name'] = proc_list[1]
        settings.Global_attributes['experiment_id'] = proc_list[1]
        settings.Global_attributes['experiment'] = proc_list[1]
        settings.Global_attributes['driving_model_ensemble_member'] = proc_list[2]
        settings.Global_attributes['driving_experiment'] = "%s, %s, %s" % (proc_list[0],proc_list[1],proc_list[2])

    settings.Global_attributes['title'] = "%s %s" % (settings.Global_attributes['title'],proc_list[1])

    #Invariant attributes
    settings.Global_attributes['project_id']="CORDEX"
    settings.Global_attributes['product']="output"

    # set policy for DWD, to add set add_policy to 'True' in control_cmor.ini
    if config.get_config_value('settings', 'add_policy'):
        settings.Global_attributes['data_policy'] = config.get_model_value('policy')

    # set addtitional netcdf attributes
    settings.netCDF_attributes['RCM_NAME'] = params[0]
    settings.netCDF_attributes['RCM_NAME_ORG'] = params[1]
    settings.netCDF_attributes['cf_name'] = params[config.get_config_value('index','INDEX_VAR')]
    settings.netCDF_attributes['long_name'] = params[config.get_config_value('index','INDEX_VAR_LONG_NAME')]
    settings.netCDF_attributes['standard_name'] = params[config.get_config_value('index','INDEX_VAR_STD_NAME')]
    settings.netCDF_attributes['units'] = params[config.get_config_value('index','INDEX_UNIT')]
    settings.netCDF_attributes['missing_value'] = config.get_config_value('settings','missing_value')
    settings.netCDF_attributes['_FillValue'] = config.get_config_value('settings','missing_value')



# -----------------------------------------------------------------------------
def create_outpath(res,var):
    '''
    Create the output path from all Global attributes
    needed to confirm the CORDEX DSR
    '''
    #global use_version
    result = ""
    # Global_attributes:
    # project_id=CORDEX
    # CORDEX_domain=EUR-11
    # institute_id=CLMcom
    # driving_model_id=ECMWF-ERAINT
    # driving_experiment_name=evaluation
    # experiment_id=evaluation
    # driving_model_ensemble_member=r1i1p1
    # model_id=CLMcom-CCLM4-8-17
    # source=CLMcom-CCLM4-8-17
    # rcm_version_id=v1
    # modeling_realm=atmos
    # product=output
    # cordex/output/EUR-11/CLMcom/MPI-M-MPI-ESM-LR/historical/r1i1p1/CLMcom-CCLM4-8-17/v1/day/zg500/v20140515/
    #global Global_attributes
    #print Global_attributes
    if res == 'fx':
        # cordex/output/EUR-11/CLMcom/MIROC-MIROC5/historical/r1i1p1/r0i0p0/v1/fx/orog/v20170227
        result = "%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s" % \
                    (settings.Global_attributes["project_id"],
                     settings.Global_attributes["product"],
                     settings.Global_attributes["CORDEX_domain"],
                     settings.Global_attributes["institute_id"],
                     settings.Global_attributes["driving_model_id"],
                     settings.Global_attributes["experiment_id"],
                     settings.Global_attributes["driving_model_ensemble_member"],
                     settings.Global_attributes["model_id"],
                     settings.Global_attributes["rcm_version_id"],
                     res,
                     var,
                     settings.use_version
                    )
    else:
        result = "%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s" % \
                    (settings.Global_attributes["project_id"],
                     settings.Global_attributes["product"],
                     settings.Global_attributes["CORDEX_domain"],
                     settings.Global_attributes["institute_id"],
                     settings.Global_attributes["driving_model_id"],
                     settings.Global_attributes["experiment_id"],
                     settings.Global_attributes["driving_model_ensemble_member"],
                     settings.Global_attributes["model_id"],
                     settings.Global_attributes["rcm_version_id"],
                     res,
                     var,
                     settings.use_version
                    )
    return result


# -----------------------------------------------------------------------------
def create_filename(var,res,dt_start,dt_stop):
    ''' '''
    # 3hr file: pr_EUR-11_ECMWF-ERAINT_evaluation_r1i1p1_CLMcom-CCLM4-8-17_v1_3hr_198901010130-199012312230.nc
    # 6hr file: vas_EUR-11_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_6hr_       2003010100-2003123118.nc
    # 6hr file: pr_EUR-11_ECMWF-ERAINT_evaluation_r1i1p1_CLMcom-CCLM4-8-17_v1_6hr_1989010100-1990123118.nc
    # day file: pr_EUR-11_ECMWF-ERAINT_evaluation_r1i1p1_CLMcom-CCLM4-8-17_v1_day_19890101-19901231.nc
    # mon file: pr_EUR-11_ECMWF-ERAINT_evaluation_r1i1p1_CLMcom-CCLM4-8-17_v1_mon_198901-199012.nc
    # sem file: pr_EUR-11_ECMWF-ERAINT_evaluation_r1i1p1_CLMcom-CCLM4-8-17_v1_sem_198904-199010.nc

    # cut off the day in time range
    # TODO workaround: add times in case of 3hr and 6hr (better_ get from real time value)
    if res == "3hr":
        dt_start = "%s%s" % (dt_start,'0000')
        dt_stop = "%s%s" % (dt_stop,'2100')
    elif res == "6hr":
        dt_start = "%s%s" % (dt_start,'00')
        dt_stop = "%s%s" % (dt_stop,'18')
    elif res == "day":
        dt_start = dt_start[:8]
        dt_stop = dt_stop[:8]
    elif res in ["mon","sem"]:
        dt_start = dt_start[:6]
        dt_stop = dt_stop[:6]
    elif res == 'fx':
        result = "%s_%s_%s_%s_%s_%s_%s_%s.nc" % (var,
                        settings.Global_attributes["CORDEX_domain"],
                        settings.Global_attributes["driving_model_id"],
                        settings.Global_attributes["experiment_id"],
                        settings.Global_attributes["driving_model_ensemble_member"],
                        settings.Global_attributes["model_id"],
                        settings.Global_attributes["rcm_version_id"],
                        res
                    )
        return result

    log.info("Filename start/stop: %s, %s" % (dt_start,dt_stop))

    result = ""
    # zg500_EUR-11_MPI-M-MPI-ESM-LR_historical_r1i1p1_CLMcom-CCLM4-8-17_v1_day_19510101-19551231.nc
    result = "%s_%s_%s_%s_%s_%s_%s_%s_%s-%s.nc" % (var,
                    settings.Global_attributes["CORDEX_domain"],
                    settings.Global_attributes["driving_model_id"],
                    settings.Global_attributes["experiment_id"],
                    settings.Global_attributes["driving_model_ensemble_member"],
                    settings.Global_attributes["model_id"],
                    settings.Global_attributes["rcm_version_id"],
                    res,
                    dt_start,
                    dt_stop
                )
    return result


# -----------------------------------------------------------------------------
def compress_output(outpath,index_per_day=8):
    ''' '''
    # create object for output file
    if os.path.exists(outpath):
        try:
            ftmp_name = "%s/%s.nc" % (settings.DirWork,str(uuid.uuid1()))
            # 3hr data
            if index_per_day == 8:
                cmd = "nccopy -k 4 -d 4 %s %s" % (outpath,ftmp_name)
            else:
                cmd = "nccopy -k 4 -d 4 %s %s" % (outpath,ftmp_name)
            retval = shell(cmd)
            # remove help file
            os.remove(outpath)
            retval = shell("mv %s %s" % (ftmp_name,outpath))
        except:
            log.error("Error while compressing ouput file: (%s)" % outpath)
    else:
        log.error("File does not exist: (%s)" % outpath)


# -----------------------------------------------------------------------------
def set_attributes_create(outpath,res=None):
    ''' '''
    # create object for output file
    if os.path.exists(outpath):
        f_out = Dataset(outpath,'r+')
        # set resolution if passed
        if res:
            f_out.setncattr("frequency",res)
        # set (new) tracking_id
        f_out.setncattr("tracking_id",str(uuid.uuid1()))
        # set new creation_date
        f_out.setncattr("creation_date",datetime.now().strftime(settings.FMT))

        if 'history' in f_out.ncattrs():
            f_out.delncattr("history")

        # commit changes
        f_out.sync()
        # close output file
        f_out.close()
    else:
        log.error("File does not exist: (%s)" % outpath)


# -----------------------------------------------------------------------------
def set_coord_attributes(params,f_var,f_out):
    """
    set the attribute depending on settings in input control file
    """
    if not f_out:
        log.warning("No output object for setting coordinates value available!")
        return
    # skip variables
    #if 'mrfso' in f_out.variables or 'mrro' in f_out.variables:
        #return
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
                log.error("No lon/lat coordinates available, exiting...")
                sys.exit()
            #elif 'rlon' in f_out.variables and 'rlat' in f_out.variables:
                #f_var.coordinates = 'plev rlat rlon'
            #else:
                #f_var.coordinates = 'plev'
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
                cmd = "No lon/lat coordinates available, exiting..."
                log.error(cmd)

                sys.exit()
            #elif 'rlon' in f_out.variables and 'rlat' in f_out.variables:
                #f_var.coordinates = 'height rlat rlon'
            #else:
                #f_var.coordinates = 'height'
    else:
        if 'lon' in f_out.variables and 'lat' in f_out.variables:
            f_var.coordinates = 'lat lon'
        else:
            cmd = "No lon/lat coordinates available, exiting..."
            log.error(cmd)
            sys.exit()
        #elif 'rlon' in f_out.variables and 'rlat' in f_out.variables:
            #f_var.coordinates = 'rlat rlon'


# -----------------------------------------------------------------------------
def new_dataset_version():
    '''
    Create new dataset version from actual date
    this will be inserted in the CORDEX output DRS directory structure
    '''
    return datetime.now().strftime("%Y%m%d")


# -----------------------------------------------------------------------------
def get_out_dir(var,res,cm_type):
    '''
    creates a path from variable,resolution,cell methods
    actual: in temp directory
    later: in output directory
    '''
    if cm_type != '':
        outpath = create_outpath(res,var)
        outpath = "%s/%s" % (settings.DirOut,outpath)
        if not os.path.isdir(outpath):
            os.makedirs(outpath)
        return outpath
    else:
        return ""


# -----------------------------------------------------------------------------
def get_temp_dir(var,res,cm_type): #todo: superfluent
    '''
    creates a path from variable,resolution,cell methods
    actual: in temp directory
    later: in output directory
    '''
    return get_out_dir(var,res,cm_type)


# -----------------------------------------------------------------------------
def proc_chunking(params,reslist):
    """
    create AGG_DAY (day) or AGG_MON (mon) years chunks of yearly input files
    (as defined in .ini file; default: 5 and 10, respectively)
    """

    # get cdf variable name
    var = params[config.INDEX_VAR]

    for res in reslist:
        if res == 'day':
            max_agg = config.get_config_value('index','AGG_DAY')
            cm_type = params[config.get_config_value('index','INDEX_VAR_CM_DAY')]
        elif res == 'mon':
            max_agg = config.get_config_value('index','AGG_MON')
            cm_type = params[config.get_config_value('index','INDEX_VAR_CM_MON')]
        elif res == 'sem':
            max_agg = config.get_config_value('index','AGG_MON')
            cm_type = params[config.get_config_value('index','INDEX_VAR_CM_MON')]
        else:
            cmd = "Resolution (%s) is not supported in chunking, keep it as it is." % res
            log.warning(cmd)
            continue
        log.info("Chunking for variable (%s) and resolution (%s) " % (var,res))
        if cm_type != '':
            outdir = get_temp_dir(var,res,cm_type)
            for dirpath,dirnames,filenames in os.walk(outdir):
                f_list = []
                start_yr = 0
                stop_yr = 0
                flist = ''
                for f in sorted(filenames):
                    idx = f.index("%s_" % res)
#                    act_yr = int(f[idx+len("%s_" % res):f.index(".nc")][:4])
                    if start_yr == 0:
                        if res == 'day':
                            start_yr = int(f[idx+len("%s_" % res):f.index(".nc")][:8])
                        elif res == 'mon' or res == 'sem':
                            start_yr = int(f[idx+len("%s_" % res):f.index(".nc")][:6])
                    idx = f.rindex("-")
                    if res == 'day':
                        stop_yr = int(f[idx+1:f.index(".nc")][:8])
                    elif res == 'mon' or res == 'sem':
                        stop_yr = int(f[idx+1:f.index(".nc")][:6])
                    f_list.append("%s/%s" % (outdir,f))
                    # use year of stop date for chunk border
                    act_yr = int(f[idx+1:f.index(".nc")][:4])
                    # outfile = create_filename(var,res,str(start_yr),str(stop_yr))
                    if act_yr % max_agg == 0:
                        # TODO: correct this to first step and last step
                        # generate input filelist
                        for y in f_list:
                            flist = ("%s %s " % (flist,y))

                        # generate complete output path with output filename
                        outfile = create_filename(var,res,str(start_yr),str(stop_yr))
                        # generate outpath with outfile and outdir
                        outpath = "%s/%s" % (outdir,outfile)
#                        print outpath
                        # cat files to aggregation file
                        # skip if exist
                        if (not os.path.isfile(outpath)) or config.get_config_value('boolean','overwrite'):
                            if config.get_config_value('boolean','overwrite'):
                                log.info("Output file exist: %s, overwriting..." % (outpath))
                            retval = shell("ncrcat -h -O %s %s " % (flist,outpath))

                            # remove source files
                            if len(f_list) > 1:
                                retval = shell("rm -f %s " % (flist))
                            # set attributes
                            set_attributes_create(outpath,res)
                        else:
                            log.info("Output file exist: %s, skipping!" % (outpath))

                        # reset parameter
                        f_list = []
                        start_yr = 0
                        stop_yr = 0
                        flist = ''
                # do the same for wahts left in list
                if len(f_list) > 1:
                    # generate filename for outfile
                    outfile = create_filename(var,res,str(start_yr),str(stop_yr))
                    # generate outpath with outfile and outdir
                    outpath = "%s/%s" % (outdir,outfile)
                    # generate input filelist
                    for y in f_list:
                        flist = ("%s %s " % (flist,y))

                    # cat files to aggregation file
                    if (not os.path.isfile(outpath)) or config.get_config_value('boolean','overwrite'):
                        if config.get_config_value('boolean','overwrite'):
                            log.info("Output file exist: %s, overwriting..." % (outpath))
                        retval = shell("ncrcat -h -O %s %s " % (flist,outpath))

                        # remove source files
                        retval = shell("rm -f %s " % (flist))

                        # set attributes
                        set_attributes_create(outpath,res)
                    else:
                        log.info("Output file exist: %s, skipping!" % (outpath))


# -----------------------------------------------------------------------------
def leap_year(year, calendar='standard'):
    """
    Determine if year is a leap year
    """
    leap = False
    if ((calendar in ['standard','gregorian','proleptic_gregorian','julian']) and (year % 4 == 0)):
        leap = True
        if ((calendar == 'proleptic_gregorian') and (year % 100 == 0) and (year % 400 != 0)):
            leap = False
        elif ((calendar in ['standard', 'gregorian']) and (year % 100 == 0) and (year % 400 != 0) and (year < 1583)):
            leap = False
    return leap


# -----------------------------------------------------------------------------
def add_vertices(f_out):
    """
    add vertices to output from vertices file
    """
    # read vertices from file if exist
    if os.path.isfile(config.vertices_file):
        f_vert = Dataset(config.vertices_file,'r')
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
            var_out = f_out.createVariable('lon_vertices',datatype='f',dimensions=lon_vertices.dimensions)
            # copy content to new datatype
            if 'lon' in f_vert.variables.keys():
                f_lon = f_vert.variables['lon']
                if 'units' in f_lon.ncattrs():
                    var_out.units = str(f_lon.units)
                else:
                    var_out.units = "degrees_east"
                if not 'lon' in f_out.variables.keys():
                    _copy_var(f_vert,f_out,'lon')
            else:
                var_out.units = "degrees_east"
            f_out_lon = f_out.variables['lon']
            f_out_lon.bounds = 'lon_vertices'
            var_out[:] = lon_vertices[:]
            log.info("Vertices (lon) set!")
        if 'lat_vertices' in f_vert.variables.keys() and 'lat_vertices' not in f_out.variables.keys():
            lat_vertices = f_vert.variables['lat_vertices']
            # create lat_vertices in output
            #var_out = f_out.createVariable('lat_vertices',datatype='f',dimensions=['rlat','rlon','vertices'])
            var_out = f_out.createVariable('lat_vertices',datatype='f',dimensions=lat_vertices.dimensions)
            # copy content to new datatype
            if 'lat' in f_vert.variables.keys():
                f_lat = f_vert.variables['lat']
                if 'units' in f_lon.ncattrs():
                    var_out.units = str(f_lat.units)
                else:
                    var_out.units = "degrees_north"
                if not 'lat' in f_out.variables.keys():
                    _copy_var(f_vert,f_out,'lat')
            else:
                var_out.units = "degrees_north"
            f_out_lat = f_out.variables['lat']
            f_out_lat.bounds = 'lat_vertices'
            var_out[:] = lat_vertices[:]
            log.info("Vertices (lat) set!")

        # commit changes
        f_out.sync()


# -----------------------------------------------------------------------------
def check_resolution(params,res,process_table_only):
    '''
    check whether requested resolution is in table or not
    '''
    if res in ["1hr","3hr","6hr","12hr"]:
        res_hr=(float(res[:-2])) #extract time resolution in hours
        freq_table=params[config.get_config_value('index','INDEX_FRE_SUB')]
        freq=24./res_hr
    elif res=="day":
        res_hr=24.
        freq_table=params[config.get_config_value('index','INDEX_FRE_DAY')]
        freq=1. #requested samples per day
    elif res=="mon":
        res_hr= 28*24.  #minimum number of hours per month
        freq_table=params[config.get_config_value('index','INDEX_FRE_MON')]
        freq=1. #requested samples per month
    elif res == 'fx':
        return True
    else:
        log.warning("Time resolution (%s) is not supported, skipping..." % res)
        return False

    #if process_table_only is set: check if requested time resolution is declared in table
    if (freq_table=="" or float(freq_table) != freq) and process_table_only:
        log.warning("Requested time resolution (%s) not declared in parameter table. Skipping.." % res)
        return False
    else:
        return True


# -----------------------------------------------------------------------------

def get_attr_list(var_name):
    '''
    TODO: ATTR_SETTING
    set pre defined attributes for some variable like lon,lat
    '''
    att_lst = {}
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
    return att_lst


# -----------------------------------------------------------------------------
def copy_var(f_in,f_out,var_name):
    '''
    copy variable from in_file to out_file
    '''
    if var_name in f_in.variables and var_name not in f_out.variables:
        var_in = f_in.variables[var_name]
        if var_name in ['lat','lon']:
            new_dimensions = var_in.dimensions #'f'
        else:
            new_dimensions = var_in.dimensions
        #if var_name == 'rotated_pole':
            #var_name = 'rotated_latitude_longitude'
        if var_name in ['lat','lon']:
            new_datatype = 'd'
        else:
            new_datatype = var_in.datatype
        log.debug(new_dimensions)
        var_out = f_out.createVariable(var_name,datatype=new_datatype,dimensions=new_dimensions)
        # set all as character converted with str() function
        if var_name in ['lat','lon']:
            att_lst = get_attr_list(var_name)
        else:
            att_lst = {}
            for k in var_in.ncattrs():
                if config.get_config_value('boolean','add_vertices') == False and k == 'bounds':
                    continue
                if isinstance(var_in.getncattr(k),unicode):
                    att_lst[k] = str(var_in.getncattr(k))
                else:
                    att_lst[k] = var_in.getncattr(k)
        var_out.setncatts(att_lst)
        # copy content to new datatype
        var_out[:] = var_in[:]
        log.info("Copy: %s" % (var_out.name))


# -----------------------------------------------------------------------------
def add_coordinates(f_out):
    """
    add lat/lon to output from coordinates file
    """
    # read vertices from file if exist
    log.info(os.path.isfile(settings.coordinates_file))
    if os.path.isfile(settings.coordinates_file):
        f_coor = Dataset(settings.coordinates_file,'r')
        # copy lon
        copy_var(f_coor,f_out,'lon')
        log.info("Variable lon added!")
        # copy lat
        copy_var(f_coor,f_out,'lat')
        log.info("Variable lat added!")
        # commit changes
        f_out.sync()


# -----------------------------------------------------------------------------
def get_derotate_vars(flt=None):
    '''
    INDEX_VAR_ROTATE
    '''
    lst = []
    for row in settings.param:
        if settings.param[row][config.get_config_value('index','INDEX_VAR_ROTATE')] == 'derotate':
            if flt == None or (flt and settings.param[row][config.get_config_value('index','INDEX_VAR')].find(flt) == 0):
                lst.append(settings.param[row][config.get_config_value('index','INDEX_VAR')])
    return lst


# -----------------------------------------------------------------------------
def process_file_fix(params,in_file):
    '''
    process one input file and create one one output file

    call with:
        var: variable name (cf notification)
        res: resolution: 3hr,6h3,day,mon,cm_sem
        cm_type: cell method: sum,mean,max,min,...
        in_file: path to in file
        outdir: output directory (where the complete data goes
    '''
    # get cdf variable name
    var = params[config.get_config_value('index','INDEX_VAR')]

    # fixed
    res = 'fx'
    log.info("####################\n# Var in work: '%s'\n####################" % (var))

    # create object from netcdf file to access all parameters and attributes
    f_in = Dataset(in_file,"r")
    log.info("Input1: %s" % in_file)

    for name in f_in.ncattrs():
        if name in settings.global_attr_file: #only take attribute from file if in this list
            settings.Global_attributes[name] = str(f_in.getncattr(name))

    #TODO: ist this fix?
    name = "driving_model_ensemble_member"
    settings.Global_attributes[name] = 'r0i0p0'

    # out directory
    outdir = get_temp_dir(var,'fx','fx')
    # get file name
    outfile = create_filename(var,'fx','','')
    # create complete outpath: outdir + outfile
    outpath = "%s/%s" % (outdir,outfile)
    # skip file if exists or overwrite
    if os.path.isfile(outpath) and (not config.get_config_value('boolean','overwrite')):
        log.info("Output file exists: %s" % (outpath))
        if not config.get_config_value('boolean','overwrite'):
            log.info("Returning...")
            return
        else:
            log.info("Overwriting..")
    log.info("Output to: %s" % (outpath))

    # create object for output file
    f_out = Dataset(outpath,'w')

    # create dimensions in target file
    for name, dimension in f_in.dimensions.iteritems():
        # skip dimension
        if name in settings.varlist_reject or name in ['bnds','time']:
            continue
            #f_out.createDimension(name, len(dimension) if not dimension.isunlimited() else None)
        else:
            if dimension not in ['bnds','time']:
                f_out.createDimension(name, len(dimension) if not dimension.isunlimited() else None)

    # set dimension vertices only if set to True in settings file
    if config.get_config_value('boolean','add_vertices') == True:
        f_out.createDimension('vertices',4)

    try:
        mulc_factor = float(params[config.get_config_value('index','INDEX_COVERT_FACTOR')].strip().replace(',','.'))
    except ValueError:
        log.warning("No conversion factor set for %s in parameter table. Setting it to 1..." % params[config.get_config_value('index','INDEX_RCM_NAME')])
        mulc_factor = 1.0
    if mulc_factor == 0:
        log.warning("Conversion factor for %s is set to 0 in parameter table. Setting it to 1..." % params[config.get_config_value('index','INDEX_RCM_NAME')])
        mulc_factor = 1.0
    log.debug(f_in.variables.iteritems())
#    sys.exit()
    for var_name, variable in f_in.variables.iteritems():
        # don't copy time_bnds if cm == point or variable time_bnds
        log.debug("VAR: %s" % (var_name))
        if var_name in ['time','time_bnds','bnds']:
            continue
        var_in = f_in.variables[var_name]
        # create output variable
        if var_name in ['rlon','rlat']:
            data_type = 'd'
        elif var_name in ['lon','lat']:
            data_type = 'd'
        elif var_name in settings.varlist_reject:
            continue
            #data_type = 'i8'
        else:
            data_type = var_in.datatype
        # at variable creation set fill_vlue, later is impossible
        # also set the compression
        if config.get_config_value('boolean','nc_compress') == True:
            log.info("COMPRESS all variables")
        else:
            log.info("NO COMPRESS")
        # skip 'pressure'!!
        my_lst = []
        for dim in var_in.dimensions:
            log.debug("DIM: %s" % (dim))
            if dim in ['time','time_bnds','bnds']:
                continue
            if str(dim) not in settings.varlist_reject:
                my_lst.append(dim)
        var_dims = tuple(my_lst)
        log.info("Attributes (of variable %s): %s" % (var_name,var_in.ncattrs()))
        if var_name in [var,settings.netCDF_attributes['RCM_NAME_ORG']]:
            # TODO:test on FillValue for variables: mrfso,mrso,mrro
            # could be negativ!
            if config.get_config_value('boolean','nc_compress') == True:
                var_out = f_out.createVariable(var_name,datatype=data_type,
                    dimensions=var_dims,complevel=4,fill_value=settings.netCDF_attributes['missing_value'])
            else:
                var_out = f_out.createVariable(var_name,datatype=data_type,
                    dimensions=var_dims,fill_value=settings.netCDF_attributes['missing_value'])

        else:
            if config.get_config_value('boolean','nc_compress') == True:
                var_out = f_out.createVariable(var_name,datatype=data_type,dimensions=var_dims,complevel=4)
            else:
                var_out = f_out.createVariable(var_name,datatype=data_type,dimensions=var_dims)
        # set all as character converted with str() function
        if var_name in ['lat','lon']:
            att_lst = get_attr_list(var_name)
        else:
            att_lst = {}
            for k in var_in.ncattrs():
                if config.get_config_value('boolean','add_vertices') == False and k == 'bounds':
                    continue
                if k in ['coordinates']:
                    continue
                if k != '_FillValue':
                    if isinstance(var_in.getncattr(k),unicode):
                        att_lst[k] = str(var_in.getncattr(k))
                    else:
                        att_lst[k] = var_in.getncattr(k)
            if var_name == 'rlon':
                att_lst['axis'] = 'X'
                att_lst['long_name'] = 'longitude in rotated pole grid'

            elif var_name == 'rlat':
                att_lst['axis'] = 'Y'
                att_lst['long_name'] = 'latitude in rotated pole grid'

        var_out.setncatts(att_lst)

        # copy content to new datatype
        if var_name in ['rlon','rlat','rotated_pole']:
           var_out[:] = var_in[:]
        else:
           var_out[:] = mulc_factor * var_in[:]
#add lon and lat coordinates to output files
           f_coor = Dataset(settings.coordinates_file,'r')
        # copy lon
           copy_var(f_coor,f_out,'lon')
           log.info("Variable lon added!")
        # copy lat
           copy_var(f_coor,f_out,'lat')
           log.info("Variable lat added!")

        log.info("Copy from input: %s" % (var_out.name))

    # commit changes
    f_out.sync()

    ###################################
    # do some additional settings
    ###################################
    # rename variable
    try:
        f_out.renameVariable(settings.netCDF_attributes['RCM_NAME_ORG'],settings.netCDF_attributes['cf_name'])
    except:
        log.warning("Variable has cf name already: %s" % (var))

    # set all predefined global attributes
    f_out.setncatts(settings.Global_attributes)
    log.info("Global attributes set!")

    # commit changes
    f_out.sync()

    # exist in some output (e.g. CCLM) in CORDEX, default: False
    if config.get_config_value('boolean','add_vertices') == True:
        add_vertices(f_out)

    # create variable object to output file
    f_var = f_out.variables[settings.netCDF_attributes['cf_name']]
    # set additional variables attributes
    f_var.standard_name = settings.netCDF_attributes['standard_name']
    f_var.long_name = settings.netCDF_attributes['long_name']
    f_var.units = settings.netCDF_attributes['units']

    #add coordinates attribute to fx-variables
    f_var.coordinates = settings.netCDF_attributes['coordinates']
    #if params[config.get_config_value('index','INDEX_CM_AREA')]=='':
        #f_var.cell_methods = "time: %s" % (cm_type)
    #else:
        #f_var.cell_methods = "time: %s area: %s" % (cm_type,params[config.get_config_value('index','INDEX_CM_AREA')])
    # set attribute coordinates
    #set_coord_attributes(params,f_var,f_out)

    # set attribute missing_value
    f_var.missing_value = settings.netCDF_attributes['missing_value']
    log.debug("#####################: %s" % (f_var.ncattrs()))
    try:
        f_var.setncattr('grid_mapping','rotated_pole')
    except:
        log.warning("Variable '%s' does not exist." % ("rotated_pole"))

    # commit changes
    f_out.sync()

    # close output file
    f_out.close()

    # set attributes: frequency,tracking_id,creation_date
    set_attributes_create(outpath,res)

    # ncopy file to correct output format
    if config.get_config_value('boolean','nc_compress') == True:
        compress_output(outpath,params[config.get_config_value('index','INDEX_FRE_DAY')])
    log.info("Variable attributes set!")

    # close input file
    f_in.close()
    log.debug("Input4: %s" % in_file)

    # ready message
    log.info("Variable '%s' finished!" % (var))


# -----------------------------------------------------------------------------
def proc_seasonal_mean(params):
    ''' create seasonal mean from monthly data '''

    # get cdf variable name
    var = params[config.get_config_value('index','INDEX_VAR')]
    # first get monthly data
    res = "day"
    cm_type = params[config.get_config_value('index','INDEX_VAR_CM_DAY')]
    # get outdir
    indir = get_temp_dir(var,res,cm_type)
    log.info("Inputdir: %s" % (indir))

    # get files with monthly data from the same input (if exist)
    for dirpath,dirnames,filenames in os.walk(indir):
        # switch to sem output
        f_list = []
        start_yr = 0
        cmd = ''
        # seasonal mean
        res = 'sem'
        # get cell method
        cm_type = params[config.get_config_value('index','INDEX_VAR_CM_SEM')]
        if cm_type != '':
            t_delim = 'mean over days'
            if t_delim in cm_type:
#                cm0 = cm_type[cm_type.index(' '):]
                cm = 'mean' #cm_type[cm_type.index(t_delim)+len(t_delim):]
                cmd = "Cell method used: %s" % (cm)

            else:
                cm = cm_type
            log.info("Cell method used for cdo command: %s" % (cm))

            outdir = get_temp_dir(var,res,cm_type)
            f_lst = sorted(filenames)
            i = 0
            for f in f_lst:
                if config.get_config_value('boolean','use_search_string') and f.find(settings.search_input_string) > 0 and f.find(settings.search_input_string.replace('_','-')) > 0:
                    continue

                # first a temp file
                ftmp_name = "%s/%s%s" % (config.tmp_dir,str(uuid.uuid1()),'-help.nc')
                # for season the last month from previous year is needed
                if i == 0:
                    # generate outpath with outfile and outdir
                    f = "%s/%s" % (dirpath,f)
                    cmd = "cdo -f %s -seas%s -selmonth,3/11 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,f,ftmp_name)
                    retval = shell(cmd)

                else:
                    # first last December of previous year
                    f_hlp12 = tempfile.NamedTemporaryFile(dir=config.tmp_dir,delete=False)
                    f = "%s/%s" % (dirpath,f_lst[i-1])
                    cmd = "cdo -f %s selmonth,12 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),f,f_hlp12.name)
                    retval = shell(cmd)
                    f = "%s/%s" % (dirpath,f_lst[i])

                    # second month 1...11 of actual year
                    f_hlp1_11 = tempfile.NamedTemporaryFile(dir=config.tmp_dir,delete=False)
                    cmd = "cdo -f %s selmonth,1/11 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),f,f_hlp1_11.name)
                    retval = shell(cmd)

                    # now concatenate all 12 month
                    f_hlp12_11 = tempfile.NamedTemporaryFile(dir=config.tmp_dir,delete=False)
                    cmd = "ncrcat -h -O %s %s %s" % (f_hlp12.name,f_hlp1_11.name,f_hlp12_11.name)
                    retval = shell(cmd)

#                    cmd = "cdo -f %s -s timsel%s,3,2 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,f_hlp2.name,ftmp_name)
#                    cmd = "cdo -f %s -s timsel%s,3 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,f_hlp12_11.name,ftmp_name)
#                    cmd = "cdo -f %s timsel%s,3 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,f_hlp12_11.name,ftmp_name)
                    cmd = "cdo -f %s seas%s,3 %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,f_hlp12_11.name,ftmp_name)
                    retval = shell(cmd)

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
                try:
                    #if not 'rotated_latitude_longitude' in f_tmp.variables.keys() and 'rotated_pole' in f_tmp.variables.keys():
                        #f_tmp.renameVariable('rotated_pole','rotated_latitude_longitude')
                    if not 'rotated_pole' in f_tmp.variables.keys():
                        var_name = 'rotated_pole'
                        if var_name in f_in.variables.keys():
                            copy_var(f_in,f_tmp,var_name)
                except:
                    log.info("Variable '%s' does not exist." % ("rotated_pole"))

                # copy also height an plev: they are correct at that point
                for var_name in ['lat','lon','rotated_pole','plev','height']:
#                    print var_name,var_name in f_in.variables.keys(),var_name not in f_tmp.variables
                    if var_name in f_in.variables.keys() and var_name not in f_tmp.variables.keys():
                        copy_var(f_in,f_tmp,var_name)
                f_var.setncattr('grid_mapping','rotated_pole')
                if params[config.get_config_value('index','INDEX_CM_AREA')]=='':
                    f_var.cell_methods = "time: %s" % (cm_type)
                else:
                    f_var.cell_methods = "time: %s area: %s" % (cm_type,params[config.get_config_value('index','INDEX_CM_AREA')])

                # commit changes
                f_tmp.sync()

                # close input object
                f_in.close()

                # set attribute coordinates
                set_coord_attributes(params,f_var=f_tmp.variables[var],f_out=f_tmp)

                # commit changes
                f_tmp.sync()

                # get time variable from input
                time = f_tmp.variables['time']
                time_bnds = f_tmp.variables['time_bnds']
                # get the first time value and convert to date
                dt1 = num2date(time_bnds[0,0],time.units,time.calendar)
                # get the last time value and convert to date
                # attention: minus ONE DAY to meet the end month
                dt2 = num2date(time_bnds[len(time_bnds)-1,1]-1,time.units,time.calendar)
                dt_start = str(dt1)[:7].replace("-","")
                dt_stop = str(dt2)[:7].replace("-","")

                # close output object
                f_tmp.close()

                # create outpath to store
                outfile = create_filename(var,res,dt_start,dt_stop)
                outpath = "%s/%s" % (outdir,outfile)
                if not os.path.isfile(outpath):
                    # rename temp file to output filename outpath
                    retval = shell("mv %s %s" % (ftmp_name,outpath))

                    # set attributes
                    set_attributes_create(outpath,res)
                    # correct netcdf version
                    if config.get_config_value('boolean','nc_compress') == True:
                        compress_output(outpath,params[config.get_config_value('index','INDEX_FRE_DAY')])

                    # exist in some output (e.g. CCLM) in CORDEX, default: False
                    if config.get_config_value('boolean','add_vertices') == True:
                        f_out = Dataset(outpath,'r+')
                        add_vertices(f_out)
                        f_out.close()
                else:
                    os.remove(ftmp_name)
                # next file index in the list
                i += 1
        else:
            log.warning("No cell method set for this variable (%s) and time resolution (%s)." % (var,res))


# -----------------------------------------------------------------------------
def proc_test_var(process_list,varlist,reslist):
    '''
    check which:
    - variables are possible in which output resolution
    - time settings are in input files
    - input variable/directory is available
    '''
    log.info("Start Test")
    for var in varlist:

        if var in config.get_model_value('var_list_fixed'):
            continue
        params = settings.param[var]
        set_attributes(params,process_list)

        in_dir = "%s/%s" % (get_input_path(var),params[config.get_config_value('index','INDEX_RCM_NAME')])
        log.info("Looking for input dir: %s" % (in_dir))
        if os.path.isdir(in_dir) == False:
            in_dir = "%s/%s" % (get_input_path(var),params[config.get_config_value('index','INDEX_RCM_NAME')].replace('p',''))
            log.info("Looking for input dir: %s" % (in_dir))
        if os.path.isdir(in_dir) == True:
            log.info("###############################################################")
            log.info("Input directory for cf variable '%s' exists: %s" % (var,in_dir))
            for dirpath,dirnames,filenames in os.walk(in_dir, followlinks=True):
                i = 0
                for f in sorted(filenames):
                    in_file = "%s/%s" % (dirpath,f)
                    print("Infile: ",in_file) #,params[config.INDEX_MODEL_LEVEL]
                    f_in = Dataset(in_file,'r')
                    if params[config.get_config_value('index','INDEX_RCM_NAME')] in f_in.variables.keys():
                        f_var = f_in.variables[params[config.get_config_value('index','INDEX_RCM_NAME')]]
                    elif params[config.get_config_value('index','INDEX_RCM_NAME_ORG')] in f_in.variables.keys():
                        f_var = f_in.variables[params[config.get_config_value('index','INDEX_RCM_NAME_ORG')]]
                    else:
                        break
                    # get time variable from input
                    time_in = f_in.variables['time']

                    if 'calendar' in time_in.ncattrs():
                        in_calendar = str(time_in.calendar)
                    else:
                        g_attr = 'driving_model_id'
                        if g_attr in f_in.ncattrs():
                            if 'MIROC' in f_in.getncattr(g_attr):
                                in_calendar = '365_day'
                            elif 'CanESM2' in f_in.getncattr(g_attr):
                                in_calendar = '365_day'
                            elif 'HadGEM2' in f_in.getncattr(g_attr):
                                in_calendar = '360_day'
                            else:
                                in_calendar = 'standard'
                        else:
                            in_calendar = 'standard'

                    if config.get_config_value('boolean','use_alt_units'):
                        time_in_units = config.get_config_value('settings','alt_units')
                    else:
                        time_in_units = time_in.units

                    dt_in1 = num2date(time_in[0],time_in_units,calendar=in_calendar)
                    dt_in1_year = dt_in1.year
                    log.info("Year(time): %d" % (dt_in1_year))
                    log.info("First time step: %s" % (str(dt_in1)))
                    dt_in2 = num2date(time_in[1],time_in_units,calendar=in_calendar)
                    dt_in2_year = dt_in2.year
                    log.info("Year(time): %d" % (dt_in2_year))
                    log.info("Second time step: %s" % (str(dt_in2)))
                    a = datetime.strptime(str(dt_in1), settings.FMT)
                    b = datetime.strptime(str(dt_in2), settings.FMT)
                    tdelta = b - a
                    time_step = (24 * tdelta.days)+(tdelta.seconds / 3600)
                    log.info("Time step interval: %s h" % time_step)
                    dt_in_max = num2date(time_in[len(time_in)-1],time_in_units,calendar=in_calendar)
                    log.info("Last time step: %s" % (str(dt_in_max)))

                    for n in range(len(time_in)):
                        if num2date(time_in[n],time_in_units,calendar=in_calendar).year == dt_in1_year:
                            data_max_len = n
                    # add one count
                    data_max_len = data_max_len + 1

                    # move the reference date to 1949-12-01T00:00:00Z
                    # by setting time:units to: "days since 1949-12-01T00:00:00Z"
                    # now get the difference in time.units for refdate: start point for all settings in time and time_bnds
                    num_refdate_diff = date2num(dt_in1,units=config.get_config_value('settings','units'),calendar=in_calendar)
                    num_refdate_diff = float(int(num_refdate_diff))
                    # show some numbers
                    log.info("num_refdate_diff: %s" % str(num_refdate_diff))
                    log.info("Startdate for time settings: %s, %s" % (str(num_refdate_diff),str(num2date(num_refdate_diff,units=config.get_config_value('settings','units'),calendar=in_calendar))))

                    f_in.close()
                    i = i + 1
                    if i > 0:
                        break

        else:
            continue
    log.info("End")


# -----------------------------------------------------------------------------
def proc_corr_var(params,res,key):
    '''
    correct time - climatology problem
    '''

    if key not in ['correct_fillvalue','convert_to_float','add_coordinates','climatology','missing_value','missing_value_set','division_1000','division_6','add_plev_height','remove_height']:
        log.warning("Unknown key: %s" % (key))
        return

    # get cdf variable name
    var = params[config.get_config_value('index','INDEX_VAR')]

    # first get monthly data
    #res = "sem"
    cm_type = params[config.get_config_value('index','INDEX_VAR_CM_DAY')]
    # get outdir
    indir = get_temp_dir(var,res,cm_type)
    log.info("Inputdir: %s" % (indir))

    # get files with monthly data from the same input (if exist)
    for dirpath,dirnames,filenames in os.walk(indir):
        f_lst = sorted(filenames)
        #print "List: ",f_lst
        for f in f_lst:
            infile = "%s/%s" % (dirpath,f)
            log.info(infile)

            # correct negative missing_value
            if key == 'correct_fillvalue': # == True or var in ['mrfso','mrro','mrros','mrso','snw']) and os.path.isfile(outpath):
                _FillValue = config.get_config_value('float','missing_value')
                cmd = "ncatted -h -O -a missing_value,%s,m,f,-%s -a _FillValue,%s,m,f,-%s %s" %  (var,_FillValue,var,_FillValue,infile)
                retval = shell(cmd)
                cmd = "ncatted -h -O -a missing_value,%s,m,f,%s -a _FillValue,%s,m,f,%s %s" %  (var,_FillValue,var,_FillValue,infile)
                retval = shell(cmd)

            # convert variable form double to float
            elif key == 'convert_to_float':
                # mv file to temp dir
                f_in = Dataset(infile,'r')
                if var in f_in.variables.keys():
                    if 'lat' in f_in.variables.keys():
                        f_lat = f_in['lat']
                        if f_lat.datatype == 'float32':
                            print(f_lat.name,"Float")
                        else:
                            print("###########################################")
                            print(f_lat.name,"Double") #,f_var.datatype == 'float64'
                    if 'lon' in f_in.variables.keys():
                        f_lon = f_in['lon']
                        if f_lon.datatype == 'float32':
                            print(f_lon.name,"Float")
                        else:
                            print("###########################################")
                            print(f_lon.name,"Double") #,f_var.datatype == 'float64'
                    f_var = f_in[var]
                    if f_var.name in [var]: #,'lon','lat','height','plev']:
                        if f_var.datatype == 'float32':
                            print(f_var.name,"Float")
                        else:
                            print("###########################################")
                            print(f_var.name,"Double") #,f_var.datatype == 'float64'

                            tmpfile = "%s/%s" % (settings.DirWork,f)
                            cmd = "mv %s %s" % (infile,tmpfile)
                            print(cmd)
                            retval = shell(cmd)
                            # now conert to float
                            cmd = "ncap2 -s '%s=float(%s)' %s %s" % (var,var,tmpfile,infile)
                            print(cmd)
                            retval = shell(cmd)
                            if os.path.isfile(tmpfile) and os.path.isfile(infile):
                                os.remove(tmpfile)
            # add coordinates attribute to variable or set to correct value
            elif key == 'add_coordinates':
                if not os.path.isfile(infile):
                    continue
                f_in = Dataset(infile,'r+')
                log.info(f_in.variables.keys())
                if 'lon' in f_in.variables.keys() and 'lat' in f_in.variables.keys():
                    f_var = f_in.variables[var]
                    if 'height' in f_in.variables.keys():
                        f_var.coordinates = 'height lat lon'
                    elif 'plev' in f_in.variables.keys():
                        f_var.coordinates = 'plev lat lon'
                    else:
                        f_var.coordinates = 'lat lon'
                    f_in.sync()
                f_in.close()

            # place holder for correction of attribute, only for some CORDEX variables defined
            elif key == 'climatology':
                f_in = Dataset(infile,'r')
                f_var = f_in.variables[var]
                print(f_var.ncattrs())
                f_in.close()

            # correct missing_value from negative to positive value
            elif key == 'missing_value':
                cmd = "ncatted -h -O -a missing_value,%s,m,f,-1.e20 -a _FillValue,%s,m,f,-1.e20 %s" %  (var,var,infile)
                print(cmd)
                retval = shell(cmd)
                cmd = "ncatted -h -O -a missing_value,%s,m,f,1.e20 -a _FillValue,%s,m,f,1.e20 %s" %  (var,var,infile)
                print(cmd)
                retval = shell(cmd)

            # set missing_value
            elif key == 'missing_value_set':
                retval = shell("ncatted -h -O -a missing_value,%s,m,f,1.e20 -a _FillValue,%s,m,f,1.e20 %s" %  (var,var,infile))

            # multiply variable with 0.001!
            elif key == 'division_1000':
                if var in ['mrfso','mrso']:
                    tmpfile = "%s/%s" % (settings.DirWork,f)
                    retval = shell("mv %s %s" % (infile,tmpfile))
                    retval = shell("ncap2 -s '%s=%s*0.001' %s %s" % (var,var,tmpfile,infile))
                    if os.path.isfile(tmpfile):
                        os.remove(tmpfile)

            # multiply variable with 1./6.
            elif key == 'division_6':
                tmpfile = "%s/%s" % (settings.DirWork,f)
                retval = shell("mv %s %s" % (infile,tmpfile))
                #f1 = float(1./6.)
                # 16 digits too much?
                f1 = str("%.16f" % (1./6.))
                retval = shell("ncap2 -s '%s=%s*%s' %s %s" % (var,var,f1,tmpfile,infile))
                if os.path.isfile(tmpfile):
                    os.remove(tmpfile)

            # add plev | height variable to file, correct coordinates setting
            elif key == 'add_plev_height':
                if int(params[config.get_config_value('index','INDEX_VAL_LEV')].strip()) > 0:
                    f_out = Dataset(infile,'r+')
                    # pressure level variable
                    if params[config.get_config_value('index','INDEX_MODEL_LEVEL')] == config.get_config_value('settings','PModelType'):
                        if not 'plev' in f_out.variables:
                            var_out = f_out.createVariable('plev',datatype='d')
                            var_out.units = "Pa"
                            var_out.axis = "Z"
                            var_out.positive = "down"
                            var_out.long_name = "pressure"
                            var_out.standard_name = "air_pressure"
                            var_out[0] = params[config.get_config_value('index','INDEX_VAL_PLEV')]
                            f_var = f_out.variables[var]
                            f_var.coordinates = 'plev lat lon'
                            f_out.sync()
                    # model level variable
                    elif params[config.get_config_value('index','INDEX_MODEL_LEVEL')] == config.get_config_value('settings','MModelType'):
                        if not 'height' in f_out.variables:
                            var_out = f_out.createVariable('height',datatype='d')
                            var_out.units = "m"
                            var_out.axis = "Z"
                            var_out.positive = "up"
                            var_out.long_name = "height"
                            var_out.standard_name = "height"
                            var_out[0] = params[config.get_config_value('index','INDEX_VAL_HEIGHT')]
                            f_var = f_out.variables[var]
                            f_var.coordinates = 'height lat lon'
                            f_out.sync()
                    f_out.close()

            # remove variable height form file, correct coordinates settings for variable
            elif key == 'remove_height':
                if var in ['mrfso','mrso']:
                    f_in = Dataset(infile,'r')
                    if 'height' in f_in.variables.keys():
                        var_in = f_in.variables[var]
                        tmpfile = "%s/%s" % (settings.DirWork,f)
                        retval = shell("mv %s %s" % (infile,tmpfile))
                        retval = shell("ncks -x -v height %s %s" % (tmpfile,infile))
                        if os.path.isfile(infile):
                            f_in = Dataset(infile,'r+')
                            var_in = f_in.variables[var]
                            var_in.coordinates = var_in.coordinates.replace('height ','')
                            f_in.sync()
                            log.info("Var coordinates: %s" % (var_in.coordinates))
                        if os.path.isfile(tmpfile):
                            os.remove(tmpfile)
                    else:
                        log.info("Variable 'height' not in file: %s" % (infile))
                    f_in.close()

            # not supported key (list could be extended if needed)
            else:
                log.info("Unknown key: %s" % (key))
                return


# -----------------------------------------------------------------------------
def derotate_uv():
    """
    derotate u and v variables
    """

    var_list_rotate_u = get_derotate_vars(flt='u')
    var_list_rotate_v = get_derotate_vars(flt='v')
    var_list_rotated = get_derotate_vars(flt=None)

    # assign process list to variable
    for var in var_list_rotated:
        params = settings.param[var]
        #print params
        out_dir = "%s/%s" % (get_input_path(var),params[config.get_config_value('index','INDEX_RCM_NAME')])
        #print out_dir
        if os.path.isdir(out_dir) == False:
            log.info("Output directory does not exist: %s" % out_dir)
            os.makedirs(out_dir)

    for var in var_list_rotate_u:
        log.debug(var)
        #params = config._read_params(var)
        params = settings.param[var]
        log.debug(params)
        out_dir = "%s/%s" % (get_input_path(var),params[config.get_config_value('index','INDEX_RCM_NAME')])
        in_dir_base = ("%s/%s" % (settings.BasePath,settings.DirIn))
#        in_dir = get_input_path(var)

        in_var_u = params[config.get_config_value('index','INDEX_RCM_NAME')]
        in_dir_u = "%s/%s" % (in_dir_base,in_var_u)
        in_var_v = params[config.get_config_value('index','INDEX_RCM_NAME')].replace('U','V')
        in_dir_v = "%s/%s" % (in_dir_base,in_var_v)
        out_dir_u = "%s/%s" % (get_input_path(var),in_var_u)
        out_dir_v = "%s/%s" % (get_input_path(var),in_var_v)

        print(in_dir_u)
        print(in_dir_v)
        print(out_dir_v)
        print(out_dir_u)
        for dirpath,dirnames,filenames in os.walk(in_dir_u, followlinks=True):
            for f in sorted(filenames):
                print(f)
                start_range = f[f.rindex('_')+1:f.rindex('.')]
                in_file_u = "%s/%s" % (in_dir_u,f)
                in_file_v = "%s/%s" % (in_dir_v,f.replace('U','V'))
                out_file_u = "%s/%s" % (out_dir_u,f)
                out_file_v = "%s/%s" % (out_dir_v,f.replace('U','V'))
                # input files available?
                if os.path.isfile(in_file_u) and os.path.isfile(in_file_v):
                    # start if does output files NOT exist
                    if not os.path.isfile(out_file_u) or not os.path.isfile(out_file_v):
                        out_file = "%s/UV_%s-%s_%s.nc" % (config.DirWork,in_var_u,in_var_v,start_range)
                        out_file_derotate = "%s/UV_%s-%s_%s_derotate.nc" % (config.DirWork,in_var_u,in_var_v,start_range)
                        if not os.path.isfile(out_file):
                            cmd = "cdo merge %s %s %s" % (in_file_u,in_file_v,out_file)
                            retval = shell(cmd)
                        # only these two have the names as CCLM variable in the file
                        print(in_var_u,in_var_v)
                        if in_var_u == "U_10M" or in_var_v == "V_10M":
                            if os.path.isfile(out_file) and not os.path.isfile(out_file_derotate):
                                cmd = "cdo rotuvb,%s,%s %s %s" % (in_var_u,in_var_v,out_file,out_file_derotate)
                                retval = shell(cmd)
                            if os.path.isfile(out_file_derotate) and not os.path.isfile(out_file_u):
                                cmd = "cdo selvar,%s %s %s" % (in_var_u,out_file_derotate,out_file_u)
                                retval = shell(cmd)
                            if os.path.isfile(out_file_derotate) and not os.path.isfile(out_file_v):
                                cmd = "cdo selvar,%s %s %s" % (in_var_v,out_file_derotate,out_file_v)
                                retval = shell(cmd)
                            ## remove temp files
                            #if os.path.isfile(out_file):
                                #os.remove(out_file)
                            #if os.path.isfile(out_file_derotate):
                                #os.remove(out_file_derotate)
                        # all other have only U and V inside
                        else:
                            if os.path.isfile(out_file) and not os.path.isfile(out_file_derotate):
                                cmd = "cdo rotuvb,U,V %s %s" % (out_file,out_file_derotate)
                                retval = shell(cmd)
                            if os.path.isfile(out_file_derotate) and not os.path.isfile(out_file_u):
                                cmd = "cdo selvar,U %s %s" % (out_file_derotate,out_file_u)
                                retval = shell(cmd)
                            if os.path.isfile(out_file_derotate) and not os.path.isfile(out_file_v):
                                cmd = "cdo selvar,V %s %s" % (out_file_derotate,out_file_v)
                                retval = shell(cmd)
                        # remove temp files
                        if os.path.isfile(out_file):
                            os.remove(out_file)
                        if os.path.isfile(out_file_derotate):
                            os.remove(out_file_derotate)


# -----------------------------------------------------------------------------
def process_file(params,in_file,var,reslist):
    '''
    process one input file and create one one output file

    call with:
        var: variable name (cf notification)
        res: resolution: 3hr,6hr,day,mon,cm_sem
        cm_type: cell method: sum,mean,max,min,...
        in_file: path to in file
        outdir: output directory (where the complete data goes
    '''

    log.info("####################\n# Var in work: '%s'\n####################" % (var))

    # create object from netcdf file to access all parameters and attributes
    f_in = Dataset(in_file,"r")
    log.info("Input1: %s" % in_file)

    for name in f_in.ncattrs():
        if name in settings.global_attr_file: #only take attribute from file if in this list
            settings.Global_attributes[name] = str(f_in.getncattr(name))

    # get time variable from input
    time_in = f_in.variables['time']

    # get time_bnds variable from input
    #if 'time_bnds' in f_in.variables.keys():
        #time_bnds_in = f_in.variables['time_bnds']

    if 'calendar' in time_in.ncattrs():
        in_calendar = str(time_in.calendar)
    else:
        g_attr = 'driving_model_id'
        if g_attr in f_in.ncattrs():
            if 'MIROC' in f_in.getncattr(g_attr):
                in_calendar = '365_day'
            elif 'CanESM2' in f_in.getncattr(g_attr):
                in_calendar = '365_day'
            elif 'HadGEM2' in f_in.getncattr(g_attr):
                in_calendar = '360_day'
            else:
                in_calendar = 'standard'
        else:
            in_calendar = 'standard'

    # mark for use another time unit
    if settings.use_alt_units: ## and dt_in_year_chk < settings.alt_start_year: # or possible use of: config.use_alt_units:
        time_in_units = config.ALT_UNITS
    else:
        time_in_units = time_in.units

    # now get the 'new' time/date
    dt_in = num2date(time_in[:],time_in_units,calendar=in_calendar)
    dt_in_year = num2date(time_in[0],time_in_units,calendar=in_calendar).year

    switch_infile = False
    for n in range(len(time_in)):
        if num2date(time_in[n],time_in_units,calendar=in_calendar).year == dt_in_year:
            data_max_len = n
        else:
            switch_infile = True
    # add one count
    data_max_len = data_max_len + 1


    if switch_infile == True: ## and dt_in_year_chk < settings.alt_start_year:
        in_file_new = "%s/%s-%s" % (config.DirWork,str(uuid.uuid1()),os.path.basename(in_file))
        # that does not work!!
#        cmd = "cdo -f %s -s selyear,%d %s %s" % (config.get_config_value('settings', 'cdo_nctype'),dt_in_year,in_file,in_file_new)
        # only December istsupported
        t1 = num2date(time_in[0],time_in_units,time_in.calendar)
        t0 = num2date(time_in[0],"days since 1949-12-01 00:00:00",time_in.calendar)
        shift_days = (t1 - t0).days # one month (January): 31
        cmd = "cdo -f %s -s selyear,%d  -shifttime,%ddays -setreftime,%s,%s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),dt_in_year,shift_days,config.get_config_value('settings','alt_units_cdo_date'),config.get_config_value('settings','alt_units_cdo_time'),in_file,in_file_new)
        retval = shell(cmd)
        in_file = in_file_new
        # close old obejct before
        f_in.close()
        # create object from netcdf file to access all parameters and attributes
        f_in = Dataset(in_file,"r")
        log.info("Input1 (new): %s" % in_file)
        # get time variable from input
        time_in = f_in.variables['time']
        if settings.use_alt_units:
            time_in_units = config.ALT_UNITS
        else:
            time_in_units = time_in.units

        # calculate the date range of the file
        dt_in = num2date(time_in[:],time_in_units,calendar=in_calendar)
        # get new year
        dt_in_year = num2date(time_in[0],time_in_units,calendar=in_calendar).year
        for n in range(len(time_in)):
            if num2date(time_in[n],time_in_units,calendar=in_calendar).year == dt_in_year:
                data_max_len = n
        # add one count
        data_max_len = data_max_len + 1

    ## get start and stop date from in_file

    # get first value of array time
    dt_start_in = str(dt_in[0])
    dt_start_in = dt_start_in[:dt_start_in.index(' ')].replace('-','')

    # get last value of array time
    dt_stop_in = str(dt_in[data_max_len-1])
    dt_stop_in = dt_stop_in[:dt_stop_in.index(' ')].replace('-','')
    log.info("Start: %s, stop: %s" % (dt_start_in,dt_stop_in))

    # now create the corretc filenale in temp directory
    # calculate time difference between first two time steps (in hours)
    # in hours: should be 1 or 3 or 6
    a = datetime.strptime(str(dt_in[0]), settings.FMT)
    b = datetime.strptime(str(dt_in[1]), settings.FMT)
    log.info("First time step in input file: %s" % (str(a)))

    tdelta = b - a
    tdelta_seconds = tdelta.seconds
    input_time_step = tdelta_seconds / 3600 + (tdelta.days * 24)
    log.info("Input data time interval: %shourly" % (str(input_time_step)))

    # difference one day: seconds of time delta are '0'!
    if tdelta_seconds == 0:
        tdelta_seconds = tdelta.days * 24 * 3600
    log.info("Time starts at: %s, %s, difference (in seconds) is: %s" % (str(a),str(b),str(tdelta.seconds)))

    # define variables for storing the pathes for mrfso and mrso
    in_file_help = ""
    in_file_org = ""

    new_reslist=list(reslist) #remove resolutions from this list that are higher than the input data resolution
    # process all requested resolutions
    for res in reslist:

        if res in ["1hr","3hr","6hr","12hr"]:
            res_hr=(float(res[:-2])) #extract time resolution in hours
            cm_type = params[config.get_config_value('index','INDEX_VAR_CM_SUB')]
        elif res=="day":
            res_hr=24.
            cm_type = params[config.get_config_value('index','INDEX_VAR_CM_DAY')]
        elif res=="mon":
            res_hr= 28*24.  #minimum number of hours per month
            cm_type = params[config.get_config_value('index','INDEX_VAR_CM_MON')]

        #check if requested time resolution is possible given the input time resolution
        if res_hr < input_time_step:
            log.warning("Requested time resolution (%s) is higher than time resolution of input data (%s hr). Skip this resolution for all following files.." % (res,input_time_step))
            new_reslist.remove(res)
            continue

        # process only if cell method is definded in input matrix
        if cm_type != '':
            log.info("#########################")
            log.info("resolution: '%s'\ncell method: '%s'\ncalendar: '%s'" % (res,cm_type,in_calendar))
            log.info("#########################")
            # out directory
            outdir = get_temp_dir(var,res,cm_type)

            # get file name
            outfile = create_filename(var,res,dt_start_in,dt_stop_in)
            # create complete outpath: outdir + outfile
            outpath = "%s/%s" % (outdir,outfile)
            # skip file if exist

            if os.path.isfile(outpath):
                log.info("Output file exists: %s" % (outpath))
                if not config.get_config_value('boolean','overwrite'):
                    log.info("Skipping...")
                    continue
                else:
                    log.info("Overwriting..")
            log.info("Output to: %s" % (outpath))

            # set step wide of cdo command
            if res == '1hr':
                selhour = "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23"
                nstep = 1 / (tdelta_seconds/3600)
            elif res == '3hr':
                selhour = "0,3,6,9,12,15,18,21"
                nstep = 3 / (tdelta_seconds/3600)
            # 6 hourly data
            elif res == '6hr':
                selhour = "0,6,12,18"
                nstep = 6 / (tdelta_seconds/3600)
            # 12 hourly data
            elif res == '12hr':
                selhour = "0,12"
                nstep = 12 / (tdelta_seconds/3600)
            # daily data
            elif res == 'day':
                nstep = 24 / (tdelta_seconds/3600)
            # yearly data, consider calendar!!
            elif res == 'mon':
                if in_calendar in ('standard','gregorian','proleptic_gregorian','noleap','365_day','julian'):
                    nstep = 365 * 24 / (tdelta_seconds/3600)
                elif in_calendar == '360_day':
                    nstep = 360 * 24 / (tdelta_seconds/3600)
                elif in_calendar in ('366_day','all_leap'):
                    nstep = 366 * 24 / (tdelta_seconds/3600)
            # TODO
            # sem is in extra proc: _proc_seasonal_mean
            #elif res == 'sem':
                #if time.calendar in ('standard','gregorian','proleptic_gregorian','noleap','365_day','julian','all_leap'):
                    #nstep = (365 * 24 / (tdelta_seconds/3600)) / 4
                #elif time.calendar == '360_day':
                    #nstep = (360 * 24 / (tdelta_seconds/3600)) / 4
                #elif time.calendar == '366_day':
                    #nstep = (366 * 24 / (tdelta_seconds/3600)) / 4

            # use VAR_CORR_LIST for reduce the list
            if params[config.get_config_value('index','INDEX_COVERT_FACTOR')] != '' and float(params[config.get_config_value('index','INDEX_COVERT_FACTOR')].strip().replace(',','.')) != 0 \
                    and float(params[config.get_config_value('index','INDEX_COVERT_FACTOR')].strip().replace(',','.')) != 1:
                    #and not var in config.VAR_CORR_LIST:
                cmd_mul = ' -mulc,%s ' % (params[config.get_config_value('index','INDEX_COVERT_FACTOR')].strip().replace(',','.'))
                # to use the time steps from input to correct the conversation factor
                # commented out for now!!
                # TODO
                if params[config.get_config_value('index','INDEX_FRE_AGG')] == 'i' or params[config.get_config_value('index','INDEX_FRE_AGG')] == '':
                    input_time_step = 1
                mulc_factor = float(params[config.get_config_value('index','INDEX_COVERT_FACTOR')].strip().replace(',','.')) / float(input_time_step)
                mulc_factor_str = str(mulc_factor)
                cmd_mul = ' -mulc,%s ' % (mulc_factor_str)
            else:
                cmd_mul = ""
            log.info("mulc factor for variable(%s): %s" % (var,cmd_mul))
            #sys.exit()

            # create help output file which is at the zthe new in_file
            if var in ['mrso','mrfso'] and not os.path.isfile(in_file_help):
                cmd1 = "cdo enssum "
                # use only layer 1 to 8 for the output
                idx_from = 1
                # use value from tabel + 1 as upper limit for the soil levels e.g. 8 + 1 = 9!
                idx_to = int(params[config.get_config_value('index','INDEX_VAL_LEV')].strip()) + 1
                arr = {}
                for i in range(idx_from,idx_to):
                    f_hlp = tempfile.NamedTemporaryFile(dir=config.tmp_dir,delete=False)
                    arr[i] = f_hlp.name
#                    f_hlp = "%s/%s-%d.nc" % (config.tmp_dir,'help',i)
                    retval = shell("cdo -f %s sellevidx,%d %s %s" %(config.get_config_value('settings', 'cdo_nctype'),i,in_file,arr[i]))
                    log.info("%s %s" % (cmd1,arr[i]))
                # ATTENTION
                # now calculate the sum
#                f_hlp = "%s/%s-%s.nc" % (config.tmp_dir,'help','sum')
                f_hlp = tempfile.NamedTemporaryFile(dir=config.tmp_dir,delete=False)
                cmd = "%s %s" % (cmd1,f_hlp.name)
                retval = shell(cmd)
                # multiply with factor 1000 (from csv table)
                # switch from original in_file to the new in_file for these variables
                #in_file = "%s/%s-%s.nc" % (config.tmp_dir,'help','1000')
                in_file_help = "%s/help-%s-%s.nc" % (config.tmp_dir,var,str(uuid.uuid1()))
#                in_file = tempfile.NamedTemporaryFile(dir=config.tmp_dir)
                cmd = "cdo mulc,%d %s %s" % (int(params[config.get_config_value('index','INDEX_COVERT_FACTOR')]),f_hlp.name,in_file_help)
                retval = shell(cmd)
                # remove all help files
                os.remove(f_hlp.name)
                for i in range(idx_from,idx_to):
                    os.remove(arr[i])
                in_file_org = in_file
                in_file = in_file_help

            ftmp_name = "%s/%s-%s.nc" % (settings.DirWork,str(uuid.uuid1()),var)
#            fp_tmp = open(ftmp_name, 'w+')
            # exchange in_file name
            #if var in ['mrso','mrfso'] and os.path.isfile(in_file_help):
                #in_file_org = in_file
                #in_file = in_file_help
            log.info("Cell method: %s" % (cm_type))
            # get type of function to create the output file: point,mean,maximum,minimum,sum
            # extract cell method from string
            t_delim = 'mean over days'
            if t_delim in cm_type:
                cm0 = cm_type[cm_type.index(' '):]
                cm = 'mean' #cm_type[cm_type.index(t_delim)+len(t_delim):]
                cmd = "Cell method used: %s" % (cm0)

            else:
                cm = cm_type
            log.info("Cell method used for cdo command: %s" % (cm))

            # mulc has been already done before!!
            if var in ['mrso','mrfso']:
                cmd_mul = ""

            # 3 / 6 hourly data
            if res == '1hr' or res == '3hr' or res == "6hr":
                if cm == 'point':
                    cmd = "cdo -f %s -s selhour,%s %s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),selhour,cmd_mul,in_file,ftmp_name)
                else:
                    cmd = "cdo -f %s -s timsel%s,%s %s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,nstep,cmd_mul,in_file,ftmp_name)
            # daily data
            elif res == 'day':
                if cm in ['maximum','minimum']:
                    cm1 = cm[:3]
                else:
                    cm1 = cm
                # multiply with constant value from table (only if not 0)
                #if float(params[config.get_config_value('index','INDEX_COVERT_FACTOR].strip().replace(',','.')) != 0 and float(params[config.get_config_value('index','INDEX_COVERT_FACTOR].strip().replace(',','.')) != 1:
                    #cmd_mul = ' -mulc,%s ' % (params[config.get_config_value('index','INDEX_COVERT_FACTOR].strip().replace(',','.'))
                #else:
                    #cmd_mul = ""
                cmd = "cdo -f %s -s day%s %s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm1,cmd_mul,in_file,ftmp_name)
            # monthy data
            elif res == 'mon':
                # get file with daily data from the same input (if exist)
                DayFile = create_filename(var,'day',dt_start_in,dt_stop_in)
                DayPath = "%s/%s" % (get_temp_dir(var,'day',cm_type),DayFile)
                # use day files or prcess this step before
                if os.path.isfile(DayPath):
                    cmd = "cdo -f %s -s mon%s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,DayPath,ftmp_name)
                else:
                    # day and mon: same cell methods (cm)
                    cmd = "cdo -f %s -s -mon%s -day%s %s %s %s" % (config.get_config_value('settings', 'cdo_nctype'),cm,cm,cmd_mul,in_file,ftmp_name)
            # do cmd
            retval = shell(cmd)

            ## move file
            #cmd = "mv %s %s" % (fp_tmp.name,outpath)
            #retval = shell(cmd)

            ## check output file
            #if not os.path.isfile(outpath):
                #log.info("Output file: %s does not exist!" % (outpath))
                ## if not exist for some reason return and go ahead
                #return

            ####################################################
            # open to output file
            ####################################################

            # open ftmp_name for reading
            f_tmp = Dataset(ftmp_name,'r')
            #print "Variables: ",f_tmp.variables.keys()

            # create object for output file
            f_out = Dataset(outpath,'w')

            # create dimensions in target file
            for name, dimension in f_tmp.dimensions.iteritems():
                # skip list items
                if name in settings.varlist_reject:
                    continue
                    #f_out.createDimension(name, len(dimension) if not dimension.isunlimited() else None)
                else:
                    f_out.createDimension(name, len(dimension) if not dimension.isunlimited() else None)

            # set dimension vertices only if set to True in settings file
            if config.get_config_value('boolean','add_vertices') == True:
                f_out.createDimension('vertices',4)
                log.info("Add vertices")

            # copy variables from temp file
            for var_name in f_tmp.variables.keys():
                # don't copy time_bnds if cm == point or variable time_bnds
                if cm == 'point' and var_name == 'time_bnds': # or var_name == 'pressure':
                    continue
                var_in = f_tmp.variables[var_name]
                # create output variable
                if var_name in ['rlon','rlat']:
                    data_type = 'd'
                elif var_name in ['lon','lat']:
                    data_type = 'd'
                elif var_name in settings.varlist_reject:
                    continue
                    #data_type = 'i8'
                else:
                    data_type = var_in.datatype
                # at variable creation set fill_vlue, later is impossible
                # also set the compression
                if config.get_config_value('boolean','nc_compress') == True:
                    log.info("COMPRESS variable: %s" % (var_name))
                else:
                    log.info("NO COMPRESS")
                # skip 'pressure'!!
                my_lst = []
                for dim in var_in.dimensions:
                    if str(dim) not in settings.varlist_reject:
                        my_lst.append(dim)
                var_dims = tuple(my_lst)
                log.info("Dimensions (of variable %s): %s" % (var_name,str(var_dims)))
                log.info("Attributes (of variable %s): %s" % (var_name,var_in.ncattrs()))
                if var_name in [var,settings.netCDF_attributes['RCM_NAME_ORG']]:
                    if config.get_config_value('boolean','nc_compress') == True:
                        var_out = f_out.createVariable(var_name,datatype=data_type,
                            dimensions=var_dims,complevel=4,fill_value=settings.netCDF_attributes['missing_value'])
                    else:
                        var_out = f_out.createVariable(var_name,datatype=data_type,
                            dimensions=var_dims,fill_value=settings.netCDF_attributes['missing_value'])
                    log.info("FillValue(output): %s,%s" % (var_name,var_out._FillValue))
                else:
                    if config.get_config_value('boolean','nc_compress') == True:
                        var_out = f_out.createVariable(var_name,datatype=data_type,dimensions=var_dims,complevel=4)
                    else:
                        var_out = f_out.createVariable(var_name,datatype=data_type,dimensions=var_dims)
                #if '_FillValue' in var_in.ncattrs() and var_in._FillValue < 0:
                    #correct_fillvalue = True
                log.info("Dimensions (of variable %s): %s" % (var_name,str(f_out.dimensions)))
                # set all character fields as character converted with str() function
                # create attribute list
                if var_name in ['lat','lon']:
                    att_lst = get_attr_list(var_name)
                else:
                    att_lst = {}
                    for k in var_in.ncattrs():
                        if k != '_FillValue':
                            if isinstance(var_in.getncattr(k),unicode):
                                att_lst[k] = str(var_in.getncattr(k))
                            else:
                                att_lst[k] = var_in.getncattr(k)
                var_out.setncatts(att_lst)

                # copy content to new datatype
                var_out[:] = var_in[:]
                log.info("Copy from tmp: %s" % (var_out.name))
                if var_out.name == 'time':
                    if 'calendar' in var_out.ncattrs():
                        if var_out.getncattr('calendar') != in_calendar:
                            var_out.calendar = in_calendar
                        else:
                            var_out.calendar = str(var_out.getncattr('calendar'))
                    elif 'bounds' in var_out.ncattrs():
                        var_out.bounds = str(var_out.getncattr('bounds'))
                        var_out.setncattr('test_bounds1',var_out.getncattr('bounds'))
                        var_out.test_bounds2 = var_out.getncattr('bounds')
                    elif 'standard_name' in var_out.ncattrs():
                        var_out.standard_name = str(var_out.getncattr('standard_name'))

            # copy lon/lat and rlon/rlat from input if needed:
            for var_name in f_in.variables.keys():
                # take only the variables lat and lon
                if (var_name in ['lon','lat','rlon','rlat'] and var_name in f_in.variables.keys() and
                            var_name not in f_out.variables.keys() ):
                    var_in = f_in.variables[var_name]
                    #print "IN: ",var_name, var_in.dimensions
                    #print "OUT: ",var_name,f_out.dimensions()
                    j = 0
                    for var_dim in var_in.dimensions:
                        if var_dim not in f_out.dimensions:
                            #print "CREATE DIM ",var_dim,len(var_dim),len(var_in),var_in.shape[j]
                            f_out.createDimension(var_dim,size=var_in.shape[j])
                        j = j + 1
                    if var_name in ['rlon','rlat']:
                        data_type = 'd'
                    elif var_name in ['lon','lat']:
                        data_type = 'd'
                    elif var_name in settings.varlist_reject:
                        continue
                    # create output variable
                    var_out = f_out.createVariable(var_name,datatype=data_type,dimensions=var_in.dimensions)
                    # set all character fields as character converted with str() function
                    # create attribute list
                    if var_name in ['lat','lon']:
                        att_lst = get_attr_list(var_name)
                    else:
                        att_lst = {}
                        for k in var_in.ncattrs():
                            if isinstance(var_in.getncattr(k),unicode):
                                att_lst[k] = str(var_in.getncattr(k))
                            else:
                                att_lst[k] = var_in.getncattr(k)
                    var_out.setncatts(att_lst)
                    # copy content to new datatype
                    var_out[:] = var_in[:]
                    log.info("Copy from input: %s" % (var_out.name))
#            sys.exit()

            ##############################
            # now correct time,time_bnds #
            ##############################

            # get time and time_bnds variables from output
            time = f_out.variables['time']
            # only if not point
            if cm != 'point':
                time_bnds = f_out.variables['time_bnds']

            # get length of data array (== length of time array and length of time_bnds array
            try:
                data_len = f_out.variables[settings.netCDF_attributes['RCM_NAME_ORG']].shape[0]
            except:
                data_len = f_out.variables[settings.netCDF_attributes['cf_name']].shape[0]
            data_len = min(data_len,data_max_len)
            log.info("Date len: %s" % str(data_len))

            #TODO  use/no use of time_bnds??

            # get time_bnds variable from input
            if 'time_bnds' in f_in.variables.keys():
                time_bnds_in = f_in.variables['time_bnds']
                # get first time step in input file to distingish ref date
                date_start = num2date(time_bnds_in[0,0],time_in_units,in_calendar)
            else:
                date_start = num2date(time_in[0],time_in_units,in_calendar)

            # first time step
            #date_start = num2date(time_in[0],time_in_units,in_calendar)

            # check first lower time_bound if exist
            if date_start.year < dt_in_year:
                if 'time_bnds' in f_in.variables.keys():
                    # or first time_bound lower value
                    date_start = num2date(time_bnds_in[0,0],time_in_units,in_calendar)
                else:
                    # or second time step
                    date_start = num2date(time_in[1],time_in_units,in_calendar)
            # check first upper time_bound if exist
            if date_start.year < dt_in_year:
                if 'time_bnds' in f_in.variables.keys():
                    # or first time_bound higher value
                    date_start = num2date(time_bnds_in[0,1],time_in_units,in_calendar)

            # if year of first time step still not in actual year: search time steps until actual year
            n = 1
            while date_start.year < dt_in_year and n < len(time_in):
                # next time step
                date_start = num2date(time_in[n],time_in_units,in_calendar)
                # increment index
                n += 1

            # move the reference date to 1949-12-01T00:00:00Z
            # by setting time:units to: "days since 1949-12-01T00:00:00Z"
            time.units = config.get_config_value('settings','units')
            # now get the difference in time.units for refdate: start point for all settings in time and time_bnds
            num_refdate_diff = date2num(date_start,time.units,calendar=in_calendar)

            # show some numbers
            log.info("num_refdate_diff: %s" % str(num_refdate_diff))

            # start always with time = 00:00:00
            if date_start.hour > 0:
                num_refdate_diff = float(int(num_refdate_diff))
                log.warning("Set time of start date (%s) to 00:00!" % str(date_start))

            # show some numbers
            log.info("Startdate for time settings: %s, %s" % (str(num_refdate_diff),str(num2date(num_refdate_diff,time.units,calendar=in_calendar))))

            if res == '1hr':
                num = 1. / 24.
                # set time and time_bnds
                if cm != 'point':
                    log.info("Start for time_bnds: %s, %s",str(num_refdate_diff),str(num2date(num_refdate_diff,time.units,time.calendar)))
                    for n in range(data_len):
                        time_bnds[n,0] = num_refdate_diff + (n * num)
                        time_bnds[n,1] = num_refdate_diff + ((n + 1) * num)
                        time[n] = (time_bnds[n,0] + time_bnds[n,1]) / 2.0
                else:
                    # set time
                    for n in range(data_len):
                        time[n] = num_refdate_diff + n * num
            elif res == '3hr':
                num = 0.125
                # set time and time_bnds
                if cm != 'point':
                    log.info("Start for time_bnds: %s, %s",str(num_refdate_diff),str(num2date(num_refdate_diff,time.units,time.calendar)))
                    for n in range(data_len):
                        time_bnds[n,0] = num_refdate_diff + (n * num)
                        time_bnds[n,1] = num_refdate_diff + ((n + 1) * num)
                        time[n] = (time_bnds[n,0] + time_bnds[n,1]) / 2.0
                else:
                    # set time
                    for n in range(data_len):
                        time[n] = num_refdate_diff + n * num
            elif res == '6hr':
                num = 0.25
                # set time and time_bnds
                if cm != 'point':
                    log.info("Start for time_bnds: %s, %s",str(num_refdate_diff),str(num2date(num_refdate_diff,time.units,time.calendar)))
                    for n in range(data_len):
                        time_bnds[n,0] = num_refdate_diff + (n * num)
                        time_bnds[n,1] = num_refdate_diff + ((n + 1) * num)
                        time[n] = (time_bnds[n,0] + time_bnds[n,1]) / 2.0
                else:
                    # set time
                    for n in range(data_len):
                        time[n] = num_refdate_diff + n * num
            elif res == '12hr':
                num = 0.5
                # set time and time_bnds
                if cm != 'point':
                    log.info("Start for time_bnds: %s, %s",str(num_refdate_diff),str(num2date(num_refdate_diff,time.units,time.calendar)))
                    for n in range(data_len):
                        time_bnds[n,0] = num_refdate_diff + (n * num)
                        time_bnds[n,1] = num_refdate_diff + ((n + 1) * num)
                        time[n] = (time_bnds[n,0] + time_bnds[n,1]) / 2.0
                else:
                    # set time
                    for n in range(data_len):
                        time[n] = num_refdate_diff + n * num
            elif res == 'day':
                num = 1.
                for n in range(data_len):
                    time_bnds[n,0] = num_refdate_diff + (n * num)
                    time_bnds[n,1] = num_refdate_diff + ((n + 1) * num)
                    time[n] = (time_bnds[n,0] + time_bnds[n,1]) / 2.0
            # TODO, monthly settings
            elif res == 'mon':
                # n: 0,1,...11!!
                start = num_refdate_diff
                # only 12 month a year!!
                for n in range(data_len):
                    time_bnds[n,0] = num_refdate_diff
                    log.info("bnds1: %s" % (num2date(num_refdate_diff,time.units,calendar=in_calendar)))

                    #d = num2date(time[n],time.units,time.calendar)
                    d = num2date(num_refdate_diff,time.units,calendar=in_calendar)
                    # only 12 month!
                    m = n % 12
#                    print m,m+1,data_len,time.calendar,d
                    days = settings.dpm[time.calendar][m+1]
                    # add one day in February of leap year
                    if leap_year(d.year,time.calendar) and m == 1:
                        days += 1
                    log.info("Add DAYs: %d,%d,%d" % (days,d.year,d.month))

                    num_refdate_diff += days
                    log.info("bnds2: %s" % (num2date(num_refdate_diff,time.units,calendar=in_calendar)))
                    time_bnds[n,1] = num_refdate_diff
                    time[n] = (time_bnds[n,0] + time_bnds[n,1]) / 2.0
                end = num_refdate_diff
                log.info("time_bnds difference: %s" % (str(end - start)))

            # commit changes
            f_out.sync()

            ###################################
            # do some additional settings
            ###################################
            # rename variable
            try:
                f_out.renameVariable(settings.netCDF_attributes['RCM_NAME_ORG'],settings.netCDF_attributes['cf_name'])
            except:
                log.info("Variable has cf name already: %s" % (var))

            # no time_bnds if cell method is 'point'
            if cm == 'point':
                f_var = f_out.variables['time']
                try:
                    f_var.delncattr('bounds')
                except:
                    log.info("Attribute %s not available for variable %s." % ('bounds','time'))

            if int(params[config.get_config_value('index','INDEX_VAL_LEV')].strip()) > 0 and not var in ['mrfso','mrro']:
                if params[config.get_config_value('index','INDEX_MODEL_LEVEL')] == config.get_config_value('settings','PModelType'):
                    if not 'plev' in f_out.variables:
                        var_out = f_out.createVariable('plev',datatype='d')
                        var_out.units = "Pa"
                        var_out.axis = "Z"
                        var_out.positive = "down"
                        var_out.long_name = "pressure"
                        var_out.standard_name = "air_pressure"
                        var_out[0] = params[config.get_config_value('index','INDEX_VAL_PLEV')]
                    # model level variable
                elif params[config.get_config_value('index','INDEX_MODEL_LEVEL')] == config.get_config_value('settings','MModelType'):
                    if not 'height' in f_out.variables:
                        var_out = f_out.createVariable('height',datatype='d')
                        var_out.units = "m"
                        var_out.axis = "Z"
                        var_out.positive = "up"
                        var_out.long_name = "height"
                        var_out.standard_name = "height"
                        var_out[0] = params[config.get_config_value('index','INDEX_VAL_HEIGHT')]

            # set all predefined global attributes
            #print settings.Global_attributes
            f_out.setncatts(settings.Global_attributes)
            log.info("Global attributes set!")

            # commit changes
            f_out.sync()

            # exist in some output (e.g. CCLM) in CORDEX, default: False
            if config.get_config_value('boolean','add_vertices') == True:
                add_vertices(f_out)

            # create variable object to output file
            f_var = f_out.variables[settings.netCDF_attributes['cf_name']]
            # set additional variables attributes
            f_var.standard_name = settings.netCDF_attributes['standard_name']
            f_var.long_name = settings.netCDF_attributes['long_name']
            f_var.units = settings.netCDF_attributes['units']
            if params[config.get_config_value('index','INDEX_CM_AREA')]=='':
                f_var.cell_methods = "time: %s" % (cm_type)
            else:
                f_var.cell_methods = "time: %s area: %s" % (cm_type,params[config.get_config_value('index','INDEX_CM_AREA')])

            # check wether lon/lat exist
#            print f_out.variables,not 'lon' in f_out.variables,not 'lat' in f_out.variables
            if not 'lon' in f_out.variables and not 'lat' in f_out.variables:
                # add lon/lat
                add_coordinates(f_out)

            # set attribute coordinates
            set_coord_attributes(params,f_var,f_out)

            # set attribute missing_value
            f_var.missing_value = settings.netCDF_attributes['missing_value']

            try:
                f_var.setncattr('grid_mapping','rotated_pole')
            except:
                log.warning("Variable '%s' does not exist." % ("rotated_pole"))

            # commit changes
            f_out.sync()

            # close output file
            f_out.close()

            # remove help file
            os.remove(ftmp_name)

            # set attributes: frequency,tracking_id,creation_date
            set_attributes_create(outpath,res)

            # ncopy file to correct output format
            if config.get_config_value('boolean','nc_compress') == True:
                compress_output(outpath,params[config.get_config_value('index','INDEX_FRE_DAY')])
            log.info("Variable attributes set!")

            # close tmp file
#            fp_tmp.close()

            # now correct missing_value (is actual negativ
            # TODO: set additional correct list?
            #if (correct_fillvalue == True or var in ['mrfso','mrro','mrros','mrso','snw']) and os.path.isfile(outpath):
                #_FillValue = config._parser.getfloat('settings','missing_value')
                #cmd = "ncatted -h -O -a missing_value,%s,m,f,-%s -a _FillValue,%s,m,f,-%s %s" %  (var,_FillValue,var,_FillValue,outpath)
                #retval = shell(cmd)
                #cmd = "ncatted -h -O -a missing_value,%s,m,f,%s -a _FillValue,%s,m,f,%s %s" %  (var,_FillValue,var,_FillValue,outpath)
                #retval = shell(cmd)

            ## ATTENTION: 'in_file' is only to be deleted here for these variables, otherwise it is read-only!!
            #if var in ['mrso','mrfso']:
                #in_file = in_file_org
                #os.remove(in_file_help)
            # only on file
            #sys.exit()
        else:
            cmd = "No cell method set for this variable (%s) and time resolution (%s)." % (var,res)
            log.warning(cmd)
        log.info("Input3: %s" % in_file)
        #sys.exit()

    # ATTENTION: 'in_file' is only to be deleted here for these variables, otherwise it is read-only!!
    if var in ['mrso','mrfso'] and os.path.isfile(in_file_org):
        try:
            in_file = in_file_org
            os.remove(in_file_help)
        except:
            cmd = "Could not remove file: %s" % (in_file)
            log.warning(cmd)
    if switch_infile == True and os.path.isfile(in_file):
        try:
            os.remove(in_file)
        except:
            cmd = "Could not remove file: %s" % (in_file)
            log.warning(cmd)

    # close input file
    f_in.close()
    # ready message
    log.info("Variable '%s' finished!" % (var))
    return new_reslist


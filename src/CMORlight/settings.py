# settings.py

import csv
import configuration as config
#import sys

def init(varfile):
    '''
        set global variables
    '''
    global logger_name
    logger_name = config.get_config_value('settings', 'logger_name')

    # base path for all other path
    global BasePath
    BasePath = config.get_config_value('settings', 'BasePath')

    #
    # Basic path to the archive (system dependent)
    #
    global DirIn
    DirIn = ("%s/%s" % (BasePath,config.get_config_value('settings', 'DirIn')))

    global DirOut
    DirOut = ("%s/%s" % (BasePath,config.get_config_value('settings', 'DirOut')))

    global DirProg
    DirProg = ("%s/%s" % (BasePath,config.get_config_value('settings', 'DirProg')))

    global DirConfig
    DirConfig = ("%s/%s" % (DirProg,config.get_config_value('settings', 'DirConfig')))

    global DirWork
    DirWork = ("%s/%s" % (BasePath,config.get_config_value('settings', 'DirWork')))

    global DirLog
    DirLog = ("%s/%s" % (BasePath,config.get_config_value('settings', 'DirLog')))

    global DirOutRotated
    DirOutRotated = ("%s/%s/%s" % (BasePath,config.get_config_value('settings', 'DirOutRotated'),config.get_config_value('settings','model')))

    global global_attr_list
    global_attr_list = config.get_config_value('settings','global_attr_list').split(',')

    global global_attr_file
    global_attr_file = config.get_config_value('settings','global_attr_file').split(',')

    global varlist_reject
    varlist_reject =  config.get_config_value('settings', 'varlist_reject').split(',')

    global var_skip_list
    var_skip_list =  config.get_config_value('settings', 'var_skip_list').split(',')

    global search_input_string
    search_input_string = config.get_config_value('settings','search_input_string')

    global FMT
    FMT = '%Y-%m-%d %H:%M:%S'

    global vertices_file
    vertices_file = ("%s/%s" % (DirProg,config.get_model_value('vertices_file')))

    global coordinates_file
    coordinates_file = ("%s/%s" % (DirProg,config.get_model_value('coordinates_file')))

    # dictionary for global attributes
    global Global_attributes
    Global_attributes = {}

    # dictionary for additional netcdf atributes
    global netCDF_attributes
    netCDF_attributes = {}

    global use_version
    use_version = ''

    global use_alt_units
    use_alt_units = config.get_config_value('boolean','use_alt_units')

    global alt_start_year
    alt_start_year = config.get_config_value('integer','alt_start_year')

    global param
    param = {}
    with open(varfile,'rb') as csvfile:
        reader = csv.reader(csvfile,delimiter=';')
        for row in reader:
            if row[config.get_config_value('index','INDEX_RCM_NAME_ORG')] != '' and row[config.get_config_value('index','INDEX_VAR')] != '':
                #create dictionary entries for variables names of CORDEX as well as of the RCM
                param[row[config.get_config_value('index','INDEX_VAR')]] = row
                param[row[config.get_config_value('index','INDEX_RCM_NAME')]] = row
            #if row[config.INDEX_VAR] == variable:
                #return row

    global dpm
    dpm = {'noleap':          [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       '365_day':             [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       'standard':            [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       'gregorian':           [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       'proleptic_gregorian': [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       'all_leap':            [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       '366_day':             [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       '360_day':             [0, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]}

#    print __name__

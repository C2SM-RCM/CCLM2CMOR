"""

Processes some of the entries in the configuration file: builds directory paths and lists
reads in the variables table

"""


import csv
import get_configuration as config
from collections import OrderedDict

def init(vartable):
    '''
    Set global variables and read the variables table vartable
    '''
    # base path for all other path
    global BasePath
    BasePath = config.get_config_value('settings', 'BasePath',exitprog=False)
    if BasePath[-1]=="/":
        BasePath = BasePath[:-1]
    global DataPath
    DataPath = config.get_config_value('settings', 'DataPath',exitprog=False)
    if DataPath[-1]=="/":
        DataPath = DataPath[:-1]


    global DirIn
    DirIn = ("%s/%s" % (DataPath,config.get_config_value('settings', 'DirIn')))

    global DirOut
    DirOut = ("%s/%s" % (DataPath,config.get_config_value('settings', 'DirOut')))

    global DirConfig
    DirConfig = ("%s/%s" % (BasePath,config.get_config_value('settings', 'DirConfig')))

    global DirWork
    DirWork = ("%s/%s" % (DataPath,config.get_config_value('settings', 'DirWork')))

    global DirLog
    DirLog = ("%s/%s" % (BasePath,config.get_config_value('settings', 'DirLog')))

    global DirDerotated
    DirDerotated = ("%s/%s" % (DataPath,config.get_config_value('settings', 'DirDerotated')))

    global global_attr_list
    global_attr_list = config.get_config_value('settings','global_attr_list').split(',')

    global global_attr_file
    global_attr_file = config.get_config_value('settings','global_attr_file',exitprog=False).split(',')

    global varlist_reject
    varlist_reject =  config.get_config_value('settings', 'varlist_reject').split(',')

    global var_skip_list
    var_skip_list =  config.get_config_value('settings', 'var_skip_list',exitprog=False).split(',')

    global var_list_fixed
    var_list_fixed =  config.get_sim_value('var_list_fixed',exitprog=False).split(',')

    global varlist
    varlist =  config.get_config_value('settings','varlist',exitprog=False).split(',')

    global FMT
    FMT = '%Y-%m-%d %H:%M:%S'

    global vertices_file
    vertices_file = ("%s/%s" % (DirConfig,config.get_sim_value('vertices_file', exitprog = False)))

    global coordinates_file
    coordinates_file = ("%s/%s" % (DirConfig,config.get_sim_value('coordinates_file')))

    # dictionary for global attributes
    global Global_attributes
    Global_attributes = OrderedDict()

    # dictionary for additional netcdf atributes
    global netCDF_attributes
    netCDF_attributes = OrderedDict()

    global use_version
    use_version = ''

    global param
    param = {}
    with open(DirConfig+"/"+vartable,'rt') as csvfile:
        reader = csv.reader(csvfile,delimiter=';')
        for i,row in enumerate(reader):
            if i==0: # skip header
                continue
            var=row[config.get_config_value('index','INDEX_VAR')]
            if row[config.get_config_value('index','INDEX_RCM_NAME_ORG')] != '' and var != '':
                #create dictionary entries for variables names of CORDEX as well as of the RCM
                param[var] = row
                if var!="prhmax": #as RCM name in table is equal to pr
                    param[row[config.get_config_value('index','INDEX_RCM_NAME')]] = row


    global dpm
    dpm = {'noleap':          [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       '365_day':             [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       'standard':            [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       'gregorian':           [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       'proleptic_gregorian': [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       'all_leap':            [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       '366_day':             [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
       '360_day':             [0, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]}


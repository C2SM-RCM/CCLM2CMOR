#!/bin/env python
#
# creates CORDEX standard CMOR compliant output from preprocessed input
#
#import logging as log
import os
import sys

# netcdf4 Library
from netCDF4 import Dataset
from netCDF4 import num2date
from netCDF4 import date2num
#from netCDF4 import date2index

from datetime import datetime
#from datetime import timedelta

# command line parser
from optparse import OptionParser

# configuration
import configuration as config

# temp file functions
import tempfile

# uuid support
import uuid

# global settings
import settings

# tools library
import tools

# basic setting for logging
import __init__ as base

import logging
log = logging.getLogger('cmorlight')

# -----------------------------------------------------------------------------
def process_resolution(params,reslist):
    ''' '''
    # get cdf variable name
    var = params[config.get_config_value('index','INDEX_VAR')]
    varRCM=params[config.get_config_value('index','INDEX_RCM_NAME')]
    # get cell method for the resolution
    # process resolution with the cell method: cm_...

    # create path to input files from basedir,model,driving_model
    in_dir = "%s/%s" % (tools.get_input_path(var),params[config.get_config_value('index','INDEX_RCM_NAME')])
    log.info("Looking for input dir(1): %s" % (in_dir))
    if os.path.isdir(in_dir) == False:
      log.info("Input directory does not exist(0): %s \n \t Change base path in .ini file or create directory! " % in_dir)
      return
       # if params[config.get_config_value('index','INDEX_RCM_NAME')].find('p') > 0:
        #    in_dir = "%s/%s" % (config.get_input_path(var),params[config.get_config_value('index','INDEX_RCM_NAME')][:params[config.get_config_value('index','INDEX_RCM_NAME')].find('p')])
         #   log.info("Now looking for input dir: %s" % (in_dir))
          #  if os.path.isdir(in_dir) == False:
              # log.info("Input directory does not exist(1): %s" % in_dir)
                #return
   # if os.path.isdir(in_dir) == False:
   #     in_dir = "%s" % (tools.get_input_path(var))
    #    log.info("Looking for input dir(2): %s" % (in_dir))
    #if os.path.isdir(in_dir) == False:
     #   log.warning("Input directory does not exist(2): %s" % in_dir)
      #  return
    log.info("Used dir: %s" % (in_dir))
    for dirpath,dirnames,filenames in os.walk(in_dir, followlinks=True):
        for f in sorted(filenames):
            if f.find("%s_" % var) == 0 or f.find("%s_" % varRCM) == 0 or f.find("%s_" % varRCM[:varRCM.find('p')]) == 0:
                in_file = "%s/%s" % (dirpath,f)
                if os.path.isfile(in_file):
                    # workaround for error in last input files of CCLM data from DWD
                    # use only file with e.g. _2100 in filename (only if USE_SEARCH==True)
                    if config.get_config_value('settings', 'use_search_string') and in_file.find(settings.search_input_string) < 0:
                        continue
                    log.info("Input from: %s" % (in_file))
                    #try:
                    if os.access(in_file, os.R_OK) == False:
                        log.error("Could not read file '%s', no permission!" % in_file)
                    else:
                        log.info("############################### %s" % (str(var in config.get_model_value('settings_CCLM','var_list_fixed'))))
                        if var in config.get_model_value('settings_CCLM','var_list_fixed'):
                            tools.process_file_fix(params,in_file)
                        else:
                            tools.process_file(params,in_file,var,reslist)
                else:
                    log.error("File '%s' not found!" % in_file)
#            else:
#                if f.find("%s" % var) == 0 or f.find("%s" % varRCM) == 0 or f.find("%s" % varRCM[:varRCM.find('p')]) == 0:
#                    in_file = "%s/%s" % (dirpath,f)
#                    if os.path.isfile(in_file):
#                        if var in config.get_model_value('settings_CCLM','var_list_fixed'):
#                            tools.proc_file_fix(params,in_file)

            # stop after one file with all chosen resolutions if set
            if config.get_config_value('boolean','test_only_one_file') == True:
                sys.exit()
    return True


# -----------------------------------------------------------------------------
def main():
    ''' main program, first read command line parameter '''

    parser = OptionParser(version="%prog "+base.__version__) #VERSION)

    parser.add_option("-i", "--ini",
                            action="store", dest = "inifile", default = "control_cmor2.ini",
                            help = "script ini file")
    parser.add_option("-p", "--param",
                            action="store", dest = "paramfile", default = "",
                            help = "model parameter file")
    parser.add_option("-r", "--resolution",
                            action="store", dest = "reslist", default = "",
                            help = "process output resolution")
    parser.add_option("-v", "--varlist",
                            action="store", dest = "varlist", default = "pr",
                            help = "process variable")
    parser.add_option("-a", "--all",
                            action="store_true", dest = "all_vars", default = False,
                            help = "process all vars")
    parser.add_option("-c", "--chunk-var",
                            action="store_true", dest="chunk_var", default = False,
                            help="go call chunking for the variable list")
    parser.add_option("-s", "--seasonal-mean",
                            action="store_true", dest="seasonal_mean", default=False,
                            help="go calculate seasonal mean from aggregated monthly data")
    parser.add_option("-n", "--use-version",
                            action="store", dest = "use_version", default = tools.new_dataset_version(),
                            help = "version for drs (default: today in format YYYYMMDD)")
    parser.add_option("-d", "--derotate-uv",
                            action="store_true", dest = "derotate_uv", default=False,
                            help = "derotate all u and v avariables")
    parser.add_option("-t", "--test-var",
                            action="store_true", dest="test_var", default = False,
                            help="test possible resolution for all vars")
    parser.add_option("-k", "--corr-var",
                            action="store_true", dest="corr_var", default = False,
                            help="correct variable by corr_key")
    parser.add_option("-o", "--corr-key",
                            action="store", dest="corr_key", default = "climatology",
                            help="correct key to select a function")
    parser.add_option("-y", "--alt-start-year",
                            action="store", dest="alt_start_year", default = 2100,
                            help="use alternate start year")
    parser.add_option("-u", "--use-alt-units",
                            action="store_true", dest="use_alt_units", default = False,
                            help="use alternate units for input data (only day and mon)")
    parser.add_option("-m", "--model",
                           action="store", dest="act_model", default = 'CCLM',
                          help="set used model (supported: [default: CCLM],WRF)")
    parser.add_option("-g", "--gcm_driving_model",
                            action="store", dest="driving_model_id", default = "",
                            help="set used driving model")
    parser.add_option("-x", "--experiment",
                            action="store", dest="driving_experiment_name", default = "",
                            help="set used experiment")
    parser.add_option("-e", "--ensemble",
                            action="store", dest="driving_model_ensemble_member", default = "",
                            help="set used ensemble")
    parser.add_option("-O", "--overwrite",
                            action="store_true", dest="overwrite", default = False,
                            help="Overwrite existent output files")

    (options, args) = parser.parse_args()
    options_dict=vars(options)
    config.load_configuration(options.inifile)

#    if options.act_model not in ['CCLM','WRF']:
 #       log.error("Model ist not supported: '%s'" % (options.act_model))
  #      # end programm
   #     return

   #store parsed arguments in config
    setval=["paramfile","driving_model_id","driving_experiment_name","driving_model_ensemble_member"]

    for val in setval:
        if options_dict[val]!="":
            config.set_config_value('settings_CCLM',val,options_dict[val])

    config.set_config_value('init','model',options.act_model)
    config.set_config_value('boolean','overwrite',str(options.overwrite))

    process_list=[config.get_config_value('settings_CCLM','driving_model_id'),config.get_config_value('settings_CCLM','driving_experiment_name'),config.get_config_value('settings_CCLM','driving_model_ensemble_member')]
    # now read paramfile for all variables for this RCM
    varfile = ("%s/%s" % (config.get_config_value('settings','DirConfig'),config.get_config_value('settings_CCLM','paramfile')))
    settings.init(varfile)

    # create logger
    LOG_BASE = settings.DirLog
    if os.path.isdir(LOG_BASE) == False:
        print("Logging directory does not exist: %s" % LOG_BASE)
        os.makedirs(LOG_BASE)
        if os.path.isdir(LOG_BASE) == True:
            print("Logging directory created: %s" % LOG_BASE)
    LOG_FILENAME = os.path.join(LOG_BASE,base.logfile)

    # get logger and assign logging filename
    log = base.setup_custom_logger(settings.logger_name,filename=LOG_FILENAME)


    # creating working directory if not exist
    if not os.path.isdir(settings.DirWork):
        log.warning("Working directory does not exist, creating: %s" % (settings.DirWork))
        os.makedirs(settings.DirWork)

    if not os.path.isdir(settings.DirOut):
        log.info("Output directory does not exist, creating: %s" % (settings.DirOut))
        os.makedirs(settings.DirOut)

    # assing some new parameter
    settings.use_version = "v%s" % (options.use_version)
    settings.use_alt_units = options.use_alt_units
    # derotate u and v
    if options.derotate_uv == True:
        tools.derotate_uv()
        return

    if options.all_vars == False:
        varlist = options.varlist.split(',')
    else:
        varlist = [] #config.varlist['3hr'] + config.varlist['6hr']
        varlist.extend(tools.get_var_lists(flt=None))


    if options.reslist=="": #if output resolutions not given in command -> take from inifile
        reslist=config.get_config_value('settings','reslist').replace(" ",",") #to allow for space as delimiter
        reslist=list(filter(None,reslist.split(','))) #split string and remove empty strings
    else:
        reslist = options.reslist.split(',')
    #TODO: allow for whitespace separation -> need to change in optparse
    #reslist = options.reslist.replace(" ",",") #to allow for space as delimiter
    #reslist=list(filter(None,reslist.split(','))) #split string and remove empty strings


    # if nothing is set: exit the program
    if len(reslist) == 1 and reslist[0] == '' and options.seasonal_mean == False and options.test_var == False:
        log.error("No output resolution/aggregation set, exiting...")
        return

    # test modus
    if options.test_var == True:
        tools.proc_test_var(process_list,varlist,reslist)
        return

    log.info("Configuration read from: %s" % os.path.abspath(varfile))
    log.info("Variable(s): %s " % varlist)
    log.info("Requested time output resolution(s): %s " % reslist)
    log.info("Used RCM: %s" % config.get_config_value('init','model'))

    # process all var in varlist with input model and input experiment for proc_list item
    for var in varlist:
        if settings.param.has_key(var) == False:
            log.warning("Variable '%s' not supported!" % (var))
            continue
        else:
            # get parameter for next variable in the list
            params = settings.param[var]
            log.info("Used parameter for variable '%s': %s" % (var,params))
        if params:
            # set global attributes in the dictionary
            tools.set_attributes(params,process_list)

            # skip fixed fields from chunking, makes no sense to chunk
            if options.chunk_var == True and not var in config.get_model_value('settings_CCLM','var_list_fixed'):
                tools.proc_chunking(params,reslist)

            # seasonal mean
            elif options.seasonal_mean == True:
                tools.proc_seasonal_mean(params)

            # some procs for correction or cleanup files later
            elif options.corr_var == True:
                for res in reslist:
                    tools.proc_corr_var(params,res,key=options.corr_key)

            # process all vars from varlist with all output resolutions from reslist
            else:
                for res in reslist:
                    if tools.check_resolution(params,res) == False:
                        reslist.remove(res) #remove unsupported resolution from list

                process_resolution(params,reslist)


#########################################################
#  main program if class isn't called from other script
#########################################################
if __name__ == "__main__":
    ''' main program '''

    # call main function
    main()
    log = logging.getLogger('cmorlight')
    log.propagate = True
    log.info('##################################')
    log.info('########  End of script.  ########')
    log.info('##################################')
    ######################
    # END of program!!!  #
    ######################


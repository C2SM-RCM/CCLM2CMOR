#!/bin/env python
#
# creates CORDEX standard CMOR compliant output from preprocessed input
#
import os
import sys
import shutil

# netcdf4 Library
from netCDF4 import Dataset
from netCDF4 import num2date
from netCDF4 import date2num
#from netCDF4 import date2index

from datetime import datetime
#from datetime import timedelta

#for multiprocessing
from multiprocessing import Process,Pool

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
log = logging.getLogger("cmorlight")

# -----------------------------------------------------------------------------
def process_file_unpack(args):
    '''Helper function for multiprocessing to unpack arguments before using pool.map'''
    return tools.process_file(*args)

def process_resolution(params,reslist):
    ''' '''
    log = logging.getLogger("cmorlight")

    # get cdf variable name
    var = params[config.get_config_value('index','INDEX_VAR')]
    varRCM=params[config.get_config_value('index','INDEX_RCM_NAME')]
    # create path to input files from basedir,model,driving_model
    in_dir = "%s/%s" % (tools.get_input_path(var),params[config.get_config_value('index','INDEX_RCM_NAME')])
    log.debug("Looking for input dir(1): %s" % (in_dir))
    if os.path.isdir(in_dir) == False:
      log.error("Input directory does not exist(0): %s \n \t Change base path in .ini file or create directory! " % in_dir)
      return

    multilst=[] #argument list for multiprocessing
    cores=config.get_config_value("integer","cores")

    log.info("Used dir: %s" % (in_dir))
    for dirpath,dirnames,filenames in os.walk(in_dir, followlinks=True):
        i=0
        for f in sorted(filenames):
            year=f.split("_")[-1][:4]
            #use other logger
            if config.get_config_value("boolean","multi"):
                log = logging.getLogger("cmorlight_"+year)
                log.info("\n###########################################################\n# Var in work: %s / %s\n###########################################################" % (var, varRCM))
                log.info(datetime.now())
            #if limit_range is set: skip file if it is out of range
            if config.get_config_value('boolean','limit_range'):
                if int(year) < config.get_config_value('integer','proc_start') or int(year) > config.get_config_value('integer','proc_end'):
                    log.debug("File %s out of time range! Skipping ..." % f)
                    continue
            log.info("\n###########################################################")
            if f.find("%s_" % var) == 0 or f.find("%s.nc" % var) == 0 or f.find("%s_" % varRCM) == 0 or f.find("%s.nc" % varRCM) == 0 or f.find("%s_" % varRCM[:varRCM.find('p')]) == 0:
                in_file = "%s/%s" % (dirpath,f)
                # workaround for error in last input files of CCLM data from DWD
                # use only file with e.g. _2100 in filename (only if USE_SEARCH==True)
                if config.get_config_value('boolean', 'use_search_string') and in_file.find(settings.search_input_string) < 0:
                    continue
                log.log(35,"Input from: %s" % (in_file))
                if os.access(in_file, os.R_OK) == False:
                    log.error("Could not read file '%s', no permission!" % in_file)
                else:
                    if var in config.get_model_value('var_list_fixed'):
                        tools.process_file_fix(params,in_file)
                    else:
                        if config.get_config_value("boolean","multi"):
                            multilst.append([params,in_file,var,reslist,year])
                        else:
                            reslist=tools.process_file(params,in_file,var,reslist,year)

            else:
                log.warning("File %s does match the file name conventions for this variable. File not processed...")

            i=i+1

            #process as many files simultaneously as there are cores specified
            if config.get_config_value("boolean","multi") and i==cores:
                R=[]
                pool=Pool(processes=cores)
                R.extend(pool.map(process_file_unpack,multilst))
                pool.terminate()
                #start new
                multilst=[]
                i=0
                #change reslist
               # reslist=R[0]
    log.info("Variable '%s' finished!" % (var))
    return True


# -----------------------------------------------------------------------------
def main():
    ''' main program, first read command line parameter '''

    parser = OptionParser(version="%prog "+base.__version__) #VERSION)

    parser.add_option("-i", "--ini",
                            action="store", dest = "inifile", default = "control_cmor2.ini",
                            help = "configuration file (.ini)")
    parser.add_option("-p", "--param",
                            action="store", dest = "paramfile", default = "",
                            help = "model parameter file (table)")
    parser.add_option("-r", "--resolution",
                            action="store", dest = "reslist", default = "",
                            help = "list of desired output resolutions (supported: 1hr (1-hourly), 3hr (3-hourly),6hr (6-hourly),day (daily),mon (monthly) ,sem (seasonal),fx (for time invariant variables)")
    parser.add_option("-v", "--varlist",
                            action="store", dest = "varlist", default = "pr",
                            help = "list of variables to be processed")
    parser.add_option("-a", "--all",
                            action="store_true", dest = "all_vars", default = False,
                            help = "process all variables")
    parser.add_option("-c", "--chunk-var",
                            action="store_true", dest="chunk_var", default = False,
                            help="go call chunking for the variable list")
#    parser.add_option("-s", "--seasonal-mean",
#                            action="store_true", dest="seasonal_mean", default=False,
#                            help="go calculate seasonal mean from aggregated monthly data")
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
    parser.add_option("-E", "--ensemble",
                            action="store", dest="driving_model_ensemble_member", default = "",
                            help="set used ensemble")
    parser.add_option("-O", "--overwrite",
                            action="store_true", dest="overwrite", default = False,
                            help="Overwrite existent output files")
    parser.add_option("-f", "--force_proc",
                            action="store_false", dest="process_table_only", default = True,
                            help="Process variable at specific resolution only if this resolution is declared in the parameter table")
    parser.add_option("-S", "--silent",
                            action="store_false", dest="normal_log", default = True,
                            help="Write only minimal information to log (variables and resolutions in progress, warnings and errors)")
    parser.add_option("-V", "--verbose",
                            action="store_true", dest="verbose_log", default = False,
                            help="Verbose logging for debugging")
    parser.add_option("-A", "--append_log",
                            action="store_true", dest="append_log", default = False,
                            help="Append to log instead of overwrite")
    parser.add_option("-l", "--limit",
                            action="store_true", dest="limit_range", default = False,
                            help="Limit time range for processing (range set in .ini file or parsed)")
    parser.add_option("-s", "--start",
                            action="store", dest="proc_start", default = "",
                            help="Start year for processing if --limit is set.")
    parser.add_option("-e", "--end",
                            action="store", dest="proc_end", default = "",
                            help="End year for processing if --limit is set.")
    parser.add_option("-M", "--multi",
                            action="store_true", dest="multi", default = False,
                            help="Use multiprocessing with number of cores specified in .ini file.")
    parser.add_option( "--remove",
                            action="store_true", dest="remove_src", default = False,
                            help="Remove source files after chunking")







    (options, args) = parser.parse_args()
    options_dict=vars(options)
    config.load_configuration(options.inifile)

    if options.act_model not in ['CCLM','WRF']:
        sys.exit("Model ist not supported: '%s'" % (options.act_model))
        # end programm

    #limit range if start and end are given in command line
    if options.proc_start!="" and options.proc_end!="":
        options.limit_range=True

   #store parsed arguments in config
    setval=["paramfile","driving_model_id","driving_experiment_name","driving_model_ensemble_member"]
    for val in setval:
        if options_dict[val]!="":
            config.set_config_value('settings_',val,options_dict[val])

    config.set_config_value('settings','model',options.act_model)
    config.set_config_value('boolean','overwrite',options.overwrite)
    config.set_config_value('boolean','limit_range',options.limit_range)
    config.set_config_value('boolean','remove_src',options.remove_src)
    config.set_config_value('boolean','multi',options.multi)
    config.set_config_value('integer','proc_start',options.proc_start)
    config.set_config_value('integer','proc_end',options.proc_end)

    process_list=[config.get_model_value('driving_model_id'),config.get_model_value('driving_experiment_name'),config.get_model_value('driving_model_ensemble_member')]
    # now read paramfile for all variables for this RCM
    varfile = ("%s/%s" % (config.get_config_value('settings','DirConfig'),config.get_model_value('paramfile')))
    settings.init(varfile)

    # create logger
    LOG_BASE = settings.DirLog
    if os.path.isdir(LOG_BASE) == False:
        print("Logging directory does not exist: %s" % LOG_BASE)
        os.makedirs(LOG_BASE)
        if os.path.isdir(LOG_BASE) == True:
            print("Logging directory created: %s" % LOG_BASE)
    LOG_FILENAME = os.path.join(LOG_BASE,'CMORlight.')
    logext = datetime.now().strftime("%d-%m-%Y")+'.log'

    # get logger and assign logging filename (many loggers for multiprocessing)
    if options.limit_range and options.multi:
        #create logger for each processing year
        for y in range(config.get_config_value("integer","proc_start"),config.get_config_value("integer","proc_end")+1):
            logfile=LOG_FILENAME+str(y)+'.'+logext
            log = base.setup_custom_logger("cmorlight_"+str(y),logfile,config.get_config_value('boolean','propagate_log'),options.normal_log,options.verbose_log,options.append_log)
        #change general logger name
        LOG_FILENAME+="%s_%s." % (config.get_config_value("integer","proc_start"),config.get_config_value("integer","proc_end"))

    log = base.setup_custom_logger("cmorlight",LOG_FILENAME+logext,config.get_config_value('boolean','propagate_log'),options.normal_log,options.verbose_log,options.append_log)

    if not options.limit_range and options.multi:
        print("To use multiprocessing you have to limit the time range (with -l) and specify this range in the .ini file! Exiting...")
        log.error("To use multiprocessing you have to limit the time range (with -l) and specify this range in the .ini file! Exiting...")
        sys.exit()

    # creating working directory if not exist
    if not os.path.isdir(settings.DirWork):
        log.info("Working directory does not exist, creating: %s" % (settings.DirWork))
        os.makedirs(settings.DirWork)

    if not os.path.isdir(settings.DirOut):
        log.info("Output directory does not exist, creating: %s" % (settings.DirOut))
        os.makedirs(settings.DirOut)

    # assing some new parameter
    if config.get_config_value('boolean','add_version_to_outpath'):
        settings.use_version = "v%s" % (options.use_version)
    settings.use_alt_units = options.use_alt_units
    # derotate u and v
    if options.derotate_uv == True:
        tools.derotate_uv()
        return

    if options.all_vars == False:
        varlist = options.varlist.split(',')
        if varlist==[]:
            log.error("No variables set for processing! Exiting...")
            return
    else:
        varlist = [] #config.varlist['3hr'] + config.varlist['6hr']
        varlist.extend(tools.get_var_lists())

    if options.reslist=="": #if output resolutions not given in command -> take from inifile
        reslist=config.get_config_value('settings','reslist').replace(" ",",") #to allow for space as delimiter
        reslist=list(filter(None,reslist.split(','))) #split string and remove empty strings
    else:
        reslist = options.reslist.split(',')

    #TODO: allow for whitespace separation -> need to change in optparse
    #reslist = options.reslist.replace(" ",",") #to allow for space as delimiter
    #reslist=list(filter(None,reslist.split(','))) #split string and remove empty strings


    # if nothing is set: exit the program


    # test modus
    if options.test_var == True:
        tools.proc_test_var(process_list,varlist,reslist)
        return

    #Remove variables in var_skip_list from varlist
    if settings.var_skip_list[0]!="":
        log.info("Variables %s were found in var_skip_list. Skip these variables" % settings.var_skip_list)
        new_varlist=list(varlist)
        for var in varlist:
            params = settings.param[var]
            varCCLM = params[config.get_config_value('index','INDEX_VAR')]
            varRCM= params[config.get_config_value('index','INDEX_RCM_NAME')]
            if (varCCLM in settings.var_skip_list) or (varRCM in settings.var_skip_list):
                new_varlist.remove(var)
        varlist=list(new_varlist)


    log.info("Configuration read from: %s" % os.path.abspath(varfile))
    log.info("Variable(s): %s " % varlist)
    log.info("Requested time output resolution(s): %s " % reslist)
    log.info("Used RCM: %s" % config.get_config_value('settings','model'))
    if options.process_table_only:
        log.info("For each variable processing only resolutions declared in parameter table")
    else:
        log.info("Processing all resolutions lower equal the input data resolution")

    # process all var in varlist with input model and input experiment for proc_list item
    for var in varlist:
        reslist_act=list(reslist) #new copy of reslist
        for res in reslist:
            if tools.check_resolution(params,res,options.process_table_only) == False:
                reslist_act.remove(res) #remove resolution from list if it is not in table or if it is not supported
        if var not in settings.param:
            log.warning("Variable '%s' not supported!" % (var))
            continue
        else:
            # get parameter for next variable in the list
            params = settings.param[var]
            varCCLM = params[config.get_config_value('index','INDEX_VAR')]
            varRCM= params[config.get_config_value('index','INDEX_RCM_NAME')]
            log.log(35,"\n\n\n###########################################################\n# Var in work: %s / %s\n###########################################################" % (varCCLM, varRCM))

            log.debug("Used parameter for variable '%s': %s" % (var,params))

        if reslist_act==[]:
            log.warning("None of the given resolutions appears in the table! Skipping variable...")
            continue
        if params:
            # set global attributes in the dictionary
            tools.set_attributes(params,process_list)

            # skip fixed fields from chunking, makes no sense to chunk
            if options.chunk_var == True and not var in config.get_model_value('var_list_fixed'):
                log.log(35, "Chunking files \n #######################")
                tools.proc_chunking(params,reslist_act)

            # some procs for correction or cleanup files later
            elif options.corr_var == True:
                for res in reslist_act:
                    tools.proc_corr_var(params,res,key=options.corr_key)

            # process all vars from varlist with all output resolutions from reslist
            else:
                process_resolution(params,reslist_act)


#########################################################
#  main program if class isn't called from other script
#########################################################
if __name__ == "__main__":
    ''' main program '''

    # call main function
    main()
    #clean up temp files
    shutil.rmtree(settings.DirWork)

    #Clean up .tmp files in output directory (if on last run program crashed while writing a file)
    for root, dirs, files in os.walk(settings.DirOut):
        for file in files:
            if file[-4:]==".tmp":
                os.remove(os.path.join(root, file))

    log = logging.getLogger('cmorlight')
    log.propagate = True
    log.log(35,'\n##################################\n########  End of script.  ########\n##################################')
    ######################
    # END of program!!!  #
    ######################


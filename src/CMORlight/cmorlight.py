"""

Main script of the second CMOR step. Calls all other Python functions.

"""

import os
import sys
import shutil
import datetime
#for multiprocessing
from multiprocessing import Pool
# command line parser
import argparse

# configuration
import get_configuration as config

# global settings
import settings
# tools library
import tools

# basic setting for logging
import init_log

import logging

# -----------------------------------------------------------------------------
def process_file_unpack(args):
    '''Helper function for multiprocessing to unpack arguments before using pool.map'''
    
    return tools.process_file(*args)

def proc_seasonal_unpack(args):
    '''Helper function for multiprocessing to unpack arguments before using pool.map (seasonal processing)'''    

    tools.proc_seasonal(*args)

def process_resolution(params,reslist,nvar,nfiles,currfile):
    '''
    Processes files for variable defined by params for all resolutions in reslist

    Parameters
    ----------
    params : list
        Row in variables table corresponding to variable processed in the call of this function
    reslist : list
        List of resolutions the variable should be processed at
    nvar : int
        Number of variables (needed for progress bar)
    nfiles : int
        Currently estimated total number of files for all variables (needed for progress bar)
    currfile : int
        Currently already processed number of files
    '''
  
    #Do seasonal resolution=
    if "sem" in reslist:
        seasonal = True
        reslist.remove("sem")
    else:
        seasonal = False
        
    log = logging.getLogger("cmorlight")

    # get cdf variable name
    var = params[config.get_config_value('index','INDEX_VAR')]
    varRCM=params[config.get_config_value('index','INDEX_RCM_NAME')]
    # create path to input files from basedir,model,driving_model
    in_dir = "%s/%s" % (tools.get_input_path(),params[config.get_config_value('index','INDEX_RCM_NAME')])
    log.debug("Looking for input dir(1): %s" % (in_dir))

    if os.path.isdir(in_dir) == False:
        log.error("Input directory does not exist(0): %s \n \t Change base path in .ini file or create directory! " % in_dir)
        return nfiles,currfile

    cores=config.get_config_value("integer","multi",exitprog=False)
    multilst=[]
    seaslst=[]
    log.info("Used dir: %s" % (in_dir))
    for dirpath,dirnames,filenames in os.walk(in_dir, followlinks=True):
        if not nfiles:
            #estimate total 
            if config.get_config_value('boolean','limit_range'):
                nfiles = nvar * (config.get_config_value('integer','proc_end') - config.get_config_value('integer','proc_start') + 1)
            else:
                nfiles = nvar * len(filenames)
        if len(filenames)==0:
            log.warning("No files found! Skipping this variable...")

        i=0
        for f in sorted(filenames):
            if f[-3:] != ".nc":
                continue

            if var not in settings.var_list_fixed:
                year=f.split("_")[-1][:4]


            #use other logger
            if cores > 1 and var not in settings.var_list_fixed :
                logger = logging.getLogger("cmorlight_"+year)
                logger.info("\n###########################################################\n# Var in work: %s / %s\n###########################################################" % (var, varRCM))
                logger.info("Start processing at: "+str(datetime.datetime.now()))
            else:
                logger = logging.getLogger("cmorlight")

            #if limit_range is set: skip file if it is out of range
            if config.get_config_value('boolean','limit_range') and var not in settings.var_list_fixed:
                if int(year) < config.get_config_value('integer','proc_start') or int(year) > config.get_config_value('integer','proc_end'):
                    continue
                #Define first and last month of file
                if config.get_config_value('integer',"proc_start") == int(year):
                    firstlast=[config.get_config_value('integer',"first_month"),12] 
                elif config.get_config_value('integer',"proc_end") == int(year):
                    firstlast=[1,config.get_config_value('integer',"last_month")] 
                else:
                    firstlast=[1,12]

            else:
                firstlast=[1,12] 
                    
            logger.info("\n###########################################################")
            if f.find("%s_" % var) == 0 or f.find("%s.nc" % var) == 0 or f.find("%s_" % varRCM) == 0 or f.find("%s.nc" % varRCM) == 0 or f.find("%s_" % varRCM[:varRCM.find('p')]) == 0:
                in_file = "%s/%s" % (dirpath,f)
                logger.log(35,"Input from: %s" % (in_file))
                if os.access(in_file, os.R_OK) == False:
                    logger.error("Could not read file '%s', no permission!" % in_file)
                else:
                    if var in settings.var_list_fixed:
                        tools.process_file_fix(params,in_file)
                        
                    else:
                        if cores > 1:
                            multilst.append([params,in_file,var,reslist,year,firstlast])
                            seaslst.append([params,year])

                        else:
                            reslist=tools.process_file(params,in_file,var,reslist,year,firstlast)
                            if seasonal:
                                tools.proc_seasonal(params,year)
            else:
                logger.warning("File %s does match the file name conventions for this variable. File not processed...")

            i=i+1

            #process as many files simultaneously as there are cores specified
            if i==cores and multilst!=[]:
                log.info("Processing years %s to %s simultaneously" %(seaslst[0][1],seaslst[-1][1]))
                pool=Pool(processes=cores)
                R=pool.map(process_file_unpack,multilst)
                pool.terminate()     
                #seasonal processing:
                if seasonal:
                    pool=Pool(processes=cores)
                    pool.map(proc_seasonal_unpack,seaslst)
                    pool.terminate()
                
                currfile += len(multilst)
                #start new
                multilst=[]
                seaslst=[]
                i=0
                #change reslist
                reslist=R[0]
                #update currfile
                
            if  cores <= 1:
                currfile += 1
                
            #print progress bar
            tools.print_progress(currfile,nfiles)
            
    
    #process remaining files
    if len(multilst)!=0:
        log.info("Processing years %s to %s simultaneously" %(seaslst[0][1],seaslst[-1][1]))
        pool=Pool(processes=len(multilst))
        R=pool.map(process_file_unpack,multilst)
        pool.terminate()
        #seasonal processing:
        if seasonal:
            pool=Pool(processes=cores)
            pool.map(proc_seasonal_unpack,seaslst)
            pool.terminate()
        
        #update currfile
        currfile += len(multilst)
        tools.print_progress(currfile,nfiles)

    log.info("Variable '%s' finished!" % (var))
    
    return nfiles,currfile

# -----------------------------------------------------------------------------
def main():
    ''' main program, first read command line parameter '''

    parser = argparse.ArgumentParser()
    parser.add_argument("-X", "--EXP",
                            action="store", dest="exp", default = "",
                            help="Driving experiment (e.g. historical or rcp85)")
    parser.add_argument("-G", "--GCM",
                            action="store", dest="gcm", default = "",
                            help="Driving GCM")
    parser.add_argument("-E", "--ENS",
                            action="store", dest="ens", default = "",
                            help="Ensemble member of the driving GCM")
    parser.add_argument("-r", "--resolution",
                            action="store", dest = "reslist", default = "",
                            help = "list of desired output resolutions, comma-separated (supported: 1hr (1-hourly), 3hr (3-hourly),6hr (6-hourly),day (daily),mon (monthly) ,sem (seasonal),fx (for time invariant variables)")
    parser.add_argument("-v", "--varlist",
                            action="store", dest = "varlist", default = "",
                            help = "comma-separated list of variables (RCM or CORDEX name)  to be processed. If combined with --all: start with variable and process all remaining variables from the alphabetic order (ordered by RCM name) [until end variable, if given].")
    parser.add_argument("-a", "--all",
                            action="store_true", dest = "all_vars", default = False,
                            help = "process all available variables")
    parser.add_argument("-O", "--overwrite",
                            action="store_true", dest="overwrite", default = False,
                            help="Overwrite existent output files")
    parser.add_argument("-M", "--multi",
                            action="store", dest="multi", default = 1,
                            help="Use multiprocessing and specify number of available cores.")
    parser.add_argument("-c", "--chunk-var",
                            action="store_true", dest="chunk_var", default = False,
                            help="Concatenate files to chunks")
    parser.add_argument( "--remove",
                            action="store_true", dest="remove_src", default = False,
                            help="Remove source files after chunking")
    parser.add_argument("-s", "--start",
                            action="store", dest="proc_start", default = "",
                            help="Start year (and start month if not January) for processing. Format: YYYY[MM] ")
    parser.add_argument("-e", "--end",
                            action="store", dest="proc_end", default = "",
                            help="End year (and end month if not December) for processing. Format: YYYY[MM]")
    parser.add_argument("-P", "--propagate",
                            action="store_true", dest="propagate", default = False,
                            help="Propagate log to standard output.")
    parser.add_argument("-S", "--silent",
                            action="store_false", dest="normal_log", default = True,
                            help="Write only minimal information to log (variables and resolutions in progress, warnings and errors)")
    parser.add_argument("-V", "--verbose",
                            action="store_true", dest="verbose_log", default = False,
                            help="Verbose logging for debugging")
    parser.add_argument("-A", "--append_log",
                            action="store_true", dest="append_log", default = False,
                            help="Append to log instead of overwrite")
    parser.add_argument("-f", "--force_proc",
                            action="store_false", dest="process_table_only", default = True,
                            help="Try to process variable at specific resolution regardless of what is written in the variables table")
    parser.add_argument("-n", "--use-version",
                            action="store", dest = "use_version", default = tools.new_dataset_version(),
                            help = "version to be added to directory structure")
    parser.add_argument("-i", "--ini",
                            action="store", dest = "inifile", default = "control_cmor.ini",
                            help = "configuration file (.ini)")
    parser.add_argument("-d", "--no_derotate",
                            action="store_false", dest = "derotate_uv", default=True,
                            help = "derotate all u and v avariables")
    parser.add_argument("-m", "--simulation",
                           action="store", dest="simulation", default = '',
                          help="which simulation specific settings to choose")
    options = parser.parse_args()

    config.load_configuration(options.inifile)
    if options.simulation != "":
        config.set_config_value('settings','simulation',options.simulation)

    #limit range if start and end are given in command line
    if options.proc_start!="" and options.proc_end!="":
        limit_range=True
    else:
        limit_range=False

   #store parsed arguments in config
    if options.proc_start != "":
        config.set_config_value('integer',"proc_start",options.proc_start[:4])
        if len(options.proc_start)==6:
            config.set_config_value('integer',"first_month",options.proc_start[4:])
        else:
            config.set_config_value('integer',"first_month","1")
    if options.proc_end != "":
        config.set_config_value('integer',"proc_end",options.proc_end[:4])
        if len(options.proc_end)==6:
            config.set_config_value('integer',"last_month",options.proc_end[4:])
        else:
            config.set_config_value('integer',"last_month","12")
    if options.varlist != "":
        config.set_config_value('settings','varlist',options.varlist)
    
    change_driv_exp = False 
    if options.gcm != "":
        config.set_model_value('driving_model_id',options.gcm)
        change_driv_exp = True 
    if options.ens != "":
        config.set_model_value('driving_model_ensemble_member',options.ens)
        change_driv_exp = True 
    if options.exp != "":
        config.set_model_value('driving_experiment_name',options.exp)
        config.set_model_value('experiment_id',options.exp)
        change_driv_exp = True 
  
    if change_driv_exp:
        config.set_model_value('driving_experiment',"%s, %s, %s" % (config.get_sim_value('driving_model_id'),config.get_sim_value('experiment_id'),config.get_sim_value('driving_model_ensemble_member')))        
    config.set_config_value('boolean','overwrite',options.overwrite)
    config.set_config_value('boolean','limit_range',limit_range)
    config.set_config_value('boolean','remove_src',options.remove_src)
    config.set_config_value('integer','multi',options.multi)
    config.set_config_value('boolean','derotate_uv',options.derotate_uv)
    config.set_config_value('boolean','propagate_log',options.propagate)

    #Extend input path if respective option is set:
    if config.get_config_value('boolean','extend_DirIn')==True:
        DirIn=config.get_config_value('settings','DirIn')+'/'+ config.get_sim_value('driving_model_id')+'/'+ config.get_sim_value('driving_experiment_name')
        config.set_config_value('settings','DirIn',DirIn)
        DirDerotated=config.get_config_value('settings','DirDerotated')+'/'+ config.get_sim_value('driving_model_id')+'/'+ config.get_sim_value('driving_experiment_name')
        config.set_config_value('settings','DirDerotated',DirDerotated)

    # now read vartable for all variables for this RCM

    vartable= config.get_sim_value('vartable')
    settings.init(vartable)

    # create logger
    LOG_BASE = settings.DirLog
    if os.path.isdir(LOG_BASE) == False:
        print("Create logging directory: %s" % LOG_BASE)
        if not os.path.isdir(LOG_BASE):
            os.makedirs(LOG_BASE)
    LOG_FILENAME = os.path.join(LOG_BASE,'CMORlight.')+config.get_sim_value('driving_model_id')+"_"+config.get_sim_value('experiment_id')+"."
    logext = datetime.datetime.now().strftime("%d-%m-%Y")+'.log'

    # get logger and assign logging filename (many loggers for multiprocessing)
    if limit_range and int(options.multi) > 1:
        #create logger for each processing year
        for y in range(config.get_config_value("integer","proc_start"),config.get_config_value("integer","proc_end")+1):
            logfile=LOG_FILENAME+str(y)+'.'+logext
            log = init_log.setup_custom_logger("cmorlight_"+str(y),logfile,config.get_config_value('boolean','propagate_log'),options.normal_log,options.verbose_log,options.append_log)
        #change general logger name
        LOG_FILENAME+="%s_%s." % (config.get_config_value("integer","proc_start"),config.get_config_value("integer","proc_end"))

    log = init_log.setup_custom_logger("cmorlight",LOG_FILENAME+logext,config.get_config_value('boolean','propagate_log'),options.normal_log,options.verbose_log,options.append_log)

    if not limit_range and int(options.multi) > 1:
        print("To use multiprocessing you have to limit the time range by specifying this range over the command line (-s START, -e END)! Exiting...")
        log.error("To use multiprocessing you have to limit the time range by specifying this range over the command line (-s START, -e END)! Exiting...")
        sys.exit()

    # creating working directory if not existent
    if not os.path.isdir(settings.DirWork):
        log.debug("Working directory does not exist, creating: %s" % (settings.DirWork))
        if not os.path.isdir(settings.DirWork):
            os.makedirs(settings.DirWork)

    if not os.path.isdir(settings.DirOut):
        log.debug("Output directory does not exist, creating: %s" % (settings.DirOut))
        if not os.path.isdir(settings.DirOut):
            os.makedirs(settings.DirOut)

    if config.get_config_value('boolean','add_version_to_outpath') or options.use_version != tools.new_dataset_version():
        settings.use_version = options.use_version
    varlist = settings.varlist
    if options.all_vars == False:
        if varlist==[] or varlist==[''] :
            raise Exception("No variables set for processing! Set with -v or -a or in configuration file.")
    else:
        varlist_all = [] #config.varlist['3hr'] + config.varlist['6hr']
        varlist_all.extend(tools.get_var_lists())
        if ( len(varlist)==1 or len(varlist)==2) and varlist!=['']: #start from given variable
            try:
                varstart = settings.param[varlist[0]][config.get_config_value('index','INDEX_VAR')]
            except:
                cmd="Variable %s not found in list of all variables! Cannot start processing from this variable" % varlist[0]
                log.error(cmd)
                raise Exception(cmd)
            try:
                if len(varlist)==2:
                    varend = settings.param[varlist[1]][config.get_config_value('index','INDEX_VAR')]
                    varlist=varlist_all[varlist_all.index(varstart):varlist_all.index(varend)+1]
                else:
                    varlist=varlist_all[varlist_all.index(varstart):]
            except:
                cmd="Variable %s not found in list of all variables! Cannot stop processing at this variable" % varlist[1]
                log.error(cmd)
                raise Exception(cmd)

        elif len(varlist)>2:
            cmd="Option --all contradicts giving a variable list with more than two variables!"
            log.error(cmd)
            raise Exception(cmd)
        else:
            varlist = varlist_all            
    if options.reslist=="": #if output resolutions not given in command -> take from inifile
        reslist=config.get_config_value('settings','reslist').replace(" ",",") #to allow for space as delimiter
        reslist=list(filter(None,reslist.split(','))) #split string and remove empty strings
    else:
        reslist = options.reslist.split(',')

    # if nothing is set: exit the program


    log.info("Configuration read from: %s" % os.path.abspath(vartable))
    log.info("Variable(s): %s " % varlist)
    log.info("Requested time output resolution(s): %s " % reslist)
    if options.process_table_only:
        log.info("For each variable processing only resolutions declared in parameter table")
    else:
        log.info("Processing all resolutions lower equal the input data resolution")

    # process all var in varlist with input model and input experiment for proc_list item
    # needed for progress bar
    nfiles = None #estimated total number of files
    currfile = 0 #currently processed files
    for var in varlist:
        if var not in settings.param:
            log.warning("Variable '%s' not supported!" % (var))
            continue
        params = settings.param[var]
        varCMOR= params[config.get_config_value('index','INDEX_VAR')]
        varRCM= params[config.get_config_value('index','INDEX_RCM_NAME')]
        if (varCMOR in settings.var_skip_list) or (varRCM in settings.var_skip_list):
            log.debug("###########################################################")
            log.debug("Variable was found in var_skip_list. Skip this variables")
            continue
        log.log(35,"\n\n\n###########################################################\n# Var in work: %s / %s\n###########################################################" % (varCMOR, varRCM))
     
        # set global attributes in the dictionary
        tools.set_attributes(params)
        # skip fixed fields from chunking, makes no sense to chunk
        if options.chunk_var == True and not var in settings.var_list_fixed:
            log.log(35, "Chunking files \n #######################")
            tools.proc_chunking(params,reslist)
        else:
            reslist_act=list(reslist) #new copy of reslist
            if (varRCM not in settings.var_list_fixed) and (varCMOR not in settings.var_list_fixed):
                for res in reslist:
                    if tools.check_resolution(params,res,options.process_table_only) == False:
                        reslist_act.remove(res) #remove resolution from list (for this variable) if it is not in table or if it is not supported
    
            if reslist_act==[]:
                log.warning("None of the given resolutions appears in the table! Skipping variable...")
                continue
    
            # process all vars from varlist with all output resolutions from reslist
            nfiles, currfile = process_resolution(params,reslist_act,len(varlist),nfiles,currfile)


#########################################################
#  main program if class isn't called from other script
#########################################################
if __name__ == "__main__":
    ''' main program '''
    
    #start timing
    time1=datetime.datetime.now()

    # call main function
    main()

    time2=datetime.datetime.now()
    log = logging.getLogger('cmorlight')

    #calculate processing time
    time_diff=time2-time1
    hours, remainder = divmod(time_diff.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    log.log(35,'\nTotal processing time: %s hours %s minutes %s seconds' % (int(hours),int(minutes),round(seconds)))
    log.log(35,'\n##################################\n########  End of script.  ########\n##################################')

    ######################
    # END of program!!!  #
    ######################


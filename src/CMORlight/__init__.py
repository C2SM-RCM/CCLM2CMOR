import logging
#import logging.handlers
#import settings

import os
import datetime

__version__ = open('VERSION', "r").read()
VERSION = "v%s, DKRZ, 2016,2017" % (__version__)
logfile = 'CMORlight.'+datetime.datetime.now().strftime("%d-%m-%Y")+'.log'

#LOG_BASE = os.environ['HOME']
#LOG_BASE = settings.DirLog # = '/mnt/lustre01/work/bb0931/CMOR/logs'
#if os.path.isdir(LOG_BASE) == False:
    #print("Output directory does not exist: %s" % LOG_BASE)
    #os.makedirs(LOG_BASE)

#LOG_FILENAME = os.path.join(LOG_BASE,logfile)

#logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG, format='%(asctime)s %(process)s %(levelname)s:%(message)s')
#print logging.getLogger("CMORLIGHT")
#LOGGER = logging.getLogger("CMORLIGHT")
#logging.info('Starting...')

#log = logging.getLogger(__name__)

# Add the log messageq handler to the logger
#handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000)

#log.addHandler(handler)

def setup_custom_logger(name,filename='/dev/null',propagate=False,normal_log=True,verbose_log=False):
    #formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    if verbose_log:
        level=logging.DEBUG
    elif normal_log:
        level=logging.INFO
    else:
        level=logging.WARNING

    formatter = logging.Formatter(fmt='%(levelname)s:  %(message)s')
   # formatter = logging.Formatter(fmt='%(asctime)s %(module)s %(levelname)s:  %(message)s',datefmt='%H:%M:%S')
    #formatter = logging.Formatter(fmt='%(asctime)s %(process)s %(levelname)s:%(message)s')
    log = logging.getLogger(name)
    log.setLevel(level)
    logging.addLevelName(35,"")
    #if filename:
        #logging.basicConfig(filename=filename, level=logging.DEBUG, format='%(asctime)s %(process)s %(levelname)s:%(message)s')
    handler = logging.FileHandler(filename)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.propagate = propagate
    return log


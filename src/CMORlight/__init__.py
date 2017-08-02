#import logging
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

import logging
def setup_custom_logger(name,filename='/dev/null'):
    #formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    formatter = logging.Formatter(fmt='%(asctime)s %(process)s %(levelname)s:%(message)s')
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    #if filename:
        #logging.basicConfig(filename=filename, level=logging.DEBUG, format='%(asctime)s %(process)s %(levelname)s:%(message)s')
    handler = logging.FileHandler(filename)
    handler.setFormatter(formatter)      
    log.addHandler(handler)
    #print log
    log.propagate = False
    return log


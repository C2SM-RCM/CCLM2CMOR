#!/usr/bin/python
#
# configure programm
#
# Hans Ramthun
# DKRZ 2016, 2017
#
#
######################################################################################################
import logging
import pkg_resources
import os
import sys
import settings
#import csv

from _compat import PY2
if PY2:
    import ConfigParser
else:
    import configparser

RAW_OPTIONS = [('logging', 'format'), ]

CONFIG = None

LOGGER = logging.getLogger("cmorlight")
# -----------------------------------------------------------------------------


def get_config_value(section, option, inifile=None):
    """Get desired value from  configuration files
    :param section: section in configuration files
    :type section: string
    :param option: option in the section
    :type option: string
    :returns: value found in the configuration file
    """

    if not CONFIG:
        sys.exit("ERROR: Load configuration file before getting/setting config values! Exiting...")

    value = ''

    if CONFIG.has_section(section):
        if CONFIG.has_option(section, option):
            raw = (section, option) in RAW_OPTIONS
            value = CONFIG.get(section, option, raw=raw)

            # Convert Boolean string to real Boolean values
            if value.lower() == "false":
                value = False
            elif value.lower() == "true":
                value = True

        else:
            LOGGER.error("Option %s in section %s in configuration file does not exist!" % (option,section))
    else:
        LOGGER.error("Section %s in configuration file does not exist!" % (section))

    if section == 'index':
        value = int(value)
    elif section == 'float':
        value = float(value)
    elif section == 'integer':
        value = int(value)
    return value


# -----------------------------------------------------------------------------
def get_model_value(option):
    """Get value from model section."""

    model = get_config_value('settings','model')
    return get_config_value("settings_%s" % (model), option)


# -----------------------------------------------------------------------------
def set_config_value(section, option, value,inifile=None):
    ''' '''
    if not CONFIG:
        sys.exit("ERROR: Load configuration file before getting/setting config values! Exiting...")

    if section=="settings_":  #add model value to section
        section=section+get_config_value('init','model')
    if not CONFIG.has_section(section):
        CONFIG.add_section(section)
    value=str(value)

    CONFIG.set(section, option, value)


# -----------------------------------------------------------------------------
def load_configuration(inifile):
    """Load PyWPS configuration from configuration files.
    The later configuration file in the array overwrites configuration
    from the first.
    :param cfgfiles: list of configuration files
    """
    global CONFIG

  #  LOGGER.info('loading configuration from %s' % inifile)
    if PY2:
        CONFIG = ConfigParser.SafeConfigParser()
    else:
        CONFIG = configparser.ConfigParser()

    CONFIG.add_section('init')
    CONFIG.set("init","inifile",inifile)
    CONFIG.readfp(open(pkg_resources.resource_filename(__name__,inifile)))
    #Extend input path if respective option is set:
    if CONFIG.get('boolean','extend_DirIn')=='True':
      DirIn=CONFIG.get('settings','DirIn')+'/'+ get_model_value('driving_model_id')+'/'+ get_model_value('driving_experiment_name')
      CONFIG.set('settings','DirIn',DirIn)
      DirOutRotated=CONFIG.get('settings','DirOutRotated')+'/'+ get_model_value('driving_model_id')+'/'+ get_model_value('driving_experiment_name')
      CONFIG.set('settings','DirOutRotated',DirOutRotated)


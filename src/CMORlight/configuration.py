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
import sys
import os

if (sys.version_info < (3, 0)):
    import ConfigParser
else:
    import configparser

RAW_OPTIONS = [('logging', 'format'), ]

CONFIG = None

LOGGER = logging.getLogger("cmorlight")
# -----------------------------------------------------------------------------


def get_config_value(section, option, exitprog = True):
    """Get desired value from  configuration files
    :param section: section in configuration files
    :type section: string
    :param option: option in the section
    :type option: string
    :returns: value found in the configuration file
    """

    if not CONFIG:
        raise Exception("ERROR: Load configuration file before getting/setting config values! Exiting...")

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

    if value == "" and exitprog:
        raise Exception("Option %s in section %s in configuration file does not exist!" % (option,section))

    if section == 'index':
        value = int(value)
    elif section == 'float':
        value = float(value)
    elif section == 'integer':
        value = int(value)
    return value


# -----------------------------------------------------------------------------
def get_sim_value(option, exitprog = True):
    """Get value from simulation section."""

    simulation = get_config_value('settings','simulation')
    return get_config_value("settings_%s" % (simulation), option, exitprog)


# -----------------------------------------------------------------------------
def set_config_value(section, option, value):
    ''' '''
    if not CONFIG:
        sys.exit("ERROR: Load configuration file before getting/setting config values! Exiting...")

    if section=="settings_":  #add simulation value to section
        section=section+get_config_value('settings','simulation')
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
    if (sys.version_info < (3, 0)):
        CONFIG = ConfigParser.SafeConfigParser()
    else:
        CONFIG = configparser.ConfigParser()

    CONFIG.readfp(open(pkg_resources.resource_filename(__name__,inifile)))

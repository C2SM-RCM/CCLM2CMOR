"""

Reads in configuration from control_cmor.ini and provides functions to read or change the entries

"""

import logging
import pkg_resources
import sys

if (sys.version_info < (3, 0)):
    import ConfigParser
else:
    import configparser

RAW_OPTIONS = [('logging', 'format'), ]

CONFIG = None

LOGGER = logging.getLogger("cmorlight")
# -----------------------------------------------------------------------------


def get_config_value(section, option, exitprog = True):
    """
    Get desired value from  configuration file

    Parameters
    ----------

    section : str
        section in configuration file
    option : str
        option in the section
    exitprog : bool
        whether to exit the program with an error message if value was not found

    Returns
    -------

    value found in the configuration file
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
    """
    Get value from simulation section.

    Parameters
    ----------

    option : str
        option in the simulation section

    exitprog : bool
        whether to exit the program with an error message if value was not found

    Returns
    -------

    value found in the configuration file

    """

    simulation = get_config_value('settings','simulation')
    return get_config_value("settings_%s" % (simulation), option, exitprog)

## -----------------------------------------------------------------------------
def set_model_value(option, value):
    """
    Set value in simulation section.

    Parameters
    ----------

    option : str
        option in the simulation section

    value : str
        value to be set
    """

    ''' '''
    simulation = get_config_value('settings','simulation')
    set_config_value("settings_%s" % (simulation), option,value)


# -----------------------------------------------------------------------------
def set_config_value(section, option, value):
    """
    Set configuration value.

    Parameters
    ----------

    section : str
        section in configuration file
    option : str
        option in the section
    value : convertible to str
        value to be set

    """
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
    """
    Load PyWPS configuration from configuration files.
    The later configuration file in the array overwrites configuration
    from the first.

    Parameters
    ----------
    inifile : str or list of str
        absolute path(s) to configuration file(s)
    """
    global CONFIG

  #  LOGGER.info('loading configuration from %s' % inifile)
    if (sys.version_info < (3, 0)):
        CONFIG = ConfigParser.SafeConfigParser()
    else:
        CONFIG = configparser.ConfigParser()

    CONFIG.readfp(open(pkg_resources.resource_filename(__name__,inifile)))

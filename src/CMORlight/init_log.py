"""

Sets up custom logger

"""

import logging

def setup_custom_logger(name,filename='/dev/null',propagate=False,normal_log=True,verbose_log=False,append_log=False):
    """
    Sets up custom logger and returns it

    Parameters
    ----------

    name : str
        Name of the logger with which it can be called
    filename : str
        absolute path of the logger
    propagate : bool
        if logged information should also be propagated to the standard output
    normal_log : bool
        if True, logger gets logging level INFO; if false, the level is WARNING (unless verbose_log == True)
    verbose_log : bool
        if True, logger gets logging level DEBUG
    append_log : bool
        if True, logged information is appended to the file, if false, the file is overwritten

    Returns
    -------

    log : logging.Logger
        Custom logger
    """
    if verbose_log:
        level=logging.DEBUG
    elif normal_log:
        level=logging.INFO
    else:
        level=logging.WARNING

    if append_log:
        mode='a'
    else:
        mode='w'
    formatter = logging.Formatter(fmt='%(levelname)s:  %(message)s')
   # formatter = logging.Formatter(fmt='%(asctime)s %(module)s %(levelname)s:  %(message)s',datefmt='%H:%M:%S')
    #formatter = logging.Formatter(fmt='%(asctime)s %(process)s %(levelname)s:%(message)s')
    log = logging.getLogger(name)
    log.setLevel(level)
    logging.addLevelName(35,"")
    fh = logging.FileHandler(filename,mode=mode)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    if propagate:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        log.addHandler(ch)

    return log


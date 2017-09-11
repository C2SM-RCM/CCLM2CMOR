import logging

def setup_custom_logger(name,filename='/dev/null',propagate=False,normal_log=True,verbose_log=False,append_log=False):
    #formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
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
    handler = logging.FileHandler(filename,mode=mode)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.propagate = propagate
    return log


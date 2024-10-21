"""exceptlib"""
import sys

from functools import reduce
from logging import getLogger
from os import path
from types import ModuleType
from typing import Tuple


logger = getLogger(__name__)


class NotThisException(BaseException):
    """not this exception"""

    def __init_subclass__(cls) -> None:
        """return None"""
        raise Exception("subclassing not recommended")
    

class ExceptionProfiler:
    """exception profiler"""
    pass
    # decorate a function with exc_from_mod and use it for custom or
    # default profiling. Custom profiling is acheived through hooks
    # that are passed in during instantiation, while defaul profiling
    # will use exceptlib's logger to emit key details from the module,
    # possibly including package metadata. ...

class ExceptionGrouper:
    """exception grouper"""
    pass
    # uses ast to parse the module its instanted in to search for any
    # raise clauses, through its classmethod find. From the set of
    # raise clauses found, exceptions are extracted and used to create
    # and return an exception group. By default, find explores the
    # current module and its children.


def exc_from_mod(*modules: ModuleType, **kwargs) -> Tuple[BaseException]:
    """return Tuple[BaseException]
    
    :param *modules: zero or more module objects
    :param **kwargs: zero or more configuration arguments

    Accept one or more module object arguments, and return a tuple of
    exception objects. If the module object is attributed to the
    exception currently being raised, then return a tuple with at least
    the current exception. Otherwise return an tuple whose lone
    exception is an `exceptlib.NotThisException` class.

    Default behavior can be tuned in a few ways. ...
    """
    logger.debug("exc_from_mod: enter")

    # obtain current exception from all based on thread id
    exc = sys.exception()
    if exc is None:
        logger.exception("exc_from_mod: no exception")
        raise Exception("no exception")
        # TODO: verify isolation of exception
    
    # don't be passive
    if not modules:
        logger.debug("exc_from_mod: no modules")
        return (exc,)

    # container for modules encountered in traceback objects
    mods = list()

    # loop through all the traceback objects
    trb = exc.__traceback__
    while trb is not None:

        # obtain file name and module name
        file_name = trb.tb_frame.f_code.co_filename
        logger.debug("exc_from_mod: file_name=%s", file_name)

        # look for the module in sys.module first
        trb_mods = list()
        if (sys_mods := mods_from_filename(file_name, sys.modules)):
            logger.debug("exc_from_mod: not in sys.modules")
            trb_mods += sys_mods
        if (global_mods := mods_from_filename(file_name, globals)):
            logger.debug("exc_from_mod: not in sys.modules")
            trb_mods += global_mods

        # append this level's mods and reset the traceback
        mods.append(trb_mods)
        trb = trb.tb_next

    # default return value
    result = (NotThisException,)

    # evaluate if module of root traceback object is implicated
    if kwargs.get("root_only", False) and trb_mods[-1]:
        if not set(trb_mods[-1]).isdisjoint(set(modules)):
            result = (exc,)

    # otherwise evaluate if any modules are implicated
    mods = reduce(lambda x,y: x + y, mods)
    if not set(mods).isdisjoint(set(modules)):
        result = (exc,)
    
    # cleanup and return result
    logger.debug("exc_from_mod: exc=%s", result)
    return result


def mods_from_filename(file_name: str, search_space: dict) -> ModuleType:
    """return ModuleType
    
    :param file_name: file name string
    :param search_space: arbitrary mapping
    
    Accept a filename object and return module or None.
    """
    logger.debug("mod_from_filename: enter")

    # ensure file_name refers to existing file
    if not path.exists(file_name):
        logger.exception("mod_from_filename: dne; file_name=%s", file_name)
        return None

    # look for and return matches
    matches = list()
    for value in search_space.values():
        if hasattr(value, __file__) and value.__file__ == file_name:
            logger.debug("mod_from_filename: %s found", value.__name__)
            matches.append(value)
    return matches

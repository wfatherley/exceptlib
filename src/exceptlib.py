"""exceptlib"""
import sys
import threading
import traceback

from logging import getLogger
from types import ModuleType, TracebackType
from typing import Tuple

from importlib.util import spec_from_file_location
from importlib.util import module_from_spec


logger = getLogger(__name__)


type ExceptionTuple = Tuple[BaseException | Exception]


class NotThisException(BaseException):
    """not this exception"""

    def __init_subclass__(cls) -> None:
        """return None"""
        raise Exception("subclassing not recommended")


def exc_from_mod(*modules: ModuleType, **kwargs) -> ExceptionTuple:
    """return Tuple[BaseException]
    
    :param *modules: zero or more module objects
    :param **kwargs: zero or more configuration arguments

    Accept one or more module object arguments, and return a tuple of
    exception objects. If the module object is attributed to the root
    exception currently being raised, then return a tuple with at least
    the current exception. Otherwise return an tuple whose lone
    exception is an `exceptlib.NotThisException` class.

    Default behavior can be tuned in a few ways.
    """
    logger.debug("exc_from_mod: enter")

    thread_id = kwargs.get("thread_id", threading.get_ident())
    logger.debug("exc_from_mod: thread_id=%i", thread_id)

    # obtain current exception from all based on thread id
    exc = sys._current_exceptions().get(thread_id)
    if exc is None:
        logger.debug("exc_from_mod: no exception; thread_id=%i", thread_id)
        raise RuntimeError("thread has no exception")

    # container for modules encountered in traceback objects
    trb_mods = list()

    # loop through all the traceback objects
    trb = exc.__traceback__
    while trb is not None:

        # obtain module and add to set of modules
        trb_mod = mod_from_trb(trb)
        trb_mods.append(trb_mod)

        # run a hook if module is not in a normal place
        if trb_mod not in sys.modules:
            logger.debug(
                "exc_from_mod: %s not in sys.modules", trb_mod.__name__
            )
            kwargs.get("module_missing_hook", lambda e: None)(exc)

        # reset the traceback
        trb = trb.tb_next

    # evaluate if module of root traceback object is implicated
    if kwargs.get("root_only", False) and trb_mods[-1] in modules:
        return (exc,)

    # otherwise evaluate if any modules are implicated
    trb_mods = set(trb_mods)
    if trb_mods - set(modules) != trb_mods:
        return (exc,)
    
    # finally raise a never-to-match exception
    else:
        return (NotThisException,)
    # TODO: multiple exceptions, eg "raise x from y"


def mod_from_trb(traceback: TracebackType) -> ModuleType:
    """return TracebackType
    
    :param traceback: the traceback object to evaluate
    
    Accept a traceback object, extract from the corresponding code
    object its filename, and try to return a module object.
    """
    logger.debug("mod_from_trb: enter")
    return module_from_spec(
        spec_from_file_location(traceback.tb_frame.f_code.co_filename)
    )
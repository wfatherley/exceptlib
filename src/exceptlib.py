"""exceptlib"""
import ast
import sys

from functools import reduce
from logging import DEBUG, getLogger
from pathlib import Path
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


class ExceptionTuple(tuple):
    """exception tuple"""
    
    @classmethod
    def find(cls, *exclude: BaseException, **kwargs) -> Tuple[BaseException]:
        """return Tuple[BaseException]
        
        :param *exclude: zero or more exception objects
        :param **kwargs: zero or more configuration arguments

        Return a tuple of distinct exception classes found in the
        calling module. This classmethod searches the module's AST
        for `raise` statements, extracts their exception class, and
        adds them to an internal set. After the search, the set is cast
        to a tuple and returned.


        """
        log_level = kwargs.get("log_level", DEBUG)
        logger.log(log_level, "ExceptionGrouper.walk: enter")

        # verify being called in a module
        path_obj = Path(__file__)
        if not path_obj.exists():
            raise Exception("uncallable; search in globals")

        excs = set()
        for node in ast.walk(ast.parse(path_obj.read_text())):

            # skip over non raise nodes
            if not isinstance(node, ast.Raise):
                continue

            # case when exc is NoneType
            if node.exc is None:
                continue

            # case when exc is ast.Name
            name_id = getattr(node.exc, "id", None)

            # cases when exc is ast.Call
            if name_id is None:

                # case when func is ast.Name
                name_id = getattr(node.exc.func, "id", None)
                
                # case when func is ast.Attribute
                if isinstance(node.exc.func, ast.Attribute):
                    name_id = node.exc.func.value.id

            # add the exception to exception set
            if (exc := eval(name_id)) not in exclude:
                excs.add(exc)

        # instantiate and return exception group
        return tuple(excs)


def exc_from_mod(*modules: ModuleType, **kwargs) -> Tuple[BaseException]:
    """return Tuple[BaseException]
    
    :param *modules: zero or more module objects
    :param **kwargs: zero or more configuration arguments

    Return a tuple of exceptions if a module object in `modules` is the
    root cause of the current exception. Raise `RuntimeError` if there
    is no current exception, or if any of the objects in `modules` is
    not of type `ModuleType`. Currently, the tuple of exceptions always
    contains one exception-- the current exception, again, if one of
    `modules` is its root cause, or `exceptlib.NotThisException` if
    none of `modules` is implicated as root cause of current exception.

    This function is designed to be called as the predicate of an
    `except` clause, so that the clause may be entered based on module
    rather than exception identity. Set optional keyword argument
    `any_traceback` to `True` to return a tuple with the current
    exception if any of `modules` is specified in any traceback. Pass
    optional keyword argument `log_level` with a valid logging level to
    set `exceptlib`'s logger to that level.

    The exception `exceptlib.NotThisException` is a direct subclass of
    built-in `BaseException`, so that the chance of entering an
    `except` block spuriously is limited only to use of
    `NotThisException` outside of module `exceptlib`.
    """
    log_level = kwargs.get("log_level", DEBUG)
    logger.log(log_level, "exc_from_mod: enter")

    # get current exception from sys.exc_info triple
    exc_t, exc, trb = sys.exc_info()
    logger.log(log_level, "exc_from_mod: exc_t=%s; exc=%s", exc_t, exc)

    # raise on possibly irregular behavior
    if exc is None:
        logger.exception("exc_from_mod: no exception")
        raise RuntimeError("no exception to handle")
    
    # raise if any module parameter is not a module
    if any(map(lambda m: not isinstance(m, ModuleType), modules)):
        logger.exception("exc_from_mod: bad module parameter(s)")
        raise RuntimeError("module parameters must be of type ModuleType")
    
    # don't suppress
    if not modules:
        logger.log(log_level, "exc_from_mod: no modules")
        return (exc_t,)

    # container for modules encountered in traceback objects
    mods = list()

    # loop through all the traceback objects
    while trb is not None:

        # obtain file name and module name
        file_name = trb.tb_frame.f_code.co_filename
        logger.log(log_level, "exc_from_mod: file_name=%s", file_name)

        # to contain sublists of module found at this traceback
        trb_mods = list()

        # search in sys.modules and append any mods to trb_mods
        sys_mods = mods_from_filename(
            file_name, sys.modules, log_level=log_level
        )
        if sys_mods is not None:
            logger.log(log_level, "exc_from_mod: sys_mods=%s", sys_mods)
            trb_mods += sys_mods

        # search in globals and append any mods to trb_mods
        global_mods = mods_from_filename(
            file_name, globals(), log_level=log_level
        )
        if global_mods is not None:
            logger.log(log_level, "exc_from_mod: global_mods=%s", global_mods)
            trb_mods += global_mods

        # append this level's mods and reset the traceback
        mods.append(trb_mods)
        trb = trb.tb_next

    # default return value
    result = (NotThisException,)
    logger.log(log_level, "exc_from_mod: result=%s", result)

    # evaluate if module of root traceback object is implicated
    if not kwargs.get("any_traceback", False) and trb_mods[-1]:
        if not set(trb_mods[-1]).isdisjoint(set(modules)):
            result = (exc_t,)
            logger.log(
                log_level, "exc_from_mod: root only; result=%s", result
            )

    # otherwise evaluate if any modules are implicated
    else:
        mods = reduce(lambda x,y: x + y, mods)
        if not set(mods).isdisjoint(set(modules)):
            result = (exc_t,)
            logger.log(log_level, "exc_from_mod: any level result=%s", result)
    
    # cleanup and return result
    logger.log(log_level, "exc_from_mod: exc=%s", result)
    return result


def mods_from_filename(
    file_name: str, search_space: dict, **kwargs
) -> ModuleType:
    """return ModuleType
    
    :param file_name: file name string
    :param search_space: arbitrary mapping
    :param **kwargs: keyword arguments
    
    Accept a filename object and return module or None.
    """
    log_level = kwargs.get("log_level", DEBUG)
    logger.log(log_level, "mod_from_filename: enter; file_name=%s", file_name)

    # ensure file_name refers to existing file
    if not Path(file_name).exists():
        logger.log(log_level, "mod_from_filename: file not found")
        return None

    # look for and return matches
    matches = list()
    for value in search_space.values():
        if hasattr(value, "__file__") and value.__file__ == file_name:
            logger.log(log_level, "mod_from_filename: mod=%s", value.__name__)
            matches.append(value)
    return matches


exceptions = ExceptionTuple.find()

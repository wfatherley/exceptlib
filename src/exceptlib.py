"""Exception handling tools."""
import ast
import inspect
import sys
import traceback

from logging import getLogger
from pathlib import Path
from random import sample
from string import ascii_letters
from types import ModuleType, TracebackType
from typing import Any

from collections.abc import Sequence # pylint: disable=E0401
from importlib.util import module_from_spec, spec_from_file_location


logger = getLogger(__name__)


def random_exception(name: str=None, **attributes: dict) -> BaseException:
    """:return BaseException: a ``BaseException`` subclass
    
    :param name: optional subclass name string
    :param **attributes: a mapping of attributes and methods

    Dynamically create and return a ``BaseException`` subclass. When
    called without parameter ``name``, the returned subclass will
    have a random 15-character (alpha only) name. Without any
    keyword arguments, it will inheret ``BaseException.__dict__``.
    """
    logger.debug("random_exception: enter")
    name = name or "".join(sample(ascii_letters, 15))
    return type(name, (BaseException,), attributes)


class NotThisException(BaseException):
    """A sentinal-like exception class.
    
    This ``BaseException`` subclass supports the need for a "private"
    exception. For example, instances of ``exceptlib.ExceptionFrom``
    utlize this private exception to pass exception handling to the
    next avaialable ``except`` clause, if any. This exception should
    not need to be raised in normal circumstances-- utility is limited
    to applications surrounding ``exceptlib``, and care should be taken
    when using it elsewhere.
    """

    def __init_subclass__(cls) -> None:
        """:return None:"""
        raise TypeError("subclassing not recommended")


class ExceptionFrom(tuple):
    """A ``tuple`` subclass for use in exception handling.

    When called as the predicate of an ``except`` clause, this object
    enables the handling of the current exception by module rather than
    by exception or exception group. Input parameters are zero or more
    module objects.

    If zero module objects are supplied, this object is always an empty
    ``tuple``. If one or more module objects are supplied, this object
    is a length-one tuple, with

     - the current exception as its sole element if any of the module \
    objects raised the exception;
     - a dynamically-created, "difficult to replicate" exception if \
    none of the module objects raised the exception.
    
    In other words, an ``except`` clause with a predicate of the
    form ``ExceptionFrom(mod1, mod2, ...)`` is entered only if one of
    ``mod1, mod2, ...`` raised the current exception, and no prior
    ``except`` clauses have entered.

    Different behavior is acheived through the ``root_only`` keyword
    only argument. When set to ``False`` (default is ``True``), the
    sole element of this object is the current except if one of the
    input module objects raised at any point in the current exception's
    chain.

    When called in an expression assignment, this object acts to scrape
    exception types raised in the module object sources. For example,
    obtain a tuple of exception types raised in ``re``, the expression
    ``exceptlib.ExceptionFrom(re)`` can be used and bound to some
    variable. To scrape exception types raised by a containing module,
    the classmethod ``exceptlib.ExceptionFrom.here`` can be used.
    """

    def __new__(cls, *target_modules: ModuleType, **kwargs: dict) -> tuple:
        """:return tuple: zero or more exceptions
        
        :param *target_modules: zero or more module objects
        :param **kwargs: optional keyword arguments
        
        Accept zero or more module objects, WIP.
        """
        logger.debug("ExceptionFrom.__init__: enter")

        # enter assume handling exception by module
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type is not None:
            target_is_involved = evaluate_implicated(
                get_traceback_modules(exc_traceback),
                target_modules,
                root_only=kwargs.get("root_only", True)
            )

            # set class to a tuple with the current exception
            if target_is_involved:
                return tuple.__new__(cls, (exc_value,))

            # or impossible exception if target module(s) not involved
            return tuple.__new__(cls, (random_exception()(),))

        # or enter scraping functionality if no current exception
        return tuple.__new__(cls, get_raised(*target_modules))

    @classmethod
    def here(
        cls,
        *exclude: BaseException,
        from_file: bool=False
    ) -> tuple[BaseException]:
        """:return tuple[BaseException]: scraped exception types
        
        :param *exclude: zero or more excluded exception types
        :param search_space: ``None`` or sequence of name-module maps

        Return a tuple of distinct exception classes found in the
        calling module. This classmethod searches the module's AST
        for ``raise`` statements, extracts their exception class, and
        adds them to an internal set. After the search, the set is cast
        to an exception tuple and returned.

        Zero or more exceptions can be passed in to indicate they
        should be excluded. By default, this classmethod searches both
        ``sys.modules`` and ``globals()`` to find a module object whose
        name matches ``__name__``.
        """
        logger.debug("ExceptionFrom.here: enter")
        path_obj = Path(__file__)

        # return empty tuple when nothing to parse
        if not path_obj.exists():
            return cls()

        # obtain module in which this is called
        if from_file:
            module = module_from_spec(
                spec_from_file_location(__name__, __file__)
            )
        else:
            module = globals().get(__name__) or sys.modules.get(__name__)

        # raise if no module or return exceptions less excluded
        if module is None:
            raise NameError("unable to find module %s", __name__)
        return cls(e for e in get_raised(module) if e not in exclude)


def get_raised(
    *modules: ModuleType, file_encoding="utf-8"
) -> tuple[BaseException]:
    """:return tuple[BaseException]: scraped exception types
    
    :param *modules: one or more modules to scrape
    :param file_encoding: string representing encoding of module files
    
    Accept zero or more module objects and scrape raise clauses from
    their ASTs, exctracting each exception type. Return a tuple of the
    distinct exception types found.
    """
    logger.debug("get_raised: enter")

    # don't handle builtin modules
    if any(m.__name__ in sys.builtin_module_names for m in modules):
        logger.error("get_raised: encountered builtin; modules=%s", modules)
        raise ValueError("builtin modules are not currently supported")

    # ensure result contains distinct exception types
    exceptions = set()

    # search in all input module objects
    for module in modules:

        # using ast.walk as traversal
        module_source = Path(inspect.getfile(module)).read_text(file_encoding)
        for node in ast.walk(ast.parse(module_source)):

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
            if (exception_type := getattr(module, name_id, None)) is not None:
                exceptions.add(exception_type)
            else:
                exceptions.add(eval(name_id)) # pylint: disable=W0123

    # instantiate and return exception tuple
    return tuple(exceptions)


def get_traceback_modules(exc_traceback: TracebackType) -> tuple[tuple]:
    """:return tuple[tuple]: of module objects
    
    :param exc_traceback: traceback object to extract modules from
    """

    # loop over frames and modules
    result = []
    for frame in traceback.walk_tb(exc_traceback):
        for module in sys.modules.values():
            if getattr(module, "__file__", "") == frame.f_code.co_filename:
                result.append(module)

    # recast and return result
    return tuple(result)


def evaluate_implicated(
    involved_modules: tuple[ModuleType],
    target_modules: tuple[ModuleType],
    root_only: bool=True
) -> bool:
    """:return bool: the module is involved or not
    
    :param involved_modules: tuple of modules involved in the exception
    :param target_modules: tuple of target modules
    :param root_only: flag to tune target module qualification
    
    Given ``involved_modules``, a tuple of module objects extracted
    from an exception's tracebacks, compare to ``target_modules``, a
    tuple of arbitrary module objects. If any from ``target_modules``
    matches the last in ``involved_modules`` (i.e. the exception's
    root module), return ``True``.

    Set ``root_only`` to ``False`` to return ``True`` when *any one of*
    ``target_modules`` is an element in ``involved_modules``.
    """
    logger.debug("evaluate_implicated: enter")

    # when there is module proper that raised
    if not involved_modules:
        return False

    # when concern is about the root module that raised is a target
    if root_only:
        involved_modules = involved_modules[-1:]

    # return result
    if not set(involved_modules).isdisjoint(set(target_modules)):
        return True
    return False


def get_modules_from_filename(
    file_name: str, search_space: Sequence, ensure_exists: bool=True
) -> tuple[ModuleType]:
    """:return tuple[ModuleType]:
    
    :param file_name: file name string
    :param search_space: arbitrary mapping
    :param ensure_exists: 
    
    Accept a filename and attempt to find it as a __file__ attribute of
    ModuleType values in a search space dictionary. Return a tuple
    whose elements are modules that match the input filename.
    
    By default, the input filename must exist for the search to be
    performed; ``ValueError`` is raised if it does not. To alter this
    default behavior, set optional parameter ``ensure_exists`` to
    ``False``.
    """
    logger.debug("mod_from_filename: enter; file_name=%s", file_name)

    # ensure file_name refers to existing file
    if ensure_exists and not Path(file_name).exists():
        logger.error(
            "mod_from_filename: DNE or is builtin; file_name=%s", file_name
        )
        raise ValueError("module file name DNE, possible builtin")

    # look for and return matches
    matches = []
    for value in search_space:
        if getattr(value, "__file__", None) == file_name:
            logger.debug("mod_from_filename: mod=%s", value.__name__)
            if isinstance(value, ModuleType):
                matches.append(value)
    return tuple(matches)


def get_code_filenames(exception: BaseException) -> tuple[str]:
    """:return tuple[str]: of involved module filenames
    
    :param exception: exception object to extract filenames from
    
    Accept an exception instance and walk through its tracebacks,
    appending to a results list each file name found in the
    corresponding code object. Return the list as a tuple.
    """
    logger.debug("get_code_filenames: enter")
    result = []

    # extract code filename from all frames from all tracebacks
    for traceback in get_tracebacks(exception):
        frame = traceback.tb_frame
        while frame is not None:
            result.append(frame.f_code.co_filename)
            frame = frame.f_back

    return tuple(result)


def get_tracebacks(exception: BaseException) -> tuple[TracebackType]:
    """:return tuple[TracebackType]:
    
    :param exception: exception object to extract tracebacks from

    Accept an exception instance and return a tuple containing its
    traceback objects, ordered latest to earliest.
    """
    logger.debug("get_tracebacks: enter")
    result = []

    if not isinstance(exception, BaseException):
        logger.error(
            "get_tracebacks: not an exception; exception=%s", exception
        )
        raise ValueError("input not of type BaseException")

    # bind first exception and begin loop if not none
    traceback = exception.__traceback__
    while traceback is not None:

        # append at first in loop then rebind to next traceback
        result.append(traceback)
        traceback = traceback.tb_next
    return tuple(result)


def get_exception_chain(
    exception_obj: tuple | BaseException, earliest_first: bool=True
) -> tuple[BaseException]:
    """:return tuple[BaseException]:
    
    :param exception_obj: ``exc_info`` triple or exception instance
    :param earliest_first: boolean sorting flag

    Accept a ``sys.exc_info``-like triple or an exception instance, and
    accumulate it and any chained exceptions. Return a tuple of these
    exceptions in earliest-to-latest order by default. Set
    ``earliest_first`` to ``False` to return in latest-to-earliest
    order.
    """
    logger.debug("get_exception_chain: enter")

    # preprocess and initialize result containter
    if is_hot_exc_info(exception_obj):
        exception_obj = exception_obj[1]
    if not isinstance(exception_obj, BaseException):
        raise ValueError("input not an exception or exc_info tuple")
    result = [exception_obj]

    # get any other chained exceptions
    while True:

        # enter if: raise new_exc from original_exc
        if exception_obj.__cause__ is not None:
            exception_obj = exception_obj.__cause__

        # enter if: raised without from keyword during original_exc
        #           or with from None
        elif exception_obj.__context__ is not None:
            exception_obj = exception_obj.__context__

        # break if no chain or end of chain and maybe append
        else:
            break
        result.append(exception_obj)

    # maybe reverse and then return
    if earliest_first:
        result.reverse()
    return tuple(result)


def is_hot_exc_info(obj: Any) -> bool:
    """:return bool:
    
    :param obj: object to inspect
    
    Accept any object and determine if it is a triple, along the lines
    of what ``sys.exc_info`` returns when the interpreter is handling an
    exception.
    """
    logger.debug("is_exc_info: enter")
    if isinstance(obj, tuple) and len(obj) == 3:
        if obj[0] is None:
            return False
        if isinstance(obj[1], obj[0]) and isinstance(obj[2], TracebackType):
            return True
    return False


def f(tb):
    while tb.tb_next is not None:
        tb = tb.tb_next
    
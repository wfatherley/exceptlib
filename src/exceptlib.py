"""Exception handling tools."""
import ast
import inspect
import sys

from functools import reduce
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
    """:return BaseException:
    
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
    
    This ``BaseException`` subclass exists to support the need for a
    an exception that cannot happen during runtime. In this way, its
    similar to the return value of ``random_exception``, but doesn't
    involve dynamic class creation.
    """

    def __init_subclass__(cls) -> None:
        """:return None:"""
        raise TypeError("subclassing not recommended")


class ExceptionFrom(tuple):
    """A tuple subclass for use in exception handling.
    
    This `tuple` subclass is designed to be the predicate of an
    ``except`` clause. Rather than containing elements of type
    ``BaseException``, this object contains elements of type
    ``types.ModuleType``. The functionality during exception
    handling events is therefore to handle the current exception by
    module.
    """

    def __new__(cls, *target_modules: ModuleType, **kwargs: dict) -> tuple:
        """:return tuple:
        
        :param *target_modules: sequence of module objects
        :param **kwargs: optional keyword arguments
        
        Construct class, a tuple of zero or more exception types. The
        elements in this tuple depend on two factors-- if the thread
        has a current exception and which module objects are passed in.

        When there is a current exception and one of the input module
        objects raised the exception, then this is a length-one tuple
        whose element is the exception type. There is an optional
        keyword argument, ``root_only``, which when set to ``False``
        makes this a length-one tuple of the current exception type if
        any of the input module objects was involved in any of the
        current exception's tracebacks. The aim is to enter exception
        handling based on module by calling this class in an ``except``
        clause. If there are no input modules passed in, this is a
        length-zero tuple.

        When there is no current exception, and no input modules, this
        is a length-zero tuple. Otherwise, this is a variable length
        tuple of the distinct exception types raised by the one or more
        input module objects. This behavior can be used to construct
        exception groups.
        """
        logger.debug("ExceptionFrom.__init__: enter")

        # enter assume handling exception by module
        if exception_chain := get_exception_chain(sys.exc_info()):
            target_is_involved = evaluate_implicated(
                get_modules(exception_chain[0]),
                target_modules,
                root_only=kwargs.get("root_only", True)
            )

            # set class to a tuple with the current exception
            if target_is_involved:
                return tuple.__new__(cls, (exception_chain[-1],))

            # or impossible exception if target module(s) not involved
            return tuple.__new__(cls, (random_exception()(),))

        # or enter scraping functionality if no current exception
        return tuple.__new__(cls, get_raised(*target_modules))

    @classmethod
    def here(cls, *exclude: BaseException) -> tuple[BaseException]:
        """:return tuple[BaseException]:
        
        :param *exclude: zero or more exception objects

        Return a tuple of distinct exception classes found in the
        calling module. This classmethod searches the module's AST
        for ``raise`` statements, extracts their exception class, and
        adds them to an internal set. After the search, the set is cast
        to an exception tuple and returned.

        Zero or more exceptions can be passed in to indicate they
        should be excluded.
        """
        logger.debug("ExceptionFrom.here: enter")
        path_obj = Path(__file__)

        # return empty tuple when nothing to parse
        if not path_obj.exists():
            return cls()

        # use a fresh module
        module = module_from_spec(
            spec_from_file_location(__name__, __file__)
        )
        return cls(e for e in get_raised(module) if e not in exclude)


def get_raised(
    *modules: ModuleType, file_encoding="utf-8"
) -> tuple[BaseException]:
    """:return tuple[BaseException]:
    
    :param *modules: one or more input modules
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


def evaluate_implicated(
    involved_modules: tuple[ModuleType],
    target_modules: tuple[ModuleType],
    root_only: bool=True
) -> bool:
    """:return bool:
    
    :param involved_modules: tuple of modules involved in the exception
    :param target_modules: tuple of target modules
    :param root_only: flag to tune target module qualification
    
    Given ``involved_modules``, a tuple of module objects extracted
    from an exception's tracebacks, compare to ``target_modules``, a
    tuple of arbitrary module objects. If any from ``target_modules``
    matches the last in ``involved_modules`` (i.e. the exception's
    root module), return ``True``.

    Set ``root_only`` to ``False`` to return ``True`` when any one of
    ``target_modules`` is an element in ``involved_modules``.
    """
    logger.debug("evaluate_implicated: enter")

    # when there is module proper that raised
    if not involved_modules:
        return False

    # when concern is about the root module that raised is a target
    if root_only:
        involved_modules = involved_modules[-1]

    # when concern that any target was involved in the raising
    else:
        involved_modules = reduce(lambda x,y: x + y, involved_modules)

    # return result
    if not set(involved_modules).isdisjoint(set(target_modules)):
        return True
    return False


def get_modules(exception: BaseException, **search_kwargs) -> tuple[tuple]:
    """:return tuple[tuple]:
    
    :param exception: exception object to extract modules from
    :param **search_kwargs: optional keyword arguments
    
    Accept one exception instance and return a tuple of tuples. Each
    tuple in the containing tuple contains at least one module object,
    corresponding to a particular traceback object bound to the
    exception instance. The last tuple corresponds to the very first
    traceback object so that the module it contains is the module that
    first raised.

    Pass additional keyword arguments to tune behavior. For example,
    ``search_space`` is a mapping in which module objects are found,
    given the file name extracted from a traceback object. This is
    necessary since multiple of one module may exist while only one
    raised. Pass in ``ensure_exists`` to ensure a particular filename
    exists during the search for module objects.
    """
    logger.debug("get_modules: enter")

    # unpack search keyword arguments for clarity
    ensure_exists = search_kwargs.get("ensure_exists", True)
    search_space = search_kwargs.get(
        "search_space", (sys.modules.values(), globals().values())
    )

    # loop over code filenames found in each traceback of exception
    result = []
    for filename in get_code_filenames(exception):
        for search_space_item in search_space:

            # search for modules by filename in search spaces
            modules = get_modules_from_filename(
                    filename, search_space_item, ensure_exists=ensure_exists
                )
            if modules:
                result.append(modules)

    # recast and return result
    return tuple(result)


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
    """:return tuple[str]:
    
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

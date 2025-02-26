"""Exception handling tools."""
import ast
import sys
import traceback

from collections import defaultdict
from functools import reduce
from logging import getLogger
from pathlib import Path
from random import sample
from string import ascii_letters
from types import ModuleType, TracebackType
from typing import Any, Generator


logger = getLogger(__name__)


# standard exceptions and associated data structures
std_excs = standard_exceptions = (
    BaseException,
    GeneratorExit,
    KeyboardInterrupt,
    SystemExit,
    Exception,
    ArithmeticError,
    FloatingPointError,
    OverflowError,
    ZeroDivisionError,
    AssertionError,
    AttributeError,
    BufferError,
    EOFError,
    ImportError,
    ModuleNotFoundError,
    LookupError,
    IndexError,
    KeyError,
    MemoryError,
    NameError,
    UnboundLocalError,
    OSError,
    BlockingIOError,
    ChildProcessError,
    ConnectionError,
    BrokenPipeError,
    ConnectionAbortedError,
    ConnectionRefusedError,
    ConnectionResetError,
    FileExistsError,
    FileNotFoundError,
    InterruptedError,
    IsADirectoryError,
    NotADirectoryError,
    PermissionError,
    ProcessLookupError,
    TimeoutError,
    ReferenceError,
    RuntimeError,
    NotImplementedError,
    RecursionError,
    StopAsyncIteration,
    StopIteration,
    SyntaxError,
    IndentationError,
    TabError,
    SystemError,
    TypeError,
    ValueError,
    UnicodeError,
    UnicodeDecodeError,
    UnicodeEncodeError,
    UnicodeTranslateError,
    Warning,
    BytesWarning,
    DeprecationWarning,
    EncodingWarning,
    FutureWarning,
    ImportWarning,
    PendingDeprecationWarning,
    ResourceWarning,
    RuntimeWarning,
    SyntaxWarning,
    UnicodeWarning,
    UserWarning,
)

# not available before 3.11
try:
    standard_exceptions += (
        BaseExceptionGroup, ExceptionGroup, # pylint: disable=E0602
    )
except NameError:
    pass

# not available before 3.13
try:
    standard_exceptions += (PythonFinalizationError,) # pylint: disable=E0602
except NameError:
    pass

# helpful data structures
std_exc_names = standard_exception_names = tuple(e.__name__ for e in std_excs)
std_excs_map = dict(zip(std_exc_names, std_excs))


class ExceptionFrom(tuple):
    """A ``tuple`` subclass for use in exception handling.

    There are two applications for this class. The first is to allow
    exception handlers to enter based on module rather than exception.
    For example, ``except ExceptionFrom(re): ...`` enters if the
    interpreter's current exception involved or originated from ``re``.
    
    By default, the calling exception handler will enter if any of
    modules passed to this class is the root cause of the active
    exception. To inhibit this behavior, i.e. the exception handler
    enters if any modules passed to this class is involved in the
    traceback or exception chain, set keyword only parameter to
    ``False``.
    
    This class does not influence the interpreter's exception handling
    priority mechanism, it simply allows a program to enter an
    exception handler based on module.

    The second application stems from its ability to scrape exception
    types from simple, pure-Python modules. When the interpreter has
    no current exception, the call ``ExceptionFrom(re)`` returns a
    tuple containing distinct exception types raised in the module
    ``re``.
    """

    def __new__(cls, *target_modules: ModuleType, **kwargs: dict) -> tuple:
        """:return tuple: zero or more exceptions
        
        :param *target_modules: zero or more module objects
        :param **kwargs: optional keyword arguments

        Construct a tuple of exception types based on some number of
        modules passed inline. The behavior of this class depends on if
        there is an active exception held by the interpreter:
        
        Return a tuple with the active exception as its sole element if
        any modules passed in is the root cause in raising the active
        exception. If none of the modules is the root cause, return a
        tuple whose sole element is a random exception (see
        ``exceptlib.random_exception``). Set keyword only parameter
        ``root_only`` (defaults to ``True``) to ``False`` so that a
        tuple with the active exception is returned only if any of the
        modules is at least involved by record of the tracebacks in the
        exception chain.

        If there is no active exception, return a tuple of unique
        exception types raised by the modules passed inline.
        """
        logger.debug("ExceptionFrom.__new__: enter")

        # give nothing for nothing
        if not target_modules:
            return tuple.__new__(cls, ())

        # support pure-python, file-based modules for now
        for module in target_modules:
            if not isinstance(module, ModuleType):
                logger.error(
                    "ExceptionFrom.__new__: bad_types=%s", target_modules
                )
                raise TypeError("target modules must be of type ModuleType")
            if not getattr(module, "__file__", "").endswith(".py"):
                logger.error(
                    "ExceptionFrom.__new__:: unsupported_module=%s", module
                )
                raise ValueError(f"unsupported module: {str(module)}")

        # case when there is a current exception
        if exc_info_chain := exc_infos():

            # extract modules from tracebacks
            traceback_modules = ()
            if kwargs.get("root_only", True):
                traceback_modules += (
                    get_traceback_modules(exc_info_chain[-1][-1])[-1],
                )
            else:
                for _, _, tb in exc_info_chain:
                    traceback_modules += get_traceback_modules(tb)

            # return tuple with current exception if target module raised
            if not set(traceback_modules).isdisjoint(set(target_modules)):
                return tuple.__new__(
                    cls, (exc_info[0] for exc_info in exc_info_chain)
                )

            # otherwise return tuple with random exception
            return tuple.__new__(cls, (random_exception(),))

        # case when there is no current exception
        return tuple.__new__(cls, get_raised(*target_modules))


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

    # ensure result contains distinct exception types
    exceptions = set()

    # for each input module
    for module in modules:

        # parse the module ast
        module_node = ast.parse(
            Path(module.__file__).read_text(encoding=file_encoding)
        )

        # walk through raise nodes and accumulate exceptions
        for raise_node in raise_nodes_from_module_node(module_node):
            exc_name = _id_from_call_or_name_node(raise_node.exc)
            exc_type = getattr(module, exc_name, std_excs_map.get(exc_name))
            if exc_type is None:
                node = ast.dump(raise_node)
                logger.error("get_raised: bad_raise=%s", node)
                raise RuntimeError(f"can't find excpetion from raise: {node}")
            exceptions.add(exc_type)

    # instantiate and return exception tuple
    return tuple(exceptions)


def _id_from_call_or_name_node(node: ast.Call | ast.Name) -> str | None:
    """:return str | None:
    
    :param node: instance of ``ast.Call`` or ``ast.Name``

    Extract the ``id`` attribute of the input node and return it.
    """
    logger.debug("_id_from_call_or_name_node: enter")

    # raise for bad nodes types
    if not isinstance(node, (ast.Call, ast.Name)):
        node = ast.dump(node)
        logger.error("_id_from_call_or_name_node: bad_node=%s", node)
        raise TypeError(f"expected ast.Call or ast.Name, got {node}")

    # extract and return id
    exc_type_name = None
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            return exc_type_name
        exc_type_name = node.func.id
    elif isinstance(node, ast.Name):
        exc_type_name = node.id
    return exc_type_name


def raise_nodes_from_module_node(module: ast.Module) -> tuple[ast.Raise]:
    """:return tuple[ast.Raise]: sequence of ``ast.Raise`` instances

    :param module: an ``ast.Module`` instance to scrape

    Accept an ``ast.Module`` instance and scrape instances of
    ``ast.Raise`` from it. Return a tuple of them, such that their
    ``exc`` attributes are ``ast.(Call | Name)`` objects corresponding
    to an actual exception, rather than a variable name or exception
    handler name that aliases an exception.
    """
    logger.debug("raise_nodes_from_module_node: enter")
    exc_handlers = []
    name_map = defaultdict(list)
    raise_nodes = []
    for node in ast.walk(module):
        if isinstance(node, ast.Assign):
            name_map = _update_name_map(node, name_map)
        elif isinstance(node, ast.ExceptHandler):
            exc_handlers.append(node)
            name_map = _update_name_map(node, name_map)
        elif isinstance(node, ast.Raise):
            raise_nodes.append(node)
    for i, node in enumerate(raise_nodes):
        raise_nodes[i] = _handle_raise_node(node, exc_handlers, name_map)
    return reduce(lambda x, y: x + y, raise_nodes)


def _handle_raise_node(
    node: ast.Raise, exc_handlers: list, name_map: dict
) -> tuple[ast.Raise]:
    """:return tuple[ast.Raise]:
    
    :param node: instance of ``ast.Raise`` to parse
    :param exc_handlers: list of exception handler encountered
    :param name_map: dictionary to update with node information
    
    Process an ``ast.Raise`` instance, and return it and possibly
    others in a tuple. Processing involves replacing its exc attribute
    with a ``ast.Call`` or ``ast.Name`` instance. For example when the
    exc attribute is an exception handler name or a variable name. When
    the raise statement is bare, it's also possible that a cognate
    exception handler specifies more than one exception, so include an
    ``ast.Raise`` instance for each one.
    """
    logger.debug("_handle_raise_node: enter")

    # return value
    nodes = []

    # case a bare raise
    if node.exc is None:

        # first check if raise is in except block
        parent_exc_handler = None
        for exc_handler in exc_handlers:
            for exc_handler_child in ast.walk(exc_handler):
                if id(exc_handler_child) == id(node):
                    parent_exc_handler = exc_handler

        # add RuntimeError raise if bare and outside exc handler
        if parent_exc_handler is None:
            nodes.append(
                ast.Raise(exc=ast.Name("RuntimeError"), cause=node.cause)
            )

        # add BaseException raise if exception handler is also bare
        elif parent_exc_handler.type is None:
            nodes.append(
                ast.Raise(exc=ast.Name("BaseException"), cause=node.cause)
            )

        # add raise with exception handler exception
        elif isinstance(parent_exc_handler.type, (ast.Call, ast.Name)):
            nodes.append(
                ast.Raise(exc=parent_exc_handler.type, cause=node.cause)
            )

        # add all raises from tuple of exception handler exceptions
        elif isinstance(parent_exc_handler.type, ast.Tuple):
            for elt in parent_exc_handler.type.elts:
                nodes.append(ast.Raise(exc=elt, cause=node.cause))

        # raise if exception could not be found
        else:
            node = ast.dump(node)
            logger.error("_handle_raise_node: bad_raise=%s", node)
            raise RuntimeError(f"couldn't find exception: {node}")

    # case not bare raise
    else:
        exc_name = _id_from_call_or_name_node(node.exc)
        exc = node.exc

        # possibly get actual exception from alias
        if name_map.get(exc_name, []):
            for exc_name, exc in _generate_assignment_chain(name_map, exc_name):

                # check exception handler names
                for exc_handler in exc_handlers:
                    if exc_handler.name != exc_name:
                        continue
                    if isinstance(exc_handler.type, ast.Tuple):
                        for elt in exc_handler.type.elts:
                            nodes.append(ast.Raise(exc=elt, cause=node.cause))
                    elif isinstance(exc_handler.type, (ast.Call, ast.Name)):
                        nodes.append(
                            ast.Raise(exc=exc_handler.type, cause=node.cause)
                        )

        # then add to nodes
        nodes.append(ast.Raise(exc=exc, cause=node.cause))

    # return tuple of raise nodes
    return tuple(nodes)


def _generate_assignment_chain(name_map: dict, key: str) -> Generator:
    """":return Generator: generates chained assignments
    
    :param name_map: dictionary of name-node pairs
    :param key: starting target name
    
    Accept a mapping of name-node pairs and a key. Starting with the
    key, find the corresponding node and yield it. Use that node's name
    as the key to find another node. Keep going until the key is not in
    the mapping and return.
    """
    logger.debug("_generate_assignment_chain: enter")
    if key not in name_map:
        return
    while key in name_map:
        value = name_map[key][-1]
        yield key, value
        key = None
        if isinstance(value, ast.Name):
            key = _id_from_call_or_name_node(value)


def _update_name_map(
    node: ast.Assign | ast.ExceptHandler, name_map: dict
) -> dict:
    """:return dict:
    
    :param node: node to parse
    :param name_map: dictionary to update with node information

    Accept an ``ast.Assign`` or ``ast.ExceptHandler`` node, extract a
    name-value pair from it, update ``name_map`` with the name-value
    pair, and return ``name_map``.

    A name-value pair for ``ast.ExceptHandler`` objects are its name
    and type attributes, respectively. If its name attribute is
    ``None``, this function does not update ``name_map``.

    More than one name-value pair can be extracted from an
    ``ast.Assign`` instance. Name-value pairs in this case are the
    target and value attributes, respectively.
    """
    logger.debug("_update_name_map: enter")

    # only handle assign and exc handler nodes
    if not isinstance(node, (ast.Assign, ast.ExceptHandler)):
        node = ast.dump(node)
        logger.error("_update_name_map: bad_node=%s", node)
        raise TypeError(
            f"expected ast.Assign or ast.ExceptHandler, got {node}"
        )

    # case node is assign
    if isinstance(node, ast.Assign):

        # update stacks in name map with most recent assignments
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            name_map[target.id].append(node.value)

    # case node is exception handler
    elif isinstance(node, ast.ExceptHandler):

        # update a stack with its most recent assignment
        if node.name:
            name_map[node.name].append(node.type)

    # return the map
    return name_map


def random_exception(name: str=None, **attributes: dict) -> BaseException:
    """:return BaseException: a ``BaseException`` subclass
    
    :param name: optional subclass name string
    :param **attributes: a mapping of attributes and methods

    Dynamically create and return a ``BaseException`` subclass. When
    called without parameter ``name``, the returned subclass will
    have a random 15-character (alpha only) name. Without any
    keyword arguments, it will inheret ``BaseException.__dict__``.

    The purpose of this function is to provide programs with the
    ability to utilize private exceptions-- since the name and type of
    the return value are created at runtime, it's not possible for an
    exception handler to handle it unless the exception handler itself
    has dynamic abilities. This function is used by ``exceptlib`` to
    permit an interpreter to escape an exception handler that calls
    ``exceptlib.ExceptionFrom`` with uninvolved modules.
    """
    logger.debug("random_exception: enter")
    name = name or "".join(sample(ascii_letters, 15))
    return type(name, (BaseException,), attributes)


def get_traceback_modules(exc_traceback: TracebackType) -> tuple[ModuleType]:
    """:return tuple[ModuleType]: modules extracted from traceback
    
    :param exc_traceback: traceback object to extract modules from

    Walk through the active exception's traceback and accumulate module
    objects by inspecting file name attributes of code objects. Return
    a tuple of the module objects.
    """
    logger.debug("get_traceback_modules: enter")

    # avoid looping over sys.modules in the loop over tracebacksimprove
    sys_modules = {
        v.__file__: v for v in sys.modules.values() if hasattr(v, "__file__")
    }

    # accumulate modules in most-recent-call-last order
    result = []
    for frame, _ in traceback.walk_tb(exc_traceback):
        code = frame.f_code
        if hasattr(code, "co_filename"):
            module = sys_modules.get(code.co_filename)
            if module is not None:
                result.append(module)
    return tuple(result)


def exc_infos() -> tuple[tuple]:
    """:return tuple[tuple]:
    
    Return a tuple of ``sys.exc_info``-like triples for the current
    exception's entire ``__context__`` chain, including itself.
    If there is no current exception, return an empty tuple.
    """
    logger.debug("exc_infos: enter")
    result = [sys.exc_info()]
    if result[-1][0] is None:
        return ()
    while result[-1][1].__context__ is not None:
        result.append(
            (
                type(result[-1][1].__context__),
                result[-1][1].__context__,
                result[-1][1].__context__.__traceback__
            )
        )
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
        if (
            isinstance(obj[0], BaseException)
            and isinstance(obj[1], obj[0])
            and isinstance(obj[2], TracebackType)
        ):
            return True
    return False

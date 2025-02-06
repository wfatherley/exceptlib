"""Exception handling tools."""
import ast
import inspect
import sys
import traceback

from collections import defaultdict
from logging import getLogger
from pathlib import Path
from random import sample
from string import ascii_letters
from types import ModuleType, TracebackType
from typing import Any

from importlib.util import module_from_spec, spec_from_file_location


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


class ExceptionFrom(tuple):
    """A ``tuple`` subclass for use in exception handling.

    There are three applications for this class. The first is to allow
    exception handlers to enter based on module rather than exception.
    For example, ``except ExceptionFrom(re): ...`` enters if the
    interpreter's current exception originated from ``re``. This class
    does not influence the interpreter's exception handling priority
    mechanism, it simply allows a program to enter an exception handler
    based on module.

    The second and third applications are simple exception scraping
    mechanisms. When the interpreter has no current exception, the
    call ``ExceptionFrom(re)`` returns a tuple containing distinct
    exception types raised in the module ``re``. Similarly, the call
    ``ExceptionFrom.here()`` returns a tuple of exceptions raised by
    the containing module.

    There are additional parameters available to tune the API described
    above, each discussed in their cognate memeber.
    """

    def __new__(cls, *target_modules: ModuleType, **kwargs: dict) -> tuple:
        """:return tuple: zero or more exceptions
        
        :param *target_modules: zero or more module objects
        :param **kwargs: optional keyword arguments
        """
        logger.debug("ExceptionFrom.__new__: enter")

        # give nothing for nothing
        if not target_modules:
            return tuple.__new__(cls, ())

        # only allow module types
        if any(not isinstance(m, ModuleType) for m in target_modules):
            raise TypeError("target modules must be of type ModuleType")

        # case when there is a current exception
        if exc_info_chain := exc_infos():

            # extract modules from tracebacks
            involved_modules = ()
            if kwargs.get("root_only", True):
                involved_modules += get_traceback_modules(
                    exc_info_chain[-1][-1]
                )
            else:
                for _, _, tb in exc_info_chain:
                    involved_modules += get_traceback_modules(tb)

            # return tuple with current exception if target module raised
            if not set(involved_modules).isdisjoint(set(target_modules)):
                return tuple.__new__(
                    cls, (exc_info[0] for exc_info in exc_info_chain)
                )

            # otherwise return tuple with random exception
            return tuple.__new__(cls, (random_exception(),))

        # case when there is no current exception
        return tuple.__new__(cls, get_raised(*target_modules))

    @classmethod
    def here(cls, *, from_file: bool=False) -> tuple[BaseException]:
        """:return tuple[BaseException]: scraped exception types
        
        :param from_file: set to ``True`` to load from file
        
        Return a tuple of exception classes raised by the calling
        module. If changes are applied to the module source during
        a runtime, it's possible to capture them by setting keyword-
        only parameter ``from_file`` to ``True``.
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
            raise NameError(f"unable to find module {__name__}")
        return cls(module)


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

        # map for name:exception-type pairs
        exc_alias_cache = {}

        # using ast.walk as traversal
        module_source = Path(inspect.getfile(module)).read_text(file_encoding)
        for node in ast.walk(ast.parse(module_source)):

            # update exception alias cache
            if not isinstance(node, ast.Raise):
                exc_alias_cache.update(
                    exc_alias_and_type_name_from_assign_ast(node) or {}
                )
                continue

            # otherwise obtain exception type name or alias
            exc_or_alias_name = exc_type_name_from_raise_ast(node)

            # add exception type if exception type name is found
            exc_type = getattr(module, exc_or_alias_name, None)
            if exc_type is not None:
                exceptions.add(exc_type)
            elif exc_type := std_excs_map.get(exc_or_alias_name) is not None:
                exceptions.add(exc_type)

            # or interpolate a bare raise and add
            else:
                raise Warning("bare raise")

    # instantiate and return exception tuple
    return tuple(exceptions)


def exc_type_name_from_raise_ast(raise_node: ast.Raise) -> str | None:
    """:return str: name of exception in ``ast.Raise`` node
    
    :param raise_node: an instance of ``ast.Raise``

    Extract exception type name from an ``ast.Raise`` node and return
    it. For example, a raise node of the form
    ``raise TypeError("oops")`` will return the string ``"TypeError"``.
    Bare ``raise``s will result in ``None`` being returned, and a node
    raising a bound name (e.g.,
    ``raise alias_to_an_exception_instance_or_class``) will return the
    bound name (i.e. ``alias_to_an_exception_instance_or_class``).
    """
    logger.debug("exc_name_from_raise_ast: enter")

    # raise for non-raise nodes
    if not isinstance(raise_node, ast.Raise):
        raise TypeError(f"expected ast.Raise, got {type(raise_node)}")

    # return None for bare raise
    if raise_node.exc is None:
        return None

    # otherwise return the exception type name or None
    return id_from_call_or_name_ast(raise_node.exc)


def exc_alias_and_type_name_from_assign_ast(assign_node: ast.Assign) -> dict | None:
    """:return dict:"""
    logger.debug("exc_alias_and_type_from_any_ast: enter")

    # raise for non-assign nodes
    if not isinstance(assign_node, ast.Assign):
        raise TypeError(f"expected ast.Raise, got {type(assign_node)}")

    # results container
    result = {}

    # obtain exception type name or return None if dne
    exc_type_name = id_from_call_or_name_ast(assign_node.value)
    if exc_type_name is None:
        return None

    # otherwise return exception type name for each bound name
    for name_node in assign_node.targets:
        result[name_node.id] = exc_type_name
    return result


def id_from_call_or_name_ast(
    node: ast.Call | ast.Name
) -> str | None:
    """:return str | None:
    
    :param node: instance of ``ast.Call`` or ``ast.Name``
    
    
    """
    logger.debug("id_from_call_or_name_ast: enter")

    # raise for bad nodes types
    if not isinstance(node, (ast.Call, ast.Name)):
        logger.exception("id_from_call_or_name_ast: got %s", type(node))
        raise TypeError(f"expected ast.Call or ast.Name, got {type(node)}")

    # extract id
    exc_type_name = None
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            exc_type_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            exc_type_name = node.func.value.id
    elif isinstance(node, ast.Name):
        exc_type_name = node.id
    return exc_type_name


def get_traceback_modules(exc_traceback: TracebackType) -> tuple[ModuleType]:
    """:return tuple[ModuleType]: modules extracted from traceback
    
    :param exc_traceback: traceback object to extract modules from
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


class ExceptionTypeScraper(ast.NodeVisitor):
    """Exception type scraper."""

    def __init__(self, module: ModuleType) -> None:
        """:return None:"""
        logger.debug("ExcTypeNameScraper.__init__: enter")

        # just set attributes
        self.module = module
        self.except_block_excs_stack = []
        self.exception_alias_cache = defaultdict(list)
        self.raised_exceptions = set()

        super().__init__()

    def exc_from_name(
        self, node_id: str
    ) -> BaseException | None:
        """:return BaseException | None:
        
        :param node_id: string representing exception name
        
        Return an exception type whose name is specified by ``node_id``
        or ``None.

        First check the exception alias cache for a match, in case
        the name is an alias of an exception. Then check
        ``self.module`` using ``getattr`` for a match, and then check
        ``exceptlib.std_excs_map``. Return the matched exception type
        or ``None``.
        """

        # search in various containers or return None
        if (exc_type := std_excs_map.get(node_id)) is not None:
            return exc_type
        elif (exc_type := getattr(self.module, node_id, None)) is not None:
            return exc_type
        

    def clear(self) -> None:
        """:return None:
        
        Clear the except-block stack and exception alias cache and
        module, then return ``None``.
        """

        # remove current module reference
        self.module = None

        # use container apis
        self.except_block_excs_stack.clear()
        self.exception_alias_cache.clear()
        self.raised_exceptions.clear()

    def id_from_call_or_name_ast(
        self, node: ast.Call | ast.Name
    ) -> str | None:
        """:return str | None:
        
        :param node: instance of ``ast.Call`` or ``ast.Name``

        Extract the ``id`` attribute of the input node and return it.
        """

        # raise for bad nodes types
        if not isinstance(node, (ast.Call, ast.Name)):
            raise TypeError(f"expected ast.Call or ast.Name, got {type(node)}")

        # extract id
        exc_type_name = None
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                return exc_type_name
            exc_type_name = node.func.id
        elif isinstance(node, ast.Name):
            exc_type_name = node.id
        return exc_type_name

    def visit_Assign(self, node: ast.Assign) -> None:
        """:return None:
        
        :param node: an instance of ``ast.Assign`` to inspect

        The purpose of having this method is to find exceptions that
        are bound to names in a module. This is necessary because some
        ``except`` clauses will use such names rather than using an
        exception class or instance.

        There are two different ways this can work: a name can be bound
        to a single exception class or instance, or it can be bound to
        a tuple of exception classes or instances.
        """
        logger.debug("ExcTypeNameScraper.visit_Assign: enter")

        # case assignment is directly to exception class or instance
        if isinstance(node.value, (ast.Call, ast.Name)):
            exc_name = self.id_from_call_or_name_ast(node.value)
            if exc_name is None:
                return
            exc_type = self.exc_from_name(exc_name)
            if exc_type is None or not issubclass(exc_type, BaseException):
                return

        # case assignment is to tuple of exception classes or instances
        elif isinstance(node.value, ast.Tuple):
            exc_types = []
            for elt in node.value.elts:
                if not isinstance(elt, (ast.Call, ast.Name)):
                    return
                exc_name = self.id_from_call_or_name_ast(elt)
                if exc_name is None:
                    return
                exc_type = self.exc_from_name(exc_name)
                if exc_type is None or not issubclass(exc_type, BaseException):
                    return
                exc_types.append(exc_type)
            exc_type = tuple(exc_types)

        # otherwise return
        else:
            return
        
        # add aliases to exception alias cache
        for name_node in node.targets:
            if not isinstance(name_node, ast.Name):
                node_dump = ast.dump(node)
                raise TypeError(f"unsupported assign object: {node_dump}")
            self.exception_alias_cache[name_node.id].append(exc_type)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """:return None:
        
        The purpose of this method is to maintain a stack of exceptions
        extracted from except clauses, earliest to latest.

        To do this, explicit exception types are simply added to the
        stack as the are found. If an exception class or instance has
        an alias, this method has to find the class or instance from
        the alias using the exception alias cache.
        """

        # case the handler is bare
        if node.type is None:
            exc_type = BaseException

        # case the handler has a single exception or alias
        elif isinstance(node.type, (ast.Call, ast.Name)):
            exc_name = self.id_from_call_or_name_ast(node.type)
            exc_type = self.exc_from_name(exc_name)
            if not issubclass(exc_type, BaseException):
                raise RuntimeError(f"not an exc or alias: {ast.dump(node)}")
            
        # case the handler has a tuple of exceptions or aliases
        elif isinstance(node.type, ast.Tuple):
            for i, elt in enumerate(node.type.elts):
                if not isinstance(elt, (ast.Call, ast.Name)):
                    return # can excs be any other ast node?
                exc_name = self.id_from_call_or_name_ast(elt)
                exc_type = self.exc_from_name(exc_name)
                if not issubclass(exc_type, BaseException):
                    return
                node.type.elts[i] = exc_type
            exc_type = tuple(node.type.elts)

        # append exception or tuple to stack
        self.except_block_excs_stack.append(exc_type)

        # handle aliasing
        if node.name is not None:
            self.exception_alias_cache[node.name].append(exc_type)
            if node.body:
                for child in node.body:
                    if not isinstance(child, ast.Raise):
                        continue
                    if hasattr(child.exc, "id") and child.exc.id == node.name:
                        self.raised_exceptions.add(exc_type)

    def visit_Raise(self, node: ast.Raise) -> None:
        """:return None:
        
        The purpose of having this method is to find exceptions to
        scrape from the module. There are several ways exceptions are
        raise:

        1. Directly in this node, either as a class or instance
        2. Directly in this node, but using an alias
        3. With this node bare, and an explicit except clause
        4. With this node bare and bare except clause
        """
        logger.debug("ExcTypeNameScraper.visit_Raise: enter")

        # find exception for a bare raise
        if node.exc is None:
            try:
                exc_type = self.except_block_excs_stack.pop()
            except IndexError as e:
                e.add_note(f"unable to extract from: {ast.dump(node)}")
                raise e

        # find exception for a non-bare raise
        else:
            print(ast.dump(node), "\n\n\n")
            exc_name = self.id_from_call_or_name_ast(node.exc)
            exc_type = self.exc_from_name(exc_name)

        if exc_type is None:
            raise RuntimeError(f"unable to extract from: {ast.dump(node)}")
        self.raised_exceptions.add(exc_type)

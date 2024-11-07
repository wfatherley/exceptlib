"""exceptlib"""
import ast
import inspect
import sys

from functools import reduce
from logging import getLogger
from pathlib import Path
from types import ModuleType
from typing import Tuple

from importlib.util import module_from_spec, spec_from_file_location


logger = getLogger(__name__)


class NotThisException(BaseException):
    """not this exception"""

    def __init_subclass__(cls) -> None:
        """return None"""
        raise Exception("subclassing not recommended")


class ExceptionFrom(tuple):
    """exception from tuple"""

    def __init__(self, *target_modules: ModuleType, **kwargs) -> None:
        """return None
        
        :param *target_modules: sequence of module objects
        :param **kwargs: optional keyword arguments
        

        """
        logger.debug("ExceptionFrom.__init__: enter")
        exc_typ, exc_val, _ = sys.exc_info()
        if exc_typ is not None:
            target_is_involved = evaluate_implicated(
                get_modules(exc_val),
                target_modules,
                root_only=kwargs.get("root_only", True)
            )
            if target_is_involved:
                super().__init__((exc_typ,))
            else:
                super().__init__((NotThisException,))
        else:
            super().__init__(get_raised(*target_modules))
    
    @classmethod
    def here(cls, *exclude: BaseException, **kwargs) -> Tuple[BaseException]:
        """return Tuple[BaseException]
        
        :param *exclude: zero or more exception objects
        :param **kwargs: zero or more configuration arguments

        Return a tuple of distinct exception classes found in the
        calling module. This classmethod searches the module's AST
        for `raise` statements, extracts their exception class, and
        adds them to an internal set. After the search, the set is cast
        to an exception tuple and returned.
        """
        logger.debug("ExceptionFrom.find: enter")
        path_obj = Path(__file__)
        if not path_obj.exists():
            raise Exception("not found; search in globals")
        module = module_from_spec(
            spec_from_file_location(__name__, __file__)
        )
        return cls(get_raised(module))


def get_raised(*modules: ModuleType) -> tuple:
    """return tuple"""
    logger.debug("get_raised: enter")
    exceptions = set()
    for module in modules:
        with open(inspect.getfile(module), "r") as file_obj:
            module_ast = ast.parse(file_obj.read())
        for node in ast.walk(module_ast):

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
            exceptions.add(eval(name_id))

    # instantiate and return exception tuple
    return tuple(exceptions)
    

def evaluate_implicated(
    involved_modules: tuple[ModuleType],
    target_modules: tuple[ModuleType],
    root_only: bool=True
) -> bool:
    """return bool"""
    logger.debug("evaluate_implicated: enter")
    if not involved_modules:
        return False
    if root_only:
        if not set(involved_modules[-1]).isdisjoint(set(target_modules)):
            return True
    else:
        involved_modules = reduce(lambda x,y: x + y, involved_modules)
        if not set(involved_modules).isdisjoint(set(target_modules)):
            return True
    return False


def get_modules(exception: BaseException, **search_kwargs) -> tuple:
    """return tuple"""
    logger.debug("get_modules: enter")
    ensure_exists = search_kwargs.get("ensure_exists", True)
    search_space = search_kwargs.get("search_space", (sys.modules, globals()))
    result = list()
    for filename in get_code_filenames(exception):
        for element in search_space:
            result.append(
                modules_from_filename(
                    element, search_space, ensure_exists=ensure_exists
                )
            )
    return tuple(result)


def get_code_filenames(exception: BaseException) -> tuple:
    """return tuple"""
    logger.debug("get_code_filenames: enter")
    result = list()
    for traceback in get_tracebacks(exception):
        result.append(traceback.tb_frame.f_code.co_filename)
    return tuple(result)


def get_tracebacks(exception: BaseException) -> tuple:
    """return tuple"""
    logger.debug("get_tracebacks: enter")
    result = list()
    traceback = exception.__exception__
    while traceback is not None:
        result.append(traceback)
        traceback = traceback.tb_next
    return tuple(result)


def modules_from_filename(
    file_name: str, search_space: dict, ensure_exists: bool=True
) -> tuple[ModuleType]:
    """return ModuleType
    
    :param file_name: file name string
    :param search_space: arbitrary mapping
    
    Accept a filename and attempt to find it as a __file__ attribute of
    ModuleType values in a search space dictionary. Return a list whose
    elements are modules that match the input filename.
    
    By default, the input filename must exist for the search to be
    performed; an empty list is returned when the it does not. To alter
    this default behavior, set optional parameter `ensure_exists` to
    `False`.
    """
    logger.debug("mod_from_filename: enter; file_name=%s", file_name)

    # ensure file_name refers to existing file
    if ensure_exists and not Path(file_name).exists():
        logger.debug("mod_from_filename: file not found")
        return tuple()

    # look for and return matches
    matches = list()
    for value in search_space.values():
        if hasattr(value, "__file__") and value.__file__ == file_name:
            logger.debug("mod_from_filename: mod=%s", value.__name__)
            if isinstance(value, ModuleType):
                matches.append(value)
    return tuple(matches)

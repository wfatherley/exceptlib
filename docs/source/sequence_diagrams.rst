``exceptlib`` sequence sequence_diagrams
========================================

WIP test


``exceptlib.ExceptionFrom.__new__``
-----------------------------------


.. mermaid::

    sequenceDiagram
        create participant Runtime
        create participant ExceptionFrom
        create participant exc_infos
        ExceptionFrom->>exc_infos:
        destroy exc_infos
        exc_infos->>ExceptionFrom: tuple
        alt active exception
            ExceptionFrom->>get_traceback_modules: TracebackType
            get_traceback_modules->>ExceptionFrom: tuple
        else not active exception
            ExceptionFrom->>get_raised: ModuleType
            get_raised->>ExceptionFrom: tuple
        end
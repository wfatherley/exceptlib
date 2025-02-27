``exceptlib`` sequence diagrams
===============================


``exceptlib.ExceptionFrom.__new__``
-----------------------------------

A shallow sequence diagram showing what happens when ``exceptlib.ExceptionFrom`` is called.

.. mermaid::

    sequenceDiagram
        create participant ExceptionFrom
        create participant exc_infos
        ExceptionFrom->>exc_infos: None
        destroy exc_infos
        exc_infos->>ExceptionFrom: tuple
        alt active exception
            alt modules involved
                ExceptionFrom->>get_traceback_modules: TracebackType
                get_traceback_modules->>ExceptionFrom: tuple
            else modules not involved
                ExceptionFrom->>random_exception: None
                random_exception->>ExceptionFrom: tuple
            end
        else not active exception
            ExceptionFrom->>get_raised: ModuleType
            get_raised->>ExceptionFrom: tuple
        end
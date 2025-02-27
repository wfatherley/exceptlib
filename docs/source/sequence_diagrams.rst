``exceptlib`` sequence diagrams
===============================


``exceptlib.ExceptionFrom.__new__``
-----------------------------------

A shallow sequence diagram showing what happens when ``exceptlib.ExceptionFrom`` is called.

.. mermaid::

    sequenceDiagram
        Runtime->>ExceptionFrom: tuple
        create participant exc_infos
        ExceptionFrom->>exc_infos: None
        destroy exc_infos
        exc_infos->>ExceptionFrom: tuple
        alt active exception
            ExceptionFrom->>get_traceback_modules: TracebackType
            get_traceback_modules->>ExceptionFrom: tuple
            alt modules involved
                ExceptionFrom->>Runtime: tuple
            else modules not involved
                ExceptionFrom->>random_exception: None
                random_exception->>ExceptionFrom: tuple
                ExceptionFrom->>Runtime: tuple
            end
        else not active exception
            ExceptionFrom->>get_raised: ModuleType
            get_raised->>ExceptionFrom: tuple
        end
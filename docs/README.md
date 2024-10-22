# `exceptlib` -- additional exception handling mechanisms

<hr>

## Summary
Exception handling in Python follows two main idioms-- catching one exception in the first `except` clause to specify its class or superclass, and catching in one or more `except*` clauses via [exception groups](https://docs.python.org/3/library/exceptions.html#exception-groups). Presented is an exception handling construct, suitable for use in both clauses, that catches by originating object. In the introduction section below, central concepts and definitions are discussed. Following the introduction, an outline of the idea is presented; an implementation is given with notes and intuition; and a discussion section finally yields an exapanded summary and future directions.

## Introduction
Exceptions occur in Python when something goes wrong. For example, `"abcd"[63]` raises `IndexError`. What to do with an exception is context dependent. As in any langauge, context varies over a spectrum. At one end, certain exceptions must be fatal, while at the other end a given exception is expected as flow of control and is suppressed. Although program design is not the main topic, a process to arrive somewhere on this spectrum with some codebase is summarized by [Joe Armstrong's *let it crash* principal](https://softwareengineering.stackexchange.com/a/421837), which is also covered in Python's [exception documentation](https://docs.python.org/3/tutorial/errors.html#handling-exceptions):

 > \[...\] it is good practice to be as specific as possible with the types of exceptions that we intend to handle, and to allow any unexpected exceptions to propagate on.
 
Exceptions are caught and handled in Python using the `except` and `except*` clauses. They both fit into the greater "try-except" scope, but behave differently.

### The `except` clause
One or more `except` clauses operate not unlike the "controller" construct of an MVC framework-- the first one to match is the first and only to enter:

```python
try:
    raise RuntimeError
except (IndexError, KeyError):
    ... # no enter
except RuntimeError:
    ... # enter
except SyntaxError:
    ... # no enter
except RuntimeError:
    ... # no enter
```

If for some reason there is no matching `except` clause, e.g. `TypeError` was raised instead of `RuntimeError` in the above snippet, then the error propogates toward any outer exception handling until it reaches the top level and causes the program to exit.

## Outline of idea
Python's `except` and `except*` clauses are designed to accept exception objects (and tuple objects in the former case) and act as a filtering mechanism to catch errors that may be handled. In most cases, a set of `traceback` objects equipped with corresponding `frame`s is available by the time a given clause is evaluated for entry. With this information considered, *what other filtering is possible?*

In light of the two key features of exceptions just mentione above, filtering and handling exceptions can be made dynamic and conditioned on features beyond exception typing. Presented in this gist is a mechanism to enter an `except` clause based on the emitting module. Here is a simple usage example of the idea:

```python
>>> import re, statistics, urllib
>>> 
>>> try:
>>>     my_bool = hasattr(urllib, "parse")           # no raise
>>>     my_other_bool = hasattr(statistics, "mean")  # no raise
>>>     my_re_obj = re.compile(7)                    # raise
>>> except exception_class_factory(statistics, urllib)
>>>     print("error came from statistics or urllib")
>>> except exception_class_factory(re):
>>>     print("error came from re")
>>> 
```

The idea is to enter an `except` clause not by exception type, but by module name.  In the usage example above, passing an integer to `re.compile` results in a `TypeError`, which is the only exception that'd raise in the `try` scope. Rather than specifying a handling mechaism with `except TypeError: ...`, exceptions are handled based on the module whose object failed. The output from above is:

```
error came from re
```



but In other words, exception handling is tuned to *a `KeyError` from module `re`* in a different `except` clause from *a `KeyError` from any other namespace*. The utility of the construct is to enhance the flexibility of certain scopes, such as a top-level runtime or a for-loop, where tradeoffs between resiliancy and complexity is a top consideration. Use in test suites for expediated regression analysis is also possible. 

Again, it turns out the initial pattern is after all not suitable:

```python
>>> try:
...     a = a
... except type("NameError", (NameError,), {}):
...     print(7)
... 
Traceback (most recent call last):
  File "<python-input-7>", line 2, in <module>
    a = a
        ^
NameError: name 'a' is not defined
```

So it seems the resolution of `NameError` doesn't seem possible, whether the name passed to `type` is `"NameError"` or anything else, and seemingly without regard to the name collision.

Anyway, there's more to the story. An except clause also evaluates a tuple instance whose values are all exception classes. In this way, can a tuple factory be designed to accept a set of names, inspect their corresponding code, and dymaically return a set of exceptions? With such a factory, it'd be possible to group exceptions by their origin into one `except` clause. Here's a contrived but suitablle sketch that functions correctly:

```python
>>> import re
>>> try:
...     a = a
... except (lambda name: (NameError,))(re):
...     print(7)
...     
7
```

Going a bit more in depth, how does the factory accumulate exceptions? The initial idea

```python
import sys, traceback
def f(*names):
    a = sys._current_exceptions()
    print(a[threading.get_ident()].__traceback__.tb_next.tb_frame.f_code.co_filename)
    return TypeError

def f(*names):
    a = sys._current_exceptions()
    trb = a[threading.get_ident()].__traceback__
    print(trb.tb_frame.f_code.co_filename)
    while True:
        trb = trb.tb_next
        if trb is None:
            print("done")
            break
        print(trb.tb_frame.f_code.co_filename)
    return TypeError

    # exc = sys.exception()
    # trb = exc.__traceback__
    # frm = trb.tb_frame
    # cod = frm.f_code
    # print(cod.co_name, cod.co_qualname, cod.co_filename)
    # for frame in traceback.walk_stack(trb.tb_frame):
    #     try:
    #         cod = frame.f_code
    #         print(cod.co_name, cod.co_qualname, cod.co_filename)
    #     except:
    #         break
    # return Exception

import re
import sys, traceback, threading
try:
    a = re.compile(7)
except f():
    raise
except TypeError:
    print(7)
    a = sys._current_exceptions()
    print(a[threading.get_ident()].__traceback__.tb_next.tb_frame.f_code.co_filename)
    frm = exc_tb.tb_frame
    cod = frm.f_code
    print(trb.tb_lasti, cod.co_name, cod.co_qualname, cod.co_filename)
    for frame in traceback.walk_stack(trb.tb_frame):
        try:
            cod = frame.f_code
            print(cod.co_name, cod.co_qualname, cod.co_filename)
        except:
            break
```

## reject cache
Turns out this initial eine of thinking is incorrect (excersice: why?), but the point is that there might be dozens of names that fail on one specific exception type, but the exception handling for any two subsets of names might be very different for the overall program.

The idea is to group exceptions raised by code in specific modules into `except` clauses.

## Usage patterns

```python

```

## Notes
Harden the the `NotThisException` class so that it can't be used.


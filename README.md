# `exceptlib` - exception handling mechanisms

<hr>

## Summary
Exceptions occur in Python when something goes wrong. For example, `"abcd"[63]` raises `IndexError`. What to do with an exception is context dependent-- in any langauge, context informs a spectrum of handling mechanisms. At one end, certain exceptions will or must be fatal, while at the other end a given exception acts as control of flow and is suppressed. A process to arrive somewhere on this spectrum is summarized by [Joe Armstrong's *let it crash* principal](https://softwareengineering.stackexchange.com/a/421837), which is also covered in Python's [exception documentation](https://docs.python.org/3/tutorial/errors.html#handling-exceptions):

> \[...\] it is good practice to be as specific as possible with the types of exceptions that we intend to handle, and to allow any unexpected exceptions to propagate on.

This experimental library extends Python's exception handling mechanism with two available functionalities as its API:

 - handling exceptions by module;
 - and exception class scraping from modules.

This library is under active development; it may require additional tuning and there are plans to add additional features.

## Usage notes
The main feature of `exceptlib` is handling exceptions by module through the `ExceptionFrom` class. For example:

```python
import re
import statistics
import urllib

from exceptlib import ExceptionFrom


try:
    a = parse.quote("python.org.:443/not found")  # no raise
    b = statistics.mean([1,2,3])                  # no raise
    c = re.compile(7)                             # raise TypeError
except ExceptionFrom(statistics, urllib):
    print("hello from statistics and urllib") # no print
except IndexError:
    print("it was index error")               # no print
except ExceptionFrom(re):
    print("hello from re")                    # print
except TypeError:
    print("it was a type error")              # no print
```

In the `try` block above, three calls are made with the last raising `TypeError`. When working to find a handler for this exception, the interpreter traverses the `except` blocks that follow, looking for the first one that specifies `TyperError`.

 - The first `except` block is set up to handle any exception arising from `statistics` or `urllib`, and is not entered since neither module raised;
 - because the current exception is not an instance of `IndexError`, the second `except` block is not enetered either;
 - since the error came from `re`, the third `except` block executes;
 - and since the third is entered, the last `except` block is not entered despite indicating `TypeError`.

The conceptual utilities of `exceptlib.ExceptionFrom` span program flexibility and development operations:

 - enable certain retries and fallbacks during runtime exceptions with less boilerplate;
 - enhance or simplify RCAs in test;
 - and generally widen the scope of `except` clauses.

In addition to its functionality as the predicate of the `except` statment, `exceptlib.ExceptionFrom` provides additional introspective functionality:

```python
...

# a tuple of distinct exceptions raised in this source file
excs_raised_here: tuple = ExceptionFrom.here()

# a tuple of distinct exceptions raised by the input modules
excs_raised_from: tuple = ExceptionFrom(re, urllib)
```

The `ExceptionFrom.here` class method is useful to scrape exceptions from a containing module, possibly for use in defining exception groups for example. Calling `ExceptionFrom` when there is no current exception will direct it to scrape distinct exceptions from `raise` statements in the specified modules.

## Install
This library is available through [PyPI](https://pypi.org/project/exceptlib/) and [GitHub](https://github.com/wfatherley/exceptlib).

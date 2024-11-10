# `exceptlib` - exception handling mechanisms

<hr>

## Summary
Exceptions occur in Python when something goes wrong. For example, `"abcd"[63]` raises `IndexError`. What to do with an exception is context dependent-- in any langauge, context informs a spectrum of handling mechanisms. At one end, certain exceptions will or must be fatal, while at the other end a given exception acts as control of flow and is suppressed. A process to arrive somewhere on this spectrum with some codebase is summarized by [Joe Armstrong's *let it crash* principal](https://softwareengineering.stackexchange.com/a/421837), which is also covered in Python's [exception documentation](https://docs.python.org/3/tutorial/errors.html#handling-exceptions):

> \[...\] it is good practice to be as specific as possible with the types of exceptions that we intend to handle, and to allow any unexpected exceptions to propagate on.

This experimental library extends Python's exception handling mechanism with two available functionalities as its API:

 - handling exceptions by module object;
 - and exception class scraping from module objects.

As this library is actively being developed, there are plans to add additional features aimed at profiling exceptions.

## Usage notes
The main feature `exceptlib` is handling exceptions by module. For example:

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

In the `try` block above, three calls are made with the last raising `TypeError`. When working to find a handler for this exception, the interpreter begins sequentially traversing the `except` blocks that follow, looking for the first one that specifies `TyperError`. The first `except` block is set up to handle any exception arising from `statistics` or `urllib`, and is not entered since neither module raised. Because the current exception is not an instance of `IndexError`, the second `except` block is not enetered either. Since the error came from `re`, the third `except` block is entered. And since the third is entered, the last `except` block is not entered despite indicating `TypeError`.

While this concrete example is contrived for demonstration, the utility of `exceptlib.ExceptionFrom` spans program flexibility and development operations:

 - enable certain retries and fallbacks during exception handling with less boilerplate;
 - enhance regression or performance testing facilities for 3rd party libraries;
 - widen the scope of `except` clauses.

In addition to its functionality as the predicate of `except` statments, `exceptlib.ExceptionFrom` provides additional introspective functionality through a class method and its constructor:

```python
import re, urllib

# a tuple of distinct exceptions raised in this source file
these_exc_tuple = ExceptionFrom.here()

# a tuple of distinct exceptions raised by the input modules
exc_tuple = ExceptionFrom(re, urllib)
```

The `ExceptionFrom.here` class method is useful to scrape exceptions from a containing module, possibly for use in defining exception groups for example. Calling `ExceptionFrom` when there is no current exception will direct its constructor to scrape distinct exceptions from the specified modules.

## Install
This library is available through [PyPI](https://pypi.org/project/exceptlib/) and [GitHub](https://github.com/wfatherley/exceptlib).

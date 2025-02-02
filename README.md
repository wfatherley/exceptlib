# `exceptlib` - exception handling mechanisms

<hr>

## Summary
Exceptions occur in Python when something goes wrong. For example, `"abcd"[63]` raises `IndexError`. What to do with an exception is context dependent-- in any langauge, context informs a spectrum of handling mechanisms. At one end, certain exceptions must be fatal, while at the other end a given exception acts as control of flow and is suppressed. A process to arrive somewhere on this spectrum is summarized by [Joe Armstrong's *let it crash* principal](https://softwareengineering.stackexchange.com/a/421837), which is also covered in Python's [exception documentation](https://docs.python.org/3/tutorial/errors.html#handling-exceptions):

> \[...\] it is good practice to be as specific as possible with the types of exceptions that we intend to handle, and to allow any unexpected exceptions to propagate on.

This experimental library extends Python's exception handling mechanism with two additional functionalities:

 - handling exceptions by module;
 - and exception class scraping from modules.

This library is under active development; it may require additional tuning and there are plans to add additional features.

## Usage notes
The main feature of `exceptlib` is handling exceptions by module with `ExceptionFrom`. For example:

```python
import re

from exceptlib import ExceptionFrom


try:
    re_obj = re.compile(7)
except ExceptionFrom(re) as e:
    print(f"re raised {e[0]}")
```

The malformed call to `re.compile` raises `TypeError`. The interpreter calls `ExceptionFrom` when trying to enter the `except` block. When called, `ExceptionFrom` compares its module arguments to those in the current exception's traceback to determine if any are the direct cause. Since `re` raised, `ExceptionFrom` returns the tuple `(TypeError)` so that `except` block is entered.

Handling exceptions by module enables a wider degree of abstraction for exception handling. Specific advantages include:

 - enable certain retries and fallbacks for exceptions in production with less boilerplate;
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

The `ExceptionFrom.here` class method is useful to scrape exceptions from `raise` statements in the containing module, possibly for use in defining exception groups for example. Calling `ExceptionFrom` when there is no current exception will direct it to scrape distinct exceptions from `raise` statements in the specified modules.

## Install
This library is available through [PyPI](https://pypi.org/project/exceptlib/) and [GitHub](https://github.com/wfatherley/exceptlib).

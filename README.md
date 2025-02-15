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
    print(f"re raised:", e)
```

The malformed call to `re.compile` raises `TypeError`. The interpreter calls `ExceptionFrom` when trying to enter the `except` block. When called, `ExceptionFrom` compares its module arguments to those in the current exception's traceback to determine if any are involved. Since `re` raised, `ExceptionFrom` returns the tuple `(TypeError,)` and causes that `except` block to enter.

Handling exceptions by module enables a wider degree of abstraction for exception handling. Specific advantages include:

 - enable certain retries and fallbacks for exceptions in production with less boilerplate;
 - enhance or simplify RCAs in test;
 - and generally widen the scope of `except` clauses.

In addition to its functionality as the predicate of the `except` statment, `exceptlib.ExceptionFrom` provides introspective functionality:

```python
...

# a tuple of distinct exceptions raised by the input modules
excs_raised_from: tuple = ExceptionFrom(re, urllib)
```

Calling `ExceptionFrom` when there is no current exception will direct it to scrape distinct exceptions from `raise` statements in the specified modules.

## Installation notes
This library is available through [PyPI](https://pypi.org/project/exceptlib/) and [GitHub](https://github.com/wfatherley/exceptlib).

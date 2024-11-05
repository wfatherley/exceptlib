# `exceptlib` - exception handling mechanisms

<hr>

## Summary
Exceptions occur in Python when something goes wrong. For example, `"abcd"[63]` raises `IndexError`. What to do with an exception is context dependent. In any langauge, context informs a spectrum of handling mechanisms. At one end, certain exceptions will or must be fatal, while at the other end a given exception acts as control of flow and is suppressed. A process to arrive somewhere on this spectrum with some codebase is summarized by [Joe Armstrong's *let it crash* principal](https://softwareengineering.stackexchange.com/a/421837), which is also covered in Python's [exception documentation](https://docs.python.org/3/tutorial/errors.html#handling-exceptions):

> \[...\] it is good practice to be as specific as possible with the types of exceptions that we intend to handle, and to allow any unexpected exceptions to propagate on.

This library extends some of Python's exception handling mechanisms. Currently it has three functionalities as its API:

 - handling exceptions by module object;
 - exception class scraping from module objects;
  - robust and extensible profiling of exceptions.

## Usage notes
This library enables the handling exceptions by module, e.g.,

```python
import re
import statistics
import urllib

from exceptlib import exc_from_mod


try:
    a = parse.quote("python.org.:443/not found")  # no raise
    b = statistics.mean([1,2,3])                  # no raise
    c = re.compile(7)                             # raise TypeError
except exc_from_mod(statistics, urllib):
    print("hello from statistics and urllib") # no print
except IndexError:
    print("it was index error")               # no print
except exc_from_mod(re):
    print("hello from re")                    # print
except TypeError:
    print("it was a type error")              # no print

```

While this example is contrived for demonstration, the utility of `exceptlib.exc_from_mod` spans program flexibility and development operations:

 - enable certain retries during exception handling with less boilerplate;
 - enhance regression or performance testing facilities for 3rd party libraries.


```python
with exceptlib.ExceptionProfiler():
    my_program.run()
```


```python
try:
    ...
except SomeException:
    raise swap_traceback(...) from ...

    # ???
```

## change
Instead of `exc_from_mod` and various other names, suppose `ExceptionFrom` as a class with these patterns:

```python
import re, urllib

# a tuple of exceptions raised in this source file
these_exc_tuple = ExceptionFrom.here()

# a tuple of exceptions raised by the input module sources
exc_tuple = ExceptionFrom(re, urllib)

try:
    ...
except ExceptionFrom(re, urllib):
    # enters *iff* the exception root is from re or urllib
    ...
```
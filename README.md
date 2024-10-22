# `exceptlib` -- exception handling mechanisms

<hr>

## Summary
Exceptions occur in Python when something goes wrong. For example, `"abcd"[63]` raises `IndexError`. What to do with an exception is context dependent. In any langauge, context informs a spectrum handling mechanisms. At one end, certain exceptions will or must be fatal, while at the other end a given exception is expected as flow of control and is suppressed. A process to arrive somewhere on this spectrum with some codebase is summarized by [Joe Armstrong's *let it crash* principal](https://softwareengineering.stackexchange.com/a/421837), which is also covered in Python's [exception documentation](https://docs.python.org/3/tutorial/errors.html#handling-exceptions):

> \[...\] it is good practice to be as specific as possible with the types of exceptions that we intend to handle, and to allow any unexpected exceptions to propagate on.

This library extends some of Python's exception handling mechanisms. Currently it has three functionalities as its API:

 - handling exceptions by module;
 - robust and extensible profiling of exceptions;
 - automated exception group creation.

## Usage
Handling exceptions by module, e.g.,

```python
import re, statistics, urllib
from exceptlib import exc_from_mod

try:
    a = parse.quote("python.org.:443/not found")  # no raise
    b = statistics.mean([1,2,3])                  # no raise
    b = re.compile(7)                             # raise
except exc_from_mod(statistics, urllib)
    print("error came from statistics or urllib") # no print
except exc_from_mod(re):
    print("error came from re")                   # print
```

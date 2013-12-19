CobraScript
===========

Simple experiment of translate basic python ast to javascript.

Install
-------

CobraScript itself is written in python and a main installation
source is from PyPI (python package index)::

    pip install cobrascript


Command line
------------

.. code-block:: text

    usage: cobrascript [-h] [-g] [-w] [-o outputfile.js] [-b] [-j]
                       [--indent INDENT] [--auto-camelcase]
                       input.py [input.py ...]

    Python to Javascript translator.

    positional arguments:
      input.py              A list of python files for translate.

    optional arguments:
      -h, --help            show this help message and exit
      -g, --debug           Activate debug mode (only for developers).
      -w, --warnings        Show statick analizer warnings.
      -o outputfile.js, --output outputfile.js
                            Set output file (by default is stdout).
      -b, --bare            Compile without a toplevel closure.
      -j, --join            Join python files before compile.
      --indent INDENT       Set default output indentation level.
      --auto-camelcase      Convert all identifiers to camel case.

Overview
--------

Assignment
~~~~~~~~~~

CobraScript/Python:

.. code-block:: python

    somenumber = 22
    some_string = "Hello"

Javascript:

.. code-block:: js

    var somenumber, some_string;
    somenumber = 22;
    some_string = "Hello";

Functions & Lambdas
~~~~~~~~~~~~~~~~~~~

CobraScript/Python:

.. code-block:: python


    func1 = lambda x: x*2

    def func2():
        return 2

Javascript:

.. code-block:: js

    var func1, func2;

    func1 = function(x) {
        return x*2;
    }
    func2 = function() {
        return 2;
    }


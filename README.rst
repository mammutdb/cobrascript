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


Lists & Dicts
~~~~~~~~~~~~~

CobraScript/Python:

.. code-block:: python

    mylist = [1, 2, 3, 4]

    mydict = {
        "foo": 1,
        "bar": [2,3,4]
    }

Javascript:

.. code-block:: js

    var mylist, mydict;

    mydict = {
        "foo": 1,
        "bar": [1,2,3]
    }


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


If, Elif and Else
~~~~~~~~~~~~~~~~~

CobraScript/Python:

.. code-block:: python

    if x > y:
        return x
    elif x < y:
        return y
    else:
        return 0

Javascript:

.. code-block:: js

    if (x > y) {
        return x;
    } else if (x < y) {
        return y;
    } else {
        return 0;
    }


For loop
~~~~~~~~

CobraScript/Python:

.. code-block:: python

    for item in [1,2,3,4,5]:
        console.log(item)

Javascript:

.. code-block:: js

    var item, ref_0, ref_1;
    for (ref_0 = 0, ref_1 = [1,2,3,4,5]; ref_0 < ref_1.length; ref_0++) {
        item = ref_1[ref_0];
        console.log(item);
    }


Operators
~~~~~~~~~

This is a equivalence table between python operators and translated
javascript operators:

+-------------+------------+
| CobraScript | JavaScript |
+=============+============+
| ``is``      | ``===``    |
+-------------+------------+
| ``==``      | ``===``    |
+-------------+------------+
| ``!=``      | ``!==``    |
+-------------+------------+
| ``and``     | ``&&``     |
+-------------+------------+
| ``or``      | ``||``     |
+-------------+------------+

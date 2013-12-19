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
    mylist = [1,2,3,4];
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

Pending to implement
--------------------

- Assignment destructing
- Classes with hineritance
- Dict comprensions.
- Variable arguments.
- Array slicing.

License
-------

.. code-block:: text

    Copyright (c) 2013 Andrey Antukh <niwi@niwi.be>

    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:
    1. Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.
    3. The name of the author may not be used to endorse or promote products
       derived from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
    IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
    OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
    IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
    NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
    THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

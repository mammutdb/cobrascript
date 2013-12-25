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


While loop
~~~~~~~~~~

CobraScript/Python:

.. code-block:: python

    while 2 > a:
        console.log(1)

Javascript:

.. code-block:: js

    while (2 > a) {
        console.log(1);
    }


Decorators
~~~~~~~~~~

CobraScript/Python:

.. code-block:: python

    def debug(func):
        def _decorator():
            console.log("call....")
            return func.apply(null, arguments)

        return _decorator

    @debug
    def sum(a1, a2, a3):
        return a1 + a2 + a3

    console.log(sum(1,2,3))


Javascript:

.. code-block:: js

    var debug, sum;
    debug = function(func) {
        var _decorator;
        _decorator = function() {
            console.log("call....");
            return func.apply(null, arguments);
        };
        return _decorator;
    };
    sum = function(a1, a2, a3) {
        return (a1 + a2) + a3;
    };
    sum = debug(sum);
    console.log(sum(1, 2, 3));


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


Global object
~~~~~~~~~~~~~

This part is slighty distinct from others, because follows python
philosofy: "explicit better than implicit".

For expose some variables to global scope, you should import ``_global``
module (special form module).

Example:

.. code-block:: python

    # example_file.py

    import _global as g

    # g represents a window object
    g.some_variable = 2

And this is translated to:

.. code-block:: js

    // example_file.js
    (function()
        var g;
        g = this;
        g.some_variable = 2;
    }).call(this);


New operator
~~~~~~~~~~~~

Python as is does not suport new operator. For emulate javascript new operator,
cobrascript exposes other special-form import thar exposes "magic" function
that emulates a new operator.

Example:

.. code-block:: python

    import _new as new_instance
    defer = new_instance(SomeClass, "param1", "param2")

And, this is translated to:

.. code-block:: js

    (function() {
        var defer, new_instance;
        new_instance = function() { //
            // Some special function for call new.
            // (For full function definition, you can see
            //  tests code)
        };

        defer = new_instance(SomeClass, "param1", "param2");
    }).call(this);


Full list of implemented features
---------------------------------

Translation
~~~~~~~~~~~

- Variable assignation.
- Multiple variable assignation.
- Binary and Logical operators.
- Functions, Lambdas and Nested functions.
- Dicts and Lists.
- Function calls.
- Positional arguments.
- For and while loops.
- List comprensions.
- Try/Except/Finally statements.
- Explicit global object.
- Explicit new function for create object.


Static Analisys
~~~~~~~~~~~~~~~

- Lexycal scope handling.
- Protection for overwrite imported special forms.

Command line
~~~~~~~~~~~~

- Bare mode: compile module without wrapped closure
- Join: join multiple files before compile.
- Auto CamelCase: convert identifieres automatically from
  snake case to camel case.

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

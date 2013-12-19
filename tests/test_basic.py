# -*- coding: utf-8 -*-

import pytest

from cobra.base import compile
from .utils import norm


def test_basic_op_add():
    assert compile("2 + 2") == "2 + 2;"


def test_basic_op_mul():
    assert compile("2 * 2") == "2 * 2;"


def test_basic_op_sub():
    assert compile("2 - 2") == "2 - 2;"


def test_basic_op_div():
    assert compile("2 / 2") == "2 / 2;"


def test_basic_op_mod():
    assert compile("2 % 2") == "2 % 2;"


def test_logic_equal():
    assert compile("2 == 2") == "2 === 2;"


def test_logic_not_equal():
    assert compile("2 != 2") == "2 !== 2;"


def test_logic_gt():
    assert compile("2 > 2") == "2 > 2;"


def test_logic_gte():
    assert compile("2 >= 2") == "2 >= 2;"


def test_logic_lt():
    assert compile("2 < 2") == "2 < 2;"


def test_logic_lte():
    assert compile("2 <= 2") == "2 <= 2;"


def test_logic_is():
    assert compile("2 is 2") == "2 === 2;"


def test_logic_expr():
    assert compile("True and False") == "true && false;"


def test_logic_nested_expr():
    assert compile("True and (False or True)") == "true && (false || true);"


def test_simple_assignation():
    input = "x = 2"
    expected = """
    var x;
    x = 2;
    """
    assert compile(input) == norm(expected)


def test_nested_operations():
    input = "x = 2 * ((33 + 2.2) / 2)"
    expected = """
    var x;
    x = 2 * ((33 + 2.2) / 2);
    """
    assert compile(input) == norm(expected)


def test_none_assignation():
    input = "x = None"
    expected = """
    var x;
    x = null;
    """
    assert compile(input) == norm(expected)


def test_boolean_assignation():
    input = """
    x = True
    y = False
    """
    expected = """
    var x, y;
    x = true;
    y = false;
    """
    assert compile(input) == norm(expected)


def test_simple_multiple_assignation():
    input = "x = y = 2"
    expected = """
    var x, y;
    x = y = 2;
    """
    assert compile(input) == norm(expected)


def test_assignation_with_operation():
    input = """
    x = 0
    x += 2
    x -= 2
    x /= 2
    x *= 2
    """
    expected = """
    var x;
    x = 0;
    x += 2;
    x -= 2;
    x /= 2;
    x *= 2;
    """
    assert compile(input) == norm(expected)


def test_simple_function_declaration():
    input = """
    def foo():
        return 2
    """

    expected = """
    var foo;
    foo = function() {
        return 2;
    };
    """

    assert compile(input) == norm(expected)


def test_simple_function_declaration_with_args():
    input = """
    def foo(a, b):
        return a + b
    """

    expected = """
    var foo;
    foo = function(a, b) {
        return a + b;
    };
    """

    assert compile(input) == norm(expected)


def test_nested_function():
    input = """
    def foo(a, b):
        def bar():
            return 2
        return bar
    """

    expected = """
    var foo;
    foo = function(a, b) {
        var bar;
        bar = function() {
            return 2;
        };
        return bar;
    };
    """

    assert compile(input) == norm(expected)


def test_simple_function_call():
    input = """
    x = foo("Hello World")
    """

    expected = """
    var x;
    x = foo("Hello World");
    """

    assert compile(input) == norm(expected)


def test_simple_function_call_with_multiple_args():
    input = """
    x = foo("Hello World", 2, 2.3)
    """

    expected = """
    var x;
    x = foo("Hello World", 2, 2.3);
    """

    assert compile(input) == norm(expected)


def test_function_call_with_lambda_as_parameter():
    input = """
    x = jQuery(".span")
    x.on("click", lambda e: e.preventDefault())
    """

    expected = """
    var x;
    x = jQuery(".span");
    x.on("click", function(e) {
        e.preventDefault();
    });
    """

    assert compile(input) == norm(expected)


def test_assign_dict():
    input = """
    x = {"foo": 2, "bar": {"kk": 3}}
    """

    expected = """
    var x;
    x = {
        "foo": 2,
        "bar": {
            "kk": 3
        }
    };
    """

    assert compile(input) == norm(expected)


def test_assign_dict_with_lists():
    input = """
    x = {"foo": 2, "bar": {"kk": [1, 2, 3]}}
    """

    expected = """
    var x;
    x = {
        "foo": 2,
        "bar": {
            "kk": [1,2,3]
        }
    };
    """

    assert compile(input) == norm(expected)

def test_simple_if_statement():
    input = """
    def foo(a):
        if a is None:
            return None

        return a + 2
    """

    expected = """
    var foo;
    foo = function(a) {
        if (a === null) {
            return null;
        }
        return a + 2;
    };
    """

    assert compile(input) == norm(expected)

def test_simple_if_statement_with_else():
    input = """
    def foo(a):
        if a is None:
            return None
        else:
            return a + 2
    """

    expected = """
    var foo;
    foo = function(a) {
        if (a === null) {
            return null;
        } else {
            return a + 2;
        }
    };
    """

    assert compile(input) == norm(expected)


def test_simple_if_statement_with_elif():
    input = """
    def foo(a):
        if a is None:
            return None
        elif a == 0:
            return a + 2
    """

    expected = """
    var foo;
    foo = function(a) {
        if (a === null) {
            return null;
        } else if (a === 0) {
            return a + 2;
        }
    };
    """

    assert compile(input) == norm(expected)


def test_basic_for():
    input = """
    for item in [1,2,3,4,5]:
        console.log(item)
    """

    expected = """
    var item, ref_0, ref_1;
    for (ref_0 = 0, ref_1 = [1,2,3,4,5]; ref_0 < ref_1.length; ref_0++) {
        item = ref_1[ref_0];
        console.log(item);
    }
    """
    assert compile(input) == norm(expected)


def test_nested_for():
    input = """
    for item1 in [1,2,3,4,5]:
        for item2 in [10, 20, 34]:
            console.log(item1, item2)
    """

    expected = """
    var item1, item2, ref_0, ref_1, ref_2, ref_3;
    for (ref_2 = 0, ref_3 = [1,2,3,4,5]; ref_2 < ref_3.length; ref_2++) {
        item1 = ref_3[ref_2];
        for (ref_0 = 0, ref_1 = [10,20,34]; ref_0 < ref_1.length; ref_0++) {
            item2 = ref_1[ref_0];
            console.log(item1, item2);
        }
    }
    """
    compiled = compile(input)
    assert compiled == norm(expected)

def test_basic_while():
    input = """
    while True:
        console.log("test")
    """

    expected = """
    while (true) {
        console.log("test");
    }
    """
    assert compile(input) == norm(expected)


def test_nested_while():
    input = """
    while True:
        while True:
            console.log("test")
    """

    expected = """
    while (true) {
        while (true) {
            console.log("test");
        }
    }
    """
    compiled = compile(input)
    assert compiled == norm(expected)

def test_while_else():
    input = """
    while my_var:
        console.log("test")
    else:
        console.log("test else")
    """

    expected = """
    var ref_0;
    ref_0 = true;
    while (my_var) {
        ref_0 = false;
        console.log("test");
    }
    if (ref_0) {
        console.log("test else");
    }
    """
    compiled = compile(input)
    print(compiled)
    assert compiled == norm(expected)

def test_basic_list_comprehensions():
    input = """
    count = [num for num in [1, 2, 3, 4]]
    """

    expected = """
    var count;
    count = (function() {
        var _i, _len, _values, _results;
        _values = [1,2,3,4];
        _results = [];
        for (_i = 0, _len = _values.length; _i < _len; _i++) {
            _results.push(_values[_i])
        }
        return _results;
    })();
    """
    compiled = compile(input)
    assert compiled == norm(expected)

def test_exceptions_raise():
    input = """
    raise "sample exception"
    """

    expected = """
    throw "sample exception";
    """
    compiled = compile(input)
    print(compiled)
    assert compiled == norm(expected)


def test_conditional_list_comprehensions():
    input = """
    count = [num for num in [1, 2, 3, 4] if num != 4]
    """

    expected = """
    var count;
    count = (function() {
        var _i, _len, _values, _results;
        _values = [1,2,3,4];
        _results = [];
        for (_i = 0, _len = _values.length; _i < _len; _i++) {
            if (num !== 4) {
                _results.push(_values[_i])
            }
        }
        return _results;
    })();
    """
    compiled = compile(input)
    print(compiled)
    assert compiled == norm(expected)


def test_multiple_conditional_list_comprehensions():
    input = """
    count = [num for num in [1, 2, 3, 4] if num != 4 if num != 3]
    """

    expected = """
    var count;
    count = (function() {
        var _i, _len, _values, _results;
        _values = [1,2,3,4];
        _results = [];
        for (_i = 0, _len = _values.length; _i < _len; _i++) {
            if (num !== 4 && num !== 3) {
                _results.push(_values[_i])
            }
        }
        return _results;
    })();
    """
    compiled = compile(input)
    assert compiled == norm(expected)


def test_exceptions_try_except():
    input = """
    try:
        do_some_thing()
    except Error as e:
        do_some_thing_other()
    """

    expected = """
    try {
        do_some_thing();
    } catch (e) {
        do_some_thing_other();
    }
    """
    compiled = compile(input)
    assert compiled == norm(expected)


def test_exceptions_try_finally():
    input = """
    try:
        do_some_thing()
    finally:
        do_some_thing_other()
    """

    expected = """
    try {
        do_some_thing();
    } finally {
        do_some_thing_other();
    }
    """
    compiled = compile(input)
    assert compiled == norm(expected)

def test_global_import():
    input = """
    import _global as g
    """

    expected = """
    var g;
    g = this;
    """
    compiled = compile(input)
    print(compiled)
    assert compiled == norm(expected)


def test_global_import_and_try_overwrite():
    input = """
    import _global as g
    g = 2
    """

    with pytest.raises(RuntimeError):
        compiled = compile(input)

def test_new_import():
    input = """
    import _new as new
    """

    expected = """
    var new;
    new = function(_class) { var ___args_array = Array.apply(null, arguments); var ___clazz = ___args_array.slice(0, 1)[0]; var ___args = ___args_array.slice(1); var ___constructor = ___clazz; function Fake() { ___constructor.apply(this, ___args); } Fake.prototype = ___constructor.prototype; return new Fake();};
    """

    compiled = compile(input)
    assert compiled == norm(expected)


def test_new_import_and_try_overwrite():
    input = """
    import _new as new
    new = 2
    """

    with pytest.raises(RuntimeError):
        compiled = compile(input)

def test_auto_camel_case():
    input = """
    xx = foo_bar()
    """

    expected = """
    var xx;
    xx = fooBar();
    """
    compiled = compile(input, translate_options={"auto_camelcase": True})
    assert compiled == norm(expected)


def test_module_as_closure():
    input = """
    xx = foo_bar()
    """

    expected = """
    (function() {
        var xx;
        xx = foo_bar();
    }).call(this);
    """
    compiled = compile(input, translate_options={"module_as_closure": True})
    assert compiled == norm(expected)
# def test_basic_class():
#     input = """
#     class MyClass:
#         def foo(self):
#             return 2
#     """
#
#     expected = ""
#     compiled = compile(input)
#     print(compiled)
#
#     assert compiled == norm(expected)

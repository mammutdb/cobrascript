# -*- coding: utf-8 -*-

# import sys
# sys.path.insert(0, "..")
# print(sys.path)

import unittest

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


def test_simple_assignation():
    input = "x = 2"
    expected = """
    var x;
    x = 2;
    """
    assert compile(input) == norm(expected)


def test_none_assignation():
    input = "x = None"
    expected = """
    var x;
    x = null;
    """
    assert compile(input) == norm(expected)


def test_simple_multiple_assignation():
    input = "x = y = 2"
    expected = """
    var x, y;
    x = y = 2;
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

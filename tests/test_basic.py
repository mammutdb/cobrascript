# -*- coding: utf-8 -*-

# import sys
# sys.path.insert(0, "..")
# print(sys.path)

import unittest

import cobra.base as cobra
from .utils import norm

def test_simple_assignation():
    input = "x = 2"
    expected = """
    var x;
    x = 2;
    """
    assert cobra.compile(input) == norm(expected)

def test_simple_multiple_assignation():
    input = "x = y = 2"
    expected = """
    var x, y;
    x = y = 2;
    """
    assert cobra.compile(input) == norm(expected)

# -*- coding: utf-8 -*-

import ast

from . import ast as ecma_ast
from . import compiler
from . import translator
from . import utils


def parse(data:str) -> object:
    """
    Given a string with python source code,
    returns a python ast tree.
    """

    return ast.parse(data)


def translate(data:object) -> object:
    """
    Given a python ast tree, translate it to
    ecma ast.
    """

    return translator.TranslateVisitor().translate(data)


def compile(data:str) -> str:
    python_tree = parse(data)
    ecma_tree = translate(python_tree)
    return compiler.ECMAVisitor().visit(ecma_tree)

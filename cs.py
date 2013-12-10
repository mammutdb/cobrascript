#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import abc
import ast
import io
import sys
import pprint

from collections import defaultdict

import slimit.ast as slim_ast


class Stack(object):
    def __init__(self):
        self._data = []

    def get_last(self):
        if len(self._data) == 0:
            raise ValueError("Stack is empty")
        return self._data[-1]

    def push(self, item):
        self._data.append(item)

    def drop_last(self):
        if len(self._data) == 0:
            raise ValueError("Stack is empty")

        try:
            return self._data[-1]
        finally:
            self._data = self._data[:-1]

class CobraNode(object):
    def __init__(self):
        self.node = None

    def __repr__(self):
        return "<wrapper {}>".format(repr(self.node))


class CompilerVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()

        self.parent_stack = Stack()

        self._scoped_parents = []
        self._scoped_childs = defaultdict(lambda: [])
        self._scoped_level = 0

    def compile_ast(self, ast_tree):
        self.visit(ast_tree, root=True)
        return self.result.node.to_ecma()

    @property
    def scoped_childs(self):
        return self._scoped_childs[self._scoped_level]

    @property
    def scoped_last_parent(self):
        if len(self._scoped_parents) == 0:
            return None
        return self._scoped_parents[-1]

    @scoped_last_parent.setter
    def scoped_last_parent(self, value):
        self._scoped_parents.append(value)

    @scoped_last_parent.deleter
    def scoped_last_parent(self):
        self._scoped_parents = self._scoped_parents[:-1]

    def increment_scope_level(self):
        self._scoped_level += 1

    def decrement_scope_level(self):
        self._scoped_level -= 1

        if self._scoped_level < 0:
            raise RuntimeError("invalid scope level")

    def visit(self, node, root=False):
        # print("enter:", node)

        jsnode = CobraNode()

        self.scoped_last_parent = jsnode
        self.scoped_childs.append(jsnode)
        self.increment_scope_level()

        super().visit(node)

        name = node.__class__.__name__
        current = self.scoped_last_parent
        current.node = self._compile_node(node, self.scoped_childs)

        # print("exit:", node, current)
        # print("childs:", self.scoped_childs)
        # print()

        del self.scoped_last_parent

        if self.scoped_last_parent is None:
            self.result = current

        self.decrement_scope_level()

    def _compile_node(self, node, childs):
        name = node.__class__.__name__
        fn = getattr(self, "_compile_{}".format(name), None)
        if fn:
            return fn(node, childs)

    def _compile_BinOp(self, node, childs):

        n = slim_ast.BinOp(childs[1].node,
                           childs[0].node,
                           childs[2].node)

        # Ugly hack
        if "BinOp" not in [x.node.__class__.__name__ for x in childs]:
            n._parens = True

        return n

    def _compile_Num(self, node, childs):
        return slim_ast.Number(node.n)

    def _compile_Add(self, node, childs):
        return "+"

    def _compile_Return(self, node, childs):
        return slim_ast.Return(childs[0].node)

    def _compile_FunctionDef(self, node, childs):
        return slim_ast.FuncDecl(slim_ast.Identifier(node.name),
                                 None,
                                 [x.node for x in childs[1:]])

    def _compile_Module(self, node, childs):
        return slim_ast.Program([x.node for x in childs])

def compile(string):
    tree = ast.parse(string)

    compiler = CompilerVisitor()
    return compiler.compile_ast(tree)


def main(filename):
    with io.open(filename, "rt") as f:
        text = f.read()
    r = compile(text)
    print(r)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise RuntimeError("Invalid parameters")

    sys.exit(main(sys.argv[1]))

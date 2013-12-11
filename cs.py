#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import abc
import ast
import io
import sys
import pprint

from collections import defaultdict
from collections import ChainMap

import slimit.ast as slim_ast


class GenericStack(object):
    def __init__(self):
        self._data = []

    def get_last(self):
        if self.is_empty():
            return None
        return self._data[-1]

    def push(self, item):
        self._data.append(item)

    def pop(self):
        if len(self._data) == 0:
            raise ValueError("Stack is empty")

        try:
            return self._data[-1]
        finally:
            self._data = self._data[:-1]

    def is_empty(self):
        return len(self._data) == 0


class LeveledStack(object):
    def __init__(self):
        self.data = defaultdict(lambda: [])
        self.level = 0

    def inc_level(self):
        self.level += 1

    def dec_level(self):
        del self.data[self.level]
        self.level -= 1

        if self.level < 0:
            raise RuntimeError("invalid stack level")

    def append(self, value):
        self.data[self.level].append(value)

    def get_value(self):
        return self.data[self.level]


class ScopeStack(object):
    def __init__(self):
        self.data = ChainMap({})

    def __contains__(self, key):
        return key in self.data

    def set(self, key, value):
        self.data[key] = value

    def is_empty(self):
        return len(self.data) == 0

    def new_scope(self):
        self.data = self.data.new_child()

    def drop_scope(self):
        self.data = self.data.parents

    def first(self):
        if len(self.data.maps) == 0:
            return {}
        return self.data.maps[0]


class NodeWrapper(object):
    def __init__(self):
        self.node = None

    def __repr__(self):
        return "<wrapper {}>".format(repr(self.node))


class CompilerVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()

        self.level_stack = LeveledStack()
        self.bin_op_stack = GenericStack()
        self.scope = ScopeStack()

        self.indentation = 0
        self.debug = True

    def print(self, *args, **kwargs):
        if self.debug:
            prefix = "    " * self.indentation
            print(prefix, *args, **kwargs)

    def compile_ast(self, ast_tree):
        self.visit(ast_tree, root=True)
        return self.result.node.to_ecma()

    def visit(self, node, root=False):
        node_wrapper = NodeWrapper()

        self.level_stack.append(node_wrapper)
        self.level_stack.inc_level()

        self.print("enter:", node)
        self._pre_visit_node(node, node_wrapper)

        self.indentation += 1
        super().visit(node)
        self.indentation -= 1

        # import pdb; pdb.set_trace()
        self._post_visit_node(node, node_wrapper)
        node_wrapper.node = self._compile_node(node, self.level_stack.get_value())

        self.print("childs:", self.level_stack.get_value())
        self.print("exit:", node)

        self.level_stack.dec_level()

        if self.indentation == 0:
            self.result = node_wrapper

    # Special visit fields

    def visit_BinOp(self, node):
        self.bin_op_stack.push(node)
        self.generic_visit(node)
        self.bin_op_stack.pop()

    # Compile methods

    def _pre_visit_node(self, node, wrapper):
        name = node.__class__.__name__
        fn = getattr(self, "_pre_visit_{}".format(name), None)
        if fn:
            return fn(node, wrapper)

    def _post_visit_node(self, node, wrapper):
        name = node.__class__.__name__
        fn = getattr(self, "_post_visit_{}".format(name), None)
        if fn:
            return fn(node, wrapper)

    def _compile_node(self, node, childs):
        name = node.__class__.__name__
        fn = getattr(self, "_compile_{}".format(name), None)
        if fn:
            return fn(node, childs)

    # Pre/Post Compile specific methods

    def _pre_visit_Module(self, node, wrapper):
        self.scope.new_scope()

    def _pre_visit_FunctionDef(self, node, wrapper):
        self.scope.new_scope()

    # Specific compile methods

    def _compile_BinOp(self, node, childs):
        n = slim_ast.BinOp(childs[1].node,
                           childs[0].node,
                           childs[2].node)

        if not self.bin_op_stack.is_empty():
            n._parens = True

        return n

    def _compile_Num(self, node, childs):
        return slim_ast.Number(node.n)

    def _compile_Add(self, node, childs):
        return "+"

    def _compile_Mult(self, node, childs):
        return "*"

    def _compile_Return(self, node, childs):
        return slim_ast.Return(childs[0].node)

    def _compile_FunctionDef(self, node, childs):
        identifier = slim_ast.Identifier(node.name)
        func_expr = slim_ast.FuncExpr(None, childs[0].node, [x.node for x in childs[1:]])
        var_decl = slim_ast.VarDecl(identifier, func_expr)

        # Drop inner scope (temporary is unused)
        self.scope.drop_scope()

        if node.name not in self.scope:
            self.scope.set(node.name, identifier)

        return var_decl

    def _compile_Module(self, node, childs):
        childs = [x.node for x in childs]
        identifiers = list(self.scope.first().values())
        var_decls = list(map(lambda x: slim_ast.VarDecl(x), identifiers))

        self.scope.drop_scope()
        return slim_ast.Program([slim_ast.VarStatement(var_decls)] + childs)

    def _compile_arguments(self, node, childs):
        return [x.node for x in childs]

    def _compile_Name(self, node, childs):
        return slim_ast.Identifier(node.id)

    def _compile_arg(self, node, childs):
        return slim_ast.Identifier(node.arg)

    def _compile_Str(self, node, childs):
        return node.s

    def _compile_Dict(self, node, childs):
        properties = []

        msize = int(len(childs)/2)

        keys = [x.node for x in childs[:msize]]
        values = [x.node for x in childs[msize:]]

        for key, value in zip(keys, values):
            identifier = slim_ast.Identifier(key)
            assign_instance = slim_ast.Assign(":", identifier, value)
            properties.append(assign_instance)

        return slim_ast.Object(properties)


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

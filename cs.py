#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import abc
import ast
import io
import sys
import pprint

# TODO: introduce argparse for commandline

# Global class registry

nodes = {}

def _resolve_node_instance(node, indent=0):
    cls = nodes[node.__class__.__name__]
    return cls(node, indent=indent)

class NodeMeta(type):
    def __init__(cls, name, bases, attrs):
        nodes[name] = cls
        super().__init__(name, bases, attrs)


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


class CompilerVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()

        self.scope_stack = Stack()
        self.parent_stack = Stack()
        self.indent_level = 0
        self.indent_chars = 2

    def indent_str_expr(self, data, modifier=0):
        ic = " " * self.indent_chars
        return (ic * (self.indent_level+modifier)) + data

    def get_cs_node(self, node):
        cls = nodes[node.__class__.__name__]
        return cls(node)

    def compile_ast(self, ast_tree):
        self.visit(ast_tree, root=True)
        return self.compiled_data

    def visit(self, node, root=False):
        # Get cs Node instance for abs node.
        nd = self.get_cs_node(node)
        print("enter:", node, nd)

        # If node implements a new scope, set it
        if nd.new_scope:
            self.indent_level += 1
            self.scope_stack.push(nd)

        # Set parent scope before proces childs
        self.parent_stack.push(nd)

        super().visit(node)

        self.parent_stack.drop_last()

        if not root:
            print(nd.compile(self))
            lp = self.parent_stack.get_last()
            lp.data.append("".join(nd.compile(self)))

        if root:
            self.compiled_data = "\n".join([x.rstrip() for x in nd.compile(self)])

        if nd.new_scope:
            self.indent_level -= 1

        print("exit:", node, nd.data)


# Nodes definition

class Node(metaclass=NodeMeta):
    new_scope = False
    is_root = False

    def __init__(self, node):
        self.node = node
        self.data = []

    def get_code(self):
        raise NotImplementedError()


class Module(Node):
    new_scope = True
    is_root = True

    def compile(self, compiler):
        module_code = [
            ";(function(this) {",
            "\n".join(self.data),
            "}).call(this);",
        ]

        return module_code


class Expr(Node):
    def compile(self, compiler):
        return [compiler.indent_str_expr(" ".join(self.data)), ";"]


class BinOp(Node):
    def compile(self, compiler):
        return [" ".join(self.data)]


class Num(Node):
    def compile(self, compiler):
        return [str(self.node.n)]


class Add(Node):
    def compile(self, compiler):
        return ["+"]


class Sub(Node):
    def get_code(self, indent=0):
        return "-"


class Mult(Node):
    def get_code(self, indent=0):
        return "*"


class Div(Node):
    def get_code(self, indent=0):
        return "/"


class arguments(Expr):
    pass


class Return(Expr):
    def compile(self, compiler):
        return [" ".join(self.data), ";"]

class FunctionDef(Node):
    new_scope = True

    def compile(self, compiler):
        code = []

        main = "var {0} = function ()".format(self.node.name)
        code.append(compiler.indent_str_expr(main, modifier=-1))
        code.append("{")

        for code_expr in self.data:
            code.append(compiler.indent_str_expr(code_expr))
            code.append("\n")

        code.append(compiler.indent_str_expr("};\n", modifier=-1))
        return code


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

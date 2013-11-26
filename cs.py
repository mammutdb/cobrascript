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


# Nodes definition

class Node(metaclass=NodeMeta):
    """
    Base class for all compiller Nodes
    """
    def __init__(self, ast_node, indent=0, child=None):
        self.ast_node = ast_node
        self.indent = indent

    def iter_nodes(self):
        for node in ast.iter_child_nodes(self.ast_node):
            yield _resolve_node_instance(node, self.indent)

    def get_code(self):
        raise NotImplementedError()


class Module(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indent += 4

    def get_code(self):
        code = "\n\n".join(n.get_code() for n in self.iter_nodes())
        return "".join([";(function(this) {\n", code, "}).call(this);"])


class Expr(Node):
    def get_code(self):
        code = " ".join(x.get_code() for x in self.iter_nodes())
        return "{indent}{code};\n".format(indent=" "*self.indent,
                                          code=code)

class Num(Node):
    def get_code(self):
        return str(self.ast_node.n)


class Add(Node):
    def get_code(self):
        return "+"


class Sub(Node):
    def get_code(self, indent=0):
        return "-"


class Mult(Node):
    def get_code(self, indent=0):
        return "*"


class Div(Node):
    def get_code(self, indent=0):
        return "/"


class BinOp(Node):
    def get_code(self):
        left = _resolve_node_instance(self.ast_node.left)
        op = _resolve_node_instance(self.ast_node.op)
        right = _resolve_node_instance(self.ast_node.right)

        return "{left} {op} {right}".format(left=left.get_code(),
                                            right=right.get_code(),
                                            op=op.get_code())

class Return(Node):
    def get_code(self):
        code = " ".join(x.get_code() for x in self.iter_nodes())
        return "{indent}return {code};\n".format(indent=" " * self.indent,
                                                 code=code)

class FunctionDef(Node):
    def iter_nodes(self):
        for node in self.ast_node.body:
            yield _resolve_node_instance(node, self.indent+4)

    def get_code(self):
        code = ["{0}var {1} = function ()".format(" "*self.indent, self.ast_node.name)]
        code.append(" {\n")

        for node in self.iter_nodes():
            code.append(node.get_code())
            code.append("\n")

        code.append(" "*self.indent)
        code.append("};\n")
        return "".join(code)

def compile_node(node):
    return _resolve_node_instance(node).get_code()

def compile(string):
    tree = ast.parse(string)
    return compile_node(tree)

def main(filename):
    with io.open(filename, "rt") as f:
        text = f.read()
    r = compile(text)
    print(r)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise RuntimeError("Invalid parameters")

    sys.exit(main(sys.argv[1]))

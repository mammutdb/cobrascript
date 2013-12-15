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
        return self.result.to_ecma()

    def visit(self, node, root=False):
        self.level_stack.inc_level()

        self.print("enter:", node)

        if isinstance(node, (ast.Module, ast.FunctionDef)):
            self.scope.new_scope()

        self.indentation += 1

        super().visit(node)
        self.indentation -= 1

        js_node = self._compile_node(node, self.level_stack.get_value())

        self.print("childs:", self.level_stack.get_value())
        self.print("exit:", node)

        self.level_stack.dec_level()

        if js_node is not None:
            self.level_stack.append(js_node)

        if self.indentation == 0:
            self.result = js_node

    # Special visit fields

    def visit_BinOp(self, node):
        self.bin_op_stack.push(node)
        self.generic_visit(node)
        self.bin_op_stack.pop()

    # Compile methods

    def _compile_node(self, node, childs):
        name = node.__class__.__name__
        fn = getattr(self, "_compile_{}".format(name), None)
        if fn:
            return fn(node, childs)

    # Specific compile methods

    def _compile_BinOp(self, node, childs):
        n = slim_ast.BinOp(childs[1], childs[0], childs[2])
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
        return slim_ast.Return(childs[0])

    def _compile_FunctionDef(self, node, childs):
        # Scope var declaration
        scope_identifiers = list(self.scope.first().values())
        scope_var_decls = list(map(lambda x: slim_ast.VarDecl(x), scope_identifiers))
        scope_var_statement = slim_ast.VarStatement(scope_var_decls)

        arguments = childs[1:]

        # Add scope var statement only if any var is defined
        if len(scope_var_decls) > 0:
            arguments = [scope_var_statement] + arguments

        identifier = slim_ast.Identifier(node.name)
        func_expr = slim_ast.FuncExpr(None, childs[0], arguments)
        var_decl = slim_ast.VarDecl(identifier, func_expr)

        # Drop inner scope (temporary is unused)
        self.scope.drop_scope()

        if node.name not in self.scope:
            self.scope.set(node.name, identifier)

        return slim_ast.ExprStatement(var_decl)

    def _compile_Lambda(self, node, childs):
        exprs = map(slim_ast.ExprStatement, childs[1:])
        func_expr = slim_ast.FuncExpr(None, childs[0], list(exprs))
        return func_expr

    def _compile_Module(self, node, childs):
        identifiers = list(self.scope.first().values())
        var_decls = list(map(lambda x: slim_ast.VarDecl(x), identifiers))
        var_statement = slim_ast.VarStatement(var_decls)
        self.scope.drop_scope()

        return slim_ast.Program([var_statement] + childs)

    def _compile_Expr(self, node, childs):
        return slim_ast.ExprStatement(childs[0])

    def _compile_arguments(self, node, childs):
        return childs

    def _compile_Name(self, node, childs):
        return slim_ast.Identifier(node.id)

    def _compile_arg(self, node, childs):
        return slim_ast.Identifier(node.arg)

    def _compile_Str(self, node, childs):
        return slim_ast.String('"{}"'.format(node.s))

    def _compile_Call(self, node, childs):
        if isinstance(node.func, ast.Name):
            fcall = slim_ast.FunctionCall(childs[0], childs[1:])
            return fcall

        elif isinstance(node.func, ast.Attribute):
            dotaccessor = childs[0]
            arguments = list(filter(bool, childs[1:]))

            function_call = slim_ast.FunctionCall(dotaccessor, arguments)
            return function_call

        raise NotImplementedError(":D")

    def _compile_Attribute(self, node, childs):
        variable_identifier = childs[0]
        attribute_access_identifier = slim_ast.Identifier(node.attr)
        dotaccessor = slim_ast.DotAccessor(variable_identifier, attribute_access_identifier)
        return dotaccessor

    def _compile_Assign(self, node, childs):
        identifiers = childs[:-1]
        value = childs[-1]

        assign_decl = None

        for target in reversed(identifiers):
            if isinstance(target, slim_ast.Identifier):
                if target.value not in self.scope:
                    self.scope.set(target.value, target)

            if assign_decl is None:
                assign_decl = slim_ast.Assign("=", target, value)
            else:
                assign_decl = slim_ast.Assign("=", target, assign_decl)

        return slim_ast.ExprStatement(assign_decl)

    def _compile_Index(self, node, childs):
        # FIXME: seems to be incomplete
        return childs[0]

    def _compile_Subscript(self, node, childs):
        node_identifier = childs[0]
        expr_identifier = childs[1]

        if node_identifier.value not in self.scope:
            raise RuntimeError("undefined variable {} at line {}".format(node_identifier.value,
                                                                         node.lineno))
        return slim_ast.BracketAccessor(node_identifier, expr_identifier)

    def _compile_List(self, node, childs):
        return slim_ast.Array(childs)

    def _compile_Dict(self, node, childs):
        properties = []

        msize = int(len(childs)/2)
        keys = childs[:msize]
        values = childs[msize:]

        for key, value in zip(keys, values):
            identifier = slim_ast.Identifier(key.value)
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

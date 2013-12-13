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

        self.level_stack.inc_level()

        self.print("enter:", node)
        self._pre_visit_node(node, node_wrapper)

        self.indentation += 1
        super().visit(node)
        self.indentation -= 1

        self._post_visit_node(node, node_wrapper)
        node_wrapper.node = self._compile_node(node, self.level_stack.get_value())

        self.print("childs:", self.level_stack.get_value())
        self.print("exit:", node)

        self.level_stack.dec_level()

        if node_wrapper.node is not None:
            self.level_stack.append(node_wrapper)

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
        # Scope var declaration
        scope_identifiers = list(self.scope.first().values())
        scope_var_decls = list(map(lambda x: slim_ast.VarDecl(x), scope_identifiers))
        scope_var_statement = slim_ast.VarStatement(scope_var_decls)

        arguments = [x.node for x in childs[1:]]

        # Add scope var statement only if any var is defined
        if len(scope_var_decls) > 0:
            arguments = [scope_var_statement] + arguments

        identifier = slim_ast.Identifier(node.name)
        func_expr = slim_ast.FuncExpr(None, childs[0].node, arguments)
        var_decl = slim_ast.VarDecl(identifier, func_expr)

        # Drop inner scope (temporary is unused)
        self.scope.drop_scope()

        if node.name not in self.scope:
            self.scope.set(node.name, identifier)

        return slim_ast.ExprStatement(var_decl)

    def _compile_Lambda(self, node, childs):
        exprs = map(slim_ast.ExprStatement, [x.node for x in childs[1:]])
        func_expr = slim_ast.FuncExpr(None, childs[0].node, list(exprs))
        return func_expr

    def _compile_Module(self, node, childs):
        identifiers = list(self.scope.first().values())
        var_decls = list(map(lambda x: slim_ast.VarDecl(x), identifiers))
        var_statement = slim_ast.VarStatement(var_decls)
        self.scope.drop_scope()

        childs = [x.node for x in childs]
        return slim_ast.Program([var_statement] + childs)

    def _compile_Expr(self, node, childs):
        return slim_ast.ExprStatement(childs[0].node)

    def _compile_arguments(self, node, childs):
        return [x.node for x in childs]

    def _compile_Name(self, node, childs):
        return slim_ast.Identifier(node.id)

    def _compile_arg(self, node, childs):
        return slim_ast.Identifier(node.arg)

    def _compile_Str(self, node, childs):
        return slim_ast.String('"{}"'.format(node.s))

    def _compile_Call(self, node, childs):
        if isinstance(node.func, ast.Name):
            fcall = slim_ast.FunctionCall(childs[0].node, [x.node for x in childs[1:]])
            return fcall

        elif isinstance(node.func, ast.Attribute):
            arguments = list(filter(bool, [x.node for x in childs]))

            node_attribute_identifier = slim_ast.Identifier(node.func.value.id)
            node_attribute_call_identifier = slim_ast.Identifier(node.func.attr)

            dotaccessor = slim_ast.DotAccessor(node_attribute_identifier,
                                               node_attribute_call_identifier)
            function_call = slim_ast.FunctionCall(dotaccessor, arguments)
            return function_call

        raise NotImplementedError(":D")

    def _compile_Assign(self, node, childs):
        if isinstance(node.value, (ast.Name, ast.List)):
            # FIXME: multiple targets
            target = node.targets[0]

            variable_identifier = slim_ast.Identifier(target.value.id)
            attribute_access_identifier = slim_ast.Identifier(target.attr)
            dotaccessor = slim_ast.DotAccessor(variable_identifier, attribute_access_identifier)

            var_decl = slim_ast.VarDecl(dotaccessor, childs[0].node)
            return slim_ast.ExprStatement(var_decl)

        elif isinstance(node.value, ast.Call):
            # TODO: review node.value for possible use.
            identifier = childs[0].node
            right_part = childs[1].node

            var_decl = slim_ast.VarDecl(identifier, right_part)

            if identifier.value not in self.scope:
                self.scope.set(identifier.value, identifier)

            return slim_ast.ExprStatement(var_decl)

        raise NotImplementedError(":D")

    def _compile_List(self, node, childs):
        return slim_ast.Array([x.node for x in childs])

    def _compile_Dict(self, node, childs):
        properties = []

        msize = int(len(childs)/2)
        keys = [x.node for x in childs[:msize]]
        values = [x.node for x in childs[msize:]]

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

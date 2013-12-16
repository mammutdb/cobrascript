# -*- coding: utf-8 -*-

import ast

from .utils import GenericStack
from .utils import LeveledStack
from .utils import ScopeStack

from . import ast as ecma_ast


class TranslateVisitor(ast.NodeVisitor):
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

    def translate(self, tree):
        self.visit(tree, root=True)
        return self.result

    def visit(self, node, root=False):
        self.level_stack.inc_level()

        self.print("enter:", node)

        if isinstance(node, (ast.Module, ast.FunctionDef)):
            self.scope.new_scope()

        self.indentation += 1

        super().visit(node)
        self.indentation -= 1

        js_node = self._translate_node(node, self.level_stack.get_value())

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

    def _translate_node(self, node, childs):
        name = node.__class__.__name__
        fn = getattr(self, "_translate_{}".format(name), None)
        if fn:
            return fn(node, childs)

    # Specific compile methods

    def _translate_BinOp(self, node, childs):
        n = ecma_ast.BinOp(childs[1], childs[0], childs[2])
        if not self.bin_op_stack.is_empty():
            n._parens = True
        return n

    def _translate_Num(self, node, childs):
        return ecma_ast.Number(str(node.n))

    def _translate_Add(self, node, childs):
        return "+"

    def _translate_Mult(self, node, childs):
        return "*"

    def _translate_Sub(self, node, childs):
        return "-"

    def _translate_Div(self, node, childs):
        return "/"

    def _translate_Mod(self, node, childs):
        return "%"

    def _translate_Return(self, node, childs):
        return ecma_ast.Return(childs[0])

    def _create_scope_var_statement(self):
        scope_identifiers = list(self.scope.first().values())
        if len(scope_identifiers) == 0:
            return None

        scope_identifiers = sorted(scope_identifiers, key=lambda x: x.value)
        scope_var_decls = list(map(lambda x: ecma_ast.VarDecl(x), scope_identifiers))
        return ecma_ast.VarStatement(scope_var_decls)

    def _translate_FunctionDef(self, node, childs):
        scope_var_statement = self._create_scope_var_statement()
        arguments = childs[1:]

        # Add scope var statement only if any var is defined
        if scope_var_statement:
            arguments = [scope_var_statement] + arguments

        identifier = ecma_ast.Identifier(node.name)
        func_expr = ecma_ast.FuncExpr(None, childs[0], arguments)
        var_decl = ecma_ast.VarDecl(identifier, func_expr)

        # Drop inner scope (temporary is unused)
        self.scope.drop_scope()

        if node.name not in self.scope:
            self.scope.set(node.name, identifier)

        return ecma_ast.ExprStatement(var_decl)

    def _translate_Lambda(self, node, childs):
        exprs = map(ecma_ast.ExprStatement, childs[1:])
        func_expr = ecma_ast.FuncExpr(None, childs[0], list(exprs))
        return func_expr

    def _translate_Module(self, node, childs):
        scope_var_statement = self._create_scope_var_statement()
        self.scope.drop_scope()

        if scope_var_statement:
            return ecma_ast.Program([scope_var_statement] + childs)
        return ecma_ast.Program(childs)

    def _translate_Expr(self, node, childs):
        return ecma_ast.ExprStatement(childs[0])

    def _translate_arguments(self, node, childs):
        return childs

    def _translate_Name(self, node, childs):
        return ecma_ast.Identifier(node.id)

    def _translate_arg(self, node, childs):
        return ecma_ast.Identifier(node.arg)

    def _translate_Str(self, node, childs):
        return ecma_ast.String('"{}"'.format(node.s))

    def _translate_Call(self, node, childs):
        if isinstance(node.func, ast.Name):
            fcall = ecma_ast.FunctionCall(childs[0], childs[1:])
            return fcall

        elif isinstance(node.func, ast.Attribute):
            dotaccessor = childs[0]
            arguments = list(filter(bool, childs[1:]))

            function_call = ecma_ast.FunctionCall(dotaccessor, arguments)
            return function_call

        raise NotImplementedError(":D")

    def _translate_Attribute(self, node, childs):
        variable_identifier = childs[0]
        attribute_access_identifier = ecma_ast.Identifier(node.attr)
        dotaccessor = ecma_ast.DotAccessor(variable_identifier, attribute_access_identifier)
        return dotaccessor

    def _translate_Assign(self, node, childs):
        identifiers = childs[:-1]
        value = childs[-1]

        assign_decl = None

        for target in reversed(identifiers):
            if isinstance(target, ecma_ast.Identifier):
                if target.value not in self.scope:
                    self.scope.set(target.value, target)

            if assign_decl is None:
                assign_decl = ecma_ast.Assign("=", target, value)
            else:
                assign_decl = ecma_ast.Assign("=", target, assign_decl)

        return ecma_ast.ExprStatement(assign_decl)

    def _translate_Index(self, node, childs):
        # FIXME: seems to be incomplete
        return childs[0]

    def _translate_Subscript(self, node, childs):
        node_identifier = childs[0]
        expr_identifier = childs[1]

        if node_identifier.value not in self.scope:
            raise RuntimeError("undefined variable {} at line {}".format(node_identifier.value,
                                                                         node.lineno))
        return ecma_ast.BracketAccessor(node_identifier, expr_identifier)

    def _translate_List(self, node, childs):
        return ecma_ast.Array(childs)

    def _translate_Dict(self, node, childs):
        properties = []

        msize = int(len(childs)/2)
        keys = childs[:msize]
        values = childs[msize:]

        for key, value in zip(keys, values):
            identifier = ecma_ast.Identifier(key.value)
            assign_instance = ecma_ast.Assign(":", identifier, value)
            properties.append(assign_instance)

        return ecma_ast.Object(properties)

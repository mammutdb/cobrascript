# -*- coding: utf-8 -*-

import ast
import re
from collections import defaultdict

from .utils import GenericStack
from .utils import LeveledStack
from .utils import ScopeStack
from .utils import to_camel_case
from .utils import normalize

from . import ast as ecma_ast


class TranslateVisitor(ast.NodeVisitor):
    def __init__(self, module_as_closure=False, auto_camelcase=False, debug=True):
        super().__init__()

        self.level_stack = LeveledStack()
        self.bin_op_stack = GenericStack()
        self.scope = ScopeStack()

        self.references = defaultdict(lambda: 0)
        self.indentation = 0

        self.meta_debug = debug
        self.meta_auto_camelcase = auto_camelcase
        self.meta_module_as_closure = module_as_closure
        self.meta_global_object = None
        self.meta_global_new = None

    def print(self, *args, **kwargs):
        if self.meta_debug:
            prefix = "    " * self.indentation
            print(prefix, *args, **kwargs)

    def translate(self, tree):
        return self.visit(tree, root=True)

    def process_idf(self, identifier):
        if self.meta_auto_camelcase:
            identifier.value = to_camel_case(identifier.value)
        return identifier

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

        return js_node

    # Special visit fields

    def visit_BinOp(self, node):
        self.bin_op_stack.push(node)
        self.generic_visit(node)
        self.bin_op_stack.pop()

    def visit_BoolOp(self, node):
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

    def _translate_UnaryOp(self, node, childs):
        operator = ""
        if type(node.op) == ast.USub:
            operator = "-"
        elif type(node.op) == ast.UAdd:
            operator = "+"
        elif type(node.op) == ast.Not:
            operator = "!"
        elif type(node.op) == ast.Invert:
            operator = "~"

        return ecma_ast.UnaryOp(operator, childs[0], postfix=False)

    def _translate_BinOp(self, node, childs):
        if type(node.op) == ast.Pow:
            da = ecma_ast.DotAccessor(ecma_ast.Identifier("Math"),
                                      ecma_ast.Identifier("pow"))
            n = ecma_ast.FunctionCall(da, [childs[0], childs[1]])
        elif type(node.op) == ast.FloorDiv:
            da = ecma_ast.DotAccessor(ecma_ast.Identifier("Math"),
                                      ecma_ast.Identifier("floor"))
            op = ecma_ast.BinOp("/", childs[0], childs[1])
            n = ecma_ast.FunctionCall(da, [op])
        elif type(node.op) == ast.BitOr:
            n = ecma_ast.BinOp("|", childs[0], childs[1])
        elif type(node.op) == ast.BitAnd:
            n = ecma_ast.BinOp("&", childs[0], childs[1])
        elif type(node.op) == ast.BitXor:
            n = ecma_ast.BinOp("^", childs[0], childs[1])
        elif type(node.op) == ast.LShift:
            n = ecma_ast.BinOp("<<", childs[0], childs[1])
        elif type(node.op) == ast.RShift:
            n = ecma_ast.BinOp(">>", childs[0], childs[1])
        else:
            n = ecma_ast.BinOp(childs[1], childs[0], childs[2])
            if not self.bin_op_stack.is_empty():
                n._parens = True
        return n

    def _translate_BoolOp(self, node, childs):
        binop = ecma_ast.BinOp(childs[0], childs[1], childs[2])
        if not self.bin_op_stack.is_empty():
            binop._parens = True
        return binop

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

    def _translate_Is(self, node, childs):
        return "==="

    def _translate_Eq(self, node, childs):
        return "==="

    def _translate_NotEq(self, node, childs):
        return "!=="

    def _translate_Lt(self, node, childs):
        return "<"

    def _translate_LtE(self, node, childs):
        return "<="

    def _translate_Gt(self, node, childs):
        return ">"

    def _translate_GtE(self, node, childs):
        return ">="

    def _translate_And(self, node, childs):
        return "&&"

    def _translate_Or(self, node, childs):
        return "||"

    def _translate_Delete(self, node, childs):
        deletes = []
        for child in childs:
            if child.value not in self.scope:
                self.scope.set(child.value, child)
            deletes.append(ecma_ast.ExprStatement(ecma_ast.UnaryOp('delete', child)))
        return ecma_ast.SetOfNodes(deletes)

    def _translate_Return(self, node, childs):
        if childs:
            return ecma_ast.Return(childs[0])
        return ecma_ast.Return()

    def _create_scope_var_statement(self, root=False):
        scope_identifiers = self.scope.get_scope_identifiers(root=root)

        if len(scope_identifiers) == 0:
            return None

        scope_var_decls = list(map(lambda x: ecma_ast.VarDecl(x), scope_identifiers))
        return ecma_ast.VarStatement(scope_var_decls)

    def _translate_FunctionDef(self, node, childs):
        scope_var_statement = self._create_scope_var_statement()

        if node.decorator_list:
            body_stmts = childs[1:-len(node.decorator_list)]
            decorators = childs[-len(node.decorator_list):]
        else:
            body_stmts = childs[1:]
            decorators = []

        # Add scope var statement only if any var is defined
        if scope_var_statement:
            body_stmts = [scope_var_statement] + body_stmts

        identifier = self.process_idf(ecma_ast.Identifier(node.name))
        func_expr = ecma_ast.FuncExpr(None, childs[0], body_stmts)
        var_decl = ecma_ast.VarDecl(identifier, func_expr)

        # Drop inner scope (temporary is unused)
        self.scope.drop_scope()

        if node.name not in self.scope:
            self.scope.set(node.name, identifier)

        expr_stmt = ecma_ast.ExprStatement(var_decl)

        # Add fast link to func expression
        # Usefull for class translations
        expr_stmt._func_expr = func_expr
        expr_stmt._func_expr._identifier = identifier

        decoration_statements = []
        for decorator in decorators:
            fcall_expr = ecma_ast.FunctionCall(decorator, [identifier])
            assign_expr = ecma_ast.Assign("=", identifier, fcall_expr)
            decoration_statements.append(ecma_ast.ExprStatement(assign_expr))

        if decoration_statements:
            reversed_decoration_statements = list(reversed(decoration_statements))
            return ecma_ast.SetOfNodes([expr_stmt] + reversed_decoration_statements)

        return expr_stmt

    def _translate_Lambda(self, node, childs):
        exprs = map(ecma_ast.ExprStatement, childs[1:])
        func_expr = ecma_ast.FuncExpr(None, childs[0], list(exprs))
        return func_expr

    def _translate_Module(self, node, childs):
        body_stmts = childs

        if self.meta_global_object:
            global_idf = self.process_idf(ecma_ast.Identifier(self.meta_global_object))
            self.scope.set(self.meta_global_object, global_idf, special_form=True)
            global_assign = ecma_ast.Assign("=", global_idf, ecma_ast.Identifier("this"))
            global_stmt = ecma_ast.ExprStatement(global_assign)
            body_stmts = [global_stmt] + body_stmts

        if self.meta_global_new:
            new_idf = self.process_idf(ecma_ast.Identifier(self.meta_global_new))
            self.scope.set(self.meta_global_new, new_idf, special_form=True)

            raw_new_js = """
            function() {
                var ___args_array = Array.apply(null, arguments);
                var ___clazz = ___args_array.slice(0, 1)[0];
                return new (___clazz.bind.apply(___clazz, ___args_array))();
            }"""

            normalized_new_js = "".join(normalize(raw_new_js).split("\n"))
            normalized_new_js = re.sub(r"\s+", " ", normalized_new_js)

            new_assign = ecma_ast.Assign("=", new_idf, ecma_ast.String(normalized_new_js))
            new_stmt = ecma_ast.ExprStatement(new_assign)
            body_stmts = [new_stmt] + body_stmts

        scope_var_statement = self._create_scope_var_statement(root=True)
        self.scope.drop_scope()

        if scope_var_statement:
            body_stmts = [scope_var_statement] + body_stmts

        if self.meta_module_as_closure:
            container_func_expr = ecma_ast.FuncExpr(None, None, body_stmts)
            container_func_expr._parens = True
            dotaccessor_func_expr = ecma_ast.DotAccessor(container_func_expr,
                                                         ecma_ast.Identifier("call"))

            main_function_call = ecma_ast.FunctionCall(dotaccessor_func_expr, [ecma_ast.This()])
            main_expr = ecma_ast.ExprStatement(main_function_call)
            return ecma_ast.Program([main_expr])

        return ecma_ast.Program(body_stmts)

    def _translate_Import(self, node, childs):
        for child in childs:
            if child["name"] == "_global":
                self.meta_global_object = child["asname"] or child["name"]

            elif child["name"] == "_new":
                self.meta_global_new = child["asname"] or child["name"]

        return None

    def _translate_alias(self, node, childs):
        return node.__dict__

    def _translate_Expr(self, node, childs):
        return ecma_ast.ExprStatement(childs[0])

    def _translate_arguments(self, node, childs):
        return childs

    def _translate_Break(self, node, childs):
        return ecma_ast.Break()

    def _translate_Continue(self, node, childs):
        return ecma_ast.Continue()

    def _translate_Name(self, node, childs):
        if node.id == "None":
            return ecma_ast.Null(node.id)

        elif node.id == "True":
            return ecma_ast.Boolean("true")

        elif node.id == "False":
            return ecma_ast.Boolean("false")

        name = node.id
        return self.process_idf(ecma_ast.Identifier(name))

    def _translate_arg(self, node, childs):
        return self.process_idf(ecma_ast.Identifier(node.arg))

    def _translate_Str(self, node, childs):
        return ecma_ast.String('"{}"'.format(node.s))

    def _translate_Call(self, node, childs):
        if isinstance(node.func, ast.Name):
            fcall = ecma_ast.FunctionCall(childs[0], childs[1:])
            return fcall

        else:
            dotaccessor = childs[0]
            arguments = list(filter(bool, childs[1:]))

            function_call = ecma_ast.FunctionCall(dotaccessor, arguments)
            return function_call

    def _translate_Attribute(self, node, childs):
        variable_identifier = childs[0]
        attribute_access_identifier = self.process_idf(ecma_ast.Identifier(node.attr))
        dotaccessor = ecma_ast.DotAccessor(variable_identifier, attribute_access_identifier)
        return dotaccessor

    def _translate_AugAssign(self, node, childs):
        target = childs[0]
        assign_decl = None

        # FIXME: should be used issubclass instead of type
        if type(node.op) == ast.Pow or type(node.op) == ast.FloorDiv:
            if type(node.op) == ast.Pow:
                da = ecma_ast.DotAccessor(ecma_ast.Identifier("Math"),
                                          ecma_ast.Identifier("pow"))
                n = ecma_ast.FunctionCall(da, [childs[0], childs[1]])
            elif type(node.op) == ast.FloorDiv:
                op = ecma_ast.BinOp("/", childs[0], childs[1])
                da = ecma_ast.DotAccessor(ecma_ast.Identifier("Math"),
                                          ecma_ast.Identifier("floor"))
                n = ecma_ast.FunctionCall(da, [op])
            assign_decl = ecma_ast.Assign("=", target, n)
        else:
            op, value = childs[1], childs[2]

            if isinstance(target, ecma_ast.Identifier):
                if target.value not in self.scope:
                    self.scope.set(target.value, target)

            if assign_decl is None:
                assign_decl = ecma_ast.Assign(op + "=", target, value)
            else:
                assign_decl = ecma_ast.Assign(op + "=", target, assign_decl)

        return ecma_ast.ExprStatement(assign_decl)

    def _translate_Assign(self, node, childs):
        identifiers = childs[:-1]
        value = childs[-1]

        main_assign_decl = None
        extra_exprs = []

        for target in reversed(identifiers):
            if isinstance(target, ecma_ast.Identifier):
                if target.value not in self.scope:
                    self.scope.set(target.value, target)

            # Multiple assignation
            if isinstance(target, ecma_ast.Array) and isinstance(value, ecma_ast.Array):
                # Mock array target with identifier
                new_target = self.get_unique_identifier("_ref")

                # Create additional assing expresion for each item of array/tuple.
                for i, item in enumerate(target):
                    _ba = ecma_ast.BracketAccessor(new_target, ecma_ast.Number(str(i)))
                    _as = ecma_ast.Assign("=", item, _ba)
                    extra_exprs.append(ecma_ast.ExprStatement(_as))

                # Substitute a real target with autogenerated new identifier.
                target = new_target

            if main_assign_decl is None:
                main_assign_decl = ecma_ast.Assign("=", target, value)
            else:
                main_assign_decl = ecma_ast.Assign("=", target, main_assign_decl)

        main_expr = ecma_ast.ExprStatement(main_assign_decl)
        if len(extra_exprs) == 0:
            return main_expr
        return ecma_ast.SetOfNodes([main_expr] + extra_exprs)


    def _translate_Index(self, node, childs):
        return childs[0]

    def _translate_Subscript(self, node, childs):
        node_identifier = childs[0]

        if hasattr(node.slice, 'lower') or hasattr(node.slice, 'upper') or hasattr(node.slice, 'step'):
            if hasattr(node.slice, 'step') and node.slice.step:
                raise NotImplementedError(":D")

            slice_values = []
            if hasattr(node.slice, 'lower') and node.slice.lower:
                slice_values.append(self.translate(node.slice.lower))
            else:
                slice_values.append(ecma_ast.Number("0"))

            if hasattr(node.slice, 'upper') and node.slice.upper:
                slice_values.append(self.translate(node.slice.upper))

            da = ecma_ast.DotAccessor(node_identifier, ecma_ast.Identifier("slice"))
            return ecma_ast.FunctionCall(da, slice_values)
        else:
            expr_identifier = childs[1]

            # FIXME: convert to warning.
            # if node_identifier.value not in self.scope:
            #     raise RuntimeError("undefined variable {} at line {}".format(node_identifier.value,
            #                                                                  node.lineno))
            return ecma_ast.BracketAccessor(node_identifier, expr_identifier)

    def _translate_List(self, node, childs):
        return ecma_ast.Array(childs)

    def _translate_Tuple(self, node, childs):
        return ecma_ast.Array(childs)

    def _translate_Dict(self, node, childs):
        properties = []

        msize = int(len(childs)/2)
        keys = childs[:msize]
        values = childs[msize:]

        for key, value in zip(keys, values):
            identifier = self.process_idf(ecma_ast.Identifier(key.value))
            assign_instance = ecma_ast.Assign(":", identifier, value)
            properties.append(assign_instance)

        return ecma_ast.Object(properties)

    def _translate_If(self, node, childs):
        predicate = childs[0]

        # consecuent
        consequent_blocks_size = len(node.body)
        consequent_blocks = childs[1:consequent_blocks_size+1]
        consequent = ecma_ast.Block(consequent_blocks)

        # alternative
        alternative_blocks_size = len(node.orelse)
        alternative_blocks = childs[consequent_blocks_size+1:]

        if alternative_blocks_size > 0:
            if alternative_blocks_size == 1 and isinstance(alternative_blocks[0], ecma_ast.If):
                alternative = alternative_blocks[0]
            else:
                alternative = ecma_ast.Block(alternative_blocks)
        else:
            alternative = None

        ifnode = ecma_ast.If(predicate, consequent, alternative)
        return ifnode

    def _translate_Compare(self, node, childs):
        binop = ecma_ast.BinOp(childs[1], childs[0], childs[2])
        # if not self.bin_op_stack.is_empty():
        #     n._parens = True
        return binop

    def get_unique_identifier(self, prefix="ref"):
        for i in range(100000000):
            candidate = "{}_{}".format(prefix, i)
            if candidate not in self.scope:
                identifier = self.process_idf(ecma_ast.Identifier(candidate))
                self.scope.set(candidate, identifier)
                return identifier

    def _translate_While(self, node, childs):
        predicate = childs[0]

        # consecuent
        body_blocks_size = len(node.body)
        body = childs[1:body_blocks_size+1]

        else_body = None
        if node.orelse:
            else_condition_idf = self.get_unique_identifier()
            else_body = childs[body_blocks_size+1:]

        if else_body is None:
            return ecma_ast.While(predicate, ecma_ast.Block(body))

        # FIXME: this seems inconsistent :S
        initialize_assign = ecma_ast.Assign("=", else_condition_idf,
                                            ecma_ast.Boolean("true"))
        initialize_condition = ecma_ast.ExprStatement(initialize_assign)

        while_body = ecma_ast.Block([
            ecma_ast.ExprStatement(ecma_ast.Assign("=", else_condition_idf, ecma_ast.Boolean("false")))
        ] + body)

        while_sentence = ecma_ast.While(predicate, while_body)
        else_sentence = ecma_ast.If(else_condition_idf, ecma_ast.Block(else_body))
        return ecma_ast.SetOfNodes([initialize_condition, while_sentence, else_sentence])

    def _translate_ListComp(self, node, childs):
        if len(node.generators) != 1:
            raise RuntimeError("Only implemented 1 generator per comprehension")

        generator = node.generators[0]
        values = generator.iter
        target = generator.target
        expresion = childs
        ifs = generator.ifs

        counter_idf = self.get_unique_identifier("_i")
        len_idf = self.get_unique_identifier("_len")
        values_idf = self.get_unique_identifier("_values")
        results_idf = self.get_unique_identifier("_results")

        counter_var_decl = ecma_ast.VarDecl(counter_idf)
        len_var_decl = ecma_ast.VarDecl(len_idf)
        values_var_decl = ecma_ast.VarDecl(values_idf)
        results_var_decl = ecma_ast.VarDecl(results_idf)

        var_stmt = ecma_ast.VarStatement([counter_var_decl, len_var_decl, values_var_decl, results_var_decl])

        initialize_values = ecma_ast.ExprStatement(ecma_ast.Assign("=", values_idf, self.translate(values)))
        initialize_results = ecma_ast.ExprStatement(ecma_ast.Assign("=", results_idf, ecma_ast.Array([])))

        # For init
        init = ecma_ast.Comma(
            ecma_ast.Assign("=", counter_idf, ecma_ast.Number("0")),
            ecma_ast.Assign("=", len_idf, ecma_ast.DotAccessor(values_idf, ecma_ast.Identifier("length")))
        )

        # For condition
        cond = ecma_ast.BinOp("<", counter_idf, len_idf)

        # For count
        count = ecma_ast.UnaryOp("++", counter_idf, postfix=True)

        push_on_results = ecma_ast.FunctionCall(
            ecma_ast.DotAccessor(results_idf, ecma_ast.Identifier("push")),
            ecma_ast.ExprStatement(ecma_ast.BracketAccessor(values_idf, counter_idf))
        )

        if ifs:
            composed_condition = None
            for comprehension_cond in ifs:
                if composed_condition is None:
                    composed_condition = self.translate(comprehension_cond)
                else:
                    composed_condition = ecma_ast.BinOp("&&", composed_condition, self.translate(comprehension_cond))
            for_loop_block = ecma_ast.Block([ecma_ast.If(composed_condition, ecma_ast.Block([push_on_results]))])
        else:
            for_loop_block = ecma_ast.Block([push_on_results])

        for_stmt = ecma_ast.For(init, cond, count, for_loop_block)

        return_results = ecma_ast.Return(results_idf)

        func_block = ecma_ast.Block([var_stmt, initialize_values, initialize_results, for_stmt, return_results])

        func_expr = ecma_ast.FuncExpr(None, None, func_block)
        func_expr._parens = True

        listcomp_stmt = ecma_ast.FunctionCall(func_expr)

        return listcomp_stmt

    def _translate_For(self, node, childs):
        counter_idf = self.get_unique_identifier()
        iterable_idf = self.get_unique_identifier()

        item_idf = childs[0]
        iterable = childs[1]
        main_body_expr = childs[2]

        iterable_var_decl = ecma_ast.VarDecl(iterable_idf, iterable)
        iterable_var_stmt = ecma_ast.VarStatement(iterable_var_decl)

        # For condition
        cond_right_stmt = ecma_ast.DotAccessor(iterable_idf, ecma_ast.Identifier("length"))
        cond = ecma_ast.BinOp("<", counter_idf, cond_right_stmt)

        # For count
        count = ecma_ast.UnaryOp("++", counter_idf, postfix=True)

        # For init
        init_first = ecma_ast.Assign("=", counter_idf, ecma_ast.Number("0"))
        init_second = ecma_ast.Assign("=", iterable_idf, iterable)
        init = ecma_ast.Comma(init_first, init_second)

        # For body
        accesor = ecma_ast.BracketAccessor(iterable_idf, counter_idf)
        item_body_stmt = ecma_ast.ExprStatement(
                            ecma_ast.Assign("=", item_idf, accesor))
        if item_idf.value not in self.scope:
            self.scope.set(item_idf.value, item_idf)

        body_block = ecma_ast.Block([item_body_stmt, main_body_expr])

        # For
        for_stmt = ecma_ast.For(init, cond, count, body_block)

        return for_stmt

    def _translate_Raise(self, node, childs):
        return ecma_ast.Throw(childs[0])

    def _translate_Try(self, node, childs):
        fin_stmts = []
        finally_node = None

        if len(node.finalbody) > 0:
            fin_stmts = childs[-len(node.finalbody):]
            childs = childs[:-len(node.finalbody)]

        catches_stmts = list(filter(lambda x: isinstance(x, ecma_ast.Catch), childs))

        try_stmts = list(filter(lambda x: isinstance(x, ecma_ast.ExprStatement), childs))
        catch_stmt = len(catches_stmts) > 0 and catches_stmts[0] or None

        if len(fin_stmts) > 0:
            fin_block = ecma_ast.Block(fin_stmts)
            finally_node = ecma_ast.Finally(fin_block)

        try_block = ecma_ast.Block(try_stmts)
        try_node = ecma_ast.Try(try_block, catch=catch_stmt, fin=finally_node)
        return try_node

    def _translate_ExceptHandler(self, node, childs):
        expr_stmts = list(filter(lambda x: isinstance(x, ecma_ast.ExprStatement), childs))

        identifier = self.process_idf(ecma_ast.Identifier(node.name))
        # identifiers = list(filter(lambda x: isinstance(x, ecma_ast.Identifier), childs))

        block_stmt = ecma_ast.Block(expr_stmts)
        return ecma_ast.Catch(identifier, block_stmt)

    def _translate_ClassDef(self, node, childs):
        functions = list(map(lambda x: x._func_expr,
                                filter(lambda x: hasattr(x, "_func_expr"), childs)))
        childs = list(filter(lambda x: not hasattr(x, "_func_expr"), childs))

        # Constructor

        constructor_func_expr = None
        for fn in functions:
            if fn._identifier.value == "__init__":
                constructor_func_expr = fn
                self.scope.unset("__init__")
                break

        if constructor_func_expr is None:
            constructor_func_expr = ecma_ast.FuncExpr(None, None, None)
        else:
            functions = list(filter(lambda x: x is not constructor_func_expr, functions))

        self.scope.new_scope()
        inner_class_idf = self.get_unique_identifier("classref")

        assign_expr = ecma_ast.Assign("=", inner_class_idf, constructor_func_expr)
        constructor_expr = ecma_ast.ExprStatement(assign_expr)

        body_stmts = [constructor_expr]

        # Functions definition
        for fn in functions:
            fn_dt_prototype = ecma_ast.DotAccessor(inner_class_idf,
                                                   ecma_ast.Identifier("prototype"))
            fn_dt_attr = ecma_ast.DotAccessor(fn_dt_prototype, fn._identifier)
            fn_assign_expr = ecma_ast.Assign("=", fn_dt_attr, fn)
            fn_expr = ecma_ast.ExprStatement(fn_assign_expr)

            body_stmts.append(fn_expr)

        body_stmts.append(ecma_ast.Return(inner_class_idf))

        # Class closure
        # Contains all class definition
        scope_var_statement = self._create_scope_var_statement()
        main_container_func = ecma_ast.FuncExpr(None, None, [scope_var_statement] + body_stmts)
        main_container_func._parens = True
        main_function_call = ecma_ast.FunctionCall(main_container_func)
        main_identifier = self.process_idf(ecma_ast.Identifier(node.name))
        main_assign = ecma_ast.Assign("=", main_identifier, main_function_call)
        main_expr = ecma_ast.ExprStatement(main_assign)

        self.scope.drop_scope()

        if node.name not in self.scope:
            self.scope.set(node.name, main_identifier)

        return main_expr

# -*- coding: utf-8 -*-

import argparse
import ast
import functools
import io
import sys

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


def translate(data:object, **kwargs) -> object:
    """
    Given a python ast tree, translate it to
    ecma ast.
    """

    return translator.TranslateVisitor(**kwargs).translate(data)


def compile(data:str, translate_options=None, compile_options=None) -> str:
    if translate_options is None:
        translate_options = {}

    if compile_options is None:
        compile_options = {}

    # Normalize
    data = utils.normalize(data)

    # Parse python to ast
    python_tree = parse(data)

    # Translate python ast to js ast
    ecma_tree = translate(python_tree, **translate_options)

    # Compile js ast to js string
    return compiler.ECMAVisitor(**compile_options).visit(ecma_tree)


def _read_file(path:str):
    with io.open(path, "rt") as f:
        return f.read()

def _compile_files(paths:list, join=False, translate_options=None, compile_options=None) -> str:
    _compile = functools.partial(compile, translate_options=translate_options,
                                compile_options=compile_options)
    if join:
        return _compile("\n".join(_read_file(path) for path in paths))
    return "\n\n".join(_compile(_read_file(path)) for path in paths)


def main():
    parser = argparse.ArgumentParser(prog="cobrascript",
                                     description="Python to Javascript translator.")
    parser.add_argument("files", metavar="input.py", type=str, nargs="+",
                        help="A list of python files for translate.")
    parser.add_argument("-g", "--debug", action="store_true", default=False,
                        help="Activate debug mode (only for developers).")
    parser.add_argument("-w", "--warnings", action="store_true", default=False,
                        help="Show static analizer warnings.")
    parser.add_argument("-o", "--output", action="store", type=str, metavar="outputfile.js",
                        help="Set output file (by default is stdout).")
    parser.add_argument("-b", "--bare", action="store_true", default=False,
                        help="Compile without a toplevel closure.")
    parser.add_argument("-j", "--join", action="store_true", default=False,
                        help="Join python files before compile.")
    parser.add_argument("--indent", action="store", type=int, default=4,
                        help="Set default output indentation level.")
    parser.add_argument("--auto-camelcase", action="store_true", default=False,
                        dest="auto_camelcase", help="Convert all identifiers to camel case.")

    parsed = parser.parse_args()

    reader_join = True if parsed.join else False
    translate_options = {"module_as_closure": not parsed.bare,
                         "debug": parsed.debug,
                         "auto_camelcase": parsed.auto_camelcase}
    compile_options = {"indent_chars": int(parsed.indent/2)}

    compiled_data = _compile_files(parsed.files, join=reader_join,
                                   translate_options=translate_options,
                                   compile_options=compile_options)

    if parsed.output:
        with io.open(parsed.output, "wt") as f:
            print(compiled_data, file=f)
    else:
        print(compiled_data, file=sys.stdout)

    return 0

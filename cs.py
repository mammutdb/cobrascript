#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io

from cobra.base import compile

def main(filename):
    with io.open(filename, "rt") as f:
        text = f.read()
    r = compile(text)
    print(r)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise RuntimeError("Invalid parameters")

    sys.exit(main(sys.argv[1]))

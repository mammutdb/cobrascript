# -*- coding: utf-8 -*-

import textwrap

from collections import defaultdict
from collections import ChainMap
from cobra.ast import SetOfNodes


def normalize(data:str):
    return textwrap.dedent(data).strip()


def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + "".join(x.title() for x in components[1:])


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
        if type(value) == SetOfNodes:
            self.data[self.level] += value
        else:
            self.data[self.level].append(value)

    def get_value(self):
        return self.data[self.level]


class ScopeStack(object):
    def __init__(self):
        self.data = ChainMap({})
        self.special_forms = {}

    def __contains__(self, key):
        return key in self.data

    def set(self, key, value, special_form=False):
        if not special_form:
            self.data[key] = value
        else:
            self.special_forms[key] = value

        if not self.validate():
            raise RuntimeError("Special form overwriten")

    def unset(self, key):
        del self.data[key]

    def is_empty(self):
        return len(self.data) == 0

    def new_scope(self):
        self.data = self.data.new_child()

    def drop_scope(self):
        self.data = self.data.parents

    def get_scope_identifiers(self, root=False):
        first_level = self.data.maps[0] if len(self.data.maps) > 0 else {}
        merged_stmts = list(first_level.values())

        if root:
            merged_stmts = list(self.special_forms.values()) + merged_stmts

        return sorted(merged_stmts, key=lambda x: x.value)

    def validate(self):
        normal_scope = set(self.data.keys())
        special_form_scope = set(self.special_forms.keys())
        return len(normal_scope.intersection(special_form_scope)) == 0

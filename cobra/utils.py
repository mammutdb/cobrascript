# -*- coding: utf-8 -*-

import textwrap

from collections import defaultdict
from collections import ChainMap


def normalize(data:str):
    return textwrap.dedent(data).strip()


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

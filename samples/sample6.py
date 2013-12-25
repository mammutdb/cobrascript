# -*- coding: utf-8 -*-

def debug(func):
    def _decorator():
        console.log("call....")
        return func.apply(null, arguments)

    return _decorator


@debug
def sum(a1, a2, a3):
    return a1 + a2 + a3

console.log(sum(1,2,3))

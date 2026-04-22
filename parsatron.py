#   _____                     _                   
#  |  __ \                   | |                  
#  | |__) |_ _ _ __ ___  __ _| |_ _ __ ___  _ __  
#  |  ___/ _` | '__/ __|/ _` | __| '__/ _ \| '_ \ 
#  | |  | (_| | |  \__ \ (_| | |_| | | (_) | | | |
#  |_|   \__,_|_|  |___/\__,_|\__|_|  \___/|_| |_|

from functools import cache, reduce
from itertools import chain
from operator import add
# ===== Results & Errors =====
FAIL = object()
def make_result(i, parsed, error): return [i, parsed, error]
def result_pos(result): return result[0]
def parsed(result): return result[1]
def error(result): return result[2]
def is_success(result): return parsed(result) is not FAIL

def make_error(i, possibilities): return [i, possibilities]
def error_pos(error): return error[0]
def error_possibilities(error): return error[1]

def error_merge(a, b):
    if error_pos(a) > error_pos(b): return a
    elif error_pos(b) > error_pos(a): return b
    return make_error(error_pos(a), error_possibilities(a) | error_possibilities(b))

def error_msg(error):
    if not error_possibilities(error):
        return ''
    return f"@{error_pos(error)}: Expected {' OR '.join(error_possibilities(error))}"

def succeed(thing, pos):
    return make_result(pos, thing, make_error(pos, set()))
    
def fail(expected, pos):
    return make_result(pos, FAIL, make_error(pos, {expected}))

# ===== Parsing Primitives =====
def success(x):
    return lambda source, i: succeed(x, i)
def failure(x):
    return lambda source, i: fail(x, i)

def consume(name, predicate, n):
    def parser(source, cursor=0):
        if 0 <= cursor < len(source) and predicate(source[cursor : cursor + n]):
            return succeed(source[cursor:cursor + n], cursor + n)
        else:
            return fail(name, cursor)
    return parser

# ===== Primitive Parsing Combinators =====
def label(name, parser):
    def f(source, pos=0):
        result = parser(source, pos)
        if is_success(result):
            return result
        return make_result(pos,
            FAIL,
            make_error(
                error_pos(error(result)), 
                error_possibilities(error(result))))
    return f

def bind(parser, continuation):
    def f(source, pos=0):
        result = parser(source, pos)
        if not is_success(result):
            return make_result(pos, FAIL, error(result))
        another_result = continuation(parsed(result))(source, result_pos(result))
        if not is_success(another_result):
            return make_result(pos, FAIL, error_merge(error(result), error(another_result)))
        return make_result(
                result_pos(another_result),
                parsed(another_result),
                error_merge(error(result), error(another_result)))
    return f

def recover(parser, handler):
    def f(source, pos=0):
        result = parser(source, pos)
        if is_success(result):
            return result
        another_result = handler(error_msg(error(result)))(source, result_pos(result))
        if is_success(another_result):
            return make_result(
                    result_pos(another_result),
                    parsed(another_result),
                    error_merge(error(result), error(another_result)))
        return make_result(pos, FAIL, error_merge(error(result), error(another_result)))
    return f

@cache
def lazy(parser_f):
    def f(*args):
        return parser_f()(*args)
    return f

# ===== Derived Parsing Combinators =====
def charIf(f, name):
    return consume(name, f, 1)

def char(c):
    return consume(repr(c), lambda x: x == c, 1)

def charIn(chars):
    return consume(f"any of {repr(chars)}", lambda x: x in chars, 1)

def string(x):
    return consume(repr(x), lambda chunk: chunk == x, len(x))

def ignoreLeft(p1, p2):
    return bind(p1, lambda _:
                bind(p2, lambda y:
                success(y)))

def ignoreRight(p1, p2):
    return bind(p1, lambda x:
                bind(p2, lambda _:
                success(x)))

def wrapped(starting, ending, parser):
    return ignoreLeft(starting, ignoreRight(parser, ending))

def fmap(f, parser):
    return bind(parser, lambda result: 
                success(f(result)))

def sequence(combiner, *parsers):
    if len(parsers) == 1:
        return parsers[0]
    return bind(parsers[0], lambda thing: 
                bind(sequence(combiner, *parsers[1:]), lambda another_thing: 
                    success(combiner(thing, another_thing))))

def alternate(*parsers):
    if len(parsers) == 1:
        return parsers[0]
    return recover(parsers[0],
                lambda _: alternate(*parsers[1:]))

def optional(default, parser):
    return alternate(parser, success(default))

def many(combiner, empty, parser):
    return optional(empty,
                sequence(combiner, 
                    parser,
                    lazy(lambda: many(combiner, empty, parser))))

def some(combiner, empty, parser):
    return sequence(combiner,
                parser,
                many(combiner, empty, parser))

def separatedMany(combiner, empty, sep, parser):
    return optional(empty, 
                separatedSome(combiner, empty, sep,
                    parser))

def separatedSome(combiner, empty, sep, parser):
    return sequence(combiner,
                parser,
                many(combiner, empty,
                    ignoreLeft(sep,
                        parser)))

# ===== RUNNER =====
def run(parser, source, on_error = (lambda x: x)):
    result = parser(source)
    if is_success(result):
        return parsed(result)
    return on_error(error_msg(error(result)))
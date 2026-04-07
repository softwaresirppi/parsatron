#   _____                     _                   
#  |  __ \                   | |                  
#  | |__) |_ _ _ __ ___  __ _| |_ _ __ ___  _ __  
#  |  ___/ _` | '__/ __|/ _` | __| '__/ _ \| '_ \ 
#  | |  | (_| | |  \__ \ (_| | |_| | | (_) | | | |
#  |_|   \__,_|_|  |___/\__,_|\__|_|  \___/|_| |_|

from functools import cache

class Fail:
    def __init__(self, expected):
        self.expected = expected
    def __repr__(self):
        return f"Expected({self.expected})"

def isFail(x):
    return isinstance(x, Fail)

def succeed(x):
    return lambda string, i: (x, string, i)

def exactly(x):
    def f(string, i=0):
        if string[i:i+len(x)] == x:
            return x, string, i + len(x)
        else:
            return Fail(x), string, i
    return f

def charIf(predicate):
    def f(string, i=0):
        if 0 <= i < len(string) and predicate(string[i]):
            return string[i], string, i + 1
        else:
            return Fail("satisfied"), string, i
    return f

def bind(parser, continuation):
    def f(string, i=0):
        thing, source, i = parser(string, i)
        if isFail(thing):
            return thing, source, i
        return continuation(thing)(source, i)
    return f

def alternate(*parsers):
    def f(string, i=0):
        best_fail, source, best_i = Fail("no alternatives"), string, i
        for p in parsers: 
            alt_thing, source, alt_i = p(string, i)
            if not isFail(alt_thing):
                return alt_thing, source, alt_i
            if best_i < alt_i:
                best_fail, source, best_i = alt_thing, source, alt_i
        return best_fail, source, best_i
    return f

def label(expected, parser):
    def f(string, i=0):
        thing, source, i = parser(string, i)
        if isFail(thing):
            return Fail(expected), source, i
        return thing, source, i
    return f

def report(thing, string, i):
    def truncate(text, n):
        return text[:n] + '...' if n < len(text) else text
    if isFail(thing):
        return f"Unexpected {repr(truncate(string[i:], 32))}, expected {repr(thing.expected)}"
    if i == len(string):
        return thing
    else:
        return f"Unconsumed input: {repr(truncate(string[i:], 32))}"

@cache
def lazy(parser_f):
    def f(string, i=0):
        return parser_f()(string, i)
    return f

# ===== ABSTRACTION CURTAIN =====

def charIn(chars):
    return charIf(lambda x: x in chars)

def fmap(f, parser):
    return bind(parser, lambda result: 
            succeed(f(result)))

def ignoreLeft(p1, p2):
    return bind(p1, lambda _:
           bind(p2, lambda y:
           succeed(y)))

def ignoreRight(p1, p2):
    return bind(p1, lambda x:
           bind(p2, lambda _:
           succeed(x)))

def wrapped(starting, ending, parser):
    return ignoreLeft(starting, ignoreRight(parser, ending))

def sequence(combiner, *parsers):
    if len(parsers) == 1:
        return parsers[0]
    return bind(parsers[0], lambda thing: 
                bind(sequence(combiner, *parsers[1:]), lambda another_thing: 
                    succeed(combiner(thing, another_thing))))

def optional(default, parser):
    return alternate(parser, succeed(default))

def many(combiner, empty, parser):
    return alternate(
            sequence(combiner, parser, lazy(lambda: many(combiner, empty, parser))),
            succeed(empty))

def some(combiner, empty, parser):
    return sequence(combiner, parser, many(combiner, empty, parser))

def separatedMany(combiner, empty, sep, parser):
    return optional(empty,
        sequence(combiner,
            parser,
            many(combiner, empty, ignoreLeft(sep, parser))))

def separatedSome(combiner, empty, sep, parser):
    return sequence(combiner,
            parser,
            many(combiner,
                empty,
                ignoreLeft(sep, parser)))
#   _____                     _                   
#  |  __ \                   | |                  
#  | |__) |_ _ _ __ ___  __ _| |_ _ __ ___  _ __  
#  |  ___/ _` | '__/ __|/ _` | __| '__/ _ \| '_ \ 
#  | |  | (_| | |  \__ \ (_| | |_| | | (_) | | | |
#  |_|   \__,_|_|  |___/\__,_|\__|_|  \___/|_| |_|

class Fail:
    def __init__(self, expected):
        self.expected = expected
    def __repr__(self):
        return f"Expected({self.expected})"

def isFail(x):
    return isinstance(x, Fail)

def succeed(x):
    return lambda string: (x, string)

def exactly(x):
    def f(string):
        if string[:len(x)] == x:
            return x, string[len(x):]
        else:
            return Fail(x), string
    return f

def charIf(predicate):
    def f(string):
        if string and predicate(string[0]):
            return string[0], string[1:]
        else:
            return Fail("satisfied"), string
    return f

def bind(parser, continuation):
    def f(string):
        thing, rest = parser(string)
        if isFail(thing):
            return thing, rest
        return continuation(thing)(rest)
    return f

def alternate(*parsers):
    def f(string):
        best_fail, best_rest = Fail("deadend"), string
        for p in parsers:
            thing, rest = p(string)
            if not isFail(thing):
                return thing, rest
            if len(rest) < len(best_rest):  # furthest failure = best error
                best_fail, best_rest = thing, rest
        return best_fail, best_rest
    return f

def label(expected, parser):
    def f(string):
        thing, rest = parser(string)
        if isFail(thing):
            return Fail(expected), rest
        return thing, rest
    return f

# def alternate(*parsers):
#     if not parsers:
#         return lambda string: (Fail("deadend"), string)
#     def f(string):
#         results = [p(string) for p in parsers]
#         for thing, rest in results:
#             if not isFail(thing):
#                 return thing, rest
#         print(results)
#         return min(results, key=lambda r: len(r[1]))
#     return f

def lazy(parser_f):
    def f(string):
        return parser_f()(string)
    return f

# ABSTRACTION CURTAIN
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

def wrapped(starting, ending, parser):
    return ignoreLeft(starting, ignoreRight(parser, ending))
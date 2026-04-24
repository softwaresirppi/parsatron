from parsatron import *
from operator import add
from sys import stdin

# ===== WHITESPACE =====
whitespace = many(add, '', charIn(" \n\r\t"))

# ===== NUMBER =====
sign = optional('', char('-'))

digit = charIn("0123456789")

digits = some(add, '', digit)

wholePart = alternate(
    char('0'),
    sequence(add,
        charIf(lambda x: x in "123456789", "non-zero digit"),
        many(add, '', digit)))

fractionPart = optional('',
    sequence(add, 
        char('.'), 
        digits))

exponent_part = optional('',
    sequence(add,
        charIn("eE"),
        optional('', charIn("+-")),
        digits))

jsonNumber = fmap(lambda x: float(x) if ('.' in x or 'e' in x or 'E' in x) else int(x), 
    sequence(add,
        sign,
        wholePart,
        fractionPart,
        exponent_part))

# ===== STRING =====
escapeMap = {
    '"': '"',
    '\\': '\\',
    '/': '/',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t'
}

unicode = ignoreLeft(
    char('u'),
    fmap(lambda hex: chr(int(hex, 16)),
        sequence(add, *(4 * [charIn("0123456789abcdefABCDEF")]))))

jsonString = wrapped(char('"'), char('"'), 
    many(add, '',
        alternate(
            charIf(lambda x: not (x in "\"\\" or ord(x) < 32), "string character"),
            ignoreLeft(
                char('\\'),
                alternate(
                    fmap(escapeMap.__getitem__,
                         charIn(escapeMap.keys())),
                    unicode)))))

# ===== ARRAY =====
jsonArray = wrapped(char('['), char(']'),
    alternate(
        separatedSome(lambda x, y: [x] + y, [],
            char(','), 
            lazy(lambda: jsonValue)),
        fmap(lambda x: [], whitespace)))

# ===== OBJECT =====
jsonObject = wrapped(char('{'), char('}'),
    alternate(
        separatedSome(lambda x, y: x | y, {},
            char(','),
            sequence(lambda x, y: {x: y},
                wrapped(
                    whitespace,
                    whitespace,
                    jsonString),
                ignoreLeft(
                    char(':'),
                    lazy(lambda: jsonValue)))),
        fmap(lambda x: {}, whitespace)))

# ===== VALUE =====
jsonValue = wrapped(whitespace, whitespace,
    alternate(
        jsonString,
        jsonNumber,
        jsonArray,
        jsonObject,
        fmap(lambda _: True, string('true')),
        fmap(lambda _: False, string('false')),
        fmap(lambda _: None, string('null'))))

if __name__ == '__main__':
    print(run(jsonValue, stdin.read()))
from parsatron import *
from operator import add
from sys import stdin

# ===== WHITESPACE =====
whitespace = many(add, '', charIn(" \n\r\t"))

# ===== NUMBER =====
sign = optional('', exactly('-'))

digit = charIn("0123456789")

digits = some(add, '', digit)

wholePart = alternate(
    exactly('0'),
    sequence(add,
        charIf(lambda x: x in "123456789"),
        many(add, '', digit)))

fractionPart = optional('',
    sequence(add, 
        exactly('.'), 
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
            exactly('u'),
            fmap(lambda hex: chr(int(hex, 16)),
                sequence(add, *(4 * [charIn("0123456789abcdefABCDEF")]))))

jsonString = wrapped(exactly('"'), exactly('"'), 
    many(add, '',
        alternate(
            charIf(lambda x: not (x in "\"\\" or ord(x) < 32)),
            ignoreLeft(
                exactly('\\'),
                alternate(
                    fmap(escapeMap.__getitem__, charIn(escapeMap.keys())),
                    unicode)))))

# ===== ARRAY =====
jsonArray = wrapped(exactly('['), exactly(']'), 
    alternate(
        separatedSome(lambda x, y: [x] + y, [], exactly(','), 
            lazy(lambda: jsonValue)),
        fmap(lambda x: [], whitespace)))

# ===== OBJECT =====
jsonObject = wrapped(exactly('{'), exactly('}'),
    alternate(
        separatedSome(lambda x, y: x | y, {}, exactly(','),
            sequence(lambda x, y: {x: y},
                wrapped(
                    whitespace,
                    whitespace,
                    jsonString),
                ignoreLeft(
                    exactly(':'),
                    lazy(lambda: jsonValue)))),
        fmap(lambda x: {}, whitespace)))

# ===== VALUE =====
jsonValue = wrapped(whitespace, whitespace,
    alternate(
        jsonString,
        jsonNumber,
        jsonArray,
        jsonObject,
        fmap(lambda x: True, exactly('true')),
        fmap(lambda x: False, exactly('false')),
        fmap(lambda x: None, exactly('null'))))

print(
    report(
        *jsonValue(
            ''.join(stdin.readlines()))))
from parsatron import *
from operator import add
from sys import stdin

# ===== WHITESPACE =====
whitespace = label("whitespaces",
    many(add, '', charIn(" \n\r\t")))

# ===== NUMBER =====
sign = optional('', char('-'))

digit = label("digit", charIn("0123456789"))

digits = label("digits",
    some(add, '', digit))

wholePart = label("integer",
    alternate(
        char('0'),
        sequence(add,
            charIf(lambda x: x in "123456789", "non-zero digit"),
            many(add, '', digit))))

fractionPart = label("fractional",
    optional('',
        sequence(add, 
            char('.'), 
            digits)))

exponent_part = label("exponent",
    optional('',
        sequence(add,
            charIn("eE"),
            optional('', charIn("+-")),
            digits)))

jsonNumber = label("JSON Number",
    fmap(lambda x: float(x) if ('.' in x or 'e' in x or 'E' in x) else int(x), 
        sequence(add,
            sign,
            wholePart,
            fractionPart,
            exponent_part)))

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

unicode = label("unicode escape (\\uXXXX)",
    ignoreLeft(
        char('u'),
        fmap(lambda hex: chr(int(hex, 16)),
            sequence(add, *(4 * [charIn("0123456789abcdefABCDEF")])))))

jsonString = label("JSON String",
    wrapped(char('"'), char('"'), 
        many(add, '',
            alternate(
                charIf(lambda x: not (x in "\"\\" or ord(x) < 32), "string character"),
                label("escape sequence", 
                    ignoreLeft(
                        char('\\'),
                        alternate(
                            fmap(escapeMap.__getitem__,
                                 charIn(escapeMap.keys())),
                            unicode)))))))

# ===== ARRAY =====
jsonArray = label("JSON Array",
    wrapped(char('['), char(']'),
        alternate(
            label("array elements",
                separatedSome(lambda x, y: [x] + y, [],
                    char(','), 
                    lazy(lambda: jsonValue))),
            label("empty array",
                fmap(lambda x: [], whitespace)))))

# ===== OBJECT =====
jsonObject = label("JSON Object",
    wrapped(char('{'), char('}'),
        alternate(
            label("object entries",
                separatedSome(lambda x, y: x | y, {},
                    char(','),
                    sequence(lambda x, y: {x: y},
                        wrapped(
                            whitespace,
                            whitespace,
                            label("object key (string)", jsonString)),
                        ignoreLeft(
                            char(':'),
                            lazy(lambda: jsonValue))))),
            label("empty object",
                fmap(lambda x: {}, whitespace)))))

# ===== VALUE =====
jsonValue = label("JSON Value", 
    wrapped(whitespace, whitespace,
        alternate(
            jsonString,
            jsonNumber,
            jsonArray,
            jsonObject,
            fmap(lambda x: True, string('true')),
            fmap(lambda x: False, string('false')),
            fmap(lambda x: None, string('null')))))

if __name__ == '__main__':
    print(run(jsonValue, stdin.read()))
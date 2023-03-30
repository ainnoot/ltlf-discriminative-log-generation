from ltlf2dfa.parser.ltlf import *

__p = LTLfParser()


def existence(x):
    return __p(f"F({x})")


def absence(x):
    return __p(f"!F({x})")


def init(x):
    return __p(f"{x}")


def last(x):
    return __p(f"F({x} & X(! true))")


def choice(x, y):
    return __p(f"F({x}) | F({y})")


def exclusivechoice(x, y):
    return __p(f"(F({x}) | F({y})) & !(F({x}) & F({y}))")


def respondedexistence(x, y):
    return __p(f"F({x}) -> F({y})")


def coexistence(x, y):
    return LTLfAnd([respondedexistence(x, y), respondedexistence(y, x)])


def response(x, y):
    return __p(f"G( {x} -> F({y}))")


def alternateresponse(x, y):
    return __p(f"G({x} -> X(!{x} U {y}))")


def chainresponse(x, y):
    return __p(f"G({x}-> X({y}))")


def precedence(x, y):
    return __p(f"!{y} W {x}")


def alternateprecedence(x, y):
    return __p(f"(!{y} W {x}) & G({y} -> (!{y} W {x}))")


def chainprecedence(x, y):
    return __p(f"G(X({y}) -> {x})")


def succession(x, y):
    return LTLfAlways(LTLfAnd([response(x, y), precedence(x, y)]))


def alternatesuccession(x, y):
    return LTLfAlways(LTLfAnd([alternateresponse(x, y), alternateprecedence(x, y)]))


def chainsuccession(x, y):
    return LTLfAlways(LTLfAnd([chainresponse(x, y), chainprecedence(x, y)]))


def notcoexistence(x, y):
    return __p(f"(F({x}) -> !F({y})) & (F({y}) -> !F({x}))")


def notsuccession(x, y):
    return __p(f"G({x}) -> !F({y})")


def notchainsuccession(x, y):
    return __p(f"G({x} -> !X({y}))")

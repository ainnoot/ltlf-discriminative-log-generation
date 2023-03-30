import parse
import re
from ltlf2dfa.parser.ltlf import LTLfParser, LTLfAnd, LTLfTrue
from discriminative_log_generator.tasks.exceptions import *


def validate_activity(activity_str):
    if re.fullmatch(r"[a-z][a-z_0-9]*", activity_str) is None:
        raise InvalidActivity(activity_str)


def merge_specifications(block):
    ltlf_formulae = block["ltlf"] if "ltlf" in block.keys() else []
    decl_constraints = block["declare"] if "declare" in block.keys() else []
    formulae = []
    p = LTLfParser()

    for ltlf_f in ltlf_formulae:
        formulae.append(p(ltlf_f))

    for decl_c in decl_constraints:
        formulae.append(parse_declare_constraint(decl_c))

    if len(formulae) == 0:
        raise Exception("A Partition must be defined by at least one formula, got 0")

    if len(formulae) == 1:
        return formulae[0]

    return LTLfAnd(formulae)


def parse_declare_constraint(decl):
    mask = "{template}({activities})"
    params = parse.parse(mask, decl).named

    from discriminative_log_generator.tasks import declare_constraints

    available_declare_templates = dir(declare_constraints)

    if params["template"].lower() not in available_declare_templates:
        raise UnknownDeclareConstraint(params["template"])

    return getattr(declare_constraints, params["template"].lower())(
        *(params["activities"].split(","))
    )


def np_random_closure(method, args=dict(), seed=77):
    from numpy.random import default_rng

    g = default_rng(seed=seed)
    if method not in dir(g):
        raise Exception(f"Unknown numpy.random function {method}")

    f = getattr(g, method)
    try:
        f(**args)
    except Exception as e:
        raise Exception(
            f"Something wrong when calling {method} with parameters {args} - check numpy documentation."
        )

    def rng_closure():
        return f(**args)

    return rng_closure

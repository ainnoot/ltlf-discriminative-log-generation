import lark.exceptions

from discriminative_log_generator.parse import DECLARE_CONSTRAINTS
from ltlf2dfa.parser.ltlf import LTLfParser


__all__ = ['parse_model']


class UnknownDeclareTemplate(RuntimeError):
    def __init__(self, template):
        join = "\n\t"
        super().__init__(f"Unrecognized template: {template}. Available ones: {join.join(DECLARE_CONSTRAINTS)}")


class UnknownActivity(RuntimeError):
    def __init__(self, activity):
        super().__init__(f"The activity {activity} does not exist. Did you forget it in the `activities` block?")


def is_declare_constraint(expression):
    template, _ = expression.split('(', 1)
    template = ''.join(template.split(' ')).lower()
    return template in DECLARE_CONSTRAINTS


def parse_declare_constraint(decl, known_activities):
    if not is_declare_constraint(decl):
        raise UnknownDeclareTemplate(decl)

    template, activity_tokens = decl.split('(', 1)
    activity_tokens = activity_tokens[:-1]

    activities = []
    for token in activity_tokens.split(','):
        if token.strip().lower() not in known_activities:
            raise UnknownActivity(token)
        activities.append(token.strip().lower())

    from discriminative_log_generator.parse import __declare_constraints as declare_constraints

    return getattr(declare_constraints, ''.join(t.lower().strip() for t in template.split(' ')))(*activities)


def parse_ltlf(expression, known_activities):
    p = LTLfParser()
    formula = p(expression)
    try:
        for a in formula.find_labels():
            if a not in known_activities:
                raise UnknownActivity(a)
        return formula
    except:
        # TODO: Handle parsing errors in an informative way
        raise Exception(f"Parsing error on formula: {expression}")


def parse_model(expressions, known_activities):
    model = []
    for expression in expressions:
        if is_declare_constraint(expression):
            model.append(parse_declare_constraint(expression, known_activities))
        else:
            model.append(parse_ltlf(expression, known_activities))

    return model


if __name__ == '__main__':
    parse_ltlf("G(a ->F(b))", {'a', 'b', 'c'})
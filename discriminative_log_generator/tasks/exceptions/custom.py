class InvalidActivity(Exception):
    def __init__(self, name):
        super().__init__(f"{name} is not a valid activity name, as it does not match [a-z][a-z_0-9]*!")


class InvalidRandomnessMethod(Exception):
    def __init__(self, name):
        super().__init__(f"{name} is not a valid numpy.random random number generator.")


class InvalidRandomnessParameters(Exception):
    def __init__(self, name, params):
        super().__init__(f"{name} cannot be called with parameters {params}. Check numpy documentation.")


class EmptySpecification(Exception):
    def __init__(self):
        super().__init__()


class UnknownDeclareConstraint(Exception):
    def __init__(self, name):
        from discriminative_log_generator.tasks import declare_constraints
        msg = [f"Unknown DECLARE constraint: {name}.\n Available ones (not case-sensitive):"]
        for constraint in dir(declare_constraints):
            msg.append(f"\t * {constraint}")

        super().__init__("\n".join(msg))


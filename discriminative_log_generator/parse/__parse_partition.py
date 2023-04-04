from dataclasses import dataclass
from typing import Callable, Dict, Any

import yaml
from ltlf2dfa.base import Formula

from discriminative_log_generator.parse.__parse_model import parse_model


class MissingAttribute(Exception):
    def __init__(self, attribute):
        super().__init__(f"Each partition requires a `{attribute}` field, which is missing!")


def np_random_closure(method, args=dict()):
    @dataclass
    class Function(Callable):
        method_name: str
        kwargs: Dict[str, Any]
        f: Callable

        def __call__(self):
            return self.f()

        def __repr__(self):
            return self.__str__()

        def __str__(self):
            return f"{self.method_name}(kwargs={self.kwargs})"

    from numpy.random import default_rng

    import os
    seed = os.getenv('GILLIE_PYTHON_SEED')
    # TODO: Validate seed is an integer?
    g = default_rng(seed=None if seed is None else int(seed))
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

    return Function(method, args, rng_closure)


def parse_length_distribution(block):
    # TODO: Exceptions and other things
    return np_random_closure(block['numpy.random'], block['kwargs'])


@dataclass(frozen=True)
class Partition:
    label: str
    model: list[Formula]
    rng: Callable
    n: int


def parse_partition(block, known_activities):
    for attribute in ['label', 'discriminative_behavior', 'trace_length', 'n']:
        if attribute not in block:
            raise MissingAttribute(attribute)

    label = block['label']
    discriminative_behavior = parse_model(block['discriminative_behavior'], known_activities)
    trace_length = parse_length_distribution(block['trace_length'])

    return Partition(
        label,
        discriminative_behavior,
        trace_length,
        block['n']
    )


if __name__ == '__main__':
    example = """
    - discriminative_behavior:
      - chainresponse(a_1,a_2)
      - G(x -> F(y -> F(t)))
      
      label: pos_1
      
      n: 100
      
      trace_length:
        numpy.random: normal
        kwargs:
          loc: 30.0
          scale: 1.0
    """

    data = yaml.safe_load(example)
    print(data[0])
    partiton = parse_partition(data[0], {'a_1', 'a_2', 'x', 'y', 't'})

    print(partiton)
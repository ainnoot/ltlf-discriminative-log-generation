from dataclasses import dataclass
import re
from typing import List, Dict, Union, Tuple, Set, Callable
import numpy.random
import parse

from discriminative_log_generator.conf import declare

import yaml
from ltlf2dfa.base import Formula
from ltlf2dfa.parser.ltlf import LTLfParser, LTLfAnd, LTLfTrue


@dataclass(frozen=True)
class Activity:
    pattern = r'[a-z][a-z_0-9]*'
    value: str

    def __post_init__(self):
        assert re.fullmatch(Activity.pattern, self.value) is not None, f"Activity names must match {Activity.pattern}! \"{self.value}\" is not valid"


@dataclass(frozen=True)
class LengthDistribution:
    generate_one: Callable

    def get_value(self):
        return self.generate_one()

    @staticmethod
    def from_dict(data):
        generator = data['generator']
        params = data['params']

        if generator not in dir(numpy.random):
            raise Exception(f"{generator} is not a valid numpy.random function!")

        generator_f = getattr(numpy.random, generator)

        try:
            generator_f(**params)
        except Exception as e:
            raise Exception(f"Something wrong with {generator} parameters'?")

        return LengthDistribution(lambda: generator_f(**params))



@dataclass(frozen=True)
class Model:
    formula: Formula

    @staticmethod
    def from_dict(data):
        p = LTLfParser()

        formulae = []
        for f in data['ltlf']:
            print("Parsed LTLf formula:", f)
            try:
                formulae.append(p(f))
            except Exception as e:
                raise Exception(f"Invalid formula: {f}")

        for f in data['declare']:
            print("Parsed Declare constraint:", f)
            try:
                mask = "{template}({activities})"
                params = parse.parse(mask, f).named

                available_declare_templates = dir(declare)
                if params['template'] not in available_declare_templates:
                    raise Exception(f"Unkown Declare constraint: {f}")

                formulae.append(getattr(declare, params['template'])(*(params['activities'].split(','))))
            except Exception as e:
                raise Exception("Something wrong with Declare constraint", f)

        if len(formulae) < 2:
            formulae.append(LTLfTrue())

        return Model(LTLfAnd(formulae))


@dataclass(frozen=True)
class PartitionSettings:
    name: str
    model: Model
    length_distribution: LengthDistribution
    num_traces: int

    @staticmethod
    def from_dict(data):
        name = data['name']

        model = Model.from_dict(data['model'])

        length_distribution = LengthDistribution.from_dict(data['settings'])

        return PartitionSettings(name, model, length_distribution, data['num_traces'])


@dataclass(frozen=True)
class LogGeneratorSettings:
    activity_set: Set[Activity]
    partition_settings: List[PartitionSettings]

    @property
    def activities(self):
        return set([a.value for a in self.activity_set])

    @staticmethod
    def from_yaml(block):
        block_keys = block.keys()

        assert 'activities' in block_keys or 'synthetic_activities' in block_keys
        assert not ('activities' in block_keys and 'synthetic_activities' in block_keys)

        if 'activities' in block_keys:
            activity_set = [Activity(a) for a in block['activities']]
        elif 'synthetic_activities' in block_keys:
            prefix = block['synthetic_activities']['prefix']
            n = block['synthetic_activities']['n']
            activity_set = [Activity(f'{prefix}_{i}') for i in range(1, n+1)]
        else:
            raise Exception("Missing activities!")

        partitions = [PartitionSettings.from_dict(p) for p in block['partitions']]

        return LogGeneratorSettings(set(activity_set), partitions)


if __name__ == '__main__':
    with open('example.yaml', 'r') as f:
        data = yaml.safe_load(f)

    print(LogGeneratorSettings.from_yaml(data))
import sys

import yaml
from ltlf2dfa.parser.ltlf import LTLfParser
from discriminative_log_generator.ltlf import partition_formulae, ltlf_to_dfa, generate_random_trace
from argparse import ArgumentParser
from discriminative_log_generator.conf import LogGeneratorSettings

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument("settings", type=str)
    args = p.parse_args()

    with open(args.settings, 'r') as f:
        generator_settings: LogGeneratorSettings = LogGeneratorSettings.from_yaml(yaml.safe_load(f))

    partitioning_formulae = partition_formulae([ps.model.formula for ps in generator_settings.partition_settings])

    dfas = [ltlf_to_dfa(formula) for formula in partitioning_formulae]

    for partition, formula in zip(generator_settings.partition_settings, partitioning_formulae):
        dfa = ltlf_to_dfa(formula)
        print(f"Generating traces for Partition {partition.name}")

        for idx in range(partition.num_traces):
            random_trace = generate_random_trace(dfa, int(partition.length_distribution.get_value()), generator_settings.activities)
            random_trace = tuple(x.lower() for x in random_trace)
            print(random_trace)

        print("\n\n\n\n")
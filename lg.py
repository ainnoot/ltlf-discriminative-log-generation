import sys

import pandas
import yaml
from discriminative_log_generator.ltlf import partition_formulae, ltlf_to_dfa, generate_random_trace
from argparse import ArgumentParser
from discriminative_log_generator.conf import LogGeneratorSettings
from discriminative_log_generator.dump import trace_to_dataframe
import pm4py

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument("settings", type=str)
    p.add_argument("output_file", type=str)
    args = p.parse_args()

    with open(args.settings, 'r') as f:
        generator_settings: LogGeneratorSettings = LogGeneratorSettings.from_yaml(yaml.safe_load(f))

    partitioning_formulae = partition_formulae([ps.model.formula for ps in generator_settings.partition_settings])

    dfas = [ltlf_to_dfa(formula) for formula in partitioning_formulae]

    log = []
    for partition, formula in zip(generator_settings.partition_settings, partitioning_formulae):
        dfa = ltlf_to_dfa(formula)
        print(f"Generating traces for Partition {partition.name}")

        for idx in range(partition.num_traces):
            random_trace = generate_random_trace(dfa, int(partition.length_distribution.get_value()), generator_settings.activities)
            random_trace = tuple(x.lower() for x in random_trace)
            log.append(random_trace)

    event_log = pandas.DataFrame(columns=['case:concept:name', 'concept:name', 'time:timestamp'])
    for case_id, trace in enumerate(log, start=1):
        event_log = pandas.concat([event_log, trace_to_dataframe(trace, case_id)])

    pm4py.write_xes(event_log, args.output_file)

from collections import defaultdict

import yaml
from ltlf2dfa.ltlf import LTLfAnd

from discriminative_log_generator.parse import parse_partition, parse_model, parse_activity_block
from discriminative_log_generator.export import write_to, event_log_dataframe_from_dict_of_traces
from discriminative_log_generator.mona_to_dfa import separation_formula, generate_random_trace, ltlf_to_dfa


def and_formula(formulae):
    if len(formulae) == 1:
        return formulae[0]
    return LTLfAnd(formulae)


class GenerateLogTask:
    def __init__(self):
        self.activities = set()
        self.partitions = []
        self.base_model = None
        self.log = None

    def generate_log(self):
        base_formula = and_formula(self.base_model)
        dict_of_traces = defaultdict(lambda: [], dict())

        discrim_formulae = [and_formula(p.model) for p in self.partitions]

        for idx, partition in enumerate(self.partitions):
            traces = []
            to_accept = discrim_formulae[idx]
            to_reject = discrim_formulae[:idx] + discrim_formulae[idx+1:]

            discrim_behavior_formula = separation_formula(to_accept, to_reject)
            merge_with_model = LTLfAnd([base_formula, discrim_behavior_formula])

            dfa = ltlf_to_dfa(merge_with_model)

            for i in range(partition.n):
                length = partition.rng()
                traces.append(generate_random_trace(dfa, 1 + int(length), self.activities))

            dict_of_traces[partition.label].extend(traces)

        self.log = event_log_dataframe_from_dict_of_traces(dict_of_traces)
        return self.log

    def write(self, path):
        write_to(self.log, path)

    @staticmethod
    def from_yaml(path):
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        activities = parse_activity_block(data['activities'])
        base_model = parse_model(data['base_model'], activities)
        partitions = [parse_partition(block, activities) for block in data['partitions']]

        task = GenerateLogTask()
        task.activities = activities
        task.base_model = base_model
        task.partitions = partitions

        return task
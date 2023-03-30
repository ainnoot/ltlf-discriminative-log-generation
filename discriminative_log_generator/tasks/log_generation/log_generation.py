from dataclasses import dataclass
from typing import Callable

import yaml

from discriminative_log_generator.dfa_translation import ltlf_to_dfa, generate_random_trace, separation_formula
from discriminative_log_generator.export.trace_to_dataframe import event_log_dataframe_from_dict_of_traces
import pm4py
from discriminative_log_generator.tasks.utils import validate_activity
from discriminative_log_generator.tasks.utils import np_random_closure, merge_specifications
from math import floor
from ltlf2dfa.parser.ltlf import LTLfParser
from ltlf2dfa.base import Formula


@dataclass(frozen=True)
class Partition:
    specification: Formula
    trace_length_distribution: Callable
    num_traces: int
    label: str


class GenerateLogTask:
    def __init__(self):
        self.activities = set()
        self.partitions = list()

    def set_activities(self, activities):
        for a in activities:
            validate_activity(a)
            self.activities.add(a)
        return self

    def add_partition(self, p):
        unknown_activities = set(p.specification.find_labels()).difference(self.activities)
        if len(unknown_activities) > 0:
            raise Exception(f"Unknown activities: {unknown_activities}.")

        if p.num_traces <= 0:
            raise Exception("Number of traces to generate must be a positive number.")

        self.partitions.append(p)

        return self

    def generate_log(self):
        assert len(self.activities) > 0, "Cant' generate a log with no activities"
        assert len(self.partitions) > 0, "Can't generate a log with no partitions"

        log_partitions = dict()

        # Build partitioning formulae for all partitions
        all_formulae = [p.specification for p in self.partitions]
        for idx, partition in enumerate(self.partitions):
            print(f"Generating log for partition {partition}")
            partition_formula = separation_formula(partition.specification, all_formulae[:idx] + all_formulae[idx + 1:])
            dfa = ltlf_to_dfa(partition_formula)

            log_partitions[partition.label] = [generate_random_trace(dfa, 1 + floor(partition.trace_length_distribution()), self.activities) for _ in range(partition.num_traces)]

        self.activities = set()
        self.partitions = list()

        return log_partitions


def build_task_from_yaml(path):
    def parse_activities(block):
        activities = []
        for activity in block:
            if type(activity) == str:
                activities.append(activity)
            elif type(activity) == dict:
                assert 'prefix' in activity.keys()
                assert 'range' in activity.keys()
                lb, ub = activity['range']
                activities.extend([f"{activity['prefix']}_{i}" for i in range(lb, ub+1)])
            else:
                raise Exception()
        return activities

    def parse_length_distribution(block):
        from discriminative_log_generator.tasks.utils import np_random_closure
        assert 'numpy.random' in block.keys()
        assert 'kwargs' in block.keys()
        return np_random_closure(block['numpy.random'], block['kwargs'])

    def parse_partition(block):
        keys = block.keys()
        assert 'formula' in keys
        assert 'num_traces' in keys
        assert 'trace_length' in keys
        assert 'label' in keys

        formula = merge_specifications(block['formula'])
        num_traces = block['num_traces']
        rng = parse_length_distribution(block['trace_length'])
        label = block['label']

        return Partition(formula, rng, num_traces, label)

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    assert 'activities' in data.keys()
    activities = parse_activities(data['activities'])

    task = GenerateLogTask()
    task.set_activities(activities)

    for partition in data['partitions']:
        p = parse_partition(partition)
        task.add_partition(p)

    return task
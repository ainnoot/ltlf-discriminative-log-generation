import sys
from dataclasses import dataclass
from typing import Callable

import yaml

from discriminative_log_generator import (
    generate_random_trace,
    separation_formula,
    ltlf_to_dfa,
)

from discriminative_log_generator.tasks.utils import validate_activity
from discriminative_log_generator.tasks.utils import (
    merge_specifications,
)

from math import floor
from ltlf2dfa.base import Formula
from loguru import logger


@dataclass(frozen=True)
class Partition:
    specification: Formula
    trace_length_distribution: Callable
    num_traces: int
    label: str

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Partition[{self.label}, {self.specification}]"


class GenerateLogTask:
    def __init__(self):
        self.activities = set()
        self.partitions = list()
        self.log = None

    def __reset__(self):
        self.activities = set()
        self.partitions = list()
        self.log = None

    def set_activities(self, activities):
        self.__reset__()

        for a in activities:
            validate_activity(a)
            self.activities.add(a)

        logger.info(f"Activities: {self.activities}")
        return self

    def add_partition(self, p):
        unknown_activities = set(p.specification.find_labels()).difference(
            self.activities
        )

        if len(unknown_activities) > 0:
            raise Exception(f"Unknown activities: {unknown_activities}.")

        if p.num_traces <= 0:
            raise Exception("Number of traces to generate must be a positive number.")

        self.partitions.append(p)
        logger.info(f"Added partition {p}")

        return self

    def generate_log(self):
        assert len(self.activities) > 0, "Cant' generate a log with no activities"
        assert len(self.partitions) > 0, "Can't generate a log with no partitions"

        log_partitions = dict()

        # Build partitioning formulae for all partitions
        all_formulae = [p.specification for p in self.partitions]
        for idx, partition in enumerate(self.partitions):
            logger.info(f"Generating strings for partition {partition}")
            partition_formula = separation_formula(
                partition.specification, all_formulae[:idx] + all_formulae[idx + 1 :]
            )

            try:
                dfa = ltlf_to_dfa(partition_formula)
                log_partitions[partition.label] = [
                    generate_random_trace(
                        dfa,
                        1 + floor(partition.trace_length_distribution()),
                        self.activities,
                    )
                    for _ in range(partition.num_traces)
                ]

            except Exception as e:
                import traceback

                traceback.print_exc()
                logger.error(
                    f"The following LTLf formula: {partition_formula}, obtained as the separation formula for partition {partition.label}, yields an empty automaton. Halting since {self.ignore_empty_dfa=}"
                )
                sys.exit(0)

        self.log = log_partitions
        return self

    def write(self, path):
        assert self.log is not None

        from discriminative_log_generator.export import (
            write_to,
            event_log_dataframe_from_dict_of_traces,
        )

        log = event_log_dataframe_from_dict_of_traces(self.log)
        write_to(log, path)

        logger.info(f"Writing to {path}")

    @staticmethod
    def from_yaml(path, seed=77):
        def parse_activities(block):
            activities = []
            for activity in block:
                if type(activity) == str:
                    activities.append(activity)
                elif type(activity) == dict:
                    assert "prefix" in activity.keys()
                    assert "range" in activity.keys()
                    lb, ub = activity["range"]
                    activities.extend(
                        [f"{activity['prefix']}_{i}" for i in range(lb, ub + 1)]
                    )
                else:
                    raise Exception()
            return activities

        def parse_length_distribution(block):
            from discriminative_log_generator.tasks.utils import np_random_closure

            assert "numpy.random" in block.keys()
            assert "kwargs" in block.keys()
            return np_random_closure(block["numpy.random"], block["kwargs"], seed=seed)

        def parse_partition(block):
            keys = block.keys()
            assert "formula" in keys
            assert "num_traces" in keys
            assert "trace_length" in keys
            assert "label" in keys

            formula = merge_specifications(block["formula"])
            num_traces = block["num_traces"]
            rng = parse_length_distribution(block["trace_length"])
            label = block["label"]

            return Partition(formula, rng, num_traces, label)

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        assert "activities" in data.keys()
        activities = parse_activities(data["activities"])

        task = GenerateLogTask()
        task.set_activities(activities)

        for partition in data["partitions"]:
            p = parse_partition(partition)
            task.add_partition(p)

        return task

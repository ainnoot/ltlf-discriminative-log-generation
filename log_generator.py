#! ./venv/bin/python
import pandas as pd
from pm4py.objects.log.obj import EventLog, EventStream

from discriminative_log_generator.tasks import GenerateLogTask
from argparse import ArgumentParser

if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("configuration", type=str, help="Path to YAML configuration file.")
    p.add_argument(
        "output_log_path",
        type=str,
        help="Log output file. Extension defines the format.",
    )
    args = p.parse_args()

    task = GenerateLogTask.from_yaml(args.configuration)
    log = task.generate_log()

    task.write(args.output_log_path)

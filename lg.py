#! ./venv/bin/python

from discriminative_log_generator.tasks import build_task_from_yaml
from discriminative_log_generator.export import event_log_dataframe_from_dict_of_traces
from discriminative_log_generator.export import write_to, event_log_dataframe_from_dict_of_traces
from argparse import ArgumentParser
import pandas as pd

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('configuration', type=str, help="Path to YAML configuration file.")
    p.add_argument("output_log_path", type=str, help="Log output file. Extension defines the format.")
    p.add_argument("-s", "--seed", type=int, default=77)
    args = p.parse_args()

    lgt = build_task_from_yaml(args.configuration, seed=args.seed)
    lgt.generate_log()
    lgt.write(args.output_log_path)

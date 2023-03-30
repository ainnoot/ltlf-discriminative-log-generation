#! ./venv/bin/python

from discriminative_log_generator.tasks import build_task_from_yaml
from discriminative_log_generator.export import event_log_dataframe_from_dict_of_traces
import pm4py
from argparse import ArgumentParser
import pandas as pd

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('configuration', type=str, help="Path to YAML configuration file.")
    p.add_argument("output_log_path", type=str, help="Log output file. Extension defines the format.")
    p.add_argument("-s", "--seed", type=int, default=77)
    args = p.parse_args()

    lgt = build_task_from_yaml(args.configuration, seed=args.seed)
    traces_by_label = lgt.generate_log()

    log_df: pd.DataFrame = event_log_dataframe_from_dict_of_traces(traces_by_label)

    file_format = args.output_log_path.split('.')[-1]
    if file_format == 'xes':
        pm4py.write_xes(log_df, args.output_log_path)
    elif file_format == 'csv':
        log_df.to_csv(args.output_log_path, index=False)
    elif file_format == 'list':
        raise Exception("TODO")
    else:
        raise Exception(f"Format {file_format} not supported; try with `xes`, `csv` or `list`!")

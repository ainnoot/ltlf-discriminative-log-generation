#! ./venv/bin/python

from discriminative_log_generator.tasks import GenerateLogTask, build_task_from_yaml
from discriminative_log_generator.export import event_log_dataframe_from_dict_of_traces
import pm4py
from argparse import ArgumentParser

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('configuration', type=str)
    p.add_argument("output_log_path", type=str)
    args = p.parse_args()

    lgt = build_task_from_yaml(args.configuration)
    traces_by_label = lgt.generate_log()

    log_df = event_log_dataframe_from_dict_of_traces(traces_by_label)

    pm4py.write_xes(log_df, args.output_log_path)

    log = pm4py.read_xes(args.output_log_path)

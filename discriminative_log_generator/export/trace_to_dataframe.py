import pandas
import pandas as pd
from datetime import datetime, timedelta


def trace_to_dataframe(iterable_of_activities, case_id, partition_label=None):
    # TODO: Time? -> Control Flow, we are not interested in time durations.
    dt = timedelta(0, 1)
    start = datetime.fromisoformat("1999-11-04T00:05:23")

    records = []

    for activity in iterable_of_activities:
        data = {
            "case:concept:name": case_id,
            "concept:name": activity,
            "time:timestamp": start,
        }

        if partition_label is not None:
            data["case:concept:partition"] = partition_label

        records.append(data)
        start = start + dt

    return pd.DataFrame.from_records(records)


def event_log_dataframe_from_dict_of_traces(dict_of_traces):
    event_log = pandas.DataFrame(
        columns=[
            "case:concept:name",
            "case:concept:partition",
            "concept:name",
            "time:timestamp",
        ]
    )
    case_id = 1

    for label, traces in dict_of_traces.items():
        for trace in traces:
            event_log = pandas.concat(
                [event_log, trace_to_dataframe(trace, case_id, label)]
            )
            case_id += 1

    return event_log

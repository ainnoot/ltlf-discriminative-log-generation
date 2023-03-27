import pandas as pd
from datetime import datetime, timedelta


def trace_to_dataframe(iterable_of_activities, case_id):
    # TODO: Time? -> Control Flow, we are not interested in time durations.
    dt = timedelta(0, 1)
    start = datetime.fromisoformat('1999-11-04T00:05:23')

    records = []

    for activity in iterable_of_activities:
        data = {
            'case:concept:name': case_id,
            'concept:name': activity,
            'time:timestamp': start
        }

        records.append(data)
        start = start + dt

    return pd.DataFrame.from_records(records)



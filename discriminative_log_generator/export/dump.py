from pathlib import Path
import pm4py


def to_strings(event_log_df, output_file):
    strings = []

    for case_id, df in event_log_df.groupby('case:concept:name'):
        df.sort_values(['time:timestamp'], inplace=True, ascending=True)

        activities = list(df['concept:name'])
        partition = df.iloc[0]['case:concept:partition']

        strings.append((','.join(activities), partition))

    with Path(output_file).open('w') as f:
        f.writelines(["{}:{}\n".format(x, y) for x, y in strings])


def to_logic_facts(event_log_df, output_file):
    facts = []

    for case_id, df in event_log_df.groupby('case:concept:name'):

        # TODO: Logic time property?
        df.sort_values(['time:timestamp'], inplace=True, ascending=True)

        for index, row in df.iterrows():
            activity = row['concept:name']
            logic_time = index

            facts.append(f"trace({case_id},{logic_time},{activity}).")

    for (case_id, partition), _ in event_log_df.groupby(['case:concept:name', 'case:concept:partition']):
        facts.append(f"partition({case_id},{partition}).")

    with Path(output_file).open('w') as f:
        f.write("\n".join(facts))


def to_xes(event_log_df, output_file):
    pm4py.write_xes(event_log_df, output_file)


def to_csv(event_log_df, output_file):
    event_log_df.to_csv(output_file, index=False)


def write_to(log, path):
    dict2fun = {
        'txt': to_strings,
        'lp': to_logic_facts,
        'xes': to_xes,
        'csv': to_csv
    }

    extension = path.split('.')[-1]
    if extension not in dict2fun.keys():
        raise Exception(f"Unknown format: {extension}. Try {{txt, lp, xes, csv}}.")

    dict2fun[extension](log, path)
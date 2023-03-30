#! ./venv/bin/python

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
    p.add_argument("-s", "--seed", type=int, default=77)
    args = p.parse_args()

    GenerateLogTask.from_yaml(args.configuration, seed=args.seed)\
        .generate_log()\
        .write(args.output_log_path)

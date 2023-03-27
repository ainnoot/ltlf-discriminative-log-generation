import sys
from ltlf2dfa.parser.ltlf import LTLfParser
from discriminative_log_generator.ltlf import partition_formulae, ltlf_to_dfa, generate_partition
from argparse import ArgumentParser

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument("-f", "--formulae", nargs='+', help="LTLf formulae that will induce the log partitions.")
    p.add_argument("-l", "--length", type=int, help="Length of the traces to generate.")
    p.add_argument("-n", "--num-traces", type=int, help="How many traces will be generated (per partition).")
    args = p.parse_args()

    parser = LTLfParser()

    pformulae = [parser(x) for x in partition_formulae(args.formulae)]

    print("Generating traces according to the following LTLf formulae:", pformulae)

    dfas = [ltlf_to_dfa(formula) for formula in pformulae]

    for idx, dfa in enumerate(dfas):
        print("Random traces for formula", pformulae[idx])
        random_words = generate_partition(dfa, args.num_traces, args.length, {"A", "B", "C", "D", "E", "F", "G"})

        for w in random_words:
            print(w)
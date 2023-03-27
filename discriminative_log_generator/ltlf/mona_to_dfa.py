import sys
from collections import defaultdict
from copy import copy
from typing import List
import traceback

from ltlf2dfa.base import MonaProgram, Formula
from ltlf2dfa.ltlf2dfa import compute_declare_assumption, to_dfa
from logaut.backends.common.process_mona_output import parse_mona_output, MONAOutput

from ltlf2dfa.parser.ltlf import LTLfNot, LTLfAnd, LTLfTrue
from automata.fa.dfa import DFA
from random import Random, choice


class PatchException(Exception):
    def __init__(self, libname, tb):
        self.message = f"Unable to patch: {libname}\nOriginal error: {tb}"


def patch_ltlf2dfa():
    try:
        MonaProgram.__str__ = lambda self: f"MonaProgram[{self.program}]"

        def mona_program(self):
            if self.vars:
                top_comment = f"#{str(self.formula)} UNDER DECLARE ASSUMPTION"
                header = self.HEADER
                vars = ", ".join(self.vars + ["__placeholder__"])

                formula_mona = self.formula.to_mona()
                unwrap_formula = "(" + formula_mona[1:-1] + ") & (" + compute_declare_assumption(self.vars + ['__placeholder__'])[:-1] + ")"

                return "{};\n{};\nvar2 {};\n{};\n".format(
                    top_comment,
                    header,
                    vars,
                    unwrap_formula,
                )

            else:
                return "#{};\n{};\n{};\n".format(
                    str(self.formula), self.HEADER, self.formula.to_mona()
                )

        MonaProgram.mona_program = mona_program
    except Exception as e:
        raise PatchException('ltlf2dfa', traceback.format_exc())

    return True


def patch_automatalib():
    try:
        def random_word(self, k, *, seed=None):
            self._populate_count_cache_up_to_len(k)
            state = self.initial_state
            if self._count_cache[k][state] == 0:
                raise ValueError(f"Language has no words of length {k}")

            result = []
            rng = Random(seed)
            for remaining in range(k, 0, -1):
                total = self._count_cache[remaining][state]
                choice = rng.randint(0, total-1)
                for symbol, next_state in self.transitions[state].items():  # pragma: no branch
                    next_state_count = self._count_cache[remaining - 1][next_state]
                    if choice < next_state_count:
                        result.append(symbol)
                        state = next_state
                        break
                    choice -= next_state_count

            assert state in self.final_states
            return result #''.join(result)

        DFA.random_word = random_word
    except Exception as e:
        raise PatchException('automata-lib', traceback.format_exc())

    return True


def mona_to_automatalib(mona: MONAOutput):
    def decode_guard(guard):
        if 'X' in guard:
            return None

        if guard.count('1') != 1:
            return None

        return guard.find('1')

    def find_initial_state():
        def is_null(x):
            return x == 'X' * len(mona.variable_names)

        mona_initial_state = mona.initial_state
        for dst, outgoing_edges in mona.transitions[mona_initial_state].items():
            if len(outgoing_edges) == 1 and is_null(list(outgoing_edges)[0]):
                return dst

        raise Exception("Something strange going on in MONA, check:", mona)

    transitions = defaultdict(lambda: dict(), dict())
    free_variables = mona.variable_names
    for source_state, outgoing_transitions in mona.transitions.items():
        for dest_state, outgoing_edges in outgoing_transitions.items():
            for guard in outgoing_edges:
                variable_index = decode_guard(guard)
                if variable_index is not None:
                    transitions[source_state][free_variables[variable_index]] = dest_state

    return DFA(
        states=transitions.keys(),
        input_symbols=free_variables,
        initial_state=find_initial_state(),
        final_states=mona.accepting_states,
        transitions=transitions,
        allow_partial=True
    )


def partition_formulae(formulae: List[Formula]):
    partitioning_formulae = []

    for i in range(len(formulae)):
        pos = formulae[i]
        neg = formulae[:i] + formulae[i+1:]
        if len(neg) < 2:
            neg.append(LTLfTrue())
        partitioning_formulae.append(LTLfAnd([pos, LTLfNot(LTLfAnd(neg))]))

    return partitioning_formulae


def ltlf_to_dfa(ltlf):
    mona_dfa = parse_mona_output(to_dfa(ltlf, mona_dfa_out=True))
    dfa = mona_to_automatalib(mona_dfa)
    return dfa


def generate_random_trace(dfa, length, available_activities):
    involved_variables = set(a.lower() for a in dfa.input_symbols)
    fillers = list(a.lower() for a in available_activities.difference(involved_variables))

    if len(fillers) == 0:
        raise RuntimeError("Impossible to replace __placeholder__ with an activity, all activities are involved in the formula!")

    random_dfa_word = dfa.random_word(length)
    random_dfa_word = map(lambda x: x if x != '__placeholder__' else choice(fillers), random_dfa_word)
    return tuple(random_dfa_word)




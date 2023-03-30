from collections import defaultdict
from logaut.backends.common.process_mona_output import parse_mona_output, MONAOutput
from ltlf2dfa.ltlf2dfa import to_dfa
from ltlf2dfa.parser.ltlf import LTLfNot, LTLfAnd
from automata.fa.dfa import DFA
from random import choice


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

        raise Exception("I knew that sooner or later I had to read MONA's documentation for real, check this out:", mona)

    transitions = defaultdict(lambda: dict(), dict())
    free_variables = mona.variable_names
    for source_state, outgoing_transitions in mona.transitions.items():
        for dest_state, outgoing_edges in outgoing_transitions.items():
            for guard in outgoing_edges:
                variable_index = decode_guard(guard)
                if variable_index is not None:
                    transitions[source_state][free_variables[variable_index]] = dest_state

    if len(mona.accepting_states) == 0:
        raise Exception(f"The MONA program is unsatisfiable.")

    return DFA(
        states=transitions.keys(),
        input_symbols=free_variables,
        initial_state=find_initial_state(),
        final_states=mona.accepting_states,
        transitions=transitions,
        allow_partial=True
    )


def ltlf_to_dfa(ltlf):
    mona_dfa = parse_mona_output(to_dfa(ltlf, mona_dfa_out=True))
    dfa = mona_to_automatalib(mona_dfa)

    if len(dfa.final_states) == 0:
        raise Exception(f"This formula {ltlf} is unsatisfiable.")

    return dfa


def separation_formula(to_accept, to_reject):
    """
    DFA that accepts models of `to_accept` and is rejected by all formulae in `to_reject`
    """
    return LTLfAnd([to_accept, *[LTLfNot(x) for x in to_reject]])


def generate_random_trace(dfa, length, activities):
    involved_variables = set(a.lower() for a in dfa.input_symbols)
    fillers = list(a.lower() for a in activities.difference(involved_variables))

    if len(fillers) == 0:
        raise RuntimeError("Impossible to replace __placeholder__ with an activity, all activities are already involved in the formula!")

    random_dfa_word = dfa.random_word(length)
    random_dfa_word = map(lambda x: x.lower() if x != '__placeholder__' else choice(fillers).lower(), random_dfa_word)
    return tuple(random_dfa_word)




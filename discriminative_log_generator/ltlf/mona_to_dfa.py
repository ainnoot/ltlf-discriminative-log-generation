from collections import defaultdict

from ltlf2dfa.base import MonaProgram
from ltlf2dfa.ltlf2dfa import compute_declare_assumption, to_dfa, ter2symb
from logaut.backends.common.process_mona_output import parse_mona_output, MONAOutput

from ltlf2dfa.parser.ltlf import LTLfParser
from sympy import symbols
from automata.fa.dfa import DFA
from random import Random, choice


def patch_ltlf2dfa():
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


def patch_automatalib():
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


def mona_to_automatalib(mona: MONAOutput):
    def decode_guard(guard):
        if 'X' in guard:
            return None

        if guard.count('1') != 1:
            return None

        return guard.find('1')

    def find_initial_state():
        return 1

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


if __name__ == '__main__':
    # Adding Declare assumption to MonaProgram by default
    patch_ltlf2dfa()

    # Do not join state names when returning random word
    patch_automatalib()

    formula = LTLfParser()("G(a -> X(b)) && G(c -> F(d))")
    mona_dfa = parse_mona_output(to_dfa(formula, mona_dfa_out=True))

    dfa = mona_to_automatalib(mona_dfa)

    involved_variables = set(dfa.input_symbols)
    activities = {"A", "B", "C", "D", "__placeholder__", "Q", "X", "T"}
    available_fillers = list(activities.difference(involved_variables))

    if len(available_fillers) == 0:
        raise RuntimeError("Impossible to replace __placeholder__ with an activity, all activities are involved in the formula!")

    for _ in range(10):
        random_dfa_word = dfa.random_word(8)
        random_dfa_word = map(lambda x: x if x != '__placeholder__' else choice(available_fillers), random_dfa_word)
        print(list(random_dfa_word))
from .mona_to_dfa import ltlf_to_dfa, generate_random_trace, separation_formula


class PatchException(Exception):
    def __init__(self, libname, tb):
        self.message = f"Unable to patch: {libname}\nOriginal error: {tb}"


def patch_ltlf2dfa():
    from ltlf2dfa.ltlf2dfa import compute_declare_assumption, to_dfa
    from logaut.backends.common.process_mona_output import parse_mona_output, MONAOutput
    from ltlf2dfa.base import MonaProgram, Formula
    import traceback

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
    from random import Random
    import traceback
    from automata.fa.dfa import DFA

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


patch_automatalib()
patch_ltlf2dfa()
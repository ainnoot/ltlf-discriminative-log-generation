from .mona_to_dfa import patch_ltlf2dfa, patch_automatalib, partition_formulae, ltlf_to_dfa, generate_random_trace


print("Patching ltl2dfa...", patch_ltlf2dfa())
print("Patching automata-lib...", patch_automatalib())

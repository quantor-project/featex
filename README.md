# CQP-based feature extraction for ICE corpora in QuanTOR

## Common files

- `macros/featex.m`: defines key macros for interoperability with Python/Perl scripts
- `macros/*.m`: further macros may be used by individual CQP extraction scripts
- `wordlists/`: contains various word lists for use in CQP extraction scripts
  - `wordlists/tmp/`: temporary word lists currently used by demo scripts for Perl version

## Python version

- `featex.py`: script for feature aggregation and output of feature matrix
- `featex.cqp`: example CQP script for feature extraction

## Perl version

- `featex.perl`: original Perl script (should work exactly the same as `featex.py`)
  - usage sample: `cqp -c -D ICE9 -f ice_get_features.cqp | perl featex.perl ice9_features.tsv`
- `ice_get_features.cqp`: CQP feature extraction script for testing (should work with ICE9 corpus)

- `featex-annotate.perl`: annotate all token-level features as s-attributes in CWB corpus (doesn't generate feature matrix)
  - requires CWB/Perl modules (install with `cpan CWB CWB::CL`)
  - see `perl featex-annotate.perl -h` for options (should be self-explanatory)
  - usage sample: `cqp -c -D ICE9 -f ice_get_feature_tokens.cqp | perl featex-annotate.perl ICE9`
- `ice_get_feature_tokens.cqp`: modified CQP feature extraction script for `featex-annotate.perl`
  - must be changed to use `/token[]` rather than `/token_count[]` for all features to be written back into CWB corpus
  - don't annotate features such as nouns, lexical words, etc. -> would be overkill

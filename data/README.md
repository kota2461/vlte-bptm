# Local Pattern Lab Data

`pattern_lab.db` is created here by the Pattern Lab CLI. The SQLite database
contains source metadata, review candidates, human decisions, approved
patterns, and training-run metadata.

Generated databases and exported training data should not be committed unless
their source licensing and personal-data handling have been reviewed.

`observations.db` may be created explicitly by `vlte-observe --store`. It
contains only policy-filtered daily aggregates, is ignored by Git, and is
subject to the 30-day retention policy. It is not a complete anonymization
guarantee; OS access, backups, and the source input file remain operator
responsibilities.

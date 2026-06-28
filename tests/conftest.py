"""Pytest-wide configuration.

Freezes ``SOURCE_DATE_EPOCH`` for the whole test session so that generator
scripts (run in-process or via ``subprocess.run``, which inherits the
environment) emit a stable ``generated_at`` / ``frozen_at`` timestamp. Without
this, regenerating an artifact during a test run rewrites its timestamp and
leaves tracked build/ and fixture files dirty after every run.

See ``semantic_routing/reproducibility.py``. ``setdefault`` lets an explicit
external value win, e.g. when reproducing a specific committed artifact.
"""

import os

# 2026-01-01T00:00:00+00:00 -- an obvious frozen sentinel, not a real run time.
os.environ.setdefault("SOURCE_DATE_EPOCH", "1767225600")
